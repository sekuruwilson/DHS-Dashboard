import os
import re
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import (
    Category, Indicator, IndicatorValue, District, Province,
    DHSUploadedDataset, SystemAuditLog
)
from .forms import CategoryForm, IndicatorForm, DataValueForm


# ─────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────

def admin_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')


def audit(request, action, description, details=None, success=True):
    SystemAuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        description=description,
        details=details,
        ip_address=get_client_ip(request),
        success=success,
    )


DHS_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'DHS', 'data'))

RECODE_MAP = {
    'hr': 'HR', 'pr': 'PR', 'ir': 'IR',
    'mr': 'MR', 'kr': 'KR', 'br': 'BR', 'cr': 'CR',
}


def identify_recode(filename):
    """Return the recode key (HR/PR/IR…) from a filename."""
    name = filename.lower()
    for code in RECODE_MAP:
        if code in name:
            return RECODE_MAP[code]
    return None




# ─────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────

def admin_login_view(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')

    context = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                audit(request, 'LOGIN', f'Admin login: {username}')
                return redirect(request.GET.get('next', 'admin_dashboard'))
            else:
                context['error_message'] = "Access denied. Admin privileges required."
        else:
            context['error_message'] = "Invalid username or password."

    return render(request, 'admin/admin_login.html', context)


def admin_logout_view(request):
    audit(request, 'LOGOUT', f'Admin logout: {request.user.username}')
    logout(request)
    return redirect('admin_login')


# ─────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def admin_dashboard_view(request):
    datasets = DHSUploadedDataset.objects.all().order_by('recode_type')
    recent_logs = SystemAuditLog.objects.select_related('user').all()[:10]

    context = {
        'total_categories': Category.objects.count(),
        'total_indicators': Indicator.objects.count(),
        'total_values': IndicatorValue.objects.count(),
        'total_districts': District.objects.filter(
            province__name__in=['Kigali City','Southern Province','Western Province','Northern Province','Eastern Province']
        ).exclude(
            name__in=['Kigali City','Southern Province','Western Province','Northern Province','Eastern Province']
        ).count(),
        'total_users': User.objects.count(),
        'uploaded_datasets': datasets,
        'recent_logs': recent_logs,
        'categories': Category.objects.all().order_by('name'),
    }
    return render(request, 'admin/dashboard.html', context)


# ─────────────────────────────────────────────────
# DATASET UPLOAD
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def dataset_upload_view(request):
    """Upload one or more .dta files. Stores them in DHS/data/ and records metadata."""
    if not os.path.exists(DHS_DATA_DIR):
        os.makedirs(DHS_DATA_DIR)

    if request.method == 'POST':
        year = request.POST.get('year', '').strip()
        if not year.isdigit():
            messages.error(request, "Please provide a valid survey year.")
            return redirect('admin_dataset_upload')

        year = int(year)
        files = request.FILES.getlist('dta_files')
        if not files:
            messages.error(request, "No files selected.")
            return redirect('admin_dataset_upload')

        saved = 0
        for f in files:
            recode = identify_recode(f.name)
            if not recode:
                messages.warning(request, f"Skipped '{f.name}': cannot identify recode type.")
                continue

            target_path = os.path.join(DHS_DATA_DIR, f"{recode}_{year}.DTA")
            with open(target_path, 'wb+') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            # Read metadata quickly
            try:
                import pyreadstat
                _, meta = pyreadstat.read_dta(target_path, metadataonly=True)
                num_rows = meta.number_rows
                num_vars = len(meta.column_names)
            except Exception:
                num_rows = None
                num_vars = None

            DHSUploadedDataset.objects.update_or_create(
                recode_type=recode, year=year,
                defaults={
                    'original_filename': f.name,
                    'file_path': target_path,
                    'uploaded_by': request.user,
                    'num_rows': num_rows,
                    'num_vars': num_vars,
                }
            )
            saved += 1
            audit(request, 'UPLOAD',
                  f"Uploaded {recode} dataset ({year})",
                  details=f"File: {f.name}, Rows: {num_rows}, Vars: {num_vars}")

        messages.success(request, f"Successfully uploaded {saved} dataset(s) for year {year}.")
        return redirect('admin_dataset_upload')

    uploaded = DHSUploadedDataset.objects.all().order_by('year', 'recode_type')
    return render(request, 'admin/data/upload.html', {'uploaded': uploaded})


@user_passes_test(admin_required, login_url='admin_login')
def dataset_delete_view(request, pk):
    ds = get_object_or_404(DHSUploadedDataset, pk=pk)
    if request.method == 'POST':
        try:
            if os.path.exists(ds.file_path):
                os.remove(ds.file_path)
        except OSError:
            pass
        desc = str(ds)
        ds.delete()
        audit(request, 'DATA_DELETE', f"Deleted dataset: {desc}")
        messages.success(request, f"Deleted dataset {desc}.")
    return redirect('admin_dataset_upload')


# ─────────────────────────────────────────────────
# VARIABLE EXPLORER
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def dataset_variables_view(request):
    """Read metadata from uploaded .dta files and show all variable names/labels."""
    variables = []
    datasets = DHSUploadedDataset.objects.all().order_by('recode_type')
    selected_recode = request.GET.get('recode', '')
    search_q = request.GET.get('q', '').lower()

    for ds in datasets:
        if selected_recode and ds.recode_type != selected_recode:
            continue
        if not os.path.exists(ds.file_path):
            continue
        try:
            import pyreadstat
            _, meta = pyreadstat.read_dta(ds.file_path, metadataonly=True)
            labels = meta.column_labels or {}
            for col in meta.column_names:
                label = labels.get(col, '') if isinstance(labels, dict) else ''
                if search_q and search_q not in col.lower() and search_q not in label.lower():
                    continue
                variables.append({
                    'recode': ds.recode_type,
                    'year': ds.year,
                    'name': col,
                    'label': label,
                })
        except Exception as e:
            messages.warning(request, f"Could not read {ds.recode_type} ({ds.year}): {e}")

    paginator = Paginator(variables, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin/data/variables.html', {
        'page_obj': page_obj,
        'datasets': datasets,
        'selected_recode': selected_recode,
        'search_q': search_q,
        'total_vars': len(variables),
    })


# ─────────────────────────────────────────────────
# INDICATOR CALCULATOR
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def indicator_calculate_view(request):
    """List all available indicators from dhs_indicator.py and allow running them."""
    from .dhs_indicator import INDICATORS

    # Build flat list of indicators with their chapters and required recodes
    indicator_list = []
    for chapter, inds in INDICATORS.items():
        for ind_name, meta in inds.items():
            indicator_list.append({
                'chapter': chapter,
                'name': ind_name,
                'req': meta['req'],
            })

    # Available datasets grouped by recode type
    available_recodes = set(DHSUploadedDataset.objects.values_list('recode_type', flat=True))
    available_years = sorted(set(DHSUploadedDataset.objects.values_list('year', flat=True)), reverse=True)

    context = {
        'indicator_list': indicator_list,
        'available_recodes': available_recodes,
        'available_years': available_years,
    }
    return render(request, 'admin/data/calculate.html', context)


@user_passes_test(admin_required, login_url='admin_login')
def indicator_run_view(request):
    """Run a single indicator calculation and save results to the DB."""
    if request.method != 'POST':
        return redirect('admin_indicator_calculate')

    from .dhs_indicator import INDICATORS
    from .dhs_core import load_data

    chapter = request.POST.get('chapter')
    ind_name = request.POST.get('indicator')
    year = request.POST.get('year', '')

    if not year.isdigit():
        messages.error(request, "Invalid year.")
        return redirect('admin_indicator_calculate')
    year = int(year)

    # Find indicator definition
    ind_def = INDICATORS.get(chapter, {}).get(ind_name)
    if not ind_def:
        messages.error(request, f"Indicator '{ind_name}' not found.")
        return redirect('admin_indicator_calculate')

    # Load required datasets
    datasets = {}
    missing = []
    for recode in ind_def['req']:
        ds = DHSUploadedDataset.objects.filter(recode_type=recode, year=year).first()
        if not ds or not os.path.exists(ds.file_path):
            # Try any year for that recode
            ds = DHSUploadedDataset.objects.filter(recode_type=recode).order_by('-year').first()
        if ds and os.path.exists(ds.file_path):
            df = load_data(ds.file_path)
            if df is not None and not df.empty:
                datasets[recode] = df
            else:
                missing.append(recode)
        else:
            missing.append(recode)

    if missing:
        messages.error(request, f"Missing datasets: {', '.join(missing)}. Please upload them first.")
        audit(request, 'COMPUTE', f"Failed: {ind_name} — missing {missing}", success=False)
        return redirect('admin_indicator_calculate')

    # Run calculation
    try:
        result_df = ind_def['fn'](datasets)
    except Exception as e:
        messages.error(request, f"Calculation error for '{ind_name}': {e}")
        audit(request, 'COMPUTE', f"Error: {ind_name}", details=str(e), success=False)
        return redirect('admin_indicator_calculate')

    if result_df is None or result_df.empty:
        messages.warning(request, f"'{ind_name}' returned no data (possibly missing variables in dataset).")
        return redirect('admin_indicator_calculate')

    # Ensure the category exists
    category, _ = Category.objects.get_or_create(name=chapter)

    # Determine if multi-category result
    has_category = 'Category' in result_df.columns

    saved = 0
    skipped = 0

    for _, row in result_df.iterrows():
        loc_name = row.get('Location')
        value = row.get('Value')
        data_label = str(row.get('Category', 'Total')) if has_category else 'Total'

        if loc_name is None or value is None:
            continue

        import math
        if isinstance(value, float) and math.isnan(value):
            continue

        district = resolve_district_by_name(str(loc_name))
        if not district:
            skipped += 1
            continue

        indicator, _ = Indicator.objects.get_or_create(
            name=ind_name, category=category, year=year,
            defaults={'unit': 'Percentage (%)'}
        )

        IndicatorValue.objects.update_or_create(
            indicator=indicator, district=district,
            data_label=data_label, year=year,
            defaults={'value': float(value)}
        )
        saved += 1

    audit(request, 'COMPUTE',
          f"Computed: {ind_name} ({year})",
          details=f"Saved {saved} values, skipped {skipped} unmatched locations")

    messages.success(request, f"✅ '{ind_name}' ({year}): saved {saved} values ({skipped} locations skipped).")
    return redirect('admin_indicator_calculate')


# ─────────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    q = request.GET.get('q', '')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin/users/list.html', {'page_obj': page_obj, 'q': q})


@user_passes_test(admin_required, login_url='admin_login')
def user_create_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'report')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'admin/users/form.html', {'action': 'Create'})

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
            return render(request, 'admin/users/form.html', {'action': 'Create'})

        user = User.objects.create_user(username=username, email=email, password=password)
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()

        audit(request, 'USER_CREATE', f"Created user: {username} (role={role})")
        messages.success(request, f"User '{username}' created successfully.")
        return redirect('admin_user_list')

    return render(request, 'admin/users/form.html', {'action': 'Create'})


@user_passes_test(admin_required, login_url='admin_login')
def user_edit_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'report')
        password = request.POST.get('password', '').strip()

        target_user.email = email
        target_user.is_staff = (role == 'admin')
        target_user.is_superuser = (role == 'admin')
        if password:
            target_user.set_password(password)
        target_user.save()

        audit(request, 'USER_UPDATE', f"Updated user: {target_user.username}")
        messages.success(request, f"User '{target_user.username}' updated.")
        return redirect('admin_user_list')

    role = 'admin' if target_user.is_staff else 'report'
    return render(request, 'admin/users/form.html', {
        'action': 'Edit', 'target_user': target_user, 'role': role
    })


@user_passes_test(admin_required, login_url='admin_login')
def user_delete_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin_user_list')
    if request.method == 'POST':
        name = target_user.username
        target_user.delete()
        audit(request, 'USER_DELETE', f"Deleted user: {name}")
        messages.success(request, f"User '{name}' deleted.")
    return redirect('admin_user_list')


@user_passes_test(admin_required, login_url='admin_login')
def user_toggle_active_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = "activated" if target_user.is_active else "deactivated"
        audit(request, 'USER_UPDATE', f"User {status}: {target_user.username}")
        messages.success(request, f"User '{target_user.username}' {status}.")
    return redirect('admin_user_list')


# ─────────────────────────────────────────────────
# AUDIT LOGS
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def audit_log_view(request):
    from datetime import datetime
    all_logs = SystemAuditLog.objects.select_related('user').all()

    # Overall stats (unfiltered)
    total_count = all_logs.count()
    success_count = all_logs.filter(success=True).count()
    failed_count = all_logs.filter(success=False).count()

    # Apply filters
    logs = all_logs
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '').strip()
    success_filter = request.GET.get('success', '')
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if action_filter:
        logs = logs.filter(action=action_filter)
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    if success_filter == '1':
        logs = logs.filter(success=True)
    elif success_filter == '0':
        logs = logs.filter(success=False)
    if date_from:
        try:
            logs = logs.filter(timestamp__date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            date_from = ''
    if date_to:
        try:
            logs = logs.filter(timestamp__date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            date_to = ''

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin/audit/list.html', {
        'page_obj': page_obj,
        'action_choices': SystemAuditLog.ACTION_CHOICES,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'success_filter': success_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': total_count,
        'success_count': success_count,
        'failed_count': failed_count,
    })


# ─────────────────────────────────────────────────
# CATEGORY MANAGEMENT (existing)
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def category_list_view(request):
    categories = Category.objects.all()
    return render(request, 'admin/categories/list.html', {'categories': categories})


@user_passes_test(admin_required, login_url='admin_login')
def category_create_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('admin_categories')
    else:
        form = CategoryForm()
    return render(request, 'admin/categories/form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def category_edit_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('admin_categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'admin/categories/form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('admin_categories')
    return render(request, 'admin/categories/delete.html', {'category': category})


# ─────────────────────────────────────────────────
# INDICATOR MANAGEMENT (existing)
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def indicator_list_admin_view(request):
    indicators = Indicator.objects.select_related('category').all().order_by('name')
    categories = Category.objects.all().order_by('name')
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    if query:
        indicators = indicators.filter(name__icontains=query)
    if category_id:
        indicators = indicators.filter(category_id=category_id)
    paginator = Paginator(indicators, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'indicators': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'categories': categories,
    }
    return render(request, 'admin/indicators/list.html', context)


@user_passes_test(admin_required, login_url='admin_login')
def indicator_create_view(request):
    if request.method == 'POST':
        form = IndicatorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Indicator created successfully.')
            return redirect('admin_indicators')
    else:
        form = IndicatorForm()
    return render(request, 'admin/indicators/form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def indicator_edit_view(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    if request.method == 'POST':
        form = IndicatorForm(request.POST, instance=indicator)
        if form.is_valid():
            form.save()
            messages.success(request, 'Indicator updated successfully.')
            return redirect('admin_indicators')
    else:
        form = IndicatorForm(instance=indicator)
    return render(request, 'admin/indicators/form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def indicator_delete_view(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    if request.method == 'POST':
        indicator.delete()
        messages.success(request, 'Indicator deleted successfully.')
        return redirect('admin_indicators')
    return render(request, 'admin/indicators/delete.html', {'indicator': indicator})


# ─────────────────────────────────────────────────
# DATA VALUES (existing)
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def datavalue_list_view(request):
    values = IndicatorValue.objects.select_related('indicator', 'district').all()
    paginator = Paginator(values, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin/datavalues/list.html', {'page_obj': page_obj})


@user_passes_test(admin_required, login_url='admin_login')
def datavalue_create_view(request):
    if request.method == 'POST':
        form = DataValueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data Value added successfully.')
            return redirect('admin_datavalues')
    else:
        form = DataValueForm()
    return render(request, 'admin/datavalues/form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def datavalue_edit_view(request, pk):
    value = get_object_or_404(IndicatorValue, pk=pk)
    if request.method == 'POST':
        form = DataValueForm(request.POST, instance=value)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data Value updated successfully.')
            return redirect('admin_datavalues')
    else:
        form = DataValueForm(instance=value)
    return render(request, 'admin/datavalues/form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def datavalue_delete_view(request, pk):
    value = get_object_or_404(IndicatorValue, pk=pk)
    if request.method == 'POST':
        value.delete()
        messages.success(request, 'Data Value deleted successfully.')
        return redirect('admin_datavalues')
    return render(request, 'admin/datavalues/delete.html', {'value': value})


# ─────────────────────────────────────────────────
# LOCATION MANAGEMENT (existing)
# ─────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def location_list_view(request):
    from django.db.models import Count
    # Exclude 'National' from list of actual provinces and annotate with actual district count
    provinces = Province.objects.exclude(name='National').annotate(
        actual_districts_count=Count(
            'districts',
            filter=~Q(districts__name__in=['Kigali City', 'Southern Province', 'Western Province', 'Northern Province', 'Eastern Province', 'Rwanda'])
        )
    ).order_by('name')
    
    # Exclude aggregate districts from actual districts list
    districts = District.objects.select_related('province').exclude(
        name__in=['Kigali City', 'Southern Province', 'Western Province', 'Northern Province', 'Eastern Province', 'Rwanda']
    ).order_by('name')
    
    # Separate the aggregate/system records so they are still visible/managed but clearly distinguished
    system_locations = District.objects.select_related('province').filter(
        name__in=['Kigali City', 'Southern Province', 'Western Province', 'Northern Province', 'Eastern Province', 'Rwanda']
    ).order_by('province__name', 'name')
    
    return render(request, 'admin/locations/list.html', {
        'provinces': provinces, 
        'districts': districts,
        'system_locations': system_locations
    })


from .forms import ProvinceForm, DistrictForm


@user_passes_test(admin_required, login_url='admin_login')
def province_create_view(request):
    if request.method == 'POST':
        form = ProvinceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Province created successfully.')
            return redirect('admin_locations')
    else:
        form = ProvinceForm()
    return render(request, 'admin/locations/province_form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def province_edit_view(request, pk):
    province = get_object_or_404(Province, pk=pk)
    if request.method == 'POST':
        form = ProvinceForm(request.POST, instance=province)
        if form.is_valid():
            form.save()
            messages.success(request, 'Province updated successfully.')
            return redirect('admin_locations')
    else:
        form = ProvinceForm(instance=province)
    return render(request, 'admin/locations/province_form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def province_delete_view(request, pk):
    province = get_object_or_404(Province, pk=pk)
    if request.method == 'POST':
        province.delete()
        messages.success(request, 'Province deleted successfully.')
        return redirect('admin_locations')
    return render(request, 'admin/locations/delete.html', {'object': province, 'type': 'Province'})


@user_passes_test(admin_required, login_url='admin_login')
def district_create_view(request):
    if request.method == 'POST':
        form = DistrictForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'District created successfully.')
            return redirect('admin_locations')
    else:
        form = DistrictForm()
    return render(request, 'admin/locations/district_form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def district_edit_view(request, pk):
    district = get_object_or_404(District, pk=pk)
    if request.method == 'POST':
        form = DistrictForm(request.POST, instance=district)
        if form.is_valid():
            form.save()
            messages.success(request, 'District updated successfully.')
            return redirect('admin_locations')
    else:
        form = DistrictForm(instance=district)
    return render(request, 'admin/locations/district_form.html', {'form': form})


@user_passes_test(admin_required, login_url='admin_login')
def district_delete_view(request, pk):
    district = get_object_or_404(District, pk=pk)
    if request.method == 'POST':
        district.delete()
        messages.success(request, 'District deleted successfully.')
        return redirect('admin_locations')
    return render(request, 'admin/locations/delete.html', {'object': district, 'type': 'District'})


def resolve_district_by_name(name):
    """Map a location name to a District DB object, supporting custom aliases."""
    if not name:
        return None
    name = name.strip()
    
    aliases = {
        "Rwanda": "Rwanda",
        "National": "Rwanda",
        "Rwanda (National)": "Rwanda",
        "Kigali City": "Kigali City",
        "South": "Southern Province",
        "West": "Western Province",
        "North": "Northern Province",
        "East": "Eastern Province",
        "East Province": "Eastern Province",
        "Eastern Province": "Eastern Province",
        "Southern Province": "Southern Province",
        "Western Province": "Western Province",
        "Northern Province": "Northern Province",
    }
    
    mapped = aliases.get(name, name)
    return District.objects.filter(name__iexact=mapped).first()


def save_indicators_from_json(file_path, category, year):
    """Read indicator data from a JSON file and save to the database."""
    import json
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    indicator_name = data.get('indicator')
    unit = data.get('unit', 'Percentage (%)')
    values_data = data.get('data', {})
    
    if not indicator_name:
        return 0
        
    indicator, _ = Indicator.objects.get_or_create(
        name=indicator_name,
        category=category,
        year=year,
        defaults={'unit': unit}
    )
    
    saved_count = 0
    for loc_name, value in values_data.items():
        district = resolve_district_by_name(loc_name)
        if district:
            IndicatorValue.objects.update_or_create(
                indicator=indicator,
                district=district,
                year=year,
                data_label='Total',
                defaults={'value': float(value)}
            )
            saved_count += 1
            
    return saved_count


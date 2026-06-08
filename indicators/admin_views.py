"""
Admin panel views — Dashboard, Dataset Upload, User Management, Audit Logs.

Upload flow: when a .DTA file is uploaded, a background thread automatically
computes every indicator whose required recode files are all present on disk.
"""
import os
import math
import threading
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    Category, DHSUploadedDataset, District, Indicator,
    IndicatorValue, SystemAuditLog,
)


# ──────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────

DHS_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'DHS', 'data')
)

RECODE_MAP = {
    'hr': 'HR', 'pr': 'PR', 'ir': 'IR',
    'mr': 'MR', 'kr': 'KR', 'br': 'BR', 'cr': 'CR',
}


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def admin_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return forwarded.split(',')[0] if forwarded else request.META.get('REMOTE_ADDR')


def audit(request, action, description, details=None, success=True):
    SystemAuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        description=description,
        details=details,
        ip_address=get_client_ip(request),
        success=success,
    )


def identify_recode(filename):
    """Detect the DHS recode type (HR/PR/IR…) from a filename."""
    name = filename.lower()
    for code, label in RECODE_MAP.items():
        if code in name:
            return label
    return None


def resolve_district_by_name(name):
    """Map a DHS output location string to a District DB record."""
    if not name:
        return None
    aliases = {
        'Rwanda': 'Rwanda',
        'National': 'Rwanda',
        'Rwanda (National)': 'Rwanda',
        'Kigali City': 'Kigali City',
        'South': 'Southern Province',
        'West': 'Western Province',
        'North': 'Northern Province',
        'East': 'Eastern Province',
        'East Province': 'Eastern Province',
        'Eastern Province': 'Eastern Province',
        'Southern Province': 'Southern Province',
        'Western Province': 'Western Province',
        'Northern Province': 'Northern Province',
    }
    mapped = aliases.get(name.strip(), name.strip())
    return District.objects.filter(name__iexact=mapped).first()


# ──────────────────────────────────────────────────────────────
# BACKGROUND INDICATOR COMPUTATION
# ──────────────────────────────────────────────────────────────

def _compute_all_for_year(year, user_id):
    """
    Runs inside a background thread.

    For the given survey year, loads every uploaded recode file and runs
    all INDICATORS whose required recodes are fully available on disk.
    Results are written to the database.
    """
    from .dhs_core import load_data
    from .dhs_indicator import INDICATORS

    # Collect what's on disk for this year
    datasets_qs = DHSUploadedDataset.objects.filter(year=year)
    available = {ds.recode_type for ds in datasets_qs}

    # Load DataFrames once (cache per recode type)
    dataframes = {}
    for ds in datasets_qs:
        if os.path.exists(ds.file_path):
            df = load_data(ds.file_path)
            if df is not None and not df.empty:
                dataframes[ds.recode_type] = df

    computed = 0
    skipped = 0
    errors = 0

    for chapter_name, indicators in INDICATORS.items():
        category, _ = Category.objects.get_or_create(name=chapter_name)

        for ind_name, config in indicators.items():
            required = set(config['req'])
            if not required.issubset(available):
                skipped += 1
                continue  # not all required files uploaded yet

            # Build the subset of dataframes this indicator needs
            datasets_for_fn = {r: dataframes[r] for r in required if r in dataframes}
            if set(datasets_for_fn.keys()) != required:
                skipped += 1
                continue

            try:
                result_df = config['fn'](datasets_for_fn)
            except Exception:
                errors += 1
                continue

            if result_df is None or result_df.empty:
                continue

            indicator, _ = Indicator.objects.get_or_create(
                name=ind_name,
                category=category,
                year=year,
                defaults={'unit': 'Percentage (%)'},
            )

            has_category_col = 'Category' in result_df.columns

            for _, row in result_df.iterrows():
                loc_name = row.get('Location')
                value = row.get('Value')
                data_label = str(row.get('Category', 'Total')) if has_category_col else 'Total'

                if loc_name is None or value is None:
                    continue
                if isinstance(value, float) and math.isnan(value):
                    continue

                district = resolve_district_by_name(str(loc_name))
                if not district:
                    continue

                IndicatorValue.objects.update_or_create(
                    indicator=indicator,
                    district=district,
                    data_label=data_label,
                    year=year,
                    defaults={'value': float(value)},
                )
                computed += 1

    # Write a summary audit log entry (no request object in thread)
    user = User.objects.filter(pk=user_id).first()
    SystemAuditLog.objects.create(
        user=user,
        action='COMPUTE',
        description=f'Auto-computed indicators for year {year}',
        details=(
            f'Computed {computed} values | '
            f'Skipped {skipped} indicators (missing recodes) | '
            f'Errors: {errors}'
        ),
        success=(errors == 0),
    )


def trigger_background_computation(year, user):
    """
    Spawns a daemon thread that computes all available indicators for
    the given year.  Closes the current DB connection first so the
    thread starts with its own fresh connection.
    """
    user_id = user.id

    def _worker():
        connection.close()   # each thread needs its own DB connection
        _compute_all_for_year(year, user_id)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


# ──────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────

def admin_login_view(request):
    if request.user.is_authenticated and admin_required(request.user):
        return redirect('admin_dashboard')

    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user and admin_required(user):
            login(request, user)
            audit(request, 'LOGIN', f'Admin login: {user.username}')
            return redirect(request.GET.get('next', 'admin_dashboard'))
        error = 'Invalid credentials or insufficient privileges.'

    return render(request, 'admin/admin_login.html', {'error': error})


def admin_logout_view(request):
    audit(request, 'LOGOUT', f'Admin logout: {request.user.username}')
    logout(request)
    return redirect('admin_login')


# ──────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def admin_dashboard_view(request):
    uploaded_datasets = DHSUploadedDataset.objects.all().order_by('year', 'recode_type')
    recent_logs = SystemAuditLog.objects.select_related('user').all()[:10]

    # Available recode types per year for quick status display
    years_with_recodes = {}
    for ds in uploaded_datasets:
        years_with_recodes.setdefault(ds.year, []).append(ds.recode_type)

    context = {
        'total_indicators': Indicator.objects.count(),
        'total_values': IndicatorValue.objects.count(),
        'total_datasets': uploaded_datasets.count(),
        'total_users': User.objects.count(),
        'uploaded_datasets': uploaded_datasets,
        'years_with_recodes': years_with_recodes,
        'recent_logs': recent_logs,
    }
    return render(request, 'admin/dashboard.html', context)


# ──────────────────────────────────────────────────────────────
# DATASET UPLOAD
# ──────────────────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def dataset_upload_view(request):
    """
    Upload one or more .DTA files for a given survey year.
    After a successful upload, indicators are computed automatically
    in a background thread.
    """
    if request.method == 'POST':
        year = request.POST.get('year', '').strip()
        if not year.isdigit():
            messages.error(request, 'Please provide a valid survey year.')
            return redirect('admin_dataset_upload')

        year = int(year)
        os.makedirs(DHS_DATA_DIR, exist_ok=True)
        files = request.FILES.getlist('dta_files')

        if not files:
            messages.error(request, 'No files were selected.')
            return redirect('admin_dataset_upload')

        saved = 0
        for f in files:
            recode = identify_recode(f.name)
            if not recode:
                messages.warning(request, f"Skipped '{f.name}': unrecognised recode type.")
                continue

            dest_path = os.path.join(DHS_DATA_DIR, f'{recode}_{year}.DTA')
            with open(dest_path, 'wb+') as out:
                for chunk in f.chunks():
                    out.write(chunk)

            # Read basic metadata without loading full data
            try:
                import pyreadstat
                _, meta = pyreadstat.read_dta(dest_path, metadataonly=True)
                num_rows = meta.number_rows
                num_vars = len(meta.column_names)
            except Exception:
                num_rows = num_vars = None

            DHSUploadedDataset.objects.update_or_create(
                recode_type=recode,
                year=year,
                defaults={
                    'original_filename': f.name,
                    'file_path': dest_path,
                    'uploaded_by': request.user,
                    'num_rows': num_rows,
                    'num_vars': num_vars,
                },
            )
            audit(
                request, 'UPLOAD',
                f'Uploaded {recode} dataset ({year})',
                details=f'File: {f.name} | Rows: {num_rows} | Vars: {num_vars}',
            )
            saved += 1

        if saved:
            messages.success(
                request,
                f'{saved} file(s) uploaded for {year}. '
                'Indicator computation has started in the background.'
            )
            trigger_background_computation(year, request.user)
        return redirect('admin_dataset_upload')

    uploaded = DHSUploadedDataset.objects.all().order_by('year', 'recode_type')

    # Group datasets by year for the template
    years = {}
    for ds in uploaded:
        years.setdefault(ds.year, []).append(ds)

    return render(request, 'admin/data/upload.html', {'uploaded': uploaded, 'years': years})


@user_passes_test(admin_required, login_url='admin_login')
def dataset_compute_view(request, year):
    """
    Trigger background indicator computation for an already-uploaded year.

    GET  — check whether data already exists for this year and ask for
            confirmation before overwriting.
    POST — confirmed; start the background job.
    """
    available = list(
        DHSUploadedDataset.objects.filter(year=year).values_list('recode_type', flat=True)
    )
    if not available:
        messages.error(request, f'No datasets registered for year {year}.')
        return redirect('admin_dataset_upload')

    existing_indicators = Indicator.objects.filter(year=year).count()
    existing_values = IndicatorValue.objects.filter(year=year).count()
    already_computed = existing_indicators > 0

    if request.method == 'POST':
        trigger_background_computation(year, request.user)
        messages.success(
            request,
            f'Computation started for {year} '
            f'(recodes: {", ".join(available)}). '
            'Existing values will be updated in place — no duplicates created. '
            'Check Audit Logs when it finishes.'
        )
        return redirect('admin_dataset_upload')

    # GET — show confirmation page if data already exists, otherwise ask once
    return render(request, 'admin/data/compute_confirm.html', {
        'year': year,
        'available_recodes': available,
        'already_computed': already_computed,
        'existing_indicators': existing_indicators,
        'existing_values': existing_values,
    })


@user_passes_test(admin_required, login_url='admin_login')
def dataset_delete_view(request, pk):
    ds = get_object_or_404(DHSUploadedDataset, pk=pk)
    if request.method == 'POST':
        try:
            if os.path.exists(ds.file_path):
                os.remove(ds.file_path)
        except OSError:
            pass
        label = str(ds)
        ds.delete()
        audit(request, 'DATA_DELETE', f'Deleted dataset: {label}')
        messages.success(request, f'Dataset {label} deleted.')
    return redirect('admin_dataset_upload')


# ──────────────────────────────────────────────────────────────
# USER MANAGEMENT
# ──────────────────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def user_list_view(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('-date_joined')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    page_obj = Paginator(users, 20).get_page(request.GET.get('page'))
    return render(request, 'admin/users/list.html', {'page_obj': page_obj, 'q': q})


@user_passes_test(admin_required, login_url='admin_login')
def user_create_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'report')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'admin/users/form.html', {'action': 'Create'})

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'admin/users/form.html', {'action': 'Create'})

        user = User.objects.create_user(username=username, email=email, password=password)
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()

        audit(request, 'USER_CREATE', f'Created user: {username} (role={role})')
        messages.success(request, f"User '{username}' created.")
        return redirect('admin_user_list')

    return render(request, 'admin/users/form.html', {'action': 'Create'})


@user_passes_test(admin_required, login_url='admin_login')
def user_edit_view(request, pk):
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        role = request.POST.get('role', 'report')
        password = request.POST.get('password', '').strip()

        target.email = request.POST.get('email', '').strip()
        target.is_staff = role == 'admin'
        target.is_superuser = role == 'admin'
        if password:
            target.set_password(password)
        target.save()

        audit(request, 'USER_UPDATE', f'Updated user: {target.username}')
        messages.success(request, f"User '{target.username}' updated.")
        return redirect('admin_user_list')

    return render(request, 'admin/users/form.html', {
        'action': 'Edit',
        'target_user': target,
        'role': 'admin' if target.is_staff else 'report',
    })


@user_passes_test(admin_required, login_url='admin_login')
def user_delete_view(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_user_list')
    if request.method == 'POST':
        name = target.username
        target.delete()
        audit(request, 'USER_DELETE', f'Deleted user: {name}')
        messages.success(request, f"User '{name}' deleted.")
    return redirect('admin_user_list')


@user_passes_test(admin_required, login_url='admin_login')
def user_toggle_active_view(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
    else:
        target.is_active = not target.is_active
        target.save()
        status = 'activated' if target.is_active else 'deactivated'
        audit(request, 'USER_UPDATE', f'User {status}: {target.username}')
        messages.success(request, f"User '{target.username}' {status}.")
    return redirect('admin_user_list')


# ──────────────────────────────────────────────────────────────
# AUDIT LOGS
# ──────────────────────────────────────────────────────────────

@user_passes_test(admin_required, login_url='admin_login')
def audit_log_view(request):
    logs = SystemAuditLog.objects.select_related('user').all()

    total_count = logs.count()
    success_count = logs.filter(success=True).count()
    failed_count = logs.filter(success=False).count()

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

    page_obj = Paginator(logs, 30).get_page(request.GET.get('page'))

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

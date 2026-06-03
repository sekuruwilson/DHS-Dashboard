from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Province, District
from .forms import ProvinceForm, DistrictForm

def admin_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

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
                next_url = request.GET.get('next', 'admin_dashboard')
                return redirect(next_url)
            else:
                context['error_message'] = "Access denied. Admin privileges required."
        else:
            context['error_message'] = "Invalid username or password."
            
    return render(request, 'admin/admin_login.html', context)

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

@user_passes_test(admin_required, login_url='admin_login')
def admin_dashboard_view(request):
    from .models import Category, Indicator, IndicatorValue, District
    context = {
        'total_chapters': Category.objects.count(),
        'total_indicators': Indicator.objects.count(),
        'total_values': IndicatorValue.objects.count(),
        'total_districts': District.objects.count(),
        'categories': Category.objects.all().order_by('name'), # For dropdown
    }
    return render(request, 'admin/dashboard.html', context)

from .models import Category
from .forms import CategoryForm
from django.shortcuts import get_object_or_404

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

from .models import Indicator
from .forms import IndicatorForm
from django.core.paginator import Paginator
from django.db.models import Q

@user_passes_test(admin_required, login_url='admin_login')
def indicator_list_admin_view(request):
    indicators = Indicator.objects.select_related('category').all().order_by('name')
    categories = Category.objects.all().order_by('name')
    
    # Filtering
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    
    if query:
        indicators = indicators.filter(name__icontains=query)
    if category_id:
        indicators = indicators.filter(category_id=category_id)
        
    # Pagination
    paginator = Paginator(indicators, 20) # Show 20 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
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

from .forms import DataValueForm
from .models import IndicatorValue

@user_passes_test(admin_required, login_url='admin_login')
def datavalue_list_view(request):
    values = IndicatorValue.objects.select_related('indicator', 'district').all()
    # Pagination
    paginator = Paginator(values, 50) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
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



@user_passes_test(admin_required, login_url='admin_login')
def location_list_view(request):
    provinces = Province.objects.prefetch_related('districts').all().order_by('name')
    districts = District.objects.select_related('province').all().order_by('name')
    return render(request, 'admin/locations/list.html', {
        'provinces': provinces,
        'districts': districts
    })

# --- Province Views ---
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

# --- District Views ---
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

from .forms import IndicatorJSONUploadForm, SingleIndicatorDataForm
from .models import District, Indicator, IndicatorValue, Category
import json
from django.http import JsonResponse

@user_passes_test(admin_required, login_url='admin_login')
def admin_add_data_view(request):
    manual_form = SingleIndicatorDataForm()
    upload_form = IndicatorJSONUploadForm()
    
    if request.method == 'POST':
        if 'manual_submit' in request.POST:
            manual_form = SingleIndicatorDataForm(request.POST)
            if manual_form.is_valid():
                indicator = manual_form.cleaned_data['indicator']
                district = manual_form.cleaned_data['district']
                data_label = manual_form.cleaned_data['data_label']
                year = manual_form.cleaned_data['year']
                value = manual_form.cleaned_data['value']
                
                # Use update_or_create to avoid duplicates
                IndicatorValue.objects.update_or_create(
                    indicator=indicator, district=district, data_label=data_label, year=year,
                    defaults={'value': value}
                )
                messages.success(request, f"Data updated for {indicator.name}")
                return redirect('admin_add_data')
                
        elif 'upload_submit' in request.POST:
            upload_form = IndicatorJSONUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                category = upload_form.cleaned_data['category']
                year = upload_form.cleaned_data['year']
                json_file = request.FILES['json_file']
                try:
                    data = json.load(json_file)
                    
                    # --- Phase 1: Dry-Run Validation ---
                    validation_errors = []
                    
                    if not isinstance(data, list) and not isinstance(data, dict):
                        validation_errors.append("Invalid structure: JSON must be a list of indicators or a single indicator object.")
                    
                    items_to_validate = [data] if isinstance(data, dict) else data
                    if not items_to_validate:
                        validation_errors.append("Invalid data: JSON file is empty.")
                        
                    for idx, item in enumerate(items_to_validate):
                        label_prefix = f"Record #{idx+1}"
                        
                        indicator_name = item.get('indicator')
                        if not indicator_name or not isinstance(indicator_name, str):
                            validation_errors.append(f"{label_prefix}: 'indicator' name is missing or invalid.")
                            continue
                            
                        # Check if indicator already exists in DB for this category and year
                        if Indicator.objects.filter(name__iexact=indicator_name, category=category, year=year).exists():
                            validation_errors.append(f"{label_prefix}: Indicator '{indicator_name}' already exists in category '{category}' for the year {year}. Upload aborted.")
                            continue
                            
                        label_prefix = f"Indicator '{indicator_name}'"
                        
                        indicator_data = item.get('data')
                        if indicator_data is None or not isinstance(indicator_data, dict):
                            validation_errors.append(f"{label_prefix}: 'data' object is missing or invalid.")
                            continue
                            
                        for dist_name, dist_val in indicator_data.items():
                            district = District.objects.filter(name=dist_name).first()
                            if not district:
                                validation_errors.append(f"{label_prefix}: Unrecognized location/district name '{dist_name}'.")
                                continue
                                
                            if isinstance(dist_val, dict):
                                for sub_label, sub_val in dist_val.items():
                                    try:
                                        float(sub_val)
                                    except (ValueError, TypeError):
                                        validation_errors.append(f"{label_prefix} ({dist_name}): Value for '{sub_label}' ({sub_val}) must be a number.")
                            else:
                                try:
                                    float(dist_val)
                                except (ValueError, TypeError):
                                    validation_errors.append(f"{label_prefix} ({dist_name}): Value ({dist_val}) must be a number.")
                                    
                    if validation_errors:
                        for err in validation_errors[:5]:
                            messages.error(request, err)
                        if len(validation_errors) > 5:
                            messages.error(request, f"... and {len(validation_errors) - 5} more validation errors. Upload aborted.")
                        return render(request, 'admin/data/add_data.html', {
                            'manual_form': manual_form,
                            'upload_form': upload_form
                        })
                        
                    # --- Phase 2: Transaction-Safe Database Writes ---
                    from django.db import transaction
                    
                    count = 0
                    with transaction.atomic():
                        for item in items_to_validate:
                            indicator_name = item.get('indicator')
                            unit = item.get('unit', 'Percentage (%)')
                            indicator_data = item.get('data', {})
                            
                            indicator, _ = Indicator.objects.get_or_create(
                                name=indicator_name, category=category, year=year,
                                defaults={'unit': unit}
                            )
                            
                            for dist_name, dist_val in indicator_data.items():
                                district = District.objects.filter(name=dist_name).first()
                                if not district:
                                    continue
                                
                                if isinstance(dist_val, dict):
                                    for label, val in dist_val.items():
                                        IndicatorValue.objects.update_or_create(
                                            indicator=indicator, district=district, data_label=label, year=year,
                                            defaults={'value': val}
                                        )
                                        count += 1
                                else:
                                    IndicatorValue.objects.update_or_create(
                                        indicator=indicator, district=district, data_label="Total", year=year,
                                        defaults={'value': dist_val}
                                    )
                                    count += 1
                    
                    messages.success(request, f"Successfully uploaded {count} data points from JSON.")
                    return redirect('admin_indicators')
                except json.JSONDecodeError as jde:
                    messages.error(request, f"Invalid JSON syntax: {str(jde)}")
                except Exception as e:
                    messages.error(request, f"Error processing upload: {str(e)}")
    
    return render(request, 'admin/data/add_data.html', {
        'manual_form': manual_form,
        'upload_form': upload_form
    })


# ── Report Builder ─────────────────────────────────────────────────────────────

DISTRICT_ORDER = ['Rwamagana','Nyagatare','Gatsibo','Kayonza','Kirehe','Ngoma','Bugesera','Eastern Province','Rwanda']

def _report_sort_key(name):
    try:
        return DISTRICT_ORDER.index(name)
    except ValueError:
        return 99

@user_passes_test(admin_required, login_url='admin_login')
def report_builder_view(request):
    categories = Category.objects.prefetch_related('indicators').all().order_by('name')
    all_years = sorted(Indicator.objects.values_list('year', flat=True).distinct(), reverse=True)
    return render(request, 'admin/report/builder.html', {
        'categories': categories,
        'all_years': all_years,
    })

@user_passes_test(admin_required, login_url='admin_login')
def report_indicator_data(request, pk):
    indicator = get_object_or_404(Indicator, pk=pk)
    year = request.GET.get('year')
    try:
        year = int(year) if year else indicator.year
    except (ValueError, TypeError):
        year = indicator.year

    if indicator.year != year:
        alt = Indicator.objects.filter(
            name=indicator.name, category=indicator.category, year=year
        ).first()
        if alt:
            indicator = alt

    values = indicator.values.filter(year=year).select_related('district')
    all_locations = sorted({v.district.name for v in values}, key=_report_sort_key)
    available_labels = sorted({v.data_label for v in values})

    datasets_map = {lbl: {loc: None for loc in all_locations} for lbl in available_labels}
    for val in values:
        datasets_map[val.data_label][val.district.name] = val.value

    datasets = [
        {'label': lbl, 'data': [datasets_map[lbl][loc] for loc in all_locations]}
        for lbl in available_labels
    ]
    table_rows = []
    for loc in all_locations:
        row = {'district': loc}
        for lbl in available_labels:
            row[lbl] = datasets_map.get(lbl, {}).get(loc)
        table_rows.append(row)

    return JsonResponse({
        'id': indicator.pk,
        'indicator_name': indicator.name,
        'category_name': str(indicator.category),
        'unit': indicator.unit,
        'year': year,
        'labels': all_locations,
        'datasets': datasets,
        'available_labels': available_labels,
        'table_rows': table_rows,
    })

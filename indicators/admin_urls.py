from django.urls import path
from . import admin_views

urlpatterns = [
    # Auth
    path('login/', admin_views.admin_login_view, name='admin_login'),
    path('logout/', admin_views.admin_logout_view, name='admin_logout'),
    
    # Dashboard
    path('', admin_views.admin_dashboard_view, name='admin_dashboard'),
    
    # Category Management
    path('categories/', admin_views.category_list_view, name='admin_categories'),
    path('categories/create/', admin_views.category_create_view, name='admin_category_create'),
    path('categories/update/<int:pk>/', admin_views.category_edit_view, name='admin_category_edit'),
    path('categories/delete/<int:pk>/', admin_views.category_delete_view, name='admin_category_delete'),
    
    # Indicator Management
    path('indicators/', admin_views.indicator_list_admin_view, name='admin_indicators'),
    path('indicators/create/', admin_views.indicator_create_view, name='admin_indicator_create'),
    path('indicators/update/<int:pk>/', admin_views.indicator_edit_view, name='admin_indicator_edit'),
    path('indicators/delete/<int:pk>/', admin_views.indicator_delete_view, name='admin_indicator_delete'),
    
    # Data Value Management
    path('data-values/', admin_views.datavalue_list_view, name='admin_datavalues'),
    path('data/add/', admin_views.admin_add_data_view, name='admin_add_data'),
    path('data-values/create/', admin_views.datavalue_create_view, name='admin_datavalue_create'),
    path('data-values/update/<int:pk>/', admin_views.datavalue_edit_view, name='admin_datavalue_edit'),
    path('data-values/delete/<int:pk>/', admin_views.datavalue_delete_view, name='admin_datavalue_delete'),
    
    # Location Management
    path('locations/', admin_views.location_list_view, name='admin_locations'),
    
    # Province CRUD
    path('locations/province/create/', admin_views.province_create_view, name='admin_province_create'),
    path('locations/province/edit/<int:pk>/', admin_views.province_edit_view, name='admin_province_edit'),
    path('locations/province/delete/<int:pk>/', admin_views.province_delete_view, name='admin_province_delete'),

    # District CRUD
    path('locations/district/create/', admin_views.district_create_view, name='admin_district_create'),
    path('locations/district/edit/<int:pk>/', admin_views.district_edit_view, name='admin_district_edit'),
    path('locations/district/delete/<int:pk>/', admin_views.district_delete_view, name='admin_district_delete'),
]

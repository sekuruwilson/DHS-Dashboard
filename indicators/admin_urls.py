from django.urls import path
from . import admin_views

urlpatterns = [
    # Auth
    path('login/', admin_views.admin_login_view, name='admin_login'),
    path('logout/', admin_views.admin_logout_view, name='admin_logout'),

    # Dashboard
    path('', admin_views.admin_dashboard_view, name='admin_dashboard'),

    # ── Dataset Management ─────────────────────────
    path('datasets/', admin_views.dataset_upload_view, name='admin_dataset_upload'),
    path('datasets/delete/<int:pk>/', admin_views.dataset_delete_view, name='admin_dataset_delete'),
    path('datasets/variables/', admin_views.dataset_variables_view, name='admin_dataset_variables'),

    # ── Indicator Calculator ───────────────────────
    path('compute/', admin_views.indicator_calculate_view, name='admin_indicator_calculate'),
    path('compute/run/', admin_views.indicator_run_view, name='admin_indicator_run'),

    # ── Category Management ────────────────────────
    path('categories/', admin_views.category_list_view, name='admin_categories'),
    path('categories/create/', admin_views.category_create_view, name='admin_category_create'),
    path('categories/update/<int:pk>/', admin_views.category_edit_view, name='admin_category_edit'),
    path('categories/delete/<int:pk>/', admin_views.category_delete_view, name='admin_category_delete'),

    # ── Indicator Management ───────────────────────
    path('indicators/', admin_views.indicator_list_admin_view, name='admin_indicators'),
    path('indicators/create/', admin_views.indicator_create_view, name='admin_indicator_create'),
    path('indicators/update/<int:pk>/', admin_views.indicator_edit_view, name='admin_indicator_edit'),
    path('indicators/delete/<int:pk>/', admin_views.indicator_delete_view, name='admin_indicator_delete'),

    # ── Data Value Management ──────────────────────
    path('data-values/', admin_views.datavalue_list_view, name='admin_datavalues'),
    path('data-values/create/', admin_views.datavalue_create_view, name='admin_datavalue_create'),
    path('data-values/update/<int:pk>/', admin_views.datavalue_edit_view, name='admin_datavalue_edit'),
    path('data-values/delete/<int:pk>/', admin_views.datavalue_delete_view, name='admin_datavalue_delete'),

    # ── Location Management ────────────────────────
    path('locations/', admin_views.location_list_view, name='admin_locations'),
    path('locations/province/create/', admin_views.province_create_view, name='admin_province_create'),
    path('locations/province/edit/<int:pk>/', admin_views.province_edit_view, name='admin_province_edit'),
    path('locations/province/delete/<int:pk>/', admin_views.province_delete_view, name='admin_province_delete'),
    path('locations/district/create/', admin_views.district_create_view, name='admin_district_create'),
    path('locations/district/edit/<int:pk>/', admin_views.district_edit_view, name='admin_district_edit'),
    path('locations/district/delete/<int:pk>/', admin_views.district_delete_view, name='admin_district_delete'),

    # ── User Management ────────────────────────────
    path('users/', admin_views.user_list_view, name='admin_user_list'),
    path('users/create/', admin_views.user_create_view, name='admin_user_create'),
    path('users/edit/<int:pk>/', admin_views.user_edit_view, name='admin_user_edit'),
    path('users/delete/<int:pk>/', admin_views.user_delete_view, name='admin_user_delete'),
    path('users/toggle/<int:pk>/', admin_views.user_toggle_active_view, name='admin_user_toggle'),

    # ── Audit Logs ─────────────────────────────────
    path('audit-logs/', admin_views.audit_log_view, name='admin_audit_logs'),
]

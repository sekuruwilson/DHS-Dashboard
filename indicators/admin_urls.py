from django.urls import path
from . import admin_views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────
    path('login/',  admin_views.admin_login_view,  name='admin_login'),
    path('logout/', admin_views.admin_logout_view, name='admin_logout'),

    # ── Dashboard ─────────────────────────────────────
    path('', admin_views.admin_dashboard_view, name='admin_dashboard'),

    # ── Dataset Upload ────────────────────────────────
    path('datasets/',                          admin_views.dataset_upload_view,  name='admin_dataset_upload'),
    path('datasets/delete/<int:pk>/',          admin_views.dataset_delete_view,  name='admin_dataset_delete'),
    path('datasets/compute/<int:year>/',       admin_views.dataset_compute_view, name='admin_dataset_compute'),

    # ── User Management ───────────────────────────────
    path('users/',                admin_views.user_list_view,         name='admin_user_list'),
    path('users/create/',         admin_views.user_create_view,       name='admin_user_create'),
    path('users/edit/<int:pk>/',  admin_views.user_edit_view,         name='admin_user_edit'),
    path('users/delete/<int:pk>/',admin_views.user_delete_view,       name='admin_user_delete'),
    path('users/toggle/<int:pk>/',admin_views.user_toggle_active_view,name='admin_user_toggle'),

    # ── Audit Logs ────────────────────────────────────
    path('audit-logs/', admin_views.audit_log_view, name='admin_audit_logs'),
]

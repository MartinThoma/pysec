"""URL configuration for pysec server app."""

from django.urls import path

from . import views

app_name = "server"

urlpatterns = [
    # Web interface
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("client/<int:client_id>/", views.client_detail, name="client_detail"),
    # Client API endpoints (with trailing slash)
    path("api/audit-log/", views.AuditLogAPI.as_view(), name="api_audit_log"),
    path("api/packages/", views.PackagesAPI.as_view(), name="api_packages_submit"),
    path(
        "api/security-info/",
        views.SecurityInfoAPI.as_view(),
        name="api_security_info",
    ),
    # Client API endpoints (without trailing slash for backward compatibility)
    path("api/audit-log", views.AuditLogAPI.as_view(), name="api_audit_log_no_slash"),
    path(
        "api/packages",
        views.PackagesAPI.as_view(),
        name="api_packages_submit_no_slash",
    ),
    path(
        "api/security-info",
        views.SecurityInfoAPI.as_view(),
        name="api_security_info_no_slash",
    ),
    # Admin API endpoints
    path("api/clients/", views.api_clients, name="api_clients"),
    path("api/audit-logs/", views.api_audit_logs, name="api_audit_logs"),
    path("api/packages-list/", views.api_packages, name="api_packages_list"),
    path(
        "api/security-info-list/",
        views.api_security_info,
        name="api_security_info_list",
    ),
]

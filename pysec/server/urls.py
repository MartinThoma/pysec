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
    # Client API endpoints
    path("api/audit-log/", views.AuditLogAPIView.as_view(), name="api_audit_log"),
    path("api/packages/", views.PackagesAPIView.as_view(), name="api_packages_submit"),
    path(
        "api/security-info/",
        views.SecurityInfoAPIView.as_view(),
        name="api_security_info",
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

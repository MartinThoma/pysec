"""Django admin for pysec server."""

from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest

from .models import AuditLog, Client, Package, SecurityInfo


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin interface for Client model."""

    list_display = ["name", "token_preview", "created_at", "last_seen"]
    list_filter = ["created_at", "last_seen"]
    search_fields = ["name"]
    readonly_fields = ["created_at"]
    fields = ["name", "token", "created_at", "last_seen"]

    def token_preview(self, obj: Client) -> str:
        """Show preview of token."""
        return f"{obj.token[:16]}..." if obj.token else "No token"

    token_preview.short_description = "Token"  # type: ignore[attr-defined]

    def get_form(
        self, request: HttpRequest, obj: Client | None = None, **kwargs
    ) -> type[ModelForm[Client]]:
        """Customize the form to show token help text."""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields[
            "token"
        ].help_text = "Leave blank to auto-generate a secure token"
        return form


AUDIT_LOG_MAX_LENGTH = 100


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""

    list_display = ["client", "timestamp", "event_preview", "created_at"]
    list_filter = ["timestamp", "created_at", "client"]
    search_fields = ["client__name", "event"]
    readonly_fields = ("created_at",)

    def event_preview(self, obj: AuditLog) -> str:
        """Show preview of event text."""
        return (
            obj.event[:100] + "..."
            if len(obj.event) > AUDIT_LOG_MAX_LENGTH
            else obj.event
        )

    event_preview.short_description = "Event"  # type: ignore[attr-defined]


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Admin interface for Package model."""

    list_display = ["name", "version", "client", "submitted_at"]
    list_filter = ["submitted_at", "client"]
    search_fields = ["name", "version", "client__name"]
    readonly_fields = ["submitted_at"]


@admin.register(SecurityInfo)
class SecurityInfoAdmin(admin.ModelAdmin):
    """Admin interface for SecurityInfo model."""

    list_display = [
        "client",
        "disk_encrypted",
        "screen_lock_timeout",
        "auto_updates_enabled",
        "os_checker_available",
        "submitted_at",
    ]
    list_filter = [
        "disk_encrypted",
        "auto_updates_enabled",
        "os_checker_available",
        "submitted_at",
        "client",
    ]
    search_fields = ["client__name", "error"]
    readonly_fields = ["submitted_at"]

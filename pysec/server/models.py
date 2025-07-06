"""Django models for pysec server."""

import secrets
import string

from django.db import models
from django.utils import timezone


def generate_client_token() -> str:
    """Generate a secure random token for client authentication."""
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(64))


class Client(models.Model):
    """Client model for storing client information."""

    name = models.CharField(max_length=255, unique=True)
    token = models.CharField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "clients"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        """Override save to generate token automatically if not provided."""
        if not self.token:
            self.token = generate_client_token()
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """Audit log model for storing client audit events."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    event = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "audit_logs"
        ordering = ("-timestamp",)

    def __str__(self) -> str:
        return f"{self.client.name} - {self.timestamp}"


class Package(models.Model):
    """Package model for storing client package information."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "packages"
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} {self.version}"


class SecurityInfo(models.Model):
    """Security information model for storing client security settings."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    disk_encrypted = models.BooleanField(null=True, blank=True)
    screen_lock_timeout = models.IntegerField(null=True, blank=True)
    auto_updates_enabled = models.BooleanField(null=True, blank=True)
    os_checker_available = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)  # noqa: DJ001
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "security_info"
        ordering = ("-submitted_at",)

    def __str__(self) -> str:
        return f"Security info for {self.client.name}"

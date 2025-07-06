"""Define the Django application configuration for the pysec server."""

from django.apps import AppConfig


class ServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pysec.server"

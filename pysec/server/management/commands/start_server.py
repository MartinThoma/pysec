"""Django management command to start the pysec server."""

from argparse import ArgumentParser

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Start the pysec Django server."""

    help = "Start the pysec Django server"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host to bind the server to (default: 127.0.0.1)",
        )
        parser.add_argument(
            "--port",
            default="8000",
            help="Port to bind the server to (default: 8000)",
        )

    def handle(self, **options) -> None:
        host = options["host"]
        port = options["port"]

        self.stdout.write(
            self.style.SUCCESS(f"Starting pysec Django server on {host}:{port}"),
        )
        self.stdout.write(
            self.style.WARNING(f"Access the dashboard at: http://{host}:{port}/"),
        )
        self.stdout.write(
            self.style.WARNING(f"Access the admin at: http://{host}:{port}/admin/"),
        )

        # Use Django's runserver command
        call_command("runserver", f"{host}:{port}")

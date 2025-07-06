"""Django management command to create a new client."""

from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from pysec.server.auth import generate_client_token
from pysec.server.models import Client


class Command(BaseCommand):
    """Create a new client with token."""

    help = "Create a new client with authentication token"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "name",
            help="Name of the client to create",
        )

    def handle(self, **options) -> None:
        name = options["name"]

        # Check if client already exists
        if Client.objects.filter(name=name).exists():
            self.stdout.write(
                self.style.ERROR(f'Client "{name}" already exists'),
            )
            return

        # Generate token and create client
        token = generate_client_token()
        client = Client.objects.create(name=name, token=token)

        self.stdout.write(
            self.style.SUCCESS(f'Client "{name}" created successfully'),
        )
        self.stdout.write(f"Client ID: {client.pk}")
        self.stdout.write(f"Token: {token}")
        self.stdout.write(
            self.style.WARNING("Save this token securely - it will not be shown again!"),
        )

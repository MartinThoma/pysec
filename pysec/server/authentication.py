"""Custom authentication for pysec server."""

from datetime import datetime, timezone
from typing import Any

from django.http import HttpRequest
from rest_framework import authentication, exceptions

from .models import Client


class ClientUser:
    """Wrapper class to make Client compatible with DRF authentication."""

    def __init__(self, client: Client) -> None:
        self.client = client
        # Add required attributes for DRF
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Delegate any other attribute access to the wrapped client."""
        return getattr(self.client, name)


class ClientTokenAuthentication(authentication.BaseAuthentication):
    """Custom authentication class for client token authentication."""

    def authenticate(self, request: HttpRequest) -> tuple[ClientUser, str] | None:
        """Authenticate using client token from Authorization header."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        try:
            client = Client.objects.get(token=token)

            # Update last seen only if it's been more than 1 minute since last update
            # to avoid database lock issues with rapid requests
            now = datetime.now(timezone.utc)
            if client.last_seen is None or (now - client.last_seen).total_seconds() > 60:  # noqa: PLR2004
                client.last_seen = now
                client.save()

            # Return (user, auth) tuple with wrapped client
            return (ClientUser(client), token)

        except Client.DoesNotExist as err:
            raise exceptions.AuthenticationFailed("Invalid token") from err

    def authenticate_header(self, request: HttpRequest) -> str:  # noqa: ARG002
        """Return the authentication header."""
        return "Bearer"

"""DRF Spectacular extensions for pysec server."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from drf_spectacular.openapi import AutoSchema

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ClientTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    """OpenAPI authentication extension for ClientTokenAuthentication."""

    target_class = "pysec.server.authentication.ClientTokenAuthentication"
    name = "ClientTokenAuth"
    priority = 0

    def get_security_definition(self, _auto_schema: "AutoSchema") -> dict[str, str]:
        """Define the security scheme for client token authentication."""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Token",
            "description": "Client token authentication using Bearer token",
        }

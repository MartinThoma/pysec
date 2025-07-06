"""Django REST Framework serializers for pysec server."""

from typing import Any

from rest_framework import serializers

from .models import AuditLog, Client, Package, SecurityInfo


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model."""

    class Meta:
        model = Client
        fields = ["id", "name", "token", "created_at", "last_seen"]
        read_only_fields = ["id", "token", "created_at", "last_seen"]


class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new clients."""

    class Meta:
        model = Client
        fields = ["id", "name", "token", "created_at"]
        read_only_fields = ["id", "token", "created_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""

    client_id = serializers.IntegerField(source="client.id", read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "client_id", "timestamp", "event", "created_at"]
        read_only_fields = ["id", "client_id", "created_at"]


class AuditLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating audit logs."""

    class Meta:
        model = AuditLog
        fields = ["timestamp", "event"]

    def create(self, validated_data: dict[str, Any]) -> AuditLog:
        """Create audit log with client from context."""
        validated_data["client"] = self.context["client"]
        return super().create(validated_data)


class PackageSerializer(serializers.ModelSerializer):
    """Serializer for Package model."""

    client_id = serializers.IntegerField(source="client.id", read_only=True)

    class Meta:
        model = Package
        fields = ["id", "client_id", "name", "version", "submitted_at"]
        read_only_fields = ["id", "client_id", "submitted_at"]


class PackagesListSerializer(serializers.Serializer):
    """Serializer for bulk package creation."""

    packages = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            required=True,
        ),
        allow_empty=True,
    )

    def validate_packages(self, value: list[dict[str, str]]) -> list[dict[str, str]]:
        """Validate package list structure."""
        for pkg in value:
            if "name" not in pkg or "version" not in pkg:
                raise serializers.ValidationError(
                    "Each package must have 'name' and 'version' fields"
                )
        return value

    def create(self, validated_data: dict[str, Any]) -> dict[str, str]:
        """Create packages with client from context."""
        client = self.context["client"]
        packages = validated_data["packages"]

        # Remove existing packages for this client
        Package.objects.filter(client=client).delete()

        # Bulk create new packages
        package_objects = [
            Package(
                client=client,
                name=pkg["name"],
                version=pkg["version"],
            )
            for pkg in packages
        ]

        Package.objects.bulk_create(package_objects, batch_size=1000)
        return {"status": "success"}


class SecurityInfoSerializer(serializers.ModelSerializer):
    """Serializer for SecurityInfo model."""

    client_id = serializers.IntegerField(source="client.id", read_only=True)

    class Meta:
        model = SecurityInfo
        fields = [
            "id",
            "client_id",
            "disk_encrypted",
            "screen_lock_timeout",
            "auto_updates_enabled",
            "os_checker_available",
            "error",
            "submitted_at",
        ]
        read_only_fields = ["id", "client_id", "submitted_at"]


class SecurityInfoCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating security info."""

    class Meta:
        model = SecurityInfo
        fields = [
            "disk_encrypted",
            "screen_lock_timeout",
            "auto_updates_enabled",
            "os_checker_available",
            "error",
        ]

    def create(self, validated_data: dict[str, Any]) -> SecurityInfo:
        """Create security info with client from context."""
        client = self.context["client"]

        # Remove existing security info for this client
        SecurityInfo.objects.filter(client=client).delete()

        # Create new security info
        validated_data["client"] = client
        return super().create(validated_data)

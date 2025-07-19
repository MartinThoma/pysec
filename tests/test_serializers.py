"""Tests for pysec server serializers."""

from pysec.server.serializers import PackagesListSerializer


def test_validate_packages_valid_data() -> None:
    """Test validate_packages with valid package data."""
    valid_packages = [
        {
            "name": "requests",
            "version": "2.28.1",
            "package_repository": "PYTHON_PIP",
        },
        {
            "name": "django",
            "version": "4.2.0",
            "package_repository": "PYTHON_PIP",
        },
        {
            "name": "nginx",
            "version": "1.20.1",
            "package_repository": "APT",
        },
    ]

    data = {"packages": valid_packages}
    serializer = PackagesListSerializer(data=data)

    assert serializer.is_valid() is True
    assert serializer.validated_data["packages"] == valid_packages
    assert len(serializer.validated_data["packages"]) == 3  # noqa: PLR2004


def test_validate_packages_empty_list() -> None:
    """Test validate_packages with an empty list."""
    data = {"packages": []}
    serializer = PackagesListSerializer(data=data)

    assert serializer.is_valid() is True
    assert serializer.validated_data["packages"] == []
    assert len(serializer.validated_data["packages"]) == 0


def test_validate_packages_missing_name_field() -> None:
    """Test validate_packages raises ValidationError when 'name' field is missing."""
    invalid_packages = [
        {
            "version": "2.28.1",
            "package_repository": "PYTHON_PIP",
        },
    ]

    data = {"packages": invalid_packages}
    serializer = PackagesListSerializer(data=data)

    assert serializer.is_valid() is False
    assert "packages" in serializer.errors
    assert (
        "Each package must have 'name', 'version', and 'package_repository' fields"
        in str(serializer.errors["packages"])
    )


def test_validate_packages_missing_version_field() -> None:
    """Test validate_packages raises ValidationError when 'version' field is missing."""
    invalid_packages = [
        {
            "name": "requests",
            "package_repository": "PYTHON_PIP",
        },
    ]

    data = {"packages": invalid_packages}
    serializer = PackagesListSerializer(data=data)

    assert serializer.is_valid() is False
    assert "packages" in serializer.errors
    assert (
        "Each package must have 'name', 'version', and 'package_repository' fields"
        in str(serializer.errors["packages"])
    )


def test_validate_packages_missing_package_repository_field() -> None:
    """Test validate_packages raises error when 'package_repository' is missing."""
    invalid_packages = [
        {
            "name": "requests",
            "version": "2.28.1",
        },
    ]

    data = {"packages": invalid_packages}
    serializer = PackagesListSerializer(data=data)

    assert serializer.is_valid() is False
    assert "packages" in serializer.errors
    assert (
        "Each package must have 'name', 'version', and 'package_repository' fields"
        in str(serializer.errors["packages"])
    )

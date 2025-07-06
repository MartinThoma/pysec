"""Tests for server and client functionality."""

import json
import os
import tempfile

import pytest
from django.contrib.auth.models import User
from django.test import Client as DjangoTestClient
from rest_framework import status

from pysec.client import ClientConfig
from pysec.config import get_client_config_file
from pysec.server.auth import CLIENT_TOKEN_LENGHT
from pysec.server.models import AuditLog, Client, Package, SecurityInfo

TEST_TOKEN_VALUE = "test-token"  # noqa: S105


@pytest.fixture
def test_client() -> DjangoTestClient:
    """Create Django test client."""
    return DjangoTestClient()


@pytest.fixture
def admin_user(db) -> User:
    """Create admin user for testing."""
    return User.objects.create_user(username="admin", password="testpass123")  # noqa: S106


@pytest.fixture
def test_auth_client(db) -> Client:
    """Create test client with known token."""
    return Client.objects.create(name="test-client", token=TEST_TOKEN_VALUE)


@pytest.mark.django_db
def test_client_model() -> None:
    """Test Django Client model functionality."""
    # Test creating a client
    client = Client.objects.create(name="test-client", token=TEST_TOKEN_VALUE)
    assert client.name == "test-client"
    assert client.token == TEST_TOKEN_VALUE

    # Test getting client by token
    found_client = Client.objects.filter(token=TEST_TOKEN_VALUE).first()
    assert found_client is not None
    assert found_client.name == "test-client"

    # Test getting client by name
    found_client = Client.objects.filter(name="test-client").first()
    assert found_client is not None
    assert found_client.token == TEST_TOKEN_VALUE

    # Test auto-generation of token
    client_auto = Client.objects.create(name="auto-token-client")
    assert client_auto.token != ""
    assert len(client_auto.token) == CLIENT_TOKEN_LENGHT


@pytest.mark.django_db
def test_package_model() -> None:
    """Test Django Package model functionality."""
    client = Client.objects.create(name="test-client")

    # Test creating packages
    package1 = Package.objects.create(client=client, name="requests", version="2.25.1")
    _package2 = Package.objects.create(client=client, name="django", version="4.2.0")

    assert package1.client == client
    assert package1.name == "requests"
    assert package1.version == "2.25.1"

    # Test querying packages
    packages = Package.objects.filter(client=client).order_by("name")
    assert len(packages) == 2  # noqa: PLR2004
    assert packages[0].name == "django"
    assert packages[1].name == "requests"


@pytest.mark.django_db
def test_security_info_model() -> None:
    """Test Django SecurityInfo model functionality."""
    client = Client.objects.create(name="test-client")

    # Test creating security info
    security_info = SecurityInfo.objects.create(
        client=client,
        disk_encrypted=True,
        screen_lock_timeout=15,
        auto_updates_enabled=True,
        os_checker_available=True,
    )

    assert security_info.client == client
    assert security_info.disk_encrypted is True
    assert security_info.screen_lock_timeout == 15  # noqa: PLR2004
    assert security_info.auto_updates_enabled is True
    assert security_info.os_checker_available is True


def test_client_config() -> None:
    """Test client configuration save/load."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock XDG_CONFIG_HOME environment variable
        original_env = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = temp_dir

        try:
            # Test saving config
            config = ClientConfig(
                server_url="http://localhost:8000",
                token=TEST_TOKEN_VALUE,  # noaq: S106
            )
            config.save()
            config_file = get_client_config_file()
            assert config_file.exists()

            # Test loading config
            config = ClientConfig.load()
            assert config is not None
            assert config.server_url == "http://localhost:8000"
            assert config.token == TEST_TOKEN_VALUE

        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["XDG_CONFIG_HOME"] = original_env
            elif "XDG_CONFIG_HOME" in os.environ:
                del os.environ["XDG_CONFIG_HOME"]


@pytest.mark.django_db
def test_server_login(test_client: DjangoTestClient, admin_user: User) -> None:
    """Test server login functionality."""
    # Test GET login page
    response = test_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert b"PySec" in response.content

    # Test redirect to login
    response = test_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert b"Login" in response.content

    # Test POST login with incorrect credentials
    response = test_client.post(
        "/login/",
        data={"username": "admin", "password": "wrongpass"},
    )
    assert response.status_code == status.HTTP_200_OK  # Should stay on login page
    assert b"Login" in response.content

    # Test POST login with correct credentials
    response = test_client.post(
        "/login/",
        data={"username": "admin", "password": "testpass123"},
    )
    assert response.status_code == status.HTTP_302_FOUND  # Redirect on successful login

    # Test after already logged in
    response = test_client.get("/")
    assert response.status_code == status.HTTP_302_FOUND
    assert b"Login" not in response.content


@pytest.mark.django_db
def test_api_endpoints_require_auth(test_client: DjangoTestClient) -> None:
    """Test that API endpoints require authentication."""
    # Test client API without auth
    response = test_client.get("/api/audit-log/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = test_client.post(
        "/api/packages/",
        data='{"packages": []}',
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Test admin API without login (these require admin login, not client token)
    response = test_client.get("/api/clients/")
    assert response.status_code == status.HTTP_302_FOUND  # Redirect to login


@pytest.mark.django_db
def test_api_endpoints_return_json(test_client: DjangoTestClient) -> None:
    """Test that API endpoints always return JSON responses."""
    # Test unauthenticated client API request returns JSON error
    response = test_client.get("/api/audit-log/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("content-type") == "application/json"
    data = response.json()
    assert "error" in data

    # Test invalid API endpoint returns Django 404
    response = test_client.get("/api/nonexistent/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_web_ui_returns_html(test_client: DjangoTestClient) -> None:
    """Test that web UI endpoints return HTML responses."""
    # Test login page returns HTML
    response = test_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")
    assert b"PySec" in response.content


@pytest.mark.django_db
def test_security_info_endpoint_without_auth(test_client: DjangoTestClient) -> None:
    """Test security information endpoint requires authentication."""
    # Test submitting security info without authentication
    security_data = {
        "disk_encrypted": True,
        "screen_lock_timeout": 15,
        "auto_updates_enabled": True,
        "os_checker_available": True,
    }

    response = test_client.post(
        "/api/security-info/",
        data=json.dumps(security_data),
        content_type="application/json",
    )

    # Should return 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Should return JSON error
    assert response.headers.get("content-type") == "application/json"
    data = response.json()
    assert "error" in data


@pytest.mark.django_db
def test_security_info_endpoint(
    test_client: DjangoTestClient,
    admin_user: User,
    test_auth_client: Client,
) -> None:
    """Test security information submission endpoint."""
    # Login as admin
    test_client.force_login(admin_user)

    # Test submitting security info with client token
    security_data = {
        "disk_encrypted": True,
        "screen_lock_timeout": 15,
        "auto_updates_enabled": True,
        "os_checker_available": True,
    }

    response = test_client.post(
        "/api/security-info/",
        data=json.dumps(security_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {TEST_TOKEN_VALUE}",
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["status"] == "success"

    # Verify security info was saved
    security_info = SecurityInfo.objects.filter(client=test_auth_client).first()
    assert security_info is not None
    assert security_info.disk_encrypted is True
    assert security_info.screen_lock_timeout == 15  # noqa: PLR2004
    assert security_info.auto_updates_enabled is True
    assert security_info.os_checker_available is True


@pytest.mark.django_db
def test_audit_log_endpoint(
    test_client: DjangoTestClient,
    test_auth_client: Client,
) -> None:
    """Test audit log submission endpoint."""
    audit_data = {
        "timestamp": "2023-01-01T12:00:00Z",
        "event": "test audit event",
    }

    response = test_client.post(
        "/api/audit-log/",
        data=json.dumps(audit_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {TEST_TOKEN_VALUE}",
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["status"] == "success"

    # Verify audit log was saved
    audit_log = AuditLog.objects.filter(client=test_auth_client).first()
    assert audit_log is not None
    assert audit_log.event == "test audit event"


@pytest.mark.django_db
def test_packages_endpoint(
    test_client: DjangoTestClient,
    test_auth_client: Client,
) -> None:
    """Test packages submission endpoint."""
    packages_data = {
        "packages": [
            {"name": "requests", "version": "2.25.1"},
            {"name": "django", "version": "4.2.0"},
        ],
    }

    response = test_client.post(
        "/api/packages/",
        data=json.dumps(packages_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {TEST_TOKEN_VALUE}",
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["status"] == "success"

    # Verify packages were saved
    packages = Package.objects.filter(client=test_auth_client).order_by("name")
    assert len(packages) == 2  # noqa: PLR2004
    assert packages[0].name == "django"
    assert packages[0].version == "4.2.0"
    assert packages[1].name == "requests"
    assert packages[1].version == "2.25.1"


@pytest.mark.django_db
def test_dashboard_view(test_client: DjangoTestClient, admin_user: User) -> None:
    """Test dashboard view."""
    # Create some test clients
    Client.objects.create(name="client1")
    Client.objects.create(name="client2")

    # Login and access dashboard
    test_client.force_login(admin_user)
    response = test_client.get("/dashboard/")

    assert response.status_code == status.HTTP_200_OK
    assert b"client1" in response.content
    assert b"client2" in response.content


@pytest.mark.django_db
def test_admin_api_clients(test_client: DjangoTestClient, admin_user: User) -> None:
    """Test admin API for clients management."""
    # Login as admin
    test_client.force_login(admin_user)

    # Test GET clients
    response = test_client.get("/api/clients/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    # Test POST to create client
    response = test_client.post(
        "/api/clients/",
        data=json.dumps({"name": "test-client-api"}),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test-client-api"
    assert "token" in data
    assert "id" in data


@pytest.mark.django_db
def test_client_detail_view(test_client: DjangoTestClient, admin_user: User) -> None:
    """Test client detail view."""
    # Create test client with data
    client = Client.objects.create(name="test-client")
    Package.objects.create(client=client, name="requests", version="2.25.1")
    SecurityInfo.objects.create(client=client, disk_encrypted=True)

    # Login and access client detail
    test_client.force_login(admin_user)
    response = test_client.get(f"/client/{client.pk}/")

    assert response.status_code == status.HTTP_200_OK
    assert b"test-client" in response.content
    assert b"requests" in response.content

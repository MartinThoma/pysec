"""Django views for pysec server."""

import json
from datetime import datetime, timezone

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseBase, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import AuditLog, Client, Package, SecurityInfo


def index(request: HttpRequest) -> HttpResponse:
    """Home page."""
    if request.user.is_authenticated:
        return redirect("server:dashboard")
    return render(request, "server/login.html")


@require_http_methods(["POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """Login endpoint."""
    username = request.POST.get("username")
    password = request.POST.get("password")

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect("server:dashboard")
    return render(request, "server/login.html", {"error": "Invalid credentials"})


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard page."""
    clients = Client.objects.all().order_by("-created_at")
    return render(request, "server/dashboard.html", {"clients": clients})


@login_required
def client_detail(request: HttpRequest, client_id: int) -> HttpResponse:
    """Client detail page."""
    client = get_object_or_404(Client, id=client_id)
    audit_logs = AuditLog.objects.filter(client=client).order_by("-timestamp")
    packages = Package.objects.filter(client=client).order_by("name")
    security_info = SecurityInfo.objects.filter(client=client).order_by("-submitted_at")

    return render(
        request,
        "server/client_detail.html",
        {
            "client": client,
            "audit_logs": audit_logs,
            "packages": packages,
            "security_info": security_info,
        },
    )


# API Views for client communication


@method_decorator(csrf_exempt, name="dispatch")
class APIView(View):
    """Base API view with client token authentication."""

    def dispatch(
        self,
        request: HttpRequest,
        *args,
        **kwargs,
    ) -> HttpResponseBase:
        # Check for client token authentication
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Authentication required"}, status=401)

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        try:
            self.client = Client.objects.get(token=token)
            # Update last seen only if it's been more than 1 minute since last update
            # to avoid database lock issues with rapid requests
            now = datetime.now(timezone.utc)
            if (
                self.client.last_seen is None
                or (now - self.client.last_seen).total_seconds() > 60  # noqa: PLR2004
            ):
                self.client.last_seen = now
                self.client.save()
        except Client.DoesNotExist:
            return JsonResponse({"error": "Invalid token"}, status=401)

        return super().dispatch(request, *args, **kwargs)


class AuditLogAPI(APIView):
    """API endpoint for audit log submission."""

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data = json.loads(request.body)
            timestamp_str = data.get("timestamp")
            event = data.get("event")

            if not timestamp_str or not event:
                return JsonResponse({"error": "Missing timestamp or event"}, status=400)

            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            AuditLog.objects.create(
                client=self.client,
                timestamp=timestamp,
                event=event,
            )

            return JsonResponse({"status": "success"})

        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({"error": f"Invalid data: {e!s}"}, status=400)


class PackagesAPI(APIView):
    """API endpoint for package list submission."""

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data = json.loads(request.body)
            packages = data.get("packages", [])

            # Remove existing packages for this client
            Package.objects.filter(client=self.client).delete()

            # Bulk create packages for better performance
            package_objects = [
                Package(
                    client=self.client,
                    name=pkg["name"],
                    version=pkg["version"],
                )
                for pkg in packages
            ]

            # Use bulk_create for much better performance with large datasets
            Package.objects.bulk_create(package_objects, batch_size=1000)

            return JsonResponse({"status": "success"})

        except (json.JSONDecodeError, KeyError) as e:
            return JsonResponse({"error": f"Invalid data: {e!s}"}, status=400)


class SecurityInfoAPI(APIView):
    """API endpoint for security information submission."""

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            data = json.loads(request.body)

            # Remove existing security info for this client
            SecurityInfo.objects.filter(client=self.client).delete()

            # Create new security info
            SecurityInfo.objects.create(
                client=self.client,
                disk_encrypted=data.get("disk_encrypted"),
                screen_lock_timeout=data.get("screen_lock_timeout"),
                auto_updates_enabled=data.get("auto_updates_enabled"),
                os_checker_available=data.get("os_checker_available", False),
                error=data.get("error"),
            )

            return JsonResponse({"status": "success"})

        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({"error": f"Invalid data: {e!s}"}, status=400)


# Admin API Views


@login_required
def api_clients(request: HttpRequest) -> JsonResponse:
    """API endpoint to list clients."""
    if request.method == "POST":
        # Create new client
        try:
            data = json.loads(request.body)
            name = data.get("name")

            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)

            # Generate token using the model's generate_client_token function
            client = Client.objects.create(name=name)

            return JsonResponse(
                {
                    "id": client.pk,
                    "name": client.name,
                    "token": client.token,
                    "created_at": client.created_at.isoformat(),
                },
            )

        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({"error": f"Invalid data: {e!s}"}, status=400)

    else:  # GET
        clients = Client.objects.all()
        return JsonResponse(
            [
                {
                    "id": client.pk,
                    "name": client.name,
                    "created_at": client.created_at.isoformat(),
                    "last_seen": client.last_seen.isoformat()
                    if client.last_seen
                    else None,
                }
                for client in clients
            ],
            safe=False,
        )


@login_required
def api_audit_logs(request: HttpRequest) -> JsonResponse:
    """API endpoint to get audit logs."""
    client_id = request.GET.get("client_id")

    logs = AuditLog.objects.all()
    if client_id:
        logs = logs.filter(client_id=client_id)

    logs = logs.order_by("-timestamp")

    return JsonResponse(
        [
            {
                "id": log.pk,
                "client_id": log.client.pk,
                "timestamp": log.timestamp.isoformat(),
                "event": log.event,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        safe=False,
    )


@login_required
def api_packages(request: HttpRequest) -> JsonResponse:
    """API endpoint to get packages."""
    client_id = request.GET.get("client_id")

    packages = Package.objects.all()
    if client_id:
        packages = packages.filter(client_id=client_id)

    packages = packages.order_by("name")

    return JsonResponse(
        [
            {
                "id": package.pk,
                "client_id": package.client.pk,
                "name": package.name,
                "version": package.version,
                "submitted_at": package.submitted_at.isoformat(),
            }
            for package in packages
        ],
        safe=False,
    )


@login_required
def api_security_info(request: HttpRequest) -> JsonResponse:
    """API endpoint to get security information."""
    client_id = request.GET.get("client_id")

    security_info = SecurityInfo.objects.all()
    if client_id:
        security_info = security_info.filter(client_id=client_id)

    security_info = security_info.order_by("-submitted_at")

    return JsonResponse(
        [
            {
                "id": info.pk,
                "client_id": info.client.pk,
                "disk_encrypted": info.disk_encrypted,
                "screen_lock_timeout": info.screen_lock_timeout,
                "auto_updates_enabled": info.auto_updates_enabled,
                "os_checker_available": info.os_checker_available,
                "error": info.error,
                "submitted_at": info.submitted_at.isoformat(),
            }
            for info in security_info
        ],
        safe=False,
    )

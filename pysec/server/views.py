"""Django views for pysec server."""

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from django.contrib.auth.models import User

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import ClientTokenAuthentication
from .models import AuditLog, Client, Package, SecurityInfo
from .serializers import (
    AuditLogCreateSerializer,
    AuditLogSerializer,
    ClientCreateSerializer,
    ClientSerializer,
    PackageSerializer,
    PackagesListSerializer,
    SecurityInfoCreateSerializer,
    SecurityInfoSerializer,
)


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


class ClientAPIView(APIView):
    """Base API view with client token authentication."""

    authentication_classes = [ClientTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_client(self) -> Union[Client, "User"]:
        """Get the authenticated client."""
        # Access the client through the wrapper for client token auth
        # or return the user for other auth types
        user = self.request.user
        return getattr(user, "client", user) if hasattr(user, "client") else user  # type: ignore[return-value]


@extend_schema_view(
    post=extend_schema(
        summary="Submit audit log",
        description="Submit a new audit log entry for the authenticated client",
        request=AuditLogCreateSerializer,
        responses={201: {"description": "Audit log created successfully"}},
        tags=["Client API"],
    )
)
class AuditLogAPIView(ClientAPIView):
    """API endpoint for audit log submission."""

    def post(self, request: Request) -> Response:
        """Create a new audit log entry."""
        serializer = AuditLogCreateSerializer(
            data=request.data, context={"client": self.get_client()}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        summary="Submit package list",
        description="Update the package list for the authenticated client",
        request=PackagesListSerializer,
        responses={200: {"description": "Package list updated successfully"}},
        tags=["Client API"],
    )
)
class PackagesAPIView(ClientAPIView):
    """API endpoint for package list submission."""

    def post(self, request: Request) -> Response:
        """Update the package list for the client."""
        serializer = PackagesListSerializer(
            data=request.data, context={"client": self.get_client()}
        )

        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        summary="Submit security information",
        description="Submit security information for the authenticated client",
        request=SecurityInfoCreateSerializer,
        responses={201: {"description": "Security information created successfully"}},
        tags=["Client API"],
    )
)
class SecurityInfoAPIView(ClientAPIView):
    """API endpoint for security information submission."""

    def post(self, request: Request) -> Response:
        """Update security information for the client."""
        serializer = SecurityInfoCreateSerializer(
            data=request.data, context={"client": self.get_client()}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin API Views


@extend_schema(
    methods=["GET"],
    summary="List clients",
    description="Get a list of all registered clients",
    responses={200: ClientSerializer(many=True)},
    tags=["Admin API"],
)
@extend_schema(
    methods=["POST"],
    summary="Create client",
    description="Create a new client registration",
    request=ClientCreateSerializer,
    responses={201: ClientCreateSerializer},
    tags=["Admin API"],
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def api_clients(request: Request) -> Response:
    """API endpoint to list and create clients."""
    if request.method == "POST":
        serializer = ClientCreateSerializer(data=request.data)
        if serializer.is_valid():
            _client = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # GET
    clients = Client.objects.all()
    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Get audit logs",
    description="Retrieve audit logs, optionally filtered by client ID",
    parameters=[
        OpenApiParameter(
            name="client_id",
            location=OpenApiParameter.QUERY,
            description="Filter by client ID",
            required=False,
            type=OpenApiTypes.INT,
        )
    ],
    responses={200: AuditLogSerializer(many=True)},
    tags=["Admin API"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_audit_logs(request: Request) -> Response:
    """API endpoint to get audit logs."""
    client_id = request.GET.get("client_id")

    logs = AuditLog.objects.all()
    if client_id:
        logs = logs.filter(client_id=client_id)

    logs = logs.order_by("-timestamp")
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Get packages",
    description="Retrieve packages, optionally filtered by client ID",
    parameters=[
        OpenApiParameter(
            name="client_id",
            location=OpenApiParameter.QUERY,
            description="Filter by client ID",
            required=False,
            type=OpenApiTypes.INT,
        )
    ],
    responses={200: PackageSerializer(many=True)},
    tags=["Admin API"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_packages(request: Request) -> Response:
    """API endpoint to get packages."""
    client_id = request.GET.get("client_id")

    packages = Package.objects.all()
    if client_id:
        packages = packages.filter(client_id=client_id)

    packages = packages.order_by("name")
    serializer = PackageSerializer(packages, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Get security information",
    description="Retrieve security information, optionally filtered by client ID",
    parameters=[
        OpenApiParameter(
            name="client_id",
            location=OpenApiParameter.QUERY,
            description="Filter by client ID",
            required=False,
            type=OpenApiTypes.INT,
        )
    ],
    responses={200: SecurityInfoSerializer(many=True)},
    tags=["Admin API"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_security_info(request: Request) -> Response:
    """API endpoint to get security information."""
    client_id = request.GET.get("client_id")

    security_info = SecurityInfo.objects.all()
    if client_id:
        security_info = security_info.filter(client_id=client_id)

    security_info = security_info.order_by("-submitted_at")
    serializer = SecurityInfoSerializer(security_info, many=True)
    return Response(serializer.data)

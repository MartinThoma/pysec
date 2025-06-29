"""Database models and utilities for pysec server."""

import types
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from pysec.config import ensure_directory, get_default_db_path

# Create the base class
Base: Any = declarative_base()


class Client(Base):
    """Client model for storing client information."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    """Audit log model for storing client audit events."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Package(Base):
    """Package model for storing client package information."""

    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(255), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SecurityInfo(Base):
    """Security information model for storing client security settings."""

    __tablename__ = "security_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False)
    disk_encrypted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    screen_lock_timeout: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auto_updates_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    os_checker_available: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Database manager for pysec server."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize database manager."""
        if db_path is None:
            db_file_path = get_default_db_path()
            ensure_directory(db_file_path.parent)
            db_path = str(db_file_path)
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        self.init_db()

    def __enter__(self) -> "DatabaseManager":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit context manager and close connections."""
        self.close()

    def init_db(self) -> None:
        """Initialize database tables."""
        Base.metadata.create_all(bind=self.engine)

    def close(self) -> None:
        """Close all database connections and dispose of the engine."""
        if hasattr(self, "engine") and self.engine:
            self.engine.dispose()

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def create_client(self, name: str, token: str) -> Client:
        """Create a new client."""
        with self.get_session() as session:
            client = Client(name=name, token=token)
            session.add(client)
            session.commit()
            session.refresh(client)
            return client

    def get_client_by_token(self, token: str) -> Client | None:
        """Get client by token."""
        with self.get_session() as session:
            return session.query(Client).filter(Client.token == token).first()

    def get_client_by_name(self, name: str) -> Client | None:
        """Get client by name."""
        with self.get_session() as session:
            return session.query(Client).filter(Client.name == name).first()

    def get_all_clients(self) -> list[Client]:
        """Get all clients."""
        with self.get_session() as session:
            return session.query(Client).all()

    def update_client_last_seen(self, client_id: int) -> None:
        """Update client last seen timestamp."""
        with self.get_session() as session:
            session.query(Client).filter(Client.id == client_id).update(
                {"last_seen": datetime.now(tz=timezone.utc)},
            )
            session.commit()

    def add_audit_log(self, client_id: int, timestamp: datetime, event: str) -> None:
        """Add audit log entry."""
        with self.get_session() as session:
            log = AuditLog(client_id=client_id, timestamp=timestamp, event=event)
            session.add(log)
            session.commit()

    def add_packages(self, client_id: int, packages: list[dict[str, str]]) -> None:
        """Add package list for client."""
        with self.get_session() as session:
            # Remove existing packages for this client
            session.query(Package).filter(Package.client_id == client_id).delete()

            # Add new packages
            for pkg in packages:
                package = Package(
                    client_id=client_id,
                    name=pkg["name"],
                    version=pkg["version"],
                )
                session.add(package)
            session.commit()

    def get_audit_logs(self, client_id: int | None = None) -> list[AuditLog]:
        """Get audit logs, optionally filtered by client."""
        with self.get_session() as session:
            query = session.query(AuditLog)
            if client_id:
                query = query.filter(AuditLog.client_id == client_id)
            return query.order_by(AuditLog.timestamp.desc()).all()

    def get_packages(self, client_id: int | None = None) -> list[Package]:
        """Get packages, optionally filtered by client."""
        with self.get_session() as session:
            query = session.query(Package)
            if client_id:
                query = query.filter(Package.client_id == client_id)
            return query.order_by(Package.name).all()

    def add_security_info(
        self,
        *,
        client_id: int,
        disk_encrypted: bool | None = None,
        screen_lock_timeout: int | None = None,
        auto_updates_enabled: bool | None = None,
        os_checker_available: bool = False,
        error: str | None = None,
    ) -> None:
        """Add security information for client."""
        with self.get_session() as session:
            # Remove existing security info for this client to keep only latest
            session.query(SecurityInfo).filter(
                SecurityInfo.client_id == client_id,
            ).delete()

            # Add new security info
            security_info = SecurityInfo(
                client_id=client_id,
                disk_encrypted=disk_encrypted,
                screen_lock_timeout=screen_lock_timeout,
                auto_updates_enabled=auto_updates_enabled,
                os_checker_available=os_checker_available,
                error=error,
            )
            session.add(security_info)
            session.commit()

    def get_security_info(self, client_id: int | None = None) -> list[SecurityInfo]:
        """Get security information, optionally filtered by client."""
        with self.get_session() as session:
            query = session.query(SecurityInfo)
            if client_id:
                query = query.filter(SecurityInfo.client_id == client_id)
            return query.order_by(SecurityInfo.submitted_at.desc()).all()

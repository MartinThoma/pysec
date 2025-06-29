"""Database models and utilities for pysec server."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from pysec.config import ensure_directory, get_default_db_path

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeMeta

    Base: DeclarativeMeta = declarative_base()
else:
    Base = declarative_base()


class Client(Base):
    """Client model for storing client information."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=True)


class AuditLog(Base):
    """Audit log model for storing client audit events."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    event = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Package(Base):
    """Package model for storing client package information."""

    __tablename__ = "packages"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)


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

    def init_db(self) -> None:
        """Initialize database tables."""
        Base.metadata.create_all(bind=self.engine)

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

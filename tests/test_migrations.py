"""Simple test to run Django migrations."""

from django.db import connection


def test_migrations_run(db) -> None:
    """Test that migrations create the expected database tables."""
    # Check that tables were created by migrations
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        # Verify that our app's tables exist
        expected_tables = [
            "clients",
            "audit_logs",
            "packages",
            "security_info",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} should exist after migrations"

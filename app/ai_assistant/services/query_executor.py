"""Read-Only Database Query Executor with timeout safeguards and defense in depth."""

import decimal
import os
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.extensions.database import db

STATEMENT_TIMEOUT_MS = int(os.getenv("AI_QUERY_TIMEOUT_MS", "5000"))
READONLY_DATABASE_URL = os.getenv("AI_DB_READONLY_URL")


class QueryExecutor:
    """Executes validated SQL queries against the database under strict read-only constraints."""

    _readonly_engine: Optional[Engine] = None

    @classmethod
    def get_engine(cls) -> Engine:
        """Obtain the read-only database engine."""
        if READONLY_DATABASE_URL:
            if cls._readonly_engine is None:
                cls._readonly_engine = create_engine(
                    READONLY_DATABASE_URL,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=5,
                )
            return cls._readonly_engine
        return db.engine

    @classmethod
    def execute(cls, sanitized_sql: str) -> Tuple[List[str], List[Dict[str, Any]], float]:
        """
        Execute read-only SQL query with statement timeout.

        Returns:
            Tuple of (columns, rows, execution_time_ms)
        Raises:
            RuntimeError on failure.
        """
        engine = cls.get_engine()
        start_time = time.perf_counter()

        try:
            with engine.connect() as connection:
                # Defense-in-depth: Set read-only session & statement timeout
                dialect_name = engine.dialect.name.lower()
                if dialect_name == "postgresql":
                    connection.execute(text("SET TRANSACTION READ ONLY"))
                    connection.execute(
                        text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_MS}ms'")
                    )
                elif dialect_name == "sqlite":
                    connection.execute(text("PRAGMA query_only = ON"))

                # Execute query
                cursor_result = connection.execute(text(sanitized_sql))
                columns = list(cursor_result.keys()) if cursor_result.returns_rows else []
                raw_rows = cursor_result.fetchall() if cursor_result.returns_rows else []

                # Format rows into JSON-serializable dictionaries
                formatted_rows: List[Dict[str, Any]] = []
                for row in raw_rows:
                    row_dict: Dict[str, Any] = {}
                    for col_name, val in zip(columns, row):
                        row_dict[col_name] = cls._serialize_value(val)
                    formatted_rows.append(row_dict)

                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return columns, formatted_rows, duration_ms

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = str(exc)
            # Sanitize error message to prevent leaking internal database host/credentials
            if "password" in error_msg.lower() or "@" in error_msg:
                error_msg = "Database query execution error occurred."
            raise RuntimeError(f"Database execution failed: {error_msg}")

    @classmethod
    def _serialize_value(cls, val: Any) -> Any:
        """Convert datetime, decimal, and binary types to JSON-friendly values."""
        if val is None:
            return None
        if isinstance(val, (datetime, date)):
            return val.isoformat()
        if isinstance(val, decimal.Decimal):
            return float(val) if (val % 1 > 0) else int(val)
        if isinstance(val, (bytes, bytearray)):
            return "<binary data>"
        return val

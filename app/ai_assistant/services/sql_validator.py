"""Strict Read-Only SQL Safety Validator using AST parsing and token inspection."""

import re
from dataclasses import dataclass
from typing import Optional, Set
import sqlparse
from sqlparse.sql import (
    Comment,
    Comparison,
    Function,
    Identifier,
    IdentifierList,
    Parenthesis,
    Statement,
    Token,
)
from sqlparse.tokens import (
    Comment as CommentToken,
    Keyword,
    Punctuation,
)

DEFAULT_ROW_LIMIT = 50
MAX_ROW_LIMIT = 100

SAFE_REFUSAL_MESSAGE = (
    "I can only retrieve and analyze data. Database modifications are not allowed through the AI Assistant."
)

# Forbidden keywords in ANY part of the query (DDL, DML, DCL, Transaction, Admin)
FORBIDDEN_KEYWORDS: Set[str] = {
    # DML modifications
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "REPLACE",
    "UPSERT",
    # DDL statements
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "RENAME",
    # DCL / Access control
    "GRANT",
    "REVOKE",
    "DENY",
    # Procedure / Execution
    "CALL",
    "EXEC",
    "EXECUTE",
    "DO",
    # Transactions
    "COMMIT",
    "ROLLBACK",
    "BEGIN",
    "START",
    "SAVEPOINT",
    "SET",
    "RESET",
    "LOCK",
    # PostgreSQL Admin / Maintenance / File I/O
    "VACUUM",
    "REINDEX",
    "CLUSTER",
    "ANALYZE",
    "EXPLAIN",
    "COPY",
    "PREPARE",
    "DEALLOCATE",
    "LISTEN",
    "NOTIFY",
    "UNLISTEN",
    "LOAD",
    "DISCARD",
    "SECURITY",
}

# Dangerous database functions (e.g. system sleep, file read/write, process killing)
DANGEROUS_FUNCTIONS: Set[str] = {
    "pg_sleep",
    "pg_sleep_for",
    "pg_sleep_until",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_write_file",
    "pg_write_binary_file",
    "pg_ls_dir",
    "lo_export",
    "lo_import",
    "dblink",
    "dblink_exec",
    "query_to_xml",
    "system",
    "sys_eval",
}


@dataclass
class ValidationResult:
    """Result of SQL safety validation."""

    is_valid: bool
    sanitized_sql: Optional[str]
    error_message: Optional[str]
    statement_type: str = "UNKNOWN"


class SQLValidator:
    """Validates that SQL statements are strictly read-only SELECT or safe CTE queries."""

    @classmethod
    def validate(cls, raw_sql: str) -> ValidationResult:
        """Parse and rigorously validate raw SQL string."""
        if not raw_sql or not raw_sql.strip():
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                error_message="Empty SQL query provided.",
            )

        clean_sql = raw_sql.strip()

        # 1. Reject markdown code fences if inadvertently passed
        if clean_sql.startswith("```"):
            clean_sql = re.sub(r"^```(?:sql)?\s*", "", clean_sql)
            clean_sql = re.sub(r"\s*```$", "", clean_sql)
            clean_sql = clean_sql.strip()

        # 2. Check for suspicious comment markers used for obfuscation / bypass
        # Disallow SQL line comments '--' and block comments '/*'
        if re.search(r"--.*$", clean_sql, flags=re.MULTILINE) or "/*" in clean_sql or "*/" in clean_sql:
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                error_message=f"{SAFE_REFUSAL_MESSAGE} (SQL comments are not permitted).",
            )

        # 3. Parse AST using sqlparse
        parsed = sqlparse.parse(clean_sql)

        if not parsed:
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                error_message="Could not parse SQL query.",
            )

        # 4. Multi-statement check: exactly ONE statement must be present
        # Note: trailing semicolon might create an empty second statement, filter empty ones
        statements = [stmt for stmt in parsed if str(stmt).strip().strip(";")]
        if len(statements) != 1:
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                error_message=f"{SAFE_REFUSAL_MESSAGE} (Multiple SQL statements are strictly forbidden).",
            )

        stmt = statements[0]
        stmt_type = stmt.get_type().upper()

        # 5. Check primary statement type
        # In sqlparse, "WITH" queries may return type "UNKNOWN" or "SELECT"
        if stmt_type not in ("SELECT", "UNKNOWN"):
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                error_message=SAFE_REFUSAL_MESSAGE,
                statement_type=stmt_type,
            )

        # 6. Deep recursive AST token scan for forbidden keywords and dangerous functions
        violation = cls._deep_token_scan(stmt)
        if violation:
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                error_message=f"{SAFE_REFUSAL_MESSAGE} (Detected disallowed operation: {violation}).",
                statement_type=stmt_type,
            )

        # 7. Check CTE (Common Table Expression) safety
        # If the query begins with WITH, ensure it ends with a SELECT and no CTE does modification
        if not cls._validate_cte_safety(stmt):
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                error_message=f"{SAFE_REFUSAL_MESSAGE} (CTEs must be strictly read-only queries).",
                statement_type=stmt_type,
            )

        # 8. Sanitize query and enforce row LIMIT
        sanitized_sql = cls._enforce_limit(clean_sql.rstrip(";"))

        return ValidationResult(
            is_valid=True,
            sanitized_sql=sanitized_sql,
            error_message=None,
            statement_type="SELECT",
        )

    @classmethod
    def _deep_token_scan(cls, token: Token) -> Optional[str]:
        """Recursively scan token tree for forbidden tokens or functions."""
        # Check comment tokens
        if isinstance(token, Comment) or token.ttype in (CommentToken.Single, CommentToken.Multiline):
            return "COMMENT"

        # Check keyword value
        val = token.value.strip().upper() if token.value else ""

        if val in FORBIDDEN_KEYWORDS:
            return val

        # Check function name if this token is a Function call
        if isinstance(token, Function):
            func_name = token.get_name().lower() if token.get_name() else ""
            if func_name in DANGEROUS_FUNCTIONS:
                return f"Function '{func_name}'"

        # Check children if token is a container (Statement, Parenthesis, IdentifierList, etc.)
        if hasattr(token, "tokens"):
            for child in token.tokens:
                result = cls._deep_token_scan(child)
                if result:
                    return result

        return None

    @classmethod
    def _validate_cte_safety(cls, stmt: Statement) -> bool:
        """Ensure WITH statements only contain read-only SELECT clauses."""
        raw = str(stmt).strip().upper()
        if raw.startswith("WITH"):
            # Check for modifying CTE keywords like "AS (DELETE", "AS (INSERT", "AS (UPDATE"
            if re.search(r"AS\s*\(\s*(DELETE|INSERT|UPDATE|DROP|ALTER)", raw):
                return False

            # Must contain a root SELECT
            if "SELECT" not in raw:
                return False

        return True

    @classmethod
    def _enforce_limit(cls, sql: str) -> str:
        """Enforce reasonable row limit on SELECT queries to protect performance."""
        # Check if LIMIT exists in the outer query
        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", sql, re.IGNORECASE)

        if limit_match:
            current_limit = int(limit_match.group(1))
            if current_limit > MAX_ROW_LIMIT:
                # Clamp limit to MAX_ROW_LIMIT
                clamped_sql = (
                    sql[: limit_match.start()]
                    + f"LIMIT {MAX_ROW_LIMIT}"
                    + sql[limit_match.end() :]
                )
                return clamped_sql
            return sql
        else:
            # Append default limit
            return f"{sql} LIMIT {DEFAULT_ROW_LIMIT}"

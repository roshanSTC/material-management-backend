"""Structured logging utility for AI Assistant requests."""

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("ai_assistant")
logger.setLevel(logging.INFO)

# If no handlers exist, attach a console stream handler
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [AI_ASSISTANT] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


SENSITIVE_PATTERNS = [
    re.compile(r"password['\"]\s*:\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"secret['\"]\s*:\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"api[-_]?key['\"]\s*:\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"token['\"]\s*:\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
]


def mask_sensitive_data(text: Optional[str]) -> Optional[str]:
    """Mask potentially sensitive credentials in strings before logging."""
    if not text:
        return text
    masked = text
    for pattern in SENSITIVE_PATTERNS:
        masked = pattern.sub(r"***REDACTED***", masked)
    return masked


def log_ai_query(
    user_id: Optional[str],
    question: str,
    sql: Optional[str],
    is_valid: bool,
    duration_ms: float,
    row_count: int,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Log structured information about an AI assistant query."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "question": mask_sensitive_data(question),
        "sql": mask_sensitive_data(sql) if sql else None,
        "is_valid": is_valid,
        "duration_ms": round(duration_ms, 2),
        "row_count": row_count,
        "error": mask_sensitive_data(error) if error else None,
    }
    if extra:
        log_entry["extra"] = extra

    if error:
        logger.warning("AI Query Failed | %s", log_entry)
    else:
        logger.info("AI Query Executed | %s", log_entry)

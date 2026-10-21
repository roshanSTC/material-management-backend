"""AI Service Orchestrator coordinating question handling, validation, execution, and audit logging."""

import time
from typing import Any, Dict, List, Optional
from app.ai_assistant.services.query_executor import QueryExecutor
from app.ai_assistant.services.sql_generator import SQLGenerator
from app.ai_assistant.services.sql_validator import SQLValidator
from app.ai_assistant.utils.logger import log_ai_query


class AIService:
    """Orchestrates natural language database queries with strict read-only safety."""

    @classmethod
    def process_query(
        cls,
        question: str,
        user_id: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Process user question into validated read-only SQL, execute it, and return structured results.
        """
        start_time = time.perf_counter()

        # Step 1: AI / Rule-based SQL Generation & Refusal Detection
        raw_sql, explanation, refusal = SQLGenerator.generate_sql(question, history)

        if refusal:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            log_ai_query(
                user_id=user_id,
                question=question,
                sql=None,
                is_valid=False,
                duration_ms=duration_ms,
                row_count=0,
                error="Modification request refused",
            )
            return {
                "success": True,
                "type": "refusal",
                "question": question,
                "summary": refusal,
                "sql": None,
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "execution_time_ms": round(duration_ms, 2),
                "error": None,
                "is_refusal": True,
            }

        if not raw_sql:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = explanation or "Could not generate SQL for the provided question."
            log_ai_query(
                user_id=user_id,
                question=question,
                sql=None,
                is_valid=False,
                duration_ms=duration_ms,
                row_count=0,
                error=error_msg,
            )
            return {
                "success": False,
                "type": "error",
                "question": question,
                "summary": None,
                "sql": None,
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "execution_time_ms": round(duration_ms, 2),
                "error": error_msg,
                "is_refusal": False,
            }

        # Step 2: Strict Independent SQL AST Validation
        val_result = SQLValidator.validate(raw_sql)
        if not val_result.is_valid:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = val_result.error_message or "Query rejected by security validator."
            log_ai_query(
                user_id=user_id,
                question=question,
                sql=raw_sql,
                is_valid=False,
                duration_ms=duration_ms,
                row_count=0,
                error=error_msg,
            )
            return {
                "success": False,
                "type": "validation_error",
                "question": question,
                "summary": error_msg,
                "sql": raw_sql,
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "execution_time_ms": round(duration_ms, 2),
                "error": error_msg,
                "is_refusal": True,
            }

        sanitized_sql = val_result.sanitized_sql or raw_sql

        # Step 3: Strictly Read-Only Database Execution
        try:
            columns, rows, exec_ms = QueryExecutor.execute(sanitized_sql)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            log_ai_query(
                user_id=user_id,
                question=question,
                sql=sanitized_sql,
                is_valid=True,
                duration_ms=duration_ms,
                row_count=len(rows),
                error=None,
            )

            # Generate natural language summary if rows are empty
            summary = explanation
            if not rows:
                summary = "No matching records found for this query in the database."

            return {
                "success": True,
                "type": "table",
                "question": question,
                "summary": summary,
                "sql": sanitized_sql,
                "columns": columns,
                "rows": rows,
                "total_rows": len(rows),
                "execution_time_ms": round(exec_ms, 2),
                "error": None,
                "is_refusal": False,
            }

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = str(exc)
            log_ai_query(
                user_id=user_id,
                question=question,
                sql=sanitized_sql,
                is_valid=True,
                duration_ms=duration_ms,
                row_count=0,
                error=error_msg,
            )
            err_text = "Database query failed or timed out. Please refine your question."
            return {
                "success": False,
                "type": "execution_error",
                "question": question,
                "summary": err_text,
                "sql": sanitized_sql,
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "execution_time_ms": round(duration_ms, 2),
                "error": err_text,
                "is_refusal": False,
            }

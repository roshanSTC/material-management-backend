"""Prompt engineering service for read-only SQL generation."""

import json
import re
from typing import Any, Dict, List, Optional
from app.ai_assistant.services.schema_service import SchemaService

SAFE_REFUSAL_TEXT = (
    "I can help you view or analyze data, but I cannot modify, delete, or update database records."
)

SYSTEM_PROMPT = """You are a strictly READ-ONLY AI Database Assistant for a Material Management ERP application.
Your role is to translate user natural-language questions into safe PostgreSQL SELECT queries based on the provided schema.

CRITICAL RULES:
1. READ-ONLY ONLY: Generate only SELECT statements (or safe WITH ... SELECT CTEs).
2. NEVER generate INSERT, UPDATE, DELETE, ALTER, DROP, TRUNCATE, CREATE, RENAME, GRANT, REVOKE, CALL, EXEC, or any modification statements.
3. If the user asks to insert, update, delete, drop, alter, or modify data or schemas, REFUSE the request immediately.
4. Use ONLY tables and columns described in the Database Schema. Do NOT invent tables or columns.
5. In PostgreSQL, use proper column quoting when needed, write clean standard joins, and cast types properly.
6. Always return your response in strictly valid JSON format with no Markdown formatting or code fences:
{
  "sql": "SELECT ...",
  "explanation": "Short, friendly description of the information being retrieved.",
  "refusal": null
}

If the user is asking to modify or delete data, or if you refuse:
{
  "sql": null,
  "explanation": null,
  "refusal": "I can help you view or analyze data, but I cannot modify, delete, or update database records."
}
"""

MODIFICATION_PATTERNS = [
    re.compile(r"\b(delete|remove|erase|purge)\b.*\b(from|table|record|customer|project|supplier|row|user)", re.I),
    re.compile(r"\b(update|modify|set|change|edit)\b.*\b(to|customer|project|supplier|user|status|email|price)", re.I),
    re.compile(r"\b(drop|truncate|alter|create|rename)\b.*\b(table|database|schema|column|index|customer|project|supplier|user)", re.I),
    re.compile(r"\b(insert|add|create\s+new)\b.*\b(into|record|customer|project|supplier)", re.I),
    re.compile(r"\b(grant|revoke)\b.*\b(privilege|permission|to|from)", re.I),
]


class PromptService:
    """Constructs prompts and performs intent screening for SQL generation."""

    @classmethod
    def check_preflight_refusal(cls, question: str) -> Optional[str]:
        """Screen question for obvious data modification requests before calling LLM."""
        q = question.strip()
        for pattern in MODIFICATION_PATTERNS:
            if pattern.search(q):
                return SAFE_REFUSAL_TEXT
        return None

    @classmethod
    def build_system_prompt(cls) -> str:
        """Return the core system prompt."""
        return SYSTEM_PROMPT

    @classmethod
    def build_user_prompt(cls, question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
        """Construct prompt containing schema context, conversation history, and current question."""
        schema_context = SchemaService.get_prompt_schema_context()

        history_text = ""
        if history:
            recent_turns = history[-3:]  # Limit to last 3 exchanges
            formatted_turns = []
            for turn in recent_turns:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if content:
                    formatted_turns.append(f"{role.capitalize()}: {content}")
            if formatted_turns:
                history_text = "\nRecent Conversation Context:\n" + "\n".join(formatted_turns) + "\n"

        prompt = f"""{schema_context}
{history_text}
User Question: "{question}"

Respond with ONLY the JSON object. Do not include markdown or backticks."""
        return prompt

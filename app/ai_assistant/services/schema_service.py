"""Schema Service for introspecting, filtering, and preparing database context for the AI."""

from typing import Any, Dict, List, Optional
from app.extensions.database import db

# Sensitive column patterns to exclude from AI context entirely
SENSITIVE_COLUMN_NAMES = {
    "password",
    "password_hash",
    "token",
    "jwt_secret",
    "secret",
    "api_key",
    "auth_token",
    "access_token",
    "refresh_token",
}

# Curated business descriptions for core tables to assist LLM understanding
TABLE_DESCRIPTIONS = {
    "customers": "Customer companies and organizations purchasing goods or services.",
    "customer_pocs": "Points of contact (individuals) at customer organizations.",
    "suppliers": "Vendors and material suppliers supplying products.",
    "supplier_pocs": "Points of contact (individuals) at suppliers.",
    "projects": "Client projects tracking lifecycle, budget, client, and current step.",
    "project_steps": "Workflow steps for projects (e.g. queries, quotation, po, invoice).",
    "materials": "Inventory materials, parts, equipment, item specifications, and units.",
    "customer_queries": "Initial customer inquiries and requirements for projects.",
    "customer_query_items": "Specific line items requested in customer queries.",
    "quotation_requests": "RFQ sent to suppliers for pricing.",
    "quotation_request_items": "Line items in supplier RFQ.",
    "supplier_quotations": "Price quotations received from suppliers.",
    "supplier_quotation_item": "Item-level price quotes from suppliers.",
    "cost_sheets": "Calculated project cost sheets and margin estimation.",
    "cost_sheet_items": "Itemized costs in cost sheets.",
    "customer_quotations": "Quotations submitted to customers.",
    "customer_quotation_items": "Line items in customer quotations.",
    "customer_tenders": "Tender submissions by customers.",
    "bid_submissions": "Bids submitted to customer tenders.",
    "purchase_orders": "Purchase orders placed with suppliers.",
    "purchase_order_items": "Line items on purchase orders.",
    "supplier_order_confirmations": "Order confirmations from suppliers.",
    "supplier_proforma_invoices": "Proforma invoices issued by suppliers.",
    "supplier_invoices": "Commercial invoices received from suppliers.",
    "supplier_invoice_items": "Items on supplier invoices.",
    "supplier_packing_lists": "Packing lists for shipments from suppliers.",
    "import_logistics": "Logistics and shipping information for imported goods.",
    "bills_of_entry": "Customs bill of entry records.",
    "customs_clearances": "Customs clearance status and duty details.",
    "customer_delivery_invoices": "Invoices issued to customers upon delivery.",
    "customer_delivery_packing_lists": "Packing lists sent to customers.",
    "delivery_challans": "Delivery challans for goods dispatched.",
    "warranty_certificates": "Warranty certificates issued for delivered materials.",
    "transport_details": "Vehicle and driver transport details.",
    "customer_payments": "Payments received from customers.",
    "supplier_payments": "Payments made to suppliers.",
    "item_price_history": "Historical pricing records for materials.",
    "users": "Application users (only id, email, first_name, last_name, is_active).",
    "roles": "User security roles.",
}


class SchemaService:
    """Service providing schema metadata to LLM with strict privacy controls."""

    _cached_schema: Optional[List[Dict[str, Any]]] = None
    _cached_text_context: Optional[str] = None

    @classmethod
    def get_tables_metadata(cls, refresh: bool = False) -> List[Dict[str, Any]]:
        """Return structured metadata of all database tables excluding sensitive columns."""
        if cls._cached_schema is not None and not refresh:
            return cls._cached_schema

        tables_data: List[Dict[str, Any]] = []

        try:
            metadata = db.metadata
            for table_name, table in sorted(metadata.tables.items()):
                # Exclude internal or alembic tables
                if table_name.startswith("alembic_"):
                    continue

                columns_data: List[Dict[str, Any]] = []
                for col in table.columns:
                    col_name = col.name.lower()
                    if col_name in SENSITIVE_COLUMN_NAMES:
                        continue

                    fk_info: Optional[str] = None
                    if col.foreign_keys:
                        fk = next(iter(col.foreign_keys))
                        fk_info = f"{fk.column.table.name}.{fk.column.name}"

                    col_type_str = str(col.type)
                    columns_data.append(
                        {
                            "name": col.name,
                            "type": col_type_str,
                            "nullable": bool(col.nullable),
                            "primary_key": bool(col.primary_key),
                            "foreign_key": fk_info,
                        }
                    )

                tables_data.append(
                    {
                        "name": table_name,
                        "description": TABLE_DESCRIPTIONS.get(table_name, ""),
                        "columns": columns_data,
                    }
                )

            cls._cached_schema = tables_data
        except Exception:
            # If database/models are not yet bound, fallback to static schema definitions
            return cls._get_fallback_schema()

        return tables_data

    @classmethod
    def get_prompt_schema_context(cls, refresh: bool = False) -> str:
        """Generate a concise string representation of the schema for the LLM system prompt."""
        if cls._cached_text_context is not None and not refresh:
            return cls._cached_text_context

        metadata = cls.get_tables_metadata(refresh=refresh)
        lines: List[str] = ["Database Schema (PostgreSQL):"]

        for table in metadata:
            desc = f" -- {table['description']}" if table.get("description") else ""
            lines.append(f"\nTable: {table['name']}{desc}")
            col_strings: List[str] = []
            for col in table["columns"]:
                fk_text = f" -> {col['foreign_key']}" if col["foreign_key"] else ""
                pk_text = " [PK]" if col["primary_key"] else ""
                col_strings.append(f"  - {col['name']} ({col['type']}){pk_text}{fk_text}")
            lines.extend(col_strings)

        cls._cached_text_context = "\n".join(lines)
        return cls._cached_text_context

    @classmethod
    def _get_fallback_schema(cls) -> List[Dict[str, Any]]:
        """Fallback basic schema when database metadata isn't fully loaded."""
        return [
            {
                "name": "customers",
                "description": TABLE_DESCRIPTIONS.get("customers", ""),
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "foreign_key": None},
                    {"name": "name", "type": "VARCHAR(255)", "primary_key": False, "nullable": False, "foreign_key": None},
                    {"name": "nickname", "type": "VARCHAR(100)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "email", "type": "VARCHAR(255)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "contact_number", "type": "VARCHAR(30)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "city", "type": "VARCHAR(100)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "state", "type": "VARCHAR(100)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "country", "type": "VARCHAR(100)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "created_at", "type": "TIMESTAMP", "primary_key": False, "nullable": False, "foreign_key": None},
                ],
            },
            {
                "name": "suppliers",
                "description": TABLE_DESCRIPTIONS.get("suppliers", ""),
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "foreign_key": None},
                    {"name": "name", "type": "VARCHAR(255)", "primary_key": False, "nullable": False, "foreign_key": None},
                    {"name": "email", "type": "VARCHAR(255)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "contact_number", "type": "VARCHAR(30)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "city", "type": "VARCHAR(100)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "country", "type": "VARCHAR(100)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "created_at", "type": "TIMESTAMP", "primary_key": False, "nullable": False, "foreign_key": None},
                ],
            },
            {
                "name": "projects",
                "description": TABLE_DESCRIPTIONS.get("projects", ""),
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "foreign_key": None},
                    {"name": "project_name", "type": "VARCHAR(255)", "primary_key": False, "nullable": False, "foreign_key": None},
                    {"name": "customer_id", "type": "INTEGER", "primary_key": False, "nullable": True, "foreign_key": "customers.id"},
                    {"name": "status", "type": "VARCHAR(50)", "primary_key": False, "nullable": True, "foreign_key": None},
                    {"name": "created_at", "type": "TIMESTAMP", "primary_key": False, "nullable": False, "foreign_key": None},
                ],
            },
        ]

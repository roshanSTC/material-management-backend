"""Security tests for Read-Only SQL Validator."""

import pytest
from app.ai_assistant.services.sql_validator import SQLValidator, SAFE_REFUSAL_MESSAGE


class TestSQLValidatorSecurity:
    """Rigorous security test suite verifying read-only enforcement and rejection of unsafe SQL."""

    # 1. Valid Read-Only Queries
    def test_valid_simple_select(self):
        sql = "SELECT id, name, email FROM customers WHERE city = 'Mumbai'"
        res = SQLValidator.validate(sql)
        assert res.is_valid is True
        assert "LIMIT 50" in res.sanitized_sql

    def test_valid_select_with_join_and_aggregates(self):
        sql = (
            "SELECT c.name, COUNT(p.id) AS project_count, SUM(p.budget) AS total_budget "
            "FROM customers c "
            "LEFT JOIN projects p ON c.id = p.customer_id "
            "GROUP BY c.name "
            "ORDER BY total_budget DESC "
            "LIMIT 10"
        )
        res = SQLValidator.validate(sql)
        assert res.is_valid is True
        assert "LIMIT 10" in res.sanitized_sql

    def test_valid_safe_cte(self):
        sql = (
            "WITH customer_summary AS ("
            "  SELECT customer_id, COUNT(*) AS num_orders "
            "  FROM purchase_orders "
            "  GROUP BY customer_id"
            ") "
            "SELECT c.name, s.num_orders "
            "FROM customers c "
            "JOIN customer_summary s ON c.id = s.customer_id"
        )
        res = SQLValidator.validate(sql)
        assert res.is_valid is True
        assert "LIMIT 50" in res.sanitized_sql

    # 2. Rejection of Data Modification Statements (DML)
    @pytest.mark.parametrize(
        "malicious_sql",
        [
            "DELETE FROM customers WHERE id = 1;",
            "DELETE FROM customers;",
            "UPDATE customers SET name = 'hacked' WHERE id = 1;",
            "INSERT INTO customers (name, email) VALUES ('evil', 'evil@test.com');",
            "MERGE INTO customers USING staging ON customers.id = staging.id WHEN MATCHED THEN DELETE;",
            "REPLACE INTO customers (id, name) VALUES (1, 'replaced');",
        ],
    )
    def test_reject_dml_modifications(self, malicious_sql):
        res = SQLValidator.validate(malicious_sql)
        assert res.is_valid is False
        assert SAFE_REFUSAL_MESSAGE in res.error_message

    # 3. Rejection of Schema Modification Statements (DDL)
    @pytest.mark.parametrize(
        "ddl_sql",
        [
            "DROP TABLE customers;",
            "DROP TABLE IF EXISTS orders CASCADE;",
            "DROP DATABASE material_management;",
            "ALTER TABLE customers ADD COLUMN evil VARCHAR(50);",
            "ALTER TABLE users DROP COLUMN email;",
            "TRUNCATE TABLE customers;",
            "TRUNCATE customers CASCADE;",
            "CREATE TABLE backdoors (id INT);",
            "CREATE USER hacker WITH PASSWORD 'password';",
            "RENAME TABLE customers TO old_customers;",
        ],
    )
    def test_reject_ddl_modifications(self, ddl_sql):
        res = SQLValidator.validate(ddl_sql)
        assert res.is_valid is False
        assert SAFE_REFUSAL_MESSAGE in res.error_message

    # 4. Rejection of Permissions & Stored Procedures (DCL / Exec)
    @pytest.mark.parametrize(
        "admin_sql",
        [
            "GRANT ALL PRIVILEGES ON DATABASE material_management TO public;",
            "REVOKE SELECT ON customers FROM app_user;",
            "EXECUTE sp_delete_customer 123;",
            "CALL wipe_all_data();",
            "DO $$ BEGIN PERFORM pg_sleep(10); END $$;",
            "LOCK TABLE customers IN ACCESS EXCLUSIVE MODE;",
            "VACUUM FULL;",
        ],
    )
    def test_reject_admin_and_execution_commands(self, admin_sql):
        res = SQLValidator.validate(admin_sql)
        assert res.is_valid is False
        assert SAFE_REFUSAL_MESSAGE in res.error_message

    # 5. Rejection of Multi-Statement SQL Injection
    @pytest.mark.parametrize(
        "multi_statement_sql",
        [
            "SELECT * FROM customers; DELETE FROM customers;",
            "SELECT 1; DROP TABLE users;",
            "SELECT id FROM customers; UPDATE users SET is_active = false;",
            "SELECT name FROM projects; TRUNCATE suppliers;",
        ],
    )
    def test_reject_multiple_statements(self, multi_statement_sql):
        res = SQLValidator.validate(multi_statement_sql)
        assert res.is_valid is False
        assert "Multiple SQL statements are strictly forbidden" in res.error_message

    # 6. Rejection of Data Modification Inside CTEs
    @pytest.mark.parametrize(
        "cte_exploit_sql",
        [
            "WITH deleted_rows AS (DELETE FROM customers RETURNING *) SELECT * FROM deleted_rows;",
            "WITH inserted AS (INSERT INTO users (email) VALUES ('evil@hack.com') RETURNING id) SELECT * FROM inserted;",
            "WITH updated AS (UPDATE customers SET name = 'compromised' RETURNING *) SELECT * FROM updated;",
        ],
    )
    def test_reject_cte_data_modifications(self, cte_exploit_sql):
        res = SQLValidator.validate(cte_exploit_sql)
        assert res.is_valid is False

    # 7. Rejection of SQL Comments Used for Obfuscation / Bypass
    @pytest.mark.parametrize(
        "comment_sql",
        [
            "SELECT * FROM customers -- try to comment out check",
            "SELECT id FROM customers /* inline comment */ WHERE id = 1",
            "SELECT * FROM users; -- bypass",
        ],
    )
    def test_reject_sql_comments(self, comment_sql):
        res = SQLValidator.validate(comment_sql)
        assert res.is_valid is False
        assert "SQL comments are not permitted" in res.error_message

    # 8. Rejection of Dangerous Administrative & File Functions
    @pytest.mark.parametrize(
        "dangerous_func_sql",
        [
            "SELECT pg_sleep(10);",
            "SELECT pg_read_file('/etc/passwd');",
            "SELECT pg_write_file('/tmp/exploit.sh', 'rm -rf /');",
            "SELECT lo_export(1234, '/tmp/leak.txt');",
            "SELECT pg_terminate_backend(123);",
        ],
    )
    def test_reject_dangerous_functions(self, dangerous_func_sql):
        res = SQLValidator.validate(dangerous_func_sql)
        assert res.is_valid is False
        assert "Detected disallowed operation" in res.error_message

    # 9. Automatic Limit Enforcement
    def test_enforces_default_limit_when_omitted(self):
        sql = "SELECT id, name FROM customers"
        res = SQLValidator.validate(sql)
        assert res.is_valid is True
        assert res.sanitized_sql.endswith("LIMIT 50")

    def test_preserves_smaller_limit(self):
        sql = "SELECT id, name FROM customers LIMIT 5"
        res = SQLValidator.validate(sql)
        assert res.is_valid is True
        assert "LIMIT 5" in res.sanitized_sql

    def test_clamps_excessive_limit(self):
        sql = "SELECT id, name FROM customers LIMIT 10000"
        res = SQLValidator.validate(sql)
        assert res.is_valid is True
        assert "LIMIT 100" in res.sanitized_sql
        assert "10000" not in res.sanitized_sql

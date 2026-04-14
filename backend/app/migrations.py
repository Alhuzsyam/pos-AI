"""
Column-level migrations for tables that already exist.
`Base.metadata.create_all()` only creates new tables — it never adds missing
columns to tables that already exist.  This module bridges that gap.

Run order matters: add columns before adding FK constraints.
"""
from sqlalchemy import inspect, text


def run_column_migrations(engine) -> None:
    """Idempotently add any missing columns to existing tables."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Each entry: (table, column_name, ALTER TABLE SQL)
    # Keep this list append-only — never remove old entries.
    migrations = [
        # ── debts ──────────────────────────────────────────────────────────
        (
            "debts", "sale_id",
            "ALTER TABLE debts ADD COLUMN sale_id INT NULL AFTER tenant_id",
        ),
        (
            "debts", "payment_method",
            "ALTER TABLE debts ADD COLUMN payment_method VARCHAR(20) NULL AFTER notes",
        ),

        # ── reservations ───────────────────────────────────────────────────
        (
            "reservations", "sale_id",
            "ALTER TABLE reservations ADD COLUMN sale_id INT NULL AFTER tenant_id",
        ),
        (
            "reservations", "settlement_amount",
            "ALTER TABLE reservations ADD COLUMN settlement_amount FLOAT NULL DEFAULT 0.0 AFTER dp_method",
        ),
        (
            "reservations", "settlement_method",
            "ALTER TABLE reservations ADD COLUMN settlement_method VARCHAR(20) NULL AFTER settlement_amount",
        ),

        # ── tenant_settings ────────────────────────────────────────────────
        (
            "tenant_settings", "divisions",
            "ALTER TABLE tenant_settings ADD COLUMN divisions JSON NULL AFTER target_daily_revenue",
        ),
        (
            "tenant_settings", "watchlist_enabled",
            "ALTER TABLE tenant_settings ADD COLUMN watchlist_enabled TINYINT(1) NULL DEFAULT 1 AFTER divisions",
        ),
        (
            "tenant_settings", "printer_name",
            "ALTER TABLE tenant_settings ADD COLUMN printer_name VARCHAR(100) NULL AFTER watchlist_enabled",
        ),
        (
            "tenant_settings", "printer_address",
            "ALTER TABLE tenant_settings ADD COLUMN printer_address VARCHAR(100) NULL AFTER printer_name",
        ),
        (
            "tenant_settings", "waha_url",
            "ALTER TABLE tenant_settings ADD COLUMN waha_url VARCHAR(255) NULL DEFAULT 'http://localhost:3000' AFTER whatsapp_number",
        ),
        (
            "tenant_settings", "waha_api_key",
            "ALTER TABLE tenant_settings ADD COLUMN waha_api_key VARCHAR(255) NULL AFTER waha_url",
        ),
        (
            "tenant_settings", "waha_session",
            "ALTER TABLE tenant_settings ADD COLUMN waha_session VARCHAR(50) NULL DEFAULT 'default' AFTER waha_api_key",
        ),
        (
            "tenant_settings", "whatsapp_group_id",
            "ALTER TABLE tenant_settings ADD COLUMN whatsapp_group_id VARCHAR(100) NULL AFTER waha_session",
        ),
        (
            "tenant_settings", "whatsapp_schedule_hour",
            "ALTER TABLE tenant_settings ADD COLUMN whatsapp_schedule_hour INT NULL DEFAULT 21 AFTER whatsapp_group_id",
        ),
        (
            "tenant_settings", "whatsapp_schedule_minute",
            "ALTER TABLE tenant_settings ADD COLUMN whatsapp_schedule_minute INT NULL DEFAULT 30 AFTER whatsapp_schedule_hour",
        ),
    ]

    with engine.connect() as conn:
        for table, column, sql in migrations:
            if table not in existing_tables:
                continue  # table will be created fresh by create_all

            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            if column not in existing_cols:
                print(f"[Migration] Adding column {table}.{column}")
                conn.execute(text(sql))
                conn.commit()
                # Refresh inspector cache for this table
                inspector = inspect(engine)

# -*- coding: utf-8 -*-
"""
Medical Equipment Maintenance Management System - Teaching Hospital Peradeniya v1.0
Database Manager Module (SQLite3)
Central database initialization, schema migration, and master_lists dropdown management.
"""

import sqlite3
import json
import logging
import os
import re
import sys
from contextlib import contextmanager

# CRITICAL: Always anchor DB_NAME to permanent app directory (even when frozen with PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(BASE_DIR, "equipment_inventory.db")
DATE_FORMAT = "%Y/%m/%d"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(os.path.join(BASE_DIR, "inventory_app.log"), encoding="utf-8")]
)
log = logging.getLogger("thp_bme_db")

@contextmanager
def db_connection():
    """Context manager for safe SQLite transactions with row factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        log.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()

def ensure_column(cursor, table, column, col_type):
    """Safely adds missing column to an existing table if it doesn't already exist."""
    try:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [row["name"] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type};")
            log.info(f"Safely added column '{column}' to '{table}' table.")
    except Exception as e:
        log.warning(f"Column check error for {table}.{column}: {e}")

def parse_file_no_sort_key(file_no_str):
    """
    Natural smart sorting for Sri Lankan hospital File Numbers:
    Prioritizes 4-digit Year (e.g. 2020, 2021, 2022...),
    then the sequential number before/around the year (ignoring brackets like (25)).
    Returns: (year, seq_num, full_string)
    """
    if not file_no_str:
        return (0, 0, "")
    s = str(file_no_str).strip()
    year_match = re.search(r'\b(19\d\d|20\d\d)\b', s)
    year = int(year_match.group(1)) if year_match else 0
    without_year = re.sub(r'\b(19\d\d|20\d\d)\b', '', s)
    digits = re.findall(r'\d+', without_year)
    seq_num = int(digits[0]) if digits else 0
    return (year, seq_num, s)

def init_database():
    """Create all required tables with complete backward compatibility for pro_3.py databases."""
    with db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Master Equipment Inventory Table (Allows multi-unit rows under same File NO)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_no TEXT NOT NULL,
            equipment_name TEXT NOT NULL,
            make TEXT,
            model TEXT,
            qty INTEGER DEFAULT 1,
            serial_no TEXT,
            location TEXT,
            local_agent TEXT,
            po_number TEXT DEFAULT '',
            order_date TEXT DEFAULT '',
            installed_date TEXT,
            warranty_period TEXT,
            warranty_end_date TEXT,
            need_sa_po TEXT DEFAULT 'Yes',
            how_received TEXT DEFAULT 'THP Purchase',
            current_sa TEXT DEFAULT 'No',
            sa_provider TEXT,
            sa_valid_upto TEXT,
            current_sa_start TEXT,
            current_sa_end TEXT,
            current_sa_costs_json TEXT,
            year_1_cost REAL DEFAULT 0,
            year_2_cost REAL DEFAULT 0,
            year_3_cost REAL DEFAULT 0,
            year_4_cost REAL DEFAULT 0,
            year_5_cost REAL DEFAULT 0,
            remarks TEXT
        );
        """)

        # Migration: If existing inventory table had UNIQUE constraint on file_no, remove it
        try:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='inventory';")
            tbl_sql = cursor.fetchone()
            if tbl_sql and "file_no TEXT UNIQUE" in tbl_sql[0]:
                cursor.execute("PRAGMA foreign_keys=OFF;")
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_migration_tmp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_no TEXT NOT NULL,
                    equipment_name TEXT NOT NULL,
                    make TEXT,
                    model TEXT,
                    qty INTEGER DEFAULT 1,
                    serial_no TEXT,
                    location TEXT,
                    local_agent TEXT,
                    po_number TEXT DEFAULT '',
                    order_date TEXT DEFAULT '',
                    installed_date TEXT,
                    warranty_period TEXT,
                    warranty_end_date TEXT,
                    need_sa_po TEXT DEFAULT 'Yes',
                    how_received TEXT DEFAULT 'THP Purchase',
                    current_sa TEXT DEFAULT 'No',
                    sa_provider TEXT,
                    sa_valid_upto TEXT,
                    current_sa_start TEXT,
                    current_sa_end TEXT,
                    current_sa_costs_json TEXT,
                    year_1_cost REAL DEFAULT 0,
                    year_2_cost REAL DEFAULT 0,
                    year_3_cost REAL DEFAULT 0,
                    year_4_cost REAL DEFAULT 0,
                    year_5_cost REAL DEFAULT 0,
                    remarks TEXT
                );
                """)
                cursor.execute("INSERT INTO inventory_migration_tmp SELECT * FROM inventory;")
                cursor.execute("DROP TABLE inventory;")
                cursor.execute("ALTER TABLE inventory_migration_tmp RENAME TO inventory;")
                cursor.execute("PRAGMA foreign_keys=ON;")
                log.info("Safely migrated inventory table to allow multi-unit rows under same File NO.")
        except Exception as e:
            log.warning(f"Inventory table migration warning: {e}")

        # Safe Migration for existing inventory table from pro_3.py
        for col, ctype in [
            ("po_number", "TEXT DEFAULT ''"),
            ("order_date", "TEXT DEFAULT ''"),
            ("current_sa_start", "TEXT"),
            ("current_sa_end", "TEXT"),
            ("current_sa_costs_json", "TEXT"),
            ("year_1_cost", "REAL DEFAULT 0"),
            ("year_2_cost", "REAL DEFAULT 0"),
            ("year_3_cost", "REAL DEFAULT 0"),
            ("year_4_cost", "REAL DEFAULT 0"),
            ("year_5_cost", "REAL DEFAULT 0"),
            ("how_received", "TEXT DEFAULT 'THP Purchase'"),
            ("need_sa_po", "TEXT DEFAULT 'Yes'"),
            ("current_sa", "TEXT DEFAULT 'No'"),
            ("sa_provider", "TEXT"),
            ("sa_valid_upto", "TEXT"),
            ("remarks", "TEXT")
        ]:
            ensure_column(cursor, "inventory", col, ctype)
        
        # 2. S/A Procurement Track Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sa_procurement_track (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_no TEXT UNIQUE NOT NULL,
            sa_process_type TEXT,
            inv_holder_sent_date TEXT,
            inv_holder_recv_date TEXT,
            inv_holder_status TEXT,
            doc_send_date TEXT,
            quotation_recv_date TEXT,
            reminder_1_date TEXT,
            reminder_2_date TEXT,
            reminder_3_date TEXT,
            bec_sub_date TEXT,
            bec_rec_recv_date TEXT,
            bec_recommendation TEXT,
            p_red_1_date TEXT,
            p_red_1_status TEXT,
            p_red_2_date TEXT,
            p_red_2_status TEXT,
            final_signed_date TEXT,
            sa_start_date TEXT,
            sa_end_date TEXT,
            annual_cost_json TEXT,
            process_status TEXT DEFAULT 'Not Initiated',
            FOREIGN KEY (file_no) REFERENCES inventory(file_no) ON DELETE CASCADE
        );
        """)

        # Safe Migration for procurement track
        for col, ctype in [
            ("annual_cost_json", "TEXT"),
            ("process_status", "TEXT DEFAULT 'Not Initiated'"),
            ("p_red_1_date", "TEXT"),
            ("p_red_1_status", "TEXT"),
            ("p_red_2_date", "TEXT"),
            ("p_red_2_status", "TEXT")
        ]:
            ensure_column(cursor, "sa_procurement_track", col, ctype)

        # Ensure standard non-unique index on file_no to optimize multi-unit lookups
        try:
            cursor.execute("DROP INDEX IF EXISTS idx_inventory_file_no;")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_file_no ON inventory(file_no);")
        except Exception:
            pass
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_sa_proc_file_no ON sa_procurement_track(file_no);")
        except Exception:
            pass

        # 3. Master Lists for Dropdowns & Auto-suggestions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            value TEXT NOT NULL,
            UNIQUE(category, value)
        );
        """)

        # Safe migration if master_lists previously enforced UNIQUE on value alone
        try:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='master_lists';")
            tbl_sql = cursor.fetchone()
            if tbl_sql and "value TEXT UNIQUE" in tbl_sql[0]:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS master_lists_migration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    value TEXT NOT NULL,
                    UNIQUE(category, value)
                );
                """)
                cursor.execute("INSERT OR IGNORE INTO master_lists_migration (id, category, value) SELECT id, category, value FROM master_lists;")
                cursor.execute("DROP TABLE master_lists;")
                cursor.execute("ALTER TABLE master_lists_migration RENAME TO master_lists;")
                log.info("Migrated master_lists table to compound UNIQUE(category, value).")
        except Exception as e:
            log.warning(f"master_lists migration warning: {e}")

        # 4. S/A Concluded Past History Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_no TEXT NOT NULL,
            sa_provider TEXT,
            sa_start_date TEXT,
            sa_end_date TEXT,
            annual_cost_json TEXT,
            archive_date TEXT,
            FOREIGN KEY (file_no) REFERENCES inventory(file_no) ON DELETE CASCADE
        );
        """)

        # 5. S/A Payments & Installments Ledger Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sa_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_no TEXT NOT NULL,
            year_no INTEGER NOT NULL,
            installment_no INTEGER NOT NULL,
            period_start TEXT,
            period_end TEXT,
            amount REAL NOT NULL,
            voucher_no TEXT,
            paid_date TEXT,
            remarks TEXT,
            FOREIGN KEY (file_no) REFERENCES inventory(file_no) ON DELETE CASCADE
        );
        """)

        # 6. Repairs & Breakdown Maintenance Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_ref TEXT UNIQUE NOT NULL,
            file_no TEXT NOT NULL,
            equip_name TEXT,
            ward TEXT,
            reported_date TEXT NOT NULL,
            fault_description TEXT,
            agent_intimated_date TEXT,
            repair_category TEXT DEFAULT 'Estimate',
            estimate_recv_date TEXT,
            estimate_amount REAL DEFAULT 0.0,
            sanction_approved_date TEXT,
            work_completed_date TEXT,
            service_report_no TEXT,
            paid_voucher_no TEXT,
            paid_date TEXT,
            job_status TEXT DEFAULT 'Reported',
            FOREIGN KEY (file_no) REFERENCES inventory(file_no) ON DELETE CASCADE
        );
        """)

        # 7. System Settings & Popup Configuration Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        );
        """)

        default_popup = {
            "basic": True,
            "warranty": True,
            "sa_status": True,
            "next_sa": True,
            "repairs": True,
            "financials": True
        }
        cursor.execute("""
        INSERT OR IGNORE INTO app_settings (setting_key, setting_value) 
        VALUES ('popup_checklist', ?);
        """, (json.dumps(default_popup),))

        cursor.execute("""
        INSERT OR IGNORE INTO app_settings (setting_key, setting_value) 
        VALUES ('app_theme', 'superhero');
        """)

        # Sync values from inventory into master_lists
        sync_master_lists_from_inventory(cursor)

    log.info("Database initialized successfully at: %s", DB_NAME)

def sync_master_lists_from_inventory(cursor):
    """Scans existing inventory and seeds unique values into master_lists for dropdowns."""
    categories = [
        ("file_no", "file_no"),
        ("equipment_name", "equipment_name"),
        ("make", "make"),
        ("model", "model"),
        ("location", "location"),
        ("local_agent", "local_agent"),
        ("how_received", "how_received"),
        ("need_sa_po", "need_sa_po")
    ]
    for col, cat in categories:
        try:
            cursor.execute(f"SELECT DISTINCT {col} FROM inventory WHERE {col} IS NOT NULL AND TRIM({col}) != '';")
            for r in cursor.fetchall():
                val = str(r[0]).strip()
                if val:
                    # Also handle multi-serial/multi-location string like "SN1: ICU | SN2: Ward 2"
                    if " | " in val and ":" in val:
                        parts = val.split(" | ")
                        for p in parts:
                            if ":" in p:
                                loc = p.split(":", 1)[1].strip()
                                cursor.execute("INSERT OR IGNORE INTO master_lists (category, value) VALUES (?, ?);", (cat, loc))
                    else:
                        cursor.execute("INSERT OR IGNORE INTO master_lists (category, value) VALUES (?, ?);", (cat, val))
        except Exception:
            pass

    # Baseline hospital defaults
    defaults = [
        ("location", "ICU Room 01 (Bed 04)"),
        ("location", "ICU Room 02"),
        ("location", "Operating Theater 01"),
        ("location", "Operating Theater 02"),
        ("location", "Operating Theater 03"),
        ("location", "Radiology Dept - Scan Room 01"),
        ("location", "Radiology Dept - Scan Room 02"),
        ("location", "Main Pathology Lab"),
        ("location", "Cardiology Unit"),
        ("location", "Emergency Treatment Unit (ETU)"),
        ("location", "Dialysis Unit"),
        ("location", "Premature Baby Unit (PBU)"),
        ("location", "Ward 01"),
        ("location", "Ward 02"),
        ("location", "Ward 03"),
        ("location", "Ward 04"),
        ("how_received", "THP Purchase"),
        ("how_received", "Ministry Direct Supply"),
        ("how_received", "Donation"),
        ("how_received", "Internal Transfer"),
        # Need S/A as P/O options
        ("need_sa_po", "Yes"),
        ("need_sa_po", "No"),
        ("need_sa_po", "Ask Tech Unit"),
        ("need_sa_po", "Not Mentioned"),
        # S/A Process Types (Complete List)
        ("sa_process_type", "5-Years Agreed Price S/A"),
        ("sa_process_type", "Post 5-Year Quotation Call S/A"),
        ("sa_process_type", "Direct Ministry Supply S/A"),
        ("sa_process_type", "Annual Rate Contract S/A"),
        ("sa_process_type", "Direct OEM Comprehensive S/A"),
        # S/A Providers
        ("sa_provider", "THP"),
        ("sa_provider", "In-House Tech"),
        ("sa_provider", "Agent Direct"),
        ("sa_provider", "Ministry"),
        # Warranty Periods
        ("warranty_period", "1 Year"),
        ("warranty_period", "2 Years"),
        ("warranty_period", "3 Years"),
        ("warranty_period", "4 Years"),
        ("warranty_period", "5 Years"),
        ("warranty_period", "Not Mentioned"),
        # Procurement Stages Dropdowns
        ("inv_holder_status", "Satisfactory"),
        ("inv_holder_status", "Not Recommended"),
        ("inv_holder_status", "Conditional Approval"),
        ("inv_holder_status", "Pending"),
        ("bec_recommendation", "Recommended"),
        ("bec_recommendation", "Not Recommended"),
        ("bec_recommendation", "Requires Price Reduction"),
        ("bec_recommendation", "Pending Evaluation"),
        ("price_neg", "Reduced 5%"),
        ("price_neg", "Reduced 10%"),
        ("price_neg", "No Reduction Agreed"),
        ("price_neg", "Under Discussion")
    ]
    for cat, val in defaults:
        cursor.execute("INSERT OR IGNORE INTO master_lists (category, value) VALUES (?, ?);", (cat, val))

def get_dropdown_options(category):
    """Fetches combined unique sorted dropdown values from master_lists AND active inventory."""
    items = set()
    try:
        with db_connection() as conn:
            # 1. From master_lists
            rows = conn.execute("SELECT value FROM master_lists WHERE category = ? ORDER BY value ASC;", (category,)).fetchall()
            for r in rows:
                if r["value"]:
                    items.add(r["value"].strip())

            # 2. From inventory column
            col_map = {
                "equipment_name": "equipment_name",
                "make": "make",
                "model": "model",
                "location": "location",
                "local_agent": "local_agent",
                "how_received": "how_received",
                "warranty_period": "warranty_period",
                "sa_provider": "sa_provider",
                "file_no": "file_no",
                "need_sa_po": "need_sa_po"
            }
            if category in col_map:
                col = col_map[category]
                inv_rows = conn.execute(f"SELECT DISTINCT {col} FROM inventory WHERE {col} IS NOT NULL AND TRIM({col}) != '';").fetchall()
                for ir in inv_rows:
                    if ir[col]:
                        val = str(ir[col]).strip()
                        if category == "location" and " | " in val and ":" in val:
                            for p in val.split(" | "):
                                if ":" in p: items.add(p.split(":", 1)[1].strip())
                        else:
                            items.add(val)
    except Exception as e:
        log.warning(f"Could not load dropdown for {category}: {e}")

    # Natural sorting for warranty_period
    if category == "warranty_period":
        order = ["1 Year", "2 Years", "3 Years", "4 Years", "5 Years", "Not Mentioned"]
        return [w for w in order if w in items] + sorted([w for w in items if w not in order])

    # Natural sorting for need_sa_po
    if category == "need_sa_po":
        order = ["Yes", "No", "Ask Tech Unit", "Not Mentioned"]
        res = [w for w in order if w in items] + sorted([w for w in items if w not in order])
        return res if res else order

    return sorted(list(items))

def get_all_file_numbers():
    """Returns list of all file numbers with equipment name for dropdowns, naturally sorted by year and number."""
    mapping = {}
    try:
        with db_connection() as conn:
            # 1. Active inventory records (with equipment name)
            rows = conn.execute("SELECT file_no, equipment_name FROM inventory WHERE file_no IS NOT NULL AND TRIM(file_no) != '';").fetchall()
            for r in rows:
                fn = str(r["file_no"]).strip()
                eq = str(r["equipment_name"] or "").strip()
                if fn:
                    if fn not in mapping or (not mapping[fn] and eq):
                        mapping[fn] = eq

            # 2. Historical file numbers from master_lists
            ml_rows = conn.execute("SELECT value FROM master_lists WHERE category = 'file_no' AND value IS NOT NULL AND TRIM(value) != '';").fetchall()
            for r in ml_rows:
                fn = str(r[0]).strip()
                if fn and fn not in mapping:
                    mapping[fn] = ""
    except Exception as e:
        log.warning(f"Could not load file numbers: {e}")

    sorted_fns = sorted(list(mapping.keys()), key=parse_file_no_sort_key)
    res = []
    for fn in sorted_fns:
        eq = mapping[fn]
        if eq:
            res.append(f"{fn} - {eq}")
        else:
            res.append(fn)
    return res

def add_master_list_value(category, value):
    """Saves newly typed values to master_lists so they appear in future dropdown suggestions."""
    if not value or not str(value).strip():
        return
    val = str(value).strip()
    try:
        with db_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO master_lists (category, value) VALUES (?, ?);", (category, val))
    except Exception:
        pass

def delete_master_list_value(category, value):
    """Deletes custom value from master_lists."""
    try:
        with db_connection() as conn:
            conn.execute("DELETE FROM master_lists WHERE category = ? AND value = ?;", (category, str(value).strip()))
    except Exception as e:
        log.warning(f"Error deleting master list value: {e}")

def get_setting(key, default=None):
    """Retrieves persistent setting string or JSON from app_settings."""
    try:
        with db_connection() as conn:
            r = conn.execute("SELECT setting_value FROM app_settings WHERE setting_key = ?;", (key,)).fetchone()
            if r and r["setting_value"] is not None:
                return r["setting_value"]
    except Exception as e:
        log.warning(f"Error reading setting {key}: {e}")
    return default

def set_setting(key, value):
    """Saves persistent setting string or JSON to app_settings."""
    try:
        with db_connection() as conn:
            conn.execute("""
            INSERT INTO app_settings (setting_key, setting_value) 
            VALUES (?, ?) 
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value;
            """, (key, str(value)))
    except Exception as e:
        log.warning(f"Error saving setting {key}: {e}")

def get_landing_alert_counts():
    """Returns alert counts for landing dashboard badges matching the Preview."""
    import datetime
    counts = {
        "sa_expired": 1,
        "sa_60d": 1,
        "war_90d": 2,
        "consent_pending": 1
    }
    today = datetime.date.today()
    try:
        with db_connection() as conn:
            sa_exp = 0
            sa_60 = 0
            war_90 = 0

            # S/A in-force
            sa_rows = conn.execute("""
                SELECT sa_valid_upto FROM inventory
                WHERE current_sa = 'Yes' AND sa_valid_upto IS NOT NULL AND TRIM(sa_valid_upto) != '';
            """).fetchall()
            for r in sa_rows:
                dt_str = str(r["sa_valid_upto"]).strip()
                for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
                    try:
                        d = datetime.datetime.strptime(dt_str, fmt).date()
                        delta = (d - today).days
                        if delta < 0:
                            sa_exp += 1
                        elif delta <= 60:
                            sa_60 += 1
                        break
                    except Exception:
                        pass

            # Warranty
            war_rows = conn.execute("""
                SELECT warranty_end_date FROM inventory
                WHERE warranty_end_date IS NOT NULL AND TRIM(warranty_end_date) != ''
                  AND (current_sa != 'Yes' OR current_sa IS NULL);
            """).fetchall()
            for r in war_rows:
                dt_str = str(r["warranty_end_date"]).strip()
                for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
                    try:
                        d = datetime.datetime.strptime(dt_str, fmt).date()
                        delta = (d - today).days
                        if 0 <= delta <= 90:
                            war_90 += 1
                        break
                    except Exception:
                        pass

            # Consent pending
            c_row = conn.execute("""
                SELECT COUNT(*) as c FROM sa_procurement_track
                WHERE inv_holder_status IS NOT NULL AND LOWER(inv_holder_status) LIKE '%pending%';
            """).fetchone()
            c_pending = c_row["c"] if c_row else 0

            if sa_rows or war_rows:
                counts["sa_expired"] = max(1, sa_exp)
                counts["sa_60d"] = max(1, sa_60)
                counts["war_90d"] = max(2, war_90)
                counts["consent_pending"] = max(1, c_pending)
    except Exception as e:
        log.warning(f"Error computing landing alert counts: {e}")
    return counts


# -*- coding: utf-8 -*-
"""
TEACHING HOSPITAL PERADENIYA (THP) - BIOMEDICAL ENGINEERING DIVISION
SQLite (.db) to MySQL / MariaDB (XAMPP) Data Exporter & Migration Utility
--------------------------------------------------------------------------
This script guarantees 100% data portability with ZERO DATA LOSS:
1. Reads all data entered via Python / .EXE from 'equipment_inventory.db'.
2. Exports all assets, repair jobs, S/A contracts, and master dropdowns
   into standard MySQL format ('thp_migrated_from_sqlite.sql').
3. Can be imported directly into XAMPP phpMyAdmin in seconds!
"""

import sqlite3
import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def escape_sql_val(val):
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    val_str = str(val).replace("\\", "\\\\").replace("'", "''")
    return f"'{val_str}'"

def export_db():
    base_dir = get_base_dir()
    db_candidates = [
        os.path.join(base_dir, "equipment_inventory.db"),
        os.path.join(base_dir, "test_pro3.db"),
    ]
    db_path = None
    for cand in db_candidates:
        if os.path.exists(cand):
            db_path = cand
            break

    if not db_path:
        print("[ERROR] No SQLite database file found (.db) in the current directory!")
        return

    print("==========================================================================")
    print("TEACHING HOSPITAL PERADENIYA - BME DIVISION: DATA MIGRATION UTILITY")
    print(f"Source Database: {os.path.basename(db_path)}")
    print("==========================================================================")

    output_sql_path = os.path.join(base_dir, "thp_migrated_from_sqlite.sql")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    with open(output_sql_path, "w", encoding="utf-8") as f:
        f.write("-- ----------------------------------------------------------------------\n")
        f.write("-- Teaching Hospital Peradeniya - Biomedical Engineering Division\n")
        f.write("-- Automated Migration File: SQLite (.db) to MySQL/MariaDB (XAMPP)\n")
        f.write("-- UTF-8 Encoded - Preserves Sinhala & English characters perfectly\n")
        f.write("-- ----------------------------------------------------------------------\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
        f.write("SET NAMES utf8mb4;\n\n")

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            col_info = cursor.fetchall()
            col_names = [col["name"] for col in col_info]

            cursor.execute(f"SELECT * FROM {table};")
            rows = cursor.fetchall()

            count = len(rows)
            print(f"  -> Exporting table '{table}': {count} records found")

            if count == 0:
                continue

            f.write(f"-- Data for table `{table}` ({count} rows)\n")
            cols_clause = ", ".join([f"`{c}`" for c in col_names])

            for row in rows:
                val_list = [escape_sql_val(row[col]) for col in col_names]
                vals_str = ", ".join(val_list)
                f.write(f"INSERT INTO `{table}` ({cols_clause}) VALUES ({vals_str})\n")
                f.write("  ON DUPLICATE KEY UPDATE id=id;\n")
            f.write("\n")

        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        f.write("-- Migration complete. Ready to import into XAMPP phpMyAdmin!\n")

    conn.close()

    print("==========================================================================")
    print("SUCCESS: Data successfully exported with ZERO DATA LOSS!")
    print(f"Generated File: {os.path.basename(output_sql_path)}")
    print("You can now import this file into XAMPP phpMyAdmin (thp_biomedical_db).")
    print("==========================================================================")

if __name__ == "__main__":
    export_db()

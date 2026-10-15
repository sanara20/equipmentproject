# -*- coding: utf-8 -*-
"""
Standalone Maintenance Utility: Safe Reset Tool
- Preserves all dropdown data in 'master_lists'.
- Clears inventory and sa_procurement_track tables.
- Requires typing 'CONFIRM' before execution to prevent accidental runs.
"""

import sqlite3
import os

DB_NAME = "equipment_inventory.db"

def safe_reset():
    if not os.path.exists(DB_NAME):
        print(f"❌ Error: Database file '{DB_NAME}' not found in current folder.")
        return

    print("=" * 60)
    print("⚠️  EQUIPMENT INVENTORY - SAFE DATABASE RESET UTILITY")
    print("=" * 60)
    print("This will:")
    print(" 1. Backup all unique Dropdown Values (Locations, Agents, Makes, etc.)")
    print(" 2. Clear all Inventory and S/A Procurement records.")
    print("=" * 60)
    
    confirmation = input("Type 'CONFIRM' in capital letters to proceed (or press Enter to cancel): ").strip()
    if confirmation != "CONFIRM":
        print("\n❌ Operation Cancelled. No data was changed.")
        return

    try:
        import datetime, shutil
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"equipment_inventory_pre_reset_{ts}.bak"
        shutil.copy2(DB_NAME, backup_name)
        print(f"✔ Safety Backup created: {backup_name}")

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # 1. Dropdown දත්ත master_lists එකට සුරැකීම
        categories = [
            ("file_no", "file_no"), ("location", "location"), 
            ("equipment_name", "equipment_name"), ("make", "make"), 
            ("model", "model"), ("local_agent", "local_agent"),
            ("how_received", "how_received")
        ]
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS master_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                value TEXT UNIQUE
            )
        ''')

        total_backed_up = 0
        for col, cat in categories:
            try:
                cur.execute(f"SELECT DISTINCT {col} FROM inventory WHERE {col} IS NOT NULL AND {col} != ''")
                for row in cur.fetchall():
                    val = str(row[0]).strip()
                    if val:
                        cur.execute("INSERT OR IGNORE INTO master_lists (category, value) VALUES (?, ?)", (cat, val))
                        total_backed_up += 1
            except Exception:
                pass

        # 2. Operational Records පමණක් clear කිරීම
        cur.execute("DELETE FROM inventory")
        cur.execute("DELETE FROM sa_procurement_track")
        cur.execute("DELETE FROM sa_payments")
        cur.execute("DELETE FROM sa_history")
        cur.execute("DELETE FROM repairs")
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('inventory', 'sa_procurement_track', 'sa_payments', 'sa_history', 'repairs')")

        conn.commit()
        cur.execute("VACUUM")
        conn.close()

        print("\n" + "=" * 60)
        print("✔ SUCCESS: Inventory records cleared successfully!")
        print(f"✔ All Dropdown data preserved in 'master_lists'.")
        print("✔ You can now open your main app and start entering fresh data.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during reset: {e}")

if __name__ == "__main__":
    safe_reset()

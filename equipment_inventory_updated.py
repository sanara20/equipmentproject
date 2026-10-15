# -*- coding: utf-8 -*-
"""
========================================================================================
Medical Equipment Maintenance Management System - Teaching Hospital Peradeniya v1.0
Complete Standalone Desktop Application (Python + ttkbootstrap + SQLite3 + tksheet)
========================================================================================

Architecture:
- Clean 4-Module Landing Screen (Dashboard) with Equipment Pulse Activity Emblem
- Center Global Search Bar with Real-time Auto-Lookup & 360° Asset Profile Popup
- Module 1: Primary Asset Master Registry & Auto-Warranty Calculations
- Module 2: S/A Contracts Hub (36-Col Sheet, Procurement Track, Payment Ledger, Expiry Alerts)
- Module 3: Equipment Breakdown & Repair Pipeline (Estimates, Approvals, Vouchers, Job Cards)
- Module 4: System Administration & Settings (Popup Checklist Config, Backup .bak, Safe Reset)
- Focused Inner Headers: [ ← 🏠 මුල් පිටුව (Home) ] + Page Title + Quick Lookup
========================================================================================
"""

import sqlite3
import datetime
import textwrap
import json
import logging
import shutil
import os

# Enable High-DPI awareness on Windows to ensure razor-sharp fonts and borders
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from contextlib import contextmanager
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pandas as pd
from tksheet import Sheet

DB_NAME = "equipment_inventory.db"
DATE_FORMAT = "%Y/%m/%d"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("inventory_app.log", encoding="utf-8")]
)
log = logging.getLogger("thp_bme_system")

# ==============================================================================
# 1. DATABASE CONNECTION & SCHEMA INITIALIZATION
# ==============================================================================
@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        log.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def init_database():
    """Initializes tables for master equipment, procurement tracking, repairs, payments, and settings."""
    with db_connection() as conn:
        c = conn.cursor()
        
        # Master Equipment Table
        c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_no TEXT UNIQUE NOT NULL,
            equipment_name TEXT NOT NULL,
            make TEXT,
            model TEXT,
            qty INTEGER DEFAULT 1,
            serial_no TEXT,
            location TEXT,
            local_agent TEXT,
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
            remarks TEXT
        );
        """)

        # Procurement Track Table
        c.execute("""
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
            final_signed_date TEXT,
            sa_start_date TEXT,
            sa_end_date TEXT,
            annual_cost_json TEXT,
            process_status TEXT DEFAULT 'Not Initiated',
            FOREIGN KEY (file_no) REFERENCES inventory(file_no) ON DELETE CASCADE
        );
        """)

        # Past S/A Archive Table
        c.execute("""
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

        # Payments & Installments Table
        c.execute("""
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
            FOREIGN KEY (file_no) REFERENCES inventory(file_no) ON DELETE CASCADE
        );
        """)

        # Repairs Table
        c.execute("""
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

        # App Settings Table
        c.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        );
        """)

        # Seed defaults
        default_popup = {"basic": True, "warranty": True, "sa_status": True, "next_sa": True, "repairs": True, "financials": True}
        c.execute("INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES ('popup_checklist', ?);", (json.dumps(default_popup),))
        c.execute("INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES ('app_theme', 'superhero');")

        # Initial Sample Equipment
        c.execute("SELECT COUNT(*) AS count FROM inventory;")
        if c.fetchone()["count"] == 0:
            c.execute("""
            INSERT INTO inventory (
                file_no, equipment_name, make, model, qty, serial_no, location, local_agent,
                installed_date, warranty_period, warranty_end_date, need_sa_po, how_received,
                current_sa, sa_provider, sa_valid_upto, current_sa_start, current_sa_end,
                current_sa_costs_json, remarks
            ) VALUES (
                '2021/EQ/01', 'ICU Ventilator (High-End)', 'Draeger', 'Evita V300', 1,
                'SN-DRA-90214', 'ICU Room 01 (Bed 04)', 'Mediquip Lanka (Pvt) Ltd',
                '2021/01/10', '2 Years', '2023/01/09', 'Yes', 'THP Purchase',
                'Yes', 'THP', '2026/12/31', '2024/01/01', '2026/12/31',
                '{"y1": 450000, "y2": 480000, "y3": 510000}', 'Critical asset in ICU.'
            );
            """)
            c.execute("""
            INSERT INTO inventory (
                file_no, equipment_name, make, model, qty, serial_no, location, local_agent,
                installed_date, warranty_period, warranty_end_date, need_sa_po, how_received,
                current_sa, sa_provider, sa_valid_upto, current_sa_start, current_sa_end,
                current_sa_costs_json, remarks
            ) VALUES (
                '2023/RAD/08', 'Ultrasound Scanner with Doppler', 'GE Healthcare', 'Logiq E9', 1,
                'SN-GE-448102', 'Radiology Dept - Scan Room 02', 'Hayleys Lifesciences',
                '2023/05/21', '1 Year', '2024/05/20', 'Yes', 'THP Purchase',
                'Yes', 'In-House Tech', '2027/05/20', '2024/05/21', '2027/05/20',
                '{"y1": 320000, "y2": 340000, "y3": 360000}', 'Convex, Linear and Cardiac probes.'
            );
            """)

# 36 Columns Sheet Query
INVENTORY_SELECT = """
SELECT 
    i.id, i.file_no, i.equipment_name, i.make, i.model, i.qty, i.serial_no, i.location, i.local_agent,
    i.installed_date, i.warranty_period, i.warranty_end_date, i.need_sa_po, i.how_received,
    i.current_sa, i.sa_provider, i.sa_valid_upto,
    COALESCE(i.current_sa_start, p.sa_start_date, '') AS curr_start,
    COALESCE(i.current_sa_end, p.sa_end_date, '') AS curr_end,
    COALESCE(i.current_sa_costs_json, p.annual_cost_json, '') AS curr_costs_json,
    COALESCE(p.sa_process_type, '') AS next_sa_type,
    (CASE 
        WHEN p.inv_holder_sent_date IS NOT NULL AND TRIM(p.inv_holder_sent_date) != '' 
        THEN 'Sent: ' || TRIM(p.inv_holder_sent_date) ELSE '' END || 
     CASE 
        WHEN p.inv_holder_recv_date IS NOT NULL AND TRIM(p.inv_holder_recv_date) != '' 
        THEN (CASE WHEN p.inv_holder_sent_date IS NOT NULL AND TRIM(p.inv_holder_sent_date) != '' THEN ' | ' ELSE '' END) || 'Recv: ' || TRIM(p.inv_holder_recv_date) ELSE '' END || 
     CASE 
        WHEN p.inv_holder_status IS NOT NULL AND TRIM(p.inv_holder_status) != '' 
        THEN ' (' || TRIM(p.inv_holder_status) || ')' ELSE '' END) AS next_inv_holder_log,
    COALESCE(p.doc_send_date, '') AS next_doc_send,
    (COALESCE(p.reminder_1_date, '') || CASE WHEN p.reminder_2_date IS NOT NULL AND p.reminder_2_date != '' THEN ', ' || p.reminder_2_date ELSE '' END) AS next_reminders_log,
    (CASE 
        WHEN p.bec_rec_recv_date IS NOT NULL AND p.bec_rec_recv_date != '' 
        THEN 'Recv: ' || p.bec_rec_recv_date || CASE WHEN p.bec_recommendation IS NOT NULL AND p.bec_recommendation != '' THEN ' (' || p.bec_recommendation || ')' ELSE '' END
        WHEN p.bec_sub_date IS NOT NULL AND p.bec_sub_date != '' THEN 'Sub: ' || p.bec_sub_date ELSE '' END) AS next_bec_log,
    (CASE WHEN (p.p_red_1_date IS NULL OR p.p_red_1_date = '') AND (p.p_red_1_status IS NULL OR p.p_red_1_status = '') THEN ''
          ELSE COALESCE(p.p_red_1_date, '') || ' (' || COALESCE(p.p_red_1_status, '') || ')' END) AS next_pred_log,
    COALESCE(p.final_signed_date, '') AS next_signed_date,
    COALESCE(p.sa_start_date, '') AS next_start_date,
    COALESCE(p.sa_end_date, '') AS next_end_date,
    COALESCE(p.process_status, '') AS next_proc_status,
    (SELECT GROUP_CONCAT(h.sa_provider || ' [' || h.sa_start_date || '-' || h.sa_end_date || ']', ' | ') FROM sa_history h WHERE LOWER(h.file_no) = LOWER(i.file_no)) AS past_sa_history,
    i.remarks
FROM inventory i
LEFT JOIN sa_procurement_track p ON i.file_no = p.file_no
ORDER BY i.id ASC;
"""

HEADERS_36 = [
    "ID", "File NO", "Equipment Name", "Make", "Model", "QTY", "Serial Number(s)", "Location", "Local Agent",
    "Installed Date", "Warranty Period", "Warranty End Date", "Need S/A as P/O", "How Received",
    "Current S/A", "S/A Provider", "S/A Valid Up To", "Current S/A Start", "Current S/A End",
    "Year 1 Cost", "Year 2 Cost", "Year 3 Cost", "Year 4 Cost", "Year 5 Cost",
    "Upcoming S/A Process Type", "Inv. Holder Consent Log", "Doc Request Date", "Reminders Log",
    "BEC Recommendation Log", "Price Negotiation Log", "Final Agreement Signed Date",
    "Upcoming S/A Start Date", "Upcoming S/A End Date", "Overall Procurement Status",
    "Past S/A Archive History", "Remarks"
]

# ==============================================================================
# 2. MAIN APPLICATION CLASS
# ==============================================================================
class THPEquipmentApp(ttk.Window):
    def __init__(self):
        super().__init__(
            title="Medical Equipment Maintenance Management System - Teaching Hospital Peradeniya v1.0",
            themename="superhero",
            size=(1300, 850),
            minsize=(1024, 700)
        )
        init_database()
        self.root_container = ttk.Frame(self)
        self.root_container.pack(fill=BOTH, expand=True)
        self.show_landing_page()

    def clear_container(self):
        for w in self.root_container.winfo_children():
            w.destroy()

    # --------------------------------------------------------------------------
    # LANDING PAGE (මුල් පිටුව)
    # --------------------------------------------------------------------------
    def show_landing_page(self):
        self.clear_container()

        # Root scrollable canvas ensuring 100% responsiveness on any laptop/monitor resolution
        landing_canvas = tk.Canvas(self.root_container, bg="#1e293b", highlightthickness=0)
        landing_vsb = ttk.Scrollbar(self.root_container, orient=VERTICAL, command=landing_canvas.yview)
        landing_canvas.configure(yscrollcommand=landing_vsb.set)

        landing_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        landing_vsb.pack(side=RIGHT, fill=Y)

        inner_center = ttk.Frame(landing_canvas, padding=(25, 12))
        frame_win = landing_canvas.create_window((0, 0), window=inner_center, anchor="nw")

        def _on_frame_cfg(e):
            landing_canvas.configure(scrollregion=landing_canvas.bbox("all"))

        def _on_canvas_cfg(e):
            landing_canvas.itemconfig(frame_win, width=e.width)

        inner_center.bind("<Configure>", _on_frame_cfg)
        landing_canvas.bind("<Configure>", _on_canvas_cfg)

        def _on_mw(e):
            if landing_canvas.winfo_exists():
                landing_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        landing_canvas.bind_all("<MouseWheel>", _on_mw)

        # Top Bar: Status Indicator (Left) & Prominent Admin & Settings (Right - Design 3)
        top_bar = ttk.Frame(inner_center)
        top_bar.pack(fill=X, pady=(0, 10))

        status_box = ttk.Frame(top_bar)
        status_box.pack(side=LEFT)
        status_canvas = tk.Canvas(status_box, width=12, height=12, bg="#1e293b", highlightthickness=0)
        status_canvas.pack(side=LEFT, padx=(0, 6))
        status_canvas.create_oval(2, 2, 10, 10, fill="#10b981", outline="#34d399", width=1)
        tk.Label(
            status_box,
            text="SYSTEM ACTIVE • ONLINE",
            font=("Consolas", 9, "bold"),
            fg="#10b981",
            bg="#1e293b"
        ).pack(side=LEFT)

        admin_box = ttk.Frame(top_bar)
        admin_box.pack(side=RIGHT)
        ttk.Button(
            admin_box,
            text="⚙️ Admin & Settings",
            command=self.request_admin_access,
            bootstyle="primary",
            cursor="hand2"
        ).pack(side=RIGHT)

        # Header Area: Centered ECG Pulse Icon ABOVE Title + Version Tag
        hdr_box = ttk.Frame(inner_center)
        hdr_box.pack(pady=(0, 6))

        # ECG Pulse Canvas Centered ABOVE Title
        pulse_box = ttk.Frame(hdr_box)
        pulse_box.pack(anchor="center", pady=(0, 3))
        canvas = tk.Canvas(pulse_box, width=50, height=32, bg="#1e293b", highlightthickness=1, highlightbackground="#0284c7")
        canvas.pack(anchor="center")
        canvas.create_line(4, 16, 12, 16, fill="#38bdf8", width=2)
        canvas.create_line(12, 16, 18, 5, fill="#38bdf8", width=2)
        canvas.create_line(18, 5, 25, 27, fill="#38bdf8", width=2)
        canvas.create_line(25, 27, 32, 9, fill="#38bdf8", width=2)
        canvas.create_line(32, 9, 38, 16, fill="#38bdf8", width=2)
        canvas.create_line(38, 16, 46, 16, fill="#38bdf8", width=2)

        t_frame = ttk.Frame(hdr_box)
        t_frame.pack(anchor="center")
        ttk.Label(t_frame, text="Medical Equipment Maintenance Management System", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        ttk.Label(t_frame, text=" v1.0 ", font=("Consolas", 10, "bold"), bootstyle="info-inverse").pack(side=LEFT, padx=8)
        ttk.Label(hdr_box, text="🏥 Teaching Hospital - Peradeniya", font=("Segoe UI", 10, "bold"), bootstyle="secondary").pack(anchor="center", pady=(1, 0))

        # Center Search Bar with 360° View Button
        s_box = ttk.Frame(inner_center)
        s_box.pack(fill=X, padx=40, pady=(0, 12))
        self.home_search_var = tk.StringVar()
        self.home_search_entry = ttk.Entry(s_box, textvariable=self.home_search_var, font=("Segoe UI", 11))
        self.home_search_entry.pack(side=LEFT, ipady=5, padx=(0, 8), fill=X, expand=True)
        self.home_search_entry.insert(0, "Search Equipment by File NO, Name, Location or 360° View...")
        self.home_search_entry.bind("<FocusIn>", lambda e: self.home_search_entry.delete(0, tk.END) if "Search Equipment" in self.home_search_entry.get() else None)
        self.home_search_entry.bind("<Return>", lambda e: self.trigger_search())

        ttk.Button(s_box, text="👁️ 360° View", command=self.trigger_search, bootstyle="info", cursor="hand2", width=12).pack(side=RIGHT, ipady=4, padx=(6, 0))
        ttk.Button(s_box, text="✖ Clear", command=lambda: self.home_search_entry.delete(0, tk.END), bootstyle="secondary-outline", cursor="hand2", width=10).pack(side=RIGHT, ipady=4)

        # -------------------------------------------------------------
        # HIGH-VISIBILITY PROMINENT EXPIRY ALERTS NOTIFICATION BOARD
        # Positioned right under Search Bar so it is IMMEDIATELY VISIBLE at eye level!
        # -------------------------------------------------------------
        self.render_standalone_expiry_strip(inner_center)

        # 4 Main Operational Cards Grid (2x2) - Compact Height
        grid = ttk.Frame(inner_center)
        grid.pack(fill=BOTH, expand=True, padx=40, pady=(0, 8))
        grid.columnconfigure(0, weight=1, minsize=320)
        grid.columnconfigure(1, weight=1, minsize=320)

        # Card 1: Asset Master Registry
        self.create_card(
            grid,
            "➕ 1. ASSET MASTER REGISTRY",
            "Primary equipment registration, multi-unit serial numbers, warranty end dates & ward placement mapping.",
            "Core Asset Database",
            "success",
            lambda: self.open_module("asset")
        ).grid(row=0, column=0, padx=8, pady=5, sticky="nsew")

        # Card 2: S/A Contracts Hub
        self.create_card(
            grid,
            "📋 2. S/A CONTRACTS HUB",
            "S/A Procurement Track Pipeline (Stages 1-8), BEC Evaluations, Agreement Signing & Payment Ledger.",
            "Contract Pipeline & Ledger (2 Modules)",
            "primary",
            lambda: self.open_module("sa")
        ).grid(row=0, column=1, padx=8, pady=5, sticky="nsew")

        # Card 3: Repairs & Breakdowns
        self.create_card(
            grid,
            "🛠️ 3. REPAIRS & BREAKDOWNS",
            "Log breakdown requests, authorized agent intimations, quotation estimates, sanction approvals & settlements.",
            "Corrective Maintenance Pipeline",
            "warning",
            lambda: self.open_module("repairs")
        ).grid(row=1, column=0, padx=8, pady=5, sticky="nsew")

        # Card 4: Consolidated Inventory (Master 36-Col Matrix)
        self.create_card(
            grid,
            "🗂️ 4. CONSOLIDATED INVENTORY",
            "Master 36-column equipment matrix syncing core asset registry, S/A contract terms, procurement logs & vouchers.",
            "Master 36-Col Matrix (All Equipments)",
            "info",
            lambda: self.open_module("inventory")
        ).grid(row=1, column=1, padx=8, pady=5, sticky="nsew")

    def request_admin_access(self):
        """Security Gate: Prompts for Admin PIN before opening Settings."""
        from tkinter import simpledialog
        pin = simpledialog.askstring(
            "🔐 Admin Security Gate",
            "Enter Admin PIN / Master Password to access Settings:\n(Default initial PIN: admin123)",
            show="*"
        )
        if pin and pin.strip() == "admin123":
            self.open_module("settings")
        elif pin:
            messagebox.showerror("Access Denied", "Incorrect Admin PIN / Master Password.\nAccess to System Administration & Settings is restricted.")

    def render_standalone_expiry_strip(self, parent):
        """Interactive Expiry Alerts Notification Strip with Red-Amber glow and live counts."""
        today = datetime.date.today()
        d60 = today + datetime.timedelta(days=60)
        d90 = today + datetime.timedelta(days=90)
        today_str = today.strftime("%Y/%m/%d")
        d60_str = d60.strftime("%Y/%m/%d")
        d90_str = d90.strftime("%Y/%m/%d")

        sa_expired = 0
        sa_exp_60 = 0
        war_exp_90 = 0
        consent_pending = 0

        try:
            with db_connection() as conn:
                rows = conn.execute("""
                    SELECT i.sa_valid_upto, i.current_sa_end, i.warranty_end_date, i.current_sa,
                           p.inv_holder_sent_date, p.inv_holder_recv_date
                    FROM inventory i
                    LEFT JOIN sa_procurement_track p ON i.file_no = p.file_no;
                """).fetchall()

                for r in rows:
                    sa_date = r["sa_valid_upto"] or r["current_sa_end"]
                    if sa_date and len(str(sa_date).strip()) >= 10:
                        sd = str(sa_date)[:10].replace("-", "/")
                        if sd < today_str and r["current_sa"] == "Yes":
                            sa_expired += 1
                        elif today_str <= sd <= d60_str:
                            sa_exp_60 += 1

                    war_date = r["warranty_end_date"]
                    if war_date and len(str(war_date).strip()) >= 10:
                        wd = str(war_date)[:10].replace("-", "/")
                        if today_str <= wd <= d90_str:
                            war_exp_90 += 1

                    if r["inv_holder_sent_date"] and not r["inv_holder_recv_date"]:
                        consent_pending += 1
        except Exception:
            pass

        # Streamlined High-Visibility Expiry Alerts Strip (Clean Single-Line Border)
        card_box = ttk.LabelFrame(
            parent,
            text=" ⚠️ EXPIRY ALERTS (කල්ඉකුත්වීමේ පූර්ව නිවේදන පුවරුව) ",
            padding=8,
            bootstyle="danger"
        )
        card_box.pack(fill=X, padx=40, pady=(0, 10))

        top_row = ttk.Frame(card_box)
        top_row.pack(fill=X, pady=(0, 4))

        tl = ttk.Frame(top_row)
        tl.pack(side=LEFT)
        ttk.Label(tl, text="🔴", font=("Segoe UI", 10)).pack(side=LEFT, padx=(0, 4))
        ttk.Label(tl, text="EXPIRY ALERTS", font=("Segoe UI", 11, "bold"), bootstyle="danger").pack(side=LEFT, padx=(0, 8))
        ttk.Label(tl, text="— S/A & Warranty Expirations with Action Trackers", font=("Segoe UI", 8), bootstyle="secondary").pack(side=LEFT)

        ttk.Button(top_row, text="Open Dashboard →", command=lambda: self.open_module("alerts"), bootstyle="danger-outline", cursor="hand2").pack(side=RIGHT)

        # 4 Compact Inline Stat Tiles
        t_grid = ttk.Frame(card_box)
        t_grid.pack(fill=X)
        t_grid.columnconfigure(0, weight=1)
        t_grid.columnconfigure(1, weight=1)
        t_grid.columnconfigure(2, weight=1)
        t_grid.columnconfigure(3, weight=1)

        stat_items = [
            ("🚨 S/A Expired", f"{sa_expired} Unit(s)", "Urgent Renewal", "danger"),
            ("⏳ S/A < 60 Days", f"{sa_exp_60} Unit(s)", "Quotation Due", "warning"),
            ("🛡️ War. < 90 Days", f"{war_exp_90} Unit(s)", "Post-War S/A", "info"),
            ("📝 Consent Pending", f"{consent_pending} Unit(s)", "Ward Consent", "secondary")
        ]

        for col_idx, (st_title, st_count, st_sub, st_style) in enumerate(stat_items):
            tile = ttk.Frame(t_grid, padding=5, bootstyle=f"{st_style}")
            tile.grid(row=0, column=col_idx, padx=3, pady=2, sticky="nsew")
            ttk.Label(tile, text=st_title, font=("Segoe UI", 8, "bold"), bootstyle=f"inverse-{st_style}").pack(anchor=W)
            ttk.Label(tile, text=st_count, font=("Consolas", 10, "bold"), bootstyle=f"inverse-{st_style}").pack(anchor=W)
            ttk.Label(tile, text=st_sub, font=("Segoe UI", 7), bootstyle=f"inverse-{st_style}").pack(anchor=W)
            tile.bind("<Button-1>", lambda e: self.open_module("alerts"))

        card_box.bind("<Button-1>", lambda e: self.open_module("alerts"))

    def create_card(self, parent, title, desc, tag, style, command):
        f = ttk.Frame(parent, padding=(10, 6), bootstyle="secondary")
        t = ttk.Label(f, text=title, font=("Segoe UI", 10, "bold"), cursor="hand2")
        t.pack(anchor=W)
        t.bind("<Button-1>", lambda e: command())
        d = ttk.Label(f, text=desc, font=("Segoe UI", 8), wraplength=310)
        d.pack(anchor=W, pady=2)
        bot = ttk.Frame(f)
        bot.pack(fill=X, pady=(2, 0))
        ttk.Label(bot, text=f" {tag} ", font=("Segoe UI", 7, "bold"), bootstyle=f"{style}-inverse").pack(side=LEFT)
        ttk.Button(bot, text="Open →", command=command, bootstyle=f"{style}-link", cursor="hand2").pack(side=RIGHT)
        f.bind("<Button-1>", lambda e: command())
        return f

    # --------------------------------------------------------------------------
    # DEDICATED MODULE PAGES WITH HEADER (BACK BUTTON & QUICK LOOKUP)
    # --------------------------------------------------------------------------
    def open_module(self, module_name):
        self.clear_container()

        # Focused Header Bar: ONLY [Back to Home] + Dedicated Page Title + Quick Lookup
        hbar = ttk.Frame(self.root_container, padding=(15, 10), bootstyle="dark")
        hbar.pack(fill=X)

        left = ttk.Frame(hbar)
        left.pack(side=LEFT)
        ttk.Button(left, text="← 🏠 මුල් පිටුව (Home)", command=self.show_landing_page, bootstyle="secondary-outline").pack(side=LEFT, padx=(0, 15))

        titles = {
            "asset": ("➕ 1. Asset Master Registry", "success"),
            "sa": ("📋 2. S/A Contracts Hub", "primary"),
            "repairs": ("🛠️ 3. Equipment Repairs & Maintenance Hub", "warning"),
            "inventory": ("🗂️ 4. Consolidated Inventory (Master 36-Col Matrix)", "info"),
            "alerts": ("⚠️ Expiry & Action Alerts Dashboard", "danger"),
            "settings": ("⚙️ System Administration & Settings", "secondary")
        }
        t_text, t_style = titles.get(module_name, ("Module", "primary"))
        ttk.Label(left, text=t_text, font=("Segoe UI", 12, "bold"), bootstyle=t_style).pack(side=LEFT)

        # Quick Lookup in Inner Header (Option 2)
        right = ttk.Frame(hbar)
        right.pack(side=RIGHT)
        ttk.Label(right, text="Quick Lookup:", font=("Segoe UI", 8)).pack(side=LEFT, padx=4)
        self.inner_search_entry = ttk.Entry(right, width=20)
        self.inner_search_entry.pack(side=LEFT, padx=(0, 6))
        self.inner_search_entry.bind("<Return>", lambda e: self.trigger_inner_search())
        ttk.Button(right, text="👁️ 360° Profile", command=self.trigger_inner_search, bootstyle="info-outline").pack(side=LEFT)

        # Content Frame
        cframe = ttk.Frame(self.root_container)
        cframe.pack(fill=BOTH, expand=True)

        if module_name == "asset":
            self.render_asset_module(cframe)
        elif module_name == "sa":
            self.render_sa_module(cframe)
        elif module_name == "repairs":
            self.render_repairs_module(cframe)
        elif module_name == "inventory":
            self.render_inventory_module(cframe)
        elif module_name == "alerts":
            self.render_alerts_module(cframe)
        elif module_name == "settings":
            self.render_settings_module(cframe)

    def render_asset_module(self, parent):
        try:
            from mod_asset_registry import AssetRegistryModule
            AssetRegistryModule(parent, on_open_procurement=self.open_procurement_track_direct).pack(fill=BOTH, expand=True)
        except ImportError:
            self._render_standalone_fallback(parent, "inventory", "➕ 1. Asset Master Registry")

    def render_sa_module(self, parent):
        try:
            from mod_sa_hub import SAContractsHubModule
            self.current_sa_hub = SAContractsHubModule(
                parent, 
                show_profile_callback=self.open_360_profile,
                on_back_to_asset=lambda: self.open_module("asset")
            )
            self.current_sa_hub.pack(fill=BOTH, expand=True)
        except ImportError:
            self._render_standalone_fallback(parent, "sa_procurement_track", "📋 2. S/A Contracts Hub")

    def render_inventory_module(self, parent):
        try:
            from sa_submodules.sa_sheet import SASheetView
            SASheetView(parent, show_profile_callback=self.open_360_profile).pack(fill=BOTH, expand=True)
        except ImportError:
            self._render_standalone_fallback(parent, "inventory", "🗂️ 4. Consolidated Inventory (36 Columns)")

    def render_alerts_module(self, parent):
        try:
            from sa_submodules.sa_alerts import SAAlertsView
            SAAlertsView(parent, on_open_procurement=self.open_procurement_track_direct).pack(fill=BOTH, expand=True)
        except ImportError:
            self._render_standalone_fallback(parent, "alerts", "⚠️ Expiry & Action Alerts Dashboard")

    def open_procurement_track_direct(self, file_no=None):
        self.open_module("sa")
        if hasattr(self, 'current_sa_hub') and self.current_sa_hub:
            self.current_sa_hub.jump_to_procurement(file_no)

    def render_repairs_module(self, parent):
        try:
            from mod_repairs import RepairsModule
            RepairsModule(parent).pack(fill=BOTH, expand=True)
        except ImportError:
            self._render_standalone_fallback(parent, "repairs", "🛠️ 3. Repairs & Maintenance Hub")

    def render_settings_module(self, parent):
        try:
            from mod_settings import SettingsModule
            SettingsModule(parent).pack(fill=BOTH, expand=True)
        except ImportError:
            self._render_standalone_fallback(parent, "settings", "⚙️ System Administration & Settings")

    def _render_standalone_fallback(self, parent, target_type, title_label):
        """Self-contained fallback view when standalone script is executed without external module packages."""
        box = ttk.Frame(parent, padding=15)
        box.pack(fill=BOTH, expand=True)

        info_bar = ttk.Frame(box)
        info_bar.pack(fill=X, pady=(0, 10))
        ttk.Label(info_bar, text=f"{title_label} (Standalone Database View)", font=("Segoe UI", 11, "bold")).pack(side=LEFT)
        ttk.Button(info_bar, text="👁️ Open 360° Profile", command=lambda: self.trigger_inner_search(), bootstyle="info").pack(side=RIGHT)

        tree_frame = ttk.Frame(box)
        tree_frame.pack(fill=BOTH, expand=True)

        if target_type == "alerts":
            cols = ("Alert Type", "File NO", "Equipment Name", "Ward / Location", "Validity Date", "Status")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=150, anchor=W)
            today_str = datetime.date.today().strftime("%Y/%m/%d")
            with db_connection() as conn:
                rows = conn.execute("SELECT file_no, equipment_name, location, sa_valid_upto, current_sa, warranty_end_date FROM inventory;").fetchall()
                for r in rows:
                    if r["sa_valid_upto"] and str(r["sa_valid_upto"]) < today_str and r["current_sa"] == "Yes":
                        tree.insert("", END, values=("🚨 S/A Expired", r["file_no"], r["equipment_name"], r["location"], r["sa_valid_upto"], "EXPIRED"))
                    elif r["warranty_end_date"] and str(r["warranty_end_date"]) < today_str:
                        tree.insert("", END, values=("🛡️ Warranty Expired", r["file_no"], r["equipment_name"], r["location"], r["warranty_end_date"], "WAR_EXPIRED"))
                    elif r["sa_valid_upto"]:
                        tree.insert("", END, values=("📅 S/A Upcoming", r["file_no"], r["equipment_name"], r["location"], r["sa_valid_upto"], "Active S/A"))
        elif target_type == "repairs":
            cols = ("Job ID", "File NO", "Reported Date", "Fault Description", "Repair Category", "Status", "Estimate (LKR)")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=140, anchor=W)
            with db_connection() as conn:
                rows = conn.execute("SELECT id, file_no, reported_date, fault_description, repair_category, job_status, estimate_amount FROM repairs ORDER BY id DESC;").fetchall()
                for r in rows:
                    tree.insert("", END, values=(f"JOB-{r['id']:04d}", r["file_no"], r["reported_date"], r["fault_description"], r["repair_category"], r["job_status"], f"{r['estimate_amount']:,.2f}"))
        elif target_type == "sa_procurement_track":
            cols = ("File NO", "Equipment Name", "S/A Process Type", "Inv. Holder Consent", "Quotations", "BEC Rec.", "Agreement Signed", "Status")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=130, anchor=W)
            with db_connection() as conn:
                rows = conn.execute("""
                    SELECT p.file_no, i.equipment_name, p.sa_process_type, p.inv_holder_consent, 
                           p.quotation_call_date, p.bec_rec_date, p.final_signed_date, p.process_status
                    FROM sa_procurement_track p
                    LEFT JOIN inventory i ON p.file_no = i.file_no;
                """).fetchall()
                for r in rows:
                    tree.insert("", END, values=(r["file_no"], r["equipment_name"], r["sa_process_type"] or "N/A", r["inv_holder_consent"] or "Pending", r["quotation_call_date"] or "-", r["bec_rec_date"] or "-", r["final_signed_date"] or "Pending", r["process_status"] or "Active"))
        elif target_type == "settings":
            cols = ("Setting Key", "Setting Value", "Description")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=200, anchor=W)
            with db_connection() as conn:
                rows = conn.execute("SELECT setting_key, setting_value, description FROM app_settings;").fetchall()
                for r in rows:
                    tree.insert("", END, values=(r["setting_key"], r["setting_value"], r["description"]))
        else:
            cols = ("File NO", "Equipment Name", "Make", "Model", "QTY", "Location", "Local Agent", "Current S/A", "S/A Valid Up To", "Warranty End")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=120, anchor=W)
            with db_connection() as conn:
                rows = conn.execute("SELECT file_no, equipment_name, make, model, qty, location, local_agent, current_sa, sa_valid_upto, warranty_end_date FROM inventory;").fetchall()
                for r in rows:
                    tree.insert("", END, values=(r["file_no"], r["equipment_name"], r["make"], r["model"], r["qty"], r["location"], r["local_agent"] or "N/A", r["current_sa"] or "No", r["sa_valid_upto"] or "N/A", r["warranty_end_date"] or "N/A"))

        sb = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        def on_item_double_click(event):
            sel = tree.selection()
            if sel:
                vals = tree.item(sel[0], "values")
                if len(vals) >= 2:
                    f_no = vals[1] if target_type in ("alerts", "repairs") else vals[0]
                    self.open_360_profile(f_no)

        tree.bind("<Double-1>", on_item_double_click)

    def trigger_search(self):
        query = self.home_search_var.get().strip()
        if not query or "Search Equipment" in query:
            with db_connection() as conn:
                r = conn.execute("SELECT file_no FROM inventory LIMIT 1;").fetchone()
                if r: self.open_360_profile(r["file_no"])
            return
        self.search_and_display(query)

    def trigger_inner_search(self):
        query = self.inner_search_entry.get().strip()
        if query: self.search_and_display(query)

    def search_and_display(self, query):
        with db_connection() as conn:
            m = conn.execute("SELECT file_no FROM inventory WHERE LOWER(file_no) LIKE ? OR LOWER(equipment_name) LIKE ? OR LOWER(location) LIKE ? LIMIT 1;", (f"%{query.lower()}%", f"%{query.lower()}%", f"%{query.lower()}%")).fetchone()
            if m:
                self.open_360_profile(m["file_no"])
            else:
                messagebox.showinfo("Not Found", f"No record matching '{query}'.")

    def open_360_profile(self, file_no):
        with db_connection() as conn:
            inv = conn.execute("SELECT * FROM inventory WHERE file_no = ?;", (file_no,)).fetchone()
            proc = conn.execute("SELECT * FROM sa_procurement_track WHERE file_no = ?;", (file_no,)).fetchone()
            repairs = conn.execute("SELECT * FROM repairs WHERE file_no = ? ORDER BY id DESC LIMIT 5;", (file_no,)).fetchall()
            payments = conn.execute("SELECT * FROM sa_payments WHERE file_no = ? ORDER BY id DESC;", (file_no,)).fetchall()
            cfg_row = conn.execute("SELECT setting_value FROM app_settings WHERE setting_key = 'popup_checklist';").fetchone()

        if not inv: return

        cfg = json.loads(cfg_row["setting_value"]) if cfg_row and cfg_row["setting_value"] else {}

        modal = tk.Toplevel(self)
        modal.title(f"360° Asset Profile - {file_no}")
        modal.geometry("640x600")
        modal.minsize(550, 450)
        modal.grab_set()

        top = ttk.Frame(modal, padding=12, bootstyle="primary")
        top.pack(fill=X)
        ttk.Label(top, text=f"File NO: {file_no}", font=("Consolas", 10, "bold")).pack(anchor=W)
        ttk.Label(top, text=inv["equipment_name"], font=("Segoe UI", 12, "bold")).pack(anchor=W)

        scroll = ttk.ScrolledFrame(modal, padding=15)
        scroll.pack(fill=BOTH, expand=True)

        if cfg.get("basic", True):
            b1 = ttk.LabelFrame(scroll, text="Basic Equipment & Placement Details", padding=10)
            b1.pack(fill=X, pady=(0, 10))
            ttk.Label(b1, text=f"Make / Model: {inv['make']} / {inv['model']}").pack(anchor=W)
            ttk.Label(b1, text=f"Location: {inv['location']}").pack(anchor=W)
            ttk.Label(b1, text=f"Serial Number(s): {inv['serial_no'] or 'N/A'}").pack(anchor=W)
            ttk.Label(b1, text=f"Local Agent: {inv['local_agent'] or 'N/A'}").pack(anchor=W)

        if cfg.get("warranty", True):
            b2 = ttk.LabelFrame(scroll, text="Warranty Status", padding=10)
            b2.pack(fill=X, pady=(0, 10))
            ttk.Label(b2, text=f"Installed: {inv['installed_date']} | Period: {inv['warranty_period']}").pack(anchor=W)
            ttk.Label(b2, text=f"Warranty End Date: {inv['warranty_end_date']}", font=("Segoe UI", 9, "bold"), bootstyle="success").pack(anchor=W)

        if cfg.get("sa_status", True):
            b3 = ttk.LabelFrame(scroll, text="Active S/A Contract In-Force", padding=10)
            b3.pack(fill=X, pady=(0, 10))
            is_active = inv["current_sa"] == "Yes"
            ttk.Label(b3, text=f"Status: {'ACTIVE' if is_active else 'NO ACTIVE S/A'} | Provider: {inv['sa_provider'] or 'N/A'}").pack(anchor=W)
            ttk.Label(b3, text=f"Valid Up To: {inv['sa_valid_upto'] or 'N/A'}", font=("Segoe UI", 9, "bold"), bootstyle="warning").pack(anchor=W)

        if cfg.get("next_sa", True) and proc:
            b4 = ttk.LabelFrame(scroll, text="Upcoming Renewal Pipeline", padding=10)
            b4.pack(fill=X, pady=(0, 10))
            ttk.Label(b4, text=f"Process: {proc['sa_process_type'] or 'Under Quotation'}").pack(anchor=W)
            ttk.Label(b4, text=f"Signed Date: {proc['final_signed_date'] or 'Pending'} | Status: {proc['process_status'] or 'Initiated'}").pack(anchor=W)

        if cfg.get("repairs", True):
            b5 = ttk.LabelFrame(scroll, text=f"Recent Breakdown Logs ({len(repairs)})", padding=10)
            b5.pack(fill=X, pady=(0, 10))
            if repairs:
                for rep in repairs:
                    ttk.Label(b5, text=f"• {rep['reported_date']}: {rep['fault_description']} (Status: {rep['job_status']})").pack(anchor=W)
            else:
                ttk.Label(b5, text="No breakdown records logged.").pack(anchor=W)

        if cfg.get("financials", True):
            total_paid = sum(p["amount"] for p in payments)
            b6 = ttk.LabelFrame(scroll, text="Financial Vouchers & Settlement", padding=10)
            b6.pack(fill=X, pady=(0, 10))
            ttk.Label(b6, text=f"Total Settled S/A Payments: Rs. {total_paid:,.2f}", font=("Segoe UI", 9, "bold"), bootstyle="success").pack(anchor=W)

        ttk.Button(modal, text="Close", command=modal.destroy, bootstyle="secondary").pack(pady=10)

if __name__ == "__main__":
    app = THPEquipmentApp()
    app.mainloop()

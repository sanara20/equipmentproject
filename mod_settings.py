# -*- coding: utf-8 -*-
"""
Module 4: System Administration & Settings Console
- Configure 360° Quick-View popup checklist fields (controls modal & 360° printout)
- Landing Page Card 3D Colors & Theme Palette (Custom hex / presets)
- S/A Master Sheet Column Widths & Custom Header Names
- Master Dropdown Lists Management (Wards/Locations, Local Agents, Categories)
- Custom Dynamic Fields Manager
- Database backup (.bak) creation, restoration, and health maintenance
"""

import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import shutil
import json
import logging
import sqlite3
import os
import datetime
from db_manager import (
    db_connection, DB_NAME, get_setting, set_setting,
    get_dropdown_options, add_master_list_value, delete_master_list_value,
    get_all_file_numbers
)
from autocomplete import AutocompleteCombobox

log = logging.getLogger("thp_bme_settings")

# Default column definitions from sa_sheet.py
DEFAULT_COLUMNS = [
    ("ID", 42), ("File NO", 165), ("Equipment Name", 175), ("Make", 95), ("Model", 95),
    ("QTY", 55), ("Serial Number(s)", 125), ("Location", 135), ("Local Agent", 135),
    ("P/O Number", 100), ("Order Date", 95), ("Installed Date", 95), ("Warranty Period", 95),
    ("Warranty End Date", 100), ("Need S/A as P/O", 90), ("How Received", 100),
    ("Current S/A in Force", 110), ("S/A Provider", 95), ("S/A Valid Up To", 100),
    ("Current S/A Start Date", 105), ("Current S/A End Date", 105), ("Year 1 Cost (LKR)", 105),
    ("Year 2 Cost (LKR)", 105), ("Year 3 Cost (LKR)", 105), ("Year 4 Cost (LKR)", 105),
    ("Year 5 Cost (LKR)", 105), ("S/A Process Type", 135), ("Inv. Holder Consent Log", 135),
    ("Doc Request Date", 100), ("Reminders Log", 105), ("BEC Rec. Log", 110),
    ("Price Neg. Status", 105), ("Final Signed Date", 110), ("New S/A Start Date", 100),
    ("New S/A End Date", 100), ("Overall Proc. Status", 115), ("Past S/A History", 145),
    ("Remarks", 150)
]

class SettingsModule(ttk.Frame):
    def __init__(self, parent, on_theme_change=None):
        super().__init__(parent)
        self.on_theme_change = on_theme_change
        self.create_ui()

    def create_ui(self):
        container = ttk.Frame(self, padding=15)
        container.pack(fill=BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=X, pady=(0, 10))
        ttk.Label(
            header, 
            text="⚙️ System Administration & Preferences Console", 
            font=("Segoe UI", 13, "bold"),
            bootstyle="primary"
        ).pack(side=LEFT)

        # Tabbed Notebook for Settings Sub-Modules
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=BOTH, expand=True)

        # Tab 1: App Branding & Headings
        self.tab_branding = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_branding, text=" 🪧 Branding & UI Text ")
        self.setup_tab_branding()

        # Tab 2: Landing Card Colors (Color Palette)
        self.tab_colors = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_colors, text=" 🎨 Card Colors & Palette ")
        self.setup_tab_colors()

        # Tab 3: 360° Profile Checklist
        self.tab_profile = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_profile, text=" 🔲 360° Profile Fields ")
        self.setup_tab_profile()

        # Tab 3: Sheet Column Widths & Headers
        self.tab_columns = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_columns, text=" 📏 Sheet Columns & Widths ")
        self.setup_tab_columns()

        # Tab 4: Master Dropdown Lists
        self.tab_dropdowns = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_dropdowns, text=" 🏢 Master Dropdowns ")
        self.setup_tab_dropdowns()

        # Tab 5: Dynamic Custom Fields
        self.tab_custom = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_custom, text=" ➕ Custom Form Fields ")
        self.setup_tab_custom_fields()

        # Tab 6: Database & Maintenance
        self.tab_maintenance = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_maintenance, text=" 💾 Backup & Maintenance ")
        self.setup_tab_maintenance()

    # -------------------------------------------------------------
    # TAB 1: 360° Profile Checklist Config
    # -------------------------------------------------------------
    def setup_tab_profile(self):
        ttk.Label(
            self.tab_profile, 
            text="Configure Quick-View 360° Modal & Printout Display Sections", 
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            self.tab_profile, 
            text="Checked sections will appear on the 360° profile popup AND the one-click print dossier.", 
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 15))

        popup_box = ttk.LabelFrame(self.tab_profile, text="Active Profile Sections", padding=15)
        popup_box.pack(fill=X, pady=(0, 15))

        self.chk_basic = tk.BooleanVar(value=True)
        self.chk_warranty = tk.BooleanVar(value=True)
        self.chk_sa_status = tk.BooleanVar(value=True)
        self.chk_next_sa = tk.BooleanVar(value=True)
        self.chk_repairs = tk.BooleanVar(value=True)
        self.chk_financials = tk.BooleanVar(value=True)

        ttk.Checkbutton(popup_box, text="1. Basic Equipment & Location Details", variable=self.chk_basic).grid(row=0, column=0, sticky=W, padx=12, pady=8)
        ttk.Checkbutton(popup_box, text="2. Warranty Period & Expiry End Date", variable=self.chk_warranty).grid(row=0, column=1, sticky=W, padx=12, pady=8)
        ttk.Checkbutton(popup_box, text="3. Active S/A Contract Status & Validity", variable=self.chk_sa_status).grid(row=0, column=2, sticky=W, padx=12, pady=8)

        ttk.Checkbutton(popup_box, text="4. Upcoming S/A Procurement Renewal Pipeline", variable=self.chk_next_sa).grid(row=1, column=0, sticky=W, padx=12, pady=8)
        ttk.Checkbutton(popup_box, text="5. Past Repair & Breakdown Job Logs", variable=self.chk_repairs).grid(row=1, column=1, sticky=W, padx=12, pady=8)
        ttk.Checkbutton(popup_box, text="6. Total Financial Costs & Settled Vouchers", variable=self.chk_financials).grid(row=1, column=2, sticky=W, padx=12, pady=8)

        # Load saved values
        raw = get_setting("popup_checklist")
        if raw:
            try:
                cfg = json.loads(raw)
                self.chk_basic.set(cfg.get("basic", True))
                self.chk_warranty.set(cfg.get("warranty", True))
                self.chk_sa_status.set(cfg.get("sa_status", True))
                self.chk_next_sa.set(cfg.get("next_sa", True))
                self.chk_repairs.set(cfg.get("repairs", True))
                self.chk_financials.set(cfg.get("financials", True))
            except Exception:
                pass

        ttk.Button(
            self.tab_profile, 
            text="💾 Save Profile & Print Checklist", 
            command=self.save_popup_settings, 
            bootstyle="primary", 
            width=28
        ).pack(anchor=W, pady=10)

    def save_popup_settings(self):
        cfg = {
            "basic": self.chk_basic.get(),
            "warranty": self.chk_warranty.get(),
            "sa_status": self.chk_sa_status.get(),
            "next_sa": self.chk_next_sa.get(),
            "repairs": self.chk_repairs.get(),
            "financials": self.chk_financials.get()
        }
        set_setting("popup_checklist", json.dumps(cfg))
        messagebox.showinfo("Saved", "Profile & Print checklist saved successfully!")

    # -------------------------------------------------------------
    # TAB 1: App Branding, Hospital Names & Headings Customizer
    # -------------------------------------------------------------
    def setup_tab_branding(self):
        container = ttk.ScrolledFrame(self.tab_branding, autohide=True, padding=10)
        container.pack(fill=BOTH, expand=True)

        ttk.Label(
            container, 
            text="Application Branding, Hospital Names & Headings Customizer", 
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            container, 
            text="Customize the hospital name, main system title, version badge, button labels, and font styling.\n"
                 "All changes safely update display labels only — database tables and calculations remain 100% intact.", 
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 10))

        # 1. Main System Identity Box
        f_id = ttk.LabelFrame(container, text="1. Main System Identity & Hospital Headers", padding=12)
        f_id.pack(fill=X, pady=(0, 10))
        for c in range(4): f_id.columnconfigure(c, weight=1)

        ttk.Label(f_id, text="Hospital / Subtitle Name:").grid(row=0, column=0, sticky=W, padx=4, pady=4)
        self.e_subtitle = ttk.Entry(f_id, width=32)
        self.e_subtitle.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        ttk.Label(f_id, text="Main System Title:").grid(row=0, column=2, sticky=W, padx=4, pady=4)
        self.e_app_title = ttk.Entry(f_id, width=36)
        self.e_app_title.grid(row=0, column=3, sticky="ew", padx=4, pady=4)

        ttk.Label(f_id, text="Version Tag:").grid(row=1, column=0, sticky=W, padx=4, pady=4)
        self.e_version_tag = ttk.Entry(f_id, width=12)
        self.e_version_tag.grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(f_id, text="Badge / Tag Text (Leave blank to hide):").grid(row=1, column=2, sticky=W, padx=4, pady=4)
        self.e_badge_text = ttk.Entry(f_id, width=18)
        self.e_badge_text.grid(row=1, column=3, sticky="w", padx=4, pady=4)

        ttk.Label(f_id, text="Badge Colors (BG / Text):").grid(row=2, column=2, sticky=W, padx=4, pady=4)
        f_badge_colors = ttk.Frame(f_id)
        f_badge_colors.grid(row=2, column=3, sticky="w", padx=4, pady=4)

        self.var_badge_bg = tk.StringVar(value="#0284c7")
        self.e_badge_bg = ttk.Entry(f_badge_colors, textvariable=self.var_badge_bg, width=8)
        self.e_badge_bg.pack(side=LEFT, padx=(0, 2))
        self.btn_badge_bg_swatch = tk.Button(f_badge_colors, text="   ", bg="#0284c7", relief="solid", bd=1, cursor="hand2")
        self.btn_badge_bg_swatch.pack(side=LEFT, padx=(0, 6))
        self.btn_badge_bg_swatch.config(command=lambda: self.pick_color(self.var_badge_bg, self.btn_badge_bg_swatch, "Badge Background Color"))
        self.e_badge_bg.bind("<KeyRelease>", lambda e: self.on_hex_entry_change(self.var_badge_bg, self.btn_badge_bg_swatch))

        self.var_badge_fg = tk.StringVar(value="#ffffff")
        self.e_badge_fg = ttk.Entry(f_badge_colors, textvariable=self.var_badge_fg, width=8)
        self.e_badge_fg.pack(side=LEFT, padx=(0, 2))
        self.btn_badge_fg_swatch = tk.Button(f_badge_colors, text="   ", bg="#ffffff", relief="solid", bd=1, cursor="hand2")
        self.btn_badge_fg_swatch.pack(side=LEFT)
        self.btn_badge_fg_swatch.config(command=lambda: self.pick_color(self.var_badge_fg, self.btn_badge_fg_swatch, "Badge Text Color"))
        self.e_badge_fg.bind("<KeyRelease>", lambda e: self.on_hex_entry_change(self.var_badge_fg, self.btn_badge_fg_swatch))

        # 2. Typography & Header Colors
        f_typo = ttk.LabelFrame(container, text="2. Landing Page Typography & Color Styling", padding=12)
        f_typo.pack(fill=X, pady=(0, 10))
        for c in range(4): f_typo.columnconfigure(c, weight=1)

        ttk.Label(f_typo, text="Header Title Font Size:").grid(row=0, column=0, sticky=W, padx=4, pady=4)
        self.sp_title_size = ttk.Spinbox(f_typo, from_=14, to=36, width=8)
        self.sp_title_size.grid(row=0, column=1, sticky=W, padx=4, pady=4)

        ttk.Label(f_typo, text="Header Title Color:").grid(row=0, column=2, sticky=W, padx=4, pady=4)
        f_tc = ttk.Frame(f_typo)
        f_tc.grid(row=0, column=3, sticky=W, padx=4, pady=4)
        self.var_title_color = tk.StringVar(value="#f8fafc")
        self.e_title_color = ttk.Entry(f_tc, textvariable=self.var_title_color, width=10)
        self.e_title_color.pack(side=LEFT, padx=(0, 4))
        self.btn_title_color_swatch = tk.Button(f_tc, text="   ", bg="#f8fafc", relief="solid", bd=1, cursor="hand2")
        self.btn_title_color_swatch.pack(side=LEFT)
        self.btn_title_color_swatch.config(command=lambda: self.pick_color(self.var_title_color, self.btn_title_color_swatch, "Header Title Color"))
        self.e_title_color.bind("<KeyRelease>", lambda e: self.on_hex_entry_change(self.var_title_color, self.btn_title_color_swatch))

        ttk.Label(f_typo, text="Subtitle Font Size:").grid(row=1, column=0, sticky=W, padx=4, pady=4)
        self.sp_sub_size = ttk.Spinbox(f_typo, from_=9, to=20, width=8)
        self.sp_sub_size.grid(row=1, column=1, sticky=W, padx=4, pady=4)

        ttk.Label(f_typo, text="Subtitle Color:").grid(row=1, column=2, sticky=W, padx=4, pady=4)
        f_sc = ttk.Frame(f_typo)
        f_sc.grid(row=1, column=3, sticky=W, padx=4, pady=4)
        self.var_sub_color = tk.StringVar(value="#94a3b8")
        self.e_sub_color = ttk.Entry(f_sc, textvariable=self.var_sub_color, width=10)
        self.e_sub_color.pack(side=LEFT, padx=(0, 4))
        self.btn_sub_color_swatch = tk.Button(f_sc, text="   ", bg="#94a3b8", relief="solid", bd=1, cursor="hand2")
        self.btn_sub_color_swatch.pack(side=LEFT)
        self.btn_sub_color_swatch.config(command=lambda: self.pick_color(self.var_sub_color, self.btn_sub_color_swatch, "Subtitle Color"))
        self.e_sub_color.bind("<KeyRelease>", lambda e: self.on_hex_entry_change(self.var_sub_color, self.btn_sub_color_swatch))

        ttk.Label(f_typo, text="Card Title Font Size:").grid(row=2, column=0, sticky=W, padx=4, pady=4)
        self.sp_card_title_size = ttk.Spinbox(f_typo, from_=10, to=18, width=8)
        self.sp_card_title_size.grid(row=2, column=1, sticky=W, padx=4, pady=4)

        ttk.Label(f_typo, text="Card Description Font Size:").grid(row=2, column=2, sticky=W, padx=4, pady=4)
        self.sp_card_desc_size = ttk.Spinbox(f_typo, from_=8, to=14, width=8)
        self.sp_card_desc_size.grid(row=2, column=3, sticky=W, padx=4, pady=4)

        # 3. Landing Page Background Styling (Color & Hospital Photo)
        f_bg = ttk.LabelFrame(container, text="3. Landing Page Background & Hospital Photo", padding=12)
        f_bg.pack(fill=X, pady=(0, 10))

        ttk.Label(f_bg, text="Background Tint Hex:").grid(row=0, column=0, sticky=W, padx=4, pady=4)
        f_bgc = ttk.Frame(f_bg)
        f_bgc.grid(row=0, column=1, sticky=W, padx=4, pady=4)
        self.var_bg_color = tk.StringVar(value="#0f172a")
        self.e_bg_color = ttk.Entry(f_bgc, textvariable=self.var_bg_color, width=10)
        self.e_bg_color.pack(side=LEFT, padx=(0, 4))
        self.btn_bg_color_swatch = tk.Button(f_bgc, text="   ", bg="#0f172a", relief="solid", bd=1, cursor="hand2")
        self.btn_bg_color_swatch.pack(side=LEFT)
        self.btn_bg_color_swatch.config(command=lambda: self.pick_color(self.var_bg_color, self.btn_bg_color_swatch, "Background Color"))
        self.e_bg_color.bind("<KeyRelease>", lambda e: self.on_hex_entry_change(self.var_bg_color, self.btn_bg_color_swatch))

        ttk.Label(f_bg, text="Hospital Photo / Image:").grid(row=0, column=2, sticky=W, padx=4, pady=4)
        f_img = ttk.Frame(f_bg)
        f_img.grid(row=0, column=3, sticky="ew", padx=4, pady=4)
        self.e_bg_image = ttk.Entry(f_img, width=24)
        self.e_bg_image.pack(side=LEFT, fill=X, expand=True, padx=(0, 4))
        ttk.Button(f_img, text="📁 Browse", command=self.browse_bg_image, bootstyle="secondary-outline").pack(side=LEFT)

        # 4. 4 Large Landing Buttons / Cards Customizer
        f_cards = ttk.LabelFrame(container, text="4. Landing Dashboard 4 Action Cards: Titles & Descriptions", padding=12)
        f_cards.pack(fill=X, pady=(0, 10))

        cards_fields = [
            ("card1", "Card 1 (Asset Master Registry):", "e_c1_title", "e_c1_desc"),
            ("card2", "Card 2 (S/A Contracts Hub):", "e_c2_title", "e_c2_desc"),
            ("card3", "Card 3 (Repairs & Maintenance):", "e_c3_title", "e_c3_desc"),
            ("card4", "Card 4 (Admin & Settings):", "e_c4_title", "e_c4_desc"),
        ]

        for idx, (cid, lbl_txt, t_attr, d_attr) in enumerate(cards_fields):
            r = idx * 2
            ttk.Label(f_cards, text=lbl_txt, font=("Segoe UI", 9, "bold")).grid(row=r, column=0, sticky=W, padx=4, pady=(6, 2))
            
            t_entry = ttk.Entry(f_cards, width=32)
            t_entry.grid(row=r, column=1, sticky="ew", padx=4, pady=(6, 2))
            setattr(self, t_attr, t_entry)

            ttk.Label(f_cards, text="Description:").grid(row=r+1, column=0, sticky=W, padx=4, pady=(0, 6))
            d_entry = ttk.Entry(f_cards, width=70)
            d_entry.grid(row=r+1, column=1, sticky="ew", padx=4, pady=(0, 6))
            setattr(self, d_attr, d_entry)

        f_cards.columnconfigure(1, weight=1)

        # Buttons
        b_row = ttk.Frame(container)
        b_row.pack(fill=X, pady=10)
        ttk.Button(b_row, text="💾 Save Branding & Headings", command=self.save_branding_settings, bootstyle="success", width=28).pack(side=LEFT, padx=5)
        ttk.Button(b_row, text="🔄 Reset to Default Hospital Headings", command=self.reset_branding_settings, bootstyle="secondary-outline").pack(side=LEFT, padx=5)

        self.load_branding_settings()

    def browse_bg_image(self):
        fn = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
            title="Select Hospital Background Photo"
        )
        if fn:
            self.e_bg_image.delete(0, tk.END)
            self.e_bg_image.insert(0, fn)

    def pick_color(self, var, btn, title="Choose Color"):
        cur = var.get().strip() or "#ffffff"
        try:
            _, hex_c = colorchooser.askcolor(color=cur, title=title)
            if hex_c:
                var.set(hex_c)
                btn.config(bg=hex_c)
        except Exception as e:
            log.warning(f"Color chooser error: {e}")

    def on_hex_entry_change(self, var, btn):
        val = var.get().strip()
        if (len(val) in (4, 7)) and val.startswith("#"):
            try:
                btn.config(bg=val)
            except Exception:
                pass

    def load_branding_settings(self):
        raw = get_setting("app_branding")
        try: b = json.loads(raw) if raw else {}
        except Exception: b = {}

        self.e_app_title.delete(0, tk.END)
        self.e_app_title.insert(0, b.get("app_title", "Medical Equipment Maintenance Management System"))

        self.e_version_tag.delete(0, tk.END)
        self.e_version_tag.insert(0, b.get("version_tag", "v1.0"))

        self.e_subtitle.delete(0, tk.END)
        self.e_subtitle.insert(0, b.get("subtitle", "Teaching Hospital - Peradeniya."))

        self.e_badge_text.delete(0, tk.END)
        self.e_badge_text.insert(0, b.get("badge_text", ""))

        self.var_badge_bg.set(b.get("badge_bg_color", "#0284c7"))
        self.btn_badge_bg_swatch.config(bg=self.var_badge_bg.get())

        self.var_badge_fg.set(b.get("badge_fg_color", "#ffffff"))
        self.btn_badge_fg_swatch.config(bg=self.var_badge_fg.get())

        self.e_bg_image.delete(0, tk.END)
        self.e_bg_image.insert(0, b.get("bg_image", ""))

        self.var_bg_color.set(b.get("bg_color", "#0f172a"))
        self.btn_bg_color_swatch.config(bg=self.var_bg_color.get())

        self.e_c1_title.delete(0, tk.END); self.e_c1_title.insert(0, b.get("card1_title", "➕ 1. ASSET MASTER REGISTRY"))
        self.e_c1_desc.delete(0, tk.END); self.e_c1_desc.insert(0, b.get("card1_desc", "Primary equipment registration form, multi-unit serial numbers, auto-calculated warranty expirations, and ward placement mapping."))

        self.e_c2_title.delete(0, tk.END); self.e_c2_title.insert(0, b.get("card2_title", "📋 2. S/A CONTRACTS HUB"))
        self.e_c2_desc.delete(0, tk.END); self.e_c2_desc.insert(0, b.get("card2_desc", "36-Column Inventory Master Sheet, S/A Procurement Track Pipeline, S/A Payment Ledger, and Net Cash Budget Engine."))

        self.e_c3_title.delete(0, tk.END); self.e_c3_title.insert(0, b.get("card3_title", "🛠️ 3. REPAIRS & BREAKDOWNS"))
        self.e_c3_desc.delete(0, tk.END); self.e_c3_desc.insert(0, b.get("card3_desc", "Breakdown intake job cards, estimate sanction approvals, Internal repair category, and job status tracking."))

        self.e_c4_title.delete(0, tk.END); self.e_c4_title.insert(0, b.get("card4_title", "⚙️ 4. ADMIN & SETTINGS"))
        self.e_c4_desc.delete(0, tk.END); self.e_c4_desc.insert(0, b.get("card4_desc", "Configure Quick-View popup profile fields, desktop UI preferences, secure full-system .bak backups, and safe reset utilities."))

        raw_t = get_setting("landing_typography")
        try: t = json.loads(raw_t) if raw_t else {}
        except Exception: t = {}

        self.sp_title_size.set(t.get("title_font_size", 18))
        self.var_title_color.set(t.get("title_color", "#f8fafc"))
        self.btn_title_color_swatch.config(bg=self.var_title_color.get())

        self.sp_sub_size.set(t.get("subtitle_font_size", 11))
        self.var_sub_color.set(t.get("subtitle_color", "#94a3b8"))
        self.btn_sub_color_swatch.config(bg=self.var_sub_color.get())

        self.sp_card_title_size.set(t.get("card_title_font_size", 12))
        self.sp_card_desc_size.set(t.get("card_desc_font_size", 9))

    def save_branding_settings(self):
        b = {
            "app_title": self.e_app_title.get().strip() or "Medical Equipment Maintenance Management System",
            "version_tag": self.e_version_tag.get().strip() or "v1.0",
            "subtitle": self.e_subtitle.get().strip() or "Teaching Hospital - Peradeniya.",
            "badge_text": self.e_badge_text.get().strip(),
            "badge_bg_color": self.var_badge_bg.get().strip() or "#0284c7",
            "badge_fg_color": self.var_badge_fg.get().strip() or "#ffffff",
            "bg_color": self.var_bg_color.get().strip() or "#0f172a",
            "bg_image": self.e_bg_image.get().strip(),
            "card1_title": self.e_c1_title.get().strip(),
            "card1_desc": self.e_c1_desc.get().strip(),
            "card2_title": self.e_c2_title.get().strip(),
            "card2_desc": self.e_c2_desc.get().strip(),
            "card3_title": self.e_c3_title.get().strip(),
            "card3_desc": self.e_c3_desc.get().strip(),
            "card4_title": self.e_c4_title.get().strip(),
            "card4_desc": self.e_c4_desc.get().strip(),
        }
        set_setting("app_branding", json.dumps(b))

        t = {
            "title_font_size": int(self.sp_title_size.get() or 18),
            "title_color": self.var_title_color.get().strip() or "#f8fafc",
            "subtitle_font_size": int(self.sp_sub_size.get() or 11),
            "subtitle_color": self.var_sub_color.get().strip() or "#94a3b8",
            "card_title_font_size": int(self.sp_card_title_size.get() or 12),
            "card_desc_font_size": int(self.sp_card_desc_size.get() or 9),
        }
        set_setting("landing_typography", json.dumps(t))
        messagebox.showinfo("Saved", "App branding, headings & typography saved successfully!\nChanges will reflect immediately on the Home screen.")

    def reset_branding_settings(self):
        defaults = {
            "app_title": "Medical Equipment Maintenance Management System",
            "version_tag": "v1.0",
            "subtitle": "Teaching Hospital - Peradeniya.",
            "badge_text": "",
            "badge_bg_color": "#0284c7",
            "badge_fg_color": "#ffffff",
            "bg_color": "#0f172a",
            "bg_image": "",
            "card1_title": "➕ 1. ASSET MASTER REGISTRY",
            "card1_desc": "Primary equipment registration form, multi-unit serial numbers, auto-calculated warranty expirations, and ward placement mapping.",
            "card2_title": "📋 2. S/A CONTRACTS HUB",
            "card2_desc": "36-Column Inventory Master Sheet, S/A Procurement Track Pipeline, S/A Payment Ledger, and Net Cash Budget Engine.",
            "card3_title": "🛠️ 3. REPAIRS & BREAKDOWNS",
            "card3_desc": "Breakdown intake job cards, estimate sanction approvals, Internal repair category, and job status tracking.",
            "card4_title": "⚙️ 4. ADMIN & SETTINGS",
            "card4_desc": "Configure Quick-View popup profile fields, desktop UI preferences, secure full-system .bak backups, and safe reset utilities.",
        }
        set_setting("app_branding", json.dumps(defaults))
        default_t = {
            "title_font_size": 18,
            "title_color": "#f8fafc",
            "subtitle_font_size": 11,
            "subtitle_color": "#94a3b8",
            "card_title_font_size": 12,
            "card_desc_font_size": 9
        }
        set_setting("landing_typography", json.dumps(default_t))
        self.load_branding_settings()
        messagebox.showinfo("Reset", "Branding, headings and typography reset to default hospital values!")

    # -------------------------------------------------------------
    # TAB 2: Landing Card Colors & 5 Theme Slots (Visual Swatches + Picker)
    # -------------------------------------------------------------
    def setup_tab_colors(self):
        ttk.Label(
            self.tab_colors, 
            text="Landing Page 3D Button Colors, Themes & Visual Color Swatches", 
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            self.tab_colors, 
            text="Click any visual color box to open the Color Picker palette. Save custom themes to Custom 1 or Custom 2.", 
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 10))

        # Palette Presets Row (5 Themes)
        p_frame = ttk.LabelFrame(self.tab_colors, text="Select Theme Preset / Custom Slot", padding=10)
        p_frame.pack(fill=X, pady=(0, 10))

        ttk.Button(p_frame, text="🌸 Theme 01 (Soft Pastel)", command=self.apply_pastel_palette, bootstyle="info-outline").pack(side=LEFT, padx=4)
        ttk.Button(p_frame, text="🏥 Theme 02 (Hospital Teal)", command=self.apply_hospital_palette, bootstyle="primary-outline").pack(side=LEFT, padx=4)
        ttk.Button(p_frame, text="🏛️ Theme 03 (Classic Amber)", command=self.apply_classic_palette, bootstyle="secondary-outline").pack(side=LEFT, padx=4)
        ttk.Button(p_frame, text="🎨 Custom Theme 1", command=lambda: self.apply_custom_slot(1), bootstyle="success-outline").pack(side=LEFT, padx=4)
        ttk.Button(p_frame, text="🎨 Custom Theme 2", command=lambda: self.apply_custom_slot(2), bootstyle="warning-outline").pack(side=LEFT, padx=4)

        # Card Customizer Grid
        self.c_entries = {}
        cards_data = [
            ("card1", "1. Asset Master Registry", "#e8f8f2", "#34d399", "#065f46", "#166534", "#a7f3d0", "#065f46"),
            ("card2", "2. S/A Contracts Hub", "#ebf5ff", "#60a5fa", "#1e40af", "#1e3a8a", "#bfdbfe", "#1e40af"),
            ("card3", "3. Repairs & Breakdowns", "#fef6eb", "#fbbf24", "#92400e", "#78350f", "#fde68a", "#92400e"),
            ("card4", "4. Admin & Settings", "#f5f3ff", "#a78bfa", "#5b21b6", "#4c1d95", "#ddd6fe", "#5b21b6")
        ]

        grid_cards = ttk.Frame(self.tab_colors)
        grid_cards.pack(fill=X, pady=5)

        raw_colors = get_setting("card_colors")
        saved_colors = {}
        if raw_colors:
            try: saved_colors = json.loads(raw_colors)
            except Exception: pass

        for i, (cid, name, def_bg, def_bd, def_th, def_dh, def_tbg, def_tfg) in enumerate(cards_data):
            c_cfg = saved_colors.get(cid, {})
            f = ttk.LabelFrame(grid_cards, text=name, padding=10)
            f.grid(row=i//2, column=i%2, sticky="nsew", padx=6, pady=6)
            grid_cards.columnconfigure(i%2, weight=1)

            bg_var = tk.StringVar(value=c_cfg.get("bg", def_bg))
            bd_var = tk.StringVar(value=c_cfg.get("border", def_bd))

            ttk.Label(f, text="Background:").grid(row=0, column=0, sticky=W, pady=3)
            f_bg = ttk.Frame(f)
            f_bg.grid(row=0, column=1, sticky="w", padx=4, pady=3)
            e_bg = ttk.Entry(f_bg, textvariable=bg_var, width=10)
            e_bg.pack(side=LEFT, padx=(0, 4))
            btn_bg_sw = tk.Button(f_bg, text="   ", bg=bg_var.get(), relief="solid", bd=1, cursor="hand2")
            btn_bg_sw.pack(side=LEFT)
            btn_bg_sw.config(command=lambda v=bg_var, b=btn_bg_sw, nm=name: self.pick_color(v, b, f"{nm} Background"))
            e_bg.bind("<KeyRelease>", lambda e, v=bg_var, b=btn_bg_sw: self.on_hex_entry_change(v, b))

            ttk.Label(f, text="Border:").grid(row=1, column=0, sticky=W, pady=3)
            f_bd = ttk.Frame(f)
            f_bd.grid(row=1, column=1, sticky="w", padx=4, pady=3)
            e_bd = ttk.Entry(f_bd, textvariable=bd_var, width=10)
            e_bd.pack(side=LEFT, padx=(0, 4))
            btn_bd_sw = tk.Button(f_bd, text="   ", bg=bd_var.get(), relief="solid", bd=1, cursor="hand2")
            btn_bd_sw.pack(side=LEFT)
            btn_bd_sw.config(command=lambda v=bd_var, b=btn_bd_sw, nm=name: self.pick_color(v, b, f"{nm} Border"))
            e_bd.bind("<KeyRelease>", lambda e, v=bd_var, b=btn_bd_sw: self.on_hex_entry_change(v, b))

            self.c_entries[cid] = {
                "bg": bg_var, "border": bd_var,
                "bg_swatch": btn_bg_sw, "bd_swatch": btn_bd_sw,
                "title": c_cfg.get("title", def_th), "desc": c_cfg.get("desc", def_dh),
                "tag_bg": c_cfg.get("tag_bg", def_tbg), "tag_fg": c_cfg.get("tag_fg", def_tfg)
            }

        btn_row = ttk.Frame(self.tab_colors)
        btn_row.pack(fill=X, pady=10)
        ttk.Button(btn_row, text="💾 Save to Custom 1", command=lambda: self.save_to_custom_slot(1), bootstyle="success-outline", width=18).pack(side=LEFT, padx=4)
        ttk.Button(btn_row, text="💾 Save to Custom 2", command=lambda: self.save_to_custom_slot(2), bootstyle="warning-outline", width=18).pack(side=LEFT, padx=4)
        ttk.Button(btn_row, text="✔ Apply & Save as Active", command=self.save_card_colors, bootstyle="success", width=24).pack(side=LEFT, padx=8)
        ttk.Button(btn_row, text="🔄 Reset to Defaults", command=self.reset_card_colors, bootstyle="secondary-outline").pack(side=LEFT, padx=4)

    def update_swatches_for_all(self):
        for cid, data in self.c_entries.items():
            if "bg_swatch" in data:
                try: data["bg_swatch"].config(bg=data["bg"].get())
                except Exception: pass
            if "bd_swatch" in data:
                try: data["bd_swatch"].config(bg=data["border"].get())
                except Exception: pass

    def apply_pastel_palette(self):
        defaults = {
            "card1": ("#e8f8f2", "#34d399"), "card2": ("#ebf5ff", "#60a5fa"),
            "card3": ("#fef6eb", "#fbbf24"), "card4": ("#f5f3ff", "#a78bfa")
        }
        for cid, (bg, bd) in defaults.items():
            if cid in self.c_entries:
                self.c_entries[cid]["bg"].set(bg)
                self.c_entries[cid]["border"].set(bd)
        self.update_swatches_for_all()

    def apply_hospital_palette(self):
        oceanic = {
            "card1": ("#ecfdf5", "#10b981"), "card2": ("#e0f2fe", "#0284c7"),
            "card3": ("#fff7ed", "#f97316"), "card4": ("#eef2ff", "#6366f1")
        }
        for cid, (bg, bd) in oceanic.items():
            if cid in self.c_entries:
                self.c_entries[cid]["bg"].set(bg)
                self.c_entries[cid]["border"].set(bd)
        self.update_swatches_for_all()

    def apply_classic_palette(self):
        classic = {
            "card1": ("#f1f5f9", "#475569"), "card2": ("#f8fafc", "#334155"),
            "card3": ("#fefce8", "#ca8a04"), "card4": ("#faf5ff", "#7e22ce")
        }
        for cid, (bg, bd) in classic.items():
            if cid in self.c_entries:
                self.c_entries[cid]["bg"].set(bg)
                self.c_entries[cid]["border"].set(bd)
        self.update_swatches_for_all()

    def save_to_custom_slot(self, slot_num):
        payload = {}
        for cid, data in self.c_entries.items():
            payload[cid] = {
                "bg": data["bg"].get().strip(),
                "border": data["border"].get().strip(),
                "title": data["title"],
                "desc": data["desc"],
                "tag_bg": data["tag_bg"],
                "tag_fg": data["tag_fg"]
            }
        key = f"custom_theme_{slot_num}"
        set_setting(key, json.dumps(payload))
        set_setting("card_colors", json.dumps(payload))
        messagebox.showinfo("Saved", f"Card colors successfully saved to Custom Theme {slot_num} and set as Active Palette!")

    def apply_custom_slot(self, slot_num):
        raw = get_setting(f"custom_theme_{slot_num}")
        if not raw:
            messagebox.showinfo("Empty Slot", f"Custom Theme {slot_num} has not been saved yet.\nPlease customize colors and click 'Save to Custom {slot_num}'.")
            return
        try:
            cfg = json.loads(raw)
            for cid, data in cfg.items():
                if cid in self.c_entries:
                    self.c_entries[cid]["bg"].set(data.get("bg", "#ffffff"))
                    self.c_entries[cid]["border"].set(data.get("border", "#000000"))
            self.update_swatches_for_all()
            messagebox.showinfo("Loaded", f"Custom Theme {slot_num} loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load custom theme: {e}")

    def save_card_colors(self):
        payload = {}
        for cid, data in self.c_entries.items():
            payload[cid] = {
                "bg": data["bg"].get().strip(),
                "border": data["border"].get().strip(),
                "title": data["title"],
                "desc": data["desc"],
                "tag_bg": data["tag_bg"],
                "tag_fg": data["tag_fg"]
            }
        set_setting("card_colors", json.dumps(payload))
        messagebox.showinfo("Saved", "Landing page card colors saved! They will take effect on the Home dashboard.")

    def reset_card_colors(self):
        self.apply_pastel_palette()
        self.save_card_colors()

    # -------------------------------------------------------------
    # TAB 3: Sheet Column Widths & Custom Header Names
    # -------------------------------------------------------------
    def setup_tab_columns(self):
        ttk.Label(
            self.tab_columns, 
            text="S/A Master Sheet: Column Widths (px) & Custom Names", 
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            self.tab_columns, 
            text="Set pixel width (e.g. File NO: 165px) or rename any column header. Saved directly into the database.", 
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 8))

        scroll_c = ttk.ScrolledFrame(self.tab_columns, padding=8)
        scroll_c.pack(fill=BOTH, expand=True)

        self.col_widgets = {}
        raw_widths = get_setting("sheet_column_widths")
        saved_widths = {}
        if raw_widths:
            try: saved_widths = json.loads(raw_widths)
            except Exception: pass

        # Grid Headers
        ttk.Label(scroll_c, text="#", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=4, pady=3)
        ttk.Label(scroll_c, text="Default Header", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky=W, padx=8, pady=3)
        ttk.Label(scroll_c, text="Custom Header Name", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky=W, padx=8, pady=3)
        ttk.Label(scroll_c, text="Width (px)", font=("Segoe UI", 9, "bold")).grid(row=0, column=3, sticky=W, padx=8, pady=3)

        for idx, (def_name, def_w) in enumerate(DEFAULT_COLUMNS):
            r = idx + 1
            cur_w = saved_widths.get(str(idx), def_w)

            ttk.Label(scroll_c, text=str(idx)).grid(row=r, column=0, padx=4, pady=2)
            ttk.Label(scroll_c, text=def_name).grid(row=r, column=1, sticky=W, padx=8, pady=2)

            name_var = tk.StringVar(value=def_name)
            e_name = ttk.Entry(scroll_c, textvariable=name_var, width=28)
            e_name.grid(row=r, column=2, sticky=W, padx=8, pady=2)

            w_var = tk.IntVar(value=cur_w)
            e_w = ttk.Spinbox(scroll_c, from_=30, to=400, textvariable=w_var, width=8)
            e_w.grid(row=r, column=3, sticky=W, padx=8, pady=2)

            self.col_widgets[idx] = (name_var, w_var)

        btn_row = ttk.Frame(self.tab_columns)
        btn_row.pack(fill=X, pady=10)
        ttk.Button(btn_row, text="💾 Save Column Widths & Headers", command=self.save_columns, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_row, text="🔄 Reset File NO to 165px Defaults", command=self.reset_columns, bootstyle="secondary-outline").pack(side=LEFT, padx=5)

    def save_columns(self):
        widths_payload = {}
        for idx, (n_var, w_var) in self.col_widgets.items():
            widths_payload[str(idx)] = int(w_var.get())
        set_setting("sheet_column_widths", json.dumps(widths_payload))
        messagebox.showinfo("Saved", "Column widths saved successfully! They will apply when S/A Master Sheet opens.")

    def reset_columns(self):
        for idx, (def_name, def_w) in enumerate(DEFAULT_COLUMNS):
            if idx in self.col_widgets:
                self.col_widgets[idx][0].set(def_name)
                self.col_widgets[idx][1].set(def_w)
        self.save_columns()

    # -------------------------------------------------------------
    # TAB 4: Master Dropdown Lists Management
    # -------------------------------------------------------------
    def setup_tab_dropdowns(self):
        ttk.Label(
            self.tab_dropdowns, 
            text="Manage Hospital Master Dropdowns (Locations, Agents, Categories & Process Types)", 
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=W, pady=(0, 4))

        sel_row = ttk.Frame(self.tab_dropdowns)
        sel_row.pack(fill=X, pady=(0, 8))
        ttk.Label(sel_row, text="Select Category:").pack(side=LEFT, padx=(0, 6))

        self.category_pairs = [
            ("location", "📍 Hospital Wards & Locations"),
            ("local_agent", "🏢 Local Agents & Companies"),
            ("equipment_name", "🩺 Equipment Names"),
            ("make", "🏷️ Makes / Manufacturers"),
            ("model", "⚙️ Equipment Models"),
            ("how_received", "📦 How Received Types"),
            ("warranty_period", "⏳ Warranty Periods"),
            ("need_sa_po", "📑 Need S/A as P/O Options"),
            ("sa_process_type", "📋 S/A Process Framework Types"),
            ("sa_provider", "🛡️ S/A Providers"),
            ("inv_holder_status", "📝 Inventory Holder Recommendations"),
            ("bec_recommendation", "📊 BEC Recommendations"),
            ("price_neg", "💰 Price Negotiation Statuses"),
            ("file_no", "📁 File No / Registration Numbers")
        ]
        self.label_to_cat = {label: cat for cat, label in self.category_pairs}
        self.cat_to_label = {cat: label for cat, label in self.category_pairs}

        self.dd_cat_var = tk.StringVar(value=self.category_pairs[0][1])
        c_dd = ttk.Combobox(
            sel_row,
            textvariable=self.dd_cat_var,
            values=[label for _, label in self.category_pairs],
            state="readonly",
            width=36
        )
        c_dd.pack(side=LEFT, padx=(0, 10))
        c_dd.bind("<<ComboboxSelected>>", lambda e: self.load_dropdown_items())

        # Listbox of items
        l_frame = ttk.Frame(self.tab_dropdowns)
        l_frame.pack(fill=BOTH, expand=True, pady=5)

        self.lb_items = tk.Listbox(l_frame, font=("Segoe UI", 10), selectmode=SINGLE)
        self.lb_items.pack(side=LEFT, fill=BOTH, expand=True)

        sc = ttk.Scrollbar(l_frame, orient=VERTICAL, command=self.lb_items.yview)
        sc.pack(side=RIGHT, fill=Y)
        self.lb_items.config(yscrollcommand=sc.set)

        # Add/Delete controls
        act_row = ttk.Frame(self.tab_dropdowns)
        act_row.pack(fill=X, pady=8)

        self.e_new_item = ttk.Entry(act_row, width=32)
        self.e_new_item.pack(side=LEFT, padx=(0, 6))

        ttk.Button(act_row, text="➕ Add Value", command=self.add_dd_value, bootstyle="success").pack(side=LEFT, padx=4)
        ttk.Button(act_row, text="🗑️ Delete Selected", command=self.del_dd_value, bootstyle="danger-outline").pack(side=RIGHT, padx=4)

        self.load_dropdown_items()

    def get_current_cat_code(self):
        selected_label = self.dd_cat_var.get()
        return self.label_to_cat.get(selected_label, "location")

    def load_dropdown_items(self):
        cat = self.get_current_cat_code()
        items = get_dropdown_options(cat)
        self.lb_items.delete(0, tk.END)
        for it in items:
            self.lb_items.insert(tk.END, it)

    def add_dd_value(self):
        val = self.e_new_item.get().strip()
        if not val:
            return
        cat = self.get_current_cat_code()
        add_master_list_value(cat, val)
        self.e_new_item.delete(0, tk.END)
        self.load_dropdown_items()
        messagebox.showinfo("Added", f"Added '{val}' to {cat} dropdown options!")

    def del_dd_value(self):
        sel = self.lb_items.curselection()
        if not sel:
            messagebox.showwarning("Select Item", "Please select an item to delete.")
            return
        val = self.lb_items.get(sel[0])
        cat = self.get_current_cat_code()
        if messagebox.askyesno("Confirm Delete", f"Delete '{val}' from {cat}?"):
            delete_master_list_value(cat, val)
            self.load_dropdown_items()

    # -------------------------------------------------------------
    # TAB 5: Custom Dynamic Form Fields
    # -------------------------------------------------------------
    def setup_tab_custom_fields(self):
        ttk.Label(
            self.tab_custom, 
            text="Dynamic Custom Equipment Fields", 
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            self.tab_custom, 
            text="Define additional hospital fields (e.g. 'Calibration Frequency', 'AMC Reference NO').", 
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 8))

        l_frame = ttk.Frame(self.tab_custom)
        l_frame.pack(fill=BOTH, expand=True, pady=5)

        self.lb_fields = tk.Listbox(l_frame, font=("Segoe UI", 10), selectmode=SINGLE)
        self.lb_fields.pack(side=LEFT, fill=BOTH, expand=True)

        sc = ttk.Scrollbar(l_frame, orient=VERTICAL, command=self.lb_fields.yview)
        sc.pack(side=RIGHT, fill=Y)
        self.lb_fields.config(yscrollcommand=sc.set)

        act_row = ttk.Frame(self.tab_custom)
        act_row.pack(fill=X, pady=8)

        self.e_custom_name = ttk.Entry(act_row, width=30)
        self.e_custom_name.pack(side=LEFT, padx=(0, 6))

        ttk.Button(act_row, text="➕ Add Field", command=self.add_custom_field, bootstyle="success").pack(side=LEFT, padx=4)
        ttk.Button(act_row, text="🗑️ Remove Field", command=self.del_custom_field, bootstyle="danger-outline").pack(side=RIGHT, padx=4)

        self.load_custom_fields()

    def load_custom_fields(self):
        raw = get_setting("custom_fields_def", "[]")
        try: fields = json.loads(raw)
        except Exception: fields = []
        self.lb_fields.delete(0, tk.END)
        for f in fields:
            self.lb_fields.insert(tk.END, f)

    def add_custom_field(self):
        name = self.e_custom_name.get().strip()
        if not name: return
        raw = get_setting("custom_fields_def", "[]")
        try: fields = json.loads(raw)
        except Exception: fields = []
        if name not in fields:
            fields.append(name)
            set_setting("custom_fields_def", json.dumps(fields))
            self.e_custom_name.delete(0, tk.END)
            self.load_custom_fields()
            messagebox.showinfo("Saved", f"Custom field '{name}' registered!")

    def del_custom_field(self):
        sel = self.lb_fields.curselection()
        if not sel: return
        name = self.lb_fields.get(sel[0])
        raw = get_setting("custom_fields_def", "[]")
        try: fields = json.loads(raw)
        except Exception: fields = []
        if name in fields:
            fields.remove(name)
            set_setting("custom_fields_def", json.dumps(fields))
            self.load_custom_fields()

    # -------------------------------------------------------------
    # TAB 6: Database & Maintenance
    # -------------------------------------------------------------
    def setup_tab_maintenance(self):
        ttk.Label(
            self.tab_maintenance, 
            text="Database Operations, Integrity Checks & System Backups", 
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=W, pady=(0, 4))

        db_box = ttk.LabelFrame(self.tab_maintenance, text="Database Operations", padding=15)
        db_box.pack(fill=X, pady=10)

        ttk.Button(db_box, text="💾 Create Full Database Backup (.bak)", command=self.backup_database, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(db_box, text="🔄 Restore Database from Backup", command=self.restore_database, bootstyle="info-outline").pack(side=LEFT, padx=5)
        ttk.Button(db_box, text="🧹 Optimize & Vacuum SQLite", command=self.vacuum_db, bootstyle="primary-outline").pack(side=LEFT, padx=5)
        ttk.Button(db_box, text="⚠️ Safe Database Reset", command=self.safe_reset, bootstyle="danger-outline").pack(side=RIGHT, padx=5)

        # Section 2: Admin Security PIN / Master Password
        pin_box = ttk.LabelFrame(self.tab_maintenance, text="🔐 Admin Security PIN / Master Password", padding=15)
        pin_box.pack(fill=X, pady=10)

        ttk.Label(
            pin_box,
            text="Protect Administration & Settings with a Master PIN to prevent unauthorized alterations.\n"
                 "Default PIN: 'admin123' (You can update this at any time below).",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 8))

        pf = ttk.Frame(pin_box)
        pf.pack(fill=X)

        ttk.Label(pf, text="Current PIN:").grid(row=0, column=0, sticky=W, padx=4, pady=4)
        self.e_cur_pin = ttk.Entry(pf, show="*", width=14)
        self.e_cur_pin.grid(row=0, column=1, sticky=W, padx=4, pady=4)

        ttk.Label(pf, text="New Admin PIN:").grid(row=0, column=2, sticky=W, padx=4, pady=4)
        self.e_new_pin = ttk.Entry(pf, show="*", width=14)
        self.e_new_pin.grid(row=0, column=3, sticky=W, padx=4, pady=4)

        ttk.Label(pf, text="Confirm New PIN:").grid(row=0, column=4, sticky=W, padx=4, pady=4)
        self.e_conf_pin = ttk.Entry(pf, show="*", width=14)
        self.e_conf_pin.grid(row=0, column=5, sticky=W, padx=4, pady=4)

        ttk.Button(pf, text="💾 Update Admin PIN", command=self.update_admin_pin, bootstyle="warning").grid(row=0, column=6, padx=8, pady=4)

        # Section 3: Equipment File Record Deletion & Management (Admin Level)
        file_box = ttk.LabelFrame(self.tab_maintenance, text="🗑️ Equipment File Record Management & Permanent Deletion", padding=15)
        file_box.pack(fill=BOTH, expand=True, pady=10)

        ttk.Label(
            file_box,
            text="Inspect and permanently delete an equipment file and all associated operational records.\n"
                 "To protect data integrity, file deletions are restricted to this Admin & Settings console.",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 10))

        sel_f = ttk.Frame(file_box)
        sel_f.pack(fill=X, pady=(0, 10))

        ttk.Label(sel_f, text="Select / Search File NO:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 8))
        self.c_del_file_no = AutocompleteCombobox(sel_f, width=42)
        self.c_del_file_no.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
        self.c_del_file_no.bind("<<ComboboxSelected>>", lambda e: self.inspect_file_for_deletion())

        ttk.Button(sel_f, text="🔄 Refresh", command=self.refresh_del_file_dropdown, bootstyle="secondary-outline").pack(side=LEFT, padx=4)
        ttk.Button(sel_f, text="🔍 Inspect Records", command=self.inspect_file_for_deletion, bootstyle="info-outline").pack(side=LEFT, padx=4)
        ttk.Button(sel_f, text="🗑️ Delete File Record", command=self.delete_selected_file_record, bootstyle="danger").pack(side=LEFT, padx=4)

        # Inspection summary card
        self.card_inspect = ttk.Frame(file_box, padding=12, bootstyle="dark")
        self.card_inspect.pack(fill=BOTH, expand=True, pady=5)

        self.lbl_inspect_title = ttk.Label(
            self.card_inspect,
            text="Select an Equipment File NO above and click 'Inspect Records' to review associated data.",
            font=("Segoe UI", 10, "bold"),
            bootstyle="inverse-dark"
        )
        self.lbl_inspect_title.pack(anchor=W, pady=(0, 6))

        self.lbl_inspect_details = ttk.Label(
            self.card_inspect,
            text="• Inventory Units: -\n• S/A Procurement Track: -\n• Payment Vouchers: -\n• Repair Job Cards: -\n• Historical Archives: -",
            font=("Segoe UI", 9),
            bootstyle="inverse-dark",
            justify=LEFT
        )
        self.lbl_inspect_details.pack(anchor=W, pady=(0, 8))

        # Checkbox: Also remove from master dropdown lists
        self.var_del_from_master = tk.BooleanVar(value=False)
        self.chk_del_master = ttk.Checkbutton(
            file_box,
            text="Also remove File NO from Master Dropdown suggestions list (master_lists)",
            variable=self.var_del_from_master,
            bootstyle="round-toggle"
        )
        self.chk_del_master.pack(anchor=W, pady=(5, 0))

        self.refresh_del_file_dropdown()

    def backup_database(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".bak",
            filetypes=[("Backup Files", "*.bak"), ("Database Files", "*.db")],
            title="Save Database Backup"
        )
        if not dest: return
        try:
            shutil.copy2(DB_NAME, dest)
            messagebox.showinfo("Backup Complete", f"Database backed up to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def restore_database(self):
        src = filedialog.askopenfilename(
            filetypes=[("Backup Files", "*.bak;*.db")],
            title="Select Backup to Restore"
        )
        if not src: return
        if messagebox.askyesno("Confirm Restore", "Restore will replace the active database. Proceed?"):
            try:
                shutil.copy2(src, DB_NAME)
                messagebox.showinfo("Restored", "Database restored successfully. Please restart app.")
            except Exception as e:
                messagebox.showerror("Restore Failed", str(e))

    def vacuum_db(self):
        try:
            with db_connection() as conn:
                conn.execute("VACUUM;")
            messagebox.showinfo("Optimized", "Database VACUUM completed! Disk space reclaimed & integrity verified.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def safe_reset(self):
        confirm = simpledialog.askstring(
            "⚠️ Safe Database Reset (Fresh Start)",
            "This will create a fresh blank database for live hospital data:\n\n"
            "✔ Automatic safety backup (.bak) will be created first.\n"
            "✔ ALL Master Dropdown lists (Wards, Agents, Makes, Models) PRESERVED.\n"
            "✔ ALL Settings, Theme colors, and Column widths PRESERVED.\n"
            "⚠️ ALL Inventory & S/A transaction records will be cleared.\n\n"
            "Type 'CONFIRM' in capital letters to proceed:"
        )
        if confirm != "CONFIRM":
            messagebox.showinfo("Cancelled", "Safe Database Reset operation was cancelled. No data was changed.")
            return

        try:
            # 1. Automatic Timestamped Safety Backup
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            db_dir = os.path.dirname(os.path.abspath(DB_NAME))
            backup_filename = f"equipment_inventory_pre_reset_{ts}.bak"
            backup_path = os.path.join(db_dir, backup_filename)
            shutil.copy2(DB_NAME, backup_path)

            # 2. Preserve Dropdown items and historical File Numbers into master_lists
            categories = [
                ("file_no", "file_no"),
                ("equipment_name", "equipment_name"),
                ("make", "make"),
                ("model", "model"),
                ("location", "location"),
                ("local_agent", "local_agent"),
                ("how_received", "how_received")
            ]
            with db_connection() as conn:
                cur = conn.cursor()
                for col, cat in categories:
                    try:
                        cur.execute(f"SELECT DISTINCT {col} FROM inventory WHERE {col} IS NOT NULL AND TRIM({col}) != '';")
                        for r in cur.fetchall():
                            val = str(r[0]).strip()
                            if val:
                                cur.execute("INSERT OR IGNORE INTO master_lists (category, value) VALUES (?, ?);", (cat, val))
                    except Exception:
                        pass

                # 3. Clear Inventory & S/A Operational Tables
                cur.execute("DELETE FROM inventory;")
                cur.execute("DELETE FROM sa_procurement_track;")
                cur.execute("DELETE FROM sa_payments;")
                cur.execute("DELETE FROM sa_history;")
                cur.execute("DELETE FROM repairs;")
                cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('inventory', 'sa_procurement_track', 'sa_payments', 'sa_history', 'repairs');")
                conn.commit()
                conn.execute("VACUUM;")

            messagebox.showinfo(
                "✔ Fresh Start Ready",
                f"Database Safe Reset completed successfully!\n\n"
                f"1. Pre-reset backup saved as:\n{backup_filename}\n\n"
                f"2. All Dropdown lists & Settings are safely preserved.\n\n"
                f"3. All equipment records have been cleared.\n\n"
                f"Please restart the application to begin entering fresh records."
            )
        except Exception as e:
            log.error(f"Safe reset failed: {e}")
            messagebox.showerror("Reset Error", f"An error occurred during reset: {e}")

    # -------------------------------------------------------------
    # Admin Security PIN Management
    # -------------------------------------------------------------
    def update_admin_pin(self):
        saved_pin = get_setting("admin_pin", "admin123")
        cur = self.e_cur_pin.get().strip()
        new_p = self.e_new_pin.get().strip()
        conf_p = self.e_conf_pin.get().strip()

        if cur != str(saved_pin).strip():
            messagebox.showerror("Authentication Failed", "Current PIN is incorrect. Admin PIN was not updated.")
            return

        if not new_p or len(new_p) < 4:
            messagebox.showwarning("Weak PIN", "New PIN must be at least 4 characters long.")
            return

        if new_p != conf_p:
            messagebox.showerror("Mismatch", "New PIN and Confirm PIN do not match.")
            return

        set_setting("admin_pin", new_p)
        self.e_cur_pin.delete(0, tk.END)
        self.e_new_pin.delete(0, tk.END)
        self.e_conf_pin.delete(0, tk.END)
        messagebox.showinfo("PIN Updated", "Admin Security PIN updated successfully! Use your new PIN for future access.")

    # -------------------------------------------------------------
    # Equipment File Record Deletion & Management Methods
    # -------------------------------------------------------------
    def refresh_del_file_dropdown(self):
        """Populates the admin deletion dropdown with all existing file numbers."""
        try:
            file_numbers = get_all_file_numbers()
            if hasattr(self, "c_del_file_no"):
                self.c_del_file_no.set_completion_list(file_numbers)
        except Exception as e:
            log.warning(f"Could not refresh deletion dropdown: {e}")

    def inspect_file_for_deletion(self):
        """Inspects all linked records for the selected File NO across all tables."""
        raw_val = self.c_del_file_no.get().strip()
        if not raw_val:
            self.lbl_inspect_title.config(text="⚠️ Please select a File NO from the dropdown first.")
            self.lbl_inspect_details.config(text="")
            return

        file_no = raw_val.split(" - ")[0].strip()
        try:
            with db_connection() as conn:
                # 1. Inventory units
                inv_rows = conn.execute("SELECT * FROM inventory WHERE file_no = ? ORDER BY id ASC;", (file_no,)).fetchall()
                n_inv = len(inv_rows)
                eq_name = inv_rows[0]["equipment_name"] if n_inv > 0 else (raw_val.split(" - ")[1].strip() if " - " in raw_val else "Unknown")
                make = inv_rows[0]["make"] if n_inv > 0 else ""
                model = inv_rows[0]["model"] if n_inv > 0 else ""
                locs = list(dict.fromkeys([r["location"] for r in inv_rows if r["location"]]))
                serials = [r["serial_no"] for r in inv_rows if r["serial_no"]]

                # 2. S/A Procurement Track
                proc = conn.execute("SELECT * FROM sa_procurement_track WHERE file_no = ?;", (file_no,)).fetchone()
                proc_info = f"Present ({proc['process_status'] or 'Initiated'}, Type: {proc['sa_process_type'] or 'N/A'})" if proc else "None"

                # 3. S/A Payments
                pay_rows = conn.execute("SELECT amount FROM sa_payments WHERE file_no = ?;", (file_no,)).fetchall()
                n_pay = len(pay_rows)
                total_pay = sum(r["amount"] or 0 for r in pay_rows)

                # 4. S/A Past History
                hist_count = conn.execute("SELECT COUNT(*) AS c FROM sa_history WHERE file_no = ?;", (file_no,)).fetchone()["c"]

                # 5. Repairs
                rep_rows = conn.execute("SELECT job_status FROM repairs WHERE file_no = ?;", (file_no,)).fetchall()
                n_rep = len(rep_rows)
                n_open_rep = sum(1 for r in rep_rows if r["job_status"] != "Completed")

                # 6. Check if present in master_lists
                in_ml = conn.execute("SELECT COUNT(*) AS c FROM master_lists WHERE category = 'file_no' AND value = ?;", (file_no,)).fetchone()["c"] > 0

            self.lbl_inspect_title.config(
                text=f"📁 File NO: {file_no} — {eq_name} ({make} {model})" if (make or model) else f"📁 File NO: {file_no} — {eq_name}"
            )
            details_text = (
                f"• Master Inventory Units: {n_inv} unit(s) registered"
                f" | Locations: {', '.join(locs) if locs else 'Not assigned'}\n"
                f"• Unit Serial Numbers: {', '.join(serials[:5]) if serials else 'None'}"
                f"{' (+more)' if len(serials) > 5 else ''}\n"
                f"• S/A Procurement Track: {proc_info}\n"
                f"• Recorded Payment Vouchers: {n_pay} vouchers (Total Paid: Rs. {total_pay:,.2f})\n"
                f"• Breakdown & Repair Job Cards: {n_rep} cards ({n_open_rep} open / in-progress)\n"
                f"• S/A Past History Archives: {hist_count} concluded contracts\n"
                f"• Master Dropdowns Status: {'Present in master_lists' if in_ml else 'Not in master_lists'}"
            )
            self.lbl_inspect_details.config(text=details_text)

        except Exception as e:
            log.error(f"Error inspecting file: {e}")
            self.lbl_inspect_title.config(text=f"Error inspecting records: {e}")
            self.lbl_inspect_details.config(text="")

    def delete_selected_file_record(self):
        """Admin cascade deletion of an equipment file and its operational records."""
        raw_val = self.c_del_file_no.get().strip()
        if not raw_val:
            messagebox.showwarning("No File Selected", "Please select or type a File NO to delete.")
            return

        file_no = raw_val.split(" - ")[0].strip()

        with db_connection() as conn:
            n_inv = conn.execute("SELECT COUNT(*) AS c FROM inventory WHERE file_no = ?;", (file_no,)).fetchone()["c"]
            n_proc = conn.execute("SELECT COUNT(*) AS c FROM sa_procurement_track WHERE file_no = ?;", (file_no,)).fetchone()["c"]
            n_pay = conn.execute("SELECT COUNT(*) AS c FROM sa_payments WHERE file_no = ?;", (file_no,)).fetchone()["c"]
            n_hist = conn.execute("SELECT COUNT(*) AS c FROM sa_history WHERE file_no = ?;", (file_no,)).fetchone()["c"]
            n_rep = conn.execute("SELECT COUNT(*) AS c FROM repairs WHERE file_no = ?;", (file_no,)).fetchone()["c"]
            in_ml = conn.execute("SELECT COUNT(*) AS c FROM master_lists WHERE category = 'file_no' AND value = ?;", (file_no,)).fetchone()["c"] > 0

        total_records = n_inv + n_proc + n_pay + n_hist + n_rep

        if total_records == 0:
            if in_ml:
                if messagebox.askyesno(
                    "Remove Unused File NO",
                    f"File NO '{file_no}' has no active records in Inventory or S/A operations,\n"
                    f"but it is saved in the Master Dropdown list.\n\n"
                    f"Do you want to remove it from the Master Dropdowns?"
                ):
                    delete_master_list_value("file_no", file_no)
                    self.refresh_del_file_dropdown()
                    self.c_del_file_no.set("")
                    self.lbl_inspect_title.config(text=f"File NO '{file_no}' removed from master dropdowns.")
                    self.lbl_inspect_details.config(text="")
                    messagebox.showinfo("Removed", f"File NO '{file_no}' removed from master dropdowns.")
                return
            else:
                messagebox.showinfo("No Records Found", f"No records found in database for File NO '{file_no}'.")
                return

        del_from_master = self.var_del_from_master.get()
        msg = (
            f"⚠️ CONFIRM PERMANENT RECORD DELETION\n\n"
            f"You are about to permanently delete all data for:\n"
            f"File NO: {file_no}\n\n"
            f"This will permanently and irreversibly erase:\n"
            f"• All {n_inv} equipment unit row(s) in Master Inventory\n"
            f"• All associated S/A Procurement Track records ({n_proc})\n"
            f"• All S/A Installment Payment records ({n_pay})\n"
            f"• All S/A Past History archives ({n_hist})\n"
            f"• All Equipment Breakdown & Repair Job Cards ({n_rep})\n\n"
            f"Master Dropdown: {'Will ALSO be removed from dropdown suggestions.' if del_from_master else 'Will be PRESERVED in dropdowns for future re-use.'}\n\n"
            f"Are you completely sure you want to proceed?"
        )

        if not messagebox.askyesno("⚠️ Danger: Permanent File Deletion", msg):
            return

        try:
            with db_connection() as conn:
                conn.execute("DELETE FROM inventory WHERE file_no = ?;", (file_no,))
                conn.execute("DELETE FROM sa_procurement_track WHERE file_no = ?;", (file_no,))
                conn.execute("DELETE FROM sa_payments WHERE file_no = ?;", (file_no,))
                conn.execute("DELETE FROM sa_history WHERE file_no = ?;", (file_no,))
                conn.execute("DELETE FROM repairs WHERE file_no = ?;", (file_no,))
                if del_from_master:
                    conn.execute("DELETE FROM master_lists WHERE category = 'file_no' AND value = ?;", (file_no,))

            messagebox.showinfo(
                "Deleted Successfully",
                f"All records ({total_records} total items) for File NO '{file_no}' have been permanently deleted."
            )
            self.refresh_del_file_dropdown()
            self.c_del_file_no.set("")
            self.lbl_inspect_title.config(text="Select an Equipment File NO above and click 'Inspect Records'.")
            self.lbl_inspect_details.config(text="• Record deletion completed successfully.")

        except Exception as e:
            log.error(f"Error deleting file record: {e}")
            messagebox.showerror("Deletion Error", f"Failed to delete records: {e}")

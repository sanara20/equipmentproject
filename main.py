# -*- coding: utf-8 -*-
"""
Medical Equipment Maintenance Management System - Teaching Hospital Peradeniya v1.0
Main Application Controller & High-Fidelity Landing Dashboard

Features:
- Fullscreen/Maximized High-Fidelity 4-Module Dashboard matching Preview
- Real-time Search-As-You-Type Dropdown in Global Search & Quick Lookup (Points 1, 2, 3)
- Large Spacious Rounded Cards filling the window, entire card clickable (Points 4, 6)
- Subtitle strictly "Teaching Hospital - Peradeniya." (Point 14)
- Live Metrics Status Badges
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import logging
import os

# Enable High-DPI awareness on Windows to ensure razor-sharp fonts and borders
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from db_manager import init_database, db_connection, DB_NAME, get_setting, set_setting
from autocomplete import SearchSuggestPopup
from print_helper import print_document
from mod_asset_registry import AssetRegistryModule
from mod_sa_hub import SAContractsHubModule
from mod_repairs import RepairsModule
from mod_settings import SettingsModule

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("thp_equip_main")

def get_search_candidates():
    """Returns all searchable strings (File NO, Name, Ward, Serial) for real-time auto-suggest."""
    results = []
    try:
        with db_connection() as conn:
            rows = conn.execute("SELECT file_no, equipment_name, location, serial_no FROM inventory ORDER BY file_no ASC;").fetchall()
            for r in rows:
                fn = r["file_no"]
                en = r["equipment_name"]
                loc = f" | {r['location']}" if r['location'] else ""
                results.append(f"{fn} - {en}{loc}")
    except Exception:
        pass
    return results

class THPEquipmentApplication(ttk.Window):
    def __init__(self):
        super().__init__(
            title="Medical Equipment Maintenance Management System - Teaching Hospital Peradeniya v1.0",
            themename="superhero",
            size=(1380, 880),
            minsize=(1100, 720)
        )
        
        # Maximize or center nicely
        try:
            self.state("zoomed")  # Fullscreen on Windows
        except Exception:
            pass

        # Safe Database Initialization & Schema Migration
        init_database()

        # Update window title from saved branding (version, app title, hospital subtitle)
        self.update_window_title()

        # Root Container
        self.root_container = ttk.Frame(self)
        self.root_container.pack(fill=BOTH, expand=True)

        self.show_landing_page()

    def update_window_title(self, app_title=None, subtitle=None, version_tag=None):
        """Dynamically updates the OS window title bar with configured title, subtitle, and version."""
        if not app_title or not subtitle or not version_tag:
            branding_raw = get_setting("app_branding")
            try: b = json.loads(branding_raw) if branding_raw else {}
            except Exception: b = {}
            app_title = b.get("app_title", "Medical Equipment Maintenance Management System")
            subtitle = b.get("subtitle", "Teaching Hospital - Peradeniya.")
            version_tag = b.get("version_tag", "v1.0")

        clean_sub = str(subtitle).strip().rstrip(".")
        clean_ver = str(version_tag).strip()
        full_title = f"{app_title} - {clean_sub} {clean_ver}".strip()
        try:
            self.title(full_title)
        except Exception:
            pass

    def clear_container(self):
        for widget in self.root_container.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------
    # 1. HIGH-FIDELITY LANDING DASHBOARD (මුල් පිටුව)
    # -------------------------------------------------------------
    def show_landing_page(self):
        self.clear_container()

        # Load dynamic branding and typography configured in Admin & Settings
        branding_raw = get_setting("app_branding")
        try: branding = json.loads(branding_raw) if branding_raw else {}
        except Exception: branding = {}

        typo_raw = get_setting("landing_typography")
        try: typo = json.loads(typo_raw) if typo_raw else {}
        except Exception: typo = {}

        app_title = branding.get("app_title", "Medical Equipment Maintenance Management System")
        version_tag = branding.get("version_tag", "v1.0")
        subtitle = branding.get("subtitle", "Teaching Hospital - Peradeniya.")
        badge_text = branding.get("badge_text", "")
        bg_color = branding.get("bg_color", "#0f172a")

        # Synchronize window OS title bar on load
        self.update_window_title(app_title, subtitle, version_tag)

        title_size = int(typo.get("title_font_size", 18))
        title_color = typo.get("title_color", "#f8fafc")
        sub_size = int(typo.get("subtitle_font_size", 11))
        sub_color = typo.get("subtitle_color", "#94a3b8")
        card_t_size = int(typo.get("card_title_font_size", 12))
        card_d_size = int(typo.get("card_desc_font_size", 9))

        # Root scrollable canvas ensuring 100% responsiveness on any laptop/monitor resolution
        landing_canvas = tk.Canvas(self.root_container, bg=bg_color, highlightthickness=0)
        landing_vsb = ttk.Scrollbar(self.root_container, orient=VERTICAL, command=landing_canvas.yview)
        landing_canvas.configure(yscrollcommand=landing_vsb.set)

        landing_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        landing_vsb.pack(side=RIGHT, fill=Y)

        main_canvas_frame = ttk.Frame(landing_canvas, padding=(25, 12))
        frame_win = landing_canvas.create_window((0, 0), window=main_canvas_frame, anchor="nw")

        def _on_frame_cfg(e):
            landing_canvas.configure(scrollregion=landing_canvas.bbox("all"))

        def _on_canvas_cfg(e):
            landing_canvas.itemconfig(frame_win, width=e.width)

        main_canvas_frame.bind("<Configure>", _on_frame_cfg)
        landing_canvas.bind("<Configure>", _on_canvas_cfg)

        def _on_mw(e):
            if landing_canvas.winfo_exists():
                landing_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        landing_canvas.bind_all("<MouseWheel>", _on_mw)

        # -------------------------------------------------------------
        # Top Bar: Status Indicator (Left) & Prominent Admin & Settings (Right - Design 3)
        # -------------------------------------------------------------
        top_bar = ttk.Frame(main_canvas_frame)
        top_bar.pack(fill=X, pady=(0, 10))

        status_box = ttk.Frame(top_bar)
        status_box.pack(side=LEFT)
        status_canvas = tk.Canvas(status_box, width=12, height=12, bg="#0f172a", highlightthickness=0)
        status_canvas.pack(side=LEFT, padx=(0, 6))
        status_canvas.create_oval(2, 2, 10, 10, fill="#10b981", outline="#34d399", width=1)
        tk.Label(
            status_box,
            text="SYSTEM ACTIVE • ONLINE",
            font=("Consolas", 9, "bold"),
            fg="#10b981",
            bg="#0f172a"
        ).pack(side=LEFT)

        admin_hdr_box = ttk.Frame(top_bar)
        admin_hdr_box.pack(side=RIGHT)
        ttk.Button(
            admin_hdr_box,
            text="⚙️ Admin & Settings",
            command=self.request_admin_access,
            bootstyle="primary",
            cursor="hand2"
        ).pack(side=RIGHT)

        # -------------------------------------------------------------
        # Header Area: Centered ECG Emblem ABOVE Title + Hospital Subtitle
        # -------------------------------------------------------------
        hdr_frame = ttk.Frame(main_canvas_frame)
        hdr_frame.pack(fill=X, pady=(0, 6))

        # Emblem Canvas Centered ABOVE Title
        emblem_box = ttk.Frame(hdr_frame)
        emblem_box.pack(anchor="center", pady=(0, 3))

        emblem = tk.Canvas(emblem_box, width=50, height=34, bg="#0f172a", highlightthickness=1, highlightbackground="#38bdf8")
        emblem.pack(anchor="center")
        emblem.create_oval(2, 2, 48, 32, fill="#1e293b", outline="#0284c7", width=1.5)
        # Glowing Cyan ECG Wave
        emblem.create_line(5, 17, 14, 17, fill="#38bdf8", width=2)
        emblem.create_line(14, 17, 19, 7, fill="#38bdf8", width=2)
        emblem.create_line(19, 7, 26, 27, fill="#38bdf8", width=2)
        emblem.create_line(26, 27, 33, 11, fill="#38bdf8", width=2)
        emblem.create_line(33, 11, 38, 17, fill="#38bdf8", width=2)
        emblem.create_line(38, 17, 45, 17, fill="#38bdf8", width=2)

        title_box = ttk.Frame(hdr_frame)
        title_box.pack(anchor="center")

        title_row = ttk.Frame(title_box)
        title_row.pack(anchor="center")

        tk.Label(
            title_row,
            text=app_title,
            font=("Segoe UI", title_size, "bold"),
            fg=title_color,
            bg="#0f172a"
        ).pack(side=LEFT)

        ttk.Label(
            title_row,
            text=f" {version_tag} ",
            font=("Consolas", 10, "bold"),
            bootstyle="info-inverse"
        ).pack(side=LEFT, padx=8)

        # Optional Badge: Only shown if user typed text; styled with user-selected colors!
        if badge_text and badge_text.strip():
            badge_bg = branding.get("badge_bg_color", "#0284c7")
            badge_fg = branding.get("badge_fg_color", "#ffffff")
            tk.Label(
                title_row,
                text=f" {badge_text.strip()} ",
                font=("Segoe UI", 9, "bold"),
                fg=badge_fg,
                bg=badge_bg,
                padx=6, pady=2
            ).pack(side=LEFT, padx=4)

        # Subtitle Hospital Name (Centered under title)
        tk.Label(
            title_box,
            text=subtitle,
            font=("Segoe UI", sub_size, "bold"),
            fg=sub_color,
            bg="#0f172a"
        ).pack(anchor="center", pady=(2, 0))

        # -------------------------------------------------------------
        # Points 1, 2, 3, 4: Spacious Rounded Search Bar with 360° View Button & Live Suggestions
        # -------------------------------------------------------------
        search_card = ttk.LabelFrame(main_canvas_frame, text="🔍 Global Real-Time Asset Search & 360° Profile Lookup", padding=10, bootstyle="info")
        search_card.pack(fill=X, padx=40, pady=(0, 12))

        s_row = ttk.Frame(search_card)
        s_row.pack(fill=X)

        self.home_search_entry = ttk.Entry(
            s_row,
            font=("Segoe UI", 11),
        )
        self.home_search_entry.pack(side=LEFT, ipady=5, padx=(0, 8), fill=X, expand=True)
        self.home_search_entry.insert(0, "Search Equipment by File NO, Name, Location or 360° View...")
        self.home_search_entry.bind("<FocusIn>", lambda e: self.home_search_entry.delete(0, tk.END) if "Search Equipment" in self.home_search_entry.get() else None)
        self.home_search_entry.bind("<Return>", lambda e: self.trigger_search())

        # Attach real-time Search-As-You-Type floating popup
        self.home_suggester = SearchSuggestPopup(
            self.home_search_entry,
            get_candidates_func=get_search_candidates,
            on_select_callback=self.on_search_candidate_selected
        )

        ttk.Button(
            s_row,
            text="👁️ 360° View",
            command=self.trigger_search,
            bootstyle="info",
            cursor="hand2",
            width=12
        ).pack(side=RIGHT, ipady=4, padx=(6, 0))

        ttk.Button(
            s_row,
            text="✖ Clear",
            command=self.clear_home_search,
            bootstyle="secondary-outline",
            cursor="hand2",
            width=10
        ).pack(side=RIGHT, ipady=4)

        # -------------------------------------------------------------
        # HIGH-VISIBILITY PROMINENT EXPIRY ALERTS NOTIFICATION BOARD
        # Positioned right under Search Bar so it is IMMEDIATELY VISIBLE at eye level!
        # Red-Amber Blended Glow, Pulsing Emergency Beacon, Live Counts, Clickable
        # -------------------------------------------------------------
        self.render_expiry_alerts_strip(main_canvas_frame)

        # -------------------------------------------------------------
        # 4 Large Spacious Cards with Dynamic Colors, Headings & 3D Depth
        # -------------------------------------------------------------
        custom_colors_raw = get_setting("card_colors")
        try:
            custom_colors = json.loads(custom_colors_raw) if custom_colors_raw else {}
        except Exception:
            custom_colors = {}

        cards_outer = ttk.Frame(main_canvas_frame)
        cards_outer.pack(fill=BOTH, expand=True, padx=40, pady=(0, 8))

        grid_frame = ttk.Frame(cards_outer)
        grid_frame.pack(fill=BOTH, expand=True)
        grid_frame.columnconfigure(0, weight=1, uniform="card")
        grid_frame.columnconfigure(1, weight=1, uniform="card")
        grid_frame.rowconfigure(0, weight=1, uniform="card")
        grid_frame.rowconfigure(1, weight=1, uniform="card")

        c1_cfg = custom_colors.get("card1", {
            "border": "#34d399", "bg": "#e8f8f2", "title": "#065f46",
            "desc": "#166534", "tag_bg": "#a7f3d0", "tag_fg": "#065f46"
        })
        c1_title = branding.get("card1_title", "➕ 1. ASSET MASTER REGISTRY")
        c1_desc = branding.get("card1_desc", "Primary equipment registration form, multi-unit serial numbers, auto-calculated warranty expirations, and ward placement mapping.")
        c1 = self.build_large_card(
            grid_frame,
            title=c1_title,
            desc=c1_desc,
            tag="Core Asset Master Inventory",
            border_hex=c1_cfg["border"],
            bg_hex=c1_cfg["bg"],
            title_hex=c1_cfg["title"],
            desc_hex=c1_cfg["desc"],
            tag_bg=c1_cfg["tag_bg"],
            tag_fg=c1_cfg["tag_fg"],
            action=lambda: self.open_module("asset"),
            title_size=card_t_size,
            desc_size=card_d_size,
            card_canvas_bg=bg_color
        )
        c1.grid(row=0, column=0, padx=8, pady=5, sticky="nsew")

        c2_cfg = custom_colors.get("card2", {
            "border": "#60a5fa", "bg": "#ebf5ff", "title": "#1e40af",
            "desc": "#1e3a8a", "tag_bg": "#bfdbfe", "tag_fg": "#1e40af"
        })
        c2_title = branding.get("card2_title", "📋 2. S/A CONTRACTS HUB")
        c2_desc = branding.get("card2_desc", "S/A Procurement Track Pipeline (Stages 1-8), BEC Evaluations, Agreement Signing, and Maintenance Payment Installments / Vouchers.")
        c2 = self.build_large_card(
            grid_frame,
            title=c2_title,
            desc=c2_desc,
            tag="Contract Pipeline & Payments (2 Modules)",
            border_hex=c2_cfg["border"],
            bg_hex=c2_cfg["bg"],
            title_hex=c2_cfg["title"],
            desc_hex=c2_cfg["desc"],
            tag_bg=c2_cfg["tag_bg"],
            tag_fg=c2_cfg["tag_fg"],
            action=lambda: self.open_module("sa"),
            title_size=card_t_size,
            desc_size=card_d_size,
            card_canvas_bg=bg_color
        )
        c2.grid(row=0, column=1, padx=8, pady=5, sticky="nsew")

        c3_cfg = custom_colors.get("card3", {
            "border": "#fbbf24", "bg": "#fef6eb", "title": "#92400e",
            "desc": "#78350f", "tag_bg": "#fde68a", "tag_fg": "#92400e"
        })
        c3_title = branding.get("card3_title", "🛠️ 3. REPAIRS & BREAKDOWNS")
        c3_desc = branding.get("card3_desc", "Breakdown intake job cards, estimate sanction approvals, Internal repair category, and job status tracking.")
        c3 = self.build_large_card(
            grid_frame,
            title=c3_title,
            desc=c3_desc,
            tag="Corrective Maintenance Pipeline",
            border_hex=c3_cfg["border"],
            bg_hex=c3_cfg["bg"],
            title_hex=c3_cfg["title"],
            desc_hex=c3_cfg["desc"],
            tag_bg=c3_cfg["tag_bg"],
            tag_fg=c3_cfg["tag_fg"],
            action=lambda: self.open_module("repairs"),
            title_size=card_t_size,
            desc_size=card_d_size,
            card_canvas_bg=bg_color
        )
        c3.grid(row=1, column=0, padx=8, pady=5, sticky="nsew")

        c4_cfg = custom_colors.get("card4", {
            "border": "#38bdf8", "bg": "#0d1f38", "title": "#38bdf8",
            "desc": "#bae6fd", "tag_bg": "#082f49", "tag_fg": "#38bdf8"
        })
        c4_title = branding.get("card4_title", "🗂️ 4. CONSOLIDATED INVENTORY")
        c4_desc = branding.get("card4_desc", "Master 36-column equipment matrix syncing core asset registry, S/A contract terms, procurement logs, and financial vouchers.")
        c4 = self.build_large_card(
            grid_frame,
            title=c4_title,
            desc=c4_desc,
            tag="Master 36-Col Matrix (All Equipments)",
            border_hex=c4_cfg["border"],
            bg_hex=c4_cfg["bg"],
            title_hex=c4_cfg["title"],
            desc_hex=c4_cfg["desc"],
            tag_bg=c4_cfg["tag_bg"],
            tag_fg=c4_cfg["tag_fg"],
            action=lambda: self.open_module("inventory"),
            title_size=card_t_size,
            desc_size=card_d_size,
            card_canvas_bg=bg_color
        )
        c4.grid(row=1, column=1, padx=8, pady=5, sticky="nsew")

    def request_admin_access(self):
        """Security Gate: Prompts for Admin PIN before opening Settings."""
        admin_pin = get_setting("admin_pin", "admin123")
        pin = simpledialog.askstring(
            "🔐 Admin Security Gate",
            "Enter Admin PIN / Master Password to access Settings:\n(Default initial PIN: admin123)",
            show="*"
        )
        if pin is None:
            return
        if pin.strip() == str(admin_pin).strip():
            self.open_module("settings")
        else:
            messagebox.showerror("Access Denied", "Incorrect Admin PIN / Master Password.\nAccess to System Administration & Settings is restricted.")

    def clear_home_search(self):
        """Clears landing page search bar."""
        if hasattr(self, "home_search_entry") and self.home_search_entry.winfo_exists():
            self.home_search_entry.delete(0, tk.END)

    def build_large_card(self, parent, title, desc, tag, border_hex, bg_hex, title_hex, desc_hex, tag_bg, tag_fg, action, title_size=12, desc_size=9, card_canvas_bg="#0f172a"):
        """Creates an authentic elevated 3D rounded card with reduced height so all 4 fit on screen without scrolling."""
        card = tk.Canvas(parent, height=110, bg=card_canvas_bg, highlightthickness=0, cursor="hand2")
        
        # Inner content container with soft pastel background - compact height
        inner = tk.Frame(card, bg=bg_hex, padx=14, pady=6)
        win_id = card.create_window((5, 3), window=inner, anchor="nw")

        lbl_t = tk.Label(inner, text=title, font=("Segoe UI", title_size, "bold"), fg=title_hex, bg=bg_hex, cursor="hand2")
        lbl_t.pack(anchor=W)

        # Dynamic wraplength with proper padding so letters never clip
        lbl_d = tk.Label(inner, text=desc, font=("Segoe UI", desc_size), fg=desc_hex, bg=bg_hex, justify=LEFT, cursor="hand2")
        lbl_d.pack(anchor=W, fill=X, expand=True, pady=(2, 3))

        lbl_tag = tk.Label(inner, text=f"  {tag}  ", font=("Segoe UI", 8, "bold"), fg=tag_fg, bg=tag_bg, cursor="hand2", padx=6, pady=1)
        lbl_tag.pack(anchor=W, pady=(1, 0))

        # Bind click anywhere on card and all child widgets
        for w in (card, inner, lbl_t, lbl_d, lbl_tag):
            w.bind("<Button-1>", lambda e, act=action: act())

        def make_round_pts(x1, y1, x2, y2, r=10):
            return [
                x1 + r, y1,
                x2 - r, y1,
                x2, y1,
                x2, y1 + r,
                x2, y2 - r,
                x2, y2,
                x2 - r, y2,
                x1 + r, y2,
                x1, y2,
                x1, y2 - r,
                x1, y1 + r,
                x1, y1
            ]

        def redraw_card(elevated=False):
            w = card.winfo_width()
            h = card.winfo_height()
            if w <= 30 or h <= 30:
                return
            card.delete("all")
            
            # Subtle Drop Shadow
            sx1, sy1, sx2, sy2 = 4, 3, w - 2, h - 1
            if elevated:
                sx1, sy1, sx2, sy2 = 5, 4, w - 1, h + 1
            shadow_pts = make_round_pts(sx1, sy1, sx2, sy2, r=10)
            card.create_polygon(shadow_pts, fill="#050914", outline="", smooth=True, tags="card_shadow")

            # Main Card Body with rounded corners and clean single-line border
            cx1, cy1, cx2, cy2 = (3, 2, w - 4, h - 4) if not elevated else (3, 1, w - 4, h - 5)
            body_pts = make_round_pts(cx1, cy1, cx2, cy2, r=10)
            card.create_polygon(body_pts, fill=bg_hex, outline=border_hex, width=1, smooth=True, tags="card_body")

            # Subtle top highlight
            card.create_line(cx1 + 10, cy1 + 1, cx2 - 10, cy1 + 1, fill="#ffffff", width=1, tags="card_bevel")

            # Reposition inner frame
            inner_y = 3 if not elevated else 2
            card.create_window((5, inner_y), window=inner, anchor="nw", tags="card_win", width=w - 12)
            
            # Ensure text wraplength accounts for card padding
            avail_w = max(180, w - 40)
            lbl_d.config(wraplength=avail_w)

        def on_resize(event):
            redraw_card(False)

        def on_enter(event):
            redraw_card(True)

        def on_leave(event):
            redraw_card(False)

        card.bind("<Configure>", on_resize)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        return card

    def render_expiry_alerts_strip(self, parent):
        """High-Visibility Sleek Expiry Alerts Strip with Clean Single-Line Border,
        pulsing beacon, live counts, and entire card clickable to open the Expiry Alerts Dashboard."""
        import datetime
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

        alert_box = ttk.Frame(parent, cursor="hand2")
        alert_box.pack(fill=X, padx=40, pady=(0, 10))

        canvas = tk.Canvas(alert_box, height=56, bg="#0f172a", highlightthickness=0, cursor="hand2")
        canvas.pack(fill=X, expand=True)

        def draw_strip(is_hover=False):
            canvas.delete("all")
            w = canvas.winfo_width()
            if w <= 20:
                w = 1100
            h = 54

            # Clean Single-Line Border ("තනි ඉරක් වගේ")
            border_c = "#ef4444" if not is_hover else "#f59e0b"
            border_w = 1
            bg_c = "#140707" if not is_hover else "#220c0c"

            pts = [10, 2, w-10, 2, w-2, 10, w-2, h-10, w-10, h-2, 10, h-2, 2, h-10, 2, 10]
            canvas.create_polygon(pts, fill=bg_c, outline=border_c, width=border_w, smooth=True)

            # Left Section: Beacon + Title
            canvas.create_oval(14, 19, 26, 31, fill="#ef4444", outline="#fca5a5", width=1)
            canvas.create_oval(18, 23, 22, 27, fill="#ffffff")

            canvas.create_text(
                34, 25,
                text="⚠️ EXPIRY ALERTS",
                anchor="w",
                font=("Segoe UI", 11, "bold"),
                fill="#f87171"
            )

            # 4 Inline Stat Tiles
            tiles = [
                ("S/A Expired", f"{sa_expired}", "#ef4444"),
                ("< 60 Days", f"{sa_exp_60}", "#f59e0b"),
                ("War < 90d", f"{war_exp_90}", "#06b6d4"),
                ("Consent", f"{consent_pending}", "#94a3b8")
            ]

            start_x = 210
            for i, (t_label, t_val, t_color) in enumerate(tiles):
                bx1 = start_x + i * 110
                bx2 = bx1 + 98
                by1 = 10
                by2 = 44
                canvas.create_rectangle(bx1, by1, bx2, by2, fill="#1f1010", outline=t_color, width=1)
                canvas.create_text((bx1 + bx2) // 2, 20, text=t_label, font=("Segoe UI", 8), fill="#cbd5e1")
                canvas.create_text((bx1 + bx2) // 2, 33, text=f"{t_val} Unit(s)", font=("Consolas", 9, "bold"), fill=t_color)

            # Right Callout Button
            btn_x1, btn_y1, btn_x2, btn_y2 = w - 170, 12, w - 14, 42
            btn_bg = "#dc2626" if not is_hover else "#ea580c"
            canvas.create_rectangle(btn_x1, btn_y1, btn_x2, btn_y2, fill=btn_bg, outline="#fca5a5", width=1)
            canvas.create_text(
                (btn_x1 + btn_x2) // 2, 27,
                text="View Dashboard →",
                font=("Segoe UI", 9, "bold"),
                fill="#ffffff"
            )


        def on_resize(e):
            draw_strip(False)

        def on_enter(e):
            draw_strip(True)

        def on_leave(e):
            draw_strip(False)

        def on_click(e):
            self.open_module("alerts")

        canvas.bind("<Configure>", on_resize)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        alert_box.bind("<Button-1>", on_click)

        # Trigger immediate drawing and scheduled refreshes so strip never remains blank
        draw_strip(False)
        self.after(30, lambda: draw_strip(False))
        self.after(120, lambda: draw_strip(False))

    # -------------------------------------------------------------
    # 2. FOCUSED INNER MODULE NAVIGATION WITH QUICK LOOKUP
    # -------------------------------------------------------------
    def open_module(self, module_name):
        self.clear_container()

        hbar = ttk.Frame(self.root_container, padding=(15, 10), bootstyle="dark")
        hbar.pack(fill=X)

        left = ttk.Frame(hbar)
        left.pack(side=LEFT)
        ttk.Button(
            left,
            text="← 🏠 මුල් පිටුව (Home)",
            command=self.show_landing_page,
            bootstyle="secondary-outline"
        ).pack(side=LEFT, padx=(0, 15))

        titles = {
            "asset": ("➕ 1. Asset Master Registry", "success"),
            "sa": ("📋 2. S/A Contracts Hub", "primary"),
            "repairs": ("🛠️ 3. Equipment Breakdown & Maintenance Hub", "warning"),
            "inventory": ("🗂️ 4. Consolidated Inventory (Master 36-Col Matrix)", "info"),
            "alerts": ("⚠️ Expiry & Action Alerts Dashboard", "danger"),
            "settings": ("⚙️ System Administration & Settings", "secondary")
        }
        t_text, t_style = titles.get(module_name, ("Module", "primary"))
        ttk.Label(left, text=t_text, font=("Segoe UI", 12, "bold"), bootstyle=t_style).pack(side=LEFT)

        # Quick Lookup in Inner Header with Real-Time Suggest
        right = ttk.Frame(hbar)
        right.pack(side=RIGHT)
        ttk.Label(right, text="Quick Lookup:", font=("Segoe UI", 9)).pack(side=LEFT, padx=4)
        
        self.inner_search_entry = ttk.Entry(right, width=28)
        self.inner_search_entry.pack(side=LEFT, padx=(0, 6))
        self.inner_search_entry.bind("<Return>", lambda e: self.trigger_inner_search())

        self.inner_suggester = SearchSuggestPopup(
            self.inner_search_entry,
            get_candidates_func=get_search_candidates,
            on_select_callback=self.on_search_candidate_selected
        )

        ttk.Button(right, text="👁️ 360° Profile", command=self.trigger_inner_search, bootstyle="info-outline").pack(side=LEFT)

        cframe = ttk.Frame(self.root_container)
        cframe.pack(fill=BOTH, expand=True)

        if module_name == "asset":
            AssetRegistryModule(cframe, on_open_procurement=self.open_procurement_track_direct).pack(fill=BOTH, expand=True)
        elif module_name == "sa":
            self.current_sa_hub = SAContractsHubModule(
                cframe, 
                show_profile_callback=self.open_360_profile,
                on_back_to_asset=lambda: self.open_module("asset")
            )
            self.current_sa_hub.pack(fill=BOTH, expand=True)
        elif module_name == "repairs":
            RepairsModule(cframe).pack(fill=BOTH, expand=True)
        elif module_name == "inventory":
            from sa_submodules.sa_sheet import SASheetView
            SASheetView(cframe, show_profile_callback=self.open_360_profile).pack(fill=BOTH, expand=True)
        elif module_name == "alerts":
            from sa_submodules.sa_alerts import SAAlertsView
            SAAlertsView(cframe, on_open_procurement=self.open_procurement_track_direct).pack(fill=BOTH, expand=True)
        elif module_name == "settings":
            SettingsModule(cframe).pack(fill=BOTH, expand=True)

    def open_procurement_track_direct(self, file_no=None):
        self.open_module("sa")
        if hasattr(self, 'current_sa_hub') and self.current_sa_hub:
            self.current_sa_hub.jump_to_procurement(file_no)

    # -------------------------------------------------------------
    # 3. 360° PROFILE MODAL & SEARCH HANDLERS
    # -------------------------------------------------------------
    def on_search_candidate_selected(self, candidate_text):
        file_no = candidate_text.split(" - ")[0].strip()
        self.clear_home_search()
        self.open_360_profile(file_no)

    def trigger_search(self):
        query = self.home_search_entry.get().strip()
        if not query or "Search by typing" in query:
            with db_connection() as conn:
                r = conn.execute("SELECT file_no FROM inventory LIMIT 1;").fetchone()
                if r: self.open_360_profile(r["file_no"])
                else: messagebox.showinfo("No Records", "No equipment records in database.")
            return
        self.search_and_display(query)

    def trigger_inner_search(self):
        query = self.inner_search_entry.get().strip()
        if query: self.search_and_display(query)

    def search_and_display(self, query):
        fn = query.split(" - ")[0].strip()
        with db_connection() as conn:
            m = conn.execute("""
            SELECT file_no FROM inventory 
            WHERE LOWER(file_no) LIKE ? OR LOWER(equipment_name) LIKE ? OR LOWER(location) LIKE ? OR LOWER(serial_no) LIKE ?
            LIMIT 1;
            """, (f"%{fn.lower()}%", f"%{fn.lower()}%", f"%{fn.lower()}%", f"%{fn.lower()}%")).fetchone()

            if m:
                self.open_360_profile(m["file_no"])
            else:
                messagebox.showinfo("Not Found", f"No record found matching '{query}'.")

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
        modal.geometry("680x640")
        modal.minsize(600, 500)
        modal.grab_set()

        top = ttk.Frame(modal, padding=12, bootstyle="primary")
        top.pack(fill=X)
        
        top_left = ttk.Frame(top)
        top_left.pack(side=LEFT, fill=X, expand=True)
        ttk.Label(top_left, text=f"File NO: {file_no}", font=("Consolas", 10, "bold"), bootstyle="inverse-primary").pack(anchor=W)
        ttk.Label(top_left, text=inv["equipment_name"], font=("Segoe UI", 12, "bold"), bootstyle="inverse-primary").pack(anchor=W)

        # Print Profile Button
        ttk.Button(
            top, 
            text="🖨️ Print Profile", 
            command=lambda: self.print_360_profile(inv, proc, repairs, payments, cfg), 
            bootstyle="info"
        ).pack(side=RIGHT, padx=4)

        scroll = ttk.ScrolledFrame(modal, padding=15)
        scroll.pack(fill=BOTH, expand=True)

        if cfg.get("basic", True):
            b1 = ttk.LabelFrame(scroll, text="Basic Equipment & Placement Details", padding=10)
            b1.pack(fill=X, pady=(0, 10))
            ttk.Label(b1, text=f"Make / Model: {inv['make'] or '-'} / {inv['model'] or '-'}").pack(anchor=W)
            ttk.Label(b1, text=f"Location / Ward: {inv['location'] or '-'}").pack(anchor=W)
            ttk.Label(b1, text=f"Serial Number(s): {inv['serial_no'] or '-'}").pack(anchor=W)
            ttk.Label(b1, text=f"Local Agent: {inv['local_agent'] or '-'}").pack(anchor=W)
            if inv['po_number'] or inv['order_date']:
                ttk.Label(b1, text=f"P/O Number: {inv['po_number'] or '-'} | Order Date: {inv['order_date'] or '-'}").pack(anchor=W)

        if cfg.get("warranty", True):
            b2 = ttk.LabelFrame(scroll, text="Warranty Status", padding=10)
            b2.pack(fill=X, pady=(0, 10))
            ttk.Label(b2, text=f"Installed: {inv['installed_date'] or '-'} | Period: {inv['warranty_period'] or '-'}").pack(anchor=W)
            ttk.Label(b2, text=f"Warranty End Date: {inv['warranty_end_date'] or '-'}", font=("Segoe UI", 9, "bold"), bootstyle="success").pack(anchor=W)

        if cfg.get("sa_status", True):
            b3 = ttk.LabelFrame(scroll, text="Active S/A Contract In-Force", padding=10)
            b3.pack(fill=X, pady=(0, 10))
            is_active = inv["current_sa"] == "Yes"
            ttk.Label(b3, text=f"Status: {'ACTIVE IN-FORCE' if is_active else 'NO ACTIVE S/A'} | Provider: {inv['sa_provider'] or 'N/A'}").pack(anchor=W)
            ttk.Label(b3, text=f"Valid Up To: {inv['sa_valid_upto'] or inv['current_sa_end'] or 'N/A'}", font=("Segoe UI", 9, "bold"), bootstyle="warning").pack(anchor=W)

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

    def print_360_profile(self, inv, proc, repairs, payments, cfg):
        """Prints Quick View 360° Profile respecting Admin & Settings checklist.
           Per user request: NO department header, NO signature blocks, pure clean dossier!"""
        import html
        sections_html = []

        if cfg.get("basic", True):
            sections_html.append(f"""
            <div class="profile-section">
              <div class="profile-section-hdr">1. Basic Equipment & Placement Details</div>
              <div class="profile-grid">
                <div class="profile-item"><span class="profile-lbl">File NO</span><span class="profile-val">{html.escape(str(inv['file_no']))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Equipment Name</span><span class="profile-val">{html.escape(str(inv['equipment_name']))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Make / Model</span><span class="profile-val">{html.escape(str(inv['make'] or '-'))} / {html.escape(str(inv['model'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Location / Ward</span><span class="profile-val">{html.escape(str(inv['location'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Serial Number(s)</span><span class="profile-val">{html.escape(str(inv['serial_no'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Local Agent</span><span class="profile-val">{html.escape(str(inv['local_agent'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">P/O NO & Date</span><span class="profile-val">{html.escape(str(inv['po_number'] or '-'))} | {html.escape(str(inv['order_date'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Quantity</span><span class="profile-val">{html.escape(str(inv['qty'] or 1))}</span></div>
              </div>
            </div>
            """)

        if cfg.get("warranty", True):
            sections_html.append(f"""
            <div class="profile-section">
              <div class="profile-section-hdr">2. Warranty Status</div>
              <div class="profile-grid">
                <div class="profile-item"><span class="profile-lbl">Installed Date</span><span class="profile-val">{html.escape(str(inv['installed_date'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Warranty Period</span><span class="profile-val">{html.escape(str(inv['warranty_period'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Warranty End Date</span><span class="profile-val" style="color: #166534;">{html.escape(str(inv['warranty_end_date'] or '-'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Need S/A as P/O</span><span class="profile-val">{html.escape(str(inv['need_sa_po'] or 'Yes'))}</span></div>
              </div>
            </div>
            """)

        if cfg.get("sa_status", True):
            is_active = inv["current_sa"] == "Yes"
            st_color = "#166534" if is_active else "#991b1b"
            sections_html.append(f"""
            <div class="profile-section">
              <div class="profile-section-hdr">3. Active S/A Contract In-Force</div>
              <div class="profile-grid">
                <div class="profile-item"><span class="profile-lbl">Current Status</span><span class="profile-val" style="color: {st_color};">{'ACTIVE IN-FORCE' if is_active else 'NO ACTIVE S/A'}</span></div>
                <div class="profile-item"><span class="profile-lbl">S/A Provider</span><span class="profile-val">{html.escape(str(inv['sa_provider'] or 'N/A'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Valid Up To</span><span class="profile-val" style="color: #b45309;">{html.escape(str(inv['sa_valid_upto'] or inv['current_sa_end'] or 'N/A'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Current Year Cost</span><span class="profile-val">Rs. {float(inv['year_1_cost'] or 0):,.2f}</span></div>
              </div>
            </div>
            """)

        if cfg.get("next_sa", True) and proc:
            sections_html.append(f"""
            <div class="profile-section">
              <div class="profile-section-hdr">4. Upcoming Renewal Pipeline</div>
              <div class="profile-grid">
                <div class="profile-item"><span class="profile-lbl">Process Framework</span><span class="profile-val">{html.escape(str(proc['sa_process_type'] or 'Under Quotation'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Process Status</span><span class="profile-val">{html.escape(str(proc['process_status'] or 'Initiated'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Signed Date</span><span class="profile-val">{html.escape(str(proc['final_signed_date'] or 'Pending'))}</span></div>
                <div class="profile-item"><span class="profile-lbl">Proposed Renewal Start</span><span class="profile-val">{html.escape(str(proc['sa_start_date'] or '-'))}</span></div>
              </div>
            </div>
            """)

        if cfg.get("repairs", True):
            rep_rows = ""
            if repairs:
                for rep in repairs:
                    rep_rows += f"<tr><td>{html.escape(str(rep['reported_date']))}</td><td>{html.escape(str(rep['fault_description']))}</td><td>{html.escape(str(rep['job_status']))}</td><td>Rs. {float(rep['estimate_amount'] or 0):,.2f}</td></tr>"
            else:
                rep_rows = "<tr><td colspan='4' style='text-align: center; color: #64748b;'>No breakdown records logged.</td></tr>"

            sections_html.append(f"""
            <div class="profile-section">
              <div class="profile-section-hdr">5. Breakdown & Repair History ({len(repairs)})</div>
              <div style="padding: 10px 12px;">
                <table class="print-table">
                  <thead><tr><th>Reported Date</th><th>Fault Description</th><th>Status</th><th>Estimate</th></tr></thead>
                  <tbody>{rep_rows}</tbody>
                </table>
              </div>
            </div>
            """)

        if cfg.get("financials", True):
            total_paid = sum(p["amount"] for p in payments)
            sections_html.append(f"""
            <div class="profile-section">
              <div class="profile-section-hdr">6. Financial Vouchers & Settlement</div>
              <div class="profile-grid">
                <div class="profile-item"><span class="profile-lbl">Total Settled S/A Payments</span><span class="profile-val" style="color: #166534; font-size: 13px;">Rs. {total_paid:,.2f}</span></div>
                <div class="profile-item"><span class="profile-lbl">Settled Vouchers Count</span><span class="profile-val">{len(payments)} vouchers</span></div>
              </div>
            </div>
            """)

        body_html = "".join(sections_html)
        print_document(
            title=f"360° Asset Profile: {inv['file_no']} - {inv['equipment_name']}",
            content_html=body_html,
            is_landscape=False
        )

if __name__ == "__main__":
    app = THPEquipmentApplication()
    app.mainloop()

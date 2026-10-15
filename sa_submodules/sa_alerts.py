# -*- coding: utf-8 -*-
"""
S/A Contracts Hub - Submodule 4: Expiry Alerts & Action Pending Trackers
- Expiry Quick Filter Alerts (6 Interactive Filter Buttons)
- Action Pending Trackers (4 Interactive Filter Buttons)
- Real-time Clickable Filter Grid with authentic cell dividing rules & gridlines (Request 4)
- Jump-to-Procurement action
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import datetime
import logging
from db_manager import db_connection, DATE_FORMAT
from print_helper import print_document

log = logging.getLogger("thp_bme_sa_alerts")

ALERT_HEADERS = [
    "Alert Category", "File NO", "Equipment Name", "Hospital Ward / Location",
    "Current Status", "Validity / Action Due Date", "Authorized Agent", "Priority Renewal Action"
]

class SAAlertsView(ttk.Frame):
    def __init__(self, parent, on_open_procurement=None):
        super().__init__(parent)
        self.on_open_procurement = on_open_procurement
        self.all_records = []
        self.displayed_records = []
        self.sheet = None
        self.tree = None
        self.current_filter_title = "All Equipment Expiry Alerts & Action Trackers"
        
        self.create_ui()
        self.scan_and_load_alerts()

    def create_ui(self):
        container = ttk.Frame(self, padding=15)
        container.pack(fill=BOTH, expand=True)

        # Header Bar with Rose/Danger Red Accent (Request 3)
        top = ttk.Frame(container)
        top.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            top, 
            text="🔴 Expiry Quick Filter Alerts & Action Pending Trackers", 
            font=("Segoe UI", 12, "bold"),
            bootstyle="danger"
        ).pack(side=LEFT)
        ttk.Button(top, text="🔄 Rescan & Show All", command=self.reset_to_all, bootstyle="secondary").pack(side=RIGHT)

        # -------------------------------------------------------------
        # Section 1: Expiry Quick Filter Alerts (S/A and Warranty Rows)
        # -------------------------------------------------------------
        exp_frame = ttk.LabelFrame(container, text="1. Expiry Quick Filter Alerts (Click any button to filter)", padding=10, bootstyle="danger")
        exp_frame.pack(fill=X, pady=(0, 10))

        # Row 1.a: S/A Contracts Expiry
        ttk.Label(exp_frame, text="S/A Contracts Expiry Trackers:", font=("Segoe UI", 9, "bold")).pack(anchor=W, pady=(0, 2))
        b_row1_sa = ttk.Frame(exp_frame)
        b_row1_sa.pack(fill=X, pady=(0, 6))

        self.btn_sa_expired = ttk.Button(b_row1_sa, text="🚨 S/A Expired: 0", command=lambda: self.apply_filter("sa_expired"), bootstyle="danger-outline")
        self.btn_sa_expired.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_sa_30 = ttk.Button(b_row1_sa, text="⚠️ S/A Expiring 30d: 0", command=lambda: self.apply_filter("sa_30"), bootstyle="danger-outline")
        self.btn_sa_30.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_sa_60 = ttk.Button(b_row1_sa, text="⏳ S/A Expiring 60d: 0", command=lambda: self.apply_filter("sa_60"), bootstyle="warning-outline")
        self.btn_sa_60.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_sa_90 = ttk.Button(b_row1_sa, text="📅 S/A Expiring 90d: 0", command=lambda: self.apply_filter("sa_90"), bootstyle="info-outline")
        self.btn_sa_90.pack(side=LEFT, padx=3, fill=X, expand=True)

        # Row 1.b: Warranty Expiry (Expired, 30d, 60d, 90d)
        ttk.Label(exp_frame, text="Warranty Expiry & Post-Warranty Trackers:", font=("Segoe UI", 9, "bold")).pack(anchor=W, pady=(2, 2))
        b_row1_war = ttk.Frame(exp_frame)
        b_row1_war.pack(fill=X)

        self.btn_war_expired = ttk.Button(b_row1_war, text="🛡️ War. Expired: 0", command=lambda: self.apply_filter("war_expired"), bootstyle="secondary-outline")
        self.btn_war_expired.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_war_30 = ttk.Button(b_row1_war, text="🛡️ War. Expiring 30d: 0", command=lambda: self.apply_filter("war_30"), bootstyle="warning-outline")
        self.btn_war_30.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_war_60 = ttk.Button(b_row1_war, text="🛡️ War. Expiring 60d: 0", command=lambda: self.apply_filter("war_60"), bootstyle="info-outline")
        self.btn_war_60.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_war_90 = ttk.Button(b_row1_war, text="🛡️ War. Expiring 90d: 0", command=lambda: self.apply_filter("war_90"), bootstyle="info-outline")
        self.btn_war_90.pack(side=LEFT, padx=3, fill=X, expand=True)

        # -------------------------------------------------------------
        # Section 2: Action Pending Trackers (4 Interactive Buttons)
        # -------------------------------------------------------------
        act_frame = ttk.LabelFrame(container, text="2. Action Pending Trackers (Click any button to view stage)", padding=10, bootstyle="warning")
        act_frame.pack(fill=X, pady=(0, 10))

        b_row2 = ttk.Frame(act_frame)
        b_row2.pack(fill=X)

        self.btn_act_consent = ttk.Button(b_row2, text="📝 Consent Pending: 0", command=lambda: self.apply_filter("act_consent"), bootstyle="warning-outline")
        self.btn_act_consent.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_act_quote = ttk.Button(b_row2, text="📄 Quote Call Pending: 0", command=lambda: self.apply_filter("act_quote"), bootstyle="warning-outline")
        self.btn_act_quote.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_act_bec = ttk.Button(b_row2, text="⚖️ BEC Pending: 0", command=lambda: self.apply_filter("act_bec"), bootstyle="warning-outline")
        self.btn_act_bec.pack(side=LEFT, padx=3, fill=X, expand=True)

        self.btn_act_sign = ttk.Button(b_row2, text="🤝 Signing Pending: 0", command=lambda: self.apply_filter("act_sign"), bootstyle="success-outline")
        self.btn_act_sign.pack(side=LEFT, padx=3, fill=X, expand=True)

        # -------------------------------------------------------------
        # Section 3: Interactive Table with Authentic Dividing Rules (Request 4)
        # -------------------------------------------------------------
        table_card = ttk.LabelFrame(container, text="Filtered Action Items & Priority Direct Actions", padding=10)
        table_card.pack(fill=BOTH, expand=True, pady=(0, 10))

        tbl_tools = ttk.Frame(table_card)
        tbl_tools.pack(fill=X, pady=(0, 6))

        self.lbl_status = ttk.Label(tbl_tools, text="Showing all active alerts.", font=("Segoe UI", 9, "bold"), bootstyle="info")
        self.lbl_status.pack(side=LEFT)

        ttk.Button(tbl_tools, text="🚀 Open in S/A Procurement Track Form", command=self.open_selected_in_procurement, bootstyle="primary").pack(side=RIGHT, padx=3)
        ttk.Button(tbl_tools, text="🖨️ Print Alerts Report", command=self.print_alerts_report, bootstyle="info").pack(side=RIGHT, padx=3)

        sheet_container = ttk.Frame(table_card)
        sheet_container.pack(fill=BOTH, expand=True)

        # Use tksheet.Sheet for clear dividing rules and gridlines (just like S/A Master Sheet)
        try:
            from tksheet import Sheet
            self.sheet = Sheet(
                sheet_container,
                headers=ALERT_HEADERS,
                theme="dark blue",
                show_x_scrollbar=True,
                show_y_scrollbar=True,
                show_row_index=False,
                empty_horizontal=0,
                empty_vertical=0
            )
            self.sheet.enable_bindings(
                "single_select", "row_select", "column_width_resize",
                "arrowkeys", "right_click_popup_menu", "copy", "select_all"
            )
            # Set comfortable column widths
            widths = [160, 110, 180, 160, 140, 130, 130, 150]
            for i, w in enumerate(widths):
                self.sheet.column_width(i, width=w)
            self.sheet.pack(fill=BOTH, expand=True)
        except Exception as e:
            log.warning(f"tksheet not available in alerts: {e}. Falling back to treeview.")
            self.setup_fallback_tree(sheet_container)

    def setup_fallback_tree(self, parent):
        scroll_y = ttk.Scrollbar(parent, orient=VERTICAL)
        scroll_x = ttk.Scrollbar(parent, orient=HORIZONTAL)

        self.tree = ttk.Treeview(
            parent,
            columns=ALERT_HEADERS,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)
        self.tree.pack(fill=BOTH, expand=True)

        widths = [160, 110, 180, 160, 140, 130, 130, 150]
        for h, w in zip(ALERT_HEADERS, widths):
            self.tree.heading(h, text=h)
            self.tree.column(h, width=w, minwidth=70)

        self.tree.bind("<Double-1>", lambda e: self.open_selected_in_procurement())

    def scan_and_load_alerts(self):
        """Scans database, calculates live count for all 10 buttons, and populates list."""
        today = datetime.date.today()
        self.all_records = []

        c_sa_exp = 0
        c_sa_30 = 0
        c_sa_60 = 0
        c_sa_90 = 0
        c_war_exp = 0
        c_war_30 = 0
        c_war_60 = 0
        c_war_90 = 0

        c_consent = 0
        c_quote = 0
        c_bec = 0
        c_sign = 0

        try:
            with db_connection() as conn:
                # 1. S/A in-force
                sa_rows = conn.execute("""
                SELECT i.file_no, i.equipment_name, i.location, i.local_agent, i.sa_provider, i.sa_valid_upto,
                       COALESCE(p.process_status, 'Not Initiated') AS proc_status
                FROM inventory i
                LEFT JOIN sa_procurement_track p ON i.file_no = p.file_no
                WHERE i.current_sa = 'Yes' AND i.sa_valid_upto IS NOT NULL AND TRIM(i.sa_valid_upto) != '';
                """).fetchall()

                # 2. Warranties (where current_sa != 'Yes')
                war_rows = conn.execute("""
                SELECT file_no, equipment_name, location, local_agent, warranty_end_date
                FROM inventory
                WHERE warranty_end_date IS NOT NULL AND TRIM(warranty_end_date) != ''
                  AND (current_sa != 'Yes' OR current_sa IS NULL);
                """).fetchall()

                # 3. Action Pending Trackers
                proc_rows = conn.execute("""
                SELECT p.file_no, i.equipment_name, i.location, i.local_agent,
                       p.inv_holder_sent_date, p.inv_holder_recv_date, p.inv_holder_status,
                       p.doc_send_date, p.quotation_recv_date,
                       p.bec_sub_date, p.bec_rec_recv_date, p.bec_recommendation,
                       p.final_signed_date, p.process_status
                FROM sa_procurement_track p
                LEFT JOIN inventory i ON p.file_no = i.file_no;
                """).fetchall()

            # Process S/A Expiry
            for r in sa_rows:
                v_str = r["sa_valid_upto"].strip().replace('.', '/').replace('-', '/')
                try:
                    v_date = datetime.datetime.strptime(v_str, DATE_FORMAT).date()
                except Exception:
                    continue

                days = (v_date - today).days

                cat_key = None
                if days < 0:
                    c_sa_exp += 1
                    cat_key = "sa_expired"
                    cat_lbl = f"🚨 Expired ({abs(days)}d ago)"
                elif days <= 30:
                    c_sa_30 += 1
                    cat_key = "sa_30"
                    cat_lbl = f"⚠️ Expiring in {days} Days"
                elif days <= 60:
                    c_sa_60 += 1
                    cat_key = "sa_60"
                    cat_lbl = f"⏳ Expiring in {days} Days"
                elif days <= 90:
                    c_sa_90 += 1
                    cat_key = "sa_90"
                    cat_lbl = f"📅 Expiring in {days} Days"

                if cat_key:
                    self.all_records.append({
                        "filter_keys": [cat_key],
                        "values": [
                            cat_lbl, r["file_no"], r["equipment_name"], r["location"] or "-",
                            f"S/A ({r['sa_provider'] or 'N/A'})", r["sa_valid_upto"], r["local_agent"] or "-",
                            "Initiate / Renew S/A"
                        ]
                    })

            # Process Warranty Expiry
            for r in war_rows:
                w_str = r["warranty_end_date"].strip().replace('.', '/').replace('-', '/')
                try:
                    w_date = datetime.datetime.strptime(w_str, DATE_FORMAT).date()
                except Exception:
                    continue

                days = (w_date - today).days
                cat_key = None
                if days < 0:
                    c_war_exp += 1
                    cat_key = "war_expired"
                    cat_lbl = f"🛡️ Warranty Expired ({abs(days)}d ago)"
                elif days <= 30:
                    c_war_30 += 1
                    cat_key = "war_30"
                    cat_lbl = f"🛡️ Warranty Expiring in {days}d"
                elif days <= 60:
                    c_war_60 += 1
                    cat_key = "war_60"
                    cat_lbl = f"🛡️ Warranty Expiring in {days}d"
                elif days <= 90:
                    c_war_90 += 1
                    cat_key = "war_90"
                    cat_lbl = f"🛡️ Warranty Expiring in {days}d"

                if cat_key:
                    self.all_records.append({
                        "filter_keys": [cat_key],
                        "values": [
                            cat_lbl, r["file_no"], r["equipment_name"], r["location"] or "-",
                            "No S/A in Place", r["warranty_end_date"], r["local_agent"] or "-",
                            "Prepare Quotation Call"
                        ]
                    })

            # Process 4 Action Pending Trackers
            for p in proc_rows:
                # 1. Consent Pending
                if p["inv_holder_sent_date"] and not p["inv_holder_recv_date"]:
                    c_consent += 1
                    self.all_records.append({
                        "filter_keys": ["act_consent"],
                        "values": [
                            "📝 Inv. Holder Consent Pending", p["file_no"], p["equipment_name"] or "-", p["location"] or "-",
                            "Sent for Consent", p["inv_holder_sent_date"], p["local_agent"] or "-",
                            "Follow up with Consultant"
                        ]
                    })
                # 2. Quotation Call Pending
                if p["doc_send_date"] and not p["quotation_recv_date"]:
                    c_quote += 1
                    self.all_records.append({
                        "filter_keys": ["act_quote"],
                        "values": [
                            "📄 Waiting Quotation", p["file_no"], p["equipment_name"] or "-", p["location"] or "-",
                            "Doc Request Sent", p["doc_send_date"], p["local_agent"] or "-",
                            "Send Agent Reminder"
                        ]
                    })
                # 3. BEC Evaluation Pending
                if p["bec_sub_date"] and not p["bec_rec_recv_date"]:
                    c_bec += 1
                    self.all_records.append({
                        "filter_keys": ["act_bec"],
                        "values": [
                            "⚖️ BEC Evaluation Pending", p["file_no"], p["equipment_name"] or "-", p["location"] or "-",
                            "Submitted to BEC", p["bec_sub_date"], p["local_agent"] or "-",
                            "Follow up BEC Minutes"
                        ]
                    })
                # 4. Final Signing Pending
                if p["bec_rec_recv_date"] and not p["final_signed_date"]:
                    c_sign += 1
                    self.all_records.append({
                        "filter_keys": ["act_sign"],
                        "values": [
                            "🤝 Agreement Signing Pending", p["file_no"], p["equipment_name"] or "-", p["location"] or "-",
                            f"BEC: {p['bec_recommendation'] or 'Approved'}", p["bec_rec_recv_date"], p["local_agent"] or "-",
                            "Prepare S/A Agreement"
                        ]
                    })

        except Exception as e:
            log.error(f"Error scanning alerts: {e}")

        # Update button labels with real counts
        self.btn_sa_expired.config(text=f"🚨 S/A Expired: {c_sa_exp}")
        self.btn_sa_30.config(text=f"⚠️ S/A Expiring 30d: {c_sa_30}")
        self.btn_sa_60.config(text=f"⏳ S/A Expiring 60d: {c_sa_60}")
        self.btn_sa_90.config(text=f"📅 S/A Expiring 90d: {c_sa_90}")
        self.btn_war_expired.config(text=f"🛡️ War. Expired: {c_war_exp}")
        self.btn_war_30.config(text=f"🛡️ War. Expiring 30d: {c_war_30}")
        self.btn_war_60.config(text=f"🛡️ War. Expiring 60d: {c_war_60}")
        self.btn_war_90.config(text=f"🛡️ War. Expiring 90d: {c_war_90}")

        self.btn_act_consent.config(text=f"📝 Consent Pending: {c_consent}")
        self.btn_act_quote.config(text=f"📄 Quote Pending: {c_quote}")
        self.btn_act_bec.config(text=f"⚖️ BEC Pending: {c_bec}")
        self.btn_act_sign.config(text=f"🤝 Signing Pending: {c_sign}")

        self.reset_to_all()

    def render_data(self):
        table_rows = [r["values"] for r in self.displayed_records]
        if self.sheet:
            self.sheet.set_sheet_data(table_rows)
            try:
                self.sheet.set_all_cell_sizes_to_text(True)
            except Exception:
                pass
        elif self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)
            for row in table_rows:
                self.tree.insert("", END, values=row)

    def apply_filter(self, key):
        title_map = {
            "sa_expired": "S/A Expired Equipment List",
            "sa_30": "S/A Expiring in 30 Days",
            "sa_60": "S/A Expiring in 60 Days",
            "sa_90": "S/A Expiring in 90 Days",
            "war_expired": "Warranty Expired Equipment List",
            "war_30": "Warranty Expiring in 30 Days",
            "war_60": "Warranty Expiring in 60 Days",
            "war_90": "Warranty Expiring in 90 Days",
            "act_consent": "Action Pending: Inventory Holder Consent",
            "act_quote": "Action Pending: Quotation Call Dispatches",
            "act_bec": "Action Pending: Technical Evaluation Committee (BEC)",
            "act_sign": "Action Pending: Final Agreement Signing"
        }
        self.current_filter_title = title_map.get(key, "Equipment Alerts Report")
        self.displayed_records = [r for r in self.all_records if key in r["filter_keys"]]
        self.render_data()
        self.lbl_status.config(text=f"Filter: {self.current_filter_title} ({len(self.displayed_records)} items)")

    def reset_to_all(self):
        self.current_filter_title = "All Equipment Expiry Alerts & Action Trackers"
        self.displayed_records = list(self.all_records)
        self.render_data()
        self.lbl_status.config(text=f"Showing all {len(self.displayed_records)} priority alerts & pending actions.")

    def print_alerts_report(self):
        """Prints currently filtered alerts with document title dynamically matching the active filter."""
        import html
        th_cells = "".join(f"<th>{html.escape(h)}</th>" for h in ALERT_HEADERS)
        rows_html = ""
        for rec in self.displayed_records:
            vals = rec["values"]
            td_cells = "".join(f"<td>{html.escape(str(v))}</td>" for v in vals)
            rows_html += f"<tr>{td_cells}</tr>\n"

        table_html = f"""
        <table class="print-table">
          <thead><tr>{th_cells}</tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        """
        print_document(title=self.current_filter_title, content_html=table_html, is_landscape=True)

    def open_selected_in_procurement(self):
        file_no = None
        if self.sheet:
            selected = self.sheet.get_currently_selected()
            if selected and selected.row is not None and 0 <= selected.row < len(self.displayed_records):
                file_no = self.displayed_records[selected.row]["values"][1]
        elif self.tree:
            sel = self.tree.selection()
            if sel:
                item = self.tree.item(sel[0])
                file_no = item["values"][1]

        if file_no and self.on_open_procurement:
            self.on_open_procurement(file_no)
        else:
            messagebox.showinfo("Select Item", "Please select a row from the table first.")

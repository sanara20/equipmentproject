# -*- coding: utf-8 -*-
"""
S/A Contracts Hub - Submodule 2: S/A Procurement Track Pipeline Form
Features:
- Separate S/A Process Classification section (Request 2)
- Intelligent Date-Based Auto-Selection (5-Years Agreed Price vs Post 5-Year Quotation Call)
- Manual dropdown override
- Force Promote to Active S/A Button
- 4-Stage Procurement Pipeline Tracker
- Clear Form Button
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import datetime
import logging
from autocomplete import AutocompleteCombobox
from db_manager import db_connection, DATE_FORMAT, get_dropdown_options, add_master_list_value

log = logging.getLogger("thp_bme_sa_proc")

class SAProcurementView(ttk.Frame):
    def __init__(self, parent, on_update_callback=None, on_back_to_asset=None):
        super().__init__(parent)
        self.on_update_callback = on_update_callback
        self.on_back_to_asset = on_back_to_asset
        self.create_ui()
        self.load_file_numbers()

    def create_ui(self):
        # Wrap the whole procurement tab in a ScrolledFrame to ensure smooth viewing on all screens
        scroll_outer = ttk.ScrolledFrame(self, padding=15, autohide=True)
        scroll_outer.pack(fill=BOTH, expand=True)

        container = ttk.Frame(scroll_outer)
        container.pack(fill=BOTH, expand=True)

        # Title Header
        top_title = ttk.Frame(container)
        top_title.pack(fill=X, pady=(0, 8))
        ttk.Label(
            top_title, 
            text="🟢 S/A Procurement Track Form & Upcoming Renewal Pipeline", 
            font=("Segoe UI", 12, "bold"),
            bootstyle="success"
        ).pack(side=LEFT)

        # Header with LEFT: Search / Select File NO, RIGHT: Current Active S/A Status
        top_bar = ttk.Frame(container)
        top_bar.pack(fill=X, pady=(0, 10))

        # LEFT SIDE: Search / Select File NO
        sel_box = ttk.LabelFrame(top_bar, text="Search / Select File NO", padding=8, bootstyle="primary")
        sel_box.pack(side=LEFT, fill=Y)
        combo_row = ttk.Frame(sel_box)
        combo_row.pack(anchor=W, padx=4, pady=4)
        self.file_combo = AutocompleteCombobox(combo_row, width=28)
        self.file_combo.pack(side=LEFT)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)
        ttk.Button(combo_row, text="🧹 Clear", command=self.clear_form, bootstyle="secondary-outline").pack(side=LEFT, padx=(6, 0))

        # RIGHT SIDE: Current Active S/A Status
        self.status_card = ttk.LabelFrame(top_bar, text="Current Active S/A Status", padding=8, bootstyle="info")
        self.status_card.pack(side=RIGHT, fill=BOTH, expand=True, padx=(12, 0))
        self.active_sa_lbl = ttk.Label(self.status_card, text="-- Select an equipment File NO on the left to view active contract details --", font=("Segoe UI", 9))
        self.active_sa_lbl.pack(anchor=W, padx=4, pady=4)

        # -------------------------------------------------------------
        # Request 2: Separate Process Type Section with Date-Based Auto-Detection
        # -------------------------------------------------------------
        proc_type_box = ttk.LabelFrame(container, text="📋 S/A Process Framework & Procurement Type", padding=(12, 8), bootstyle="info")
        proc_type_box.pack(fill=X, pady=(0, 10))

        pt_row = ttk.Frame(proc_type_box)
        pt_row.pack(anchor=W)

        ttk.Label(pt_row, text="S/A Process Type *:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 8))
        
        self.c_proc_type = AutocompleteCombobox(
            pt_row,
            completevalues=get_dropdown_options("sa_process_type") or [
                "5-Years Agreed Price S/A",
                "Post 5-Year Quotation Call S/A",
                "Direct Ministry Supply S/A",
                "Annual Rate Contract S/A",
                "Direct OEM Comprehensive S/A"
            ],
            width=34
        )
        self.c_proc_type.pack(side=LEFT)

        self.lbl_proc_auto_info = ttk.Label(
            proc_type_box,
            text="Select an equipment File NO above to auto-detect process type based on installation date...",
            font=("Segoe UI", 8),
            bootstyle="secondary"
        )
        self.lbl_proc_auto_info.pack(anchor=W, pady=(4, 0))

        # -------------------------------------------------------------
        # 4 Pipeline Stages
        # -------------------------------------------------------------
        stages_frame = ttk.Frame(container)
        stages_frame.pack(fill=BOTH, expand=True)
        stages_frame.columnconfigure(0, weight=1)
        stages_frame.columnconfigure(1, weight=1)

        # 1. Inventory Holder Consent
        stage1 = ttk.LabelFrame(stages_frame, text="1. Inventory Holder Consent & Intimation", padding=10)
        stage1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(stage1, text="Sent Date (YYYY/MM/DD):").grid(row=0, column=0, sticky=W, pady=3)
        self.e_inv_sent = ttk.Entry(stage1)
        self.e_inv_sent.grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(stage1, text="Recv Date (YYYY/MM/DD):").grid(row=1, column=0, sticky=W, pady=3)
        self.e_inv_recv = ttk.Entry(stage1)
        self.e_inv_recv.grid(row=1, column=1, sticky="ew", pady=3)

        ttk.Label(stage1, text="Consent Recommendation:").grid(row=2, column=0, sticky=W, pady=3)
        self.c_inv_status = ttk.Combobox(stage1, values=get_dropdown_options("inv_holder_status"))
        self.c_inv_status.grid(row=2, column=1, sticky="ew", pady=3)

        # 2. Quotations & Reminders
        stage2 = ttk.LabelFrame(stages_frame, text="2. Quotations & Reminders", padding=10)
        stage2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        ttk.Label(stage2, text="Doc Request Date:").grid(row=0, column=0, sticky=W, pady=3)
        self.e_doc_send = ttk.Entry(stage2)
        self.e_doc_send.grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(stage2, text="Quotation Recv Date:").grid(row=1, column=0, sticky=W, pady=3)
        self.e_quote_recv = ttk.Entry(stage2)
        self.e_quote_recv.grid(row=1, column=1, sticky="ew", pady=3)

        ttk.Label(stage2, text="Reminder 1 / 2 Dates:").grid(row=2, column=0, sticky=W, pady=3)
        self.e_reminders = ttk.Entry(stage2)
        self.e_reminders.grid(row=2, column=1, sticky="ew", pady=3)

        # 3. BEC Evaluation & Negotiations
        stage3 = ttk.LabelFrame(stages_frame, text="3. BEC Evaluation & Price Negotiations", padding=10)
        stage3.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        ttk.Label(stage3, text="BEC Rec Recv Date:").grid(row=0, column=0, sticky=W, pady=3)
        self.e_bec_recv = ttk.Entry(stage3)
        self.e_bec_recv.grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(stage3, text="BEC Recommendation:").grid(row=1, column=0, sticky=W, pady=3)
        self.c_bec_rec = ttk.Combobox(stage3, values=get_dropdown_options("bec_recommendation"))
        self.c_bec_rec.grid(row=1, column=1, sticky="ew", pady=3)

        ttk.Label(stage3, text="Price Neg Status:").grid(row=2, column=0, sticky=W, pady=3)
        self.c_price_neg = ttk.Combobox(stage3, values=get_dropdown_options("price_neg"))
        self.c_price_neg.grid(row=2, column=1, sticky="ew", pady=3)

        # 4. Final Agreement Signing & Promotion
        stage4 = ttk.LabelFrame(stages_frame, text="4. Final Agreement Signing & Promotion", padding=10)
        stage4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        ttk.Label(stage4, text="Final Signed Date:").grid(row=0, column=0, sticky=W, pady=3)
        self.e_signed_date = ttk.Entry(stage4)
        self.e_signed_date.grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(stage4, text="New S/A Start Date:").grid(row=1, column=0, sticky=W, pady=3)
        self.e_new_start = ttk.Entry(stage4)
        self.e_new_start.grid(row=1, column=1, sticky="ew", pady=3)

        ttk.Label(stage4, text="New S/A End Date:").grid(row=2, column=0, sticky=W, pady=3)
        self.e_new_end = ttk.Entry(stage4)
        self.e_new_end.grid(row=2, column=1, sticky="ew", pady=3)

        # Buttons Bar
        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=X, pady=(15, 0))

        ttk.Button(btn_bar, text="⚡ Force Promote to Active S/A Now", command=self.promote_to_active, bootstyle="warning-outline").pack(side=LEFT)
        ttk.Button(btn_bar, text="💾 Save Procurement Record", command=self.save_procurement, bootstyle="primary").pack(side=RIGHT, padx=4)
        ttk.Button(btn_bar, text="🔙 Back Primary Equipment Registration Form", command=self.back_to_asset_registry, bootstyle="info-outline").pack(side=RIGHT, padx=4)
        ttk.Button(btn_bar, text="🧹 Clear Form", command=self.clear_form, bootstyle="secondary").pack(side=RIGHT, padx=4)

    def back_to_asset_registry(self):
        """Shortcut to navigate back to Primary Equipment Registration Form."""
        if self.on_back_to_asset:
            self.on_back_to_asset()
        else:
            top = self.winfo_toplevel()
            if hasattr(top, "open_module"):
                top.open_module("asset")

    def clear_form(self):
        """Resets all fields in the procurement form to blank."""
        self.file_combo.set("")
        self.active_sa_lbl.config(text="Select a File NO above to view active contract details...")
        self.lbl_proc_auto_info.config(
            text="Select an equipment File NO above to auto-detect process type based on installation date...",
            bootstyle="secondary"
        )
        for entry in [self.e_inv_sent, self.e_inv_recv, self.e_doc_send, self.e_quote_recv,
                      self.e_reminders, self.e_bec_recv, self.e_signed_date, self.e_new_start, self.e_new_end]:
            entry.delete(0, tk.END)
        self.c_proc_type.set("")
        self.c_inv_status.set("")
        self.c_bec_rec.set("")
        self.c_price_neg.set("")

    def reset_form(self):
        self.clear_form()

    def load_file_numbers(self):
        try:
            from db_manager import get_all_file_numbers
            file_numbers = get_all_file_numbers()
            self.file_combo.set_completion_list(file_numbers)
            self.file_combo.set("")
            self.c_proc_type.set_completion_list(get_dropdown_options("sa_process_type"))
            self.c_inv_status.config(values=get_dropdown_options("inv_holder_status"))
            self.c_bec_rec.config(values=get_dropdown_options("bec_recommendation"))
            self.c_price_neg.config(values=get_dropdown_options("price_neg"))
            self.reset_form()
        except Exception as e:
            log.error(f"Error loading file numbers: {e}")

    def get_selected_file_no(self):
        val = self.file_combo.get()
        return val.split(" - ")[0].strip() if val else ""

    def on_file_selected(self, event=None):
        file_no = self.get_selected_file_no()
        if not file_no:
            return
        with db_connection() as conn:
            inv = conn.execute("SELECT * FROM inventory WHERE file_no = ?;", (file_no,)).fetchone()
            proc = conn.execute("SELECT * FROM sa_procurement_track WHERE file_no = ?;", (file_no,)).fetchone()

        if inv:
            status_text = (
                f"Equipment: {inv['equipment_name']} ({inv['location']})\n"
                f"Active S/A: {inv['current_sa']} | Provider: {inv['sa_provider'] or 'N/A'} | "
                f"Valid Up To: {inv['sa_valid_upto'] or 'N/A'} (Will safely remain in-force until renewal promotion)"
            )
            self.active_sa_lbl.config(text=status_text)

        # Clear fields
        for entry in [self.e_inv_sent, self.e_inv_recv, self.e_doc_send, self.e_quote_recv,
                      self.e_reminders, self.e_bec_recv, self.e_signed_date, self.e_new_start, self.e_new_end]:
            entry.delete(0, tk.END)

        self.c_proc_type.set("")
        self.c_inv_status.set("")
        self.c_bec_rec.set("")
        self.c_price_neg.set("")

        # -------------------------------------------------------------
        # Request 2: Date-based Auto-Selection using Warranty End Date
        # -------------------------------------------------------------
        today = datetime.date.today()
        auto_detected_type = ""
        auto_reason = ""

        if inv:
            war_end_str = (inv["warranty_end_date"] or "").strip().replace('.', '/').replace('-', '/')
            if war_end_str:
                try:
                    w_date = datetime.datetime.strptime(war_end_str, DATE_FORMAT).date()
                    diff_days = (today - w_date).days
                    diff_years = diff_days / 365.25

                    if diff_days <= 0:
                        auto_detected_type = "5-Years Agreed Price S/A"
                        auto_reason = f"Warranty Active Until: {war_end_str} ({abs(diff_days)} days remaining) → Auto-selected: 5-Years Agreed Price S/A"
                    elif diff_days <= (5 * 365.25):
                        auto_detected_type = "5-Years Agreed Price S/A"
                        auto_reason = f"Warranty Ended: {war_end_str} (Post-Warranty Elapsed: {diff_years:.1f} yrs ≤ 5 yrs) → Auto-selected: 5-Years Agreed Price S/A"
                    else:
                        auto_detected_type = "Post 5-Year Quotation Call S/A"
                        auto_reason = f"Warranty Ended: {war_end_str} (Post-Warranty Elapsed: {diff_years:.1f} yrs > 5 yrs) → Auto-selected: Post 5-Year Quotation Call S/A"
                except Exception as e:
                    log.warning(f"Error parsing warranty_end_date: {e}")

            # Fallback if warranty_end_date was empty
            if not auto_detected_type:
                alt_date_str = (inv["installed_date"] or inv["order_date"] or "").strip().replace('.', '/').replace('-', '/')
                if alt_date_str:
                    try:
                        i_date = datetime.datetime.strptime(alt_date_str, DATE_FORMAT).date()
                        diff_days = (today - i_date).days
                        diff_years = diff_days / 365.25
                        if diff_days <= (5 * 365.25):
                            auto_detected_type = "5-Years Agreed Price S/A"
                            auto_reason = f"Installed / Ordered: {alt_date_str} (Elapsed: {diff_years:.1f} yrs ≤ 5 yrs) → Auto-selected: 5-Years Agreed Price S/A"
                        else:
                            auto_detected_type = "Post 5-Year Quotation Call S/A"
                            auto_reason = f"Installed / Ordered: {alt_date_str} (Elapsed: {diff_years:.1f} yrs > 5 yrs) → Auto-selected: Post 5-Year Quotation Call S/A"
                    except Exception:
                        pass

        if not auto_detected_type:
            auto_detected_type = "5-Years Agreed Price S/A"
            auto_reason = "Default initial period (manual selection available via dropdown)"

        # Load existing procurement values if present
        if proc and proc["sa_process_type"]:
            self.c_proc_type.set(proc["sa_process_type"])
            self.lbl_proc_auto_info.config(
                text=f"Current Saved Type: '{proc['sa_process_type']}' | Warranty Calculation: {auto_reason}",
                bootstyle="info"
            )
        else:
            self.c_proc_type.set(auto_detected_type)
            self.lbl_proc_auto_info.config(
                text=f"✔ {auto_reason}",
                bootstyle="success"
            )

        if proc:
            self.e_inv_sent.insert(0, proc["inv_holder_sent_date"] or "")
            self.e_inv_recv.insert(0, proc["inv_holder_recv_date"] or "")
            self.c_inv_status.set(proc["inv_holder_status"] or "")
            self.e_doc_send.insert(0, proc["doc_send_date"] or "")
            self.e_quote_recv.insert(0, proc["quotation_recv_date"] or "")
            self.e_reminders.insert(0, proc["reminder_1_date"] or "")
            self.e_bec_recv.insert(0, proc["bec_rec_recv_date"] or "")
            self.c_bec_rec.set(proc["bec_recommendation"] or "")
            self.c_price_neg.set(proc["p_red_1_date"] or "")
            self.e_signed_date.insert(0, proc["final_signed_date"] or "")
            self.e_new_start.insert(0, proc["sa_start_date"] or "")
            self.e_new_end.insert(0, proc["sa_end_date"] or "")

    def save_procurement(self):
        file_no = self.get_selected_file_no()
        if not file_no:
            messagebox.showwarning("Missing File", "Please select a File NO first.")
            return

        proc_type = self.c_proc_type.get().strip()
        add_master_list_value("sa_process_type", proc_type)

        inv_status = self.c_inv_status.get().strip()
        if inv_status:
            add_master_list_value("inv_holder_status", inv_status)

        bec_rec = self.c_bec_rec.get().strip()
        if bec_rec:
            add_master_list_value("bec_recommendation", bec_rec)

        price_neg = self.c_price_neg.get().strip()
        if price_neg:
            add_master_list_value("price_neg", price_neg)

        final_date = self.e_signed_date.get().strip()
        bec_date = self.e_bec_recv.get().strip()
        quote_date = self.e_quote_recv.get().strip()
        doc_date = self.e_doc_send.get().strip()
        
        if final_date:
            proc_status = 'Agreement Signed'
        elif bec_date:
            proc_status = 'BEC Completed'
        elif quote_date:
            proc_status = 'Quotation Received'
        elif doc_date:
            proc_status = 'Docs Dispatched'
        else:
            proc_status = 'Initiated'

        with db_connection() as conn:
            existing = conn.execute("SELECT id FROM sa_procurement_track WHERE file_no = ?;", (file_no,)).fetchone()
            if existing:
                conn.execute("""
                UPDATE sa_procurement_track SET
                    sa_process_type = ?,
                    inv_holder_sent_date = ?,
                    inv_holder_recv_date = ?,
                    inv_holder_status = ?,
                    doc_send_date = ?,
                    quotation_recv_date = ?,
                    reminder_1_date = ?,
                    bec_rec_recv_date = ?,
                    bec_recommendation = ?,
                    p_red_1_date = ?,
                    final_signed_date = ?,
                    sa_start_date = ?,
                    sa_end_date = ?,
                    process_status = ?
                WHERE file_no = ?;
                """, (
                    proc_type, self.e_inv_sent.get().strip(), self.e_inv_recv.get().strip(),
                    self.c_inv_status.get().strip(), doc_date, quote_date,
                    self.e_reminders.get().strip(), bec_date, self.c_bec_rec.get().strip(),
                    self.c_price_neg.get().strip(), final_date, self.e_new_start.get().strip(),
                    self.e_new_end.get().strip(), proc_status, file_no
                ))
            else:
                conn.execute("""
                INSERT INTO sa_procurement_track (
                    file_no, sa_process_type, inv_holder_sent_date, inv_holder_recv_date, inv_holder_status,
                    doc_send_date, quotation_recv_date, reminder_1_date, bec_rec_recv_date,
                    bec_recommendation, p_red_1_date, final_signed_date, sa_start_date, sa_end_date, process_status
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
                """, (
                    file_no, proc_type, self.e_inv_sent.get().strip(), self.e_inv_recv.get().strip(),
                    self.c_inv_status.get().strip(), doc_date, quote_date,
                    self.e_reminders.get().strip(), bec_date, self.c_bec_rec.get().strip(),
                    self.c_price_neg.get().strip(), final_date, self.e_new_start.get().strip(),
                    self.e_new_end.get().strip(), proc_status
                ))

        messagebox.showinfo("Saved", f"Procurement status for {file_no} saved successfully!")
        if self.on_update_callback:
            self.on_update_callback()

    def promote_to_active(self):
        file_no = self.get_selected_file_no()
        if not file_no:
            messagebox.showwarning("Missing File", "Please select a File NO first.")
            return

        with db_connection() as conn:
            proc = conn.execute("SELECT * FROM sa_procurement_track WHERE file_no = ?;", (file_no,)).fetchone()
            inv = conn.execute("SELECT * FROM inventory WHERE file_no = ?;", (file_no,)).fetchone()

        if not proc or not proc["final_signed_date"]:
            messagebox.showwarning(
                "Not Ready for Promotion",
                f"File {file_no} does not have a Final Signed Date yet.\n"
                "Promotion should only occur after the agreement is formally executed."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Contract Promotion",
            f"Are you sure you want to promote {file_no} into an ACTIVE in-force S/A contract?\n\n"
            f"• Current Active S/A: {inv['current_sa']} (Provider: {inv['sa_provider'] or 'None'})\n"
            f"• New S/A Start: {proc['sa_start_date'] or 'N/A'}\n"
            f"• New S/A End / Valid Up To: {proc['sa_end_date'] or 'N/A'}\n\n"
            "This will archive current active details into Past History and set Current S/A = Yes."
        )
        if not confirm:
            return

        with db_connection() as conn:
            # 1. Archive current active S/A into history if it was Yes
            if inv["current_sa"] == "Yes" and inv["sa_valid_upto"]:
                conn.execute("""
                INSERT INTO sa_history (file_no, sa_provider, sa_start_date, sa_end_date)
                VALUES (?, ?, ?, ?);
                """, (file_no, inv["sa_provider"] or "THP", inv["current_sa_start"] or "", inv["sa_valid_upto"]))

            # 2. Promote new dates to inventory
            conn.execute("""
            UPDATE inventory SET
                current_sa = 'Yes',
                current_sa_start = ?,
                current_sa_end = ?,
                sa_valid_upto = ?,
                sa_provider = COALESCE(sa_provider, 'THP')
            WHERE file_no = ?;
            """, (proc["sa_start_date"], proc["sa_end_date"], proc["sa_end_date"], file_no))

            # 3. Mark procurement track as completed/active
            conn.execute("""
            UPDATE sa_procurement_track SET
                process_status = 'Agreement Signed & Active In-Force'
            WHERE file_no = ?;
            """, (file_no,))

        messagebox.showinfo("Promoted", f"Contract for {file_no} successfully promoted to ACTIVE in-force!")
        self.on_file_selected()
        if self.on_update_callback:
            self.on_update_callback()

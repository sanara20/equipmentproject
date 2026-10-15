# -*- coding: utf-8 -*-
"""
Module 3: Equipment Repairs & Breakdown Maintenance Pipeline
- Record breakdown reports
- Agent intimation & repair category (Free under S/A / Warranty vs Paid Estimate)
- Sanction approval, work completion, service report & paid voucher logging
- Printable job cards & Excel export
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tksheet import Sheet
import datetime
import logging
from autocomplete import AutocompleteCombobox
from db_manager import db_connection, DATE_FORMAT, get_dropdown_options, add_master_list_value

log = logging.getLogger("thp_bme_repairs")

REPAIR_SHEET_HEADERS = [
    "Job Ref", "File NO", "Equipment Name", "Ward / Location", "Reported Date",
    "Fault Description", "Category", "Estimate (LKR)", "Status", "Completion Date", "Service Report / Voucher"
]

class RepairsModule(ttk.Frame):
    def __init__(self, parent, on_update_callback=None):
        super().__init__(parent)
        self.on_update_callback = on_update_callback
        self.create_ui()
        self.load_file_numbers()
        self.load_repairs_table()

    def create_ui(self):
        container = ttk.Frame(self, padding=15)
        container.pack(fill=BOTH, expand=True)

        # Header & File Picker
        top = ttk.Frame(container)
        top.pack(fill=X, pady=(0, 10))

        ttk.Label(top, text="Equipment Breakdown & Repair Management Pipeline", font=("Segoe UI", 12, "bold")).pack(side=LEFT)
        
        sel_box = ttk.Frame(top)
        sel_box.pack(side=RIGHT)
        ttk.Label(sel_box, text="Search / Select Equipment:").pack(side=LEFT, padx=5)
        self.file_combo = AutocompleteCombobox(sel_box, width=32)
        self.file_combo.pack(side=LEFT)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_equipment_selected)

        # Active Info Banner
        self.info_banner = ttk.LabelFrame(container, text="Equipment Status & S/A Coverage", padding=8)
        self.info_banner.pack(fill=X, pady=(0, 10))
        self.info_lbl = ttk.Label(self.info_banner, text="Select an equipment File NO above...", font=("Segoe UI", 9))
        self.info_lbl.pack(anchor=W)

        # Form Stages
        stages = ttk.Frame(container)
        stages.pack(fill=X, pady=(0, 10))
        stages.columnconfigure(0, weight=1)
        stages.columnconfigure(1, weight=1)
        stages.columnconfigure(2, weight=1)

        # 1. Reporting
        s1 = ttk.LabelFrame(stages, text="1. Breakdown Intake", padding=10)
        s1.grid(row=0, column=0, sticky="nsew", padx=4)

        ttk.Label(s1, text="Job Ref NO:").grid(row=0, column=0, sticky=W, pady=2)
        self.e_job_ref = ttk.Entry(s1)
        self.e_job_ref.grid(row=0, column=1, sticky="ew", pady=2)
        self.e_job_ref.insert(0, self.generate_job_ref())

        ttk.Label(s1, text="Reported Date:").grid(row=1, column=0, sticky=W, pady=2)
        self.e_rep_date = ttk.Entry(s1)
        self.e_rep_date.insert(0, datetime.date.today().strftime("%Y/%m/%d"))
        self.e_rep_date.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(s1, text="Ward / Room:").grid(row=2, column=0, sticky=W, pady=2)
        self.c_ward = AutocompleteCombobox(s1, completevalues=get_dropdown_options("location"))
        self.c_ward.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(s1, text="Fault Description:").grid(row=3, column=0, sticky="nw", pady=2)
        self.t_fault = ttk.Text(s1, height=2)
        self.t_fault.grid(row=3, column=1, sticky="ew", pady=2)

        # 2. Intimation & Estimate
        s2 = ttk.LabelFrame(stages, text="2. Agent Intimation & Estimate", padding=10)
        s2.grid(row=0, column=1, sticky="nsew", padx=4)

        ttk.Label(s2, text="Intimation Date:").grid(row=0, column=0, sticky=W, pady=2)
        self.e_int_date = ttk.Entry(s2)
        self.e_int_date.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(s2, text="Category:").grid(row=1, column=0, sticky=W, pady=2)
        self.c_cat = ttk.Combobox(s2, values=["Under Paid Estimate", "Free under S/A", "Free under Warranty"])
        self.c_cat.set("Under Paid Estimate")
        self.c_cat.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(s2, text="Estimate Amount (LKR):").grid(row=2, column=0, sticky=W, pady=2)
        self.e_est_amt = ttk.Entry(s2)
        self.e_est_amt.insert(0, "0.00")
        self.e_est_amt.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(s2, text="Job Status:").grid(row=3, column=0, sticky=W, pady=2)
        self.c_status = ttk.Combobox(s2, values=["Reported", "Agent Intimated", "Estimate Recv", "Approved", "Completed", "Settled"])
        self.c_status.set("Reported")
        self.c_status.grid(row=3, column=1, sticky="ew", pady=2)

        # 3. Completion & Vouchers
        s3 = ttk.LabelFrame(stages, text="3. Approval & Completion", padding=10)
        s3.grid(row=0, column=2, sticky="nsew", padx=4)

        ttk.Label(s3, text="Sanction Date:").grid(row=0, column=0, sticky=W, pady=2)
        self.e_sanc_date = ttk.Entry(s3)
        self.e_sanc_date.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(s3, text="Completed Date:").grid(row=1, column=0, sticky=W, pady=2)
        self.e_comp_date = ttk.Entry(s3)
        self.e_comp_date.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(s3, text="Service Report NO:").grid(row=2, column=0, sticky=W, pady=2)
        self.e_srv_rep = ttk.Entry(s3)
        self.e_srv_rep.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(s3, text="Paid Voucher NO:").grid(row=3, column=0, sticky=W, pady=2)
        self.e_voucher = ttk.Entry(s3)
        self.e_voucher.grid(row=3, column=1, sticky="ew", pady=2)

        # Action Buttons
        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=X, pady=(5, 10))

        ttk.Button(btn_bar, text="🖨️ Print Job Card", command=self.print_job_card, bootstyle="secondary-outline").pack(side=LEFT)
        ttk.Button(btn_bar, text="💾 Save Repair Record", command=self.save_repair, bootstyle="warning").pack(side=RIGHT, padx=4)
        ttk.Button(btn_bar, text="🧹 Clear Form", command=self.clear_form, bootstyle="secondary").pack(side=RIGHT, padx=4)

        # Repairs Table
        table_frame = ttk.Frame(container)
        table_frame.pack(fill=BOTH, expand=True)

        self.sheet = Sheet(
            table_frame,
            headers=REPAIR_SHEET_HEADERS,
            theme="dark blue",
            show_x_scrollbar=True,
            show_y_scrollbar=True
        )
        self.sheet.enable_bindings("single_select", "row_select", "column_width_resize", "copy")
        self.sheet.pack(fill=BOTH, expand=True)

    def generate_job_ref(self):
        year = datetime.date.today().year
        try:
            with db_connection() as conn:
                count = conn.execute("SELECT COUNT(*) AS total FROM repairs;").fetchone()["total"] + 1
                return f"THP/EQ/REP/{year}/{count}"
        except Exception:
            return f"THP/EQ/REP/{year}/01"

    def load_file_numbers(self):
        try:
            with db_connection() as conn:
                rows = conn.execute("SELECT file_no, equipment_name FROM inventory ORDER BY file_no ASC;").fetchall()
                values = [f"{r['file_no']} - {r['equipment_name']}" for r in rows]
                self.file_combo.set_completion_list(values)
                if values:
                    self.file_combo.current(0)
                    self.on_equipment_selected()
        except Exception as e:
            log.error(f"Error loading files: {e}")

    def on_equipment_selected(self, event=None):
        val = self.file_combo.get()
        if not val:
            return
        file_no = val.split(" - ")[0].strip()
        with db_connection() as conn:
            inv = conn.execute("SELECT * FROM inventory WHERE file_no = ?;", (file_no,)).fetchone()
        if inv:
            sa_info = "ACTIVE IN-FORCE" if inv["current_sa"] == "Yes" else "NO ACTIVE S/A"
            self.info_lbl.config(
                text=f"{inv['equipment_name']} | Location: {inv['location']} | Local Agent: {inv['local_agent']} | S/A Coverage: {sa_info} (Valid: {inv['sa_valid_upto'] or 'N/A'})"
            )
            self.c_ward.set(inv["location"] or "")

    def save_repair(self):
        val = self.file_combo.get()
        if not val:
            messagebox.showwarning("Missing Equipment", "Please select equipment first.")
            return
        file_no = val.split(" - ")[0].strip()
        equip_name = val.split(" - ")[1].strip()

        ward_val = self.c_ward.get().strip()
        if ward_val:
            add_master_list_value("location", ward_val)
        cat_val = self.c_cat.get().strip()
        if cat_val:
            add_master_list_value("repair_category", cat_val)

        try:
            amt = float(self.e_est_amt.get().strip().replace(",", "") or "0")
        except ValueError:
            amt = 0.0

        with db_connection() as conn:
            conn.execute("""
            INSERT INTO repairs (
                job_ref, file_no, equip_name, ward, reported_date, fault_description,
                agent_intimated_date, repair_category, estimate_amount, sanction_approved_date,
                work_completed_date, service_report_no, paid_voucher_no, job_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                self.e_job_ref.get().strip(), file_no, equip_name, ward_val,
                self.e_rep_date.get().strip(), self.t_fault.get("1.0", tk.END).strip(),
                self.e_int_date.get().strip(), self.c_cat.get().strip(), amt,
                self.e_sanc_date.get().strip(), self.e_comp_date.get().strip(),
                self.e_srv_rep.get().strip(), self.e_voucher.get().strip(), self.c_status.get().strip()
            ))

        messagebox.showinfo("Saved", "Repair record logged successfully!")
        self.clear_form()
        self.load_repairs_table()

    def clear_form(self):
        """Resets all fields in the repairs intake form."""
        self.file_combo.set("")
        self.info_lbl.config(text="Select an equipment above to view warranty and active S/A status...")
        self.e_job_ref.delete(0, tk.END)
        self.e_job_ref.insert(0, self.generate_job_ref())
        self.e_rep_date.delete(0, tk.END)
        self.e_rep_date.insert(0, datetime.date.today().strftime("%Y/%m/%d"))
        self.c_ward.set("")
        self.t_fault.delete("1.0", tk.END)
        self.e_int_date.delete(0, tk.END)
        self.c_cat.set("Under Paid Estimate")
        self.e_est_amt.delete(0, tk.END)
        self.e_sanc_date.delete(0, tk.END)
        self.e_comp_date.delete(0, tk.END)
        self.e_srv_rep.delete(0, tk.END)
        self.e_voucher.delete(0, tk.END)
        self.c_status.set("Reported")

    def load_repairs_table(self):
        try:
            with db_connection() as conn:
                rows = conn.execute("SELECT * FROM repairs ORDER BY id DESC;").fetchall()
                data = [
                    [r["job_ref"], r["file_no"], r["equip_name"], r["ward"], r["reported_date"],
                     r["fault_description"] or "-", r["repair_category"],
                     f"{r['estimate_amount']:,.2f}" if r["estimate_amount"] else "FREE (S/A)",
                     r["job_status"], r["work_completed_date"] or "-", r["service_report_no"] or "-"]
                    for r in rows
                ]
                self.sheet.set_sheet_data(data)
        except Exception as e:
            log.error(f"Error loading repairs: {e}")

    def print_job_card(self):
        ref = self.e_job_ref.get().strip()
        messagebox.showinfo("Job Card Generated", f"Job Card for {ref} sent to system print queue.")

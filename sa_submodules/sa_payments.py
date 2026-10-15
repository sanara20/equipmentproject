# -*- coding: utf-8 -*-
"""
S/A Contracts Hub - Submodule 3: S/A Payment Ledger & Net Financial Budget Engine
- Record installment payments against vouchers.
- Dynamically calculate actual cash required for custom periods:
  Net Cash Required = Gross Contract Commitment for Period - Settled Installment Vouchers
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pandas as pd
from tksheet import Sheet
import json
import datetime
import logging
from db_manager import db_connection, DATE_FORMAT

log = logging.getLogger("thp_bme_sa_payments")

PAYMENT_HEADERS = ["ID", "File NO", "Year NO", "Installment NO", "Period Start", "Period End", "Amount (LKR)", "Voucher NO", "Paid Date"]

class SAPaymentsView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_ui()
        self.load_payments()

    def create_ui(self):
        container = ttk.Frame(self, padding=15)
        container.pack(fill=BOTH, expand=True)

        # Title
        ttk.Label(container, text="S/A Payment Ledger & Net Financial Budget Engine", font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=(0, 10))

        # 1. Net Cash Outflow Forecast Box
        budget_box = ttk.LabelFrame(container, text="Net Cash Requirement Calculator for Custom Date Range", padding=12)
        budget_box.pack(fill=X, pady=(0, 15))

        f_inputs = ttk.Frame(budget_box)
        f_inputs.pack(fill=X, pady=(0, 8))

        today = datetime.date.today()
        default_start = today.strftime("%Y/%m/%d")
        default_end = (today + datetime.timedelta(days=90)).strftime("%Y/%m/%d")

        ttk.Label(f_inputs, text="Period Start:").pack(side=LEFT, padx=3)
        self.e_start = ttk.Entry(f_inputs, width=12)
        self.e_start.insert(0, default_start)
        self.e_start.pack(side=LEFT, padx=(0, 15))

        ttk.Label(f_inputs, text="Period End:").pack(side=LEFT, padx=3)
        self.e_end = ttk.Entry(f_inputs, width=12)
        self.e_end.insert(0, default_end)
        self.e_end.pack(side=LEFT, padx=(0, 15))

        ttk.Button(f_inputs, text="⚡ Calculate Net Cash Required", command=self.calculate_budget, bootstyle="success").pack(side=LEFT)

        # Result Cards
        res_frame = ttk.Frame(budget_box)
        res_frame.pack(fill=X)

        self.c_gross = ttk.Label(res_frame, text="Gross Cost:\nRs. 0.00", font=("Segoe UI", 10), justify=CENTER)
        self.c_gross.pack(side=LEFT, expand=True, fill=X, padx=5)

        self.c_paid = ttk.Label(res_frame, text="Already Paid Vouchers:\n- Rs. 0.00", font=("Segoe UI", 10), justify=CENTER)
        self.c_paid.pack(side=LEFT, expand=True, fill=X, padx=5)

        self.c_net = ttk.Label(res_frame, text="Actual Net Cash Required:\nRs. 0.00", font=("Segoe UI", 11, "bold"), bootstyle="inverse-success", justify=CENTER)
        self.c_net.pack(side=LEFT, expand=True, fill=X, padx=5)

        # 2. Record New Installment Bar
        rec_box = ttk.LabelFrame(container, text="Record New S/A Installment Payment", padding=10)
        rec_box.pack(fill=X, pady=(0, 10))

        rf = ttk.Frame(rec_box)
        rf.pack(fill=X)

        ttk.Label(rf, text="File NO:").grid(row=0, column=0, padx=4, pady=3, sticky=W)
        self.e_rec_file = ttk.Entry(rf, width=14)
        self.e_rec_file.grid(row=0, column=1, padx=4, pady=3)

        ttk.Label(rf, text="Year #:").grid(row=0, column=2, padx=4, pady=3, sticky=W)
        self.e_rec_year = ttk.Entry(rf, width=6)
        self.e_rec_year.insert(0, "1")
        self.e_rec_year.grid(row=0, column=3, padx=4, pady=3)

        ttk.Label(rf, text="Part #:").grid(row=0, column=4, padx=4, pady=3, sticky=W)
        self.e_rec_part = ttk.Entry(rf, width=6)
        self.e_rec_part.insert(0, "1")
        self.e_rec_part.grid(row=0, column=5, padx=4, pady=3)

        ttk.Label(rf, text="Amount (LKR):").grid(row=0, column=6, padx=4, pady=3, sticky=W)
        self.e_rec_amount = ttk.Entry(rf, width=12)
        self.e_rec_amount.grid(row=0, column=7, padx=4, pady=3)

        ttk.Label(rf, text="Voucher NO:").grid(row=1, column=0, padx=4, pady=3, sticky=W)
        self.e_rec_voucher = ttk.Entry(rf, width=14)
        self.e_rec_voucher.grid(row=1, column=1, padx=4, pady=3)

        ttk.Label(rf, text="Paid Date:").grid(row=1, column=2, padx=4, pady=3, sticky=W)
        self.e_rec_date = ttk.Entry(rf, width=12)
        self.e_rec_date.insert(0, default_start)
        self.e_rec_date.grid(row=1, column=3, columnspan=2, padx=4, pady=3, sticky=W)

        ttk.Button(rf, text="➕ Save Payment", command=self.save_payment, bootstyle="primary").grid(row=1, column=6, columnspan=2, padx=4, pady=3, sticky="ew")

        # 3. Payments Ledger Sheet
        sheet_box = ttk.Frame(container)
        sheet_box.pack(fill=BOTH, expand=True)

        self.sheet = Sheet(
            sheet_box,
            headers=PAYMENT_HEADERS,
            theme="dark blue",
            show_x_scrollbar=True,
            show_y_scrollbar=True
        )
        self.sheet.enable_bindings("single_select", "row_select", "column_width_resize", "copy")
        self.sheet.pack(fill=BOTH, expand=True)

    def load_payments(self):
        try:
            with db_connection() as conn:
                rows = conn.execute("SELECT * FROM sa_payments ORDER BY id DESC;").fetchall()
                data = [
                    [r["id"], r["file_no"], r["year_no"], r["installment_no"],
                     r["period_start"] or "-", r["period_end"] or "-",
                     f"{r['amount']:,.2f}", r["voucher_no"] or "-", r["paid_date"] or "-"]
                    for r in rows
                ]
                self.sheet.set_sheet_data(data)
        except Exception as e:
            log.error(f"Error loading payments: {e}")

    def save_payment(self):
        file_no = self.e_rec_file.get().strip()
        amt_str = self.e_rec_amount.get().strip().replace(",", "")
        if not file_no or not amt_str:
            messagebox.showwarning("Incomplete", "Please enter at least File NO and Amount.")
            return
        try:
            amt = float(amt_str)
            year = int(self.e_rec_year.get().strip() or "1")
            part = int(self.e_rec_part.get().strip() or "1")
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount and Year/Part must be numbers.")
            return

        with db_connection() as conn:
            conn.execute("""
            INSERT INTO sa_payments (file_no, year_no, installment_no, amount, voucher_no, paid_date)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (file_no, year, part, amt, self.e_rec_voucher.get().strip(), self.e_rec_date.get().strip()))

        messagebox.showinfo("Saved", "Payment recorded successfully!")
        self.e_rec_amount.delete(0, tk.END)
        self.e_rec_voucher.delete(0, tk.END)
        self.load_payments()

    def calculate_budget(self):
        s_date = self.e_start.get().strip()
        e_date = self.e_end.get().strip()
        if not s_date or not e_date:
            messagebox.showwarning("Input Needed", "Please specify inquiry start and end dates.")
            return

        gross = 0.0
        paid = 0.0

        with db_connection() as conn:
            # Sum up paid vouchers between these dates
            p_row = conn.execute("""
            SELECT SUM(amount) AS total_paid FROM sa_payments 
            WHERE paid_date >= ? AND paid_date <= ?;
            """, (s_date, e_date)).fetchone()
            if p_row and p_row["total_paid"]:
                paid = float(p_row["total_paid"])

            # Sum active contracts cost
            invs = conn.execute("""
            SELECT current_sa_costs_json FROM inventory 
            WHERE current_sa = 'Yes';
            """).fetchall()

            for r in invs:
                if r["current_sa_costs_json"]:
                    try:
                        c = json.loads(r["current_sa_costs_json"])
                        gross += float(c.get("y1", 0))
                    except Exception:
                        pass

        net = max(0.0, gross - paid)
        self.c_gross.config(text=f"Total Contractual Cost (Gross):\nRs. {gross:,.2f}")
        self.c_paid.config(text=f"Already Paid Vouchers:\n- Rs. {paid:,.2f}")
        self.c_net.config(text=f"Actual Net Cash Required:\nRs. {net:,.2f}")

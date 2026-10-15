# -*- coding: utf-8 -*-
"""
Module 2: S/A Contracts Hub Container
- Tab 1: 🟢 S/A Procurement Track Form & Pipeline (Stages 1-8, BEC, Signing)
- Tab 2: 🟡 Payment Ledger & Net Budget (Installment Vouchers & Balances)
(Note: Master 36-Column Equipment Matrix is now accessible via Card 4: Consolidated Inventory on the Landing Page)
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from sa_submodules.sa_procurement import SAProcurementView
from sa_submodules.sa_payments import SAPaymentsView

class SAContractsHubModule(ttk.Frame):
    def __init__(self, parent, show_profile_callback=None, on_back_to_asset=None):
        super().__init__(parent)
        self.show_profile_callback = show_profile_callback
        self.on_back_to_asset = on_back_to_asset

        # Top Information Banner clarifying module focus
        info_banner = ttk.Frame(self, bootstyle="secondary", padding=(10, 6))
        info_banner.pack(fill=X, padx=5, pady=(5, 2))
        ttk.Label(
            info_banner,
            text="📋 S/A Contracts Hub: Dedicated to Procurement Tracking & Payment Installments.",
            font=("Segoe UI", 9, "bold"),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT)
        ttk.Label(
            info_banner,
            text="(36-Column Matrix is at Landing Page Card 4: Consolidated Inventory • Expiry Alerts is at Landing Page Alert Board)",
            font=("Segoe UI", 8),
            bootstyle="inverse-secondary"
        ).pack(side=LEFT, padx=10)

        # Tabbed Notebook container
        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Tab 1: S/A Procurement Track Form & Pipeline (Emerald Green)
        tab1_frame = ttk.Frame(self.notebook)
        self.tab_proc = SAProcurementView(
            tab1_frame, 
            on_update_callback=self.on_data_updated,
            on_back_to_asset=self.on_back_to_asset
        )
        self.tab_proc.pack(fill=BOTH, expand=True)
        self.notebook.add(tab1_frame, text="  🟢 1. S/A Procurement Track Form & Pipeline  ")

        # Tab 2: Payment Ledger & Net Budget (Amber Gold)
        tab2_frame = ttk.Frame(self.notebook)
        self.tab_payments = SAPaymentsView(tab2_frame)
        self.tab_payments.pack(fill=BOTH, expand=True)
        self.notebook.add(tab2_frame, text="  🟡 2. Payment Ledger & Net Budget  ")

    def on_data_updated(self):
        """Called when procurement or status updates."""
        pass

    def jump_to_procurement(self, file_no=None):
        """Switch to Tab 1 (Procurement Track) and select the specified file_no."""
        self.notebook.select(0)
        if not file_no or not str(file_no).strip():
            self.tab_proc.clear_form()
            return
        file_no = str(file_no).strip()
        matched = False
        for i, val in enumerate(self.tab_proc.file_combo["values"]):
            if val.startswith(file_no):
                self.tab_proc.file_combo.current(i)
                self.tab_proc.on_file_selected()
                matched = True
                break
        if not matched:
            self.tab_proc.clear_form()

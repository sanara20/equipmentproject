# -*- coding: utf-8 -*-
"""
Module 1: Asset Master Registry
- File NO Dropdown with real-time auto-suggest & clean start (Point 1, 2, 7)
- ONLY QTY defaults to "1", all other fields start blank (Point 8)
- Removed "pro_3.py Master Layout" badge (Point 12)
- Clean Form Reset on Clear Form button (Point 8, 9)
- Dynamic 5-Year S/A Cost Section when Need S/A == 'Yes'
- Multi-Serial Location Mapping Modal Window when QTY > 1
- NEW FIELDS (Request 2): P/O Number & Order Date right after Local Agent and before Installed Date
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import datetime
import json
import logging
from autocomplete import AutocompleteCombobox, SearchSuggestPopup
from db_manager import (
    db_connection, DATE_FORMAT, get_dropdown_options, 
    add_master_list_value, get_all_file_numbers
)

log = logging.getLogger("thp_bme_asset_reg")

class AssetRegistryModule(ttk.Frame):
    def __init__(self, parent, on_save_callback=None, on_open_procurement=None):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.on_open_procurement = on_open_procurement
        self.unit_mappings = []
        self.loaded_file_no = None
        self.create_ui()
        self.refresh_all_dropdowns()
        # Start with completely blank form (except QTY=1)
        self.clear_form()

    def create_ui(self):
        # Action Buttons Bar pinned at bottom (Always visible, never cut off - Request 1)
        btn_bar = ttk.Frame(self, padding=(15, 10), bootstyle="dark")
        btn_bar.pack(side=BOTTOM, fill=X)

        ttk.Button(btn_bar, text="🔄 Refresh All Dropdowns", command=self.refresh_all_dropdowns, bootstyle="secondary-outline").pack(side=LEFT)
        ttk.Button(btn_bar, text="💾 Save / Update Record", command=self.save_record, bootstyle="success").pack(side=RIGHT, padx=5)
        ttk.Button(btn_bar, text="🧹 Clear Form", command=self.clear_form, bootstyle="secondary").pack(side=RIGHT, padx=5)
        ttk.Button(
            btn_bar,
            text="📋 S/A Contracts Hub ➔ Procurement Track Form",
            command=self.open_procurement_shortcut,
            bootstyle="info-outline"
        ).pack(side=RIGHT, padx=5)

        # Main Scrollable Container for all form fields (Request 1)
        self.container = ttk.ScrolledFrame(self, padding=(15, 10), autohide=True)
        self.container.pack(side=TOP, fill=BOTH, expand=True)

        # Header Bar
        header = ttk.Frame(self.container)
        header.pack(fill=X, pady=(0, 10))

        ttk.Label(header, text="Primary Equipment Registration Form (Master Asset Entry)", font=("Segoe UI", 13, "bold")).pack(side=LEFT)

        # Main Form Container Frame
        self.form_frame = ttk.LabelFrame(self.container, text="Equipment Specifications & Placement Details", padding=15)
        self.form_frame.pack(fill=X, pady=(0, 10))

        for col in range(4):
            self.form_frame.columnconfigure(col, weight=1)

        # -------------------------------------------------------------
        # Row 0: File NO & Equipment Name
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="File NO *:").grid(row=0, column=0, sticky=W, padx=6, pady=6)
        
        file_box = ttk.Frame(self.form_frame)
        file_box.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        
        self.c_file_no = AutocompleteCombobox(
            file_box,
            on_select_callback=lambda val: self.on_file_no_selected()
        )
        self.c_file_no.pack(side=LEFT, fill=X, expand=True)
        self.c_file_no.bind("<<ComboboxSelected>>", self.on_file_no_selected)
        self.c_file_no.bind("<Return>", self.on_file_no_selected)
        
        ttk.Button(file_box, text="➕ New", command=self.generate_new_file_no, bootstyle="info-outline", width=6).pack(side=RIGHT, padx=(4, 0))

        # Equipment Name (Combobox with real-time auto-suggest)
        ttk.Label(self.form_frame, text="Equipment Name *:").grid(row=0, column=2, sticky=W, padx=6, pady=6)
        self.c_name = AutocompleteCombobox(self.form_frame)
        self.c_name.grid(row=0, column=3, sticky="ew", padx=6, pady=6)

        # -------------------------------------------------------------
        # Row 1: Make & Model
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="Make / Brand:").grid(row=1, column=0, sticky=W, padx=6, pady=6)
        self.c_make = AutocompleteCombobox(self.form_frame)
        self.c_make.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(self.form_frame, text="Model:").grid(row=1, column=2, sticky=W, padx=6, pady=6)
        self.c_model = AutocompleteCombobox(self.form_frame)
        self.c_model.grid(row=1, column=3, sticky="ew", padx=6, pady=6)

        # -------------------------------------------------------------
        # Row 2: Quantity (QTY) & Serial Number(s)
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="Quantity (QTY):").grid(row=2, column=0, sticky=W, padx=6, pady=6)
        
        qty_box = ttk.Frame(self.form_frame)
        qty_box.grid(row=2, column=1, sticky="ew", padx=6, pady=6)
        
        self.e_qty = ttk.Entry(qty_box, width=8)
        self.e_qty.insert(0, "1")
        self.e_qty.pack(side=LEFT)
        self.e_qty.bind("<FocusOut>", self.on_qty_focus_out)
        self.e_qty.bind("<Return>", self.on_qty_focus_out)
        self.e_qty.bind("<KeyRelease>", lambda e: self.calc_total_cost())

        self.btn_edit_units = ttk.Button(qty_box, text="📍 Units Mapping", command=self.open_multi_location_popup, bootstyle="info-outline")
        # Hidden when QTY == 1

        ttk.Label(self.form_frame, text="Serial Number(s):").grid(row=2, column=2, sticky=W, padx=6, pady=6)
        self.e_serial = ttk.Entry(self.form_frame)
        self.e_serial.grid(row=2, column=3, sticky="ew", padx=6, pady=6)

        # -------------------------------------------------------------
        # Row 3: Location / Ward & Local Agent
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="Department / Location:").grid(row=3, column=0, sticky=W, padx=6, pady=6)
        self.c_location = AutocompleteCombobox(self.form_frame)
        self.c_location.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(self.form_frame, text="Local Agent:").grid(row=3, column=2, sticky=W, padx=6, pady=6)
        self.c_agent = AutocompleteCombobox(self.form_frame)
        self.c_agent.grid(row=3, column=3, sticky="ew", padx=6, pady=6)

        # -------------------------------------------------------------
        # Row 4: NEW FIELDS (Request 2) - P/O Number & Order Date
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="P/O Number:").grid(row=4, column=0, sticky=W, padx=6, pady=6)
        self.e_po_no = ttk.Entry(self.form_frame)
        self.e_po_no.grid(row=4, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(self.form_frame, text="Order Date (YYYY/MM/DD):").grid(row=4, column=2, sticky=W, padx=6, pady=6)
        self.e_order_date = ttk.Entry(self.form_frame)
        self.e_order_date.grid(row=4, column=3, sticky="ew", padx=6, pady=6)

        # -------------------------------------------------------------
        # Row 5: Installed Date & Warranty Period
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="Installed Date (YYYY/MM/DD):").grid(row=5, column=0, sticky=W, padx=6, pady=6)
        self.e_install_date = ttk.Entry(self.form_frame)
        self.e_install_date.grid(row=5, column=1, sticky="ew", padx=6, pady=6)
        self.e_install_date.bind("<KeyRelease>", self.calc_warranty_end)

        ttk.Label(self.form_frame, text="Warranty Period:").grid(row=5, column=2, sticky=W, padx=6, pady=6)
        self.c_warranty = ttk.Combobox(
            self.form_frame, 
            values=["1 Year", "2 Years", "3 Years", "4 Years", "5 Years", "Not Mentioned"]
        )
        self.c_warranty.grid(row=5, column=3, sticky="ew", padx=6, pady=6)
        self.c_warranty.bind("<<ComboboxSelected>>", self.on_warranty_selected)
        self.c_warranty.bind("<KeyRelease>", self.on_warranty_key_release)

        # -------------------------------------------------------------
        # Row 6: Warranty End Date & How Received
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="Warranty End Date:").grid(row=6, column=0, sticky=W, padx=6, pady=6)
        self.e_warranty_end = ttk.Entry(self.form_frame)
        self.e_warranty_end.grid(row=6, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(self.form_frame, text="How Received:").grid(row=6, column=2, sticky=W, padx=6, pady=6)
        how_box = ttk.Frame(self.form_frame)
        how_box.grid(row=6, column=3, sticky="ew", padx=6, pady=6)
        
        self.c_how_recv = AutocompleteCombobox(how_box)
        self.c_how_recv.pack(side=LEFT, fill=X, expand=True)
        self.c_how_recv.bind("<<ComboboxSelected>>", self.on_how_received_changed)
        self.c_how_recv.bind("<KeyRelease>", self.on_how_received_changed)

        self.e_how_recv_other = ttk.Entry(how_box, width=15)
        # Entry starts hidden until 'Other' is chosen

        # -------------------------------------------------------------
        # Row 7: Need S/A as P/O? & Remarks
        # -------------------------------------------------------------
        ttk.Label(self.form_frame, text="Need S/A as P/O *:").grid(row=7, column=0, sticky=W, padx=6, pady=6)
        need_sa_opts = get_dropdown_options("need_sa_po") or ["Yes", "No", "Ask Tech Unit", "Not Mentioned"]
        self.c_need_sa = ttk.Combobox(self.form_frame, values=need_sa_opts, state="readonly")
        self.c_need_sa.grid(row=7, column=1, sticky="ew", padx=6, pady=6)
        self.c_need_sa.bind("<<ComboboxSelected>>", self.toggle_sa_cost_section)

        ttk.Label(self.form_frame, text="Remarks:").grid(row=7, column=2, sticky=W, padx=6, pady=6)
        self.e_remarks = ttk.Entry(self.form_frame)
        self.e_remarks.grid(row=7, column=3, sticky="ew", padx=6, pady=6)

        # -------------------------------------------------------------
        # Dynamic 5-Year S/A Cost Section (Appears when Need S/A == 'Yes')
        # -------------------------------------------------------------
        self.sa_box = ttk.LabelFrame(self.container, text="📑 Service Agreement Details & 5-Year Cost Commitment (Need S/A = Yes)", padding=15, bootstyle="info")
        
        for col in range(4):
            self.sa_box.columnconfigure(col, weight=1)

        # Row 0: Current S/A in Force (Under Warranty / Yes / No)
        ttk.Label(self.sa_box, text="Current S/A in Force:").grid(row=0, column=0, sticky=W, padx=6, pady=4)
        self.c_curr_sa = ttk.Combobox(self.sa_box, values=["Under Warranty", "Yes", "No"], state="readonly")
        self.c_curr_sa.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self.c_curr_sa.bind("<<ComboboxSelected>>", self.toggle_curr_sa_details)

        # Sub-container for Active S/A Details (Visible ONLY if Current S/A is 'Yes')
        self.sa_active_details = ttk.Frame(self.sa_box)
        self.sa_active_details.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(2, 6))
        for col in range(4):
            self.sa_active_details.columnconfigure(col, weight=1)

        ttk.Label(self.sa_active_details, text="S/A Provider:").grid(row=0, column=0, sticky=W, padx=6, pady=4)
        self.c_sa_prov = AutocompleteCombobox(self.sa_active_details, completevalues=["THP", "In-House Tech", "Agent Direct", "Ministry"])
        self.c_sa_prov.grid(row=0, column=1, columnspan=3, sticky="ew", padx=6, pady=4)

        ttk.Label(self.sa_active_details, text="S/A Start Date (YYYY/MM/DD):").grid(row=1, column=0, sticky=W, padx=6, pady=4)
        self.e_sa_start = ttk.Entry(self.sa_active_details)
        self.e_sa_start.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(self.sa_active_details, text="S/A End Date / Valid Up To:").grid(row=1, column=2, sticky=W, padx=6, pady=4)
        self.e_sa_end = ttk.Entry(self.sa_active_details)
        self.e_sa_end.grid(row=1, column=3, sticky="ew", padx=6, pady=4)

        # Row 2: 5-Year Costs Header (Per Single Unit / Machine)
        cost_hdr = ttk.Label(self.sa_box, text="Annual Cost Breakdown per Single Unit / Machine (LKR):", font=("Segoe UI", 9, "bold"))
        cost_hdr.grid(row=2, column=0, columnspan=4, sticky=W, padx=6, pady=(8, 2))

        # Row 3: Year 1 to Year 5 Costs
        cf = ttk.Frame(self.sa_box)
        cf.grid(row=3, column=0, columnspan=4, sticky="ew", padx=6, pady=4)

        for i in range(5):
            cf.columnconfigure(i, weight=1)

        ttk.Label(cf, text="Year 1 (LKR):").grid(row=0, column=0, sticky=W)
        self.e_y1 = ttk.Entry(cf, width=12)
        self.e_y1.grid(row=1, column=0, sticky="ew", padx=3)
        self.e_y1.bind("<KeyRelease>", self.calc_total_cost)

        ttk.Label(cf, text="Year 2 (LKR):").grid(row=0, column=1, sticky=W)
        self.e_y2 = ttk.Entry(cf, width=12)
        self.e_y2.grid(row=1, column=1, sticky="ew", padx=3)
        self.e_y2.bind("<KeyRelease>", self.calc_total_cost)

        ttk.Label(cf, text="Year 3 (LKR):").grid(row=0, column=2, sticky=W)
        self.e_y3 = ttk.Entry(cf, width=12)
        self.e_y3.grid(row=1, column=2, sticky="ew", padx=3)
        self.e_y3.bind("<KeyRelease>", self.calc_total_cost)

        ttk.Label(cf, text="Year 4 (LKR):").grid(row=0, column=3, sticky=W)
        self.e_y4 = ttk.Entry(cf, width=12)
        self.e_y4.grid(row=1, column=3, sticky="ew", padx=3)
        self.e_y4.bind("<KeyRelease>", self.calc_total_cost)

        ttk.Label(cf, text="Year 5 (LKR):").grid(row=0, column=4, sticky=W)
        self.e_y5 = ttk.Entry(cf, width=12)
        self.e_y5.grid(row=1, column=4, sticky="ew", padx=3)
        self.e_y5.bind("<KeyRelease>", self.calc_total_cost)

        self.lbl_cost_total = ttk.Label(self.sa_box, text="Total 5-Year Cost: Rs. 0.00", font=("Segoe UI", 9, "bold"), bootstyle="success")
        self.lbl_cost_total.grid(row=4, column=0, columnspan=4, sticky=E, padx=6, pady=4)

    def on_how_received_changed(self, event=None):
        val = self.c_how_recv.get().strip().lower()
        if val == "other" or "other" in val or "වෙනත්" in val:
            if not self.e_how_recv_other.winfo_ismapped():
                self.e_how_recv_other.pack(side=LEFT, fill=X, expand=True, padx=(4, 0))
        else:
            if self.e_how_recv_other.winfo_ismapped():
                self.e_how_recv_other.pack_forget()

    def toggle_curr_sa_details(self, event=None):
        if self.c_curr_sa.get() == "Yes":
            self.sa_active_details.grid()
        else:
            self.sa_active_details.grid_remove()

    def refresh_all_dropdowns(self):
        """Populates file numbers and all comboboxes with real-time autocompletion."""
        file_numbers = get_all_file_numbers()
        self.c_file_no.set_completion_list(["+ [Generate New File NO]"] + file_numbers)
        
        self.c_name.set_completion_list(get_dropdown_options("equipment_name"))
        self.c_make.set_completion_list(get_dropdown_options("make"))
        self.c_model.set_completion_list(get_dropdown_options("model"))
        self.c_location.set_completion_list(get_dropdown_options("location"))
        self.c_agent.set_completion_list(get_dropdown_options("local_agent"))
        
        recv = get_dropdown_options("how_received") or ["THP Purchase", "Ministry Direct Supply", "Donation", "Internal Transfer"]
        if "Other" not in recv:
            recv.append("Other")
        self.c_how_recv.set_completion_list(recv)

        w_opts = get_dropdown_options("warranty_period") or ["1 Year", "2 Years", "3 Years", "4 Years", "5 Years", "Not Mentioned"]
        self.c_warranty.config(values=w_opts)

        need_sa_opts = get_dropdown_options("need_sa_po") or ["Yes", "No", "Ask Tech Unit", "Not Mentioned"]
        self.c_need_sa.config(values=need_sa_opts)

    def on_warranty_selected(self, event=None):
        self.calc_warranty_end()

    def on_warranty_key_release(self, event=None):
        if event and event.keysym in ("BackSpace", "Delete", "Escape", "Tab", "Return", "Left", "Right", "Up", "Down"):
            self.calc_warranty_end()
            return

        typed = self.c_warranty.get().strip().lower()
        mapping = {
            "1": "1 Year",
            "2": "2 Years",
            "3": "3 Years",
            "4": "4 Years",
            "5": "5 Years",
            "n": "Not Mentioned",
            "no": "Not Mentioned",
            "not": "Not Mentioned"
        }
        if typed in mapping:
            self.c_warranty.set(mapping[typed])
            self.c_warranty.icursor(tk.END)
        elif typed.startswith("1"): self.c_warranty.set("1 Year")
        elif typed.startswith("2"): self.c_warranty.set("2 Years")
        elif typed.startswith("3"): self.c_warranty.set("3 Years")
        elif typed.startswith("4"): self.c_warranty.set("4 Years")
        elif typed.startswith("5"): self.c_warranty.set("5 Years")
        elif typed.startswith("n"): self.c_warranty.set("Not Mentioned")

        self.calc_warranty_end()

    def generate_new_file_no(self):
        year = datetime.date.today().year
        try:
            with db_connection() as conn:
                r = conn.execute("SELECT COUNT(*) AS total FROM inventory;").fetchone()
                count = (r["total"] if r else 0) + 1
                new_fn = f"{year}/EQ/{count:02d}"
        except Exception:
            new_fn = f"{year}/EQ/01"

        self.c_file_no.set(new_fn)
        return new_fn

    def on_file_no_selected(self, event=None):
        val = self.c_file_no.get().strip()
        if not val:
            return
        if "+ [Generate New File NO]" in val:
            self.clear_form()
            self.generate_new_file_no()
            return

        file_no = val.split(" - ")[0].strip()
        if file_no:
            self.load_record_by_file_no(file_no)

    def on_qty_focus_out(self, event=None):
        try:
            qty = max(1, int(self.e_qty.get().strip() or "1"))
        except ValueError:
            qty = 1
            self.e_qty.delete(0, tk.END)
            self.e_qty.insert(0, "1")

        if qty > 1:
            self.btn_edit_units.config(text=f"📍 Units Mapping ({qty})")
            self.btn_edit_units.pack(side=LEFT, padx=6)
            if len(self.unit_mappings) != qty:
                self.open_multi_location_popup()
        else:
            self.btn_edit_units.pack_forget()
            self.unit_mappings = []

        self.calc_total_cost()

    def load_record_by_file_no(self, file_no):
        """Loads existing equipment record(s) into form for viewing/editing (Consolidates multi-unit rows)."""
        try:
            with db_connection() as conn:
                rows = conn.execute("SELECT * FROM inventory WHERE file_no = ? ORDER BY id ASC;", (file_no,)).fetchall()
            
            if not rows:
                # Historical file number without active inventory records yet
                self.clear_form()
                self.c_file_no.set(file_no)
                self.loaded_file_no = file_no
                return

            self.loaded_file_no = file_no
            inv = rows[0]
            total_qty = len(rows)

            self.c_file_no.set(inv["file_no"])
            self.c_name.set(inv["equipment_name"] or "")
            self.c_make.set(inv["make"] or "")
            self.c_model.set(inv["model"] or "")
            
            # QTY
            self.e_qty.delete(0, tk.END)
            self.e_qty.insert(0, str(total_qty))

            # Consolidate serials, locations and unit mappings
            self.unit_mappings = []
            serials = []
            locations = []
            for idx, r in enumerate(rows):
                sn = (r["serial_no"] or "").strip()
                loc = (r["location"] or "").strip()
                if sn: serials.append(sn)
                if loc and loc not in locations: locations.append(loc)
                self.unit_mappings.append({"serial": sn or f"Unit {idx+1}", "location": loc})

            self.e_serial.delete(0, tk.END)
            self.e_serial.insert(0, ", ".join(serials))
            self.c_location.set(", ".join(locations))
            self.c_agent.set(inv["local_agent"] or "")

            if total_qty > 1:
                self.btn_edit_units.config(text=f"📍 Units Mapping ({total_qty})")
                self.btn_edit_units.pack(side=LEFT, padx=6)
            else:
                self.btn_edit_units.pack_forget()

            # P/O Number & Order Date (Request 2)
            self.e_po_no.delete(0, tk.END)
            self.e_po_no.insert(0, inv["po_number"] or "")
            self.e_order_date.delete(0, tk.END)
            self.e_order_date.insert(0, inv["order_date"] or "")

            self.e_install_date.delete(0, tk.END)
            self.e_install_date.insert(0, inv["installed_date"] or "")
            self.c_warranty.set(inv["warranty_period"] or "")
            self.e_warranty_end.delete(0, tk.END)
            self.e_warranty_end.insert(0, inv["warranty_end_date"] or "")
            
            raw_how = inv["how_received"] or ""
            std_how = ["THP Purchase", "Ministry Direct Supply", "Donation", "Internal Transfer"]
            if raw_how in std_how:
                self.c_how_recv.set(raw_how)
                self.e_how_recv_other.pack_forget()
            elif raw_how:
                self.c_how_recv.set("Other")
                self.e_how_recv_other.delete(0, tk.END)
                self.e_how_recv_other.insert(0, raw_how)
                self.e_how_recv_other.pack(side=LEFT, fill=X, expand=True, padx=(4, 0))
            else:
                self.c_how_recv.set("")
                self.e_how_recv_other.pack_forget()

            self.c_need_sa.set(inv["need_sa_po"] or "")
            self.e_remarks.delete(0, tk.END)
            self.e_remarks.insert(0, inv["remarks"] or "")

            # S/A fields
            self.c_curr_sa.set(inv["current_sa"] or "No")
            self.c_sa_prov.set(inv["sa_provider"] or "")
            self.e_sa_start.delete(0, tk.END)
            self.e_sa_start.insert(0, inv["current_sa_start"] or "")
            self.e_sa_end.delete(0, tk.END)
            self.e_sa_end.insert(0, inv["sa_valid_upto"] or inv["current_sa_end"] or "")
            self.toggle_curr_sa_details()

            # Costs
            costs = {}
            if inv["current_sa_costs_json"]:
                try: costs = json.loads(inv["current_sa_costs_json"])
                except Exception: pass

            for entry, key in [(self.e_y1, "y1"), (self.e_y2, "y2"), (self.e_y3, "y3"), (self.e_y4, "y4"), (self.e_y5, "y5")]:
                entry.delete(0, tk.END)
                val = costs.get(key, 0)
                if val: entry.insert(0, str(val))

            self.calc_total_cost()
            self.toggle_sa_cost_section()
        except Exception as e:
            log.error(f"Error loading record: {e}")

    def is_warranty_still_active(self):
        w_end_str = self.e_warranty_end.get().strip()
        if not w_end_str or w_end_str in ("Not Known", "Not Mentioned", "None"):
            return False
        try:
            clean_date = w_end_str.replace('.', '/').replace('-', '/')
            w_date = datetime.datetime.strptime(clean_date, DATE_FORMAT).date()
            return w_date >= datetime.date.today()
        except Exception:
            return False

    def toggle_sa_cost_section(self, event=None):
        if self.c_need_sa.get() == "Yes":
            self.sa_box.pack(fill=X, pady=(0, 10))
            # Auto-select "Under Warranty" if warranty end date is not past and user hasn't explicitly set Yes/No
            curr = self.c_curr_sa.get().strip()
            if self.is_warranty_still_active():
                if curr not in ("Yes", "No"):
                    self.c_curr_sa.set("Under Warranty")
            elif not curr:
                self.c_curr_sa.set("No")
            self.toggle_curr_sa_details()
        else:
            self.sa_box.pack_forget()

    def calc_total_cost(self, event=None):
        unit_total = 0.0
        for e in [self.e_y1, self.e_y2, self.e_y3, self.e_y4, self.e_y5]:
            val = e.get().strip().replace(",", "")
            try:
                if val: unit_total += float(val)
            except ValueError: pass

        try:
            qty = max(1, int(self.e_qty.get().strip() or "1"))
        except ValueError:
            qty = 1

        grand_total = unit_total * qty

        if qty > 1:
            self.lbl_cost_total.config(
                text=f"Total 5-Year Cost Commitment (for all {qty} machines): Rs. {grand_total:,.2f}  [Rs. {unit_total:,.2f} / single machine]"
            )
        else:
            self.lbl_cost_total.config(text=f"Total 5-Year Cost Commitment: Rs. {grand_total:,.2f}")

    def calc_warranty_end(self, event=None):
        w_str = self.c_warranty.get().strip()
        if not w_str:
            return

        if "Not Mentioned" in w_str or "not" in w_str.lower() or "none" in w_str.lower():
            self.e_warranty_end.delete(0, tk.END)
            self.e_warranty_end.insert(0, "Not Known")
            if self.c_need_sa.get() == "Yes" and self.c_curr_sa.get() == "Under Warranty":
                self.c_curr_sa.set("No")
                self.toggle_curr_sa_details()
            return

        inst_str = self.e_install_date.get().strip().replace('.', '/').replace('-', '/')
        if not inst_str:
            return
        try:
            inst_date = datetime.datetime.strptime(inst_str, DATE_FORMAT).date()
            years = 0
            if "1 Year" in w_str: years = 1
            elif "2 Year" in w_str: years = 2
            elif "3 Year" in w_str: years = 3
            elif "4 Year" in w_str: years = 4
            elif "5 Year" in w_str: years = 5

            if years > 0:
                try:
                    anniversary = inst_date.replace(year=inst_date.year + years)
                except ValueError:
                    # Handle leap year Feb 29
                    anniversary = inst_date.replace(year=inst_date.year + years, day=28)
                # Exactly 1 day subtracted: (Installed Date + Warranty Period) - 1 Day
                end_date = anniversary - datetime.timedelta(days=1)
            else:
                end_date = inst_date

            self.e_warranty_end.delete(0, tk.END)
            self.e_warranty_end.insert(0, end_date.strftime("%Y/%m/%d"))

            # Auto-update S/A Under Warranty status if Need S/A is Yes
            if self.c_need_sa.get() == "Yes":
                if self.is_warranty_still_active():
                    if self.c_curr_sa.get() != "Yes":
                        self.c_curr_sa.set("Under Warranty")
                        self.toggle_curr_sa_details()
                elif self.c_curr_sa.get() == "Under Warranty":
                    self.c_curr_sa.set("No")
                    self.toggle_curr_sa_details()
        except Exception:
            pass

    def open_multi_location_popup(self):
        try: qty = max(1, int(self.e_qty.get().strip() or "1"))
        except ValueError: qty = 1

        if qty <= 1:
            return

        locations = get_dropdown_options("location")
        raw_serials = [s.strip() for s in self.e_serial.get().split(",") if s.strip()]
        curr_loc = self.c_location.get().strip()

        # Build units mapping to exact qty
        units = []
        for i in range(qty):
            if i < len(self.unit_mappings):
                u = self.unit_mappings[i]
                sn = u.get("serial", "") or (raw_serials[i] if i < len(raw_serials) else f"Unit {i+1}")
                loc = u.get("location", "") or curr_loc or (locations[0] if locations else "")
            else:
                sn = raw_serials[i] if i < len(raw_serials) else f"Unit {i+1}"
                loc = curr_loc or (locations[0] if locations else "")
            units.append({"serial": sn, "location": loc})

        popup = tk.Toplevel(self)
        popup.title(f"📍 Multi-Unit Mapping ({qty} Units)")
        popup.geometry("620x500")
        popup.minsize(540, 380)
        popup.grab_set()

        top_info = ttk.Frame(popup, padding=12, bootstyle="primary")
        top_info.pack(fill=X)
        ttk.Label(top_info, text="Assign Serial Numbers & Wards / Locations to Each Individual Unit", font=("Segoe UI", 10, "bold")).pack(anchor=W)
        ttk.Label(top_info, text=f"Total Units in this Batch: {qty} Nos", font=("Segoe UI", 8)).pack(anchor=W)

        batch_f = ttk.Frame(popup, padding=(12, 8))
        batch_f.pack(fill=X)
        ttk.Label(batch_f, text="Set All Wards to:").pack(side=LEFT, padx=4)
        c_batch = ttk.Combobox(batch_f, values=locations, width=24)
        c_batch.pack(side=LEFT, padx=4)
        if locations: c_batch.set(locations[0])

        rows_container = ttk.ScrolledFrame(popup, padding=12)
        rows_container.pack(fill=BOTH, expand=True)

        combos = []
        for i in range(qty):
            u = units[i]
            rf = ttk.Frame(rows_container)
            rf.pack(fill=X, pady=4)
            
            ttk.Label(rf, text=f"Unit {i+1}:", font=("Segoe UI", 9, "bold"), width=8).pack(side=LEFT)
            
            ttk.Label(rf, text="S/N:").pack(side=LEFT, padx=(4, 2))
            e_sn = ttk.Entry(rf, width=18)
            e_sn.insert(0, u["serial"])
            e_sn.pack(side=LEFT, padx=(0, 8))

            ttk.Label(rf, text="Location:").pack(side=LEFT, padx=(4, 2))
            cb_loc = AutocompleteCombobox(rf, completevalues=locations)
            cb_loc.set(u["location"])
            cb_loc.pack(side=LEFT, fill=X, expand=True, padx=(0, 4))

            combos.append((e_sn, cb_loc))

        def apply_batch():
            selected = c_batch.get().strip()
            if selected:
                for _, cb in combos: cb.set(selected)

        ttk.Button(batch_f, text="Apply to All", command=apply_batch, bootstyle="secondary").pack(side=LEFT, padx=4)

        def save_mapping():
            self.unit_mappings = []
            serials_collected = []
            locs_collected = []
            for e_sn, cb in combos:
                sn_val = e_sn.get().strip()
                loc_val = cb.get().strip()
                self.unit_mappings.append({"serial": sn_val, "location": loc_val})
                if sn_val: serials_collected.append(sn_val)
                if loc_val and loc_val not in locs_collected: locs_collected.append(loc_val)
                if loc_val:
                    for lp in [l.strip() for l in loc_val.replace("|", ",").split(",") if l.strip()]:
                        add_master_list_value("location", lp)

            self.e_serial.delete(0, tk.END)
            self.e_serial.insert(0, ", ".join(serials_collected))
            self.c_location.set(", ".join(locs_collected))
            
            self.btn_edit_units.config(text=f"📍 Units Mapping ({qty})")
            self.btn_edit_units.pack(side=LEFT, padx=6)
            popup.destroy()

        bot_f = ttk.Frame(popup, padding=10)
        bot_f.pack(fill=X)
        ttk.Button(bot_f, text="Cancel", command=popup.destroy, bootstyle="secondary").pack(side=RIGHT, padx=5)
        ttk.Button(bot_f, text="Apply Units Mapping", command=save_mapping, bootstyle="success").pack(side=RIGHT, padx=5)

    def clear_form(self):
        """Resets all fields completely blank, ONLY QTY resets to '1'."""
        self.c_file_no.set("")
        self.loaded_file_no = None
        self.unit_mappings = []

        for c in [self.c_name, self.c_make, self.c_model, self.c_agent, self.c_location, 
                  self.e_po_no, self.e_order_date,
                  self.e_serial, self.e_install_date, self.c_warranty, self.e_warranty_end,
                  self.c_how_recv, self.c_need_sa, self.e_remarks, self.c_curr_sa,
                  self.c_sa_prov, self.e_sa_start, self.e_sa_end, self.e_y1, self.e_y2, self.e_y3, self.e_y4, self.e_y5]:
            if isinstance(c, (ttk.Combobox, AutocompleteCombobox)): c.set("")
            elif isinstance(c, (ttk.Entry, tk.Entry)): c.delete(0, tk.END)
        
        self.e_how_recv_other.delete(0, tk.END)
        self.e_how_recv_other.pack_forget()

        # Only QTY is set to 1
        self.e_qty.delete(0, tk.END)
        self.e_qty.insert(0, "1")
        self.btn_edit_units.pack_forget()
        self.sa_box.pack_forget()
        self.toggle_curr_sa_details()
        self.lbl_cost_total.config(text="Total 5-Year Cost Commitment: Rs. 0.00")

    def save_record(self):
        val = self.c_file_no.get().strip()
        file_no = val.split(" - ")[0].strip()
        name = self.c_name.get().strip()
        if not file_no or not name:
            messagebox.showwarning("Missing Information", "File NO and Equipment Name are required.")
            return

        try: qty = max(1, int(self.e_qty.get().strip() or "1"))
        except ValueError: qty = 1

        make_v = self.c_make.get().strip()
        model_v = self.c_model.get().strip()
        agent_v = self.c_agent.get().strip()
        po_no_v = self.e_po_no.get().strip()
        order_date_v = self.e_order_date.get().strip()
        loc_v = self.c_location.get().strip()
        
        how_v = self.c_how_recv.get().strip()
        if how_v.lower() == "other" or "other" in how_v.lower() or "වෙනත්" in how_v:
            other_text = self.e_how_recv_other.get().strip()
            if other_text:
                how_v = other_text
                add_master_list_value("how_received", other_text)

        need_sa_v = self.c_need_sa.get().strip()
        curr_sa_v = self.c_curr_sa.get().strip() if need_sa_v == "Yes" else "No"
        sa_prov_v = self.c_sa_prov.get().strip() if (need_sa_v == "Yes" and curr_sa_v == "Yes") else ""
        sa_start_v = self.e_sa_start.get().strip() if (need_sa_v == "Yes" and curr_sa_v == "Yes") else ""
        sa_end_v = self.e_sa_end.get().strip() if (need_sa_v == "Yes" and curr_sa_v == "Yes") else ""

        def parse_f(e):
            try: return float(e.get().strip().replace(",", "") or 0)
            except ValueError: return 0.0

        y1, y2, y3, y4, y5 = parse_f(self.e_y1), parse_f(self.e_y2), parse_f(self.e_y3), parse_f(self.e_y4), parse_f(self.e_y5)
        unit_5yr_total = y1 + y2 + y3 + y4 + y5
        grand_5yr_total = unit_5yr_total * qty
        costs_json = json.dumps({
            "y1": y1, "y2": y2, "y3": y3, "y4": y4, "y5": y5,
            "unit_5yr_total": unit_5yr_total,
            "grand_5yr_total": grand_5yr_total,
            "qty": qty
        })

        # Ensure unit_mappings has exact qty elements
        raw_serials = [s.strip() for s in self.e_serial.get().split(",") if s.strip()]
        if len(self.unit_mappings) != qty:
            new_units = []
            for i in range(qty):
                if i < len(self.unit_mappings):
                    new_units.append(self.unit_mappings[i])
                else:
                    sn = raw_serials[i] if i < len(raw_serials) else (raw_serials[0] if (len(raw_serials) == 1 and qty == 1) else f"Unit {i+1}")
                    new_units.append({"serial": sn, "location": loc_v})
            self.unit_mappings = new_units

        try:
            with db_connection() as conn:
                existing_rows = conn.execute("SELECT id FROM inventory WHERE file_no = ? ORDER BY id ASC;", (file_no,)).fetchall()
                existing_ids = [r["id"] for r in existing_rows]

                # Update or Insert individual rows per unit
                for idx, u in enumerate(self.unit_mappings):
                    u_sn = (u.get("serial") or "").strip()
                    u_loc = (u.get("location") or loc_v).strip()
                    
                    if idx < len(existing_ids):
                        # In-place UPDATE keeps exact row ID & position stable!
                        conn.execute("""
                        UPDATE inventory SET
                            equipment_name = ?, make = ?, model = ?, qty = 1, serial_no = ?,
                            location = ?, local_agent = ?, po_number = ?, order_date = ?,
                            installed_date = ?, warranty_period = ?, warranty_end_date = ?,
                            need_sa_po = ?, how_received = ?, current_sa = ?, sa_provider = ?,
                            sa_valid_upto = ?, current_sa_start = ?, current_sa_end = ?,
                            current_sa_costs_json = ?, year_1_cost = ?, year_2_cost = ?,
                            year_3_cost = ?, year_4_cost = ?, year_5_cost = ?, remarks = ?
                        WHERE id = ?;
                        """, (
                            name, make_v, model_v, u_sn,
                            u_loc, agent_v, po_no_v, order_date_v, self.e_install_date.get().strip(),
                            self.c_warranty.get().strip(), self.e_warranty_end.get().strip(),
                            need_sa_v, how_v, curr_sa_v, sa_prov_v, sa_end_v, sa_start_v, sa_end_v,
                            costs_json, y1, y2, y3, y4, y5, self.e_remarks.get().strip(),
                            existing_ids[idx]
                        ))
                    else:
                        # INSERT new unit row
                        conn.execute("""
                        INSERT INTO inventory (
                            file_no, equipment_name, make, model, qty, serial_no, location, local_agent,
                            po_number, order_date,
                            installed_date, warranty_period, warranty_end_date, need_sa_po, how_received,
                            current_sa, sa_provider, sa_valid_upto, current_sa_start, current_sa_end,
                            current_sa_costs_json, year_1_cost, year_2_cost, year_3_cost, year_4_cost, year_5_cost, remarks
                        ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """, (
                            file_no, name, make_v, model_v, u_sn,
                            u_loc, agent_v, po_no_v, order_date_v, self.e_install_date.get().strip(),
                            self.c_warranty.get().strip(), self.e_warranty_end.get().strip(),
                            need_sa_v, how_v, curr_sa_v, sa_prov_v, sa_end_v, sa_start_v, sa_end_v,
                            costs_json, y1, y2, y3, y4, y5, self.e_remarks.get().strip()
                        ))

                # Remove excess rows if quantity was decreased
                if len(existing_ids) > qty:
                    excess_ids = existing_ids[qty:]
                    ph = ",".join("?" * len(excess_ids))
                    conn.execute(f"DELETE FROM inventory WHERE id IN ({ph});", excess_ids)

            # Remember dropdown values (including file_no so it stays in dropdown!)
            add_master_list_value("file_no", file_no)
            add_master_list_value("equipment_name", name)
            add_master_list_value("make", make_v)
            add_master_list_value("model", model_v)
            
            # Save all locations (including multi-locations) into master dropdowns
            if loc_v:
                for lp in [l.strip() for l in loc_v.replace("|", ",").split(",") if l.strip()]:
                    add_master_list_value("location", lp)
            for u in self.unit_mappings:
                u_loc = (u.get("location") or "").strip()
                if u_loc:
                    for lp in [l.strip() for l in u_loc.replace("|", ",").split(",") if l.strip()]:
                        add_master_list_value("location", lp)

            add_master_list_value("local_agent", agent_v)
            add_master_list_value("how_received", how_v)
            if sa_prov_v:
                add_master_list_value("sa_provider", sa_prov_v)
            warranty_v = self.c_warranty.get().strip()
            if warranty_v:
                add_master_list_value("warranty_period", warranty_v)

            messagebox.showinfo("Saved", f"Equipment record {file_no} ({qty} unit(s)) saved successfully!")
            self.refresh_all_dropdowns()
            self.c_file_no.set(f"{file_no} - {name}")
            self.loaded_file_no = file_no

            if self.on_save_callback:
                self.on_save_callback()
        except Exception as e:
            log.error(f"Save error: {e}")
            messagebox.showerror("Save Error", str(e))

    def delete_current_file_record(self):
        val = self.c_file_no.get().strip()
        file_no = val.split(" - ")[0].strip()
        if not file_no:
            messagebox.showwarning("No File NO", "Please select a File NO from the dropdown to delete.")
            return

        with db_connection() as conn:
            cnt = conn.execute("SELECT COUNT(*) AS total FROM inventory WHERE file_no = ?;", (file_no,)).fetchone()["total"]

        if cnt == 0:
            messagebox.showinfo("No Records", f"No active equipment units found in inventory for File NO '{file_no}'.")
            return

        msg = (
            f"Are you sure you want to permanently delete all records for:\n"
            f"File NO: {file_no} ({cnt} unit(s))\n\n"
            f"This will permanently delete:\n"
            f"• All {cnt} equipment unit row(s) in Inventory\n"
            f"• Associated S/A Procurement Track records\n"
            f"• S/A Payments & Installments records\n"
            f"• S/A Concluded History logs\n"
            f"• Associated Repairs & Breakdown Job Cards\n\n"
            f"Note: The File NO will remain saved in master dropdowns for future use.\n"
            f"Do you want to proceed?"
        )
        if messagebox.askyesno("⚠️ Confirm Permanent Deletion", msg):
            try:
                with db_connection() as conn:
                    conn.execute("DELETE FROM inventory WHERE file_no = ?;", (file_no,))
                    conn.execute("DELETE FROM sa_procurement_track WHERE file_no = ?;", (file_no,))
                    conn.execute("DELETE FROM sa_payments WHERE file_no = ?;", (file_no,))
                    conn.execute("DELETE FROM sa_history WHERE file_no = ?;", (file_no,))
                    conn.execute("DELETE FROM repairs WHERE file_no = ?;", (file_no,))
                messagebox.showinfo("Deleted", f"All records for File NO '{file_no}' were deleted successfully.")
                self.clear_form()
                self.refresh_all_dropdowns()
                if self.on_save_callback:
                    self.on_save_callback()
            except Exception as e:
                log.error(f"Deletion error: {e}")
                messagebox.showerror("Error", f"Failed to delete records: {e}")

    def open_procurement_shortcut(self):
        file_val = self.file_no_entry.get().strip() if hasattr(self, 'file_no_entry') else ""
        if hasattr(self, 'on_open_procurement') and self.on_open_procurement:
            self.on_open_procurement(file_val)
        else:
            top = self.winfo_toplevel()
            if hasattr(top, 'open_module'):
                top.open_module("sa")
                if hasattr(top, 'current_sa_hub') and top.current_sa_hub:
                    top.current_sa_hub.jump_to_procurement(file_val)


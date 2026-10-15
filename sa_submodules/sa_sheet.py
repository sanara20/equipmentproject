# -*- coding: utf-8 -*-
"""
S/A Contracts Hub - Submodule 1: 36-Column Inventory Master Sheet
- Save Quick Edit functionality (Point 10)
- Hidden row index numbers (Point 11.i)
- Narrow ID column width (Point 11.ii)
- Multi-line text wrapping & auto-height (Point 11.iii)
- 2-line wrapped column headers (Point 11.iv)
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pandas as pd
import json
import logging
import textwrap
from db_manager import db_connection, DATE_FORMAT, get_setting, parse_file_no_sort_key
from print_helper import print_document

log = logging.getLogger("thp_bme_sa_sheet")

def wrap_cell_text(text, width=22):
    """
    Wraps text strictly at space (whole-word) boundaries.
    Never splits any word in the middle!
    """
    if not text:
        return ""
    text_s = str(text).strip()
    if len(text_s) <= width:
        return text_s

    words = text_s.split()
    lines = []
    current_line = []
    current_len = 0

    for word in words:
        word_len = len(word)
        if current_line and (current_len + 1 + word_len > width):
            lines.append(" ".join(current_line))
            current_line = [word]
            current_len = word_len
        else:
            current_line.append(word)
            current_len += (1 if current_len > 0 else 0) + word_len

    if current_line:
        lines.append(" ".join(current_line))

    return "\n".join(lines)

INVENTORY_SELECT = """
SELECT 
    i.id, i.file_no, i.equipment_name, i.make, i.model, i.qty, i.serial_no, i.location, i.local_agent,
    COALESCE(i.po_number, '') AS po_number,
    COALESCE(i.order_date, '') AS order_date,
    i.installed_date, i.warranty_period, i.warranty_end_date, i.need_sa_po, i.how_received,
    i.current_sa, i.sa_provider, i.sa_valid_upto,
    COALESCE(i.current_sa_start, p.sa_start_date, '') AS curr_start,
    COALESCE(i.current_sa_end, p.sa_end_date, '') AS curr_end,
    COALESCE(i.current_sa_costs_json, p.annual_cost_json, '') AS curr_costs_json,
    COALESCE(i.year_1_cost, 0) AS y1_direct,
    COALESCE(i.year_2_cost, 0) AS y2_direct,
    COALESCE(i.year_3_cost, 0) AS y3_direct,
    COALESCE(i.year_4_cost, 0) AS y4_direct,
    COALESCE(i.year_5_cost, 0) AS y5_direct,
    COALESCE(p.sa_process_type, '') AS next_sa_type,
    (CASE 
        WHEN p.inv_holder_sent_date IS NOT NULL AND TRIM(p.inv_holder_sent_date) != '' 
        THEN 'Sent: ' || TRIM(p.inv_holder_sent_date) 
        ELSE '' 
     END || 
     CASE 
        WHEN p.inv_holder_recv_date IS NOT NULL AND TRIM(p.inv_holder_recv_date) != '' 
        THEN (CASE WHEN p.inv_holder_sent_date IS NOT NULL AND TRIM(p.inv_holder_sent_date) != '' THEN ' | ' ELSE '' END) || 'Recv: ' || TRIM(p.inv_holder_recv_date) 
        ELSE '' 
     END || 
     CASE 
        WHEN p.inv_holder_status IS NOT NULL AND TRIM(p.inv_holder_status) != '' 
        THEN ' (' || TRIM(p.inv_holder_status) || ')' 
        ELSE '' 
     END) AS next_inv_holder_log,
    COALESCE(p.doc_send_date, '') AS next_doc_send,
    (COALESCE(p.reminder_1_date, '') || 
     CASE WHEN p.reminder_2_date IS NOT NULL AND p.reminder_2_date != '' THEN ', ' || p.reminder_2_date ELSE '' END || 
     CASE WHEN p.reminder_3_date IS NOT NULL AND p.reminder_3_date != '' THEN ', ' || p.reminder_3_date ELSE '' END) AS next_reminders_log,
    (CASE 
        WHEN p.bec_rec_recv_date IS NOT NULL AND p.bec_rec_recv_date != '' 
        THEN 'Recv: ' || p.bec_rec_recv_date || CASE WHEN p.bec_recommendation IS NOT NULL AND p.bec_recommendation != '' THEN ' (' || p.bec_recommendation || ')' ELSE '' END
        WHEN p.bec_sub_date IS NOT NULL AND p.bec_sub_date != '' 
        THEN 'Sub: ' || p.bec_sub_date 
        ELSE '' 
     END) AS next_bec_log,
    (CASE
        WHEN (p.p_red_1_date IS NULL OR p.p_red_1_date = '') AND (p.p_red_1_status IS NULL OR p.p_red_1_status = '') THEN ''
        ELSE COALESCE(p.p_red_1_date, '') || ' (' || COALESCE(p.p_red_1_status, '') || ')'
     END) AS next_pred_log,
    COALESCE(p.final_signed_date, '') AS next_signed_date,
    COALESCE(p.sa_start_date, '') AS next_start_date,
    COALESCE(p.sa_end_date, '') AS next_end_date,
    COALESCE(p.process_status, '') AS next_proc_status,
    (SELECT GROUP_CONCAT(h.sa_provider || ' [' || h.sa_start_date || '-' || h.sa_end_date || ']', ' | ') 
     FROM sa_history h WHERE LOWER(h.file_no) = LOWER(i.file_no)) AS past_sa_history,
    i.remarks
FROM inventory i
LEFT JOIN sa_procurement_track p ON i.file_no = p.file_no
ORDER BY i.id ASC;
"""

# Point 11.iv: 2-Line Wrapped Column Headers strictly matching Data Entry Form field labels
HEADERS_2LINE = [
    "ID", "File\nNO", "Equipment\nName", "Make", "Model", "QTY", "Serial\nNumber(s)",
    "Location", "Local\nAgent", "P/O\nNumber", "Order\nDate", "Installed\nDate", "Warranty\nPeriod", "Warranty\nEnd Date",
    "Need S/A\nas P/O", "How\nReceived", "Current S/A\nin Force", "S/A\nProvider", "S/A Valid\nUp To",
    "Current S/A\nStart Date", "Current S/A\nEnd Date", "Year 1 Cost\n(LKR)", "Year 2 Cost\n(LKR)",
    "Year 3 Cost\n(LKR)", "Year 4 Cost\n(LKR)", "Year 5 Cost\n(LKR)", "S/A Process\nType",
    "Inv. Holder\nConsent Log", "Doc Request\nDate", "Reminders\nLog", "BEC Rec.\nLog", "Price Neg.\nStatus",
    "Final Signed\nDate", "New S/A\nStart Date", "New S/A\nEnd Date", "Overall Proc.\nStatus",
    "Past S/A\nHistory", "Remarks"
]

HEADERS_RAW = [
    "ID", "File NO", "Equipment Name", "Make", "Model", "QTY", "Serial Number(s)",
    "Location", "Local Agent", "P/O Number", "Order Date", "Installed Date", "Warranty Period", "Warranty End Date",
    "Need S/A as P/O", "How Received", "Current S/A in Force", "S/A Provider", "S/A Valid Up To",
    "Current S/A Start Date", "Current S/A End Date", "Year 1 Cost (LKR)", "Year 2 Cost (LKR)",
    "Year 3 Cost (LKR)", "Year 4 Cost (LKR)", "Year 5 Cost (LKR)", "S/A Process Type",
    "Inv. Holder Consent Log", "Doc Request Date", "Reminders Log", "BEC Rec. Log", "Price Neg. Status",
    "Final Signed Date", "New S/A Start Date", "New S/A End Date", "Overall Proc. Status",
    "Past S/A History", "Remarks"
]

# Column Widths strictly justified like pro_3.py (Request 1)
# File NO (col 1) is set to 165px
COL_WIDTHS = [
    42,   # 0: ID
    165,  # 1: File NO (Snug, 165px)
    195,  # 2: Equipment Name (Roomy, 195px)
    105,  # 3: Make
    105,  # 4: Model
    55,   # 5: QTY
    125,  # 6: Serial Number(s)
    135,  # 7: Location
    135,  # 8: Local Agent
    100,  # 9: P/O Number
    95,   # 10: Order Date
    95,   # 11: Installed Date
    95,   # 12: Warranty Period
    100,  # 13: Warranty End Date
    90,   # 14: Need S/A as P/O
    100,  # 15: How Received
    110,  # 16: Current S/A in Force
    95,   # 17: S/A Provider
    100,  # 18: S/A Valid Up To
    105,  # 19: Current S/A Start Date
    105,  # 20: Current S/A End Date
    105,  # 21: Year 1 Cost (LKR)
    105,  # 22: Year 2 Cost (LKR)
    105,  # 23: Year 3 Cost (LKR)
    105,  # 24: Year 4 Cost (LKR)
    105,  # 25: Year 5 Cost (LKR)
    135,  # 26: S/A Process Type
    135,  # 27: Inv. Holder Consent Log
    100,  # 28: Doc Request Date
    105,  # 29: Reminders Log
    110,  # 30: BEC Rec. Log
    105,  # 31: Price Neg. Status
    110,  # 32: Final Signed Date
    100,  # 33: New S/A Start Date
    100,  # 34: New S/A End Date
    115,  # 35: Overall Proc. Status
    145,  # 36: Past S/A History
    150   # 37: Remarks
]

class SASheetView(ttk.Frame):
    def __init__(self, parent, show_profile_callback=None):
        super().__init__(parent)
        self.show_profile_callback = show_profile_callback
        self.full_data = []
        self.displayed_data = []
        self.sheet = None
        self.tree = None
        
        self.create_ui()
        self.load_data()

    def create_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="Filter Records:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        if hasattr(self.search_var, "trace_add"):
            self.search_var.trace_add("write", lambda *args: self.filter_data())
        else:
            self.search_var.trace("w", lambda *args: self.filter_data())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=28)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_data())
        search_entry.pack(side=LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="🔄 Reset Filters", command=self.reset_filters, bootstyle="secondary-outline").pack(side=LEFT, padx=3)
        
        # Point 10: Save Quick Edit Button
        ttk.Button(toolbar, text="💾 Save Quick Edit", command=self.save_quick_edit, bootstyle="warning").pack(side=LEFT, padx=8)

        ttk.Button(toolbar, text="🖨️ Print Report", command=self.open_print_dialog, bootstyle="info").pack(side=RIGHT, padx=3)
        ttk.Button(toolbar, text="📥 Export to Excel", command=self.export_excel, bootstyle="success").pack(side=RIGHT, padx=3)
        ttk.Button(toolbar, text="👁️ View 360° Profile", command=self.view_selected_profile, bootstyle="info-outline").pack(side=RIGHT, padx=3)

        self.count_label = ttk.Label(toolbar, text="Loading records...", font=("Segoe UI", 9))
        self.count_label.pack(side=RIGHT, padx=15)

        # Sheet Container
        self.sheet_frame = ttk.Frame(self)
        self.sheet_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        try:
            from tksheet import Sheet
            self.sheet = Sheet(
                self.sheet_frame,
                headers=HEADERS_2LINE,
                header_height=48,
                theme="dark blue",
                show_x_scrollbar=True,
                show_y_scrollbar=True,
                # Point 11.i: Hide Row Index (numbers column on far left)
                show_row_index=False,
                empty_horizontal=0,
                empty_vertical=0
            )
            try:
                self.sheet.header_height(48)
            except Exception:
                pass
            try:
                self.sheet.set_header_height(48)
            except Exception:
                pass
            # Enable interactive bindings: Double-Click opens 360° Profile, Shift+Double-Click edits cell
            self.sheet.enable_bindings(
                "single_select", "row_select", "column_width_resize",
                "arrowkeys", "right_click_popup_menu", "copy", "select_all",
                "double_click_column_resize"
            )
            try:
                self.sheet.bind("<Double-Button-1>", self.on_sheet_double_click)
                self.sheet.bind("<Shift-Double-Button-1>", self.on_sheet_shift_double_click)
            except Exception as e:
                log.warning(f"Error binding sheet events: {e}")
            # Apply justified column widths like pro_3.py (Request 1)
            self.apply_column_widths()
            self.sheet.pack(fill=BOTH, expand=True)
        except Exception as e:
            log.warning(f"tksheet not available or error: {e}. Falling back to standard Treeview.")
            self.setup_fallback_tree()

    def apply_column_widths(self):
        """Applies snug, justified column widths and adjusts row heights based on text lines."""
        if self.sheet:
            try:
                self.sheet.header_height(48)
            except Exception:
                pass
            try:
                self.sheet.set_header_height(48)
            except Exception:
                pass

            # Load custom column widths if set in Admin & Settings
            custom_widths_raw = get_setting("sheet_column_widths")
            custom_widths = {}
            if custom_widths_raw:
                try: custom_widths = json.loads(custom_widths_raw)
                except Exception: pass

            for idx, w in enumerate(COL_WIDTHS):
                actual_w = custom_widths.get(str(idx), w)
                try:
                    self.sheet.column_width(idx, width=actual_w)
                except Exception:
                    pass

            # Dynamic row height based on text line count so rows expand vertically
            for r_idx, row in enumerate(self.displayed_data):
                max_lines = max((str(cell).count('\n') + 1 for cell in row), default=1)
                if max_lines <= 1:
                    row_h = 30
                elif max_lines == 2:
                    row_h = 46
                elif max_lines == 3:
                    row_h = 62
                else:
                    row_h = min(120, max_lines * 19 + 8)

                try:
                    self.sheet.row_height(row=r_idx, height=row_h)
                except Exception:
                    pass

    def on_sheet_double_click(self, event=None):
        """Standard Double-Click: Safely opens 360° Profile popup without modifying cells!"""
        if event and (event.state & 0x0001):
            self.on_sheet_shift_double_click(event)
            return
        self.view_selected_profile()

    def on_sheet_shift_double_click(self, event=None):
        """Shift + Double-Click: Enables in-cell editing for Quick Edit!"""
        if self.sheet:
            try:
                self.sheet.enable_bindings("edit_cell")
            except Exception:
                pass

    def open_print_dialog(self):
        """Opens Smart Field Selector Popup with Quick Presets & Checkboxes for custom report printing."""
        modal = tk.Toplevel(self)
        modal.title("🖨️ Print Report - Select Columns")
        modal.geometry("560x540")
        modal.minsize(500, 460)
        modal.grab_set()

        hdr = ttk.Frame(modal, padding=12, bootstyle="primary")
        hdr.pack(fill=X)
        ttk.Label(hdr, text="🖨️ Print Equipment Report - Select Columns", font=("Segoe UI", 11, "bold"), bootstyle="inverse-primary").pack(anchor=W)
        ttk.Label(hdr, text=f"Currently Filtered: {len(self.displayed_data)} Records will be printed", font=("Segoe UI", 9), bootstyle="inverse-primary").pack(anchor=W)

        # Quick Presets
        preset_box = ttk.LabelFrame(modal, text="Quick Presets (එක් Click එකකින් තෝරාගැනීම)", padding=10)
        preset_box.pack(fill=X, padx=15, pady=(10, 5))

        btn_p_row = ttk.Frame(preset_box)
        btn_p_row.pack(fill=X)

        p_vars = {}
        for idx, col_name in enumerate(HEADERS_RAW):
            p_vars[idx] = tk.BooleanVar(value=(idx in [1, 2, 3, 4, 5, 7])) # default basic specs

        def set_preset(indices):
            for i, v in p_vars.items():
                v.set(i in indices)
            update_fit_indicator()

        ttk.Button(btn_p_row, text="📋 Basic Specs (6)", command=lambda: set_preset([1, 2, 3, 4, 5, 7]), bootstyle="info-outline").pack(side=LEFT, padx=2, expand=True, fill=X)
        ttk.Button(btn_p_row, text="🛡️ S/A Contracts (7)", command=lambda: set_preset([1, 2, 7, 16, 17, 18, 21]), bootstyle="primary-outline").pack(side=LEFT, padx=2, expand=True, fill=X)
        ttk.Button(btn_p_row, text="⏳ Warranty & Pipeline (6)", command=lambda: set_preset([1, 2, 11, 13, 14, 26]), bootstyle="warning-outline").pack(side=LEFT, padx=2, expand=True, fill=X)
        ttk.Button(btn_p_row, text="✅ All", command=lambda: set_preset(list(p_vars.keys())), bootstyle="secondary-outline").pack(side=LEFT, padx=2)
        ttk.Button(btn_p_row, text="❌ Clear", command=lambda: set_preset([]), bootstyle="secondary-outline").pack(side=LEFT, padx=2)

        # Checkboxes inside a scrollable frame
        chk_box = ttk.LabelFrame(modal, text="Custom Column Checkboxes (අවශ්‍ය තීරු පමණක් Tick කරන්න)", padding=10)
        chk_box.pack(fill=BOTH, expand=True, padx=15, pady=5)

        chk_scroll = ttk.ScrolledFrame(chk_box)
        chk_scroll.pack(fill=BOTH, expand=True)

        for idx, col_name in enumerate(HEADERS_RAW):
            cb = ttk.Checkbutton(chk_scroll, text=f"{col_name}", variable=p_vars[idx], command=lambda: update_fit_indicator())
            cb.grid(row=idx // 2, column=idx % 2, sticky=W, padx=10, pady=3)

        # Live Fit Indicator
        fit_lbl = ttk.Label(modal, text="Selected: 6 columns (A4 Landscape පිටුවට ඉතා හොඳින් ගැලපේ ✅)", font=("Segoe UI", 9, "bold"), bootstyle="success")
        fit_lbl.pack(pady=4)

        def update_fit_indicator():
            selected = [i for i, v in p_vars.items() if v.get()]
            cnt = len(selected)
            if cnt == 0:
                fit_lbl.config(text="Please select at least 1 column to print ⚠️", bootstyle="danger")
            elif cnt <= 8:
                fit_lbl.config(text=f"Selected: {cnt} columns (A4 Landscape පිටුවට ඉතා හොඳින් ගැලපේ ✅)", bootstyle="success")
            elif cnt <= 12:
                fit_lbl.config(text=f"Selected: {cnt} columns (A4 Landscape පිටුවට ගැලපේ - අකුරු මඳක් කුඩා විය හැක ℹ️)", bootstyle="info")
            else:
                fit_lbl.config(text=f"Selected: {cnt} columns (Columns වැඩි බැවින් අකුරු කුඩා වේ ⚠️)", bootstyle="warning")

        # Action Buttons
        act_row = ttk.Frame(modal, padding=(15, 10))
        act_row.pack(fill=X)

        def do_print():
            selected = [i for i, v in p_vars.items() if v.get()]
            if not selected:
                messagebox.showwarning("No Columns", "Please select at least one column to print.")
                return

            import html
            modal.destroy()

            # Build HTML table
            th_cells = "".join(f"<th>{html.escape(HEADERS_RAW[i])}</th>" for i in selected)
            rows_html = ""
            for row in self.displayed_data:
                td_cells = ""
                for i in selected:
                    val = str(row[i]).replace('\n', ' ') if i < len(row) else ""
                    td_cells += f"<td>{html.escape(val)}</td>"
                rows_html += f"<tr>{td_cells}</tr>\n"

            table_html = f"""
            <table class="print-table">
              <thead><tr>{th_cells}</tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
            """
            title = f"Equipment Inventory Report ({len(self.displayed_data)} Records)"
            print_document(title=title, content_html=table_html, is_landscape=True)

        ttk.Button(act_row, text="🖨️ Print / Preview", command=do_print, bootstyle="success", width=18).pack(side=RIGHT, padx=4)
        ttk.Button(act_row, text="Cancel", command=modal.destroy, bootstyle="secondary").pack(side=RIGHT, padx=4)

    def setup_fallback_tree(self):
        scroll_y = ttk.Scrollbar(self.sheet_frame, orient=VERTICAL)
        scroll_x = ttk.Scrollbar(self.sheet_frame, orient=HORIZONTAL)
        
        self.tree = ttk.Treeview(
            self.sheet_frame,
            columns=HEADERS_RAW,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)
        self.tree.pack(fill=BOTH, expand=True)

        for i, (h, w) in enumerate(zip(HEADERS_RAW, COL_WIDTHS)):
            self.tree.heading(h, text=h)
            self.tree.column(h, width=w, minwidth=max(40, w - 20))

    def load_data(self):
        try:
            with db_connection() as conn:
                rows = conn.execute(INVENTORY_SELECT).fetchall()
                
            self.full_data = []
            for r in rows:
                costs_json = r["curr_costs_json"] or "{}"
                try: costs = json.loads(costs_json)
                except Exception: costs = {}

                y1 = costs.get('y1', r["y1_direct"])
                y2 = costs.get('y2', r["y2_direct"])
                y3 = costs.get('y3', r["y3_direct"])
                y4 = costs.get('y4', r["y4_direct"])
                y5 = costs.get('y5', r["y5_direct"])

                row_values = [
                    r["id"],
                    r["file_no"],  # File NO is kept clean & unwrapped, fitting its dedicated width
                    wrap_cell_text(r["equipment_name"], 24),
                    wrap_cell_text(r["make"] or "", 12),
                    wrap_cell_text(r["model"] or "", 12),
                    r["qty"] or 1,
                    wrap_cell_text(r["serial_no"] or "", 16),
                    wrap_cell_text(r["location"] or "", 20),
                    wrap_cell_text(r["local_agent"] or "", 18),
                    r["po_number"] or "",
                    r["order_date"] or "",
                    r["installed_date"] or "",
                    r["warranty_period"] or "",
                    r["warranty_end_date"] or "",
                    r["need_sa_po"] or "Yes",
                    r["how_received"] or "",
                    r["current_sa"] or "No",
                    r["sa_provider"] or "",
                    r["sa_valid_upto"] or "",
                    r["curr_start"] or "",
                    r["curr_end"] or "",
                    f"{float(y1):,.2f}" if y1 else "",
                    f"{float(y2):,.2f}" if y2 else "",
                    f"{float(y3):,.2f}" if y3 else "",
                    f"{float(y4):,.2f}" if y4 else "",
                    f"{float(y5):,.2f}" if y5 else "",
                    r["next_sa_type"] or "",
                    wrap_cell_text(r["next_inv_holder_log"] or "", 18),
                    r["next_doc_send"] or "",
                    wrap_cell_text(r["next_reminders_log"] or "", 16),
                    wrap_cell_text(r["next_bec_log"] or "", 16),
                    r["next_pred_log"] or "",
                    r["next_signed_date"] or "",
                    r["next_start_date"] or "",
                    r["next_end_date"] or "",
                    r["next_proc_status"] or "",
                    wrap_cell_text(r["past_sa_history"] or "", 20),
                    wrap_cell_text(r["remarks"] or "", 22)
                ]
                self.full_data.append(row_values)

            # Naturally sort records by Year then sequence number
            self.full_data.sort(key=lambda r: parse_file_no_sort_key(r[1]))
            self.displayed_data = [list(r) for r in self.full_data]
            self.render_grid()
            self.count_label.config(text=f"Total Records: {len(self.displayed_data)}")
        except Exception as e:
            log.error(f"Error loading sheet data: {e}")
            self.count_label.config(text="Database empty or error loading.")

    def render_grid(self):
        if self.sheet:
            self.sheet.set_sheet_data(self.displayed_data)
            # Apply snug justified column widths like pro_3.py (Request 1)
            self.apply_column_widths()
            try:
                self.sheet.redraw()
                self.update_idletasks()
            except Exception:
                pass
        elif self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)
            for row in self.displayed_data:
                self.tree.insert("", END, values=row)

    def filter_data(self):
        query = self.search_var.get().strip().lower()
        if not query:
            self.displayed_data = [list(r) for r in self.full_data]
        else:
            self.displayed_data = [
                list(row) for row in self.full_data
                if any(query in str(cell).lower() for cell in row)
            ]
        self.render_grid()
        self.count_label.config(text=f"Filtered: {len(self.displayed_data)} / {len(self.full_data)}")

    def reset_filters(self):
        self.search_var.set("")
        self.displayed_data = [list(r) for r in self.full_data]
        self.render_grid()
        self.count_label.config(text=f"Total Records: {len(self.displayed_data)}")
        if self.sheet:
            self.apply_column_widths()
            try:
                self.after(30, self.sheet.redraw)
                self.after(60, self.apply_column_widths)
            except Exception:
                pass

    # -------------------------------------------------------------
    # Point 10: Save Quick Edit
    # -------------------------------------------------------------
    def save_quick_edit(self):
        """Saves any edits made directly in sheet cells back to database."""
        if not self.sheet:
            messagebox.showinfo("Quick Edit", "Direct sheet editing is active in table mode.")
            return

        current_data = self.sheet.get_sheet_data()
        if not current_data:
            return

        saved_count = 0
        try:
            with db_connection() as conn:
                for row in current_data:
                    if not row or len(row) < 3:
                        continue
                    db_id = row[0]
                    file_no = str(row[1]).strip()
                    name = str(row[2]).replace('\n', ' ').strip()
                    make = str(row[3]).strip()
                    model = str(row[4]).strip()
                    try: qty = int(row[5])
                    except Exception: qty = 1
                    serials = str(row[6]).strip()
                    location = str(row[7]).replace('\n', ' ').strip()
                    agent = str(row[8]).replace('\n', ' ').strip()
                    po_no = str(row[9]).strip()
                    order_date = str(row[10]).strip()
                    inst_date = str(row[11]).strip()
                    w_period = str(row[12]).strip()
                    w_end = str(row[13]).strip()
                    need_sa = str(row[14]).strip()
                    how_recv = str(row[15]).strip()
                    curr_sa = str(row[16]).strip()
                    sa_prov = str(row[17]).strip()
                    sa_valid = str(row[18]).strip()
                    remarks = str(row[37]).replace('\n', ' ').strip() if len(row) > 37 else ""

                    conn.execute("""
                    UPDATE inventory SET
                        equipment_name = ?, make = ?, model = ?, qty = ?,
                        serial_no = ?, location = ?, local_agent = ?,
                        po_number = ?, order_date = ?,
                        installed_date = ?, warranty_period = ?, warranty_end_date = ?,
                        need_sa_po = ?, how_received = ?, current_sa = ?,
                        sa_provider = ?, sa_valid_upto = ?, remarks = ?
                    WHERE id = ? OR file_no = ?;
                    """, (
                        name, make, model, qty, serials, location, agent,
                        po_no, order_date,
                        inst_date, w_period, w_end, need_sa, how_recv, curr_sa,
                        sa_prov, sa_valid, remarks, db_id, file_no
                    ))
                    saved_count += 1

            messagebox.showinfo("Success", f"✔ Quick Edit Saved! {saved_count} records successfully updated in database.")
            self.load_data()
        except Exception as e:
            log.error(f"Error in quick edit save: {e}")
            messagebox.showerror("Save Error", f"Could not save quick edits:\n{e}")

    def view_selected_profile(self):
        file_no = None
        if self.sheet:
            selected = self.sheet.get_currently_selected()
            if selected and selected.row is not None and 0 <= selected.row < len(self.displayed_data):
                file_no = self.displayed_data[selected.row][1]
        elif self.tree:
            sel = self.tree.selection()
            if sel:
                item = self.tree.item(sel[0])
                file_no = item["values"][1]

        if file_no and self.show_profile_callback:
            self.show_profile_callback(file_no)
        else:
            messagebox.showinfo("Select Record", "Please click on a row first.")

    def export_excel(self):
        if not self.displayed_data:
            messagebox.showwarning("Export", "No data to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="Export 36-Column S/A Inventory Sheet"
        )
        if not path:
            return
        try:
            df = pd.DataFrame(self.displayed_data, columns=HEADERS_RAW)
            df.to_excel(path, index=False)
            messagebox.showinfo("Export Successful", f"Excel sheet exported successfully:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

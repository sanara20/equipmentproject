# -*- coding: utf-8 -*-
"""
Medical Equipment Maintenance Management System - Teaching Hospital Peradeniya v1.0
High-Performance Search-As-You-Type Autocomplete & Floating Suggestion Popup
"""

import tkinter as tk
import ttkbootstrap as ttk

class SearchSuggestPopup:
    """
    Attaches a floating, real-time dropdown suggestion listbox to any Tkinter/ttk Entry or Combobox.
    Filters on every keystroke (letter or number) and closes automatically on selection or blur.
    """
    def __init__(self, entry_widget, get_candidates_func, on_select_callback=None, max_display=12):
        self.entry = entry_widget
        self.get_candidates_func = get_candidates_func
        self.on_select_callback = on_select_callback
        self.max_display = max_display
        self.popup = None
        self.listbox = None

        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>", self._on_down_key)
        self.entry.bind("<Escape>", lambda e: self.hide())

    def _on_key_release(self, event):
        # Ignore navigation keys
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return

        typed = self.entry.get().strip().lower()
        if not typed:
            self.hide()
            return

        all_items = self.get_candidates_func()
        matches = [item for item in all_items if typed in str(item).lower()]

        if not matches:
            self.hide()
            return

        self.show(matches[:self.max_display])

    def _on_down_key(self, event):
        if self.popup and self.listbox and self.listbox.size() > 0:
            self.listbox.focus_set()
            self.listbox.selection_set(0)
            return "break"

    def show(self, items):
        if not self.popup:
            self.popup = tk.Toplevel(self.entry)
            self.popup.wm_overrideredirect(True)
            self.popup.attributes("-topmost", True)

            frame = tk.Frame(self.popup, bg="#0284c7", bd=1)
            frame.pack(fill=tk.BOTH, expand=True)

            self.listbox = tk.Listbox(
                frame,
                font=("Segoe UI", 9),
                bg="#1e293b",
                fg="#f8fafc",
                selectbackground="#0284c7",
                selectforeground="#ffffff",
                relief=tk.FLAT,
                highlightthickness=0,
                activestyle="none"
            )
            scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
            self.listbox.config(yscrollcommand=scrollbar.set)

            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.listbox.bind("<ButtonRelease-1>", self._on_select)
            self.listbox.bind("<Return>", self._on_select)
            self.listbox.bind("<Escape>", lambda e: self.hide())

        self.listbox.delete(0, tk.END)
        for it in items:
            self.listbox.insert(tk.END, str(it))

        # Position precisely beneath entry
        self.entry.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = max(self.entry.winfo_width(), 260)
        h = min(len(items) * 24 + 6, 250)

        self.popup.geometry(f"{w}x{h}+{x}+{y}")
        self.popup.deiconify()

    def hide(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.listbox = None

    def _on_select(self, event=None):
        if not self.listbox:
            return
        sel = self.listbox.curselection()
        if sel:
            selected_text = self.listbox.get(sel[0])
            self.entry.delete(0, tk.END)
            self.entry.insert(0, selected_text)
            self.hide()
            self.entry.focus_set()
            if self.on_select_callback:
                self.on_select_callback(selected_text)
            try:
                self.entry.event_generate("<<ComboboxSelected>>")
            except Exception:
                pass

    def _on_focus_out(self, event):
        # Delay hiding so listbox click registers
        self.entry.after(200, self._check_focus_and_hide)

    def _check_focus_and_hide(self):
        try:
            focused = self.entry.focus_get()
            if focused != self.listbox and focused != self.entry:
                self.hide()
        except Exception:
            self.hide()


class AutocompleteCombobox(ttk.Combobox):
    """
    Combobox with integrated search-as-you-type floating suggestion popup.
    """
    def __init__(self, master=None, completevalues=None, on_select_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self._all_values = completevalues or []
        self['values'] = self._all_values
        self.on_select_callback = on_select_callback

        self.suggester = SearchSuggestPopup(
            self,
            get_candidates_func=lambda: self._all_values,
            on_select_callback=self._handle_selection
        )
        self.bind("<<ComboboxSelected>>", lambda e: self._handle_selection(self.get()))

    def set_completion_list(self, values):
        clean_list = []
        seen = set()
        for v in values:
            s = str(v).strip()
            if s and s not in seen:
                seen.add(s)
                clean_list.append(s)
        self._all_values = clean_list
        self['values'] = self._all_values

    def _handle_selection(self, val):
        if self.on_select_callback:
            self.on_select_callback(val)

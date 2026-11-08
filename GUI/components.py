import customtkinter as ctk
from typing import List, Tuple

class ResultsTable(ctk.CTkScrollableFrame):
    """
    A scrollable table widget with clickable, selectable, read-only cells
    so users can copy text without modifying data.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#242424", corner_radius=6, **kwargs)
        
        self.grid_columnconfigure(0, weight=2)  # GitHub Username
        self.grid_columnconfigure(1, weight=1)  # Commits
        self.grid_columnconfigure(2, weight=3)  # GitHub Link
        
        self._row_widgets: List[ctk.CTkBaseClass] = []
        self._build_headers()

    def _build_headers(self) -> None:
        headers = ["GitHub Username", "Commits", "GitHub Link"]
        for col, text in enumerate(headers):
            lbl = ctk.CTkLabel(
                self, 
                text=text, 
                font=("Segoe UI", 13, "bold"), 
                text_color="#DCE4EE",
                fg_color="#1F6AA5",
                corner_radius=4
            )
            lbl.grid(row=0, column=col, padx=3, pady=(0, 6), sticky="ew")

    def clear(self) -> None:
        """Removes all existing data rows while keeping the headers."""
        for widget in self._row_widgets:
            widget.destroy()
        self._row_widgets.clear()

    def populate(self, rows: List[Tuple[str, str, str]]) -> None:
        """Populates the table with (username, commits, link) tuples."""
        self.clear()
        
        for row_idx, (username, commits, link) in enumerate(rows, start=1):
            is_error = commits == "PROBLEM WITH ACCOUNT"
            text_color = "#CF6679" if is_error else "#DCE4EE"
            
            values = [username, commits, link]
            for col_idx, val in enumerate(values):
                cell = ctk.CTkEntry(
                    self,
                    font=("Segoe UI", 12, "normal"),
                    text_color=text_color,
                    fg_color="#2B2B2B",
                    border_width=1,
                    border_color="#3A3A3A",
                    corner_radius=4
                )
                cell.insert(0, val)
                # Allow clicking, highlighting, and Ctrl+C/Ctrl+A while blocking edits
                cell.bind("<Key>", self._readonly_key_handler)
                cell.grid(row=row_idx, column=col_idx, padx=3, pady=2, sticky="ew")
                self._row_widgets.append(cell)

    @staticmethod
    def _readonly_key_handler(event):
        """Permits clipboard copy, select-all, and navigation keys; blocks text edits."""
        allowed_keys = {"c", "C", "a", "A"}
        navigation_keys = {"Left", "Right", "Up", "Down", "Home", "End"}
        
        # Allow Ctrl+C and Ctrl+A (state & 4 checks the Control modifier on Windows)
        if (event.state & 4) and event.keysym in allowed_keys:
            return None
        if event.keysym in navigation_keys:
            return None
        return "break"
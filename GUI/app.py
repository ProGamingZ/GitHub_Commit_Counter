import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import asyncio
import aiohttp
import os
from typing import List, Tuple

from security import auth_manager
from core.parser import parse_markdown_file
from core.github_api import fetch_commit_count
from core.output_writer import write_results, read_results_file
from db.cache import get_cached_commits, save_to_cache
from models.schemas import ProcessingResult, Status
from gui.components import ResultsTable

# Force dark mode per design guidelines
ctk.set_appearance_mode("Dark")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Root Window Setup (Expanded for Split-Screen Architecture)
        self.title("GitHub Commit Tracker")
        self.geometry("1200x680")
        self.resizable(False, False)
        self.configure(fg_color="#242424")
        
        # 50/50 Horizontal Split Configuration
        self.grid_columnconfigure(0, weight=1, uniform="split")
        self.grid_columnconfigure(1, weight=1, uniform="split")
        self.grid_rowconfigure(0, weight=1)
        
        # State Variables
        self.input_file_path = ctk.StringVar(value="No file selected")
        self.output_folder_path = ctk.StringVar(value="No folder selected")
        self.save_token_var = ctk.BooleanVar(value=True)
        self.table_date_range_var = ctk.StringVar(value="Start Date: —   |   End Date: —")

        self._build_ui()
        self._load_initial_auth()

    def _build_ui(self):
        # =========================================================
        # LEFT PANE: User Inputs, Execution Controls & Status Log
        # =========================================================
        self.left_pane = ctk.CTkFrame(self, fg_color="transparent")
        self.left_pane.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.left_pane.grid_columnconfigure(0, weight=1)
        self.left_pane.grid_rowconfigure(2, weight=1)

        # --- Auth Section (Top Left) ---
        self.auth_frame = ctk.CTkFrame(self.left_pane, fg_color="#2B2B2B", corner_radius=10)
        self.auth_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        self.auth_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.auth_frame, text="GitHub PAT:", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.token_entry = ctk.CTkEntry(self.auth_frame, show="*", placeholder_text="ghp_xxxxxxxxxxxx", corner_radius=6)
        self.token_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.save_token_cb = ctk.CTkCheckBox(self.auth_frame, text="Save Token", variable=self.save_token_var)
        self.save_token_cb.grid(row=0, column=2, padx=10, pady=10)

        # --- Configuration Section (Middle Left) ---
        self.config_frame = ctk.CTkFrame(self.left_pane, fg_color="#2B2B2B", corner_radius=10)
        self.config_frame.grid(row=1, column=0, pady=10, sticky="ew")
        self.config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.config_frame, text="Start Date:", font=("Segoe UI", 13, "normal")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.start_date_entry = ctk.CTkEntry(self.config_frame, placeholder_text="YYYY-MM-DD", corner_radius=6)
        self.start_date_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.config_frame, text="End Date:", font=("Segoe UI", 13, "normal")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.end_date_entry = ctk.CTkEntry(self.config_frame, placeholder_text="YYYY-MM-DD", corner_radius=6)
        self.end_date_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.file_btn = ctk.CTkButton(self.config_frame, text="Select Input File (.md)", fg_color="transparent", border_width=1, corner_radius=6, command=self._select_file)
        self.file_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.file_label = ctk.CTkLabel(self.config_frame, textvariable=self.input_file_path, text_color="#DCE4EE", anchor="w")
        self.file_label.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.folder_btn = ctk.CTkButton(self.config_frame, text="Select Output Folder", fg_color="transparent", border_width=1, corner_radius=6, command=self._select_folder)
        self.folder_btn.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.folder_label = ctk.CTkLabel(self.config_frame, textvariable=self.output_folder_path, text_color="#DCE4EE", anchor="w")
        self.folder_label.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        # --- Execution & Status Section (Bottom Left) ---
        self.exec_frame = ctk.CTkFrame(self.left_pane, fg_color="#2B2B2B", corner_radius=10)
        self.exec_frame.grid(row=2, column=0, pady=(10, 0), sticky="nsew")
        self.exec_frame.grid_columnconfigure(0, weight=1)
        self.exec_frame.grid_rowconfigure(2, weight=1)

        self.execute_btn = ctk.CTkButton(self.exec_frame, text="Process", fg_color="#1F6AA5", hover_color="#144870", corner_radius=6, command=self._start_execution)
        self.execute_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.exec_frame, progress_color="#1F6AA5")
        self.progress_bar.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        self.status_log = ctk.CTkTextbox(self.exec_frame, font=("Consolas", 12, "normal"), fg_color="#242424")
        self.status_log.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # =========================================================
        # RIGHT PANE: Date Header, Results Loader & Data Table
        # =========================================================
        self.right_pane = ctk.CTkFrame(self, fg_color="#2B2B2B", corner_radius=10)
        self.right_pane.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.right_pane.grid_columnconfigure(0, weight=1)
        self.right_pane.grid_rowconfigure(2, weight=1)

        # --- Top Bar: Load Results Button & Title ---
        self.table_top_frame = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        self.table_top_frame.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        self.table_top_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.table_top_frame, 
            text="Results Overview", 
            font=("Segoe UI", 18, "bold"), 
            text_color="#DCE4EE"
        ).grid(row=0, column=0, sticky="w")

        self.load_results_btn = ctk.CTkButton(
            self.table_top_frame, 
            text="Load Results File (.txt)", 
            fg_color="transparent", 
            border_width=1, 
            corner_radius=6,
            command=self._load_results_from_dialog
        )
        self.load_results_btn.grid(row=0, column=1, sticky="e")

        # --- Date Range Banner Above Table ---
        self.date_banner = ctk.CTkLabel(
            self.right_pane,
            textvariable=self.table_date_range_var,
            font=("Segoe UI", 13, "bold"),
            text_color="#DCE4EE",
            fg_color="#242424",
            corner_radius=6,
            height=34
        )
        self.date_banner.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        # --- Copyable Read-Only Results Table ---
        self.results_table = ResultsTable(self.right_pane)
        self.results_table.grid(row=2, column=0, padx=15, pady=(5, 15), sticky="nsew")

    def _load_initial_auth(self):
        """Queries OS keyring on launch."""
        token = auth_manager.get_token()
        if token:
            self.token_entry.insert(0, token)

    def _select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md")])
        if path:
            self.input_file_path.set(path)

    def _select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.output_folder_path.set(path)

    def _load_results_from_dialog(self):
        """Allows user to pick an existing results.txt file and populates the table."""
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not path:
            return
            
        try:
            start_date, end_date, rows = read_results_file(path)
            
            # Fallback to current entry fields if file predates filename date tagging
            if start_date == "N/A" and self.start_date_entry.get().strip():
                start_date = self.start_date_entry.get().strip()
            if end_date == "N/A" and self.end_date_entry.get().strip():
                end_date = self.end_date_entry.get().strip()
                
            self._update_table_ui(start_date, end_date, rows)
            self._log(f"Loaded {len(rows)} records from {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error Loading File", f"Could not parse results file:\n{str(e)}")

    def _update_table_ui(self, start_date: str, end_date: str, rows: List[Tuple[str, str, str]]):
        """Updates the date header and populates the table on the main UI thread."""
        self.table_date_range_var.set(f"Start Date: {start_date}   |   End Date: {end_date}")
        self.results_table.populate(rows)

    def _log(self, message: str):
        """Thread-safe UI log update that auto-scrolls to the bottom."""
        self.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.status_log.insert("end", message + "\n")
        self.status_log.see("end")

    def _start_execution(self):
        """Validates inputs, disables UI, and spawns background thread."""
        token = self.token_entry.get().strip()
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        in_file = self.input_file_path.get()
        out_folder = self.output_folder_path.get()

        if not all([token, start_date, end_date]) or in_file == "No file selected" or out_folder == "No folder selected":
            messagebox.showerror("Error", "All fields, input file, and output folder must be selected.")
            return

        if self.save_token_var.get():
            auth_manager.save_token(token)
        else:
            auth_manager.delete_token()

        # Disable UI components during execution
        self.execute_btn.configure(state="disabled", fg_color="gray")
        self.file_btn.configure(state="disabled")
        self.folder_btn.configure(state="disabled")
        self.load_results_btn.configure(state="disabled")
        self.status_log.delete("1.0", "end")
        self.progress_bar.set(0)

        # Thread Handoff
        threading.Thread(
            target=self._run_async_loop, 
            args=(token, start_date, end_date, in_file, out_folder), 
            daemon=True
        ).start()

    def _run_async_loop(self, token, start_date, end_date, in_file, out_folder):
        """Creates a new event loop for the background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_batch(token, start_date, end_date, in_file, out_folder))
        finally:
            loop.close()

    async def _process_batch(self, token, start_date, end_date, in_file, out_folder):
        masked_token = f"{token[:4]}...{token[-4:]}" if len(token) >= 8 else "****"
        self._log(f"Authenticated with Token: {masked_token}")
        
        self._log(f"Reading and deduplicating {os.path.basename(in_file)}...")
        records = parse_markdown_file(in_file)
        
        if not records:
            self._log("No valid GitHub users found or file format error.")
            self.after(0, self._enable_ui)
            return

        total_users = len(records)
        self._log(f"Found {total_users} unique users. Starting batch API requests...\n")
        
        results: List[ProcessingResult] = []
        completed = 0

        async with aiohttp.ClientSession() as session:
            for record in records:
                cached_count = get_cached_commits(record.username, start_date, end_date)
                
                if cached_count is not None:
                    self._log(f"[CACHE HIT] {record.username}: {cached_count} commits")
                    results.append(ProcessingResult(
                        username=record.username,
                        commit_count=cached_count,
                        profile_url=record.profile_url,
                        status=Status.SUCCESS
                    ))
                else:
                    self._log(f"[API CALL] Fetching {record.username}...")
                    res = await fetch_commit_count(session, record.username, start_date, end_date, token)
                    results.append(res)
                    
                    if res.status == Status.SUCCESS:
                        self._log(f" -> Success: {res.commit_count} commits")
                        save_to_cache(record.username, start_date, end_date, res.commit_count)
                    else:
                        self._log(f" -> Failed: {res.status.name} | {res.error_detail}")
                    
                    await asyncio.sleep(1)

                completed += 1
                self.after(0, self.progress_bar.set, completed / total_users)

        # Output Generation
        self._log("\nWriting results to disk...")
        saved_file_path = write_results(results, out_folder, start_date, end_date)
        
        # Prepare rows and populate the Right-Side Table automatically
        table_rows: List[Tuple[str, str, str]] = [
            (
                r.username, 
                str(r.commit_count) if r.status == Status.SUCCESS else "PROBLEM WITH ACCOUNT", 
                r.profile_url
            )
            for r in results
        ]
        self.after(0, self._update_table_ui, start_date, end_date, table_rows)
        
        self._log("Batch complete!")
        self.after(0, self._enable_ui)
        self.after(0, lambda: messagebox.showinfo("Success", f"File saved to:\n{saved_file_path}"))

    def _enable_ui(self):
        self.execute_btn.configure(state="normal", fg_color="#1F6AA5")
        self.file_btn.configure(state="normal")
        self.folder_btn.configure(state="normal")
        self.load_results_btn.configure(state="normal")
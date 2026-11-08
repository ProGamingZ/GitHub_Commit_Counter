import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import asyncio
import aiohttp
import os

from security import auth_manager
from core.parser import parse_markdown_file
from core.github_api import fetch_commit_count
from core.output_writer import write_results
from db.cache import get_cached_commits, save_to_cache
from models.schemas import ProcessingResult, Status

# Force dark mode per design guidelines
ctk.set_appearance_mode("Dark")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Root Window Setup
        self.title("GitHub Commit Tracker")
        self.geometry("800x650")
        self.resizable(False, False)
        self.configure(fg_color="#242424")
        
        # Variables
        self.input_file_path = ctk.StringVar()
        self.output_folder_path = ctk.StringVar()
        self.save_token_var = ctk.BooleanVar(value=True)

        self._build_ui()
        self._load_initial_auth()

    def _build_ui(self):
        # --- Auth Section (Top) ---
        self.auth_frame = ctk.CTkFrame(self, fg_color="#2B2B2B", corner_radius=10)
        self.auth_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.auth_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.auth_frame, text="GitHub PAT:", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.token_entry = ctk.CTkEntry(self.auth_frame, show="*", placeholder_text="ghp_xxxxxxxxxxxx", corner_radius=6)
        self.token_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.save_token_cb = ctk.CTkCheckBox(self.auth_frame, text="Save Token", variable=self.save_token_var)
        self.save_token_cb.grid(row=0, column=2, padx=10, pady=10)

        # --- Configuration Section (Middle) ---
        self.config_frame = ctk.CTkFrame(self, fg_color="#2B2B2B", corner_radius=10)
        self.config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.config_frame, text="Start Date:", font=("Segoe UI", 13, "normal")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.start_date_entry = ctk.CTkEntry(self.config_frame, placeholder_text="YYYY-MM-DD", corner_radius=6)
        self.start_date_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.config_frame, text="End Date:", font=("Segoe UI", 13, "normal")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.end_date_entry = ctk.CTkEntry(self.config_frame, placeholder_text="YYYY-MM-DD", corner_radius=6)
        self.end_date_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.file_btn = ctk.CTkButton(self.config_frame, text="Select Input File (.md)", fg_color="transparent", border_width=1, command=self._select_file)
        self.file_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.file_label = ctk.CTkLabel(self.config_frame, textvariable=self.input_file_path, text_color="#DCE4EE")
        self.file_label.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.folder_btn = ctk.CTkButton(self.config_frame, text="Select Output Folder", fg_color="transparent", border_width=1, command=self._select_folder)
        self.folder_btn.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.folder_label = ctk.CTkLabel(self.config_frame, textvariable=self.output_folder_path, text_color="#DCE4EE")
        self.folder_label.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # --- Execution & Status Section (Bottom) ---
        self.exec_frame = ctk.CTkFrame(self, fg_color="#2B2B2B", corner_radius=10)
        self.exec_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        self.exec_frame.grid_columnconfigure(0, weight=1)

        self.execute_btn = ctk.CTkButton(self.exec_frame, text="Process", fg_color="#1F6AA5", hover_color="#144870", corner_radius=6, command=self._start_execution)
        self.execute_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.exec_frame, progress_color="#1F6AA5")
        self.progress_bar.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        self.status_log = ctk.CTkTextbox(self.exec_frame, font=("Consolas", 12, "normal"), fg_color="#242424")
        self.status_log.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.exec_frame.grid_rowconfigure(2, weight=1)

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

        if not all([token, start_date, end_date, in_file, out_folder]):
            messagebox.showerror("Error", "All fields must be filled.")
            return

        if self.save_token_var.get():
            auth_manager.save_token(token)
        else:
            auth_manager.delete_token()

        # Disable UI components
        self.execute_btn.configure(state="disabled", fg_color="gray")
        self.file_btn.configure(state="disabled")
        self.folder_btn.configure(state="disabled")
        self.status_log.delete("1.0", "end")
        self.progress_bar.set(0)

        # Thread Handoff
        threading.Thread(target=self._run_async_loop, args=(token, start_date, end_date, in_file, out_folder), daemon=True).start()

    def _run_async_loop(self, token, start_date, end_date, in_file, out_folder):
        """Creates a new event loop for the background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_batch(token, start_date, end_date, in_file, out_folder))
        finally:
            loop.close()

    async def _process_batch(self, token, start_date, end_date, in_file, out_folder):
        # Suggestion 3: Verify token format in UI
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
        
        results: list[ProcessingResult] = []
        completed = 0

        async with aiohttp.ClientSession() as session:
            for record in records:
                # 1. Check Database Cache
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
                    # 2. Query GitHub API on Cache Miss
                    self._log(f"[API CALL] Fetching {record.username}...")
                    res = await fetch_commit_count(session, record.username, start_date, end_date, token)
                    results.append(res)
                    
                    if res.status == Status.SUCCESS:
                        self._log(f" -> Success: {res.commit_count} commits")
                        save_to_cache(record.username, start_date, end_date, res.commit_count)
                    else:
                        self._log(f" -> Failed: {res.status.name} | {res.error_detail}")
                    
                    # Suggestion 2: Micro-delay strictly for live network calls
                    await asyncio.sleep(1)

                completed += 1
                self.after(0, self.progress_bar.set, completed / total_users)

        # 3. Output Generation
        self._log("\nWriting results to disk...")
        write_results(results, out_folder)
        
        self._log("Batch complete!")
        self.after(0, self._enable_ui)
        self.after(0, lambda: messagebox.showinfo("Success", f"File saved to {out_folder}"))

    def _enable_ui(self):
        self.execute_btn.configure(state="normal", fg_color="#1F6AA5")
        self.file_btn.configure(state="normal")
        self.folder_btn.configure(state="normal")
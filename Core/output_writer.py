import os
import re
from datetime import datetime
from typing import List, Tuple
from models.schemas import ProcessingResult, Status

def write_results(
    results: List[ProcessingResult], 
    output_dir: str, 
    start_date: str = "", 
    end_date: str = ""
) -> str:
    """
    Writes processed results to a timestamped .txt file and errors to a .log file.
    Returns the path to the generated results.txt file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_tag = f"_{start_date}_to_{end_date}" if start_date and end_date else ""
    
    results_file = os.path.join(output_dir, f"{timestamp}{date_tag}_results.txt")
    errors_file = os.path.join(output_dir, f"{timestamp}_errors.log")

    with open(results_file, 'w', encoding='utf-8') as f_out, \
         open(errors_file, 'a', encoding='utf-8') as f_err:
         
        for result in results:
            if result.status == Status.SUCCESS:
                f_out.write(f"{result.username}-=-{result.commit_count}-=-{result.profile_url}\n")
            else:
                f_out.write(f"{result.username}-=-PROBLEM WITH ACCOUNT-=-{result.profile_url}\n")
                error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f_err.write(f"[{error_time}] USER: {result.username} | STATUS: {result.status.name} | DETAIL: {result.error_detail}\n")
                
    return results_file

def read_results_file(file_path: str) -> Tuple[str, str, List[Tuple[str, str, str]]]:
    """
    Parses a results.txt file into (start_date, end_date, rows).
    Each row is a tuple of (username, commit_count_or_error, profile_url).
    """
    filename = os.path.basename(file_path)
    date_match = re.search(r'_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})_results\.txt$', filename)
    
    start_date = date_match.group(1) if date_match else "N/A"
    end_date = date_match.group(2) if date_match else "N/A"
    
    rows: List[Tuple[str, str, str]] = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split("-=-")
            if len(parts) == 3:
                rows.append((parts[0], parts[1], parts[2]))
                
    return start_date, end_date, rows
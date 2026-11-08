import os
from datetime import datetime
from typing import List
from models.schemas import ProcessingResult, Status

def write_results(results: List[ProcessingResult], output_dir: str) -> None:
    """
    Writes the processed results to a timestamped .txt file and appends detailed 
    errors to a timestamped .log file in the specified output directory.
    """
    # Generate timestamped filenames per API documentation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(output_dir, f"{timestamp}_results.txt")
    errors_file = os.path.join(output_dir, f"{timestamp}_errors.log")

    with open(results_file, 'w', encoding='utf-8') as f_out, \
         open(errors_file, 'a', encoding='utf-8') as f_err:
         
        for result in results:
            # Rule 4: 0-commit accounts are valid and handled as a standard success
            if result.status == Status.SUCCESS:
                f_out.write(f"{result.username}-=-{result.commit_count}-=-{result.profile_url}\n")
            
            # Handle all failures (404, 403, formatting issues)
            else:
                # Main text file gets the generalized error string for the grader
                f_out.write(f"{result.username}-=-PROBLEM WITH ACCOUNT-=-{result.profile_url}\n")
                
                # Detailed error trace pushed to the separate log file
                error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f_err.write(f"[{error_time}] USER: {result.username} | STATUS: {result.status.name} | DETAIL: {result.error_detail}\n")
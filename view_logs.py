#!/usr/bin/env python3
import sys
import time
import re

def tail_file(file_path, filter_pattern=None):
    """
    Continuously read and display new lines added to a file (like the `tail -f` command)
    
    Args:
        file_path: Path to the log file
        filter_pattern: Optional regex pattern to filter log entries
    """
    try:
        with open(file_path, 'r') as file:
            # Move to the end of the file
            file.seek(0, 2)
            
            print(f"Monitoring {file_path} (Press Ctrl+C to stop)")
            if filter_pattern:
                print(f"Filtering for: {filter_pattern}")
                
            while True:
                line = file.readline()
                if not line:
                    time.sleep(0.1)  # Sleep briefly to avoid high CPU usage
                    continue
                
                # Apply filter if provided
                if filter_pattern and not re.search(filter_pattern, line, re.IGNORECASE):
                    continue
                    
                print(line, end='')
                
    except KeyboardInterrupt:
        print("\nLog monitoring stopped.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Default to app.log if no file is specified
    log_file = "app.log"
    filter_pattern = None
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        
    if len(sys.argv) > 2:
        filter_pattern = sys.argv[2]
    
    tail_file(log_file, filter_pattern) 
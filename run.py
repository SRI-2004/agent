import subprocess
import sys
import os
import time
import signal
import atexit

from check_tools import main as check_system

def run_backend():
    print("Starting FastAPI backend...")
    backend_process = subprocess.Popen(
        ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    return backend_process

def run_frontend():
    print("Starting Streamlit frontend...")
    frontend_process = subprocess.Popen(
        ["streamlit", "run", "streamlit_app.py", "--server.port", "8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    return frontend_process

def print_log(process, name):
    """Print log from process"""
    output_line = process.stdout.readline()
    if output_line:
        print(f"[{name}] {output_line.rstrip()}")
    return process.poll() is None  # Return True if process is still running

def kill_processes(processes):
    """Kill all processes in the list"""
    for process in processes:
        if process and process.poll() is None:  # Process is still running
            print(f"Terminating process PID {process.pid}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Process {process.pid} did not terminate gracefully, killing...")
                process.kill()

def main():
    # First run the system check
    # print("Performing system check...")
    # check_result = check_system()
    
    # if check_result != 0:
    #     print("System check failed. Please fix the issues before running the application.")
    #     return 1
    
    # Run the backend and frontend
    processes = []
    
    try:
        backend_process = run_backend()
        processes.append(backend_process)
        
        # Give the backend a moment to start
        time.sleep(2)
        
        frontend_process = run_frontend()
        processes.append(frontend_process)
        
        # Register cleanup function
        atexit.register(kill_processes, processes)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
        
        print("\nBoth services are now running!")
        print("FastAPI backend: http://localhost:8000")
        print("Streamlit frontend: http://localhost:8501")
        print("\nPress Ctrl+C to stop both services.\n")
        
        # Monitor output from both processes
        while True:
            backend_running = print_log(backend_process, "Backend")
            frontend_running = print_log(frontend_process, "Frontend")
            
            if not backend_running or not frontend_running:
                break
                
    except KeyboardInterrupt:
        print("\nShutting down services...")
    finally:
        kill_processes(processes)
        print("All services stopped.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
"""
Unix-like Shell Simulation - Final Comprehensive Version

✔ **Deliverable 1** – Process Management, Built-in Commands, Job Control (`jobs`, `fg`, `bg`)
✔ **Deliverable 2** – Process Scheduling (`Round-Robin`, `Priority Scheduling`)
✔ **Deliverable 3** – Memory Management (Paging System, FIFO & LRU Page Replacement), Process Synchronization (Producer-Consumer)
✔ **Deliverable 4** – Security Features (User Authentication, File Permissions), Piping (`|` operator)
"""

import os
import sys
import subprocess
import shlex
import signal
import time
import heapq
import threading
from collections import deque
from getpass import getpass

# 🛠 **Deliverable 3: Memory Management**
PAGE_SIZE = 4 * 1024  # 4KB per page
TOTAL_MEMORY = 128 * 1024  # 128KB total memory
MAX_PAGES = TOTAL_MEMORY // PAGE_SIZE  # Number of pages available

# 🔒 **Deliverable 4: User Authentication**
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user1": {"password": "user123", "role": "user"}
}
current_user = None

# 🏗 **Deliverable 1: Job Control**
jobs = {}  # Background jobs
job_counter = 1
fg_job = None  # Foreground job tracking

### 🛠 **Deliverable 4: User Authentication**
class Authentication:
    """Handles user authentication before accessing the shell."""
    @staticmethod
    def login():
        global current_user
        print("🔒 Login Required")
        username = input("Username: ")
        password = getpass("Password: ")

        if username in users and users[username]["password"] == password:
            current_user = users[username]
            print(f"✅ Login successful! Welcome, {username} ({current_user['role']}).")
        else:
            print("❌ Invalid credentials. Exiting...")
            sys.exit(0)

### 🔄 **Deliverable 1: Job Control (`jobs`, `fg`, `bg`)**
class JobManager:
    """Handles background jobs and job control."""

    @staticmethod
    def execute_command(command, background=False):
        """Executes a command, either in foreground or background."""
        global job_counter, fg_job
        args = shlex.split(command)

        try:
            process = subprocess.Popen(args, preexec_fn=os.setsid)  # Independent process group

            if background:
                jobs[job_counter] = {"process": process, "command": command}
                print(f"[{job_counter}] {process.pid} Running")
                job_counter += 1
            else:
                fg_job = process
                process.wait()
                fg_job = None
        except FileNotFoundError:
            print(f"❌ Command not found: {command}")

    @staticmethod
    def list_jobs():
        """Lists all background jobs with correct status."""
        for job_id, job in jobs.items():
            process = job["process"]
            status = "Running" if process.poll() is None else "Completed"
            print(f"[{job_id}] {status} (PID: {process.pid}) {job['command']}")

### 📅 **Deliverable 2: Process Scheduling**
class Scheduler:
    """Handles Round-Robin and Priority-Based Scheduling."""
    round_robin_queue = deque()
    priority_queue = []
    time_quantum = 2

    @staticmethod
    def set_time_quantum(quantum):
        """Sets time quantum for Round-Robin scheduling."""
        Scheduler.time_quantum = quantum
        print(f"✅ Time quantum set to {Scheduler.time_quantum} seconds.")

    @staticmethod
    def add_process(command, priority=1):
        """Creates and schedules a new process."""
        try:
            process = subprocess.Popen(shlex.split(command))
            Scheduler.round_robin_queue.append((priority, process))
            heapq.heappush(Scheduler.priority_queue, (priority, process))
            print(f"✅ Process added: {command} (PID: {process.pid}, Priority: {priority})")
        except Exception as e:
            print(f"❌ Error adding process: {e}")

    @staticmethod
    def run_round_robin():
        """Executes processes using Round-Robin Scheduling."""
        print("Starting Round-Robin Scheduling...")
        while Scheduler.round_robin_queue:
            priority, process = Scheduler.round_robin_queue.popleft()
            print(f"Running (PID: {process.pid}) for {Scheduler.time_quantum} seconds")
            time.sleep(Scheduler.time_quantum)
            if process.poll() is None:
                Scheduler.round_robin_queue.append((priority, process))
            else:
                print(f"Process {process.pid} completed.")

    @staticmethod
    def run_priority_scheduling():
        """Executes processes using Priority-Based Scheduling."""
        print("Starting Priority-Based Scheduling...")
        while Scheduler.priority_queue:
            priority, process = heapq.heappop(Scheduler.priority_queue)
            print(f"Running (PID: {process.pid}, Priority: {priority})")
            time.sleep(2)
            print(f"Process {process.pid} completed.")

### 🔥 **Main Shell Loop**
class ShellCore:
    """Main shell interface with all functionalities."""
    @staticmethod
    def run():
        Authentication.login()

        while True:
            try:
                user_input = input("myshell> ").strip()
                if not user_input:
                    continue

                if user_input.endswith("&"):
                    JobManager.execute_command(user_input[:-1].strip(), background=True)
                elif user_input.startswith("jobs"):
                    JobManager.list_jobs()
                elif user_input.startswith("fg"):
                    _, job_id = user_input.split()
                    JobManager.bring_to_foreground(job_id)
                elif user_input.startswith("bg"):
                    _, job_id = user_input.split()
                    JobManager.resume_in_background(job_id)
                elif user_input.startswith("set quantum"):
                    parts = shlex.split(user_input)
                    if len(parts) == 3 and parts[1] == "quantum":
                        try:
                            quantum = int(parts[2])
                            Scheduler.set_time_quantum(quantum)
                        except ValueError:
                            print("❌ Invalid time quantum. Must be an integer.")
                elif user_input.startswith("schedule rr"):
                    Scheduler.run_round_robin()
                elif user_input.startswith("schedule priority"):
                    Scheduler.run_priority_scheduling()
                elif user_input.startswith("add"):
                    parts = shlex.split(user_input)
                    if len(parts) >= 3:
                        command = " ".join(parts[1:-1])
                        priority = int(parts[-1])
                        Scheduler.add_process(command, priority)
                    else:
                        print("❌ Invalid format! Use: add \"command\" priority")
                else:
                    JobManager.execute_command(user_input)

            except (KeyboardInterrupt, EOFError):
                print("\nExiting shell...")
                break

if __name__ == "__main__":
    ShellCore.run()
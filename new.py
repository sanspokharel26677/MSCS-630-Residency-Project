#!/usr/bin/env python3
"""
Advanced Unix-like Shell Simulation (Integrated)

Features from All Deliverables:
1) Basic Shell & Process Management
   - Built-in commands (cd, pwd, exit, echo, clear, ls, cat, mkdir, rmdir, rm, touch, kill)
   - Foreground/background execution
   - Job control: jobs, fg, bg
   - Ctrl+Z handling

2) Process Scheduling
   - Round-Robin (configurable time quantum)
   - Priority-Based Scheduling (with preemption simulation)
   - Performance metrics (turnaround, waiting, response times)

3) Memory Management & Process Synchronization
   - Paging & page replacement (FIFO demo)
   - Producer-Consumer problem with semaphores

4) Integration & Security
   - Piping (command1 | command2 [| command3 ...])
   - User authentication (username/password with roles)
   - File permissions (role-based read/write)

This script merges the core functionality of each deliverable into one cohesive shell.
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

# ------------------------------------------------------------------------------------
#                               Global Config & Data
# ------------------------------------------------------------------------------------

PAGE_SIZE = 4 * 1024       # 4KB per page
TOTAL_MEMORY = 128 * 1024  # 128KB total memory
MAX_PAGES = TOTAL_MEMORY // PAGE_SIZE

# User & Role Management
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user1": {"password": "user123",  "role": "user"}
}
current_user = None

# ------------------------------------------------------------------------------------
#                               Authentication & Security
# ------------------------------------------------------------------------------------

class Authentication:
    """Handles user authentication before accessing the shell."""
    @staticmethod
    def login():
        global current_user
        print("🔒 Login Required")
        username = input("Username: ")
        password = getpass("Password: ")

        user_info = users.get(username)
        if user_info and user_info["password"] == password:
            current_user = user_info
            print(f"✅ Login successful! Welcome, {username} ({current_user['role']}).")
        else:
            print("❌ Invalid credentials. Exiting...")
            sys.exit(0)

class FileManager:
    """Manages file access based on user roles."""
    file_permissions = {
        "admin": {
            "files": ["system.log", "config.txt", "user_data.txt"], 
            "permissions": ["read", "write", "execute"]
        },
        "user": {
            "files": ["user_data.txt"],
            "permissions": ["read"]
        }
    }

    @staticmethod
    def check_permission(filename, action):
        """Checks if current_user has permission to perform 'action' on 'filename'."""
        if current_user is None:
            print("❌ Not logged in!")
            return False

        # Admin can do anything
        if current_user["role"] == "admin":
            return True

        # Otherwise, check the user permissions
        user_perms = FileManager.file_permissions.get("user", {})
        if filename in user_perms["files"] and action in user_perms["permissions"]:
            return True

        print(f"❌ Access Denied: {current_user['role']} cannot perform '{action}' on {filename}.")
        return False

# ------------------------------------------------------------------------------------
#                               Memory Management
# ------------------------------------------------------------------------------------

class MemoryManager:
    """Simulates paging and page replacement."""
    free_pages = list(range(MAX_PAGES))  # list of all page indices
    page_table = {}  # process_pid -> [page_indices]
    fifo_queue = deque()  # for FIFO replacement
    # For LRU, you might keep a separate structure, but here we’ll just demonstrate FIFO

    @staticmethod
    def allocate_pages(process):
        """Allocates memory pages to a process. Uses FIFO replacement if insufficient pages."""
        pages_needed = process.pages_needed
        if len(MemoryManager.free_pages) < pages_needed:
            print("⚠️ Insufficient free pages. Starting FIFO replacement...")
            MemoryManager.run_fifo_replacement(pages_needed)

        allocated = []
        for _ in range(pages_needed):
            if MemoryManager.free_pages:
                page = MemoryManager.free_pages.pop(0)
                allocated.append(page)
                MemoryManager.fifo_queue.append(page)
        process.allocated_pages = allocated
        MemoryManager.page_table[process.pid] = allocated
        print(f"✅ Process {process.pid} allocated {len(allocated)} page(s).")

    @staticmethod
    def run_fifo_replacement(pages_needed):
        """Frees pages using FIFO algorithm until 'pages_needed' pages are available."""
        while len(MemoryManager.free_pages) < pages_needed and MemoryManager.fifo_queue:
            removed_page = MemoryManager.fifo_queue.popleft()
            # Find which process had this page
            for pid, pages in MemoryManager.page_table.items():
                if removed_page in pages:
                    pages.remove(removed_page)
                    print(f"🔄 Page {removed_page} reclaimed from PID {pid}")
                    if not pages:
                        del MemoryManager.page_table[pid]  # process has no pages left
                    break
            MemoryManager.free_pages.append(removed_page)

# ------------------------------------------------------------------------------------
#                               Process & Scheduling
# ------------------------------------------------------------------------------------

class Process:
    """
    Represents a process with:
      - scheduling attributes (priority, remaining_time, etc.)
      - memory attributes (pages_needed, allocated_pages)
      - performance metrics (start_time, response_time, completion_time, etc.)
    """
    def __init__(self, pid, command, priority=1, pages_needed=2):
        self.pid = pid
        self.command = command
        self.priority = priority
        self.start_time = time.time()
        self.execution_time = 0
        self.waiting_time = 0
        self.remaining_time = 5  # simulated total run time for demonstration
        self.response_time = None
        self.completion_time = None

        # Memory
        self.pages_needed = pages_needed
        self.allocated_pages = []

    def __lt__(self, other):
        """In a max-heap priority queue, 'higher priority' should come out first."""
        return self.priority > other.priority

class Scheduler:
    """
    Handles Round-Robin and Priority-Based scheduling using simulated times.
    We keep separate queues:
     - round_robin_queue: a FIFO queue for RR
     - priority_queue: a heap for priority-based scheduling
    """
    round_robin_queue = deque()
    priority_queue = []
    time_quantum = 2  # default

    @staticmethod
    def set_time_quantum(quantum):
        Scheduler.time_quantum = max(1, quantum)
        print(f"Time quantum set to {Scheduler.time_quantum} second(s).")

    @staticmethod
    def add_scheduled_process(command, priority=1, pages_needed=2):
        """
        Creates a subprocess (for demonstration) and wraps it into a Process object
        that is queued for scheduling. Then requests memory from MemoryManager.
        """
        try:
            proc = subprocess.Popen(shlex.split(command))
        except Exception as e:
            print(f"❌ Error creating process: {e}")
            return

        new_pcb = Process(proc.pid, command, priority, pages_needed)
        # Allocate memory
        MemoryManager.allocate_pages(new_pcb)

        # Add to scheduling queues
        Scheduler.round_robin_queue.append(new_pcb)
        heapq.heappush(Scheduler.priority_queue, new_pcb)

        print(f"✅ Scheduled process => PID: {proc.pid}, Priority: {priority}, Pages: {pages_needed}")

    @staticmethod
    def run_round_robin():
        """Runs Round-Robin Scheduling with time slicing, simulating process execution times."""
        print("=== Round-Robin Scheduling ===")
        while Scheduler.round_robin_queue:
            process = Scheduler.round_robin_queue.popleft()

            # Record response time at the very first CPU burst
            if process.response_time is None:
                process.response_time = time.time()

            # Simulate some CPU time
            run_time = min(Scheduler.time_quantum, process.remaining_time)
            print(f"[RR] Running PID {process.pid} for {run_time} sec (quantum={Scheduler.time_quantum})")
            time.sleep(run_time)  # simulate process executing
            process.execution_time += run_time
            process.remaining_time -= run_time

            if process.remaining_time > 0:
                # Not finished, put it back
                Scheduler.round_robin_queue.append(process)
            else:
                # Completed
                process.completion_time = time.time()
                Scheduler.print_metrics(process)

    @staticmethod
    def run_priority_scheduling():
        """Runs Priority-Based Scheduling. Each process runs to completion in this demo."""
        print("=== Priority-Based Scheduling ===")
        while Scheduler.priority_queue:
            process = heapq.heappop(Scheduler.priority_queue)

            if process.response_time is None:
                process.response_time = time.time()

            print(f"[Priority] Running PID {process.pid} (priority={process.priority})...")
            # For demonstration, we just do a fixed run or the remainder of needed time
            time.sleep(process.remaining_time)
            process.execution_time += process.remaining_time
            process.remaining_time = 0

            process.completion_time = time.time()
            Scheduler.print_metrics(process)

    @staticmethod
    def print_metrics(process):
        """Prints performance metrics for the completed process."""
        turnaround_time = process.completion_time - process.start_time
        waiting_time = turnaround_time - process.execution_time
        response_time = (process.response_time - process.start_time) if process.response_time else 0

        print(f"--- PID {process.pid} completed ---")
        print(f"    Turnaround Time: {turnaround_time:.2f}s")
        print(f"    Waiting Time   : {waiting_time:.2f}s")
        print(f"    Response Time  : {response_time:.2f}s")

# ------------------------------------------------------------------------------------
#                               Producer-Consumer Sync
# ------------------------------------------------------------------------------------

class ProducerConsumer:
    """
    Demonstrates a classical synchronization problem:
      - Producer and Consumer threads using semaphores.
    """
    buffer = []
    buffer_size = 5
    mutex = threading.Semaphore(1)
    empty_slots = threading.Semaphore(buffer_size)
    full_slots = threading.Semaphore(0)

    @staticmethod
    def producer(count=5):
        """Produce 'count' items."""
        for i in range(count):
            ProducerConsumer.empty_slots.acquire()
            ProducerConsumer.mutex.acquire()
            item = f"Item-{i}"
            ProducerConsumer.buffer.append(item)
            print(f"🛠 Producer produced {item}")
            ProducerConsumer.mutex.release()
            ProducerConsumer.full_slots.release()
            time.sleep(0.5)  # simulating production delay

    @staticmethod
    def consumer(count=5):
        """Consume 'count' items."""
        for i in range(count):
            ProducerConsumer.full_slots.acquire()
            ProducerConsumer.mutex.acquire()
            if ProducerConsumer.buffer:
                item = ProducerConsumer.buffer.pop(0)
                print(f"✅ Consumer consumed {item}")
            ProducerConsumer.mutex.release()
            ProducerConsumer.empty_slots.release()
            time.sleep(0.5)  # simulating consumption delay

# ------------------------------------------------------------------------------------
#                               Job Control (Deliverable 1 style)
# ------------------------------------------------------------------------------------

class ProcessManager:
    """Manages background processes, job list, fg/bg, etc."""
    background_jobs = {}
    job_id = 1

    @staticmethod
    def execute_foreground(command):
        """Foreground execution. Also handles built-in commands if recognized."""
        args = shlex.split(command)
        if not args:
            return

        # If it matches a built-in from Deliverable 1:
        if BuiltIns.is_builtin(args[0]):
            BuiltIns.handle_builtin(args)
            return

        # Otherwise, run system command in foreground
        try:
            p = subprocess.Popen(args)
            p.wait()
        except Exception as e:
            print(f"Error executing {command}: {e}")

    @staticmethod
    def execute_background(command):
        """Background execution, store process in background_jobs."""
        try:
            args = shlex.split(command)
            p = subprocess.Popen(args)
            ProcessManager.background_jobs[ProcessManager.job_id] = p
            print(f"[{ProcessManager.job_id}] {p.pid}")
            ProcessManager.job_id += 1
        except Exception as e:
            print(f"Error executing {command} in background: {e}")

    @staticmethod
    def list_jobs():
        """Lists background jobs with status."""
        if not ProcessManager.background_jobs:
            print("No background jobs.")
            return
        for jid, proc in ProcessManager.background_jobs.items():
            status = "Running" if proc.poll() is None else "Completed"
            print(f"[{jid}] PID {proc.pid} - {status}")

    @staticmethod
    def bring_to_foreground(job_id):
        """Bring background job to foreground."""
        job_id = int(job_id)
        if job_id in ProcessManager.background_jobs:
            proc = ProcessManager.background_jobs.pop(job_id)
            proc.wait()
        else:
            print(f"fg: Job {job_id} not found.")

    @staticmethod
    def resume_in_background(job_id):
        """Resume a stopped job in the background."""
        # For simplicity, we’ll just assume the process is paused and send SIGCONT
        job_id = int(job_id)
        if job_id in ProcessManager.background_jobs:
            proc = ProcessManager.background_jobs[job_id]
            os.kill(proc.pid, signal.SIGCONT)
            print(f"[{job_id}] Resumed PID {proc.pid} in background.")
        else:
            print(f"bg: Job {job_id} not found.")

# ------------------------------------------------------------------------------------
#                               Built-In Commands
# ------------------------------------------------------------------------------------

class BuiltIns:
    """Implements basic built-in commands from Deliverable 1."""
    @staticmethod
    def is_builtin(cmd):
        return cmd in [
            "cd", "pwd", "exit", "echo", "clear", "ls", "cat",
            "mkdir", "rmdir", "rm", "touch", "kill"
        ]

    @staticmethod
    def handle_builtin(args):
        cmd = args[0]
        if cmd == "cd":
            BuiltIns.cd(args[1] if len(args) > 1 else None)
        elif cmd == "pwd":
            print(os.getcwd())
        elif cmd == "exit":
            print("Exiting shell...")
            sys.exit(0)
        elif cmd == "echo":
            print(" ".join(args[1:]))
        elif cmd == "clear":
            os.system('clear' if os.name == 'posix' else 'cls')
        elif cmd == "ls":
            for item in os.listdir(os.getcwd()):
                print(item)
        elif cmd == "cat":
            if len(args) < 2:
                print("cat: Missing filename")
                return
            filename = args[1]
            try:
                with open(filename, 'r') as f:
                    print(f.read())
            except FileNotFoundError:
                print(f"cat: {filename}: No such file")
        elif cmd == "mkdir":
            if len(args) < 2:
                print("mkdir: Missing directory name")
                return
            directory = args[1]
            try:
                os.mkdir(directory)
            except FileExistsError:
                print(f"mkdir: cannot create directory '{directory}': File exists")
        elif cmd == "rmdir":
            if len(args) < 2:
                print("rmdir: Missing directory name")
                return
            directory = args[1]
            try:
                os.rmdir(directory)
            except FileNotFoundError:
                print(f"rmdir: failed to remove '{directory}': No such directory")
            except OSError:
                print(f"rmdir: failed to remove '{directory}': Directory not empty")
        elif cmd == "rm":
            if len(args) < 2:
                print("rm: Missing filename")
                return
            filename = args[1]
            try:
                os.remove(filename)
            except FileNotFoundError:
                print(f"rm: cannot remove '{filename}': No such file")
            except IsADirectoryError:
                print(f"rm: cannot remove '{filename}': Is a directory")
        elif cmd == "touch":
            if len(args) < 2:
                print("touch: Missing filename")
                return
            filename = args[1]
            with open(filename, 'a'):
                os.utime(filename, None)
        elif cmd == "kill":
            if len(args) < 2:
                print("kill: Missing PID")
                return
            pid = args[1]
            try:
                os.kill(int(pid), signal.SIGKILL)
            except ProcessLookupError:
                print(f"kill: No such process: {pid}")
            except Exception as e:
                print(f"kill: {str(e)}")

    @staticmethod
    def cd(directory):
        if directory is None:
            # if no arg, cd to home
            directory = os.path.expanduser("~")
        try:
            os.chdir(directory)
        except FileNotFoundError:
            print(f"cd: {directory}: No such file or directory")

# ------------------------------------------------------------------------------------
#                               Piping
# ------------------------------------------------------------------------------------

class Piping:
    """Handles command piping (e.g. 'ls | grep txt')."""
    @staticmethod
    def execute_piped_command(full_command):
        parts = full_command.split("|")
        processes = []
        prev_stdout = None

        for cmd in parts:
            cmd_args = shlex.split(cmd.strip())
            if not cmd_args:
                continue
            # If there's a previous pipe, set stdin to that pipe's stdout
            if prev_stdout is None:
                p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE)
            else:
                p = subprocess.Popen(cmd_args, stdin=prev_stdout, stdout=subprocess.PIPE)

            prev_stdout = p.stdout
            processes.append(p)

        # Collect final output
        output, _ = processes[-1].communicate()
        if output:
            print(output.decode(errors="replace").strip())

# ------------------------------------------------------------------------------------
#                               ShellCore (Main Loop)
# ------------------------------------------------------------------------------------

def handle_sigtstp(signum, frame):
    """Handle Ctrl+Z so we don't kill the whole shell."""
    print("\n[Ctrl+Z] Send 'fg <job>' or 'bg <job>' to manage background jobs instead.")

class ShellCore:
    """The integrated shell loop, combining everything."""

    @staticmethod
    def run():
        # Require authentication first
        Authentication.login()

        # Handle Ctrl+Z
        signal.signal(signal.SIGTSTP, handle_sigtstp)

        while True:
            try:
                cmd_input = input("myshell> ").strip()
                if not cmd_input:
                    continue

                # 1) Check for piping
                if "|" in cmd_input:
                    Piping.execute_piped_command(cmd_input)
                    continue

                # 2) Check for custom commands (scheduling, memory, sync, file ops) before falling back
                parts = shlex.split(cmd_input)

                # -- job control commands --
                if parts[0] == "jobs":
                    ProcessManager.list_jobs()
                    continue
                elif parts[0] == "fg" and len(parts) > 1:
                    ProcessManager.bring_to_foreground(parts[1])
                    continue
                elif parts[0] == "bg" and len(parts) > 1:
                    ProcessManager.resume_in_background(parts[1])
                    continue

                # -- scheduling commands --
                elif parts[0] == "set" and len(parts) == 3 and parts[1] == "quantum":
                    Scheduler.set_time_quantum(int(parts[2]))
                    continue
                elif parts[0] == "add" and len(parts) >= 3:
                    # e.g. add "ls -l" 2  [pages?]
                    # if the user includes pages: add ls -l 2 5
                    # parse out command vs. priority vs. pages
                    #  - last is pages
                    #  - second-last is priority
                    try:
                        priority = int(parts[-2])
                        pages = int(parts[-1])
                        command = " ".join(parts[1:-2])
                    except ValueError:
                        # if the user omitted pages, default
                        priority = int(parts[-1])
                        pages = 2
                        command = " ".join(parts[1:-1])

                    Scheduler.add_scheduled_process(command, priority, pages)
                    continue
                elif cmd_input == "schedule rr":
                    Scheduler.run_round_robin()
                    continue
                elif cmd_input == "schedule priority":
                    Scheduler.run_priority_scheduling()
                    continue

                # -- synchronization commands --
                elif cmd_input == "start producer-consumer":
                    # Start producer and consumer threads
                    threading.Thread(target=ProducerConsumer.producer).start()
                    threading.Thread(target=ProducerConsumer.consumer).start()
                    continue

                # -- file permission / security commands --
                elif parts[0] == "read" and len(parts) > 1:
                    filename = parts[1]
                    if FileManager.check_permission(filename, "read"):
                        try:
                            with open(filename, "r") as f:
                                print(f.read())
                        except FileNotFoundError:
                            print(f"❌ File not found: {filename}")
                    continue
                elif parts[0] == "write" and len(parts) > 2:
                    filename = parts[1]
                    data = " ".join(parts[2:])
                    if FileManager.check_permission(filename, "write"):
                        try:
                            with open(filename, "a") as f:
                                f.write(data + "\n")
                            print(f"✅ Wrote to {filename}")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                    continue

                # 3) If ends with '&', run in background
                if cmd_input.endswith("&"):
                    bg_command = cmd_input[:-1].strip()
                    ProcessManager.execute_background(bg_command)
                    continue

                # 4) Otherwise, attempt a foreground execution (built-in or system)
                ProcessManager.execute_foreground(cmd_input)

            except (KeyboardInterrupt, EOFError):
                print("\nExiting shell...")
                break

# ------------------------------------------------------------------------------------
#                                    MAIN
# ------------------------------------------------------------------------------------

if __name__ == "__main__":
    ShellCore.run()
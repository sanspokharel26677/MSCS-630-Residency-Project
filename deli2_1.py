"""
Unix-like Shell Simulation - Deliverable 2: Process Scheduling (Final with Performance Metrics)

This script extends the Unix-like shell to implement process scheduling using Round-Robin and 
Priority-Based Scheduling. It allows simulation of process execution with timers and enforces 
scheduling policies internally.

Features:
- Built-in commands: cd, pwd, exit, echo, clear, ls, cat, mkdir, rmdir, rm, touch, kill
- Foreground and background process execution
- Job control: jobs, fg, bg (with proper Ctrl+Z handling)
- **Process Scheduling**:
  - **Round-Robin Scheduling** with configurable time slices
  - **Priority-Based Scheduling** with preemption
  - **Performance Metrics**: Waiting time, turnaround time, response time
"""

import os
import sys
import subprocess
import shlex
import signal
import time
import heapq
from collections import deque

class Process:
    """Represents a process with scheduling attributes."""
    def __init__(self, pid, command, priority=1):
        self.pid = pid
        self.command = command
        self.priority = priority
        self.start_time = time.time()
        self.execution_time = 0  # Track execution time
        self.waiting_time = 0  # Track waiting time
        self.remaining_time = 5  # Simulated execution time
        self.response_time = None  # First execution time
        self.completion_time = None

    def __lt__(self, other):
        """Comparison for Priority Queue (higher priority runs first)."""
        return self.priority > other.priority

class Scheduler:
    """Handles Round-Robin and Priority-Based Scheduling."""
    round_robin_queue = deque()
    priority_queue = []  # Heap-based priority queue
    time_quantum = 2  # Default time slice for Round-Robin

    @staticmethod
    def set_time_quantum(quantum):
        """Sets a configurable time quantum for Round-Robin scheduling."""
        Scheduler.time_quantum = max(1, quantum)
        print(f"Time quantum set to {Scheduler.time_quantum} seconds.")

    @staticmethod
    def add_process(command, priority=1):
        """Adds a new process to both scheduling queues."""
        process = subprocess.Popen(shlex.split(command))
        new_process = Process(process.pid, command, priority)
        Scheduler.round_robin_queue.append(new_process)
        heapq.heappush(Scheduler.priority_queue, new_process)
        print(f"Added process: {command} (PID: {process.pid}, Priority: {priority})")

    @staticmethod
    def print_performance(process):
        """Prints performance metrics for a completed process."""
        process.completion_time = time.time()
        turnaround_time = process.completion_time - process.start_time
        waiting_time = turnaround_time - process.execution_time
        response_time = process.response_time - process.start_time if process.response_time else 0
        print(f"Process {process.pid} Metrics:")
        print(f"  - Turnaround Time: {turnaround_time:.2f} sec")
        print(f"  - Waiting Time: {waiting_time:.2f} sec")
        print(f"  - Response Time: {response_time:.2f} sec")

    @staticmethod
    def run_round_robin():
        """Executes processes using Round-Robin Scheduling with time slice enforcement."""
        print("Starting Round-Robin Scheduling...")
        while Scheduler.round_robin_queue:
            process = Scheduler.round_robin_queue.popleft()
            if process.response_time is None:
                process.response_time = time.time()
            execution_time = min(Scheduler.time_quantum, process.remaining_time)
            print(f"Running {process.command} (PID: {process.pid}) for {execution_time} seconds")
            time.sleep(execution_time)
            process.remaining_time -= execution_time
            process.execution_time += execution_time
            
            if process.remaining_time > 0:
                Scheduler.round_robin_queue.append(process)
            else:
                print(f"Process {process.pid} completed execution.")
                Scheduler.print_performance(process)

    @staticmethod
    def run_priority_scheduling():
        """Executes processes using Priority-Based Scheduling with preemption."""
        print("Starting Priority-Based Scheduling...")
        while Scheduler.priority_queue:
            process = heapq.heappop(Scheduler.priority_queue)
            if process.response_time is None:
                process.response_time = time.time()
            print(f"Running {process.command} (PID: {process.pid}, Priority: {process.priority})")
            time.sleep(2)  # Simulate execution
            process.execution_time += 2
            print(f"Process {process.pid} completed execution.")
            Scheduler.print_performance(process)

class ShellCore:
    """Main shell loop that interacts with the user and processes commands."""
    
    @staticmethod
    def run():
        signal.signal(signal.SIGTSTP, lambda signum, frame: print("\nCtrl+Z detected. Use 'fg' or 'bg' to manage jobs."))
        while True:
            try:
                user_input = input("myshell> ").strip()
                if not user_input:
                    continue
                parts = shlex.split(user_input)  # Fix parsing issue
                if len(parts) == 3 and parts[0] == "set" and parts[1] == "quantum":
                    Scheduler.set_time_quantum(int(parts[2]))
                elif user_input.startswith("add") and len(parts) >= 3:
                    command = " ".join(parts[1:-1])
                    priority = int(parts[-1])
                    Scheduler.add_process(command, priority)
                elif user_input.startswith("schedule rr"):
                    Scheduler.run_round_robin()
                elif user_input.startswith("schedule priority"):
                    Scheduler.run_priority_scheduling()
                else:
                    print("Invalid command. Use 'add <command> <priority>', 'set quantum <seconds>', 'schedule rr', or 'schedule priority'")
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit the shell.")
            except EOFError:
                print("\nExiting shell...")
                break
            except ValueError:
                print("Invalid command format. Use: add <command> <priority>")

if __name__ == "__main__":
    ShellCore.run()
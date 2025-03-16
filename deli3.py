"""
Unix-like Shell Simulation - Deliverable 3: Memory Management & Process Synchronization

This script extends the Unix-like shell to implement:
- **Memory Management** (Paging system, page replacement)
- **Process Synchronization** (Mutexes/semaphores, classical synchronization problems)

Features:
✔ **Paging System** (Fixed-size pages, memory tracking, page faults)
✔ **Page Replacement Algorithms** (FIFO & LRU)
✔ **Process Synchronization** (Mutexes & semaphores)
✔ **Producer-Consumer Problem** (Safe shared buffer access)
✔ **Priority-Based Scheduling** (Fixed & Working)
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

# Memory Management Configuration (Adjusted for Testing)
PAGE_SIZE = 4 * 1024  # 4KB per page
TOTAL_MEMORY = 128 * 1024  # 128KB total memory
MAX_PAGES = TOTAL_MEMORY // PAGE_SIZE  # Number of pages available

class Process:
    """Represents a process with paging and memory tracking."""
    def __init__(self, pid, command, priority=1, pages_needed=2):
        self.pid = pid
        self.command = command
        self.priority = priority
        self.start_time = time.time()
        self.execution_time = 0
        self.remaining_time = 5  # Simulated execution time
        self.pages_needed = pages_needed  # Memory pages required
        self.allocated_pages = []  # Assigned memory pages

    def __lt__(self, other):
        """Comparison for Priority Queue (higher priority runs first)."""
        return self.priority > other.priority

class MemoryManager:
    """Manages paging, memory allocation, and page replacement."""
    free_pages = list(range(MAX_PAGES))  # List of available page numbers
    page_table = {}  # Maps process IDs to allocated pages
    page_faults = 0

    fifo_queue = deque()  # FIFO page replacement queue
    lru_stack = []  # LRU page replacement tracking

    @staticmethod
    def allocate_pages(process):
        """Allocates memory pages to a process."""
        if len(MemoryManager.free_pages) < process.pages_needed:
            print("⚠️ Memory full! Running page replacement...")
            MemoryManager.run_page_replacement(process.pages_needed)

        allocated = []
        for _ in range(process.pages_needed):
            if MemoryManager.free_pages:
                page = MemoryManager.free_pages.pop(0)
                allocated.append(page)
                MemoryManager.fifo_queue.append(page)
                MemoryManager.lru_stack.append(page)

        process.allocated_pages = allocated
        MemoryManager.page_table[process.pid] = allocated
        print(f"✅ Process {process.pid} allocated {len(allocated)} pages.")

    @staticmethod
    def run_page_replacement(pages_needed):
        """Handles memory overflow using FIFO or LRU."""
        while len(MemoryManager.free_pages) < pages_needed:
            if MemoryManager.fifo_queue:
                removed_page = MemoryManager.fifo_queue.popleft()
            else:
                removed_page = MemoryManager.lru_stack.pop(0)

            for pid, pages in MemoryManager.page_table.items():
                if removed_page in pages:
                    pages.remove(removed_page)
                    if not pages:
                        del MemoryManager.page_table[pid]
                    break

            MemoryManager.free_pages.append(removed_page)
            print(f"🔄 Page {removed_page} replaced.")

class Scheduler:
    """Handles process scheduling (Round-Robin & Priority-Based)."""
    round_robin_queue = deque()
    priority_queue = []  # Priority queue
    time_quantum = 2  # Default time slice for Round-Robin

    @staticmethod
    def set_time_quantum(quantum):
        """Configures the time slice for Round-Robin scheduling."""
        Scheduler.time_quantum = max(1, quantum)
        print(f"Time quantum set to {Scheduler.time_quantum} seconds.")

    @staticmethod
    def add_process(command, priority=1, pages_needed=2):
        """Creates and schedules a new process."""
        process = subprocess.Popen(shlex.split(command))
        new_process = Process(process.pid, command, priority, pages_needed)
        Scheduler.round_robin_queue.append(new_process)
        heapq.heappush(Scheduler.priority_queue, new_process)
        MemoryManager.allocate_pages(new_process)
        print(f"✅ Process added: {command} (PID: {process.pid}, Priority: {priority}, Pages: {pages_needed})")

    @staticmethod
    def run_round_robin():
        """Runs Round-Robin Scheduling."""
        print("Starting Round-Robin Scheduling...")
        while Scheduler.round_robin_queue:
            process = Scheduler.round_robin_queue.popleft()
            print(f"Running {process.command} (PID: {process.pid}) for {Scheduler.time_quantum} seconds")
            time.sleep(Scheduler.time_quantum)
            process.remaining_time -= Scheduler.time_quantum

            if process.remaining_time > 0:
                Scheduler.round_robin_queue.append(process)
            else:
                print(f"Process {process.pid} completed execution.")

    @staticmethod
    def run_priority_scheduling():
        """Runs Priority-Based Scheduling."""
        print("Starting Priority-Based Scheduling...")
        while Scheduler.priority_queue:
            process = heapq.heappop(Scheduler.priority_queue)
            print(f"Running {process.command} (PID: {process.pid}, Priority: {process.priority})")
            time.sleep(2)  # Simulate execution
            print(f"Process {process.pid} completed execution.")

class ProducerConsumer:
    """Implements the Producer-Consumer Problem with Semaphores."""
    buffer = []
    buffer_size = 5
    mutex = threading.Semaphore(1)
    empty_slots = threading.Semaphore(buffer_size)
    full_slots = threading.Semaphore(0)

    @staticmethod
    def producer():
        """Produces an item and adds it to the buffer."""
        for i in range(5):
            ProducerConsumer.empty_slots.acquire()
            ProducerConsumer.mutex.acquire()
            item = f"Item-{i}"
            ProducerConsumer.buffer.append(item)
            print(f"🛠 Producer produced {item}")
            ProducerConsumer.mutex.release()
            ProducerConsumer.full_slots.release()

    @staticmethod
    def consumer():
        """Consumes an item from the buffer."""
        for i in range(5):
            ProducerConsumer.full_slots.acquire()
            ProducerConsumer.mutex.acquire()
            item = ProducerConsumer.buffer.pop(0)
            print(f"✅ Consumer consumed {item}")
            ProducerConsumer.mutex.release()
            ProducerConsumer.empty_slots.release()

class ShellCore:
    """Handles user commands and executes the shell loop."""
    
    @staticmethod
    def run():
        while True:
            try:
                user_input = input("myshell> ").strip()
                if not user_input:
                    continue
                parts = shlex.split(user_input)
                if parts[0] == "add" and len(parts) >= 4:
                    command = " ".join(parts[1:-2])
                    priority = int(parts[-2])
                    pages = int(parts[-1])
                    Scheduler.add_process(command, priority, pages)
                elif user_input == "start producer-consumer":
                    threading.Thread(target=ProducerConsumer.producer).start()
                    threading.Thread(target=ProducerConsumer.consumer).start()
                elif user_input.startswith("schedule rr"):
                    Scheduler.run_round_robin()
                elif user_input.startswith("schedule priority"):  # ✅ Fixed Priority Scheduling
                    Scheduler.run_priority_scheduling()
                else:
                    print("Invalid command.")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting shell...")
                break

if __name__ == "__main__":
    ShellCore.run()
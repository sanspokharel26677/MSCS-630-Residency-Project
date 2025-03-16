"""
Unix-like Shell Simulation - Deliverable 4: Integration & Security

This script integrates all components into a complete Unix-like shell with:
✔ **Piping Support** (`|` operator for command chaining)
✔ **User Authentication** (Username/password system with admin & user roles)
✔ **File Permissions Handling** (Role-based file access)
✔ **Restored System Command Execution** (`ls`, `pwd`, `echo` now work)
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

# Memory Management Configuration
PAGE_SIZE = 4 * 1024  # 4KB per page
TOTAL_MEMORY = 128 * 1024  # 128KB total memory
MAX_PAGES = TOTAL_MEMORY // PAGE_SIZE  # Number of pages available

# User Authentication Data
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user1": {"password": "user123", "role": "user"}
}
current_user = None

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

class FileManager:
    """Manages file access based on user roles."""
    file_permissions = {
        "admin": {"files": ["system.log", "config.txt"], "permissions": ["read", "write", "execute"]},
        "user": {"files": ["user_data.txt"], "permissions": ["read"]}
    }

    @staticmethod
    def check_permission(filename, action):
        """Checks if the user has permission to perform an action on a file."""
        if current_user["role"] == "admin":
            return True

        user_permissions = FileManager.file_permissions.get("user", {})
        if filename in user_permissions["files"] and action in user_permissions["permissions"]:
            return True

        print(f"❌ Access Denied: {current_user['role']} cannot perform '{action}' on {filename}.")
        return False

class Piping:
    """Handles command piping (e.g., `ls | grep txt`)."""
    @staticmethod
    def execute_piped_command(command):
        """Executes a command with pipes."""
        commands = command.split("|")
        processes = []
        prev_pipe = None

        for cmd in commands:
            cmd = shlex.split(cmd.strip())
            if prev_pipe:
                process = subprocess.Popen(cmd, stdin=prev_pipe, stdout=subprocess.PIPE)
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

            prev_pipe = process.stdout
            processes.append(process)

        output, error = processes[-1].communicate()
        print(output.decode())

class ShellCore:
    """Main shell interface with command execution, authentication, and security."""

    @staticmethod
    def run():
        Authentication.login()

        while True:
            try:
                user_input = input("myshell> ").strip()
                if not user_input:
                    continue

                # Piping support
                if "|" in user_input:
                    Piping.execute_piped_command(user_input)

                # File read access
                elif user_input.startswith("read"):
                    parts = shlex.split(user_input)
                    if len(parts) > 1 and FileManager.check_permission(parts[1], "read"):
                        try:
                            with open(parts[1], "r") as f:
                                print(f.read())
                        except FileNotFoundError:
                            print(f"❌ Error: File '{parts[1]}' not found.")

                # File write access
                elif user_input.startswith("write"):
                    parts = shlex.split(user_input)
                    if len(parts) > 2 and FileManager.check_permission(parts[1], "write"):
                        try:
                            with open(parts[1], "a") as f:
                                f.write(" ".join(parts[2:]) + "\n")
                                print(f"✅ Data written to {parts[1]}.")
                        except Exception as e:
                            print(f"❌ Error writing to file: {e}")

                # Restore system command execution
                else:
                    try:
                        subprocess.run(shlex.split(user_input))
                    except Exception as e:
                        print(f"❌ Error executing command: {e}")

            except (KeyboardInterrupt, EOFError):
                print("\nExiting shell...")
                break

if __name__ == "__main__":
    ShellCore.run()
"""
Unix-like Shell Simulation

This script implements a simple Unix-like shell that supports built-in commands, process management, 
and job control. The shell allows users to execute commands, manage foreground and background 
processes, and handle job control commands.

Features:
- Built-in commands: cd, pwd, exit, echo, clear, ls, cat, mkdir, rmdir, rm, touch, kill
- Foreground and background process execution
- Job control: jobs, fg, bg (with proper Ctrl+Z handling)
"""

import os
import sys
import subprocess
import shlex
import signal

class CommandHandler:
    """Handles built-in shell commands such as cd, pwd, exit, echo, clear, ls, cat, mkdir, rmdir, rm, touch, and kill."""

    @staticmethod
    def cd(directory):
        """Changes the current working directory."""
        try:
            os.chdir(directory)
        except FileNotFoundError:
            print(f"cd: {directory}: No such file or directory")
        except Exception as e:
            print(f"cd: {str(e)}")

    @staticmethod
    def pwd():
        """Prints the current working directory."""
        print(os.getcwd())

    @staticmethod
    def exit_shell():
        """Exits the shell."""
        print("Exiting shell...")
        sys.exit(0)

    @staticmethod
    def echo(text):
        """Prints the provided text to the terminal."""
        print(text)

    @staticmethod
    def clear():
        """Clears the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    @staticmethod
    def ls():
        """Lists the files in the current directory."""
        for item in os.listdir(os.getcwd()):
            print(item)

    @staticmethod
    def cat(filename):
        """Displays the contents of a file."""
        try:
            with open(filename, 'r') as file:
                print(file.read())
        except FileNotFoundError:
            print(f"cat: {filename}: No such file")
        except Exception as e:
            print(f"cat: {str(e)}")

    @staticmethod
    def mkdir(directory):
        """Creates a new directory."""
        try:
            os.mkdir(directory)
        except FileExistsError:
            print(f"mkdir: cannot create directory '{directory}': File exists")
        except Exception as e:
            print(f"mkdir: {str(e)}")

    @staticmethod
    def rmdir(directory):
        """Removes an empty directory."""
        try:
            os.rmdir(directory)
        except FileNotFoundError:
            print(f"rmdir: failed to remove '{directory}': No such directory")
        except OSError:
            print(f"rmdir: failed to remove '{directory}': Directory not empty")
        except Exception as e:
            print(f"rmdir: {str(e)}")

    @staticmethod
    def rm(filename):
        """Removes a file."""
        try:
            os.remove(filename)
        except FileNotFoundError:
            print(f"rm: cannot remove '{filename}': No such file")
        except IsADirectoryError:
            print(f"rm: cannot remove '{filename}': Is a directory")
        except Exception as e:
            print(f"rm: {str(e)}")

    @staticmethod
    def touch(filename):
        """Creates an empty file or updates its timestamp."""
        try:
            with open(filename, 'a'):
                os.utime(filename, None)
        except Exception as e:
            print(f"touch: {str(e)}")

    @staticmethod
    def kill(pid):
        """Terminates a process by its Process ID (PID)."""
        try:
            os.kill(int(pid), 9)
        except ProcessLookupError:
            print(f"kill: No such process: {pid}")
        except Exception as e:
            print(f"kill: {str(e)}")

class ProcessManager:
    """Manages foreground and background process execution, including job control."""

    background_jobs = {}
    job_id = 1

    @staticmethod
    def execute(command):
        """Executes a system command in the foreground."""
        try:
            args = shlex.split(command)
            if not args:
                return
            if CommandHandler.__dict__.get(args[0]):
                getattr(CommandHandler, args[0])(*args[1:])
                return
            process = subprocess.Popen(args)
            process.wait()
        except Exception as e:
            print(f"Error executing command: {str(e)}")

    @staticmethod
    def execute_background(command):
        """Executes a command in the background and tracks it."""
        try:
            args = shlex.split(command)
            process = subprocess.Popen(args)
            ProcessManager.background_jobs[ProcessManager.job_id] = process
            print(f"[{ProcessManager.job_id}] {process.pid}")
            ProcessManager.job_id += 1
        except Exception as e:
            print(f"Error executing background command: {str(e)}")

    @staticmethod
    def list_jobs():
        """Lists all background jobs."""
        if not ProcessManager.background_jobs:
            print("No background jobs.")
            return
        for job_id, process in ProcessManager.background_jobs.items():
            if process.poll() is None:  # Check if still running
                print(f"[{job_id}] Running {process.pid}")
            else:
                print(f"[{job_id}] Completed {process.pid}")

    @staticmethod
    def bring_to_foreground(job_id):
        """Brings a background job to the foreground."""
        job_id = int(job_id)
        if job_id in ProcessManager.background_jobs:
            process = ProcessManager.background_jobs.pop(job_id)
            process.wait()
        else:
            print(f"fg: Job {job_id} not found")

    @staticmethod
    def resume_in_background(job_id):
        """Resumes a stopped job in the background."""
        job_id = int(job_id)
        if job_id in ProcessManager.background_jobs:
            process = ProcessManager.background_jobs[job_id]
            os.kill(process.pid, signal.SIGCONT)  # Resume process
            print(f"[{job_id}] Resumed {process.pid}")
        else:
            print(f"bg: Job {job_id} not found")

def handle_sigtstp(signum, frame):
    """Handles Ctrl+Z to properly stop foreground jobs."""
    print("\nCtrl+Z detected. Use 'fg' or 'bg' to manage jobs.")

class ShellCore:
    """Main shell loop that interacts with the user and processes commands."""

    @staticmethod
    def run():
        # Ignore Ctrl+Z so shell does not stop itself
        signal.signal(signal.SIGTSTP, handle_sigtstp)

        while True:
            try:
                user_input = input("myshell> ").strip()
                if not user_input:
                    continue

                if user_input.endswith("&"):
                    ProcessManager.execute_background(user_input[:-1].strip())
                elif user_input.startswith("jobs"):
                    ProcessManager.list_jobs()
                elif user_input.startswith("fg"):
                    _, job_id = user_input.split()
                    ProcessManager.bring_to_foreground(job_id)
                elif user_input.startswith("bg"):
                    _, job_id = user_input.split()
                    ProcessManager.resume_in_background(job_id)
                else:
                    ProcessManager.execute(user_input)

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit the shell.")
            except EOFError:
                print("\nExiting shell...")
                break

if __name__ == "__main__":
    ShellCore.run()
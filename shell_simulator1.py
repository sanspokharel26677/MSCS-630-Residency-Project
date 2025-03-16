"""
Unix-like Shell Simulation

This script implements a simple Unix-like shell that supports built-in commands, process management, 
and job control. The shell allows users to execute commands, manage foreground and background 
processes, and handle job control commands.

Features:
- Built-in commands: cd, pwd, exit, echo, clear, ls, cat, mkdir, rmdir, rm, touch, kill
- Foreground and background process execution
- Job control: jobs, fg, bg
"""

import os
import sys
import subprocess
import shlex

class CommandHandler:
    """
    Handles built-in shell commands such as cd, pwd, exit, echo, clear, ls, cat, mkdir, rmdir, rm, touch, and kill.
    """
    
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
    
    @staticmethod
    def execute_builtin(command, args):
        """Executes a built-in command if it exists."""
        builtins = {
            "cd": CommandHandler.cd,
            "pwd": CommandHandler.pwd,
            "exit": CommandHandler.exit_shell,
            "echo": CommandHandler.echo,
            "clear": CommandHandler.clear,
            "ls": CommandHandler.ls,
            "cat": CommandHandler.cat,
            "mkdir": CommandHandler.mkdir,
            "rmdir": CommandHandler.rmdir,
            "rm": CommandHandler.rm,
            "touch": CommandHandler.touch,
            "kill": CommandHandler.kill,
        }
        if command in builtins:
            builtins[command](*args)
            return True
        return False

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
            if CommandHandler.execute_builtin(args[0], args[1:]):
                return
            process = subprocess.Popen(args)
            process.wait()
        except Exception as e:
            print(f"Error executing command: {str(e)}")

class ShellCore:
    """Main shell loop that interacts with the user and processes commands."""
    
    @staticmethod
    def run():
        while True:
            try:
                user_input = input("momolover> ").strip()
                if not user_input:
                    continue
                ProcessManager.execute(user_input)
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit the shell.")
            except EOFError:
                print("\nExiting shell...")
                break

if __name__ == "__main__":
    ShellCore.run()
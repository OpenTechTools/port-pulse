import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import multiprocessing
import threading
from ..core.config import MONITOR_REFRESH_RATE, UI_UPDATE_INTERVAL, MAX_LOG_LINES_IN_UI
from ..core.logger import read_latest_logs, log_event
from ..core.process_registry import ProcessRegistry
from ..core.process_manager import ProcessCreator, ProcessTerminator, send_message_to_process
from ..core.message_handler import MessageQueue

# Custom colors and styles
BG_COLOR = "#f0f4f8"  # Light blue-gray background
ACCENT_COLOR = "#4a90e2"  # Blue accent for buttons and highlights
TEXT_COLOR = "#333333"  # Dark gray for text
SUCCESS_COLOR = "#2ecc71"  # Green for success indicators
ERROR_COLOR = "#e74c3c"  # Red for error indicators

class DashboardUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PortPulse Dashboard")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("800x600")  # Set a reasonable initial size

        self.registry = ProcessRegistry()
        self.creator = ProcessCreator()
        self.message_queue = MessageQueue()
        self.terminator = ProcessTerminator()
        
        # Main frame with padding
        self.main_frame = ttk.Frame(self.root, padding="20", style="Main.TFrame")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure style
        self._setup_styles()

        # Notebook for tabbed interface
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tab 1: Process Status
        self.process_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.process_tab, text="Process Status")
        self.setup_process_table()

        # Tab 2: Logs
        self.logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_tab, text="Logs")
        self.setup_logs_display()

        # Tab 3: Controls
        self.control_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.control_tab, text="Controls")
        self.setup_control_panel()

        # Start periodic updates
        self.update_ui()

    def _setup_styles(self):
        """Configure custom styles for a beautiful UI."""
        style = ttk.Style()
        style.theme_use("clam")  # Use a modern theme
        style.configure("Main.TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Helvetica", 10))
        style.configure("TButton", background=ACCENT_COLOR, foreground="white", font=("Helvetica", 10, "bold"))
        style.map("TButton",
                  background=[("active", "#357abd")],
                  foreground=[("active", "white")])
        style.configure("Treeview", background=BG_COLOR, fieldbackground=BG_COLOR, foreground=TEXT_COLOR)
        style.configure("Treeview.Heading", background=ACCENT_COLOR, foreground="white")
        style.configure("TNotebook.Tab", background=BG_COLOR, foreground=TEXT_COLOR)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT_COLOR)],
                  foreground=[("selected", "white")])

    def setup_process_table(self):
        """Set up the process status table with a stop button."""
        process_frame = ttk.LabelFrame(self.process_tab, text="Process Overview", padding="10", style="TLabel")
        process_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        columns = ("PID", "Port", "Role", "Status", "Last Message To")
        self.tree = ttk.Treeview(process_frame, columns=columns, show="headings", height=8, style="Treeview")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col != "Last Message To" else 150, anchor=tk.CENTER)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        stop_button = ttk.Button(process_frame, text="🛑 Stop Process", command=self.stop_process)
        stop_button.grid(row=1, column=0, pady=10)

    def check_process_alive(self, pid):
        """Check if a process is still running."""
        try:
            import os
            os.kill(int(pid), 0)
            return True
        except OSError:
            return False

    def stop_process(self):
        """Terminate the selected process in the table."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a process to terminate.", parent=self.root)
            return
        
        item = self.tree.item(selected_item)
        pid = int(item['values'][0])
        
        if not self.check_process_alive(pid):
            messagebox.showinfo("Info", f"Process PID {pid} is already terminated.", parent=self.root)
            return
        
        port = self.registry.get_port_by_pid(pid)
        if not port or port <= 0:
            messagebox.showerror("Error", f"No valid port found for PID {pid} in registry.", parent=self.root)
            return
        
        try:
            threading.Thread(target=self._terminate_process_thread, args=(pid, port), daemon=True).start()
            messagebox.showinfo("Success", f"Termination of PID {pid} initiated.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to terminate process: {e}", parent=self.root)
            log_event(f"Failed to terminate process PID {pid}: {e}", pid=pid, level="ERROR")

    def _terminate_process_thread(self, pid, port):
        """Helper method to terminate a process in a separate thread."""
        try:
            import os
            os.kill(pid, 15)
            self.terminator.terminate_process(None)
            self.creator.port_allocator.release_port(port)
            if str(pid) in self.registry.get_all_parents():
                self.registry.remove_parent_and_children(pid)
            else:
                self.registry.remove_process(port)
            print(f"Terminated process with PID {pid} and released port {port}")
            log_event(f"Terminated process via dashboard", pid=pid, port=port)
        except Exception as e:
            print(f"[ERROR] Failed to terminate process PID {pid}: {e}")
            log_event(f"Failed to terminate process PID {pid}: {e}", pid=pid, port=port, level="ERROR")

    def setup_logs_display(self):
        """Set up the logs display area."""
        logs_frame = ttk.LabelFrame(self.logs_tab, text="Recent Logs", padding="10", style="TLabel")
        logs_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.logs_text = scrolledtext.ScrolledText(logs_frame, width=80, height=15, wrap=tk.WORD, bg=BG_COLOR, fg=TEXT_COLOR)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        button_frame = ttk.Frame(logs_frame)
        button_frame.grid(row=1, column=0, pady=5)
        ttk.Button(button_frame, text="🔄 Refresh Logs", command=self.refresh_logs).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="🗑️ Clear Logs", command=self.clear_logs).grid(row=0, column=1, padx=5)

    def setup_control_panel(self):
        """Set up the control panel for creating processes and sending messages."""
        control_frame = ttk.LabelFrame(self.control_tab, text="Control Panel", padding="10", style="TLabel")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # Create Process Section
        ttk.Label(control_frame, text="Create Process").grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)
        ttk.Label(control_frame, text="Type:").grid(row=1, column=0, sticky=tk.E)
        self.process_type = tk.StringVar(value="parent")
        ttk.OptionMenu(control_frame, self.process_type, "parent", "parent", "child").grid(row=1, column=1, sticky=tk.W)

        ttk.Label(control_frame, text="Parents:").grid(row=2, column=0, sticky=tk.E)
        self.parent_count = tk.StringVar(value="1")
        ttk.Entry(control_frame, textvariable=self.parent_count, width=5).grid(row=2, column=1, sticky=tk.W)

        ttk.Label(control_frame, text="Children per Parent:").grid(row=3, column=0, sticky=tk.E)
        self.children_count = tk.StringVar(value="2")
        ttk.Entry(control_frame, textvariable=self.children_count, width=5).grid(row=3, column=1, sticky=tk.W)

        ttk.Button(control_frame, text="🚀 Create", command=self.create_process).grid(row=4, column=0, columnspan=2, pady=5)

        # Send Message to Port Section
        ttk.Label(control_frame, text="Send Message (by Port)").grid(row=5, column=0, columnspan=2, pady=5, sticky=tk.W)
        ttk.Label(control_frame, text="Target PID:").grid(row=6, column=0, sticky=tk.E)
        self.target_pid = tk.StringVar(value="")
        ttk.Entry(control_frame, textvariable=self.target_pid, width=10).grid(row=6, column=1, sticky=tk.W)

        ttk.Label(control_frame, text="Message:").grid(row=7, column=0, sticky=tk.E)
        self.message_content = tk.StringVar(value="Hello, Process!")
        ttk.Entry(control_frame, textvariable=self.message_content, width=20).grid(row=7, column=1, sticky=tk.W)

        ttk.Button(control_frame, text="📤 Send", command=self.send_message).grid(row=8, column=0, columnspan=2, pady=5)

        # Child to Child Message Section
        ttk.Label(control_frame, text="Child to Child Message").grid(row=9, column=0, columnspan=2, pady=5, sticky=tk.W)
        ttk.Label(control_frame, text="From PID:").grid(row=10, column=0, sticky=tk.E)
        self.from_pid = tk.StringVar(value="")
        ttk.Entry(control_frame, textvariable=self.from_pid, width=10).grid(row=10, column=1, sticky=tk.W)

        ttk.Label(control_frame, text="To PID:").grid(row=11, column=0, sticky=tk.E)
        self.to_pid = tk.StringVar(value="")
        ttk.Entry(control_frame, textvariable=self.to_pid, width=10).grid(row=11, column=1, sticky=tk.W)

        ttk.Label(control_frame, text="Message:").grid(row=12, column=0, sticky=tk.E)
        self.child_message_content = tk.StringVar(value="Hello, Child!")
        ttk.Entry(control_frame, textvariable=self.child_message_content, width=20).grid(row=12, column=1, sticky=tk.W)

        ttk.Button(control_frame, text="📨 Send Child", command=self.send_child_message).grid(row=13, column=0, columnspan=2, pady=5)

    def update_process_table(self):
        """Update the process status table using ProcessRegistry."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        parents = self.registry.get_all_parents()
        for pid, info in parents.items():
            status = "🟢" if self.check_process_alive(int(pid)) else "🔴"
            self.tree.insert("", tk.END, values=(pid, info["port"], "Parent", status, ""))

        children = self.registry.get_all_children()
        for pid, info in children.items():
            status = "🟢" if self.check_process_alive(int(pid)) else "🔴"
            last_msg_to = self._get_last_message_to(pid) or ""
            self.tree.insert("", tk.END, values=(pid, info["port"], "Child", status, last_msg_to))

    def _get_last_message_to(self, pid):
        """Placeholder to get last message target (enhance with actual logging if needed)"""
        return None  # Return actual last target PID if implemented

    def refresh_logs(self):
        """Refresh the logs display."""
        self.logs_text.delete(1.0, tk.END)
        logs = read_latest_logs(n=MAX_LOG_LINES_IN_UI)
        for log in logs:
            log_line = f"{log['timestamp']} | PID {log['pid']} | {log['level']}: {log['message']}\n"
            self.logs_text.insert(tk.END, log_line, (log['level'].lower() if log['level'] in ['INFO', 'ERROR'] else 'default'))
        self.logs_text.see(tk.END)

    def clear_logs(self):
        """Clear the logs display."""
        self.logs_text.delete(1.0, tk.END)

    def create_process(self):
        """Create a new process based on user input."""
        process_type = self.process_type.get()
        try:
            num_parents = int(self.parent_count.get()) if process_type == "parent" else 1
            num_children = int(self.children_count.get()) if process_type == "parent" else 0
            if num_parents < 1 or num_children < 0:
                raise ValueError("Invalid number of parents or children")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for parents and children.", parent=self.root)
            return
        
        threading.Thread(target=self._create_process_thread, args=(process_type, num_parents, num_children), daemon=True).start()

    def _create_process_thread(self, process_type, num_parents, num_children):
        """Helper method to create a process in a separate thread."""
        try:
            if process_type == "parent":
                print(f"🚀 Creating {num_parents} parent(s) with {num_children} child(ren) each...")
                self.creator.handler.test_p_process = num_parents
                self.creator.handler.test_c_process = num_children
                self.creator.create_parent_processes()
            elif process_type == "child":
                print("👶 Creating standalone child process...")
                port = self.creator.port_allocator.get_next_free_port()
                child = multiprocessing.Process(target=self.creator.child_handler, args=(1, port))
                child.start()
                self.creator.register_process(child, port)
        except Exception as e:
            print(f"[ERROR] Failed to create process: {e}")
            log_event(f"Failed to create process: {e}", level="ERROR")

    def send_message(self):
        """Send a message to the specified PID."""
        try:
            target_pid = int(self.target_pid.get())
            message = self.message_content.get()
            if not self.check_process_alive(target_pid):
                messagebox.showerror("Error", f"Process PID {target_pid} is not alive.", parent=self.root)
                return
            threading.Thread(target=self._send_message_thread, args=(target_pid, message), daemon=True).start()
        except ValueError:
            messagebox.showerror("Error", "Invalid PID number", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}", parent=self.root)
            log_event(f"Failed to send message to PID {target_pid}: {e}", pid=target_pid, level="ERROR")

    def _send_message_thread(self, target_pid, message):
        """Helper method to send a message in a separate thread."""
        print(f"📬 Sending: '{message}' to PID {target_pid}")
        try:
            success = send_message_to_process(target_pid, message)
            if success:
                log_event(f"Message sent via dashboard: {message}", pid=target_pid)
            else:
                log_event(f"Failed to send message to PID {target_pid}", pid=target_pid, level="ERROR")
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")
            log_event(f"Failed to send message to PID {target_pid}: {e}", pid=target_pid, level="ERROR")

    def send_child_message(self):
        """Send a message from one child to another."""
        try:
            from_pid = int(self.from_pid.get())
            to_pid = int(self.to_pid.get())
            message = self.child_message_content.get()
            if not self.check_process_alive(from_pid) or not self.check_process_alive(to_pid):
                messagebox.showerror("Error", "One or both PIDs are not alive.", parent=self.root)
                return
            threading.Thread(target=self._send_child_message_thread, args=(from_pid, to_pid, message), daemon=True).start()
        except ValueError:
            messagebox.showerror("Error", "Invalid PID number", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send child message: {e}", parent=self.root)
            log_event(f"Failed to send child message: {e}", level="ERROR")

    def _send_child_message_thread(self, from_pid, to_pid, message):
        """Helper method to send a child-to-child message in a separate thread."""
        print(f"📩 Sending: '{message}' from PID {from_pid} to PID {to_pid}")
        try:
            registry = ProcessRegistry()
            to_port = registry.get_port_by_pid(to_pid)
            if to_port:
                send_message_to_process(to_pid, message, sender_pid=from_pid)
                log_event(f"Child message sent from PID {from_pid} to PID {to_pid}: {message}", 
                         pid=from_pid, port=to_port)
            else:
                log_event(f"Failed to send child message: Invalid target PID {to_pid}", level="ERROR")
        except Exception as e:
            print(f"[ERROR] Failed to send child message: {e}")
            log_event(f"Failed to send child message to PID {to_pid}: {e}", pid=from_pid, level="ERROR")

    def cleanup(self):
        """Clean up processes on window close."""
        self.creator.terminate_event.set()
        self.creator.terminate_all()
        self.root.destroy()

    def update_ui(self):
        """Periodically update the UI."""
        self.update_process_table()
        self.refresh_logs()
        self.root.after(UI_UPDATE_INTERVAL, self.update_ui)

def launch_dashboard():
    """Launch the Tkinter dashboard."""
    root = tk.Tk()
    app = DashboardUI(root)
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    root.mainloop()

if __name__ == "__main__":
    launch_dashboard()
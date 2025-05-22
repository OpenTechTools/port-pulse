import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
from ..core.config import MONITOR_REFRESH_RATE, UI_UPDATE_INTERVAL, MAX_LOG_LINES_IN_UI
from ..core.monitor import ProcessMonitor
from ..core.logger import read_latest_logs
from ..core.message_handler import MessageQueue
from ..core.process_manager import ProcessCreator, ProcessTerminator

class DashboardUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PortPulse Dashboard")
        self.monitor = ProcessMonitor()
        self.creator = ProcessCreator()
        self.message_queue = MessageQueue()
        self.terminator = ProcessTerminator()
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Process Status Table
        self.setup_process_table()
        
        # Logs Display
        self.setup_logs_display()
        
        # Control Panel (Create Process, Send Message)
        self.setup_control_panel()
        
        # Start periodic updates
        self.update_ui()

    def setup_process_table(self):
        """Set up the process status table with a stop button."""
        process_frame = ttk.LabelFrame(self.main_frame, text="Process Status", padding="5")
        process_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Treeview for process table
        columns = ("PID", "Port", "Role", "Status")
        self.tree = ttk.Treeview(process_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for the treeview
        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Stop Process button
        ttk.Button(process_frame, text="Stop Process", command=self.stop_process).grid(row=1, column=0, pady=5)

    def stop_process(self):
        """Terminate the selected process in the table."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a process to terminate.")
            return
        
        # Get the PID of the selected process
        item = self.tree.item(selected_item)
        pid = int(item['values'][0])  # PID is the first column
        
        # Find the process in the monitor's tracked_processes
        process_info = next((proc for proc in self.monitor.tracked_processes if proc["pid"] == pid), None)
        if not process_info:
            messagebox.showerror("Error", "Process not found in monitor.")
            return
        
        if not process_info["alive"]:
            messagebox.showinfo("Info", "Process is already terminated.")
            return
        
        # Terminate the process
        try:
            import threading
            threading.Thread(target=self._terminate_process_thread, args=(pid, process_info["port"]), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to terminate process: {e}")

    def _terminate_process_thread(self, pid, port):
        """Helper method to terminate a process in a separate thread."""
        try:
            # Create a new ProcessTerminator instance for this operation
            terminator = ProcessTerminator()
            # Find the process in ProcessCreator's parent_processes or create a dummy process
            process = None
            for p in self.creator.parent_processes:
                if p.pid == pid:
                    process = p
                    break
            if not process:
                # If not a parent process, it might be a child; create a dummy process for termination
                import multiprocessing
                process = multiprocessing.Process(target=lambda: None)
                process.pid = pid
            
            terminator.terminate_process(process)
            # Release the port
            self.creator.port_allocator.release_port(port)
            print(f"Terminated process with PID {pid} and released port {port}")
        except Exception as e:
            print(f"[ERROR] Failed to terminate process PID {pid}: {e}")

    def setup_logs_display(self):
        """Set up the logs display area."""
        logs_frame = ttk.LabelFrame(self.main_frame, text="Recent Logs", padding="5")
        logs_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # ScrolledText for logs
        self.logs_text = scrolledtext.ScrolledText(logs_frame, width=80, height=10, wrap=tk.WORD)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons for logs
        button_frame = ttk.Frame(logs_frame)
        button_frame.grid(row=1, column=0, pady=5)
        ttk.Button(button_frame, text="Refresh Logs", command=self.refresh_logs).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Clear Logs", command=self.clear_logs).grid(row=0, column=1, padx=5)

    def setup_control_panel(self):
        """Set up the control panel for creating processes and sending messages."""
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="5")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Create Process Section
        ttk.Label(control_frame, text="Create Process").grid(row=0, column=0, columnspan=2, pady=2)
        ttk.Label(control_frame, text="Type:").grid(row=1, column=0, sticky=tk.E)
        self.process_type = tk.StringVar(value="parent")
        ttk.OptionMenu(control_frame, self.process_type, "parent", "parent", "child").grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(control_frame, text="Number of Parents:").grid(row=2, column=0, sticky=tk.E)
        self.parent_count = tk.StringVar(value="1")
        ttk.Entry(control_frame, textvariable=self.parent_count, width=5).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(control_frame, text="Children per Parent:").grid(row=3, column=0, sticky=tk.E)
        self.children_count = tk.StringVar(value="2")
        ttk.Entry(control_frame, textvariable=self.children_count, width=5).grid(row=3, column=1, sticky=tk.W)
        
        ttk.Button(control_frame, text="Create Process", command=self.create_process).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Send Message Section
        ttk.Label(control_frame, text="Send Message").grid(row=5, column=0, columnspan=2, pady=2)
        ttk.Label(control_frame, text="Target Port:").grid(row=6, column=0, sticky=tk.E)
        self.target_port = tk.StringVar(value="5000")
        ttk.Entry(control_frame, textvariable=self.target_port, width=5).grid(row=6, column=1, sticky=tk.W)
        
        ttk.Label(control_frame, text="Message:").grid(row=7, column=0, sticky=tk.E)
        self.message_content = tk.StringVar(value="Hello, Process!")
        ttk.Entry(control_frame, textvariable=self.message_content, width=20).grid(row=7, column=1, sticky=tk.W)
        
        ttk.Button(control_frame, text="Send Message", command=self.send_message).grid(row=8, column=0, columnspan=2, pady=5)

    def update_process_table(self):
        """Update the process status table."""
        self.monitor.refresh_status()
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Add updated process data
        for proc in self.monitor.tracked_processes:
            status = "🟢 ALIVE" if proc["alive"] else "🔴 DEAD"
            self.tree.insert("", tk.END, values=(proc["pid"], proc["port"], proc["role"], status))

    def refresh_logs(self):
        """Refresh the logs display."""
        self.logs_text.delete(1.0, tk.END)
        logs = read_latest_logs(n=MAX_LOG_LINES_IN_UI)
        for log in logs:
            log_line = f"{log['timestamp']} | PID {log['pid']} | {log['level']}: {log['message']}\n"
            self.logs_text.insert(tk.END, log_line)
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
        except ValueError:
            num_parents = 1
            num_children = 0
        
        # Run process creation in a separate thread to avoid blocking the UI
        import threading
        threading.Thread(target=self._create_process_thread, args=(process_type, num_parents, num_children), daemon=True).start()

    def _create_process_thread(self, process_type, num_parents, num_children):
        """Helper method to create a process in a separate thread."""
        if process_type == "parent":
            print(f"🚀 Creating {num_parents} parent(s) with {num_children} child(ren) each...")
            self.creator.handler.test_p_process = num_parents
            self.creator.handler.test_c_process = num_children
            self.creator.create_parent_processes()
        elif process_type == "child":
            print("👶 Creating standalone child process...")
            port = self.creator.port_allocator.get_next_free_port()
            self.creator.child_handler(child_id=1, port=port)

    def send_message(self):
        """Send a message to the specified port."""
        try:
            target_port = int(self.target_port.get())
            message = self.message_content.get()
            # Run message sending in a separate thread
            import threading
            threading.Thread(target=self._send_message_thread, args=(target_port, message), daemon=True).start()
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")

    def _send_message_thread(self, target_port, message):
        """Helper method to send a message in a separate thread."""
        print(f"📬 Sending: '{message}' to port {target_port}")
        try:
            asyncio.run(self.message_queue.send_message("127.0.0.1", target_port, message))
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")

    def update_ui(self):
        """Periodically update the UI."""
        self.update_process_table()
        self.refresh_logs()
        self.root.after(UI_UPDATE_INTERVAL, self.update_ui)

def launch_dashboard():
    """Launch the Tkinter dashboard."""
    root = tk.Tk()
    app = DashboardUI(root)
    root.mainloop()
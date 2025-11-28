# gui/main_window.py

import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
import sys 
from .worker import MonitorWorker # Import the new MonitorWorker

class IPCMainWindow:
    """
    Handles the GUI construction, user controls, and visualization 
    for the Real-Time Monitoring Tool.
    """
    def __init__(self, analyzer): # Takes an Analyzer, not a Scheduler
        self.analyzer = analyzer
        self.root = tk.Tk()
        self.root.title("Real-Time IPC Monitor (Tkinter)")
        self.root.geometry("1200x800")
        
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill='both', expand=True)
        
        self.control_frame = ttk.Frame(self.main_frame, width=350)
        self.control_frame.pack(side='left', fill='y', padx=15)
        
        self.vis_log_frame = ttk.Frame(self.main_frame)
        self.vis_log_frame.pack(side='right', fill='both', expand=True)
        
        self.monitor_thread = None       
        self.is_monitoring = False
        
        self.setup_control_panel()
        self.setup_visualization_log()

    def setup_control_panel(self):
        """Builds the widgets for control."""
        
        ttk.Label(self.control_frame, text="Monitoring Control", font=("Arial", 18, "bold")).pack(pady=10)
        
        ttk.Label(self.control_frame, text="Polling Interval (seconds):").pack(pady=5, anchor='w')
        self.interval_input = ttk.Entry(self.control_frame, width=20)
        self.interval_input.insert(0, "1.0") # Poll every 1 second
        self.interval_input.pack(pady=5, fill='x')
        
        # Combined Start/Stop Button
        self.toggle_button = ttk.Button(self.control_frame, text="▶️ Start Monitoring", command=self.toggle_monitoring)
        self.toggle_button.pack(pady=20, fill='x')
        
        ttk.Label(self.control_frame, text="--- Live System Analysis ---", font=("Arial", 10)).pack(pady=10)
        ttk.Label(self.control_frame, text="Tool inspects live system state (mocked data in this prototype).", wraplength=300).pack(pady=5)
        
    def setup_visualization_log(self):
        """Sets up the two-graph visualization area and log console."""
        
        self.graph_frame = ttk.Frame(self.vis_log_frame)
        self.graph_frame.pack(fill='x', expand=False, pady=5)
        
        # --- Left Graph: Throughput ---
        ttk.Label(self.graph_frame, text="Live Throughput", font=("Arial", 14)).pack(pady=5, side='left', fill='x', expand=True)
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 3))
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.graph_frame)
        self.canvas_widget1 = self.canvas1.get_tk_widget()
        self.canvas_widget1.pack(side='left', fill='both', expand=True, padx=5)
        
        # --- Right Graph: Contention Heatmap ---
        ttk.Label(self.graph_frame, text="Resource Contention", font=("Arial", 14)).pack(pady=5, side='right', fill='x', expand=True)
        self.fig2, self.ax2 = plt.subplots(figsize=(6, 3.5))
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.graph_frame)
        self.canvas_widget2 = self.canvas2.get_tk_widget()
        self.canvas_widget2.pack(side='right', fill='both', expand=True, padx=5)
        
        # Log Console
        ttk.Label(self.vis_log_frame, text="Live Event Stream:", font=("Arial", 14, "bold")).pack(pady=10, anchor='w')
        self.log_console = scrolledtext.ScrolledText(self.vis_log_frame, height=10, state='disabled', wrap=tk.WORD)
        self.log_console.pack(fill='both', expand=True, pady=5)
        self.log_console.tag_config('red', foreground='red')
        self.log_console.tag_config('orange', foreground='orange')
        self.log_console.tag_config('blue', foreground='blue')
        self.log_console.tag_config('black', foreground='black')

    def toggle_monitoring(self):
        """Starts or stops the monitoring worker thread."""
        if self.is_monitoring:
            # Stop the monitor
            if self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread.join()
            self.is_monitoring = False
            self.toggle_button.config(text="▶️ Start Monitoring")
            self.log_message("Monitoring stopped.", 'blue')
        else:
            # Start the monitor
            try:
                interval = float(self.interval_input.get())
            except ValueError:
                self.log_message("ERROR: Invalid interval.", 'red')
                return

            self.log_console.config(state='normal'); self.log_console.delete(1.0, tk.END); self.log_console.config(state='disabled')
            self.log_message(f"Monitoring started, polling every {interval}s...", 'blue')
            
            # Start the worker thread
            self.monitor_thread = MonitorWorker(
                analyzer=self.analyzer,
                polling_interval_sec=interval,
                callback=self.receive_live_event # Pass the reception method
            )
            self.monitor_thread.start()
            self.is_monitoring = True
            self.toggle_button.config(text="⏹️ Stop Monitoring")

    def receive_live_event(self, event):
        """Receives a single event and schedules the UI update."""
        
        # Tkinter only updates safely when a command is scheduled back to the main thread.
        self.root.after(0, lambda: self.process_event_and_update_ui(event))
    
    def process_event_and_update_ui(self, event):
        """Processes the received event and updates logs/graphs."""
        
        # 1. Log the event
        time_sec = event.get('time', 0)
        color_tag = 'black'
        prefix = f"Time {time_sec:.1f}s: [INFO] "
        
        if event['type'] == 'ERROR':
            color_tag = 'red'
            prefix = f"Time {time_sec:.1f}s: [❌ ERROR] "
        elif event['type'] == 'WARNING':
            color_tag = 'orange'
            prefix = f"Time {time_sec:.1f}s: [⚠️ WARNING] "
            
        log_entry = prefix + event['message']
        self.log_message(log_entry, color_tag)
        
        # 2. Update Graphs using the latest data from the Analyzer
        self.plot_throughput_and_contention()


    def plot_throughput_and_contention(self): 
        """Generates and displays both the throughput graph and the heatmap."""
        
        # Data is pulled directly from the analyzer's updated metrics
        data = self.analyzer.throughput_data
        contention_data = self.analyzer.get_contention_data()

        # --- Plot 1: Throughput (Cumulative Data Transfer) ---
        self.ax1.clear()
        if data['Time']:
            self.ax1.plot(data['Time'], data['Cumulative_Transferred'], color='blue', linewidth=2)
            self.ax1.set_title('Live Cumulative Throughput', fontsize=10)
            self.ax1.set_xlabel('Time (s)', fontsize=8)
            self.ax1.set_ylabel('Total Data', fontsize=8)
            self.ax1.tick_params(axis='both', which='major', labelsize=7)
            self.ax1.grid(True, linestyle='--', alpha=0.6)
        self.fig1.tight_layout()
        self.canvas1.draw()

        # --- Plot 2: Contention Heatmap (Total Wait Ticks per Resource) ---
        self.ax2.clear()
        if contention_data['Names']:
            names = contention_data['Names']
            wait_ticks = contention_data['Wait_Ticks']
            
            self.ax2.bar(names, wait_ticks, color=['#FF5733', '#FFC300', '#33FFB5', '#338DFF']) 
            self.ax2.set_title('Resource Wait/Contention', fontsize=10)
            self.ax2.set_ylabel('Mock Wait Ticks', fontsize=8)
            self.ax2.tick_params(axis='x', rotation=45, labelsize=7)
            self.ax2.tick_params(axis='y', labelsize=7)
        
        self.fig2.tight_layout()
        self.canvas2.draw()

    def log_message(self, message, color_tag='black'):
        """Appends a colored message to the log console."""
        self.log_console.config(state='normal')
        self.log_console.insert(tk.END, message + '\n', color_tag)
        self.log_console.see(tk.END)
        self.log_console.config(state='disabled')

    def start_loop(self):
        """Starts the Tkinter main event loop."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Handles graceful exit, stopping the worker thread."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.stop()
            self.monitor_thread.join()
        self.root.destroy()
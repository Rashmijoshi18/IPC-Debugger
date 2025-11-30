import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .worker import MonitorWorker


class IPCMainWindow:
    """
    Handles the GUI construction, user controls, and visualization 
    for the Real-Time Monitoring Tool.
    """
    def __init__(self, analyzer): 
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

    # ----------------------------------------------------

    def setup_control_panel(self):
        ttk.Label(self.control_frame, text="Monitoring Control", font=("Arial", 18, "bold")).pack(pady=10)
        
        ttk.Label(self.control_frame, text="Polling Interval (seconds):").pack(pady=5, anchor='w')
        self.interval_input = ttk.Entry(self.control_frame, width=20)
        self.interval_input.insert(0, "1.0")
        self.interval_input.pack(pady=5, fill='x')
        
        self.toggle_button = ttk.Button(self.control_frame, text="▶️ Start Monitoring", command=self.toggle_monitoring)
        self.toggle_button.pack(pady=20, fill='x')
        
        ttk.Label(self.control_frame, text="--- Live System Analysis ---", font=("Arial", 10)).pack(pady=10)
        ttk.Label(self.control_frame, text="Tool inspects live system state (mocked data in this prototype).",
                  wraplength=300).pack(pady=5)

    # ----------------------------------------------------

    def setup_visualization_log(self):
        self.graph_frame = ttk.Frame(self.vis_log_frame)
        self.graph_frame.pack(fill='x', expand=False, pady=5)
        
        # LEFT GRAPH (same as before)
        ttk.Label(self.graph_frame, text="Live Throughput", font=("Arial", 14)).pack(
            pady=5, side='left', fill='x', expand=True)
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 3))
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.graph_frame)
        self.canvas_widget1 = self.canvas1.get_tk_widget()
        self.canvas_widget1.pack(side='left', fill='both', expand=True, padx=5)
        
        # RIGHT GRAPH (same as before)
        ttk.Label(self.graph_frame, text="Resource Contention", font=("Arial", 14)).pack(
            pady=5, side='right', fill='x', expand=True)
        self.fig2, self.ax2 = plt.subplots(figsize=(6, 3.5))
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.graph_frame)
        self.canvas_widget2 = self.canvas2.get_tk_widget()
        self.canvas_widget2.pack(side='right', fill='both', expand=True, padx=5)
        
        # LOG console (unchanged)
        ttk.Label(self.vis_log_frame, text="Live Event Stream:", font=("Arial", 14, "bold")).pack(pady=10, anchor='w')
        self.log_console = scrolledtext.ScrolledText(self.vis_log_frame, height=10, state='disabled', wrap=tk.WORD)
        self.log_console.pack(fill='both', expand=True, pady=5)

        # Coloring tags
        self.log_console.tag_config('red', foreground='red')
        self.log_console.tag_config('orange', foreground='orange')
        self.log_console.tag_config('blue', foreground='blue')
        self.log_console.tag_config('black', foreground='black')

    # ----------------------------------------------------

    def toggle_monitoring(self):
        if self.is_monitoring:
            if self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread.join()

            self.is_monitoring = False
            self.toggle_button.config(text="▶️ Start Monitoring")
            self.log_message("Monitoring stopped.", 'blue')
            return

        try:
            interval = float(self.interval_input.get())
        except ValueError:
            self.log_message("ERROR: Invalid interval.", 'red')
            return

        # Clear logs
        self.log_console.config(state='normal')
        self.log_console.delete(1.0, tk.END)
        self.log_console.config(state='disabled')

        self.log_message(f"Monitoring started, polling every {interval}s...", 'blue')

        # Start worker
        self.monitor_thread = MonitorWorker(
            analyzer=self.analyzer,
            polling_interval_sec=interval,
            callback=self.receive_live_event
        )
        self.monitor_thread.start()

        self.is_monitoring = True
        self.toggle_button.config(text="⏹️ Stop Monitoring")

    # ----------------------------------------------------

    def receive_live_event(self, event):
        self.root.after(0, lambda: self.process_event_and_update_ui(event))

    def process_event_and_update_ui(self, event):
        time_sec = event.get('time', 0)
        event_type = event.get('type', 'INFO')
        message = event.get('message', '')

        prefix = f"Time {time_sec:.1f}s: "
        color_tag = 'black'

        if event_type == 'ERROR':
            prefix += "[❌ ERROR] "
            color_tag = 'red'
        elif event_type == 'WARNING':
            prefix += "[⚠️ WARNING] "
            color_tag = 'orange'
        else:
            prefix += "[INFO] "

        self.log_message(prefix + message, color_tag)

        # SAME graph behavior as before
        self.plot_throughput_and_contention()

    # ----------------------------------------------------

    def plot_throughput_and_contention(self): 
        data = self.analyzer.throughput_data
        contention_data = self.analyzer.get_contention_data()

        # SAME EXACT PLOTTING CODE — NO CHANGE
        self.ax1.clear()
        if data['Time']:
            self.ax1.plot(data['Time'], data['Cumulative_Transferred'], color='blue', linewidth=2)
            self.ax1.set_title('Live Cumulative Throughput', fontsize=10)
            self.ax1.set_xlabel('Time (s)', fontsize=8)
            self.ax1.set_ylabel('Total Data', fontsize=8)
            self.ax1.grid(True, linestyle='--', alpha=0.6)

        self.fig1.tight_layout()
        self.canvas1.draw()

        self.ax2.clear()
        if contention_data['Names']:
            self.ax2.bar(
                contention_data['Names'],
                contention_data['Wait_Ticks'],
                color=['#FF5733', '#FFC300', '#33FFB5', '#338DFF']
            )
            self.ax2.set_title('Resource Wait/Contention', fontsize=10)
            self.ax2.set_ylabel('Mock Wait Ticks', fontsize=8)
            self.ax2.tick_params(axis='x', rotation=45, labelsize=7)

        self.fig2.tight_layout()
        self.canvas2.draw()

    # ----------------------------------------------------

    def log_message(self, message, color_tag='black'):
        self.log_console.config(state='normal')
        self.log_console.insert(tk.END, message + '\n', color_tag)
        self.log_console.see(tk.END)
        self.log_console.config(state='disabled')

    # ----------------------------------------------------

    def start_loop(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.stop()
            self.monitor_thread.join()
        self.root.destroy()

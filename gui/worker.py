# gui/worker.py

import threading
import time

class MonitorWorker(threading.Thread):
    """
    Runs continuous analysis on live system data (mocked in core/ for now) 
    and sends results back to the GUI every second.
    """
    def __init__(self, analyzer, polling_interval_sec, callback):
        super().__init__()
        self.analyzer = analyzer
        self.polling_interval_sec = polling_interval_sec
        self.callback = callback 
        self.stop_event = threading.Event()

    def run(self):
        """Continuously analyzes the system state and reports events."""
        
        while not self.stop_event.is_set():
            # 1. Analyze the current system state (calls core/realtime_analyzer.py)
            self.analyzer.analyze_system_state()
            
            # 2. Get the latest event (WARNING/ERROR/INFO)
            # We assume the analyzer updates its events list with the latest info.
            current_events = self.analyzer.events[-1:] 
            
            # 3. Pass the latest event and metric data back to the GUI thread
            if current_events:
                 self.callback(current_events[0]) # Pass event for logging

            # 4. Wait for the specified interval before polling again
            time.sleep(self.polling_interval_sec)

    def stop(self):
        """Sets the stop event flag to gracefully exit the monitoring loop."""
        self.stop_event.set()
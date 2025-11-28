# core/realtime_analyzer.py

from .system_inspector import monitor_resource_contention_mock
import time
import random
from collections import defaultdict

class RealTimeAnalyzer:
    """Applies IPC analysis algorithms (Deadlock, Bottleneck) to live system data."""
    def __init__(self):
        self.total_seconds_monitored = 0
        self.cumulative_transferred = 0
        self.throughput_data = {'Time': [], 'Cumulative_Transferred': []}
        self.events = []
        self.last_contention_data = {}
        self.last_analysis_time = time.time()
        self.monitoring_active = False

    def analyze_system_state(self):
        """Polls live data and runs analysis algorithms."""
        
        # Calculate time passed since last analysis (using a fixed 1s interval for clean plotting)
        time_delta = 1.0 
        self.total_seconds_monitored += time_delta
        self.last_analysis_time = time.time() # Update the last analysis time

        # 1. Get Live Resource Data
        live_data = monitor_resource_contention_mock()
        self.last_contention_data = live_data['contention']
        
        # 2. Update Throughput Metrics
        throughput_increase = live_data['throughput_rate']
        self.cumulative_transferred += throughput_increase
        self.throughput_data['Time'].append(self.total_seconds_monitored)
        self.throughput_data['Cumulative_Transferred'].append(self.cumulative_transferred)
        
        current_event = None

        # 3. Analyze for Bottlenecks (Contention Check)
        for resource_name, data in live_data['contention'].items(): 
            wait_time = data['Total_Wait_Time']
            
            if wait_time > 60: 
                # CRITICAL SEVERITY: High, sustained contention
                message = f"HIGH CONTENTION: The resource '{resource_name}' is severely contested (Wait Time > 60)."
                # If an ERROR is found, prioritize logging it
                if current_event is None or current_event['type'] != 'ERROR':
                     current_event = {'time': self.total_seconds_monitored, 'type': 'ERROR', 'message': message}
            elif wait_time > 30:
                 # WARNING SEVERITY: Significant contention
                 message = f"CONTENTION WARNING: Resource '{resource_name}' wait time exceeds 30 units."
                 if current_event is None: # Only log WARNING if no ERROR was found
                     current_event = {'time': self.total_seconds_monitored, 'type': 'WARNING', 'message': message}


        # 4. Deadlock Check (Context-Aware MOCKED)
        if 15.0 < self.total_seconds_monitored < 17.0 and random.random() > 0.5 and current_event is None:
            
            # Define specific resource pairs for a contextual deadlock warning
            deadlock_pairs = [
                ('Lock-A (UserDB)', 'Lock-X (Cache_Write)'),
                ('Socket (192.168.1.10:5432)', 'Lock-A (UserDB)'),
                ('Pipe-B (Input_Feed)', 'Lock-X (Cache_Write)')
            ]
            resource1, resource2 = random.choice(deadlock_pairs)

            current_event = {'time': self.total_seconds_monitored, 'type': 'ERROR', 
                             'message': f'DEADLOCK (MOCKED): Circular wait detected between {resource1} and {resource2}.'}
        
        # If an event occurred, add it to the cumulative list
        if current_event:
            self.events.append(current_event)
        
        # Return the latest event or None for the GUI to log
        return current_event

    def get_contention_data(self):
        """Translates the analysis data for the GUI's Matplotlib graph."""
        
        contention_data = self.last_contention_data
        
        # Ensure we return data structured for the Matplotlib bar chart (Names and Wait_Ticks)
        formatted_data = {
            'Names': list(contention_data.keys()),
            'Wait_Ticks': [d['Total_Wait_Time'] for d in contention_data.values()]
        }
        return formatted_data
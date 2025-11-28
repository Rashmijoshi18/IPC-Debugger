# main.py

import sys
# Import the GUI module container
from gui import main_window 
# Import the new RealTimeAnalyzer
from core.realtime_analyzer import RealTimeAnalyzer 

# NOTE: The old simulation models (SimulatedProcess, Lock, etc.) are NOT imported here 
# because they are no longer used in the Real-Time Monitoring architecture.

def main():
    """
    Initializes the RealTimeAnalyzer and launches the MonitorWorker thread via the GUI.
    """
    
    # 1. 🧠 Analyzer Initialization
    # This class replaces the old Scheduler. It contains the logic to poll system data.
    analyzer = RealTimeAnalyzer()

    # 2. 🖥️ GUI Initialization and Execution (Tkinter)
    # Access the class via the module prefix (main_window.)
    window = main_window.IPCMainWindow(analyzer) 
    
    # Start the Tkinter event loop
    window.start_loop() 

if __name__ == "__main__":
    
    # CRITICAL: Before running this, ensure your core/ directory contains:
    # 1. realtime_analyzer.py
    # 2. system_inspector.py
    # AND that you have installed the psutil and matplotlib libraries.
    
    # We attempt a basic check for the core file existence (though imports handle this)
    try:
        from core import system_inspector
        from core import realtime_analyzer
    except ImportError as e:
        print(f"FATAL ERROR: Could not find core module file. Ensure core/system_inspector.py and core/realtime_analyzer.py exist.")
        print(f"Details: {e}")
        sys.exit(1)
        
    main()
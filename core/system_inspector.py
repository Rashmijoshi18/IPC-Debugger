# core/system_inspector.py

import psutil
import time
import random
from collections import defaultdict

# --- Helper Function: Get PID of a common running process for mocking ---
def _get_common_pid():
    """Returns the PID of a common application (like a browser) for mocking purposes."""
    for proc in psutil.process_iter(['pid', 'name']):
        if 'chrome' in proc.info['name'].lower() or 'firefox' in proc.info['name'].lower() or 'explorer' in proc.info['name'].lower():
            return proc.info['pid']
    return 1 # Fallback to PID 1 if no common app is found

def get_all_running_processes():
    """Retrieves and lists basic information for all running processes using psutil."""
    process_list = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            process_list.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'cpu_usage': proc.info['cpu_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return process_list

def get_live_network_connections():
    """Retrieves live network connection data (IP/Port) using psutil."""
    network_data = {}
    
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.raddr:
            local_addr = f"{conn.laddr.ip}:{conn.laddr.port}"
            remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}"
            resource_name = f"Socket ({local_addr} <-> {remote_addr})"
            
            if random.random() > 0.8: 
                 wait_time = random.randint(40, 90)
            else:
                 wait_time = 0
                 
            if wait_time > 0:
                 network_data[resource_name] = {
                    'Total_Wait_Time': wait_time,
                    'PID': conn.pid if conn.pid else 'N/A'
                }
            
    return network_data


def monitor_resource_contention_mock(target_pid=None):
    """
    Mocks IPC contention data and combines it with live network data (IP/Port).
    The IPC resources are named based on live PIDs for context.
    """
    
    contention_data = defaultdict(lambda: {'Total_Wait_Time': 0})
    
    # Get PIDs for contextual mocking
    mock_pid_reader = _get_common_pid()
    mock_pid_writer = mock_pid_reader + 1 # Simulate two related PIDs

    # --- 1. Live Network Contention Data (IP/Port) ---
    live_net_data = get_live_network_connections()
    for name, data in live_net_data.items():
        contention_data[name] = {'Total_Wait_Time': data['Total_Wait_Time']}

    # --- 2. Mock Local IPC Contention Data (Contextual Names) ---
    
    if random.random() < 0.9:
        # Resource: Shared Memory Lock
        contention_data['Lock-A (SHM_Buffer)'] = {'Total_Wait_Time': random.randint(30, 80)}
    
    if random.random() < 0.7:
        # Resource: Pipe identified by the live PIDs using it
        # This is the most realistic way to name an unnamed pipe
        pipe_name = f"Pipe_Buffer (PID {mock_pid_reader} -> PID {mock_pid_writer})"
        contention_data[pipe_name] = {'Total_Wait_Time': random.randint(10, 50)}
        
    if random.random() < 0.5:
        # Resource: Message Queue
        contention_data['MsgQueue-System-Log'] = {'Total_Wait_Time': random.randint(5, 20)}

    # Mock Throughput Data
    throughput_rate = random.uniform(5.0, 15.0)

    return {
        'contention': contention_data,
        'throughput_rate': throughput_rate
    }
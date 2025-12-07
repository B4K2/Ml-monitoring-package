import threading
import time
from datetime import datetime
from .client import APIClient
from .system import get_system_info
from .logger import BackgroundWorker # <--- Import this

# Global State
_client = None
_worker = None # <--- New global variable
_run_id = None
_step = 0 # Track global step counter

def init(api_key: str, project_id: str, run_name: str = None, config: dict = {}):
    global _client, _worker, _run_id, _step
    
    _step = 0
    _client = APIClient(api_key)
    
    # 1. Send Static Info & Start Run (Synchronous)
    sys_info = get_system_info()
    print("Connecting to ML Monitor Server...")
    response = _client.start_run(project_id, run_name, config, sys_info)
    
    if response:
        _run_id = response['run_id']
        print(f"Run Started! ID: {_run_id}")
        
        # 2. Start Background Worker
        _worker = BackgroundWorker(_client, _run_id)
        _worker.start()
    else:
        print("Failed to start run. Monitoring disabled.")

def log(metrics: dict, step: int = None):
    """
    User calls this: monitor.log({"loss": 0.5})
    """
    global _worker, _step
    
    if not _worker or not _worker.is_alive():
        return # Not initialized
    
    # Handle Step Auto-increment
    if step is not None:
        _step = step
    else:
        _step += 1

    timestamp = datetime.now().isoformat()
    
    for name, value in metrics.items():
        # Put into queue (Instant, no API call here)
        _worker.log({
            "name": name,
            "value": float(value),
            "step": _step,
            "timestamp": timestamp
        })

def finish(status="completed"):
    global _client, _worker, _run_id
    
    if _worker:
        print("Finishing run, uploading remaining logs...")
        _worker.stop() # This flushes the queue and kills the thread
        _worker = None
        
    if _client and _run_id:
        _client.finish_run(_run_id, status)
        print(f"Run finished with status: {status}")
        _run_id = None
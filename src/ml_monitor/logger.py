import threading
import time
import queue
from datetime import datetime, timezone
from .client import APIClient
from .system import get_system_metrics

class BackgroundWorker(threading.Thread):
    def __init__(self, client: APIClient, run_id: str, flush_interval=10):
        super().__init__()
        self.client = client
        self.run_id = run_id
        self.flush_interval = flush_interval # Send data every X seconds
        
        # Thread-safe queue for metrics
        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        
        # Timers
        self.last_flush = time.time()
        self.last_heartbeat = time.time()
        self.last_sys_stat = time.time()

    def log(self, metric_data):
        """Add a metric to the queue (Non-blocking)"""
        self.queue.put(metric_data)

    def run(self):
        """The main loop running in the background"""
        print("[ML Monitor] Background thread started.")
        
        while not self._stop_event.is_set():
            # 1. Collect System Metrics (every 5s)
            if time.time() - self.last_sys_stat > 5:
                self._collect_system_stats()
                self.last_sys_stat = time.time()

            # 2. Send Heartbeat (every 30s)
            if time.time() - self.last_heartbeat > 30:
                self.client.heartbeat(self.run_id)
                self.last_heartbeat = time.time()

            # 3. Flush Metrics (every 10s or if queue is big)
            if (time.time() - self.last_flush > self.flush_interval) or (self.queue.qsize() > 50):
                self._flush_queue()
                self.last_flush = time.time()

            # Sleep slightly to prevent CPU burning
            time.sleep(0.1)

        # Final flush when stopping
        self._flush_queue()

    def stop(self):
        """Signals the thread to stop and waits for it to finish"""
        self._stop_event.set()
        self.join() # Wait for thread to finish

    def _collect_system_stats(self):
        """Reads CPU/RAM and adds to queue"""
        try:
            stats = get_system_metrics()
            timestamp = datetime.now(timezone.utc).isoformat()
            
            for name, value in stats.items():
                self.queue.put({
                    "name": name,
                    "value": value,
                    "step": 0, # System stats don't really have steps
                    "timestamp": timestamp
                })
        except Exception:
            pass # Don't crash thread on sys stat fail

    def _flush_queue(self):
        """Takes everything from queue and sends it to API"""
        if self.queue.empty():
            return

        batch = []
        # Drain the queue
        while not self.queue.empty():
            try:
                batch.append(self.queue.get_nowait())
            except queue.Empty:
                break
        
        if batch:
            # Send batch to API
            self.client.log_metrics(self.run_id, batch)
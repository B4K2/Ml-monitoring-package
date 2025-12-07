import requests
from .config import Config

class APIClient:
    def __init__(self, api_key: str):
        self.config = Config()
        self.api_key = api_key
        self.session = requests.Session()
        # Set standard headers
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })

    def _post(self, endpoint: str, data: dict):
        """Helper to send POST requests with error handling."""
        url = f"{self.config.api_url}{endpoint}"
        try:
            response = self.session.post(url, json=data, timeout=5)
            response.raise_for_status() # Raise error for 400/500 codes
            return response.json()['payload']
        except requests.exceptions.RequestException as e:
            # We print error but DO NOT crash the training script
            print(f"[ML Monitor Error] Failed to contact server: {e}")
            return None

    def start_run(self, project_id: str, name: str = None, config: dict = {}, system_info: dict = {}):
        """Calls POST /experiments/runs/start/"""
        payload = {
            "project_id": project_id,
            "config": config,
            "system_info": system_info
        }
        if name:
            payload["name"] = name
            
        return self._post("/experiments/runs/start/", payload)

    def log_metrics(self, run_id: str, metrics: list):
        """Calls POST /experiments/metrics/log/"""
        payload = {
            "run_id": run_id,
            "metrics": metrics
        }
        return self._post("/experiments/metrics/log/", payload)

    def heartbeat(self, run_id: str):
        """Calls POST /experiments/runs/heartbeat/"""
        payload = {"run_id": run_id}
        return self._post("/experiments/runs/heartbeat/", payload)

    def finish_run(self, run_id: str, status: str):
        """Calls POST /experiments/runs/finish/"""
        payload = {
            "run_id": run_id,
            "status": status
        }
        return self._post("/experiments/runs/finish/", payload)
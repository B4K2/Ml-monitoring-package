import os

DEFAULT_API_URL = "http://127.0.0.1:8000/api"

class Config:
    def __init__(self):
        self.api_url = os.getenv("ML_MONITOR_URL", DEFAULT_API_URL)
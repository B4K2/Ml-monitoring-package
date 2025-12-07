import psutil
import platform

def get_system_info():
    """Static info sent once at start."""
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2)
    }

def get_system_metrics():
    """Dynamic info sent every few seconds."""
    return {
        "sys/cpu_percent": psutil.cpu_percent(),
        "sys/ram_percent": psutil.virtual_memory().percent,
        # We will add GPU support later (requires 'pynvml')
    }
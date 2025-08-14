"""
System information collection for benchmarking.

Collects OS, Python, CPU, memory, and GPU information for benchmark context.
"""

import os
import platform
from typing import Dict, Any, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False


def collect_system_info() -> Dict[str, Any]:
    """
    Collect comprehensive system information for benchmark context.
    
    Returns:
        Dictionary with system information including OS, Python version,
        CPU details, memory, and GPU information if available.
    """
    info = {}
    
    # OS and Python info
    info["os"] = platform.system()
    info["os_version"] = platform.version()
    info["python_version"] = platform.python_version()
    info["architecture"] = platform.architecture()[0]
    
    # CPU information
    info["cpu_model"] = platform.processor() or "Unknown"
    info["logical_cores"] = os.cpu_count() or "NA"
    
    if HAS_PSUTIL:
        try:
            info["physical_cores"] = psutil.cpu_count(logical=False) or "NA"
            # Get total system RAM
            memory = psutil.virtual_memory()
            info["ram_total_gb"] = round(memory.total / (1024**3), 2)
        except Exception:
            info["physical_cores"] = "NA"
            info["ram_total_gb"] = "NA"
    else:
        info["physical_cores"] = "NA"
        info["ram_total_gb"] = "NA"
    
    # GPU information
    gpu_info = _collect_gpu_info()
    info.update(gpu_info)
    
    # Torch information
    torch_info = _collect_torch_info()
    info.update(torch_info)
    
    return info


def _collect_gpu_info() -> Dict[str, Any]:
    """Collect GPU information if available."""
    gpu_info = {
        "gpu_models": "NA",
        "gpu_count": 0,
        "cuda_available": False
    }
    
    # Try to get NVIDIA GPU info via pynvml
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        
        if device_count > 0:
            gpu_models = []
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                gpu_models.append(name)
            
            gpu_info["gpu_models"] = ", ".join(gpu_models)
            gpu_info["gpu_count"] = device_count
        
    except (ImportError, Exception):
        # pynvml not available or failed
        pass
    
    return gpu_info


def _collect_torch_info() -> Dict[str, Any]:
    """Collect PyTorch information if available."""
    torch_info = {
        "torch_version": "NA",
        "cuda_available": False,
        "cuda_version": "NA"
    }
    
    try:
        import torch
        torch_info["torch_version"] = torch.__version__
        torch_info["cuda_available"] = torch.cuda.is_available()
        
        if torch.cuda.is_available():
            torch_info["cuda_version"] = torch.version.cuda or "NA"
            # Update GPU info from torch if we didn't get it from pynvml
            if torch_info.get("gpu_count", 0) == 0:
                torch_info["gpu_count"] = torch.cuda.device_count()
            if torch_info.get("gpu_models") == "NA" and torch.cuda.device_count() > 0:
                gpu_models = []
                for i in range(torch.cuda.device_count()):
                    gpu_models.append(torch.cuda.get_device_name(i))
                torch_info["gpu_models"] = ", ".join(gpu_models)
    
    except ImportError:
        # torch not available
        pass
    
    return torch_info
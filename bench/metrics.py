"""
Metrics collection for benchmarking.

Provides context managers for tracking peak RSS, VRAM usage, timing, energy,
and correctness verification.
"""

import time
import threading
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_PYNVML = True
except (ImportError, Exception):
    pynvml = None
    HAS_PYNVML = False

try:
    import torch
    HAS_TORCH = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
except ImportError:
    torch = None
    HAS_TORCH = False

try:
    import pyRAPL
    HAS_PYRAPL = True
except ImportError:
    pyRAPL = None
    HAS_PYRAPL = False


@contextmanager
def track_peak_rss(proc: Optional['psutil.Process'] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Track peak resident set size (RSS) during execution.
    
    Args:
        proc: Optional psutil.Process instance. If None, uses current process.
        
    Yields:
        Dictionary that will contain 'peak_rss_bytes', 'pre_rss_bytes', 
        and 'delta_rss_bytes' after context exit.
    """
    result = {"peak_rss_bytes": 0, "pre_rss_bytes": 0, "delta_rss_bytes": 0, "metadata": {}}
    
    if not HAS_PSUTIL:
        # Fallback: single snapshot at start/end
        result["metadata"]["method"] = "approx"
        try:
            import resource
            start_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB; on macOS it's in bytes
            if hasattr(resource, 'RUSAGE_SELF'):
                # Convert to bytes (Linux uses KB)
                start_rss = start_rss * 1024 if start_rss < 1000000 else start_rss
            result["pre_rss_bytes"] = start_rss
        except ImportError:
            start_rss = 0
            result["pre_rss_bytes"] = 0
        
        yield result
        
        try:
            import resource
            end_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            end_rss = end_rss * 1024 if end_rss < 1000000 else end_rss
            result["peak_rss_bytes"] = max(start_rss, end_rss)
            result["delta_rss_bytes"] = max(0, result["peak_rss_bytes"] - result["pre_rss_bytes"])
        except ImportError:
            result["peak_rss_bytes"] = 0
            result["delta_rss_bytes"] = 0
        return
    
    # Full tracking with psutil
    if proc is None:
        proc = psutil.Process()
    
    # Get baseline RSS before execution
    try:
        pre_rss = proc.memory_info().rss
        result["pre_rss_bytes"] = pre_rss
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pre_rss = 0
        result["pre_rss_bytes"] = 0
    
    max_rss = pre_rss
    stop_event = threading.Event()
    
    def rss_sampler():
        nonlocal max_rss
        while not stop_event.is_set():
            try:
                current_rss = proc.memory_info().rss
                max_rss = max(max_rss, current_rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            time.sleep(0.02)  # 20ms sampling interval
    
    # Start sampling thread
    sampler_thread = threading.Thread(target=rss_sampler, daemon=True)
    sampler_thread.start()
    
    try:
        yield result
    finally:
        stop_event.set()
        sampler_thread.join(timeout=1.0)  # Wait up to 1s for thread to finish
        result["peak_rss_bytes"] = max_rss
        result["delta_rss_bytes"] = max(0, max_rss - pre_rss)
        result["metadata"]["method"] = "sampled"


@contextmanager
def measure_vram_peak() -> Generator[Dict[str, Any], None, None]:
    """
    Measure peak VRAM usage during execution.
    
    Yields:
        Dictionary that will contain 'peak_vram_bytes' after context exit.
    """
    result = {"peak_vram_bytes": 0, "metadata": {"method": "NA"}}
    
    start_free = 0
    min_free = float('inf')
    device_id = 0
    
    if HAS_TORCH:
        try:
            if torch.cuda.device_count() > 0:
                start_free, _ = torch.cuda.mem_get_info(device_id)
                min_free = start_free
                result["metadata"]["method"] = "torch"
        except Exception:
            pass
    
    elif HAS_PYNVML:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            start_free = mem_info.free
            min_free = start_free
            result["metadata"]["method"] = "pynvml"
        except Exception:
            pass
    
    if start_free == 0:
        # No GPU monitoring available
        yield result
        return
    
    # Monitor during execution
    stop_event = threading.Event()
    
    def vram_sampler():
        nonlocal min_free
        while not stop_event.is_set():
            try:
                if HAS_TORCH and result["metadata"]["method"] == "torch":
                    free, _ = torch.cuda.mem_get_info(device_id)
                    min_free = min(min_free, free)
                elif HAS_PYNVML and result["metadata"]["method"] == "pynvml":
                    handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    min_free = min(min_free, mem_info.free)
                else:
                    break
            except Exception:
                break
            time.sleep(0.05)  # 50ms sampling interval
    
    sampler_thread = threading.Thread(target=vram_sampler, daemon=True)
    sampler_thread.start()
    
    try:
        yield result
    finally:
        stop_event.set()
        sampler_thread.join(timeout=1.0)
        
        # Calculate peak usage as difference from start
        if min_free < start_free:
            result["peak_vram_bytes"] = start_free - min_free
        else:
            result["peak_vram_bytes"] = 0


@contextmanager
def Timer() -> Generator[Dict[str, Any], None, None]:
    """
    Time execution with both wall time and CPU time.
    
    Yields:
        Dictionary that will contain 'wall_s' and 'cpu_s' after context exit.
    """
    result = {"wall_s": 0.0, "cpu_s": 0.0}
    
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    
    try:
        yield result
    finally:
        end_wall = time.perf_counter()
        end_cpu = time.process_time()
        
        result["wall_s"] = end_wall - start_wall
        result["cpu_s"] = end_cpu - start_cpu


@contextmanager 
def measure_energy() -> Generator[Dict[str, Any], None, None]:
    """
    Measure energy consumption during execution using pyRAPL (Linux only).
    
    Yields:
        Dictionary that will contain 'energy_uj' after context exit.
    """
    result = {"energy_uj": "NA", "metadata": {"method": "NA"}}
    
    if not HAS_PYRAPL:
        yield result
        return
    
    try:
        # Initialize RAPL
        pyRAPL.setup()
        
        # Start measurement
        meter = pyRAPL.Measurement('benchmark')
        meter.begin()
        
        try:
            yield result
        finally:
            meter.end()
            
            # Get total energy in microjoules
            total_energy = 0
            for domain in meter.result.domains:
                total_energy += getattr(meter.result, domain, 0)
            
            result["energy_uj"] = total_energy
            result["metadata"]["method"] = "pyRAPL"
            
    except Exception:
        # RAPL not available or failed
        yield result


def check_correctness(digest_a: bytes, digest_b: bytes) -> bool:
    """
    Check correctness by comparing digests.
    
    Args:
        digest_a: First digest to compare
        digest_b: Second digest to compare
        
    Returns:
        True if digests match, False otherwise
    """
    return digest_a == digest_b
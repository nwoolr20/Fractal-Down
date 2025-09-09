# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Trimble Device Integration Profiles

This module defines device-specific optimization profiles for Trimble hardware,
enabling Fractal-Down to operate optimally across the full range of Trimble devices.
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class TrimbleDevice(Enum):
    """Trimble device types with specific performance characteristics"""
    
    # Survey Controllers
    TSC7 = "tsc7"           # 2GB RAM, ARM processor
    TSC5 = "tsc5"           # 4GB RAM, Android
    
    # Construction Tablets  
    T100 = "t100"           # 4GB RAM, Windows 10
    T10 = "t10"             # 8GB RAM, Windows 11
    
    # Agricultural Displays
    FMX = "fmx"             # 2GB RAM, Linux
    CFX750 = "cfx750"       # 1GB RAM, embedded Linux
    
    # Fleet Management
    T7 = "t7"               # 1GB RAM, embedded
    PeopleNet = "peoplenet" # 2GB RAM, Android
    
    # GNSS Receivers
    R12 = "r12"             # 512MB RAM, embedded
    SPS986 = "sps986"       # 1GB RAM, embedded


@dataclass
class DeviceProfile:
    """Performance profile for a specific Trimble device"""
    
    device_type: TrimbleDevice
    total_memory_mb: int
    available_memory_mb: int
    cpu_cores: int
    storage_gb: int
    
    # Fractal-Down optimization settings
    recommended_memory_limit_mb: int
    max_concurrent_tasks: int
    priority_levels: int
    cache_size_mb: int
    
    # Device-specific capabilities
    supports_real_time: bool
    supports_complex_calculations: bool
    typical_use_cases: List[str]


# Device profile configurations optimized for Fractal-Down
TRIMBLE_DEVICE_PROFILES: Dict[TrimbleDevice, DeviceProfile] = {
    
    TrimbleDevice.TSC7: DeviceProfile(
        device_type=TrimbleDevice.TSC7,
        total_memory_mb=2048,
        available_memory_mb=1600,  # Reserve for Android OS
        cpu_cores=4,
        storage_gb=32,
        
        # Conservative settings for 2GB device
        recommended_memory_limit_mb=1400,
        max_concurrent_tasks=3,
        priority_levels=4,
        cache_size_mb=150,
        
        supports_real_time=True,
        supports_complex_calculations=False,  # Limited by memory
        typical_use_cases=[
            "real_time_positioning",
            "coordinate_transformation", 
            "simple_point_processing",
            "data_collection"
        ]
    ),
    
    TrimbleDevice.T100: DeviceProfile(
        device_type=TrimbleDevice.T100,
        total_memory_mb=4096,
        available_memory_mb=3500,  # Reserve for Windows 10
        cpu_cores=4,
        storage_gb=128,
        
        # Aggressive settings for construction workflows
        recommended_memory_limit_mb=3200,
        max_concurrent_tasks=6,
        priority_levels=5,
        cache_size_mb=400,
        
        supports_real_time=True,
        supports_complex_calculations=True,
        typical_use_cases=[
            "bim_processing",
            "clash_detection",
            "safety_monitoring",
            "machine_guidance",
            "progress_tracking"
        ]
    ),
    
    TrimbleDevice.FMX: DeviceProfile(
        device_type=TrimbleDevice.FMX,
        total_memory_mb=2048,
        available_memory_mb=1700,  # Reserve for Linux OS
        cpu_cores=2,
        storage_gb=16,
        
        # Optimized for agriculture workflows
        recommended_memory_limit_mb=1500,
        max_concurrent_tasks=4,
        priority_levels=4,
        cache_size_mb=200,
        
        supports_real_time=True,
        supports_complex_calculations=True,  # Specialized for ag processing
        typical_use_cases=[
            "variable_rate_application",
            "field_boundary_processing",
            "equipment_coordination",
            "yield_monitoring",
            "weather_integration"
        ]
    ),
    
    TrimbleDevice.CFX750: DeviceProfile(
        device_type=TrimbleDevice.CFX750,
        total_memory_mb=1024,
        available_memory_mb=800,   # Reserve for embedded Linux
        cpu_cores=1,
        storage_gb=8,
        
        # Very conservative for 1GB device
        recommended_memory_limit_mb=700,
        max_concurrent_tasks=2,
        priority_levels=3,
        cache_size_mb=50,
        
        supports_real_time=True,
        supports_complex_calculations=False,
        typical_use_cases=[
            "basic_guidance",
            "simple_field_operations",
            "data_logging"
        ]
    ),
    
    TrimbleDevice.PeopleNet: DeviceProfile(
        device_type=TrimbleDevice.PeopleNet,
        total_memory_mb=2048,
        available_memory_mb=1600,
        cpu_cores=4,
        storage_gb=32,
        
        # Fleet management optimization
        recommended_memory_limit_mb=1400,
        max_concurrent_tasks=5,
        priority_levels=4,
        cache_size_mb=200,
        
        supports_real_time=True,
        supports_complex_calculations=True,
        typical_use_cases=[
            "route_optimization",
            "driver_monitoring",
            "vehicle_diagnostics",
            "fleet_coordination",
            "safety_alerts"
        ]
    )
}


class TrimbleWorkflowOptimizer:
    """Optimizes Fractal-Down workflows for specific Trimble devices"""
    
    def __init__(self, device_type: TrimbleDevice):
        self.device_profile = TRIMBLE_DEVICE_PROFILES[device_type]
        
    def get_memory_limit(self) -> int:
        """Get recommended memory limit for this device"""
        return self.device_profile.recommended_memory_limit_mb
        
    def get_max_concurrent_tasks(self) -> int:
        """Get maximum concurrent tasks for optimal performance"""
        return self.device_profile.max_concurrent_tasks
        
    def get_priority_levels(self) -> int:
        """Get number of priority levels supported"""
        return self.device_profile.priority_levels
        
    def get_cache_size(self) -> int:
        """Get recommended cache size in MB"""
        return self.device_profile.cache_size_mb
        
    def supports_workflow(self, workflow_type: str) -> bool:
        """Check if device supports a specific workflow type"""
        return workflow_type in self.device_profile.typical_use_cases
        
    def optimize_for_use_case(self, use_case: str) -> Dict[str, any]:
        """Get optimization parameters for a specific use case"""
        
        if use_case == "real_time_safety":
            return {
                'memory_limit_mb': int(self.device_profile.recommended_memory_limit_mb * 0.8),
                'max_concurrent_tasks': min(2, self.device_profile.max_concurrent_tasks),
                'priority_levels': self.device_profile.priority_levels,
                'cache_size_mb': int(self.device_profile.cache_size_mb * 0.5),
                'guaranteed_critical_resources': True
            }
            
        elif use_case == "batch_processing":
            return {
                'memory_limit_mb': self.device_profile.recommended_memory_limit_mb,
                'max_concurrent_tasks': self.device_profile.max_concurrent_tasks,
                'priority_levels': 3,  # Simplified for batch work
                'cache_size_mb': self.device_profile.cache_size_mb,
                'guaranteed_critical_resources': False
            }
            
        elif use_case == "power_constrained":
            return {
                'memory_limit_mb': int(self.device_profile.recommended_memory_limit_mb * 0.7),
                'max_concurrent_tasks': max(1, self.device_profile.max_concurrent_tasks - 1),
                'priority_levels': self.device_profile.priority_levels,
                'cache_size_mb': int(self.device_profile.cache_size_mb * 0.7),
                'guaranteed_critical_resources': False
            }
            
        else:
            # Default optimization
            return {
                'memory_limit_mb': self.device_profile.recommended_memory_limit_mb,
                'max_concurrent_tasks': self.device_profile.max_concurrent_tasks,
                'priority_levels': self.device_profile.priority_levels,
                'cache_size_mb': self.device_profile.cache_size_mb,
                'guaranteed_critical_resources': False
            }


def get_device_recommendations(device_type: TrimbleDevice) -> str:
    """Get human-readable recommendations for device optimization"""
    
    profile = TRIMBLE_DEVICE_PROFILES[device_type]
    optimizer = TrimbleWorkflowOptimizer(device_type)
    
    recommendations = f"""
Device Optimization Recommendations for {device_type.value.upper()}

Hardware Profile:
- Total Memory: {profile.total_memory_mb}MB
- Available Memory: {profile.available_memory_mb}MB  
- CPU Cores: {profile.cpu_cores}
- Storage: {profile.storage_gb}GB

Fractal-Down Settings:
- Memory Limit: {profile.recommended_memory_limit_mb}MB
- Max Concurrent Tasks: {profile.max_concurrent_tasks}
- Priority Levels: {profile.priority_levels}
- Cache Size: {profile.cache_size_mb}MB

Supported Use Cases:
{chr(10).join(f"- {use_case}" for use_case in profile.typical_use_cases)}

Performance Characteristics:
- Real-time Processing: {'✓' if profile.supports_real_time else '✗'}
- Complex Calculations: {'✓' if profile.supports_complex_calculations else '✗'}

Optimization Notes:
"""
    
    if profile.total_memory_mb <= 1024:
        recommendations += "- Memory-constrained device: Use simplified workflows and aggressive caching\n"
    
    if profile.cpu_cores == 1:
        recommendations += "- Single-core device: Minimize concurrent operations\n"
        
    if not profile.supports_complex_calculations:
        recommendations += "- Limited computational power: Offload complex operations to cloud when possible\n"
        
    return recommendations


# Example usage
if __name__ == "__main__":
    # Test device optimization for construction tablet
    optimizer = TrimbleWorkflowOptimizer(TrimbleDevice.T100)
    
    print("Construction Safety Optimization:")
    safety_config = optimizer.optimize_for_use_case("real_time_safety")
    print(safety_config)
    
    print("\nDevice Recommendations:")
    print(get_device_recommendations(TrimbleDevice.T100))
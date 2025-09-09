# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""Digital Twins and Asset Lifecycle examples for Trimble integration."""

from typing import Dict, List, Tuple, Any
from fractal_down.dag import DAG

def create_sensor_fusion_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create sensor fusion DAG for digital twins."""
    dag = DAG()
    
    sensor_streams = dag.add_leaf("sensor_data", {"e": 0.9, "H": 0.8})
    
    def fuse_sensors(data):
        return data * 0.85  # Sensor fusion
        
    fused = dag.add_op("fuse_sensors", fuse_sensors, [sensor_streams], {
        "e": 0.8, "H": 0.4, "priority_class": "P1"
    })
    
    inputs = {sensor_streams: 1000}
    return dag, fused, inputs

def create_twin_update_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create digital twin update DAG."""
    dag = DAG()
    
    twin_state = dag.add_leaf("twin_current_state", {"e": 0.6, "H": 0.5})
    
    def update_twin(state):
        return state * 1.05  # State update
        
    updated = dag.add_op("update_twin", update_twin, [twin_state], {
        "e": 0.7, "H": 0.3, "cacheable": True
    })
    
    inputs = {twin_state: 500}
    return dag, updated, inputs

def demo_digital_twin_sync():
    """Demo digital twin synchronization."""
    print("=== Digital Twin Sync Demo ===")
    dag, root, inputs = create_sensor_fusion_dag()
    print(f"Digital twin DAG: {dag.size()} nodes")
    return dag, root, inputs
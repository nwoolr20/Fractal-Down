# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""Transportation and Logistics/Fleet examples for Trimble integration."""

from typing import Dict, List, Tuple, Any
from fractal_down.dag import DAG

def create_fleet_telematics_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create fleet telematics processing DAG."""
    dag = DAG()
    
    events = dag.add_leaf("vehicle_events", {"e": 0.8, "H": 0.9})
    
    def process_events(events):
        return events * 0.1  # 10% anomalies
        
    processed = dag.add_op("process_events", process_events, [events], {
        "e": 0.7, "H": 0.3, "priority_class": "P1"
    })
    
    inputs = {events: 1000}
    return dag, processed, inputs

def create_route_optimization_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create route optimization DAG."""
    dag = DAG()
    
    routes = dag.add_leaf("route_data", {"e": 0.6, "H": 0.7})
    
    def optimize(routes):
        return routes * 0.9  # 10% route improvement
        
    optimized = dag.add_op("optimize_routes", optimize, [routes], {
        "e": 0.8, "H": 0.2, "cacheable": True
    })
    
    inputs = {routes: 100}
    return dag, optimized, inputs

def demo_logistics_pipeline():
    """Demo logistics processing."""
    print("=== Transportation & Logistics Demo ===")
    dag, root, inputs = create_fleet_telematics_dag()
    print(f"Fleet telematics DAG: {dag.size()} nodes")
    return dag, root, inputs
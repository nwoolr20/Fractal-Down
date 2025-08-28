"""UAV and Aerial Data Capture examples for Trimble integration."""

from typing import Dict, List, Tuple, Any
from fractal_down.dag import DAG

def create_aerial_capture_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create aerial data capture DAG."""
    dag = DAG()
    
    flight_data = dag.add_leaf("flight_data", {"e": 1.0, "H": 0.9})
    
    def process_flight(data):
        return data * 0.8  # Process to mosaic
        
    processed = dag.add_op("process_flight", process_flight, [flight_data], {
        "e": 0.9, "H": 0.4, "cacheable": True
    })
    
    inputs = {flight_data: 10000}
    return dag, processed, inputs

def create_flight_data_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create flight data processing DAG."""
    dag = DAG()
    
    raw_data = dag.add_leaf("raw_flight_data", {"e": 0.8, "H": 0.8})
    
    def stabilize(data):
        return data * 0.95  # Stabilization corrections
        
    stabilized = dag.add_op("stabilize", stabilize, [raw_data], {
        "e": 0.7, "H": 0.3, "priority_class": "P1"
    })
    
    inputs = {raw_data: 5000}
    return dag, stabilized, inputs

def demo_uav_processing():
    """Demo UAV processing pipeline."""
    print("=== UAV Processing Demo ===")
    dag, root, inputs = create_aerial_capture_dag()
    print(f"UAV processing DAG: {dag.size()} nodes")
    return dag, root, inputs
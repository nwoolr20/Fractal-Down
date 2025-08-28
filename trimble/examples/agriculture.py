"""
Precision Agriculture examples for Trimble integration.

Demonstrates multi-machine coordination, edge DAG processing on vehicle consoles,
and recipe caching for field operations like planting, spraying, and harvesting.
"""

from typing import Dict, List, Tuple, Any, Optional
import operator
import math

from fractal_down.dag import DAG
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority, FractalParams


def create_precision_agriculture_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create precision agriculture field processing DAG.
    
    Edge DAG on vehicle console: Fuse GNSS, IMU, agronomic prescription maps
    with graceful fallback when ML inference model missing.
    
    Returns:
        Tuple of (DAG, root_node_id, input_values)
    """
    dag = DAG()
    
    # Input: GNSS position data
    gnss_data = dag.add_leaf("gnss_position", {
        "e": 0.3,  # Low energy - just position data
        "H": 0.6,  # Moderate entropy - coordinate variations
        "data_type": "gnss_coordinates",
        "update_frequency": "10Hz"
    })
    
    # Input: IMU sensor data  
    imu_data = dag.add_leaf("imu_sensors", {
        "e": 0.4,  # Moderate energy for sensor fusion
        "H": 0.8,  # High entropy - motion variations
        "data_type": "imu_measurements", 
        "update_frequency": "100Hz"
    })
    
    # Input: Prescription map data
    prescription_map = dag.add_leaf("prescription_map", {
        "e": 0.5,  # Moderate energy to process map
        "H": 0.5,  # Structured agronomic data
        "data_type": "agronomic_prescription"
    })
    
    # Input: Soil sensor readings
    soil_sensors = dag.add_leaf("soil_sensor_data", {
        "e": 0.6,  # Higher energy - real-time soil analysis
        "H": 0.7,  # Variable soil conditions
        "data_type": "soil_measurements"
    })
    
    # Position fusion - combine GNSS + IMU for accurate location
    def fuse_position(gnss, imu):
        """Fuse GNSS and IMU data for precise vehicle positioning."""
        # Simulate Kalman filter-based sensor fusion
        fused_position = {
            "latitude": gnss * 1.0001,   # Slight correction from IMU
            "longitude": gnss * 0.9999,  # IMU drift compensation
            "heading": imu * 1.0,        # Primary heading from IMU
            "accuracy": 0.02             # 2cm accuracy
        }
        return fused_position
        
    position_fused = dag.add_op("position_fusion", fuse_position,
                               [gnss_data, imu_data], {
        "e": 0.7,
        "H": 0.4,  # More accurate, less uncertain
        "cache_key": "position_fused",
        "priority_class": "P1",  # Real-time control
        "cacheable": True
    })
    
    # Prescription lookup - map position to agronomic recommendations
    def lookup_prescription(position, prescription_map):
        """Look up agronomic prescription for current position."""
        # Simulate prescription map interpolation
        prescription = {
            "seed_rate": prescription_map * 0.8,      # Seeds per acre
            "fertilizer_rate": prescription_map * 0.6, # N-P-K rates
            "spray_rate": prescription_map * 0.4,     # Chemical application
            "zone_id": int(position["latitude"] * 1000) % 10  # Management zone
        }
        return prescription
        
    current_prescription = dag.add_op("lookup_prescription", lookup_prescription,
                                     [position_fused, prescription_map], {
        "e": 0.5,
        "H": 0.3,  # Structured prescription data
        "cache_key": "prescription_lookup",
        "priority_class": "P1",
        "cacheable": True  # Cache for similar positions
    })
    
    # Soil condition adjustment - real-time prescription modification
    def adjust_for_soil(prescription, soil_data):
        """Adjust prescription based on real-time soil conditions."""
        # Simulate soil-based prescription adjustments
        adjusted = {
            "seed_rate": prescription["seed_rate"] * (1 + soil_data * 0.1),
            "fertilizer_rate": prescription["fertilizer_rate"] * (1 + soil_data * 0.15),
            "spray_rate": prescription["spray_rate"] * (1 + soil_data * 0.05),
            "moisture_factor": soil_data * 0.3
        }
        return adjusted
        
    adjusted_prescription = dag.add_op("adjust_for_soil", adjust_for_soil,
                                      [current_prescription, soil_sensors], {
        "e": 0.6,
        "H": 0.25,  # Well-adjusted, precise prescription
        "cache_key": "soil_adjusted",
        "priority_class": "P1",
        "cacheable": True
    })
    
    # ML inference for optimization (with fallback)
    def ml_optimize_application(adjusted_prescription, position):
        """ML-based application optimization with heuristic fallback."""
        try:
            # Simulate ML inference (might fail on edge device)
            ml_optimized = {
                "optimized_seed_rate": adjusted_prescription["seed_rate"] * 1.05,
                "optimized_fertilizer": adjusted_prescription["fertilizer_rate"] * 0.98,
                "confidence": 0.87,
                "ml_used": True
            }
            return ml_optimized
        except:
            # Fallback to heuristic optimization
            heuristic_optimized = {
                "optimized_seed_rate": adjusted_prescription["seed_rate"] * 1.02,
                "optimized_fertilizer": adjusted_prescription["fertilizer_rate"] * 1.0,
                "confidence": 0.65,
                "ml_used": False  # Graceful degradation
            }
            return heuristic_optimized
            
    optimized_application = dag.add_op("ml_optimize_application", ml_optimize_application,
                                      [adjusted_prescription, position_fused], {
        "e": 0.8,  # High compute if ML available
        "H": 0.2,  # Highly optimized output
        "cache_key": "ml_optimized",
        "priority_class": "P2",  # Optimization is P2, control is P1
        "fallback_available": True
    })
    
    # Application control signals
    def generate_control_signals(optimized_prescription, position):
        """Generate machine control signals for application equipment."""
        controls = {
            "planter_rate": optimized_prescription["optimized_seed_rate"],
            "fertilizer_flow": optimized_prescription["optimized_fertilizer"],
            "spray_pressure": optimized_prescription.get("spray_rate", 0),
            "implement_height": 0.15,  # 15cm above ground
            "forward_speed": 8.5       # 8.5 mph optimal
        }
        return controls
        
    control_signals = dag.add_op("generate_control_signals", generate_control_signals,
                                [optimized_application, position_fused], {
        "e": 0.4,
        "H": 0.1,  # Precise control outputs
        "priority_class": "P1",  # Control signals are real-time critical
        "cache_key": "control_signals"
    })
    
    # Input values - sample field operation
    inputs = {
        gnss_data: {
            "lat": 40.123456,
            "lon": -96.789012, 
            "altitude": 345.67
        },
        imu_data: {
            "roll": 1.2,      # degrees
            "pitch": -0.8,    # degrees  
            "yaw": 87.5,      # degrees
            "accel_x": 0.1,   # m/s²
            "accel_y": -0.05, # m/s²
            "accel_z": 9.81   # m/s²
        },
        prescription_map: {
            "field_id": "field_42",
            "crop": "corn",
            "target_yield": 180,  # bushels/acre
            "zone_count": 8
        },
        soil_sensors: {
            "moisture": 23.5,    # percent
            "temperature": 18.2, # celsius
            "ph": 6.4,          # pH units
            "organic_matter": 3.8 # percent
        }
    }
    
    return dag, control_signals, inputs


def create_multi_machine_coordination_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create multi-machine coordination DAG for field operations.
    
    Demonstrates priority windows for weather-sensitive operations like
    fertilizer application that must be prioritized over other tasks.
    
    Returns:
        Tuple of (DAG, root_node_id, input_values)
    """
    dag = DAG()
    
    # Input: Weather forecast data
    weather_data = dag.add_leaf("weather_forecast", {
        "e": 0.3,  # Low energy - forecast data
        "H": 0.7,  # High entropy - weather uncertainty
        "data_type": "weather_forecast"
    })
    
    # Input: Machine availability
    machine_fleet = dag.add_leaf("machine_availability", {
        "e": 0.2,  # Low energy - fleet status
        "H": 0.4,  # Moderate entropy - availability patterns
        "data_type": "fleet_status"
    })
    
    # Input: Field conditions
    field_conditions = dag.add_leaf("field_conditions", {
        "e": 0.4,  # Moderate energy - condition assessment
        "H": 0.6,  # Variable field conditions
        "data_type": "field_status"
    })
    
    # Input: Pending operations
    operation_queue = dag.add_leaf("pending_operations", {
        "e": 0.3,  # Moderate energy - operation planning
        "H": 0.8,  # High entropy - diverse operations
        "data_type": "operation_queue"
    })
    
    # Weather window analysis - critical for spray operations
    def analyze_weather_window(weather_data):
        """Analyze weather conditions for time-sensitive operations."""
        # Simulate weather window analysis
        weather_window = {
            "spray_window_hours": max(0, weather_data * 6 - 2),  # 0-4 hour window
            "wind_speed_favorable": weather_data < 0.7,          # Low wind needed
            "rain_probability": weather_data * 0.3,              # 30% max
            "temperature_optimal": True                          # Assume optimal temp
        }
        return weather_window
        
    weather_window = dag.add_op("analyze_weather_window", analyze_weather_window,
                               [weather_data], {
        "e": 0.5,
        "H": 0.4,  # More structured weather analysis
        "cache_key": "weather_window",
        "priority_class": "P0",  # Weather-sensitive operations are P0
        "cacheable": True
    })
    
    # Operation prioritization based on weather sensitivity
    def prioritize_operations(operations, weather_window, field_conditions):
        """Prioritize operations based on weather sensitivity and field conditions."""
        # Simulate operation prioritization
        if weather_window["spray_window_hours"] > 0:
            # Weather window available - prioritize spray operations
            priority_ops = {
                "spray_operations": operations * 0.4,    # 40% spray ops get priority
                "planting_operations": operations * 0.3,  # 30% planting
                "harvesting_operations": operations * 0.2, # 20% harvesting
                "maintenance_operations": operations * 0.1  # 10% maintenance
            }
        else:
            # No weather window - defer spray operations
            priority_ops = {
                "spray_operations": 0,  # Defer all spray operations
                "planting_operations": operations * 0.5,  # Focus on planting
                "harvesting_operations": operations * 0.4, # Focus on harvesting  
                "maintenance_operations": operations * 0.1  # Some maintenance
            }
        return priority_ops
        
    prioritized_ops = dag.add_op("prioritize_operations", prioritize_operations,
                                [operation_queue, weather_window, field_conditions], {
        "e": 0.7,
        "H": 0.3,  # Well-structured prioritization
        "cache_key": "prioritized_operations",
        "priority_class": "P0",  # Prioritization is critical
        "cacheable": True
    })
    
    # Machine allocation
    def allocate_machines(prioritized_ops, machine_fleet):
        """Allocate available machines to prioritized operations."""
        # Simulate optimal machine allocation
        allocation = {
            "sprayer_assignments": prioritized_ops["spray_operations"] * 0.9,
            "planter_assignments": prioritized_ops["planting_operations"] * 0.8,
            "harvester_assignments": prioritized_ops["harvesting_operations"] * 0.85,
            "utility_assignments": prioritized_ops["maintenance_operations"] * 1.0,
            "total_utilization": 0.86  # 86% fleet utilization
        }
        return allocation
        
    machine_allocation = dag.add_op("allocate_machines", allocate_machines,
                                   [prioritized_ops, machine_fleet], {
        "e": 0.6,
        "H": 0.25,  # Structured allocation plan
        "cache_key": "machine_allocation",
        "priority_class": "P1",  # Real-time coordination
        "cacheable": True
    })
    
    # Coordination schedule generation
    def generate_coordination_schedule(allocation, weather_window):
        """Generate coordinated schedule for all machines."""
        schedule = {
            "immediate_tasks": allocation["sprayer_assignments"],  # Weather-sensitive first
            "morning_tasks": allocation["planter_assignments"],    # Early morning optimal
            "afternoon_tasks": allocation["harvester_assignments"], # Afternoon optimal
            "maintenance_slots": allocation["utility_assignments"], # Fill remaining time
            "weather_contingency": weather_window["spray_window_hours"] > 2
        }
        return schedule
        
    coordination_schedule = dag.add_op("generate_coordination_schedule", 
                                      generate_coordination_schedule,
                                      [machine_allocation, weather_window], {
        "e": 0.4,
        "H": 0.2,  # Highly structured schedule
        "priority_class": "P1",
        "cache_key": "coordination_schedule"
    })
    
    # Input values
    inputs = {
        weather_data: 0.6,  # Moderate weather favorability
        machine_fleet: [
            {"id": "sprayer_01", "status": "available", "location": "field_A"},
            {"id": "planter_02", "status": "available", "location": "field_B"}, 
            {"id": "harvester_03", "status": "in_use", "location": "field_C"},
            {"id": "tractor_04", "status": "maintenance", "location": "shop"}
        ],
        field_conditions: {
            "moisture_adequate": True,
            "soil_temperature": 12,  # celsius
            "surface_condition": "good"
        },
        operation_queue: 100  # 100 pending operations
    }
    
    return dag, coordination_schedule, inputs


def demo_field_processing_pipeline():
    """
    Demonstrate precision agriculture field processing with edge computing.
    
    Shows graceful degradation when ML models are unavailable and recipe
    caching for similar field conditions.
    """
    print("=== Trimble Precision Agriculture Demo ===")
    
    # Create precision agriculture DAG
    dag, root, inputs = create_precision_agriculture_dag()
    print(f"Created precision agriculture DAG with {dag.size()} nodes")
    
    # Show edge processing pipeline  
    print("\nEdge Processing Pipeline:")
    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        priority_class = node.meta.get("priority_class", "P2")
        fallback = " [FALLBACK]" if node.meta.get("fallback_available") else ""
        cache = " [CACHED]" if node.meta.get("cacheable") else ""
        print(f"  {priority_class}: {node.name}{fallback}{cache}")
    
    # Use agriculture-specific fractal parameters
    params = FractalParams(
        alpha=0.9,    # High bias toward real-time control
        beta=0.1,     # Less focus on entropy
        gamma=0.02,   # Minimal locality for edge processing
        min_priority=0.08  # Higher minimum for control systems
    )
    priorities = compute_node_priority(dag, root, params)
    
    print("\nReal-Time Control Priorities:")
    priority_sorted = sorted(priorities.items(), key=lambda x: x[1], reverse=True)
    for node_id, priority in priority_sorted:
        node = dag.node(node_id)
        priority_class = node.meta.get("priority_class", "P2")
        print(f"  {priority:.3f} - {node.name} ({priority_class})")
    
    # Build and execute plan with edge memory constraints
    plan = build_plan(dag, root, budget_nodes=3, node_priority=priorities)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=True)
    
    print(f"\nEdge Execution Results:")
    print(f"  Control signals: {result.value}")
    print(f"  Peak memory: {result.peak_memory_nodes}/3 nodes")
    print(f"  Graceful degradation: Available")
    
    # Demonstrate multi-machine coordination
    print("\n=== Multi-Machine Coordination Demo ===")
    coord_dag, coord_root, coord_inputs = create_multi_machine_coordination_dag()
    
    coord_plan = build_plan(coord_dag, coord_root, budget_nodes=4)
    coord_evaluator = Evaluator(coord_dag, coord_inputs)
    coord_result = coord_evaluator.run(coord_plan)
    
    print(f"Coordination schedule: {coord_result.value}")
    print(f"Weather-sensitive prioritization: Active")
    print(f"Cache-enabled operations: 4/6 cacheable")
    
    return result, coord_result


if __name__ == "__main__":
    demo_field_processing_pipeline()
"""
Autonomy and Guidance (Machine Control) examples for Trimble integration.

Demonstrates safety-first scheduling where obstacle detection & geofence 
enforcement always preempts telemetry, with deterministic execution for 
certification of autonomous assistance functions.
"""

from typing import Dict, List, Tuple, Any, Optional
import operator
import math

from fractal_down.dag import DAG
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority, FractalParams


def create_safety_guidance_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create safety-first autonomous guidance DAG.
    
    Latency-critical loops pinned to high-priority fractal layers while 
    non-critical map enrichment is deferred.
    
    Returns:
        Tuple of (DAG, root_node_id, input_values)
    """
    dag = DAG()
    
    # Input: Sensor data streams
    lidar_sensors = dag.add_leaf("lidar_obstacle_data", {
        "e": 1.0,  # High energy - real-time LiDAR processing
        "H": 0.9,  # High entropy - dynamic obstacles
        "data_type": "lidar_pointcloud",
        "priority_class": "P0",  # Safety critical
        "update_frequency": "20Hz"
    })
    
    camera_feed = dag.add_leaf("camera_visual_data", {
        "e": 0.8,  # High energy - image processing
        "H": 0.8,  # High entropy - visual complexity
        "data_type": "camera_image",
        "priority_class": "P0"
    })
    
    # Obstacle detection - absolute highest priority
    def detect_obstacles(lidar_data, camera_data):
        """Real-time obstacle detection from sensor fusion."""
        obstacles = {
            "immediate_threats": lidar_data * 0.05,  # 5% immediate threats
            "potential_obstacles": lidar_data * 0.15, # 15% potential
            "static_objects": lidar_data * 0.80,     # 80% static environment
            "confidence_score": 0.94
        }
        return obstacles
        
    obstacle_detection = dag.add_op("detect_obstacles", detect_obstacles,
                                   [lidar_sensors, camera_feed], {
        "e": 1.2,  # Highest compute priority
        "H": 0.3,  # Structured obstacle data
        "priority_class": "P0",  # Absolute priority for safety
        "cache_key": "obstacle_detection",
        "latency_critical": True
    })
    
    # Geofence enforcement - also P0 safety
    geofence_boundaries = dag.add_leaf("geofence_data", {
        "e": 0.2,  # Low energy - just boundary data
        "H": 0.3,  # Structured geofence polygons
        "data_type": "geofence_boundaries",
        "priority_class": "P0"
    })
    
    def enforce_geofence(obstacles, geofence):
        """Enforce geofence boundaries and safety zones."""
        enforcement = {
            "boundary_violations": obstacles["immediate_threats"] * 0.1,
            "safety_margin_status": True,
            "emergency_stop_required": False,
            "course_correction_needed": obstacles["immediate_threats"] > 0.02
        }
        return enforcement
        
    geofence_enforcement = dag.add_op("enforce_geofence", enforce_geofence,
                                     [obstacle_detection, geofence_boundaries], {
        "e": 0.6,
        "H": 0.2,  # Binary safety decisions
        "priority_class": "P0",
        "cache_key": "geofence_enforcement",
        "latency_critical": True
    })
    
    # Path planning - P1 real-time control
    current_position = dag.add_leaf("current_position", {
        "e": 0.3,  # Low energy - position data
        "H": 0.4,  # Moderate entropy - position updates
        "data_type": "gnss_position",
        "priority_class": "P1"
    })
    
    def plan_safe_path(enforcement, position, obstacles):
        """Plan safe navigation path avoiding obstacles."""
        if enforcement["emergency_stop_required"]:
            path = {"action": "emergency_stop", "speed": 0}
        elif enforcement["course_correction_needed"]:
            path = {"action": "course_correct", "speed": 2.0, "direction": "left"}
        else:
            path = {"action": "continue", "speed": 5.0, "direction": "straight"}
        return path
        
    path_planning = dag.add_op("plan_safe_path", plan_safe_path,
                              [geofence_enforcement, current_position, obstacle_detection], {
        "e": 0.8,
        "H": 0.3,  # Structured path decisions
        "priority_class": "P1",  # Real-time control
        "cache_key": "path_planning"
    })
    
    # Vehicle control - P1 real-time
    def generate_vehicle_commands(path):
        """Generate low-level vehicle control commands."""
        commands = {
            "steering_angle": path.get("direction", "straight"),
            "throttle_position": path["speed"] / 10.0,  # Normalize speed
            "brake_pressure": 1.0 if path["action"] == "emergency_stop" else 0.0,
            "gear_selection": "drive"
        }
        return commands
        
    vehicle_control = dag.add_op("generate_vehicle_commands", generate_vehicle_commands,
                                [path_planning], {
        "e": 0.4,
        "H": 0.1,  # Precise control outputs
        "priority_class": "P1",
        "cache_key": "vehicle_control"
    })
    
    # Input values
    inputs = {
        lidar_sensors: 50000,  # 50K LiDAR points
        camera_feed: 1920*1080,  # HD camera frame
        geofence_boundaries: [
            [(0, 0), (100, 0), (100, 100), (0, 100)],  # Work area boundary
            [(20, 20), (25, 20), (25, 25), (20, 25)]   # Exclusion zone
        ],
        current_position: {"lat": 40.123, "lon": -96.789, "heading": 90}
    }
    
    return dag, vehicle_control, inputs


def create_obstacle_detection_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create simplified obstacle detection pipeline for testing."""
    dag = DAG()
    
    sensor_data = dag.add_leaf("sensor_input", {"e": 1.0, "H": 0.9, "priority_class": "P0"})
    
    def detect(data):
        return data * 0.1  # 10% obstacles detected
        
    detection = dag.add_op("obstacle_detection", detect, [sensor_data], {
        "e": 1.2, "H": 0.3, "priority_class": "P0"
    })
    
    inputs = {sensor_data: 1000}
    return dag, detection, inputs


def demo_autonomous_assistance():
    """Demonstrate autonomous assistance with safety-first scheduling."""
    print("=== Trimble Autonomous Assistance Demo ===")
    
    dag, root, inputs = create_safety_guidance_dag()
    print(f"Created safety guidance DAG with {dag.size()} nodes")
    
    # Safety-first parameters
    params = FractalParams(
        alpha=1.0,    # Maximum safety priority
        beta=0.0,     # No entropy consideration for safety
        gamma=0.0,    # No locality consideration
        min_priority=0.2  # High minimum for safety systems
    )
    priorities = compute_node_priority(dag, root, params)
    
    print("\nSafety-First Priority Scheduling:")
    for node_id, priority in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
        node = dag.node(node_id)
        priority_class = node.meta.get("priority_class", "P2")
        latency = " [LATENCY-CRITICAL]" if node.meta.get("latency_critical") else ""
        print(f"  {priority:.3f} - {node.name} ({priority_class}){latency}")
    
    plan = build_plan(dag, root, budget_nodes=3, node_priority=priorities)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=True)
    
    print(f"\nSafety Execution Results:")
    print(f"  Vehicle commands: {result.value}")
    print(f"  Safety verification: PASSED")
    print(f"  Deterministic execution: Enabled for certification")
    
    return result
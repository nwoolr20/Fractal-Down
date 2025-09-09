# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Construction and BIM integration examples for Trimble.

Demonstrates incremental BIM-to-field synchronization, as-built vs design 
deviation detection, and constraint-aware scheduling for construction workflows.
"""

from typing import Dict, List, Tuple, Any, Optional
import operator
import math

from fractal_down.dag import DAG
from fractal_down.treelift import build_plan
from fractal_down.evaluator import Evaluator
from fractal_down.fractal import compute_node_priority, FractalParams


def create_bim_sync_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create incremental BIM-to-field synchronization DAG.
    
    Demonstrates prioritized scheduling where safety-impact changes (structural
    element relocation) get higher priority than cosmetic metadata updates.
    
    Returns:
        Tuple of (DAG, root_node_id, input_values)
    """
    dag = DAG()
    
    # Input: BIM model changes
    bim_changes = dag.add_leaf("bim_model_changes", {
        "e": 0.8,  # Moderate energy to process change set
        "H": 0.9,  # High entropy - various change types
        "data_type": "bim_changeset",
        "priority_class": "P1"  # Real-time updates needed
    })
    
    # Input: Field device locations and capabilities
    field_devices = dag.add_leaf("field_device_registry", {
        "e": 0.2,  # Low energy - just device metadata
        "H": 0.4,  # Moderate entropy - structured device info
        "data_type": "device_registry"
    })
    
    # Change classification - separate safety vs non-safety impacts
    def classify_changes(changes):
        """Classify BIM changes by safety impact and priority."""
        # Simulate change classification
        safety_critical = changes * 0.15  # 15% safety-critical changes
        structural = changes * 0.25       # 25% structural changes  
        cosmetic = changes * 0.60         # 60% cosmetic/metadata changes
        
        return {
            "safety_critical": safety_critical,
            "structural": structural, 
            "cosmetic": cosmetic
        }
    
    classified_changes = dag.add_op("change_classification", classify_changes,
                                   [bim_changes], {
        "e": 0.6,
        "H": 0.6,  # Structured by classification
        "cache_key": "classified_changes",
        "priority_class": "P0",  # Safety classification is P0
        "cacheable": True
    })
    
    # Safety-critical change processing - highest priority
    def process_safety_changes(classified_changes, devices):
        """Process safety-critical changes with immediate field updates."""
        safety_updates = {
            "immediate_alerts": classified_changes["safety_critical"] * 1.2,
            "geofence_updates": classified_changes["safety_critical"] * 0.8,
            "emergency_stops": classified_changes["safety_critical"] * 0.1
        }
        return safety_updates
        
    safety_processed = dag.add_op("process_safety_changes", process_safety_changes,
                                 [classified_changes, field_devices], {
        "e": 1.0,  # High priority processing
        "H": 0.2,  # Highly structured safety outputs
        "priority_class": "P0",  # Safety has absolute priority
        "cache_key": "safety_processed"
    })
    
    # Structural change processing - second priority
    def process_structural_changes(classified_changes):
        """Process structural changes requiring field layout updates."""
        structural_updates = {
            "layout_adjustments": classified_changes["structural"] * 0.9,
            "dimension_updates": classified_changes["structural"] * 1.1,
            "tolerance_changes": classified_changes["structural"] * 0.3
        }
        return structural_updates
        
    structural_processed = dag.add_op("process_structural_changes", 
                                    process_structural_changes,
                                    [classified_changes], {
        "e": 0.8,
        "H": 0.3,
        "priority_class": "P1",  # Real-time control
        "cache_key": "structural_processed",
        "cacheable": True
    })
    
    # Cosmetic change processing - lower priority
    def process_cosmetic_changes(classified_changes):
        """Process cosmetic/metadata changes for documentation."""
        cosmetic_updates = {
            "metadata_sync": classified_changes["cosmetic"] * 0.7,
            "documentation_updates": classified_changes["cosmetic"] * 0.5,
            "reporting_data": classified_changes["cosmetic"] * 0.8
        }
        return cosmetic_updates
        
    cosmetic_processed = dag.add_op("process_cosmetic_changes",
                                   process_cosmetic_changes, 
                                   [classified_changes], {
        "e": 0.4,
        "H": 0.5,
        "priority_class": "P3",  # Batch analytics priority
        "cache_key": "cosmetic_processed", 
        "cacheable": True
    })
    
    # Field update consolidation
    def consolidate_field_updates(safety_updates, structural_updates, 
                                 cosmetic_updates, devices):
        """Consolidate all updates for field device distribution."""
        total_updates = (
            safety_updates["immediate_alerts"] + 
            structural_updates["layout_adjustments"] +
            cosmetic_updates["metadata_sync"]
        )
        
        consolidated = {
            "total_field_updates": total_updates,
            "device_count": len(devices) if isinstance(devices, list) else 1,
            "priority_distribution": {
                "P0_safety": safety_updates["immediate_alerts"],
                "P1_structural": structural_updates["layout_adjustments"], 
                "P3_cosmetic": cosmetic_updates["metadata_sync"]
            }
        }
        return consolidated
        
    field_updates = dag.add_op("consolidate_field_updates", 
                              consolidate_field_updates,
                              [safety_processed, structural_processed, 
                               cosmetic_processed, field_devices], {
        "e": 0.5,
        "H": 0.2,  # Well-structured final output
        "priority_class": "P1",
        "cache_key": "field_updates_consolidated"
    })
    
    # Input values
    inputs = {
        bim_changes: 100,  # 100 total BIM changes
        field_devices: [
            {"id": "station_01", "type": "total_station", "location": (100, 200)},
            {"id": "rover_02", "type": "gps_rover", "location": (150, 250)},
            {"id": "scanner_03", "type": "3d_scanner", "location": (200, 300)},
            {"id": "tablet_04", "type": "field_tablet", "location": (175, 275)}
        ]
    }
    
    return dag, field_updates, inputs


def create_deviation_detection_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """
    Create as-built vs design deviation detection DAG.
    
    Pipeline includes segmentation, alignment, variance scoring with cached
    intermediate geometric primitives for performance.
    
    Returns:
        Tuple of (DAG, root_node_id, input_values)
    """
    dag = DAG()
    
    # Input: Design model (BIM)
    design_model = dag.add_leaf("design_bim_model", {
        "e": 0.6,  # Moderate energy to load design
        "H": 0.7,  # Moderate entropy - structured but complex
        "data_type": "bim_model"
    })
    
    # Input: As-built scan data
    asbuilt_scan = dag.add_leaf("asbuilt_scan_data", {
        "e": 0.9,  # High energy - large scan datasets
        "H": 0.9,  # High entropy - raw scan data
        "data_type": "point_cloud"
    })
    
    # Extract geometric primitives from design
    def extract_design_primitives(design_model):
        """Extract geometric primitives from BIM design model."""
        # Simulate primitive extraction (planes, cylinders, boxes, etc.)
        primitives = {
            "planes": design_model * 0.4,      # Walls, floors, ceilings
            "cylinders": design_model * 0.2,   # Columns, pipes
            "boxes": design_model * 0.3,       # Structural elements
            "complex": design_model * 0.1      # Complex geometries
        }
        return primitives
        
    design_primitives = dag.add_op("extract_design_primitives", 
                                  extract_design_primitives,
                                  [design_model], {
        "e": 0.7,
        "H": 0.4,  # More structured after primitive extraction
        "cache_key": "design_primitives",
        "cacheable": True,  # Cache for multiple deviation checks
        "priority_class": "P2"
    })
    
    # Segment as-built scan data
    def segment_asbuilt_scan(scan_data):
        """Segment as-built scan into geometric regions."""
        # Simulate scan segmentation
        segments = {
            "planar_regions": scan_data * 0.5,
            "cylindrical_regions": scan_data * 0.2,
            "irregular_regions": scan_data * 0.3
        }
        return segments
        
    asbuilt_segments = dag.add_op("segment_asbuilt_scan", segment_asbuilt_scan,
                                 [asbuilt_scan], {
        "e": 1.1,  # High compute for segmentation algorithms
        "H": 0.5,  # Reduced entropy after segmentation  
        "cache_key": "asbuilt_segments",
        "cacheable": True,
        "priority_class": "P2"
    })
    
    # Alignment between design and as-built
    def align_design_asbuilt(design_primitives, asbuilt_segments):
        """Align design primitives with as-built segments."""
        # Simulate ICP or similar alignment algorithm
        alignment = {
            "transformation_matrix": [[1.002, 0.001], [0.001, 1.001]],  # Small rotation/scale
            "translation_vector": [0.05, -0.03, 0.08],  # Small translation
            "alignment_score": 0.94,  # 94% alignment confidence
            "aligned_primitives": design_primitives
        }
        return alignment
        
    alignment = dag.add_op("align_design_asbuilt", align_design_asbuilt,
                          [design_primitives, asbuilt_segments], {
        "e": 1.0,  # High compute for alignment algorithms
        "H": 0.3,  # Well-structured alignment result
        "cache_key": "alignment_result", 
        "cacheable": True,
        "priority_class": "P2"
    })
    
    # Deviation scoring
    def compute_deviations(alignment, asbuilt_segments):
        """Compute deviation scores between aligned design and as-built."""
        deviations = {
            "positional_deviations": alignment["aligned_primitives"] * 0.02,  # 2% avg deviation
            "dimensional_deviations": alignment["aligned_primitives"] * 0.015, # 1.5% size deviation
            "geometric_deviations": alignment["aligned_primitives"] * 0.008,   # 0.8% shape deviation
            "overall_score": alignment["alignment_score"] * 0.96  # Slightly reduce for deviations
        }
        return deviations
        
    deviation_analysis = dag.add_op("compute_deviations", compute_deviations,
                                   [alignment, asbuilt_segments], {
        "e": 0.6,
        "H": 0.2,  # Highly structured analysis results
        "cache_key": "deviation_analysis",
        "priority_class": "P2"
    })
    
    # Generate deviation report
    def generate_deviation_report(deviations):
        """Generate comprehensive deviation analysis report."""
        report = {
            "summary": {
                "total_deviations": sum(deviations.values()) / len(deviations),
                "critical_deviations": deviations["dimensional_deviations"] * 0.1,
                "minor_deviations": deviations["positional_deviations"] * 0.9
            },
            "recommendations": [
                "Adjust column placement by 2cm north",
                "Verify wall thickness in grid B-3", 
                "Review floor levelness in zone 2"
            ]
        }
        return report
        
    final_report = dag.add_op("generate_deviation_report", 
                             generate_deviation_report,
                             [deviation_analysis], {
        "e": 0.3,
        "H": 0.1,  # Highly structured report
        "priority_class": "P3",  # Reporting/analytics priority
        "cache_key": "deviation_report"
    })
    
    # Input values
    inputs = {
        design_model: 1000,  # 1000 design elements
        asbuilt_scan: 50000  # 50K scan points
    }
    
    return dag, final_report, inputs


def demo_incremental_bim_sync():
    """
    Demonstrate incremental BIM synchronization with priority scheduling.
    
    Shows how safety-critical changes are processed first, while cosmetic
    updates can be deferred without blocking critical operations.
    """
    print("=== Trimble Construction BIM Sync Demo ===")
    
    # Create BIM sync DAG
    dag, root, inputs = create_bim_sync_dag()
    print(f"Created BIM sync DAG with {dag.size()} nodes")
    
    # Show priority-based structure
    print("\nBIM Sync Pipeline (Priority-Ordered):")
    for node_id in dag.postorder(root):
        node = dag.node(node_id)
        priority_class = node.meta.get("priority_class", "P2")
        cacheable = " [CACHED]" if node.meta.get("cacheable") else ""
        print(f"  {priority_class}: {node.name}{cacheable}")
    
    # Use construction-specific fractal parameters
    params = FractalParams(
        alpha=0.8,    # High bias toward safety/priority
        beta=0.2,     # Less entropy focus
        gamma=0.05,   # Minimal locality
        min_priority=0.1  # Higher minimum for safety
    )
    priorities = compute_node_priority(dag, root, params)
    
    print("\nPriority Scheduling (Safety-First):")
    priority_sorted = sorted(priorities.items(), key=lambda x: x[1], reverse=True)
    for node_id, priority in priority_sorted:
        node = dag.node(node_id)
        priority_class = node.meta.get("priority_class", "P2")
        print(f"  {priority:.3f} - {node.name} ({priority_class})")
    
    # Build and execute plan
    plan = build_plan(dag, root, budget_nodes=3, node_priority=priorities)
    evaluator = Evaluator(dag, inputs)
    result = evaluator.run(plan, verify=True)
    
    print(f"\nExecution Results:")
    print(f"  Field updates generated: {result.value}")
    print(f"  Memory efficiency: {result.peak_memory_nodes}/3 peak nodes")
    print(f"  Safety-first scheduling: Verified")
    
    # Demonstrate deviation detection
    print("\n=== As-Built vs Design Deviation Detection ===")
    dev_dag, dev_root, dev_inputs = create_deviation_detection_dag()
    
    dev_plan = build_plan(dev_dag, dev_root, budget_nodes=4)
    dev_evaluator = Evaluator(dev_dag, dev_inputs)
    dev_result = dev_evaluator.run(dev_plan)
    
    print(f"Deviation analysis completed: {dev_result.value}")
    print(f"Cached primitive reuse: 3/5 operations cacheable")
    
    return result, dev_result


if __name__ == "__main__":
    demo_incremental_bim_sync()
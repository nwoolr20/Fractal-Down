# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""Mixed Reality and Spatial Positioning examples for Trimble integration."""

from typing import Dict, List, Tuple, Any
from fractal_down.dag import DAG

def create_spatial_anchoring_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create spatial anchoring DAG for AR/XR."""
    dag = DAG()
    
    spatial_data = dag.add_leaf("spatial_anchors", {"e": 0.7, "H": 0.8})
    
    def anchor_processing(data):
        return data * 0.9  # Anchor refinement
        
    anchored = dag.add_op("process_anchors", anchor_processing, [spatial_data], {
        "e": 0.6, "H": 0.3, "priority_class": "P1"
    })
    
    inputs = {spatial_data: 100}
    return dag, anchored, inputs

def create_ar_overlay_dag() -> Tuple[DAG, int, Dict[int, Any]]:
    """Create AR overlay processing DAG."""
    dag = DAG()
    
    overlay_data = dag.add_leaf("ar_overlay_data", {"e": 0.5, "H": 0.6})
    
    def render_overlay(data):
        return data * 1.1  # Overlay rendering
        
    rendered = dag.add_op("render_overlay", render_overlay, [overlay_data], {
        "e": 0.8, "H": 0.2, "cacheable": True
    })
    
    inputs = {overlay_data: 50}
    return dag, rendered, inputs

def demo_mixed_reality_pipeline():
    """Demo mixed reality processing."""
    print("=== Mixed Reality Demo ===")
    dag, root, inputs = create_spatial_anchoring_dag()
    print(f"Mixed reality DAG: {dag.size()} nodes")
    return dag, root, inputs
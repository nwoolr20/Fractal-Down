# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""Test that feature toggles work correctly after module import."""

import os
import pytest

import fractal_down.features as features
from fractal_down.features import FeatureNotEnabledError


def test_custom_exception_replaces_import_error():
    """Test that FeatureNotEnabledError is raised instead of ImportError."""
    with pytest.raises(FeatureNotEnabledError) as exc_info:
        features.require_feature("Test Feature", False)
    
    assert "Test Feature requires the enterprise edition" in str(exc_info.value)
    assert isinstance(exc_info.value, FeatureNotEnabledError)


def test_feature_enable_functions_update_globals():
    """Test that enable functions update the global flag variables."""
    # Save original state
    orig_gpu = os.environ.get("FRACTAL_DOWN_GPU")
    orig_gpu_enabled = features.GPU_ENABLED
    
    try:
        # Start with disabled state
        os.environ.pop("FRACTAL_DOWN_GPU", None)
        features.GPU_ENABLED = False
        
        assert not features.GPU_ENABLED
        
        # Enable GPU
        features.enable_gpu()
        
        # Global should now be True
        assert features.GPU_ENABLED
        assert os.environ.get("FRACTAL_DOWN_GPU") == "1"
    
    finally:
        # Restore original state
        if orig_gpu is not None:
            os.environ["FRACTAL_DOWN_GPU"] = orig_gpu
        else:
            os.environ.pop("FRACTAL_DOWN_GPU", None)
        features.GPU_ENABLED = orig_gpu_enabled


def test_feature_flags_checked_at_runtime():
    """Test that feature flags are checked at runtime, not import time."""
    # Save original state
    orig_gpu = os.environ.get("FRACTAL_DOWN_GPU")
    orig_gpu_enabled = features.GPU_ENABLED
    
    try:
        # Disable GPU
        os.environ.pop("FRACTAL_DOWN_GPU", None)
        features.GPU_ENABLED = False
        
        # Import gpu module when feature is disabled
        import fractal_down.gpu as gpu
        
        # Should fail initially
        with pytest.raises(FeatureNotEnabledError):
            gpu.accelerate("test")
        
        # Enable feature
        features.enable_gpu()
        
        # Now should work with the same imported module (proving runtime check)
        result = gpu.accelerate("test")
        assert "accelerated test with GPU kernels" in result
    
    finally:
        # Restore original state
        if orig_gpu is not None:
            os.environ["FRACTAL_DOWN_GPU"] = orig_gpu
        else:
            os.environ.pop("FRACTAL_DOWN_GPU", None)
        features.GPU_ENABLED = orig_gpu_enabled


def test_all_feature_modules_check_at_runtime():
    """Test that all feature modules check flags at runtime."""
    # Save original states
    orig_states = {}
    for env_var, flag_name in [
        ("FRACTAL_DOWN_GPU", "GPU_ENABLED"),
        ("FRACTAL_DOWN_DISTRIBUTED", "DISTRIBUTED_PLANNER_ENABLED"),
        ("FRACTAL_DOWN_VIZ", "VISUALIZATION_ENABLED")
    ]:
        orig_states[env_var] = os.environ.get(env_var)
        orig_states[flag_name] = getattr(features, flag_name)
    
    try:
        # Disable all features
        for env_var, flag_name in [
            ("FRACTAL_DOWN_GPU", "GPU_ENABLED"),
            ("FRACTAL_DOWN_DISTRIBUTED", "DISTRIBUTED_PLANNER_ENABLED"),
            ("FRACTAL_DOWN_VIZ", "VISUALIZATION_ENABLED")
        ]:
            os.environ.pop(env_var, None)
            setattr(features, flag_name, False)
        
        # Import modules when features are disabled
        import fractal_down.gpu as gpu
        import fractal_down.distributed_planner as distributed
        import fractal_down.visualization as viz
        
        # All should fail initially
        with pytest.raises(FeatureNotEnabledError):
            gpu.accelerate("test data")
        
        with pytest.raises(FeatureNotEnabledError):
            distributed.plan_dag(10)
        
        with pytest.raises(FeatureNotEnabledError):
            viz.render_dag("test dag")
        
        # Enable all features
        features.enable_gpu()
        features.enable_distributed_planner()
        features.enable_visualization()
        
        # All should work now
        result_gpu = gpu.accelerate("test data")
        result_distributed = distributed.plan_dag(10)
        result_viz = viz.render_dag("test dag")
        
        assert "accelerated test data with GPU kernels" in result_gpu
        assert "planned 10 nodes across cluster" in result_distributed
        assert "rendered visualization for test dag" in result_viz
    
    finally:
        # Restore original states
        for env_var, flag_name in [
            ("FRACTAL_DOWN_GPU", "GPU_ENABLED"),
            ("FRACTAL_DOWN_DISTRIBUTED", "DISTRIBUTED_PLANNER_ENABLED"),
            ("FRACTAL_DOWN_VIZ", "VISUALIZATION_ENABLED")
        ]:
            if orig_states[env_var] is not None:
                os.environ[env_var] = orig_states[env_var]
            else:
                os.environ.pop(env_var, None)
            setattr(features, flag_name, orig_states[flag_name])
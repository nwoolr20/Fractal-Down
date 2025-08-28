import os
import tempfile

import pytest

from fractal_down.dag import DAG
from fractal_down.treelift import build_plan
from fractal_down.cache import get_or_build_plan


def test_multitenant_cache_isolated_and_billing():
    dag = DAG()
    a = dag.add_leaf("a")

    def build_fn():
        return build_plan(dag, a, budget_nodes=1)

    events = []

    def hook(tenant, event):
        events.append((tenant, event))

    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["FRACTAL_DOWN_PLANS_DIR"] = tmpdir
        try:
            get_or_build_plan(dag, a, 1, build_fn, tenant_id="t1", billing_hook=hook)
            get_or_build_plan(dag, a, 1, build_fn, tenant_id="t2", billing_hook=hook)
            # Second call for tenant t1 should hit cache
            get_or_build_plan(dag, a, 1, build_fn, tenant_id="t1", billing_hook=hook)

            tenant_dirs = {p.name for p in os.scandir(tmpdir) if p.is_dir()}
            assert tenant_dirs == {"t1", "t2"}
            assert events == [("t1", "miss"), ("t2", "miss"), ("t1", "hit")]
        finally:
            del os.environ["FRACTAL_DOWN_PLANS_DIR"]


def test_multitenant_cache_eviction_per_tenant():
    dag = DAG()
    a = dag.add_leaf("a")

    def build_fn(dag, leaf):
        return build_plan(dag, leaf, budget_nodes=1)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["FRACTAL_DOWN_PLANS_DIR"] = tmpdir
        os.environ["FRACTAL_DOWN_PLAN_MAX_KEEP"] = "3"
        try:
            # Fill cache for tenant1 with unique dags
            for i in range(3):
                d = DAG()
                leaf = d.add_leaf(f"x{i}")
                get_or_build_plan(d, leaf, 1, lambda d=d, leaf=leaf: build_fn(d, leaf), tenant_id="tenant1")

            # Trigger eviction
            d_ev = DAG()
            leaf_ev = d_ev.add_leaf("evict")
            _, path4, _ = get_or_build_plan(d_ev, leaf_ev, 1, lambda d=d_ev, leaf=leaf_ev: build_fn(d, leaf), tenant_id="tenant1")

            tenant_dir = os.path.join(tmpdir, "tenant1")
            files = [f for f in os.listdir(tenant_dir) if f.endswith(".fplan")]
            assert len(files) == 3
            assert os.path.basename(path4) in files

            # Other tenant unaffected
            d2 = DAG()
            l2 = d2.add_leaf("y")
            get_or_build_plan(d2, l2, 1, lambda d=d2, leaf=l2: build_fn(d, leaf), tenant_id="tenant2")
            tenant2_dir = os.path.join(tmpdir, "tenant2")
            assert len([f for f in os.listdir(tenant2_dir) if f.endswith(".fplan")]) == 1
        finally:
            del os.environ["FRACTAL_DOWN_PLANS_DIR"]
            del os.environ["FRACTAL_DOWN_PLAN_MAX_KEEP"]


def test_invalid_tenant_id_rejected():
    dag = DAG()
    a = dag.add_leaf("a")

    def build_fn():
        return build_plan(dag, a, budget_nodes=1)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["FRACTAL_DOWN_PLANS_DIR"] = tmpdir
        try:
            with pytest.raises(ValueError):
                get_or_build_plan(dag, a, 1, build_fn, tenant_id="../evil")
        finally:
            del os.environ["FRACTAL_DOWN_PLANS_DIR"]

import os
import tempfile
from pathlib import Path

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
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["FRACTAL_DOWN_PLANS_DIR"] = tmpdir
        os.environ["FRACTAL_DOWN_PLAN_MAX_KEEP"] = "3"
        try:
            for i in range(4):
                dag = DAG()
                leaf = dag.add_leaf(f"t1_{i}")

                def build_fn(dag=dag, leaf=leaf):
                    return build_plan(dag, leaf, budget_nodes=1)

                get_or_build_plan(dag, leaf, 1, build_fn, tenant_id="t1")

            for i in range(2):
                dag = DAG()
                leaf = dag.add_leaf(f"t2_{i}")

                def build_fn(dag=dag, leaf=leaf):
                    return build_plan(dag, leaf, budget_nodes=1)

                get_or_build_plan(dag, leaf, 1, build_fn, tenant_id="t2")

            t1_files = list(Path(tmpdir, "t1").glob("*.fplan"))
            t2_files = list(Path(tmpdir, "t2").glob("*.fplan"))
            assert len(t1_files) == 3
            assert len(t2_files) == 2
        finally:
            del os.environ["FRACTAL_DOWN_PLANS_DIR"]
            del os.environ["FRACTAL_DOWN_PLAN_MAX_KEEP"]

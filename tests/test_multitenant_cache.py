import os
import tempfile

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

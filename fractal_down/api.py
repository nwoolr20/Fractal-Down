"""Simple FastAPI app exposing plan build/run endpoints."""

from typing import Any, Dict, List, Optional, Tuple
import operator

from fastapi import FastAPI
from pydantic import BaseModel

from .dag import DAG
from .treelift import build_plan
from .evaluator import Evaluator
from .cache import get_or_build_plan

# Registry of supported operations for JSON specs
OP_REGISTRY = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "div": operator.truediv,
}

app = FastAPI()

# Billing hook can be set by integrators
_billing_hook = None


def set_billing_hook(hook):
    global _billing_hook
    _billing_hook = hook


class NodeSpec(BaseModel):
    id: int
    name: str
    op: Optional[str] = None
    inputs: List[int] = []
    meta: Dict[str, Any] = {}


class DAGSpec(BaseModel):
    nodes: List[NodeSpec]
    root: int


class BuildRequest(BaseModel):
    dag: DAGSpec
    budget_nodes: int
    tenant_id: str = "default"


class BuildResponse(BaseModel):
    cache_path: str
    was_cached: bool


class RunRequest(BaseModel):
    dag: DAGSpec
    budget_nodes: int
    inputs: Dict[str, Any]
    tenant_id: str = "default"


class RunResponse(BaseModel):
    result: Any
    digest: str


def _dag_from_spec(spec: DAGSpec) -> Tuple[DAG, int, Dict[str, int]]:
    dag = DAG()
    id_map: Dict[int, int] = {}
    name_map: Dict[str, int] = {}

    for node in spec.nodes:
        if node.op is None:
            node_id = dag.add_leaf(node.name, node.meta)
        else:
            inputs = [id_map[i] for i in node.inputs]
            op = OP_REGISTRY[node.op]
            node_id = dag.add_op(node.name, op, inputs, node.meta)
        id_map[node.id] = node_id
        name_map[node.name] = node_id

    root_id = id_map[spec.root]
    return dag, root_id, name_map


@app.post("/plan/build", response_model=BuildResponse)
async def plan_build(req: BuildRequest) -> BuildResponse:
    dag, root_id, _ = _dag_from_spec(req.dag)

    def build_fn():
        return build_plan(dag, root_id, req.budget_nodes)

    plan, path, was_cached = get_or_build_plan(
        dag,
        root_id,
        req.budget_nodes,
        build_fn,
        tenant_id=req.tenant_id,
        billing_hook=_billing_hook,
    )
    return BuildResponse(cache_path=path, was_cached=was_cached)


@app.post("/plan/run", response_model=RunResponse)
async def plan_run(req: RunRequest) -> RunResponse:
    dag, root_id, name_map = _dag_from_spec(req.dag)
    inputs = {name_map[k]: v for k, v in req.inputs.items()}

    def build_fn():
        return build_plan(dag, root_id, req.budget_nodes)

    plan, _, _ = get_or_build_plan(
        dag,
        root_id,
        req.budget_nodes,
        build_fn,
        tenant_id=req.tenant_id,
        billing_hook=_billing_hook,
    )

    result = Evaluator(dag, inputs).run(plan)
    return RunResponse(result=result.value, digest=result.digest.hex())

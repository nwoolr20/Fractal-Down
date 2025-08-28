"""Simple FastAPI app exposing plan build/run endpoints."""

from typing import Any, Dict, List, Optional, Tuple
import operator

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

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


def set_billing_hook(app: FastAPI, hook) -> None:
    """Configure a billing hook for this FastAPI app."""
    app.state.billing_hook = hook


def get_billing_hook():
    return getattr(app.state, "billing_hook", None)


class NodeSpec(BaseModel):
    id: int
    name: str
    op: Optional[str] = None
    inputs: List[int] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class DAGSpec(BaseModel):
    nodes: List[NodeSpec]
    root: int


class BuildRequest(BaseModel):
    dag: DAGSpec
    budget_nodes: int
    tenant_id: str = Field(default="default", pattern=r"^[A-Za-z0-9._-]+$")


class BuildResponse(BaseModel):
    cache_path: str
    was_cached: bool


class RunRequest(BaseModel):
    dag: DAGSpec
    budget_nodes: int
    inputs: Dict[str, Any]
    tenant_id: str = Field(default="default", pattern=r"^[A-Za-z0-9._-]+$")


class RunResponse(BaseModel):
    result: Any
    digest: str


def _dag_from_spec(spec: DAGSpec) -> Tuple[DAG, int, Dict[str, int]]:
    dag = DAG()
    id_map: Dict[int, int] = {}
    name_map: Dict[str, int] = {}

    for node in spec.nodes:
        if node.id in id_map:
            raise ValueError(f"duplicate node id {node.id}")
        if node.name in name_map:
            raise ValueError(f"duplicate node name {node.name}")

        resolved_inputs = []
        for i in node.inputs:
            if i not in id_map:
                raise ValueError(f"unknown input id {i} for node {node.id}")
            resolved_inputs.append(id_map[i])

        if node.op is None:
            node_id = dag.add_leaf(node.name, node.meta)
        else:
            try:
                op = OP_REGISTRY[node.op]
            except KeyError:
                raise ValueError(f"unknown op {node.op}")
            node_id = dag.add_op(node.name, op, resolved_inputs, node.meta)

        id_map[node.id] = node_id
        name_map[node.name] = node_id

    if spec.root not in id_map:
        raise ValueError("root node missing")
    root_id = id_map[spec.root]
    return dag, root_id, name_map


@app.post("/plan/build", response_model=BuildResponse)
async def plan_build(
    req: BuildRequest, billing_hook=Depends(get_billing_hook)
) -> BuildResponse:
    try:
        dag, root_id, _ = _dag_from_spec(req.dag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    def build_fn():
        return build_plan(dag, root_id, req.budget_nodes)

    try:
        plan, path, was_cached = get_or_build_plan(
            dag,
            root_id,
            req.budget_nodes,
            build_fn,
            tenant_id=req.tenant_id,
            billing_hook=billing_hook,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return BuildResponse(cache_path=path, was_cached=was_cached)


@app.post("/plan/run", response_model=RunResponse)
async def plan_run(
    req: RunRequest, billing_hook=Depends(get_billing_hook)
) -> RunResponse:
    try:
        dag, root_id, name_map = _dag_from_spec(req.dag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        inputs = {name_map[k]: v for k, v in req.inputs.items()}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"unknown input name {e.args[0]}")

    def build_fn():
        return build_plan(dag, root_id, req.budget_nodes)

    try:
        plan, _, _ = get_or_build_plan(
            dag,
            root_id,
            req.budget_nodes,
            build_fn,
            tenant_id=req.tenant_id,
            billing_hook=billing_hook,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = Evaluator(dag, inputs).run(plan)
    return RunResponse(result=result.value, digest=result.digest.hex())

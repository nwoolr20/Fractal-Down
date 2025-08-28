import os
import tempfile
from fastapi.testclient import TestClient

from fractal_down.api import app, set_billing_hook


def test_api_build_and_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["FRACTAL_DOWN_PLANS_DIR"] = tmpdir
        try:
            client = TestClient(app)

            spec = {
                "nodes": [
                    {"id": 1, "name": "a", "op": None, "inputs": []},
                    {"id": 2, "name": "b", "op": None, "inputs": []},
                    {"id": 3, "name": "c", "op": "add", "inputs": [1, 2]},
                ],
                "root": 3,
            }

            events = []

            def hook(tenant, event):
                events.append((tenant, event))

            set_billing_hook(hook)

            resp = client.post(
                "/plan/build",
                json={"dag": spec, "budget_nodes": 2, "tenant_id": "beta"},
            )
            assert resp.status_code == 200
            assert resp.json()["was_cached"] is False

            resp2 = client.post(
                "/plan/build",
                json={"dag": spec, "budget_nodes": 2, "tenant_id": "beta"},
            )
            assert resp2.json()["was_cached"] is True

            run_resp = client.post(
                "/plan/run",
                json={
                    "dag": spec,
                    "budget_nodes": 2,
                    "tenant_id": "beta",
                    "inputs": {"a": 2, "b": 3},
                },
            )
            assert run_resp.status_code == 200
            resp_json = run_resp.json()
            assert resp_json["result"] == 5
            assert "digest" in resp_json
            assert isinstance(resp_json["digest"], str)
            assert len(resp_json["digest"]) > 0

            assert events == [("beta", "miss"), ("beta", "hit"), ("beta", "hit")]
        finally:
            set_billing_hook(None)
            del os.environ["FRACTAL_DOWN_PLANS_DIR"]


def test_api_invalid_spec_and_bad_input():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["FRACTAL_DOWN_PLANS_DIR"] = tmpdir
        try:
            client = TestClient(app)

            bad_spec = {"nodes": [{"id": 1, "name": "a", "op": None, "inputs": []}, {"id": 1, "name": "b", "op": None, "inputs": []}], "root": 1}
            resp = client.post("/plan/build", json={"dag": bad_spec, "budget_nodes": 1})
            assert resp.status_code == 400

            spec = {
                "nodes": [
                    {"id": 1, "name": "a", "op": None, "inputs": []},
                    {"id": 2, "name": "b", "op": None, "inputs": []},
                    {"id": 3, "name": "c", "op": "add", "inputs": [1, 2]},
                ],
                "root": 3,
            }
            run_resp = client.post(
                "/plan/run",
                json={"dag": spec, "budget_nodes": 2, "inputs": {"a": 1, "x": 2}},
            )
            assert run_resp.status_code == 400
        finally:
            del os.environ["FRACTAL_DOWN_PLANS_DIR"]

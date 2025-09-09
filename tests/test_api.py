# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

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

            set_billing_hook(app, hook)

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
            body = run_resp.json()
            assert body["result"] == 5
            assert isinstance(body["digest"], str) and len(body["digest"]) == 64

            assert events == [("beta", "miss"), ("beta", "hit"), ("beta", "hit")]
        finally:
            del os.environ["FRACTAL_DOWN_PLANS_DIR"]


def test_api_rejects_invalid_spec_and_inputs():
    client = TestClient(app)

    dup_spec = {
        "nodes": [
            {"id": 1, "name": "a", "op": None, "inputs": []},
            {"id": 1, "name": "b", "op": None, "inputs": []},
        ],
        "root": 1,
    }
    resp = client.post("/plan/build", json={"dag": dup_spec, "budget_nodes": 1})
    assert resp.status_code == 400

    missing_spec = {
        "nodes": [
            {"id": 1, "name": "a", "op": "add", "inputs": [2]},
        ],
        "root": 1,
    }
    resp2 = client.post("/plan/build", json={"dag": missing_spec, "budget_nodes": 1})
    assert resp2.status_code == 400

    valid_spec = {
        "nodes": [
            {"id": 1, "name": "a", "op": None, "inputs": []},
            {"id": 2, "name": "b", "op": None, "inputs": []},
        ],
        "root": 1,
    }
    bad_run = client.post(
        "/plan/run",
        json={
            "dag": valid_spec,
            "budget_nodes": 1,
            "inputs": {"missing": 1},
        },
    )
    assert bad_run.status_code == 400

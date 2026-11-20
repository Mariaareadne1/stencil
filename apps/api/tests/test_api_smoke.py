"""HTTP-level smoke tests: health, job lifecycle and error handling.

Uses the all-stub pipeline (USE_STUBS=true, set in conftest.py), so no API
keys, network access or Supabase project are needed.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.models.schemas import BrandResult
from apps.api.services import _stubs


@pytest.fixture(autouse=True)
def _no_stub_delays(monkeypatch: pytest.MonkeyPatch) -> None:
    # Stubs sleep 1.5-3s per step to imitate real latency; skip that here.
    monkeypatch.setattr(_stubs, "_sleep", lambda: 0)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_reports_ok(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_create_job_runs_stub_pipeline_to_done(client: TestClient) -> None:
    res = client.post(
        "/jobs",
        json={"handle": "demo", "product_idea": "matcha drink", "platform": "instagram"},
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # TestClient runs background tasks before returning, so the job is finished.
    job = client.get(f"/jobs/{job_id}").json()
    assert job["status"] == "done", job.get("error_message")
    assert job["handle"] == "demo"

    result = BrandResult.model_validate(job["result"])
    assert result.brand_assets.brand_name
    assert len(result.brand_assets.palette) == 5
    assert result.agency_matches


def test_unknown_job_returns_404(client: TestClient) -> None:
    res = client.get("/jobs/does-not-exist")
    assert res.status_code == 404
    assert res.json() == {"detail": "Job not found"}


@pytest.mark.parametrize(
    "body",
    [
        {"product_idea": "matcha drink"},  # missing handle
        {"handle": "demo"},  # missing product idea
        {"handle": "demo", "product_idea": "x", "platform": "myspace"},  # bad platform
    ],
)
def test_create_job_rejects_invalid_body(client: TestClient, body: dict) -> None:
    assert client.post("/jobs", json=body).status_code == 422

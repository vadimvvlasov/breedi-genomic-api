"""Tests for POST /predict-gev endpoint."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Use context manager so lifespan runs and the model is loaded."""
    with TestClient(app) as c:
        yield c


class TestPredictGEV:
    # -- happy path ----------------------------------------------------------

    def test_predict_returns_200(self, client, valid_dosages):
        resp = client.post(
            "/predict-gev",
            json={"animal_id": "cow_001", "snp_dosages": valid_dosages},
        )
        assert resp.status_code == 200

    def test_predict_response_schema(self, client, valid_dosages):
        data = client.post(
            "/predict-gev",
            json={"animal_id": "cow_001", "snp_dosages": valid_dosages},
        ).json()

        assert "animal_id" in data
        assert "gebv" in data
        assert "accuracy" in data
        assert "percentile" in data
        assert data["animal_id"] == "cow_001"
        assert isinstance(data["gebv"], float)
        assert 0.0 <= data["accuracy"] <= 1.0
        assert 0.0 <= data["percentile"] <= 100.0

    def test_predict_gebv_matches_manual_computation(
        self, client, dummy_model, valid_dosages
    ):
        """Verify API result equals direct numpy dot product."""
        expected_gebv = float(
            np.dot(dummy_model._snp_effects, np.asarray(valid_dosages))
        )

        data = client.post(
            "/predict-gev",
            json={"animal_id": "test", "snp_dosages": valid_dosages},
        ).json()

        assert pytest.approx(data["gebv"], rel=1e-3) == round(expected_gebv, 4)

    # -- validation errors ---------------------------------------------------

    def test_invalid_dosage_value(self, client):
        """Dosage must be 0, 1, or 2."""
        resp = client.post(
            "/predict-gev",
            json={"animal_id": "cow_002", "snp_dosages": [0, 1, 3, 2]},
        )
        assert resp.status_code == 422  # Pydantic validation error

    def test_negative_dosage(self, client):
        resp = client.post(
            "/predict-gev",
            json={"animal_id": "cow_003", "snp_dosages": [0, -1, 2]},
        )
        assert resp.status_code == 422

    def test_empty_dosages(self, client):
        resp = client.post(
            "/predict-gev",
            json={"animal_id": "cow_004", "snp_dosages": []},
        )
        assert resp.status_code == 422

    def test_missing_animal_id(self, client):
        resp = client.post(
            "/predict-gev",
            json={"snp_dosages": [0, 1, 2]},
        )
        assert resp.status_code == 422

    def test_wrong_number_of_snps(self, client):
        """Input must have exactly 10 000 markers (dummy model size)."""
        resp = client.post(
            "/predict-gev",
            json={"animal_id": "cow_005", "snp_dosages": [0, 1, 2]},
        )
        # Could be 400 (ValueError from model) or 422 if validated earlier
        assert resp.status_code in (400, 422)

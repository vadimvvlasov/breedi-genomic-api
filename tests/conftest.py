"""Shared pytest fixtures."""

import pytest

from app.inference import RRBLUPModel


@pytest.fixture
def dummy_model() -> RRBLUPModel:
    """Return the loaded dummy model from app/assets/model.joblib."""
    model = RRBLUPModel()
    model.load()
    return model


@pytest.fixture
def valid_dosages() -> list[int]:
    """10 000 SNP dosages matching the dummy model panel."""
    # Alternating 0, 1, 2 pattern — valid additive dosages
    return [i % 3 for i in range(10_000)]

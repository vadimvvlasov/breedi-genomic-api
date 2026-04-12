"""RR-BLUP inference module.

This module loads pre-trained SNP effect weights and computes the Genomic
Estimated Breeding Value (GEBV) as a dot product of SNP dosages and effects.

RR-BLUP (Ridge Regression BLUP) is mathematically equivalent to GBLUP and
estimates the additive effect of each SNP marker independently.  Input genotypes
are encoded as allele dosages 0, 1, or 2 (count of the alternative allele).
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

import joblib
import numpy as np

log = logging.getLogger(__name__)

# Path to the serialised model file (numpy array of SNP effects)
_MODEL_PATH = Path(__file__).parent / "assets" / "model.joblib"


class RRBLUPModel:
    """Wrapper around a pre-trained RR-BLUP model.

    The model file (`model.joblib`) is expected to contain a dictionary with
    the following keys:

    - ``snp_effects`` : numpy.ndarray, shape (n_snps,)
        Additive effect of each SNP marker (trained via RR-BLUP / GBLUP).
    - ``accuracy`` : float
        Estimated prediction accuracy (correlation GEBV ↔ true breeding value).
    - ``ref_mean`` : float
        Mean GEBV of the reference population (for percentile calculation).
    - ``ref_std`` : float
        Standard deviation of GEBV in the reference population.
    - ``version`` : str, optional
        Model version string.

    If the file is missing or cannot be parsed, the model will be in an
    "unloaded" state and ``predict`` will raise a RuntimeError.
    """

    def __init__(self, model_path: Path = _MODEL_PATH) -> None:
        self._model_path = model_path
        self._snp_effects: np.ndarray | None = None
        self._accuracy: float = 0.0
        self._ref_mean: float = 0.0
        self._ref_std: float = 1.0
        self._version: str | None = None

    # -- public API ----------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._snp_effects is not None

    @property
    def version(self) -> str | None:
        return self._version

    def load(self) -> None:
        """Load model weights from the joblib file."""
        if not self._model_path.exists():
            log.error("Model file not found: %s", self._model_path)
            return

        try:
            data = joblib.load(self._model_path)

            # Support both raw array (legacy) and dict format
            if isinstance(data, np.ndarray):
                snp_effects = data
                self._accuracy = 0.72  # sensible default
                self._ref_mean = 0.0
                self._ref_std = 1.0
            elif isinstance(data, dict):
                snp_effects = np.asarray(data["snp_effects"]).ravel()
                self._accuracy = float(data.get("accuracy", 0.72))
                self._ref_mean = float(data.get("ref_mean", 0.0))
                self._ref_std = float(data.get("ref_std", 1.0))
                self._version = data.get("version")
            else:
                raise ValueError(f"Unsupported model format: {type(data)}")

            self._snp_effects = snp_effects
            log.info(
                "RR-BLUP model loaded: %d SNPs, accuracy=%.2f, version=%s",
                len(self._snp_effects),
                self._accuracy,
                self._version or "n/a",
            )
        except Exception:
            log.exception("Failed to load RR-BLUP model from %s", self._model_path)

    def predict(self, snp_dosages: list[float]) -> dict:
        """Compute GEBV for a single animal.

        Parameters
        ----------
        snp_dosages :
            Allele dosages encoded as 0, 1, or 2 (additive model).

        Returns
        -------
        dict with keys: gebv, accuracy, percentile
        """
        if self._snp_effects is None:
            raise RuntimeError("Model is not loaded. Call .load() first.")

        dosages = np.asarray(snp_dosages, dtype=np.float64)

        if dosages.shape[0] != self._snp_effects.shape[0]:
            raise ValueError(
                f"Expected {self._snp_effects.shape[0]} SNP markers, "
                f"got {dosages.shape[0]}.  The input genotype panel must match "
                "the marker set used during RR-BLUP training."
            )

        # GEBV = Σ (snp_effect_i × dosage_i)  —  dot product
        gebv = float(np.dot(self._snp_effects, dosages))

        # Percentile relative to the reference population (assumes Normal)
        if self._ref_std > 0:
            z = (gebv - self._ref_mean) / self._ref_std
            # Approximate CDF of standard Normal via error function
            percentile = float(
                0.5 * (1.0 + math.erf(z / math.sqrt(2.0))) * 100.0
            )
        else:
            percentile = 50.0

        return {
            "gebv": round(gebv, 4),
            "accuracy": round(self._accuracy, 4),
            "percentile": round(percentile, 2),
        }

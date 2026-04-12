"""Pydantic schemas for genomic prediction API."""

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    """Request body for GEBV prediction.

    SNP dosages are encoded as 0, 1, or 2 — the number of alternative alleles
    at each locus (additive genetic model, standard in RR-BLUP / GBLUP pipelines).
    """

    animal_id: str = Field(
        ...,
        description="Unique identifier for the animal (e.g. 'cow_123')",
        min_length=1,
        max_length=64,
    )
    snp_dosages: list[float] = Field(
        ...,
        description="List of SNP allele dosages (0, 1, or 2). "
        "Each value represents the count of alternative alleles at the marker locus.",
        min_length=1,
    )

    @field_validator("snp_dosages")
    @classmethod
    def validate_dosage_values(cls, v: list[float]) -> list[float]:
        """Ensure each dosage is 0, 1, or 2 (additive allele count)."""
        for i, val in enumerate(v):
            if val not in (0.0, 1.0, 2.0, 0, 1, 2):
                raise ValueError(
                    f"SNP dosage at index {i} must be 0, 1, or 2, got {val}. "
                    "RR-BLUP expects additive allele dosages."
                )
        return v


class PredictResponse(BaseModel):
    """Response body containing the Genomic Estimated Breeding Value (GEBV)."""

    animal_id: str = Field(..., description="The animal identifier from the request.")
    gebv: float = Field(
        ...,
        description="Genomic Estimated Breeding Value — sum of weighted SNP effects.",
    )
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Prediction accuracy (correlation between GEBV and true breeding value).",
    )
    percentile: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentile rank of this animal relative to the reference population.",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="'healthy' or 'unhealthy'")
    model_loaded: bool = Field(..., description="Whether the RR-BLUP model is loaded")
    model_version: str | None = Field(
        None,
        description="Version or hash of the loaded model file",
    )

# AGENTS.md

## Commands

```bash
uv sync --all-extras           # Install dependencies
uv run python scripts/generate_dummy_model.py  # Generate test model (10K SNPs)
uv run uvicorn app.main:app --reload  # Dev server on localhost:8000
uv run pytest -v               # Run tests
docker compose up --build     # Docker build + run
```

## Key facts

- **Toolchain**: FastAPI + uvicorn, Python 3.11+, `uv` for package management
- **Model path**: `app/assets/model.joblib` - must exist to start the API
- **SNP encoding**: 0, 1, or 2 (count of alternative alleles per marker)
- **Request validation**: SNP count must match model (`snp_effects.shape[0]`). Invalid dosage → 400 error
- **Docker**: Model is baked into image. Use volume mount in `docker-compose.yml` to override without rebuild

## API

| Endpoint | Description |
|---|---|
| `GET /health` | Health check + model loaded status |
| `POST /predict-gev` | GEBV prediction from SNP dosages |
| `GET /docs` | Swagger UI |

## Model format

`model.joblib` must contain:
```python
{
    "snp_effects": np.ndarray,  # shape (n_snps,)
    "accuracy": float,
    "ref_mean": float,
    "ref_std": float,
    "version": str,  # optional
}
```
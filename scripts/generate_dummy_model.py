"""Generate a dummy RR-BLUP model file for development / testing.

Run:  uv run python scripts/generate_dummy_model.py
"""

import joblib
import numpy as np

# Simulate a panel of 10 000 SNP markers
N_SNPS = 10_000

# SNP effects drawn from a Normal distribution — typical for RR-BLUP
# In production this vector is estimated from phenotypes + genotypes
np.random.seed(42)
snp_effects = np.random.normal(loc=0.0, scale=0.01, size=N_SNPS)

# Reference population parameters (for percentile calculation)
ref_mean = 0.0
ref_std = np.std(snp_effects) * np.sqrt(N_SNPS)  # expected GEBV spread

model_data = {
    "snp_effects": snp_effects,
    "accuracy": 0.72,
    "ref_mean": float(ref_mean),
    "ref_std": float(ref_std),
    "version": "dummy-v0.1.0",
}

OUTPUT_PATH = "app/assets/model.joblib"
joblib.dump(model_data, OUTPUT_PATH)
print(f"Dummy model saved → {OUTPUT_PATH}  ({N_SNPS} SNPs)")

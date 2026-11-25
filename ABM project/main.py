"""
Main experiment runner
"""

import numpy as np
from model import Config
from behaviours import RULES, run_scenario
from metrics import summarize

def run_all(cfg):
    rows = []
    for scenario in RULES:
        cfg.scenario = scenario
        runs = []
        for r in range(cfg.n_replications):
            seed = ((cfg.seed or 0) + r)
            hist, park = run_scenario(cfg,seed,)
            runs.append(summarize(hist, park))
        result = {key: float(np.mean([run[key] for run in runs])) for key in runs[0]}
        result["scenario"] = scenario
        rows.append(result)
    return rows


if __name__ == "__main__":
    cfg = Config(seed=42)

    results = run_all(cfg)
    print("\nRESULTS\n")
    for row in results:
        print(row)
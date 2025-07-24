"""
generator.py
------------
Lightweight vital‑sign generator for teaching / simulation.

Yields one record per second with gentle physiologic variability.
"""

import numpy as np
import time
from typing import Dict, Generator, Optional


def vitals_stream(
    duration: Optional[float] = None,   # seconds (None = endless)
    fs: float = 1.0,                    # samples per second
    seed: Optional[int] = None,
    hr_base: float = 75,
    sbp_base: float = 120,
    dbp_base: float = 80,
    rr_base: float = 16,
    spo2_base: float = 98,
) -> Generator[Dict[str, float], None, None]:
    """Yield a dict of vital‑sign values every 1/fs seconds."""
    rng = np.random.default_rng(seed)
    step = 1.0 / fs
    i = 0

    while True:
        t = i * step  # elapsed seconds

        hr = hr_base + 4 * np.sin(2 * np.pi * 0.10 * t) + rng.normal(0, 1.5)
        sbp = sbp_base + 10 * np.sin(2 * np.pi * 0.05 * t) + rng.normal(0, 3)
        dbp = dbp_base + 5 * np.sin(2 * np.pi * 0.05 * t + 0.5) + rng.normal(0, 2)
        rr = rr_base + 2 * np.sin(2 * np.pi * 0.03 * t) + rng.normal(0, 0.5)
        spo2 = spo2_base + rng.normal(0, 0.2)

        yield {
            "elapsed_s": round(t, 1),
            "HR": round(hr, 1),
            "SBP": round(sbp, 1),
            "DBP": round(dbp, 1),
            "RR": round(rr, 1),
            "SpO2": round(spo2, 1),
        }

        if duration and t + step >= duration:
            break

        i += 1
        time.sleep(step)

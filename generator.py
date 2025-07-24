# generator.py
# ---------------------------------------------------------------
# Lightweight vital‑sign + waveform generator for Streamlit demos.
# Emits one dictionary per second that includes:
#   • Numeric vitals (HR, SBP, DBP, RR, SpO₂)
#   • 1‑second ECG strip (250 Hz)             -> key "ECG"
#   • 1‑second pleth/PPG strip (100 Hz)       -> key "PLETH"
# ---------------------------------------------------------------

import time
from typing import Dict, Generator, Optional

import numpy as np
import neurokit2 as nk


def vitals_stream(
    duration: Optional[float] = None,    # total seconds (None = endless)
    fs: float = 1.0,                     # numeric vitals frequency
    seed: Optional[int] = None,
    hr_base: float = 75,
    sbp_base: float = 120,
    dbp_base: float = 80,
    rr_base: float = 16,
    spo2_base: float = 98,
) -> Generator[Dict[str, float], None, None]:
    """
    Yield one vital‑sign record every 1/fs seconds.

    Each record contains:
      elapsed_s, HR, SBP, DBP, RR, SpO2, ECG (list[float]), PLETH (list[float])
    """
    rng = np.random.default_rng(seed)
    step = 1.0 / fs
    i = 0

    while True:
        t = i * step  # elapsed seconds

        # ---- numeric vitals -------------------------------------------------
        hr = hr_base + 4 * np.sin(2 * np.pi * 0.10 * t) + rng.normal(0, 1.5)
        sbp = sbp_base + 10 * np.sin(2 * np.pi * 0.05 * t) + rng.normal(0, 3)
        dbp = dbp_base + 5 * np.sin(2 * np.pi * 0.05 * t + 0.5) + rng.normal(0, 2)
        rr = rr_base + 2 * np.sin(2 * np.pi * 0.03 * t) + rng.normal(0, 0.5)
        spo2 = spo2_base + rng.normal(0, 0.2)

        # ---- waveforms ------------------------------------------------------
        ecg = nk.ecg_simulate(duration=1, sampling_rate=250, heart_rate=hr)
        pleth = nk.ppg_simulate(duration=1, sampling_rate=100)

        yield {
            "elapsed_s": round(t, 1),
            "HR": round(hr, 1),
            "SBP": round(sbp, 1),
            "DBP": round(dbp, 1),
            "RR": round(rr, 1),
            "SpO2": round(spo2, 1),
            "ECG": ecg.tolist(),       # 250‑point list
            "PLETH": pleth.tolist(),   # 100‑point list
        }

        if duration and t + step >= duration:
            break

        i += 1
        time.sleep(step)

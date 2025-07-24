"""
generator.py
------------
Synthetic vital‑sign streamer for the Streamlit monitor demo.
Yields:
  • HR, SBP, DBP, RR, SpO2, ICP  (numeric)
  • 1‑second ECG  strip @ 250 Hz
  • 1‑second Pleth strip @ 100 Hz
  • 1‑second Resp  strip @  25 Hz
"""

import time
import numpy as np
from typing import Dict, Generator, Optional

# waveform sample rates (used by app.py as well)
ECG_FS   = 250
PLETH_FS = 100
RESP_FS  = 25

# ---------- helper: one‑second waveform templates --------------------------
# Make a 5‑s “ring buffer” once; later we just roll & slice -> very fast
TEMPLATE_SEC = 5
t_ecg = np.linspace(0, TEMPLATE_SEC, ECG_FS * TEMPLATE_SEC, endpoint=False)
t_ppg = np.linspace(0, TEMPLATE_SEC, PLETH_FS * TEMPLATE_SEC, endpoint=False)
t_rsp = np.linspace(0, TEMPLATE_SEC, RESP_FS  * TEMPLATE_SEC, endpoint=False)

ecg_template = 0.01 * np.random.randn(len(t_ecg))
for beat in range(TEMPLATE_SEC):
    spike = beat * ECG_FS + ECG_FS // 4          # simple R‑wave
    ecg_template[spike - 1: spike + 2] += [0.2, 1.0, 0.2]

pleth_template = 0.6 + 0.3 * np.sin(2 * np.pi * 1.2 * t_ppg) \
                       + 0.01 * np.random.randn(len(t_ppg))

resp_template = 0.2 * np.sin(2 * np.pi * 0.25 * t_rsp)       # 15 bpm resp

# ---------------------------------------------------------------------------


def vitals_stream(duration: Optional[int] = None, fs: float = 1.0
                  ) -> Generator[Dict[str, float], None, None]:
    """
    Stream one vital‑sign record every 1/fs seconds.

    Baseline ranges (when no crisis is active):
      HR    89–95 bpm
      SBP   120–135 mmHg, DBP 80–89
      SpO2  96–98 %
      ICP   5–12  mmHg
      RR    14–18 bpm
    """
    rng = np.random.default_rng()
    step = 1.0 / fs
    i = 0

    while True:
        t = i * step

        # ---------- numeric vitals in baseline range ----------------------
        hr   = np.clip(92  + rng.normal(0, 1.5), 89, 95)
        sbp  = np.clip(127 + rng.normal(0, 4),   120, 135)
        dbp  = np.clip(85  + rng.normal(0, 3),   80,  89)
        rr   = np.clip(16  + rng.normal(0, .6),  14,  18)
        spo2 = np.clip(97  + rng.normal(0, .3),  96,  98)
        icp  = np.clip(8.5 + rng.normal(0, 2),   5,   12)

        # ---------- 1‑s waveform slices (rolling ring buffer) -------------
        shift_ecg   = (i * ECG_FS)   % len(ecg_template)
        shift_ppg   = (i * PLETH_FS) % len(pleth_template)
        shift_resp  = (i * RESP_FS)  % len(resp_template)

        ecg_1s   = np.roll(ecg_template,   -shift_ecg)  [:ECG_FS]
        pleth_1s = np.roll(pleth_template, -shift_ppg)  [:PLETH_FS]
        resp_1s  = np.roll(resp_template,  -shift_resp) [:RESP_FS]

        yield {
            "elapsed_s": round(t, 1),
            "HR": round(hr, 1),
            "SBP": round(sbp, 1),
            "DBP": round(dbp, 1),
            "RR": round(rr, 1),
            "SpO2": round(spo2, 1),
            "ICP": round(icp, 1),
            "ECG":   ecg_1s.tolist(),
            "PLETH": pleth_1s.tolist(),
            "RESP":  resp_1s.tolist(),
        }

        if duration and t + step >= duration:
            break

        i += 1
        time.sleep(step)

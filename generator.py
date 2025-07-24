"""
generator.py
------------
Streams synthetic vital‑sign data once per second.

Yields a dict with:
  • elapsed_s, HR, SBP, DBP, RR, SpO2, ICP
  • ECG      : list[float] length 250
  • PLETH    : list[float] length 100
  • RESP     : list[float] length  25
  • ICP_WAVE : list[float] length  50
"""

import time
from typing import Dict, Generator, Optional

import numpy as np

# -------- waveform sample rates (imported by app.py) -----------------
ECG_FS   = 250
PLETH_FS = 100
RESP_FS  = 25
ICP_FS   = 50           # matches the P1‑P2‑P3 sketch

BUFFER_SEC = 5          # template length for ring buffers

# -------- helper: build 5‑second waveform templates ------------------
t_ecg = np.linspace(0, BUFFER_SEC, ECG_FS * BUFFER_SEC, endpoint=False)
t_ppg = np.linspace(0, BUFFER_SEC, PLETH_FS * BUFFER_SEC, endpoint=False)
t_rsp = np.linspace(0, BUFFER_SEC, RESP_FS * BUFFER_SEC, endpoint=False)
t_icp = np.linspace(0, 1, ICP_FS, endpoint=False)          # 1‑s pulse

# ECG template: baseline + R spikes (≈ 60 bpm reference)
ecg_template = 0.01 * np.random.randn(len(t_ecg))
for beat in range(BUFFER_SEC):
    idx = beat * ECG_FS + ECG_FS // 4
    ecg_template[idx - 1: idx + 2] += [0.2, 1.0, 0.2]

# Pleth template: arterial pulse‑like sine
pleth_template = 0.6 + 0.3 * np.sin(2 * np.pi * 1.2 * t_ppg) \
                       + 0.01 * np.random.randn(len(t_ppg))

# Resp template: 15 bpm sinusoid
resp_template = 0.2 * np.sin(2 * np.pi * 0.25 * t_rsp)

# ICP pulse (P1/P2/P3) then tiled to 5 s
p1 = 12 * np.exp(-((t_icp - 0.18) / 0.04) ** 2)
p2 = 8  * np.exp(-((t_icp - 0.45) / 0.06) ** 2)
p3 = 4  * np.exp(-((t_icp - 0.72) / 0.05) ** 2)
icp_pulse = p1 + p2 + p3
icp_template = np.tile(icp_pulse, BUFFER_SEC)

# ---------------------------------------------------------------------


def vitals_stream(duration: Optional[int] = None, fs: float = 1.0
                  ) -> Generator[Dict[str, float], None, None]:
    """
    Stream one record every 1/fs seconds.

    Baseline numeric ranges:
        HR    89–95   bpm
        SBP   120–135 mmHg, DBP 80–89
        RR    14–18   bpm
        SpO2  96–98   %
        ICP   5–12    mmHg
    """
    rng  = np.random.default_rng()
    step = 1.0 / fs
    i = 0

    while True:
        t = i * step

        # ---------- numeric vitals --------------------------------------
        hr   = np.clip(92  + rng.normal(0, 1.5), 89, 95)
        sbp  = np.clip(127 + rng.normal(0, 4),   120, 135)
        dbp  = np.clip(85  + rng.normal(0, 3),   80,  89)
        rr   = np.clip(16  + rng.normal(0, .6),  14,  18)
        spo2 = np.clip(97  + rng.normal(0, .3),  96,  98)
        icp  = np.clip(8.5 + rng.normal(0, 2),   5,   12)

        # ---------- waveform slices (ring‑buffer roll) ------------------
        shift_ecg  = (i * ECG_FS)   % len(ecg_template)
        shift_ppg  = (i * PLETH_FS) % len(pleth_template)
        shift_rsp  = (i * RESP_FS)  % len(resp_template)
        shift_icp  = (i * ICP_FS)   % len(icp_template)

        ecg_1s   = np.roll(ecg_template,   -shift_ecg) [:ECG_FS]
        pleth_1s = np.roll(pleth_template, -shift_ppg) [:PLETH_FS]
        resp_1s  = np.roll(resp_template,  -shift_rsp) [:RESP_FS]
        icp_1s   = np.roll(icp_template,   -shift_icp) [:ICP_FS]

        yield {
            "elapsed_s": round(t, 1),
            "HR":   round(hr, 1),
            "SBP":  round(sbp, 1),
            "DBP":  round(dbp, 1),
            "RR":   round(rr, 1),
            "SpO2": round(spo2, 1),
            "ICP":  round(icp, 1),
            "ECG":       ecg_1s.tolist(),
            "PLETH":     pleth_1s.tolist(),
            "RESP":      resp_1s.tolist(),
            "ICP_WAVE":  icp_1s.tolist(),
        }

        # stop after given duration
        if duration and t + step >= duration:
            break

        i += 1
        time.sleep(step)

"""
generator.py
------------
Streams baseline vitals and 4 waveforms every second.

Yields a dict with keys:
  HR, SBP, DBP, RR, SpO2, ICP, ECG, PLETH, RESP, ICP_WAVE
"""

import time
from typing import Dict, Generator, Optional
import numpy as np

# sample rates (imported by app.py)
ECG_FS   = 250
PLETH_FS = 100
RESP_FS  = 25
ICP_FS   = 50          # one ICP pulse has P1 > P2 > P3 baseline

# 5‑second ring‑buffer templates ------------------------------------------------
T = 5
t_ecg   = np.linspace(0, T, ECG_FS * T,   endpoint=False)
t_ppg   = np.linspace(0, T, PLETH_FS * T, endpoint=False)
t_resp  = np.linspace(0, T, RESP_FS * T,  endpoint=False)
t_icp1s = np.linspace(0, 1, ICP_FS,       endpoint=False)

rng = np.random.default_rng()

# ECG baseline with R‑spikes
ecg_buf = 0.01 * rng.normal(size=len(t_ecg))
for beat in range(T):
    i = beat * ECG_FS + ECG_FS // 4
    ecg_buf[i-1:i+2] += [0.2, 1.0, 0.2]

# Pleth (arterial pulse surrogate)
pleth_buf = 0.6 + 0.3*np.sin(2*np.pi*1.2*t_ppg) + 0.01*rng.normal(size=len(t_ppg))

# Resp (15 bpm sine)
resp_buf = 0.2*np.sin(2*np.pi*0.25*t_resp)

# ICP baseline pulse P1>P2>P3
p1 = 12*np.exp(-((t_icp1s-0.18)/0.04)**2)
p2 =  8*np.exp(-((t_icp1s-0.45)/0.06)**2)
p3 =  4*np.exp(-((t_icp1s-0.72)/0.05)**2)
icp_pulse_normal = p1 + p2 + p3
icp_buf = np.tile(icp_pulse_normal, T)   # 5‑s ring

# ------------------------------------------------------------------------------
def vitals_stream(duration: Optional[int]=None, fs: float=1.0
                  ) -> Generator[Dict[str, float], None, None]:
    """Emit one record every 1/fs seconds."""
    step = 1.0 / fs
    i = 0
    while True:
        t = i * step
        # numeric baseline ranges
        hr   = np.clip(92  + rng.normal(0, 1.5), 89, 95)
        sbp  = np.clip(127 + rng.normal(0, 4),   120, 135)
        dbp  = np.clip(85  + rng.normal(0, 3),   80,  89)
        rr   = np.clip(16  + rng.normal(0, .6),  14,  18)
        spo2 = np.clip(97  + rng.normal(0, .3),  96,  98)
        icp  = np.clip(8.5 + rng.normal(0, 2),   5,   12)

        # waveform slices (ring‑buffer roll)
        s_ecg   = (i*ECG_FS)   % len(ecg_buf)
        s_ppg   = (i*PLETH_FS) % len(pleth_buf)
        s_resp  = (i*RESP_FS)  % len(resp_buf)
        s_icp   = (i*ICP_FS)   % len(icp_buf)

        yield {
            "elapsed_s": round(t,1),
            "HR": round(hr,1), "SBP": round(sbp,1), "DBP": round(dbp,1),
            "RR": round(rr,1), "SpO2": round(spo2,1), "ICP": round(icp,1),
            "ECG":   np.roll(ecg_buf,  -s_ecg) [:ECG_FS ].tolist(),
            "PLETH": np.roll(pleth_buf,-s_ppg) [:PLETH_FS].tolist(),
            "RESP":  np.roll(resp_buf, -s_resp)[:RESP_FS ].tolist(),
            "ICP_WAVE": np.roll(icp_buf, -s_icp)[:ICP_FS].tolist(),
        }

        if duration and t+step >= duration:
            break
        i += 1
        time.sleep(step)

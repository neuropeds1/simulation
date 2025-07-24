"""
generator.py
------------
Streams synthetic vitals and four 1‑second waveforms every second.

Yields a dict with:
  elapsed_s, HR, SBP, DBP, RR, SpO2, ICP,
  ECG (250 pts), PLETH (100 pts), RESP (25 pts), ICP_WAVE (50 pts)
"""

import time
from typing import Dict, Generator, Optional
import numpy as np

# sample rates (imported by app.py)
ECG_FS   = 250
PLETH_FS = 100
RESP_FS  = 25
ICP_FS   = 50           # ICP waveform strip

TEMPLATE_SEC = 5        # ring‑buffer length
rng = np.random.default_rng()

# ---------------------------------------------------------------------
# Build waveform templates (5‑s ring buffers)
# ---------------------------------------------------------------------
t_ecg = np.linspace(0, TEMPLATE_SEC, ECG_FS*TEMPLATE_SEC, endpoint=False)
t_ppg = np.linspace(0, TEMPLATE_SEC, PLETH_FS*TEMPLATE_SEC, endpoint=False)
t_rsp = np.linspace(0, TEMPLATE_SEC, RESP_FS*TEMPLATE_SEC, endpoint=False)

# ECG baseline + R‑spikes (~60 bpm)
ecg_buf = 0.01*rng.normal(size=len(t_ecg))
for beat in range(TEMPLATE_SEC):
    idx = beat*ECG_FS + ECG_FS//4
    ecg_buf[idx-1:idx+2] += [0.2, 1.0, 0.2]

# Pleth surrogate waveform
pleth_buf = 0.6 + 0.3*np.sin(2*np.pi*1.2*t_ppg) + 0.01*rng.normal(size=len(t_ppg))

# Respiration (15 bpm sine)
resp_buf = 0.2*np.sin(2*np.pi*0.25*t_rsp)

# ICP baseline pulse (P1>P2>P3)
t_icp1s = np.linspace(0, 1, ICP_FS, endpoint=False)
p1 = 12*np.exp(-((t_icp1s-0.18)/0.04)**2)
p2 =  8*np.exp(-((t_icp1s-0.45)/0.06)**2)
p3 =  4*np.exp(-((t_icp1s-0.72)/0.05)**2)
icp_buf = np.tile(p1+p2+p3, TEMPLATE_SEC)

# ---------------------------------------------------------------------
def vitals_stream(duration: Optional[int]=None, fs: float=1.0
                  ) -> Generator[Dict[str, float], None, None]:
    """Yield one record every 1/fs seconds."""
    step = 1.0/fs
    i = 0
    while True:
        t = i*step
        # baseline numeric vitals
        hr   = np.clip(92 + rng.normal(0,1.5), 89, 95)
        sbp  = np.clip(127+ rng.normal(0,4),   120,135)
        dbp  = np.clip(85 + rng.normal(0,3),   80, 89)
        rr   = np.clip(16 + rng.normal(0,.6),  14, 18)
        spo2 = np.clip(97 + rng.normal(0,.3),  96, 98)
        icp  = np.clip(8.5+rng.normal(0,2),    5,  12)

        # slice waveforms
        s_ecg  = (i*ECG_FS)%len(ecg_buf)
        s_ppg  = (i*PLETH_FS)%len(pleth_buf)
        s_rsp  = (i*RESP_FS)%len(resp_buf)
        s_icp  = (i*ICP_FS)%len(icp_buf)

        yield {
            "elapsed_s": round(t,1),
            "HR": round(hr,1), "SBP": round(sbp,1), "DBP": round(dbp,1),
            "RR": round(rr,1), "SpO2": round(spo2,1), "ICP": round(icp,1),
            "ECG":   np.roll(ecg_buf,  -s_ecg) [:ECG_FS ].tolist(),
            "PLETH": np.roll(pleth_buf,-s_ppg) [:PLETH_FS].tolist(),
            "RESP":  np.roll(resp_buf, -s_rsp) [:RESP_FS ].tolist(),
            "ICP_WAVE": np.roll(icp_buf,-s_icp)[:ICP_FS ].tolist(),
        }
        if duration and t+step>=duration:
            break
        i+=1
        time.sleep(step)

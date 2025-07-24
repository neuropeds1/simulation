# generator.py  (fast version – no per‑loop NeuroKit call)
import time
import numpy as np
from typing import Dict, Generator, Optional

ECG_FS   = 250   # Hz
PLETH_FS = 100   # Hz

# ----------------------------------------------------------------------
# Pre‑build one 5‑second template ECG + pleth waveform
# ----------------------------------------------------------------------
TEMPLATE_LEN = 5                                 # seconds
t_ecg   = np.linspace(0, TEMPLATE_LEN, ECG_FS*TEMPLATE_LEN, endpoint=False)
t_ppg   = np.linspace(0, TEMPLATE_LEN, PLETH_FS*TEMPLATE_LEN, endpoint=False)

# ECG template: flat baseline + spikes every 1 s  (≈ 60 bpm)
ecg_template = 0.005*np.random.randn(len(t_ecg))
for beat in range(TEMPLATE_LEN):                 # one spike per second
    idx = beat*ECG_FS + ECG_FS//4                # offset 250 ms
    ecg_template[idx-1:idx+2] += [0.15, 1.0, 0.15]

# Pleth template: smooth sine + small noise
pleth_template = 0.5 + 0.4*np.sin(2*np.pi*1.2*t_ppg) + 0.01*np.random.randn(len(t_ppg))
# ----------------------------------------------------------------------


def vitals_stream(duration: Optional[float] = None,
                  fs: float = 1.0,
                  seed: Optional[int] = None,
                  hr_base: float = 75,
                  sbp_base: float = 120,
                  dbp_base: float = 80,
                  rr_base: float = 16,
                  spo2_base: float = 98
                  ) -> Generator[Dict[str, float], None, None]:
    """
    Yield numeric vitals + 1‑s ECG & pleth strips every second.
    """
    rng  = np.random.default_rng(seed)
    step = 1.0 / fs
    i    = 0

    while True:
        t = i * step

        # ── numeric vitals (cheap) ──────────────────────────────────────────
        hr   = hr_base  + 4*np.sin(2*np.pi*0.10*t)    + rng.normal(0, 1.5)
        sbp  = sbp_base + 10*np.sin(2*np.pi*0.05*t)   + rng.normal(0, 3)
        dbp  = dbp_base + 5*np.sin(2*np.pi*0.05*t+.5) + rng.normal(0, 2)
        rr   = rr_base  + 2*np.sin(2*np.pi*0.03*t)    + rng.normal(0, .5)
        spo2 = spo2_base+ rng.normal(0, .2)

        # ── grab a 1‑s slice from the template waveforms ───────────────────
        # Scroll through the template in a ring‑buffer manner
        s_ecg   = (i * ECG_FS)   % len(ecg_template)
        s_ppg   = (i * PLETH_FS) % len(pleth_template)
        ecg_1s  = np.roll(ecg_template, -s_ecg)  [:ECG_FS]
        pleth_1s= np.roll(pleth_template, -s_ppg)[:PLETH_FS]

        yield {
            "elapsed_s": round(t, 1),
            "HR": round(hr, 1), "SBP": round(sbp, 1),
            "DBP": round(dbp, 1), "RR": round(rr, 1),
            "SpO2": round(spo2, 1),
            "ECG":   ecg_1s.tolist(),
            "PLETH": pleth_1s.tolist()
        }

        if duration and t + step >= duration:
            break

        i += 1
        time.sleep(step)

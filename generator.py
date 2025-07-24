# generator.py  – baseline + ICP‑crisis ranges
import time
import numpy as np
from typing import Dict, Generator, Optional

ECG_FS, PLETH_FS = 250, 100           # waveform sample rates
RNG = np.random.default_rng()         # global RNG so app.py can share it

# --------------------------------------------------------------------------
# Build  5‑second template waveforms once (unchanged from previous version)
# --------------------------------------------------------------------------
T_LEN = 5
t_ecg   = np.linspace(0, T_LEN, ECG_FS*T_LEN,   endpoint=False)
t_ppg   = np.linspace(0, T_LEN, PLETH_FS*T_LEN, endpoint=False)

ecg_template = 0.005*np.random.randn(len(t_ecg))
for beat in range(T_LEN):
    idx = beat*ECG_FS + ECG_FS//4
    ecg_template[idx-1:idx+2] += [0.15, 1.0, 0.15]

pleth_template = (
    0.5 + 0.4*np.sin(2*np.pi*1.2*t_ppg) + 0.01*np.random.randn(len(t_ppg))
)
# --------------------------------------------------------------------------


def vitals_stream(
    duration: Optional[float] = None,    # total seconds
    fs: float = 1.0                      # numeric vitals frequency
) -> Generator[Dict[str, float], None, None]:
    """
    Yield one record per second:
        • HR  89–95  bpm
        • SBP 120–135 / DBP 80–89 mmHg
        • SpO₂ 96–98 %
        • ICP 5–12   mmHg
        • 1‑s ECG + pleth arrays
    The app can overwrite any field (e.g. crisis vitals) before plotting.
    """
    i = 0
    step = 1.0 / fs

    while True:
        t = i * step

        # ---------- baseline numeric vitals with gentle jitter -------------
        hr   = np.clip(92  + RNG.normal(0, 1.5), 89, 95)     # bpm
        sbp  = np.clip(127 + RNG.normal(0, 4),   120, 135)   # mmHg
        dbp  = np.clip(85  + RNG.normal(0, 3),   80,  89)    # mmHg
        rr   = np.clip(16  + RNG.normal(0, 0.6), 14,  18)    # breaths
        spo2 = np.clip(97  + RNG.normal(0, 0.3), 96,  98)    # %
        icp  = np.clip(8.5 + RNG.normal(0, 2),   5,   12)    # mmHg

        # ---------- 1‑s waveform slices ------------------------------------
        s_ecg   = (i * ECG_FS)   % len(ecg_template)
        s_ppg   = (i * PLETH_FS) % len(pleth_template)
        ecg_1s  = np.roll(ecg_template,  -s_ecg)  [:ECG_FS]
        pleth_1s= np.roll(pleth_template, -s_ppg) [:PLETH_FS]

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
        }

        if duration and t + step >= duration:
            break

        i += 1
        time.sleep(step)

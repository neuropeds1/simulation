"""
generator.py  ── Runs a background Pulse Physiology Engine instance and
exposes the latest vitals via get_vitals().

USAGE (from app.py):
    from generator import start_sim, get_vitals
    start_sim()          # spins up a thread once
    ...
    vitals = get_vitals()
"""
import threading, time, math
from collections import deque

# ---------- Pulse Physiology Engine ------------------------------------
# Install once in your venv:  pip install git+https://gitlab.kitware.com/physiology/engine.git
from pulse.engine import PulseEngine

# Public dictionary updated every 100 ms
_latest = {
    "HR": 0,  "SBP": 0,  "DBP": 0, "MAP": 0,
    "SpO2": 0, "ICP": 0,
    "ABP_wave": deque(maxlen=300),   # 3 s at 100 Hz
    "ICP_wave": deque(maxlen=300),
}

_RUN_FLAG = False

def _pulse_thread():
    """Advance Pulse in real time and refresh _latest."""
    engine = PulseEngine()
    engine.initialize_patient("StandardMale.json")
    dt = 0.01          # 100 Hz simulation
    t0 = time.time()

    while _RUN_FLAG:
        engine.advance_time_s(dt)

        # Scalars
        hr   = engine.get_scalar("HeartRate").value()
        map_ = engine.get_scalar("MeanArterialPressure").value()
        spo2 = engine.get_scalar("OxygenSaturation").value()
        icp  = engine.get_scalar("IntracranialPressure").value()

        sbp, dbp = map_ + 20, map_ - 20        # crude pulse pressure

        # Synthetic waveforms (simple beats around mean values)
        f = hr / 60.0                  # Hz
        t = time.time() - t0
        abp_val = map_ + (sbp - dbp)/2 * math.sin(2*math.pi*f*t)
        icp_val = icp  + 2 * math.sin(2*math.pi*f*t)

        # Atomically update shared dict
        _latest.update(dict(
            HR=hr, SBP=sbp, DBP=dbp, MAP=map_,
            SpO2=spo2, ICP=icp,
        ))
        _latest["ABP_wave"].append(abp_val)
        _latest["ICP_wave"].append(icp_val)

        time.sleep(dt)

def start_sim():
    """Call once from app.py; safe to call repeatedly."""
    global _RUN_FLAG
    if not _RUN_FLAG:
        _RUN_FLAG = True
        threading.Thread(target=_pulse_thread, daemon=True).start()

def stop_sim():
    global _RUN_FLAG
    _RUN_FLAG = False

def get_vitals():
    """Return a *copy* of the latest vitals dict."""
    data = _latest.copy()
    # make true copies of the deques so caller can iterate safely
    data["ABP_wave"] = list(_latest["ABP_wave"])
    data["ICP_wave"] = list(_latest["ICP_wave"])
    return data

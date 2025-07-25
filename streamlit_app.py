# streamlit_app.py  ── Streamlit front‑end that consumes generator.py
import streamlit as st, numpy as np, time
from threading import Thread
from collections import deque
from generator import start_sim, get_vitals

# ----- kick off the Pulse engine in the background --------------------
start_sim()

# ----- Streamlit page config & placeholders ---------------------------
st.set_page_config("Pulse‑Driven Monitor", layout="wide")
st.title("🩺 Neuro‑oriented Vitals Monitor (all Python)")

place_tiles = st.columns(6)
labels = ["HR (bpm)", "SBP (mmHg)", "DBP (mmHg)",
          "MAP (mmHg)", "SpO₂ (%)", "ICP (mmHg)"]

# 8‑second rolling waveforms at 20 Hz UI refresh
BUF = 160
abp_buf = deque([0.0]*BUF, maxlen=BUF)
icp_buf = deque([0.0]*BUF, maxlen=BUF)
wf_abp = st.line_chart(np.zeros(BUF))
wf_icp = st.line_chart(np.zeros(BUF))

# ----- live update loop ------------------------------------------------
while True:
    v = get_vitals()          # dict from generator.py

    # Update numeric tiles
    values = [v["HR"], v["SBP"], v["DBP"], v["MAP"], v["SpO2"], v["ICP"]]
    for col, lab, val in zip(place_tiles, labels, values):
        col.metric(lab, f"{val:.1f}" if lab.startswith("SpO") else f"{val:.0f}")

    # Update waveforms
    abp_buf.extend(v["ABP_wave"][-1:])
    icp_buf.extend(v["ICP_wave"][-1:])
    wf_abp.add_rows(np.array(abp_buf).reshape(-1,1))
    wf_icp.add_rows(np.array(icp_buf).reshape(-1,1))

    time.sleep(0.05)          # 20 Hz UI refresh

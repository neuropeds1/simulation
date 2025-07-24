# app.py  ─────────────────────────────────────────────────────────────────────
import time, numpy as np, pandas as pd, altair as alt, plotly.graph_objects as go
import streamlit as st
from generator import vitals_stream, ECG_FS, PLETH_FS, RESP_FS

# ――― Streamlit page ----------------------------------------------------------------
st.set_page_config(page_title="Sim‑Vitals Monitor", layout="wide")
st.title("🩺 Simulated Patient Monitor")

# ――― sidebar controls ---------------------------------------------------------------
duration_min = st.sidebar.slider("Scenario duration (minutes)", 0.5, 10.0, 2.0, 0.5)
start_btn    = st.sidebar.button("▶️ Start / Restart", use_container_width=True)
icp_btn      = st.sidebar.button("⚠️ ICP Crisis",      use_container_width=True)

# ――― initialise session‑state -------------------------------------------------------
BUFFER_SEC = 10
keys = ["running", "gen", "df", "icp_active", "icp_timer",
        "buf_ecg", "buf_pleth", "buf_resp"]
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = None

# numeric DataFrame to hold last few seconds
if st.session_state.df is None:
    st.session_state.df = pd.DataFrame()

# waveform ring buffers
if st.session_state.buf_ecg is None:
    st.session_state.buf_ecg   = np.zeros(ECG_FS   * BUFFER_SEC)
    st.session_state.buf_pleth = np.zeros(PLETH_FS * BUFFER_SEC)
    st.session_state.buf_resp  = np.zeros(RESP_FS  * BUFFER_SEC)

# ――― handle Start / Restart ---------------------------------------------------------
if start_btn:
    st.session_state.running    = True
    st.session_state.gen        = vitals_stream(duration=int(duration_min * 60))
    st.session_state.df         = pd.DataFrame()
    st.session_state.icp_active = False
    st.session_state.icp_timer  = None
    for buf in ("buf_ecg", "buf_pleth", "buf_resp"):
        st.session_state[buf].fill(0)

# ――― handle ICP crisis button -------------------------------------------------------
if icp_btn and st.session_state.running:
    st.session_state.icp_active = True
    st.session_state.icp_timer  = time.time()

# ――― generate / override one‑second chunk -------------------------------------------
if st.session_state.running:
    try:
        row = next(st.session_state.gen)

        # crisis override  (60‑s window)
        if st.session_state.icp_active:
            if time.time() - st.session_state.icp_timer <= 60:
                row["HR"]   = np.random.normal(34,   0.5)
                row["SBP"]  = np.random.normal(190,  3)
                row["DBP"]  = np.random.normal(105,  2)
                row["ICP"]  = np.random.normal(45,   1)
                row["SpO2"] = np.random.normal(98,   0.2)
            else:
                st.session_state.icp_active = False

        # append numeric row
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([row])], ignore_index=True
        ).tail(10)

        # roll waveform buffers
        st.session_state.buf_ecg   = np.roll(st.session_state.buf_ecg,   -ECG_FS)
        st.session_state.buf_pleth = np.roll(st.session_state.buf_pleth, -PLETH_FS)
        st.session_state.buf_resp  = np.roll(st.session_state.buf_resp,  -RESP_FS)

        st.session_state.buf_ecg[-ECG_FS:]     = row["ECG"]
        st.session_state.buf_pleth[-PLETH_FS:] = row["PLETH"]
        st.session_state.buf_resp[-RESP_FS:]   = row["RESP"]

    except StopIteration:
        st.session_state.running = False

# ――― numeric dashboard --------------------------------------------------------------
if not st.session_state.df.empty:
    df = st.session_state.df
    cols = st.columns(6)
    cols[0].metric("HR (bpm)",    f"{df.HR.iloc[-1]:.0f}")
    cols[1].metric("SBP (mmHg)",  f"{df.SBP.iloc[-1]:.0f}")
    cols[2].metric("DBP (mmHg)",  f"{df.DBP.iloc[-1]:.0f}")
    cols[3].metric("RR (bpm)",    f"{df.RR.iloc[-1]:.0f}")
    cols[4].metric("SpO₂ (%)",    f"{df.SpO2.iloc[-1]:.0f}")
    cols[5].metric("ICP (mmHg)",  f"{df.ICP.iloc[-1]:.0f}")

# ――― waveform plots -----------------------------------------------------------------
def strip(buf, fs, title, color):
    t = np.linspace(-BUFFER_SEC, 0, len(buf))
    fig = go.Figure(go.Scatter(x=t, y=buf, mode="lines",
                               line=dict(color=color, width=1)))
    fig.update_layout(height=120, margin=dict(l=0,r=0,b=3,t=20),
                      paper_bgcolor="black", plot_bgcolor="black",
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      title=dict(text=title, font_color=color, x=0.01, y=0.9))
    return fig

with st.container():
    st.plotly_chart(strip(st.session_state.buf_ecg,   ECG_FS,   "ECG",   "#00FF00"),
                    use_container_width=True)
    st.plotly_chart(strip(st.session_state.buf_pleth, PLETH_FS, "PLETH","#00FFFF"),
                    use_container_width=True)
    st.plotly_chart(strip(st.session_state.buf_resp,  RESP_FS,  "RESP", "#FFFF00"),
                    use_container_width=True)

# ――― rerun loop every second --------------------------------------------------------
if st.session_state.running:
    time.sleep(1)
    (st.rerun() if hasattr(st, "rerun") else st.experimental_rerun())

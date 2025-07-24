# app.py  ─────────────────────────────────────────────────────────────────────
import time
import numpy as np                     # ⟵ NEW (for np.random.uniform)
import altair as alt
import pandas as pd
import streamlit as st
from generator import vitals_stream

# ── safe‑start for the DataFrame ─────────────────────────────────────────────
if "df" not in st.session_state or st.session_state.df is None:
    st.session_state.df = pd.DataFrame()

st.set_page_config(page_title="SimVitals", layout="wide")
st.title("🩺 Simulated Patient Monitor")

# ── sidebar ──────────────────────────────────────────────────────────────────
duration_min = st.sidebar.slider(
    "Scenario duration (minutes)", 0.5, 10.0, 2.0, 0.5
)
start_btn = st.sidebar.button("▶️ Start / Restart")
icp_btn   = st.sidebar.button("⚠️ ICP Crisis")      # ⟵ NEW button

# ── session‑state keys ───────────────────────────────────────────────────────
for key in ("running", "gen", "df", "icp_active", "icp_timer"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── handle Start / Restart ───────────────────────────────────────────────────
if start_btn:
    st.session_state.running    = True
    st.session_state.gen        = vitals_stream(
        duration=int(duration_min * 60), fs=1
    )
    st.session_state.df         = pd.DataFrame()
    st.session_state.icp_active = False
    st.session_state.icp_timer  = None

# ── handle ICP‑Crisis button ────────────────────────────────────────────────
if icp_btn and st.session_state.running:
    st.session_state.icp_active = True
    st.session_state.icp_timer  = time.time()

# ── main streaming loop ─────────────────────────────────────────────────────
if st.session_state.running:
    try:
        row = next(st.session_state.gen)   # 1‑second chunk

        # ---------- ICP‑CRISIS override (active for 60 s) -------------------------
    if st.session_state.icp_active:
    if time.time() - st.session_state.icp_timer <= 60:
        # centre values exactly where you want them
        row["HR"]   = np.random.normal(34, 0.5)          # 34 ± 0.5 bpm
        row["SBP"]  = np.random.normal(190, 3)           # 190 ± 3 mmHg
        row["DBP"]  = np.random.normal(105, 2)           # 105 ± 2 mmHg
        row["ICP"]  = np.random.normal(45, 1)            # 45 ± 1 mmHg
        row["SpO2"] = np.random.normal(98, 0.2)          # 98 ± 0.2 %

        # keep physiologic limits sane
        row["HR"]   = max(row["HR"], 30)
        row["SBP"]  = max(row["SBP"],  60)
        row["DBP"]  = max(row["DBP"],  30)
        row["ICP"]  = max(row["ICP"],   0)
        row["SpO2"] = np.clip(row["SpO2"], 70, 100)
    else:
        st.session_state.icp_active = False
# -------------------------------------------------------------------------


        # append new row
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([row])],
            ignore_index=True,
        )
        # keep only the last 10 s for snappy plotting
        st.session_state.df = st.session_state.df.tail(10)

    except StopIteration:
        st.session_state.running = False

# ── draw dashboard ──────────────────────────────────────────────────────────
if not st.session_state.df.empty:
    df = st.session_state.df

    col1, col2, col3, col4, col5, col6 = st.columns(6)      # ⟵ now 6 cols
    col1.metric("HR (bpm)",   f"{df.HR.iloc[-1]:.0f}")
    col2.metric("SBP (mmHg)", f"{df.SBP.iloc[-1]:.0f}")
    col3.metric("DBP (mmHg)", f"{df.DBP.iloc[-1]:.0f}")
    col4.metric("RR (bpm)",   f"{df.RR.iloc[-1]:.0f}")
    col5.metric("SpO₂ (%)",   f"{df.SpO2.iloc[-1]:.0f}")
    col6.metric("ICP (mmHg)", f"{df.ICP.iloc[-1]:.0f}")     # ⟵ NEW metric

    chart = (
        alt.Chart(df.melt("elapsed_s"))
        .mark_line()
        .encode(
            x=alt.X("elapsed_s:Q", title="Elapsed s"),
            y="value:Q",
            color=alt.Color("variable:N", title="Signal"),
        )
        .properties(height=220)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

# ── schedule next update ────────────────────────────────────────────────────
if st.session_state.running:
    time.sleep(1)
    (st.rerun() if hasattr(st, "rerun") else st.experimental_rerun())

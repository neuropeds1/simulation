# app.py  ──────────────────────────────────────────────────────────────────────
import time
import altair as alt
import pandas as pd
import streamlit as st
from generator import vitals_stream
import pandas as pd       # (already there in your file)

# --- safe initialisation -------------------------------------
if "df" not in st.session_state or st.session_state.df is None:
    st.session_state.df = pd.DataFrame()      # <-- start empty, not None
# -------------------------------------------------------------

st.set_page_config(page_title="SimVitals", layout="wide")
st.title("🩺 Simulated Patient Monitor")

# ── sidebar ───────────────────────────────────────────────────────────────────
duration_min = st.sidebar.slider("Scenario duration (minutes)",
                                 0.5, 10.0, 2.0, 0.5)
start_btn = st.sidebar.button("▶️  Start / Restart")

# ── session state init ────────────────────────────────────────────────────────
for key in ("running", "gen", "df"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── handle button press ───────────────────────────────────────────────────────
if start_btn:
    st.session_state.running = True
    st.session_state.gen = vitals_stream(duration=int(duration_min * 60), fs=1)
    st.session_state.df = pd.DataFrame()          # clear old trace

# ── main streaming logic ──────────────────────────────────────────────────────
if st.session_state.running:
    try:
        row = next(st.session_state.gen)          # 1‑second chunk
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([row])],
            ignore_index=True,
        )
    except StopIteration:
        st.session_state.running = False          # scenario finished

# ── draw dashboard if any data exist ──────────────────────────────────────────
if not st.session_state.df.empty:
    df = st.session_state.df

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("HR (bpm)",   f"{df.HR.iloc[-1]:.0f}")
    col2.metric("SBP (mmHg)", f"{df.SBP.iloc[-1]:.0f}")
    col3.metric("DBP (mmHg)", f"{df.DBP.iloc[-1]:.0f}")
    col4.metric("RR (bpm)",   f"{df.RR.iloc[-1]:.0f}")
    col5.metric("SpO₂ (%)",   f"{df.SpO2.iloc[-1]:.0f}")

    chart = (
        alt.Chart(df.tail(120).melt("elapsed_s"))
        .mark_line()
        .encode(
            x=alt.X("elapsed_s:Q", title="Elapsed s"),
            y="value:Q",
            color=alt.Color("variable:N", title="Signal"),
        )
        .properties(height=220)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

# ── schedule next update ──────────────────────────────────────────────────────
if st.session_state.running:
    time.sleep(1)                                # keep cadence neat
    if hasattr(st, "rerun"):                     # ≥ 1.47
        st.rerun()
    else:                                        # ≤ 1.46
        st.experimental_rerun()


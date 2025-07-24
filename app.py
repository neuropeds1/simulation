"""
app.py
------
Streamlit dashboard that subscribes to `vitals_stream` in generator.py
and updates in real time.  Ideal for demo / classroom use.
"""

import altair as alt
import pandas as pd
import streamlit as st
from generator import vitals_stream

st.set_page_config(page_title="SimVitals", layout="wide")
st.title("🩺 Simulated Patient Monitor")

# ── Sidebar controls ──────────────────────────────────────────────────────────
duration_min = st.sidebar.slider("Scenario duration (minutes)", 0.5, 10.0, 2.0, 0.5)
start_button = st.sidebar.button("▶️ Start")

# ── Persistent data store ─────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

placeholder = st.empty()  # container for dashboard widgets


def draw_dashboard(df: pd.DataFrame) -> None:
    """Render metrics + rolling waveform chart."""
    col1, col2, col3, col4, col5 = placeholder.columns(5)
    col1.metric("HR (bpm)", f"{df.HR.iloc[-1]:.0f}")
    col2.metric("SBP (mmHg)", f"{df.SBP.iloc[-1]:.0f}")
    col3.metric("DBP (mmHg)", f"{df.DBP.iloc[-1]:.0f}")
    col4.metric("RR (bpm)", f"{df.RR.iloc[-1]:.0f}")
    col5.metric("SpO₂ (%)", f"{df.SpO2.iloc[-1]:.0f}")

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


# ── Main loop ─────────────────────────────────────────────────────────────────
if start_button:
    # Reset stored data each run
    st.session_state.df = pd.DataFrame()

    for row in vitals_stream(duration=duration_min * 60, fs=1):
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([row])], ignore_index=True
        )
        draw_dashboard(st.session_state.df)
       # ⬆ with a version‑safe one:
if hasattr(st, "rerun"):          # Streamlit ≥ 1.47
    st.rerun()
else:                             # Streamlit ≤ 1.46 (keeps old name)
    st.experimental_rerun()


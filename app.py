# app.py  ──────────────────────────────────────────────────────────────
import time, numpy as np, pandas as pd, plotly.graph_objects as go
import streamlit as st
from generator import vitals_stream, ECG_FS, PLETH_FS, RESP_FS, ICP_FS

# ── page/controls ────────────────────────────────────────────────────
st.set_page_config(page_title="Sim‑Vitals Monitor", layout="wide")
st.title("🩺 Simulated Patient Monitor")

dur = st.sidebar.slider("Scenario duration (min)", 0.5, 10.0, 2.0, 0.5)
start_btn = st.sidebar.button("▶️ Start / Restart", use_container_width=True)
crisis_btn= st.sidebar.button("⚠️ ICP Crisis",      use_container_width=True)

# ── session‑state init ───────────────────────────────────────────────
BUF_S = 10
for k in ("run","gen","df","crisis","t0",
          "ecg","pleth","resp","icp"):
    if k not in st.session_state: st.session_state[k]=None

st.session_state.df = st.session_state.df or pd.DataFrame()
for name, fs in (("ecg",ECG_FS),("pleth",PLETH_FS),("resp",RESP_FS),("icp",ICP_FS)):
    if st.session_state[name] is None:
        st.session_state[name]=np.zeros(fs*BUF_S)

# ── helpers ──────────────────────────────────────────────────────────
def crisis_icp_wave():
    t=np.linspace(0,1,ICP_FS,endpoint=False)
    p1=10*np.exp(-((t-0.18)/0.04)**2)
    p2=16*np.exp(-((t-0.45)/0.05)**2)         # P2 tallest
    p3= 6*np.exp(-((t-0.72)/0.06)**2)
    return (p1+p2+p3).tolist()

def roll(buf, fs, data):
    buf=np.roll(buf,-fs); buf[-fs:]=data; return buf

def strip(buf,title,color):
    t=np.linspace(-BUF_S,0,len(buf))
    fig=go.Figure(go.Scatter(x=t,y=buf,mode="lines",
        line=dict(color=color,width=1)))
    fig.update_layout(height=120,margin=dict(l=0,r=0,b=2,t=20),
        paper_bgcolor="black",plot_bgcolor="black",
        xaxis=dict(visible=False),yaxis=dict(visible=False),
        title=dict(text=title,font_color=color,x=0.01,y=0.9))
    return fig

# ── start/restart ────────────────────────────────────────────────────
if start_btn:
    st.session_state.run=True
    st.session_state.gen=vitals_stream(duration=int(dur*60))
    st.session_state.df=pd.DataFrame()
    st.session_state.crisis=False
    for b in ("ecg","pleth","resp","icp"): st.session_state[b].fill(0)

# ── trigger crisis ───────────────────────────────────────────────────
if crisis_btn and st.session_state.run:
    st.session_state.crisis=True
    st.session_state.t0=time.time()

# ── main loop (1‑s) ─────────────────────────────────────────────────
if st.session_state.run:
    row=next(st.session_state.gen)
    # crisis override
    if st.session_state.crisis:
        if time.time()-st.session_state.t0<=60:
            row.update(
                HR   =34+np.random.normal(0,0.5),
                SBP  =190+np.random.normal(0,3),
                DBP  =105+np.random.normal(0,2),
                ICP  =45+np.random.normal(0,1),
                SpO2 =98+np.random.normal(0,0.2),
                ICP_WAVE=crisis_icp_wave()
            )
        else:
            st.session_state.crisis=False

    # save numeric
    st.session_state.df=pd.concat(
        [st.session_state.df,pd.DataFrame([row])],
        ignore_index=True).tail(10)

    # roll waveforms
    st.session_state.ecg   = roll(st.session_state.ecg,   ECG_FS,  row["ECG"])
    st.session_state.pleth = roll(st.session_state.pleth, PLETH_FS,row["PLETH"])
    st.session_state.resp  = roll(st.session_state.resp,  RESP_FS, row["RESP"])
    st.session_state.icp   = roll(st.session_state.icp,   ICP_FS,  row["ICP_WAVE"])

# ── numeric dashboard ───────────────────────────────────────────────
if not st.session_state.df.empty:
    d=st.session_state.df
    c=st.columns(6)
    c[0].metric("HR (bpm)",   f"{d.HR.iloc[-1]:.0f}")
    c[1].metric("SBP (mmHg)", f"{d.SBP.iloc[-1]:.0f}")
    c[2].metric("DBP (mmHg)", f"{d.DBP.iloc[-1]:.0f}")
    c[3].metric("RR (bpm)",   f"{d.RR.iloc[-1]:.0f}")
    c[4].metric("SpO₂ (%)",   f"{d.SpO2.iloc[-1]:.0f}")
    c[5].metric("ICP (mmHg)", f"{d.ICP.iloc[-1]:.0f}")

# ── waveform panel ──────────────────────────────────────────────────
with st.container():
    st.plotly_chart(strip(st.session_state.ecg,  "ECG",  "#00FF00"),use_container_width=True)
    st.plotly_chart(strip(st.session_state.pleth,"PLETH","#00FFFF"),use_container_width=True)
    st.plotly_chart(strip(st.session_state.resp, "RESP", "#FFFF00"),use_container_width=True)
    st.plotly_chart(strip(st.session_state.icp,  "ICP",  "#FF00FF"),use_container_width=True)

# ── auto‑rerun every second ─────────────────────────────────────────
if st.session_state.run:
    time.sleep(1)
    (st.rerun() if hasattr(st,"rerun") else st.experimental_rerun())

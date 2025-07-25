"""
app.py  ── Bokeh server that displays vitals from generator.py.

RUN:
    python app.py
then browse to http://localhost:5006/sim
"""
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div
from bokeh.plotting import curdoc, figure
from bokeh.server.server import Server

from generator import start_sim, get_vitals

# ---------- initialise shared data sources ----------------------------
src_numbers = ColumnDataSource(dict(
    labels=["HR","SBP","DBP","MAP","SpO₂","ICP"],
    values=["--"]*6,
))

src_abp = ColumnDataSource(dict(x=list(range(300)), y=[0]*300))
src_icp = ColumnDataSource(dict(x=list(range(300)), y=[0]*300))

# ---------- build UI ---------------------------------------------------
title = Div(text="<h1 style='color:#004d80'>Pulse‑Driven Neuro Monitor</h1>")

def make_waveform(title_text, source):
    p = figure(height=150, width=800, title=title_text,
               x_axis_type=None, y_axis_type=None,
               toolbar_location=None)
    p.line("x", "y", source=source, line_width=2)
    return p

wave_abp = make_waveform("Arterial BP", src_abp)
wave_icp = make_waveform("ICP (synthetic beat)", src_icp)

numbers_html = Div(text="", style={"font-size":"28px", "line-height":"34px"})

layout = column(title, numbers_html, wave_abp, wave_icp)

# ---------- periodic callback -----------------------------------------
def update():
    vit = get_vitals()

    # Update numeric banner
    src_numbers.data["values"] = [
        f"{vit['HR']:.0f}",
        f"{vit['SBP']:.0f}",
        f"{vit['DBP']:.0f}",
        f"{vit['MAP']:.0f}",
        f"{vit['SpO2']:.1f}",
        f"{vit['ICP']:.1f}",
    ]
    numbers_html.text = "  ".join(
        f"<b>{lab}</b>: {val}" for lab,val in zip(src_numbers.data["labels"], src_numbers.data["values"])
    )

    # Update waveforms
    src_abp.data.update(y=vit["ABP_wave"])
    src_icp.data.update(y=vit["ICP_wave"])

def sim_app(doc):
    start_sim()                         # kicks off Pulse thread
    doc.add_root(layout)
    doc.add_periodic_callback(update, 100)   # ms

# ---------- launch ------------------------------------------------------
server = Server({'/sim': sim_app}, port=5006, allow_websocket_origin=["*"])
server.start()
print("Visit  http://localhost:5006/sim")
server.io_loop.start()

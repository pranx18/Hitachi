from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from storagepulse.analytics import detect_anomalies, forecast_capacity, health_score, recommendations
from storagepulse.data import SYSTEMS, load_telemetry

st.set_page_config(page_title="StoragePulse · Storage Intelligence", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stSidebar"] { border-right: 1px solid rgba(151,177,193,.12); }
.eyebrow { color: #55e6c1; font-size: .73rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; margin-bottom: .45rem; }
.hero-title { font-family: 'Segoe UI', sans-serif; font-size: 2.45rem; font-weight: 600; letter-spacing: -.05em; margin: 0; color: #edf5f8; }
.hero-subtitle { color: #91a4b0; margin-top: .35rem; }
.section-title { font-family: 'Segoe UI', sans-serif; font-size: 1.15rem; font-weight: 600; margin: 1.6rem 0 .75rem; }
.metric-label { color: #91a4b0; font-size: .78rem; font-weight: 600; letter-spacing: .03em; }
.metric-value { font-family: 'Segoe UI', sans-serif; font-size: 1.8rem; font-weight: 600; margin-top: .35rem; }
.metric-foot { color: #91a4b0; font-size: .78rem; margin-top: .25rem; }
.panel { background: linear-gradient(145deg, rgba(20,33,43,.9), rgba(15,24,32,.75)); border: 1px solid rgba(151,177,193,.12); border-radius: 14px; padding: 1rem 1.1rem; }
.alert-row { padding: .8rem 0; border-bottom: 1px solid rgba(151,177,193,.10); }
.alert-row:last-child { border-bottom: 0; }
.muted { color: #91a4b0; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading simulated storage telemetry…")
def get_data() -> pd.DataFrame:
    return load_telemetry()


def metric_card(label: str, value: str, note: str, accent: str = "#e8f0f5") -> None:
    st.markdown(
        f'<div class="panel"><div class="metric-label">{label}</div><div class="metric-value" style="color:{accent}">{value}</div><div class="metric-foot">{note}</div></div>',
        unsafe_allow_html=True,
    )


def format_tb(value: float) -> str:
    return f"{value:,.1f} TB"


with st.sidebar:
    st.markdown("<div class='eyebrow'>◉ &nbsp; STORAGEPULSE</div>", unsafe_allow_html=True)
    st.caption("Infrastructure intelligence")
    st.divider()
    st.markdown("**Storage system**")
    system_id = st.selectbox("Select a storage system", list(SYSTEMS), label_visibility="collapsed")
    st.caption(str(SYSTEMS[system_id]["site"]))
    st.divider()
    st.markdown("**Signal status**")
    st.success("All telemetry feeds online", icon="🟢")
    st.caption("Simulation · 120 days of daily data")
    st.caption("Last refreshed: " + pd.Timestamp.now().strftime("%b %d, %Y · %H:%M"))
    st.divider()
    st.caption("StoragePulse demo data is synthetic and for demonstration only.")

all_data = get_data()
history = all_data.loc[all_data["system_id"] == system_id].sort_values("timestamp").reset_index(drop=True)
scored = detect_anomalies(history)
latest = history.iloc[-1]
recent_anomalies = scored.loc[scored["is_anomaly"] & (scored["timestamp"] >= history["timestamp"].max() - pd.Timedelta(days=30))]
score = health_score(latest, len(recent_anomalies))
utilization = float(latest["used_tb"] / latest["capacity_tb"] * 100)
health_label = "Healthy" if score >= 78 else "Watch" if score >= 55 else "At risk"
health_color = "#55e6c1" if score >= 78 else "#f4bd6a" if score >= 55 else "#ff7b82"

head, action = st.columns([5, 1.25], vertical_alignment="bottom")
with head:
    st.markdown("<div class='eyebrow'>OPERATIONS OVERVIEW &nbsp; / &nbsp; STORAGE FLEET</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>Storage infrastructure</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='hero-subtitle'>{system_id} &nbsp;·&nbsp; {SYSTEMS[system_id]['site']} &nbsp;·&nbsp; Daily telemetry</div>", unsafe_allow_html=True)
with action:
    refresh = st.button("↻  Refresh forecast", use_container_width=True, type="primary")

if refresh or "forecast" not in st.session_state or st.session_state.get("forecast_system") != system_id:
    st.session_state["forecast"] = forecast_capacity(history, days=30)
    st.session_state["forecast_system"] = system_id
forecast = st.session_state["forecast"]

st.markdown("<div class='section-title'>System health</div>", unsafe_allow_html=True)
cols = st.columns(5, gap="medium")
with cols[0]: metric_card("HEALTH SCORE", f"{score}<span style='font-size:1rem;color:#91a4b0'> / 100</span>", health_label, health_color)
with cols[1]: metric_card("CAPACITY USED", f"{utilization:.1f}%", f"{format_tb(float(latest['used_tb']))} of {format_tb(float(latest['capacity_tb']))}", "#e8f0f5")
with cols[2]: metric_card("READ LATENCY", f"{latest['latency_ms']:.1f} ms", "Latest daily sample", "#e8f0f5")
with cols[3]: metric_card("IOPS", f"{latest['iops']:,.0f}", "Input / output operations per second", "#e8f0f5")
with cols[4]: metric_card("ANOMALIES", str(len(recent_anomalies)), "Detected in the last 30 days", "#ffbd69" if len(recent_anomalies) else "#55e6c1")

left, right = st.columns([1.7, 1], gap="large")
with left:
    st.markdown("<div class='section-title'>Capacity outlook</div>", unsafe_allow_html=True)
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=history["timestamp"], y=history["used_tb"], mode="lines", name="Used capacity", line={"color": "#55e6c1", "width": 2.5}, fill="tozeroy", fillcolor="rgba(85,230,193,.08)"))
    chart.add_trace(go.Scatter(x=forecast["timestamp"], y=forecast["used_tb"], mode="lines", name="30-day forecast", line={"color": "#9b8cff", "width": 2.5, "dash": "dash"}))
    chart.add_trace(go.Scatter(x=history["timestamp"], y=history["capacity_tb"], mode="lines", name="Total capacity", line={"color": "rgba(255,123,130,.65)", "width": 1.3, "dash": "dot"}))
    anomalies_on_chart = scored[scored["is_anomaly"]]
    if not anomalies_on_chart.empty:
        chart.add_trace(go.Scatter(x=anomalies_on_chart["timestamp"], y=anomalies_on_chart["used_tb"], mode="markers", name="Anomaly", marker={"color": "#ffbd69", "size": 9, "symbol": "diamond"}))
    chart.update_layout(height=360, margin={"l": 8, "r": 8, "t": 15, "b": 5}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "#91a4b0", "family": "DM Sans"}, legend={"orientation": "h", "y": 1.12, "x": 0}, hovermode="x unified")
    chart.update_xaxes(showgrid=False, linecolor="rgba(151,177,193,.14)")
    chart.update_yaxes(title="Capacity (TB)", gridcolor="rgba(151,177,193,.10)", zeroline=False)
    st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    st.caption("Forecast uses a Random Forest model trained on recent usage trends. Projection is indicative, not a guarantee.")

with right:
    st.markdown("<div class='section-title'>Performance signals</div>", unsafe_allow_html=True)
    perf = go.Figure()
    perf.add_trace(go.Scatter(x=history["timestamp"], y=history["latency_ms"], name="Latency (ms)", line={"color": "#ffbd69", "width": 2}, yaxis="y"))
    perf.add_trace(go.Scatter(x=history["timestamp"], y=history["throughput_mbps"], name="Throughput (MB/s)", line={"color": "#73a7ff", "width": 2}, yaxis="y2"))
    perf.update_layout(height=265, margin={"l": 5, "r": 5, "t": 18, "b": 5}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "#91a4b0"}, legend={"orientation": "h", "y": 1.13, "x": 0}, yaxis={"title": "ms", "gridcolor": "rgba(151,177,193,.10)"}, yaxis2={"title": "MB/s", "overlaying": "y", "side": "right", "showgrid": False}, hovermode="x unified")
    st.plotly_chart(perf, use_container_width=True, config={"displayModeBar": False})
    projected_tb = float(forecast["used_tb"].iloc[-1])
    delta_tb = projected_tb - float(latest["used_tb"])
    st.markdown(f"<div class='panel'><div class='metric-label'>30-DAY CAPACITY PROJECTION</div><div class='metric-value' style='font-size:1.35rem'>{format_tb(projected_tb)}</div><div class='metric-foot'>+{delta_tb:.1f} TB projected · {float(forecast['utilization_pct'].iloc[-1]):.1f}% utilization</div></div>", unsafe_allow_html=True)

bottom_left, bottom_right = st.columns([1.1, 1], gap="large")
with bottom_left:
    st.markdown("<div class='section-title'>Recommended actions</div>", unsafe_allow_html=True)
    actions = recommendations(latest, len(recent_anomalies), forecast)
    for item in actions:
        color = "#ff7b82" if item["priority"] == "High" else "#f4bd6a" if item["priority"] == "Medium" else "#55e6c1"
        st.markdown(f"<div class='alert-row'><span style='color:{color};font-weight:700;font-size:.72rem'>{item['priority'].upper()}</span><br><b>{item['action']}</b><br><span class='muted'>{item['detail']}</span></div>", unsafe_allow_html=True)

with bottom_right:
    st.markdown("<div class='section-title'>Recent alerts</div>", unsafe_allow_html=True)
    if recent_anomalies.empty:
        st.info("No unusual samples detected in the last 30 days.")
    else:
        alerts = recent_anomalies.sort_values("timestamp", ascending=False).head(5)
        for _, alert in alerts.iterrows():
            st.markdown(f"<div class='alert-row'><span style='color:#f4bd6a;font-weight:700;font-size:.72rem'>ANOMALY DETECTED</span><br><b>{alert['timestamp'].strftime('%b %d, %Y')}</b><br><span class='muted'>Latency {alert['latency_ms']:.1f} ms · {alert['iops']:,.0f} IOPS · Isolation Forest</span></div>", unsafe_allow_html=True)

with st.expander("Explore raw telemetry"):
    st.dataframe(history.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

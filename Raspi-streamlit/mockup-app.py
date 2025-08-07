import streamlit as st
import time
import pandas as pd
import altair as alt
import numpy as np
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="FNM Team Dashboard", layout="centered")
st_autorefresh(interval=400, key="autorefresh")

# ---- UI & Style ----
st.markdown("""
    <style>
    body { background-color: #f5fff5; }
    .title { text-align: center; color: #2E8B57; font-size: 36px; font-weight: bold; }
    .subtitle { text-align: center; color: #444; font-size: 18px; margin-top: -10px; }
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 30px;
    }
    </style>
    <div class='title'>FNM Team</div>
    <div class='subtitle'>Dashboard</div>
    <hr style="margin-top:10px;"/>
""", unsafe_allow_html=True)

# ---- Mode Selection ----
mode = st.radio("Select Project", ["Decoupled", "CDI"], horizontal=True)

# ---- Inputs ----
if mode == "Decoupled":
    col1, col2 = st.columns(2)
    with col1:
        min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 5.0, 0.0, 0.1)
    with col2:
        peak_voltage = st.number_input("Set Peak Voltage (V)", 0.0, 5.0, 2.0, 0.1)
    discharge_minutes = st.number_input("Discharge Time (minutes)", min_value=0.0, value=2.0, step=0.1)
else:
    min_voltage = 0.0
    peak_voltage = 0.0
    discharge_minutes = st.number_input("Time (minutes)", min_value=0.0, value=2.0, step=0.1)

# ---- Session State Init ----
if "voltage" not in st.session_state:
    st.session_state.voltage = 0.0
if "charging" not in st.session_state:
    st.session_state.charging = True
if "data" not in st.session_state:
    st.session_state.data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "running" not in st.session_state:
    st.session_state.running = True

# ---- Simulate Voltage ----
if st.session_state.running:
    if st.session_state.charging:
        st.session_state.voltage += np.random.uniform(0.05, 0.2)
        if st.session_state.voltage >= peak_voltage:
            st.session_state.voltage = peak_voltage
            st.session_state.charging = False
    else:
        st.session_state.voltage -= np.random.uniform(0.05, 0.2)
        if st.session_state.voltage <= min_voltage:
            st.session_state.voltage = min_voltage
            st.session_state.charging = True

    elapsed_time = int(time.time() - st.session_state.start_time)
    state = "Charging" if st.session_state.charging else "Discharging"
    st.session_state.data.append({
        "Seconds": elapsed_time,
        "Voltage": st.session_state.voltage,
        "State": state
    })

# ---- Display Status ----
if st.session_state.data:
    latest_state = st.session_state.data[-1]["State"]
    state_color = "#2E8B57" if latest_state == "Charging" else "#F44336"
    st.markdown(f"""
        <div style='display:flex;align-items:center;gap:20px;'>
            <span style='font-size: 35px; color: {state_color}; font-weight: 600;'>
                Voltage (V): {st.session_state.voltage:.3f} V
            </span>
            <span style='font-size: 28px; color: white; font-weight: 600; background-color:{state_color}; padding:4px 16px; border-radius:12px;'>
                [{latest_state}]
            </span>
        </div>
    """, unsafe_allow_html=True)

# ---- Elapsed Time ----
def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h} hr {m} min {s} sec"

elapsed = int(time.time() - st.session_state.start_time)
st.write(f"Elapsed Time: {format_time(elapsed)}")

# ---- Chart ----
df = pd.DataFrame(st.session_state.data)
if mode == "Decoupled" and not df.empty:
    df["Minutes"] = df["Seconds"] / 60
    x_axis = alt.X("Minutes", title="Time (min)") if df["Seconds"].max() > 60 else alt.X("Seconds", title="Time (s)")
    chart = alt.Chart(df).mark_line().encode(
        x=x_axis,
        y=alt.Y("Voltage", title="Voltage (V)"),
        color=alt.Color("State", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "voltage_log.csv", "text/csv")
else:
    st.info("CDI mode active — voltage chart is not shown.")

# ---- Stop ----
if st.button("Stop"):
    st.session_state.running = False

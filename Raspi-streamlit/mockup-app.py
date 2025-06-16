import streamlit as st
import time
import numpy as np
import pandas as pd
import altair as alt

# ------------- Setup Page -------------
st.set_page_config(page_title="Electrolyzer Dashboard", layout="centered")

st.markdown("""
    <style>
    body {
        background-color: #f5fff5;
    }
    .title {
        text-align: center;
        color: #2E8B57;
        font-size: 36px;
        font-weight: bold;
    }
    .subtitle {
        text-align: center;
        color: #444;
        font-size: 18px;
        margin-top: -10px;
    }
    </style>
    <div class='title'>FNM Team</div>
    <div class='subtitle'>Supercapacitive Electrolyzer Dashboard</div>
    <hr style="margin-top:10px;"/>
""", unsafe_allow_html=True)

# ------------- Inputs -------------
col1, col2 = st.columns(2)
with col1:
    min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 2.0, 1.0, 0.05)
with col2:
    peak_voltage = st.number_input("Set Peak Voltage (V)", min_voltage + 0.05, 3.0, 1.8, 0.05)

# ------------- Session State -------------
# Ensure all session state variables are initialized
if "voltage" not in st.session_state:
    st.session_state.voltage = 1.0
if "charging" not in st.session_state:
    st.session_state.charging = True
if "data" not in st.session_state:
    st.session_state.data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "running" not in st.session_state:
    st.session_state.running = True

# ------------- Charging/Discharging -------------
if st.session_state.running:
    if st.session_state.charging:
        st.session_state.voltage += np.random.uniform(0.01, 0.03)
        if st.session_state.voltage >= peak_voltage:
            st.session_state.voltage = peak_voltage
            st.session_state.charging = False
    else:
        st.session_state.voltage -= np.random.uniform(0.01, 0.03)
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

# ------------- Data Prep -------------
if len(st.session_state.data) > 100:
    st.session_state.data = st.session_state.data[-100:]

df = pd.DataFrame(st.session_state.data)
df["Minutes"] = df["Seconds"] / 60

# ------------- Display Info -------------
# st.metric("Voltage (V)", f"{st.session_state.voltage:.3f}")
if st.session_state.charging:
    color = "#2E8B57"
    icon = "🔋"
else:
    color = "#F44336"
    icon = "🔻"

st.markdown(
    f"<span style='font-size: 35px; color: {color}; font-weight: 600;'>{icon} Voltage (V): {st.session_state.voltage:.3f} V</span>",
    unsafe_allow_html=True
)

# ------------- Reset Button -------------
if st.button("🔄 Reset"):
    st.session_state.voltage = min_voltage
    st.session_state.charging = True
    st.session_state.data = []
    st.session_state.start_time = time.time()
    st.session_state.running = True
    
st.write("State:", "🔋 Charging" if st.session_state.charging else "🔻 Discharging")

if st.session_state.voltage >= peak_voltage:
    st.warning("⚠️ Voltage is at peak limit!")
elif st.session_state.voltage <= min_voltage:
    st.info("ℹ️ Voltage is at minimum limit.")

if elapsed_time < 60:
    st.write(f"⏱️ Elapsed Time: {elapsed_time} seconds")
else:
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    st.write(f"⏱️ Elapsed Time: {minutes} min {seconds} sec")
    
# ------------- Plot Chart -------------
x_axis = alt.X("Minutes", title="Time (min)") if df["Seconds"].max() > 60 else alt.X("Seconds", title="Time (s)")

chart = alt.Chart(df).mark_line().encode(
    x=x_axis,
    y=alt.Y("Voltage", title="Voltage (V)"),
    color=alt.Color("State", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
).properties(width=700, height=400)

st.altair_chart(chart, use_container_width=True)

# ------------- Export CSV -------------
csv = df.to_csv(index=False).encode()
st.download_button("📥 Download Data as CSV", csv, "voltage_log.csv", "text/csv")

# ------------- Auto Refresh -------------
time.sleep(1)
st.rerun()

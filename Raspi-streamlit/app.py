import streamlit as st
from streamlit_autorefresh import st_autorefresh
import serial
import time
import pandas as pd
import altair as alt
import re

# ----------------- Refresh every 1s -----------------
st_autorefresh(interval=1000, key="serial-monitor")

# ----------------- Serial Setup -----------------
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
        time.sleep(2)
        st.session_state.ser.reset_input_buffer()
        st.success("? Serial connected.")
    except Exception as e:
        st.session_state.ser = None
        st.error(f"? Serial connection failed: {e}")

# ----------------- UI Input -----------------
st.title("? Real-time Arduino Dashboard")

col1, col2 = st.columns(2)
with col1:
    peak = st.number_input("Peak Voltage (V)", min_value=0.0, max_value=5.0, value=2.5, step=0.1)
with col2:
    minv = st.number_input("Minimum Voltage (V)", min_value=0.0, max_value=4.9, value=1.0, step=0.1)

if st.button("Send to Arduino"):
    if st.session_state.ser:
        try:
            st.session_state.ser.write(f"Peak:{peak:.2f}\n".encode())
            time.sleep(0.1)
            st.session_state.ser.write(f"Min:{minv:.2f}\n".encode())
            st.success("? Sent to Arduino.")
        except Exception as e:
            st.error(f"? Failed to send: {e}")
    else:
        st.error("? Serial not connected.")

# ----------------- Storage -----------------
if "data" not in st.session_state:
    st.session_state.data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# ----------------- Serial Reading + Parsing -----------------
st.subheader("? Latest Arduino Output")
latest_display = st.empty()

if st.session_state.ser:
    try:
        line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            latest_display.text(line)

            match = re.search(r"VOLTAGE:\s*([0-9.]+)\s*\|\s*DIR:\s*(\w+)\s*\|\s*MODE:\s*(\w+)", line)
            if match:
                voltage = float(match.group(1))
                direction = match.group(2)
                mode = match.group(3)

                elapsed_time = round(time.time() - st.session_state.start_time, 2)
                st.session_state.data.append({
                    "Time (s)": elapsed_time,
                    "Voltage": voltage,
                    "Direction": direction,
                    "Mode": mode
                })

                st.markdown(f"""
                **? Voltage**: `{voltage:.4f} V`  
                **?? Direction**: `{direction}`  
                **?? Mode**: `{mode}`  
                **? Elapsed**: `{elapsed_time:.2f} s`
                """)
    except Exception as e:
        st.error(f"? Error reading serial: {e}")

# ----------------- DataFrame and Chart -----------------
df = pd.DataFrame(st.session_state.data)
if not df.empty:
    st.subheader("? Voltage Chart")

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X("Time (s)", title="Elapsed Time (s)"),
        y=alt.Y("Voltage", title="Voltage (V)"),
        color=alt.Color("Mode", scale=alt.Scale(domain=["Charging", "Discharging"], range=["green", "red"]))
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

    # ----------------- Download -----------------
    csv = df.to_csv(index=False).encode()
    st.download_button("?? Download CSV", csv, "arduino_voltage_log.csv", "text/csv")

# ----------------- Reset -----------------
if st.button("Reset Data"):
    st.session_state.data = []
    st.session_state.start_time = time.time()
    st.experimental_rerun()

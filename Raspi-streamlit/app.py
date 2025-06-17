import streamlit as st
import time
import pandas as pd
import altair as alt
import serial
import re
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Electrolyzer Dashboard", layout="centered")
st_autorefresh(interval=400, key="autorefresh")


# ---- UI & Style ----
st.markdown("""
    <style>
    body { background-color: #f5fff5; }
    .title { text-align: center; color: #2E8B57; font-size: 36px; font-weight: bold; }
    .subtitle { text-align: center; color: #444; font-size: 18px; margin-top: -10px; }
    </style>
    <div class='title'>FNM Team</div>
    <div class='subtitle'>Supercapacitive Electrolyzer Dashboard</div>
    <hr style="margin-top:10px;"/>
""", unsafe_allow_html=True)

# ---- Input ----
col1, col2 = st.columns(2)
with col1:
    min_voltage = st.number_input("Set Minimum Voltage (V)", 0.0, 2.0, 1.0, 0.1)
with col2:
    peak_voltage = st.number_input("Set Peak Voltage (V)", 0.0, 3.0, 1.8, 0.1)

# ---- Serial ----
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
        time.sleep(2)
        st.session_state.ser.reset_input_buffer()
        st.success("Serial connected.")
    except Exception as e:
        st.session_state.ser = None
        st.error(f"Serial connection failed: {e}")

# ---- Send to Arduino ----
# if st.button("Send to Arduino"):
#     if st.session_state.ser:
#         try:
#             st.session_state.ser.write(f"Peak:{peak_voltage:.2f}\n".encode())
#             time.sleep(0.05)
#             st.session_state.ser.write(f"Min:{min_voltage:.2f}\n".encode())
#             st.success("Sent to Arduino.")
#             st.session_state.running = True
#             st.session_state.start_time = time.time()
#         except Exception as e:
#             st.error(f"Failed to send: {e}")
# ---- Send to Arduino ----
if st.button("Send to Arduino"):
    if not st.session_state.ser:
        try:
            st.session_state.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
            time.sleep(2)
            st.session_state.ser.reset_input_buffer()
            st.success("Serial connected.")
        except Exception as e:
            st.session_state.ser = None
            st.error(f"Serial connection failed: {e}")

    if st.session_state.ser:
        try:
            st.session_state.voltage = min_voltage
            st.session_state.charging = True
            st.session_state.data = []
            st.session_state.start_time = time.time()
            st.session_state.running = True
            # -------------------------------------
            st.session_state.ser.write(f"Peak:{peak_voltage:.2f}\n".encode())
            time.sleep(0.05)
            st.session_state.ser.write(f"Min:{min_voltage:.2f}\n".encode())
            st.success("Sent to Arduino and RESET all states.")
        except Exception as e:
            st.error(f"Failed to send: {e}")

# ---- Init State ----
if "voltage" not in st.session_state:
    st.session_state.voltage = 1.0
if "charging" not in st.session_state:
    st.session_state.charging = True
if "data" not in st.session_state:
    st.session_state.data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "running" not in st.session_state:
    st.session_state.running = False

# ---- Real-time Serial Read ----
if st.session_state.running and st.session_state.ser:
    try:
        while st.session_state.ser.in_waiting > 0:
            line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                match = re.search(r"VOLTAGE:\s*([0-9.]+)\s*\|\s*DIR:\s*(\w+)\s*\|\s*MODE:\s*(\w+)", line)
                if match:
                    voltage = float(match.group(1))
                    mode = match.group(3)
                    st.session_state.voltage = voltage
                    st.session_state.charging = (mode == "Charging")
                    elapsed = int(time.time() - st.session_state.start_time)
                    st.session_state.data.append({
                        "Seconds": elapsed,
                        "Voltage": voltage,
                        "State": mode
                    })
    except Exception as e:
        st.error(f"Error reading serial: {e}")

# ---- Display Voltage ----
# color = "#2E8B57" if st.session_state.charging else "#F44336"
# st.markdown(
#     f"<span style='font-size: 35px; color: {color}; font-weight: 600;'> Voltage (V): {st.session_state.voltage:.3f} V</span>",
#     unsafe_allow_html=True
# )
# ---- Display Voltage + State ----
if st.session_state.data:
    color = "#2E8B57" if st.session_state.charging else "#F44336"
    state_text = "Charging" if st.session_state.charging else "Discharging"
    state_color = "#0099FF" if st.session_state.charging else "#F44336"

    st.markdown(
        f"""
        <div style='display:flex;align-items:center;gap:20px;'>
            <span style='font-size: 35px; color: {color}; font-weight: 600;'>
                Voltage (V): {st.session_state.voltage:.3f} V
            </span>
            <span style='font-size: 28px; color: {state_color}; font-weight: 600;'>
                [{state_text}]
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<span style='font-size: 20px; color: #888;'>Waiting for Arduino data...</span>",
        unsafe_allow_html=True
    )
# color = "#2E8B57" if st.session_state.charging else "#F44336"
# state_text = "Charging" if st.session_state.charging else "Discharging"
# state_color = "#0099FF" if st.session_state.charging else "#F44336"

# st.markdown(
#     f"""
#     <div style='display:flex;align-items:center;gap:20px;'>
#         <span style='font-size: 35px; color: {color}; font-weight: 600;'>
#             Voltage (V): {st.session_state.voltage:.3f} V
#         </span>
#         <span style='font-size: 28px; color: {state_color}; font-weight: 600;'>
#             [{state_text}]
#         </span>
#     </div>
#     """,
#     unsafe_allow_html=True
# )


# ---- Control Buttons ----
# colA, colB = st.columns(2)
# with colA:
#     if st.button("Stop"):
#         st.session_state.running = False
# with colB:
#     if st.button("Reset"):
#         st.session_state.voltage = min_voltage
#         st.session_state.charging = True
#         st.session_state.data = []
#         st.session_state.start_time = time.time()
#         st.session_state.running = False
# ---- Control Button ----
if st.button("Stop"):
    if st.session_state.ser:
        try:
            st.session_state.ser.write(b"STOP\n")
            st.session_state.ser.close()
            st.session_state.ser = None
            st.success("Serial connection closed.")
        except Exception as e:
            st.error(f"Error while closing serial: {e}")
    st.session_state.running = False

# ---- Elapsed Time ----
if st.session_state.running:
    elapsed_time = int(time.time() - st.session_state.start_time)
else:
    elapsed_time = st.session_state.data[-1]["Seconds"] if st.session_state.data else 0
if elapsed_time < 60:
    st.write(f"Elapsed Time: {elapsed_time} seconds")
else:
    st.write(f"Elapsed Time: {elapsed_time // 60} min {elapsed_time % 60} sec")

# ---- Chart ----
df = pd.DataFrame(st.session_state.data)
if not df.empty:
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

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import serial
import time

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

# ----------------- UI Inputs -----------------
st.title("? Real-time Arduino Monitor")

peak = st.number_input("Peak Voltage (V)", min_value=0.0, max_value=5.0, value=2.5, step=0.1)
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

# ----------------- Read Serial Output -----------------
st.subheader("? Arduino Output")
output_area = st.empty()

if st.session_state.ser:
    try:
        lines = []
        start = time.time()
        while time.time() - start < 0.5:
            if st.session_state.ser.in_waiting > 0:
                line = st.session_state.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    lines.append(line)
        if lines:
            output_area.text("\n".join(lines))
        else:
            output_area.info("No data received from Arduino.")
    except Exception as e:
        output_area.error(f"? Error reading serial: {e}")

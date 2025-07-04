import serial
import time

ser = serial.Serial('/dev/ttyACM1', 115200, timeout=1.0)
time.sleep(3)
ser.reset_input_buffer()
print("Serial connection success")

try:
    while True:
        try:
            peak_voltage = float(input("Enter Peak Voltage : "))
            min_voltage = float(input(f"Enter Minimum Voltage : "))
            time_data = int(input(f"Enter Time : "))
            if not (0.0 < peak_voltage <= 3.3):
                continue
            if not (0.0 <= min_voltage < peak_voltage):
                continue
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        pk_msg = f"Peak:{peak_voltage:.2f}\n"
        mn_msg = f"Min:{min_voltage:.2f}\n"
        time_msg = f"Time:{time_data}\n"
        print(f"Sending: {pk_msg.strip()} and {mn_msg.strip()}")
        ser.write(pk_msg.encode('utf-8'))
        time.sleep(0.2)
        ser.write(mn_msg.encode('utf-8'))
        time.sleep(0.2)
        ser.write(time_msg.encode('utf-8'))
        print("Listening to simulation output from Arduino (press Ctrl+C to stop)...")
        print("-" * 40)

        try:
            while True:
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').rstrip()
                    if response:
                        print(response)
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopped. Returning to main loop.\n")

        print("-" * 40)

except KeyboardInterrupt:
    print("Closing serial connection.")
    ser.close()

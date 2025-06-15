import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
time.sleep(3)
ser.reset_input_buffer()
print("Serial connection success")

try:
    while True:
        try:
            peak_voltage = float(input("Enter Peak Voltage : "))
            min_voltage = float(input(f"Enter Minimum Voltage : "))

            if not (0.0 < peak_voltage <= 3.3):
                continue
            if not (0.0 <= min_voltage < peak_voltage):
                continue
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        pk_msg = f"Peak:{peak_voltage:.2f}\n"
        mn_msg = f"Min:{min_voltage:.2f}\n"
        print(f"Sending: {pk_msg.strip()} and {mn_msg.strip()}")
        ser.write(pk_msg.encode('utf-8'))
        time.sleep(0.2)
        ser.write(mn_msg.encode('utf-8'))

        print("Waiting for Arduino response...")
        start_time = time.time()
        while ser.in_waiting <= 0:
            if time.time() - start_time > 2:
                print("No response from Arduino.")
                break
            time.sleep(0.01)

        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').rstrip()
            print(f"{response}")

        print("-" * 40)

except KeyboardInterrupt:
    print("Closing serial connection.")
    ser.close()

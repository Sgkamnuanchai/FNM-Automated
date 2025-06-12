float peakVoltage = 1.8;   // Default peak voltage
float minVoltage = 1.0;    // Default minimum voltage
float voltage = 1.0;       // Start at min
bool charging = true;

void setup() {
  Serial.begin(115200);
}

void loop() {
  // --- Receive commands from Streamlit ---
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Clean newline or carriage return

    if (input.startsWith("PK:")) {
      float val = input.substring(3).toFloat();
      if (val > 0.0 && val <= 3.3) {
        peakVoltage = val;
      }
    }

    if (input.startsWith("MN:")) {
      float val = input.substring(3).toFloat();
      if (val >= 0.0 && val < peakVoltage) {
        minVoltage = val;
      }
    }
  }

  // --- Simulate voltage based on state ---
  if (charging) {
    voltage += 0.03;
    if (voltage >= peakVoltage) {
      voltage = peakVoltage;
      charging = false;
    }
  } else {
    voltage -= 0.03;
    if (voltage <= minVoltage) {
      voltage = minVoltage;
      charging = true;
    }
  }

  // --- Send current voltage to Streamlit ---
  Serial.print("V:");
  Serial.println(voltage, 3);  // 3 decimal places

  delay(1000);
}

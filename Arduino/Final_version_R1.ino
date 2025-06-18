int relay1 = 7;
int relay2 = 6;
int relay3 = 5;
int relay4 = 4;

const int voltagePin = A4;

float peak_value = 0.0;
float bottom_value = 0.0;

bool simulationRunning = false;
bool isDischarging = false;
bool peakReceived = false;
bool minReceived = false;

String lastModePrinted = "";
String lastDirectionPrinted = "";
float lastVoltage = 0.0;

unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 300000;
bool checkRequested = false;

void setup() {
  Serial.begin(115200);
  pinMode(relay1, OUTPUT);
  pinMode(relay2, OUTPUT);
  pinMode(relay3, OUTPUT);
  pinMode(relay4, OUTPUT);
  pinMode(voltagePin, INPUT);
  stopAllRelays();
}

void loop() {
  handlePiMessage();
  if (!simulationRunning || !(peakReceived && minReceived)) return;

  float currentVoltage = readVoltage();
  displayVoltageStatus(currentVoltage);

  if (!isDischarging && currentVoltage >= peak_value) {
    startDischarging();
    Serial.println("Voltage exceeded peak_value. Switching to DISCHARGING and waiting 300s...");
    isDischarging = true;
    delay(300000);
  }

  if (isDischarging && millis() - lastCheckTime >= checkInterval) {
    checkRequested = true;
    lastCheckTime = millis();
  }

  if (isDischarging && checkRequested) {
    bool shouldSwitchToCharging = false;

    while (!shouldSwitchToCharging) {
      Serial.println("Temporarily switching to CHARGING to check voltage...");
      startCharging();
      //delay(5000);

      Serial.println("Reading 5 voltage samples (2 second apart)...");
      shouldSwitchToCharging = checkVoltageAnyBelowThreshold(5, bottom_value);

      if (shouldSwitchToCharging) {
        Serial.println("Switching to CHARGING mode.");
        isDischarging = false;
      } else {
        Serial.println("All readings above bottom_value. Waiting  4 seconds before rechecking... + 2 s * 5 part = ");
        startDischarging();
        delay(300000);
      }
    }

    checkRequested = false;
  }

  String currentMode = isDischarging ? "Discharging" : "Charging";
  if (currentMode != lastModePrinted) {
    lastModePrinted = currentMode;
  }

  delay(2000);
}

//////////// === VOLTAGE READING FROM A3 === ////////////
float readVoltage() {
  int analogValue = analogRead(voltagePin);
  return analogValue * (5.0 / 1023.0);  // Convert to voltage (assuming 5V reference)
}

//////////// === DISPLAY VOLTAGE AND DIRECTION === ////////////
void displayVoltageStatus(float voltage) {
  String direction = "";
  if (voltage > lastVoltage) direction = "INCREASING";
  else if (voltage < lastVoltage) direction = "DECREASING";
  else direction = lastDirectionPrinted;

  lastVoltage = voltage;
  lastDirectionPrinted = direction;

  String mode = isDischarging ? "Discharging" : "Charging";
  Serial.print("Live Input | VOLTAGE: ");
  Serial.print(voltage, 4);
  Serial.print(" | DIR: ");
  Serial.print(direction);
  Serial.print(" | MODE: ");
  Serial.println(mode);
}

//////////// === CHECK VOLTAGE 5 TIMES === ////////////
bool checkVoltageAnyBelowThreshold(int samples, float threshold) {
  for (int i = 0; i < samples; i++) {
    delay(2000);
    float currentValue = readVoltage();
    displayVoltageStatus(currentValue);

    if (currentValue <= threshold) {
      Serial.println("Reading is below or equal to bottom_value. Switching to CHARGING mode immediately.");
      isDischarging = false;
      return true;
    }
  }
  return false;
}

//////////// === RELAY CONTROL === ////////////
void startCharging() {
  digitalWrite(relay1, LOW);
  digitalWrite(relay2, LOW);
}

void startDischarging() {
  digitalWrite(relay1, HIGH);
  digitalWrite(relay2, HIGH);
}

void stopAllRelays() {
  digitalWrite(relay1, LOW);
  digitalWrite(relay2, LOW);
}

//////////// === RECEIVE MESSAGE FROM PI === ////////////
void handlePiMessage() {
  if (Serial.available()) {
    String message = Serial.readStringUntil('\n');
    message.trim();

    if (message.startsWith("Peak:")) {
      float val = message.substring(5).toFloat();
      if (val > 0.0 && val <= 5.0) {
        peak_value = val;
        peakReceived = true;
      }
    } else if (message.startsWith("Min:")) {
      float val = message.substring(4).toFloat();
      if (val >= 0.0 && peakReceived && val < peak_value) {
        bottom_value = val;
        minReceived = true;

        isDischarging = false;
        simulationRunning = true;
        lastDirectionPrinted = "";
        lastVoltage = readVoltage();
        startCharging();

        Serial.println("Updated Peak/Min received. Starting simulation...");
        displayVoltageStatus(lastVoltage);
      }
    } else if (message.equalsIgnoreCase("STOP")) {
      simulationRunning = false;
      stopAllRelays();
      Serial.println("Simulation stopped.");
    } else if (message.equalsIgnoreCase("START")) {
      if (peakReceived && minReceived) {
        simulationRunning = true;
        isDischarging = false;
        lastDirectionPrinted = "";
        lastVoltage = readVoltage();
        startCharging();
        Serial.println("Simulation resumed.");
      } else {
        Serial.println("Cannot start: Peak and Min not set.");
      }
    }
  }
}

//08-07-2025 เปลี่ยน ระยะเวลา flashing time จาก 1 นาที เป็น 2.00 นาที

int relay1 = 7;
int relay2 = 6;

const int voltagePin = A0;

float peak_value = 0.0;
float bottom_value = 0.0;

bool simulationRunning = false;
bool isDischarging = false;
bool peakReceived = false;
bool minReceived = false;

bool isLoopPhase = false;
bool subChargingStarted = false;
unsigned long subChargingStartTime = 0;
bool waitingToRestartDischarging = false;
unsigned long lastLoopPrint = 0;
bool secondLoopPending = false;

bool rechargingBeforeLoop = false;
bool reDischargingAfterRecharge = false;

String lastDirectionPrinted = "";
float lastVoltage = 0.0;

unsigned long customDelayTime = 120000;
unsigned long dischargeBelowThresholdStart = 0; // เพิ่มตัวแปรนี้

void setup() {
  Serial.begin(115200);
  pinMode(relay1, OUTPUT);
  pinMode(relay2, OUTPUT);
  pinMode(voltagePin, INPUT);
  stopAllRelays();
}

void loop() {
  handlePiMessage();
  if (!simulationRunning || !(peakReceived && minReceived)) return;

  float currentVoltage = readVoltage();

  // Step 2: Detect peak → start discharging
  if (!isDischarging && currentVoltage >= peak_value && !isLoopPhase && !rechargingBeforeLoop && !reDischargingAfterRecharge) {
    startDischarging();
    isDischarging = true;
    Serial.println("Voltage exceeded peak_value. Switching to DISCHARGING and monitoring...");
  }

  // Modified Step: Confirm discharging until voltage ≤ 0.05V for 2 seconds before recharging
  if (isDischarging && !isLoopPhase && !rechargingBeforeLoop && !reDischargingAfterRecharge) {
    if (currentVoltage <= 0.05) {
      if (dischargeBelowThresholdStart == 0) {
        dischargeBelowThresholdStart = millis();
      } else if (millis() - dischargeBelowThresholdStart >= 2000) {
        Serial.println("Voltage <= 0.05V confirmed for 2s. Starting RECHARGING before entering Step 3...");
        isDischarging = false;
        startCharging();
        rechargingBeforeLoop = true;
        dischargeBelowThresholdStart = 0;
      }
    } else {
      dischargeBelowThresholdStart = 0;
    }
  }

  // Handle rechargingBeforeLoop
  if (rechargingBeforeLoop && !isDischarging && !isLoopPhase) {
    if (millis() - lastLoopPrint >= 1000) {
      displayVoltageStatus(currentVoltage);
      lastLoopPrint = millis();
    }
    if (currentVoltage >= peak_value) {
      Serial.println("Voltage exceeded peak again. Starting DISCHARGING before Step 3...");
      startDischarging();
      isDischarging = true;
      reDischargingAfterRecharge = true;
      rechargingBeforeLoop = false;
    }
  }

  // Monitor re-discharge after recharge → enter Step 3 when voltage ≤ 0.05V
  if (reDischargingAfterRecharge && isDischarging && currentVoltage <= 0.05) {
    Serial.println("Voltage reached 0V after re-discharge. Entering LOOP CHARGING phase (Step 3)...");
    isDischarging = false;
    isLoopPhase = true;
    subChargingStarted = true;
    reDischargingAfterRecharge = false;
    startCharging();
    subChargingStartTime = millis();
  }

  // Step 3: Loop Charging (120s)
  if (isLoopPhase && subChargingStarted && millis() - subChargingStartTime < 120000) 
  {
    if (millis() - lastLoopPrint >= 1000) 
    {
      printStoppedStatus();
      lastLoopPrint = millis();
    }
    if (!isDischarging && currentVoltage > 0.1) 
    {
      startDischarging();
      isDischarging = true;
    } else if (isDischarging && currentVoltage <= 0.05) 
    {
      startCharging();
      isDischarging = false;
    }
  }

  // Step 4: After 120s loop → start real discharging (customDelayTime)
  if (isLoopPhase && subChargingStarted && millis() - subChargingStartTime >= 120000 && !waitingToRestartDischarging && !secondLoopPending) {
    Serial.println("60 seconds passed. Restarting DISCHARGING with custom duration...");
    startDischarging();
    isDischarging = true;
    waitingToRestartDischarging = true;

    unsigned long holdStart = millis();
    while (millis() - holdStart < customDelayTime) 
    {
      printDischargingAsZero();
      delay(1000);
    }

    Serial.println("Finished Discharging loop. Entering LOOP CHARGING phase again...");
    isDischarging = false;
    isLoopPhase = true;
    subChargingStarted = false;
    waitingToRestartDischarging = false;
    secondLoopPending = true;
    startCharging();
  }

  // Step 5: Second loop charging (start when voltage > 0.1V)
  if (secondLoopPending && !subChargingStarted) {
    if (millis() - lastLoopPrint >= 1000) {
      printChargingAsZero();
      lastLoopPrint = millis();
    }

    if (currentVoltage > 0.1) {
      Serial.println("Voltage > 0.1V detected. Starting 60 second loop now...");
      subChargingStartTime = millis();
      subChargingStarted = true;
      lastLoopPrint = millis();
    }
  }

  // Step 6: After second 120s loop, charging/discharging control
  if (secondLoopPending && subChargingStarted && millis() - subChargingStartTime < 120000) {
    if (millis() - lastLoopPrint >= 1000) {
      printStoppedStatus();
      lastLoopPrint = millis();
    }
    if (!isDischarging && currentVoltage > 0.1) {
      startDischarging();
      isDischarging = true;
    } else if (isDischarging && currentVoltage <= 0.05) {
      startCharging();
      isDischarging = false;
    }
  }

  // Step 6 (exit): Resume normal charging logic
  if (secondLoopPending && subChargingStarted && millis() - subChargingStartTime >= 120000) {
    Serial.println("Second 60 second loop complete. Resuming normal charging...");
    isLoopPhase = false;
    subChargingStarted = false;
    secondLoopPending = false;
    isDischarging = false;
    startCharging();
  }

  // Step 7: Normal voltage display
  if (currentVoltage > 0.05 && !isLoopPhase && !secondLoopPending && !rechargingBeforeLoop && !reDischargingAfterRecharge) {
    displayVoltageStatus(currentVoltage);
  }

  delay(1000);
}

// === Utility functions ===

float readVoltage() {
  int analogValue = analogRead(voltagePin);
  return analogValue * (5.0 / 1023.0);
}

void displayVoltageStatus(float voltage) {
  if (voltage <= 0.05) return;
  String direction = (voltage > lastVoltage) ? "INCREASING" : (voltage < lastVoltage ? "DECREASING" : lastDirectionPrinted);
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

void printStoppedStatus() {
  Serial.println("Live Input | VOLTAGE: 0.0000 | DIR: STABLE | MODE: Stop");
}

void printDischargingAsZero() {
  Serial.println("Live Input | VOLTAGE: 0.0000 | DIR: STABLE | MODE: Discharging");
}

void printChargingAsZero() {
  Serial.println("Live Input | VOLTAGE: 0.0000 | DIR: STABLE | MODE: Charging");
}

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
    } else if (message.startsWith("Time:")) {
      unsigned long val = message.substring(5).toInt();
      if (val > 0) {
        customDelayTime = val;
        Serial.print("Updated custom delay time to: ");
        Serial.print(customDelayTime);
        Serial.println(" ms");
      } else {
        Serial.println("Invalid time value. Must be greater than 0.");
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

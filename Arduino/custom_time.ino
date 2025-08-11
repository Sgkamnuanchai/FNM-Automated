////--Setting time for charging mode and discharging mode by receiving the commands like "c_time:" and "dc_time:" from Pi--////
////--Sending HIGH means controlling the relay to connect with NO--////
////--Sending LOW means controlling the relay to connect with NC--////
  
int relayPin1 = 7;  // setting relay1 pin of Arduino
int relayPin2 = 6;  // setting relay2 pin of Arduino
int relayPin3 = 5;  // setting relay3 pin of Arduino
int relayPin4 = 4;  // setting relay4 pin of Arduino

// Separate timers (ms)
unsigned long chargeDelayTime    = 300000;  // default 300s
unsigned long dischargeDelayTime = 300000;  // default 300s

void setup() {
  Serial.begin(115200);
  pinMode(relayPin1, OUTPUT);
  pinMode(relayPin2, OUTPUT);
  pinMode(relayPin3, OUTPUT);
  pinMode(relayPin4, OUTPUT);
}

void loop() 
{
  handlePiMessage(); 
  
//-----Sending LOW to Arduino-----//

  digitalWrite(relayPin1, LOW);   //Power flows through NC of relay1 and supplies to the cells
  digitalWrite(relayPin2, LOW);   //Power flows through NC of relay2 and there is no flowing power to Charging cell 
  unsigned long chargeStart = millis();
  while ((millis() - chargeStart) < chargeDelayTime) 
  {
    handlePiMessage();            
    Charging();
    delay(1000);
  }

  

//----- Sending HIGH to Arduino-----//

  digitalWrite(relayPin1, HIGH); //Connecting NO of relay1 with COM for stopping power flow from power supply
  digitalWrite(relayPin2, HIGH); //Connecting NO of relay2 with COM for supplying power to Charging cell
  unsigned long dischargeStart = millis();
  while ((millis() - dischargeStart) < dischargeDelayTime) 
  {
    handlePiMessage();            
    Discharging();
    delay(1000);
  }

}

/////////////////////////////////////////////////////////////////////////////////////////////////////
// Receive commands from Pi:
//   c_time:<ms>     -> set charging duration (ms)
//   dc_time:<ms>    -> set discharging duration (ms)
/////////////////////////////////////////////////////////////////////////////////////////////////////

void handlePiMessage() 
{
  if (!Serial.available()) return;

  String message = Serial.readStringUntil('\n');
  message.trim();
  String lower = message;
  lower.toLowerCase();

  if (lower.startsWith("c_time:")) 
  {
    unsigned long val = message.substring(7).toInt();
    if (val > 0) 
    {
      chargeDelayTime = val;
      Serial.print("Updated CHARGING time to: ");
      Serial.print(chargeDelayTime);
      Serial.println(" ms");
    } 
    else {}
  } 
  else if (lower.startsWith("dc_time:")) 
  {
    unsigned long val = message.substring(8).toInt();
    if (val > 0) 
    {
      dischargeDelayTime = val;
      Serial.print("Updated DISCHARGING time to: ");
      Serial.print(dischargeDelayTime);
      Serial.println(" ms");
    } else {}
  }
}

////////////////////////////////////////////////////////////
//--This function is the function to discharge the cells--//
////////////////////////////////////////////////////////////

void Discharging() 
{
  Serial.println("Live Input | VOLTAGE: 0.0000 | DIR: STABLE | MODE: Discharging");
}

/////////////////////////////////////////////////////////
//--This function is the function to charge the cells--//
/////////////////////////////////////////////////////////

void Charging() 
{
  Serial.println("Live Input | VOLTAGE: 0.0000 | DIR: STABLE | MODE: Charging");
}

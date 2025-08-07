////--Sending HIGH means controlling the relay to connect with NO--////
////--Sending LOW means controlling the relay to connect with NC--////
  
int relayPin1 = 7;  // setting relay1 pin of Arduino
int relayPin2 = 6;  // setting relay2 pin of Arduino
int relayPin3 = 5;  // setting relay3 pin of Arduino
int relayPin4 = 4;  // setting relay4 pin of Arduino

unsigned long customDelayTime = 120000;  // Default 120 seconds

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
  while (millis() - chargeStart < customDelayTime) 
  {
    Charging();
    delay(1000);
  }

//----- Sending HIGH to Arduino-----//

  digitalWrite(relayPin1, HIGH); //Connecting NO of relay1 with COM for stopping power flow from power supply
  digitalWrite(relayPin2, HIGH); //Connecting NO of relay2 with COM for supplying power to Charging cell
  unsigned long dischargeStart = millis();
  while (millis() - dischargeStart < customDelayTime) 
  {
    Discharging();
    delay(1000);
  }

}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//--This function is the function to receive the command from Pi for setting the time of charging and discharging--//
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void handlePiMessage() 

{
  if (Serial.available()) 
  {
    String message = Serial.readStringUntil('\n');
    message.trim();

    if (message.startsWith("Time:")) 
    {
      unsigned long val = message.substring(5).toInt();
      if (val > 0) 
      {
        customDelayTime = val;
        Serial.print("Updated custom delay time to: ");
        Serial.print(customDelayTime);
        Serial.println(" ms");
      } 
      else 
      {
        Serial.println("Invalid time value. Must be greater than 0.");
      }
    } 
    else {}
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

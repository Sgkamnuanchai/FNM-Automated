////--For recording the data--////
////--Sending HIGH means controlling the relay by connecting COM port with NO Port --////
////--Sending LOW means controlling the relay by connecting COM port with NC Port --////
  
int relayPin1 = 7;  // setting relay1 pin of Arduino
int relayPin2 = 6;  // setting relay2 pin of Arduino


unsigned long customDelayTime = 300000;  // Default 300 seconds or 5 minutes

void setup() 
{
  Serial.begin(115200);
  pinMode(relayPin1, OUTPUT);
  pinMode(relayPin2, OUTPUT);
}

void loop() 
{
  handlePiMessage(); 
  
//-----Sending LOW to Arduino-----//

  digitalWrite(relayPin1, LOW);   //Power flows from power supply to COM, NC of relay1 and supplies to the cells
  digitalWrite(relayPin2, LOW);   //Power flows from charging cell to COM and NC of relay2 which means there is no flowing power to Charging cell/Capacitors 
  //digitalWrite(relayPin3, LOW);   //Power flows from Capacitors to COM,NC of relay3 and go through resistor for discharging the charges
  unsigned long chargeStart = millis();
  while (millis() - chargeStart < customDelayTime) 
  {
    handlePiMessage(); 
    Charging();
    delay(1000);
  }

//----- Sending HIGH to Arduino-----//

  digitalWrite(relayPin1, HIGH);    //Connecting NO of relay1 with COM for stopping power flow from power supply
  digitalWrite(relayPin2, HIGH);    //Connecting NO of relay2 with COM for supplying power to Charging cell
  //digitalWrite(relayPin3, HIGH);    //Connecting NO of relay3 with COM for disconnecting Capacitors and resistors
  unsigned long dischargeStart = millis();
  while (millis() - dischargeStart < customDelayTime) 
  {
    handlePiMessage(); 
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


void setup() 
{
  Serial.begin(9600);
}

int printSensorValue(int pin) 
{
  int value = analogRead(pin);
  printSensorValue(pin, value);
  return value;
}

void printSensorValueChar(const char* pin, int value)
{
   Serial.print("pin");
   Serial.print(pin);
   Serial.print("=");
   Serial.println(value);
}

void printSensorValue(int pin, int value)
{
   if ((pin <= 13) && (pin >= 0))
   {
     Serial.print("pin");
     Serial.print(pin);
     Serial.print("=");
     Serial.println(value);
     return;
   } 
   switch (pin)
   {
     case A0 : printSensorValueChar("A1", value); return;
     case A1 : printSensorValueChar("A2", value); return;
     case A2 : printSensorValueChar("A3", value); return;
     case A3 : printSensorValueChar("A4", value); return;
     case A4 : printSensorValueChar("A5", value); return;
     case A5 : printSensorValueChar("A6", value); return;
   }
   Serial.print("Error: pin");
   Serial.print(pin);
   Serial.print(" does not exist.");
}

int sensor_pins[] = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, A0, A1, A2, A3, A4, A5 };

void printAllSensorValues()
{
  int length = sizeof(sensor_pins)/sizeof(sensor_pins[0]);
  for (int i = 0; i < length; ++i)
  {
    printSensorValue(sensor_pins[i]);
  }
}

void loop() {
  printAllSensorValues();
  delay(30);
}

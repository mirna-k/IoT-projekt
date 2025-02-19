#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define BUZZER_D7_PIN 7
#define LED_D2_PIN 2

// Initialize the LCD with I2C address (common addresses: 0x27 or 0x3F)
LiquidCrystal_I2C lcd(0x27, 20, 4); // 20 columns, 4 rows

void setup() {
  pinMode(BUZZER_D7_PIN, OUTPUT);
  pinMode(LED_D2_PIN, OUTPUT);
  
  Serial.begin(115200);
  // Initialize LCD
  lcd.init();
  lcd.backlight(); // Turn on backlight
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n'); // Read incoming data
    int comma1 = data.indexOf(',');
    int comma2 = data.lastIndexOf(',');

    if (comma1 != -1 && comma2 != -1) {
      float t = data.substring(0, comma1).toFloat();
      float h = data.substring(comma1 + 1, comma2).toFloat();
      int water = data.substring(comma2 + 1).toInt();

      // Print on LCD
      if (t > 0) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("T:"); lcd.print(t); lcd.print((char) 223); lcd.print("C H:"); lcd.print(h); lcd.print("%");

        lcd.setCursor(0, 1);
        lcd.print("Water: "); lcd.print(water==0 ? "No" : "Yes");
		
        lcd.setCursor(0, 2);
        if (t < 10.0){
          lcd.print("Temp: low");
        } 
        else if (t > 40.0){
          lcd.print("Temp: high");
        } else lcd.print("Temp: good");

        lcd.setCursor(0, 3);
        if (h < 40.0) {
          lcd.print("Humidity: low");
        } 
        else if (h > 80.0){
          lcd.print("Humidity: high");
        } else lcd.print("Humidity: good");
      }
      
      // Debug
      Serial.print("Received -> T: "); Serial.print(t);
      Serial.print(" H: "); Serial.print(h);
      Serial.print(" Water: "); Serial.println(water);

      if(water==1){
        tone(BUZZER_D7_PIN, 1000); // Send 1KHz sound signal...
        digitalWrite(LED_D2_PIN, HIGH);
        delay(1000);        // ...for 1 sec
        noTone(BUZZER_D7_PIN);     // Stop sound...
        digitalWrite(LED_D2_PIN, LOW);
        delay(1000);        // ...for 1sec
      }
    }
  }
}


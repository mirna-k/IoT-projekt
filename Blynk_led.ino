/* Fill-in information from Blynk Device Info here */
#define BLYNK_TEMPLATE_ID           "TMPL4OGl_c_UZ"
#define BLYNK_TEMPLATE_NAME         "LED"
#define BLYNK_AUTH_TOKEN            "Lz8yGdpBSpu4U6Pk-kti8tg-MWxGy2QL"

/* Comment this out to disable prints and save space */
#define BLYNK_PRINT Serial

#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>

// Your WiFi credentials.
// Set password to "" for open networks.
char ssid[] = "";
char pass[] = "";

BLYNK_WRITE(V0) {
  digitalWrite(0, param.asInt());
}

void setup() {
  //Set the LED pin as an output pin
  pinMode(0, OUTPUT);
  //Initialize the Blynk library
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
}

void loop() {
  //Run the Blynk library
  Blynk.run();
}


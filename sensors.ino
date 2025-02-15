#include "Simple-Rain-Sensor-SOLDERED.h"
#include <DHT22.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define SENSOR_A0_PIN 12
#define SENSOR_D0_PIN 2

#define pinDATA SDA

const char* ssid = ""; // WiFi name
const char* password = ""; // Wifi password
const char* mqtt_server = ""; // IP Raspberry Pi

int notify = 0;

WiFiClient espClient;
PubSubClient client(espClient);

simpleRainSensor rainSensor(SENSOR_A0_PIN, SENSOR_D0_PIN);
DHT22 dht22(pinDATA); 

void setup()
{
  Serial.begin(115200);

  setup_wifi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  
  rainSensor.begin();
  rainSensor.calibrate(65.5);
}

void loop()
{
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float t = dht22.getTemperature();
  float h = dht22.getHumidity();
  int is_watered = rainSensor.isRaining() ? 1 : 0;

  // Send data as CSV (comma-separated)
  Serial.print(t);    // Send temperature
  Serial.print(",");  
  Serial.print(h);    // Send humidity
  Serial.print(",");
  // Serial.println(is_watered);
  // Serial.print(",");  
  Serial.println(notify);
  
  Serial.print("Sent -> T: "); Serial.print(t);
  Serial.print(" H: "); Serial.print(h);
  Serial.print(" is watered: "); Serial.println(is_watered);


  if (!isnan(t) && !isnan(h) && t > 0) {
    String payload = "{\"temperatura\": " + String(t) + ", \"vlaga\": " + String(h) + ", \"zalijevanje\": " + String(is_watered) + "}";
    client.publish("iot_plant/senzori/podaci", payload.c_str());
  }

  delay(1000);
}


void setup_wifi() {
  delay(10);
  // Connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}


void reconnect() {
  // Loop until reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("ESP8266Client")) {
      Serial.println("connected");
      // Subscribe
      client.subscribe("iot_plant/output");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(10000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  notify = (message == "1") ? 1 : 0;
}

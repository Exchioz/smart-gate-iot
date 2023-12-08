#include <WiFi.h>
#include <ESP32Servo.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

const char *WIFI_SSID = "Not4U";
const char *WIFI_PASS = "123PakeHuruf";

const int servoPin = 14;
const int infraredPin = 26; // Pin untuk sensor infrared
int IROutput;
Servo myservo;
AsyncWebServer server(80);

void setup() {
  Serial.begin(115200);

  myservo.attach(servoPin);
  pinMode(infraredPin, INPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.println("http://");
  Serial.println(WiFi.localIP());

  server.on("/open-gate", HTTP_GET, [](AsyncWebServerRequest *request) {
    IROutput = digitalRead(infraredPin);
    if (IROutput == LOW) {
      myservo.write(90);
      delay(1000);
      myservo.write(0);
      Serial.print("Gate Opened");
      request->send(200, "text/plain", "Gate Opened");
    } else {
      Serial.print("Not Detected");
      request->send(200, "text/plain", "Infrared not detected, unable to open gate");
    }
  });

  server.begin();
}

void loop() {
}


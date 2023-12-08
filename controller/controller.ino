#include <WiFi.h>
#include <ESP32Servo.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

const char *WIFI_SSID = "Not4U";
const char *WIFI_PASS = "123PakeHuruf";

const int servoPin = 14;
const int irPin = 26;

int servoValue;
// int irValue = digitalRead(irPin);

Servo myservo;
AsyncWebServer server(80);

void setup()
{
  Serial.begin(115200);

  myservo.attach(servoPin);
  pinMode(irPin, INPUT);

  // Setup WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
  }
  Serial.println("http://");
  Serial.println(WiFi.localIP());

  server.on("/check-infrared", HTTP_GET, [](AsyncWebServerRequest *request){
    int irValue = digitalRead(irPin);
    Serial.println(irValue);
    String irValueString = String(irValue);
    request->send(200, "text/plain", irValueString);});

  server.on("/open-gate", HTTP_GET, [](AsyncWebServerRequest *request){
    myservo.write(90);
    Serial.println("Buka Gerbang");
    request->send(200, "text/plain", "Gate Opened"); });

  server.on("/close-gate", HTTP_GET, [](AsyncWebServerRequest *request){
    myservo.write(0);
    Serial.println("Tutup Gerbang");
    request->send(200, "text/plain", "Gate Closed"); });
  server.begin();
}

void loop()
{
}
#include <WiFi.h>
#include <ESP32Servo.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

const char *WIFI_SSID = "Bams";
const char *WIFI_PASS = "aksyalbams";

const int servoPin = 14;
const int trigPin = 26;
const int echoPin = 27;

int servoValue;

Servo myservo;
AsyncWebServer server(80);

void setup()
{
  Serial.begin(115200);

  myservo.attach(servoPin);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Setup WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.println("Connecting to WiFi..");
  }
  Serial.println("Connected to WiFi network");
  Serial.println("http://");
  Serial.println(WiFi.localIP());

  server.on("/check-ultrasonic", HTTP_GET, [](AsyncWebServerRequest *request)
            {
    long duration, jarak;
  
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
  
    duration = pulseIn(echoPin, HIGH);
    jarak = (duration * 0.0343) / 2;

    int jarakInt = static_cast<int>(jarak);
    String jarakString = String(jarakInt);
    request->send(200, "text/plain", jarakString); });

  server.on("/open-gate", HTTP_POST, [](AsyncWebServerRequest *request)
            {
    myservo.write(90);
    Serial.println("Buka Gerbang");
    request->send(200, "text/plain", "Gate Opened"); });

  server.on("/close-gate", HTTP_POST, [](AsyncWebServerRequest *request)
            {
    myservo.write(0);
    Serial.println("Tutup Gerbang");
    request->send(200, "text/plain", "Gate Closed"); });
  server.begin();
}

void loop()
{
}
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "secrets.h"
#include "config.h"

const int SDA_PIN = 21, SCL_PIN = 22;
WebSocketsClient webSocket;
unsigned long lastWiFiRetry = 0;
bool wifiOK = false;

void reconnectWiFi() {
  if (WiFi.status() == WL_CONNECTED) { wifiOK = true; return; }
  WiFi.reconnect();
  unsigned long t = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t < 10000) delay(500);
  wifiOK = (WiFi.status() == WL_CONNECTED);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  wifiOK = true;
  Serial.println("WiFi OK");

  String path = String(WS_PATH) + "?type=translator";
  webSocket.beginSSL(WS_HOST, WS_PORT, path.c_str());
  webSocket.setReconnectInterval(5000);
  webSocket.onEvent([](WStype_t type, uint8_t* payload, size_t len) {
    if (type == WStype_TEXT && len > 0) {
      JsonDocument doc;
      if (!deserializeJson(doc, payload)) {
        int x = doc["pan"] | PAN_CENTER;
        int y = doc["tilt"] | TILT_CENTER;
        // ponytail: bounds inline — evita I2C inválido
        x = max(PAN_MIN, min(PAN_MAX, x));
        y = max(TILT_MIN, min(TILT_MAX, y));
        Wire.beginTransmission(SLAVE_ADDR);
        Wire.write((uint8_t)x);
        Wire.write((uint8_t)y);
        byte s = Wire.endTransmission();
        Serial.printf("I2C X:%d Y:%d %s\n", x, y, s == 0 ? "OK" : "ERR");
      }
    }
  });
  Serial.println("Translator WS listo");
}

void loop() {
  webSocket.loop();
  if (!wifiOK && millis() - lastWiFiRetry > 30000) {
    reconnectWiFi();
    lastWiFiRetry = millis();
  }
}

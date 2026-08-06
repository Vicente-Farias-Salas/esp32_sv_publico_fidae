#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "secrets.h"
#include "config.h"

const int SDA_PIN = 21;
const int SCL_PIN = 22;

WebSocketsClient webSocket;
unsigned long ultimaReconexionWiFi = 0;
bool wifiOK = false;

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) { wifiOK = true; return; }
  Serial.print("WiFi reconectando... ");
  WiFi.reconnect();
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(500); Serial.print(".");
  }
  wifiOK = (WiFi.status() == WL_CONNECTED);
  Serial.println(wifiOK ? "OK" : "FALLO");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("WS conectado. Enviando rol translator...");
      webSocket.sendTXT("{\"type\":\"translator\"}");
      break;

    case WStype_DISCONNECTED:
      Serial.println("WS desconectado (translator)");
      break;

    case WStype_TEXT: {
      JsonDocument doc;
      DeserializationError error = deserializeJson(doc, payload);

      if (!error && doc["pan"].is<int>() && doc["tilt"].is<int>()) {
        int target_x = doc["pan"];
        int target_y = doc["tilt"];

        // FIX: bounds checking antes de enviar por I2C
        if (target_x < PAN_MIN) target_x = PAN_MIN;
        if (target_x > PAN_MAX) target_x = PAN_MAX;
        if (target_y < TILT_MIN) target_y = TILT_MIN;
        if (target_y > TILT_MAX) target_y = TILT_MAX;

        Wire.beginTransmission(SLAVE_ADDR);
        Wire.write((uint8_t)target_x);
        Wire.write((uint8_t)target_y);
        byte status = Wire.endTransmission();

        if (status == 0) {
          Serial.printf("I2C -> X:%d | Y:%d (OK)\n", target_x, target_y);
        } else {
          Serial.printf("I2C error %d -> X:%d | Y:%d\n", status, target_x, target_y);
        }
      }
      break;
    }

    default:
      break;
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);
  Serial.println("Maestro ESP32 I2C Iniciado.");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  wifiOK = true;
  Serial.println("\nWiFi OK");

  // FIX: query param ?type=translator para identificacion
  String wsPath = String(WS_PATH) + "?type=translator";
  webSocket.beginSSL(WS_HOST, WS_PORT, wsPath.c_str());
  webSocket.setReconnectInterval(5000);   // FIX: auto-reconexion
  webSocket.onEvent(webSocketEvent);
  Serial.println("WebSocket iniciado (translator)");
}

void loop() {
  webSocket.loop();

  // FIX: reconectar WiFi si cae
  if (!wifiOK && millis() - ultimaReconexionWiFi > 30000) {
    conectarWiFi();
    ultimaReconexionWiFi = millis();
  }
}

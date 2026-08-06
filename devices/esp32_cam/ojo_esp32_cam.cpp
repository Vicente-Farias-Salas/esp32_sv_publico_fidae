#include "esp_camera.h"
#include <WiFi.h>
#include <WebSocketsClient.h>
#include "secrets.h"
#include "config.h"

// AI-Thinker pinout
#define PWDN_GPIO_NUM    32
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27
#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

WebSocketsClient webSocket;
unsigned long tiempoUltimoFrame = 0;
unsigned long ultimaReconexion = 0;
bool wifiOK = false;

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    wifiOK = true;
    return;
  }
  Serial.print("WiFi desconectado. Reconectando... ");
  WiFi.reconnect();
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    wifiOK = true;
    Serial.println(" OK");
  } else {
    wifiOK = false;
    Serial.println(" FALLO");
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("Iniciando hardware de camara...");

  // --- Cámara ---
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM; config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM; config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM; config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;  // FIX: 2 buffers para evitar dropped frames

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Falla critica al iniciar la camara. Error: 0x%x\n", err);
    delay(5000);
    ESP.restart();
  }
  Serial.println("Camara inicializada");

  // --- WiFi ---
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  wifiOK = true;
  Serial.println("\nWiFi OK");

  // --- WebSocket (SSL, Vercel has valid Let's Encrypt certs) ---
  String wsPath = String(WS_PATH) + "?type=camera";
  webSocket.beginSSL(WS_HOST, WS_PORT, wsPath.c_str());
  webSocket.setReconnectInterval(5000);  // FIX: auto-reconexion cada 5s
  webSocket.onEvent(webSocketEvent);

  Serial.print("Conectando a wss://");
  Serial.print(WS_HOST);
  Serial.print(WS_PATH);
  Serial.print("?type=camera\n");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("WS conectado (camera)");
      webSocket.sendTXT("{}");
      break;
    case WStype_DISCONNECTED:
      Serial.println("WS desconectado (camera)");
      break;
    case WStype_ERROR:
      Serial.printf("WS error\n");
      break;
    default:
      break;
  }
}

void loop() {
  webSocket.loop();

  // CHECK: WiFi periodicamente
  if (!wifiOK && millis() - ultimaReconexion > 30000) {
    conectarWiFi();
    ultimaReconexion = millis();
  }

  // Enviar frame cada 100ms (10 FPS)
  if (webSocket.isConnected() && millis() - tiempoUltimoFrame > 100) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (fb) {
      webSocket.sendBIN(fb->buf, fb->len);
      esp_camera_fb_return(fb);
      tiempoUltimoFrame = millis();
    }
  }
}

#include "esp_camera.h"
#include <WiFi.h>
#include <WebSocketsClient.h>
#include "secrets.h"
#include "config.h"

// AI-Thinker pinout
#define PWDN_GPIO_NUM   32
#define RESET_GPIO_NUM  -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM   26
#define SIOC_GPIO_NUM   27
#define Y9_GPIO_NUM     35
#define Y8_GPIO_NUM     34
#define Y7_GPIO_NUM     39
#define Y6_GPIO_NUM     36
#define Y5_GPIO_NUM     21
#define Y4_GPIO_NUM     19
#define Y3_GPIO_NUM     18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM  25
#define HREF_GPIO_NUM   23
#define PCLK_GPIO_NUM   22

WebSocketsClient webSocket;
unsigned long lastFrame = 0, lastWiFiRetry = 0;
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
  delay(1000);

  camera_config_t cfg{};
  cfg.ledc_channel = LEDC_CHANNEL_0;
  cfg.ledc_timer = LEDC_TIMER_0;
  cfg.pin_d0 = Y2_GPIO_NUM; cfg.pin_d1 = Y3_GPIO_NUM;
  cfg.pin_d2 = Y4_GPIO_NUM; cfg.pin_d3 = Y5_GPIO_NUM;
  cfg.pin_d4 = Y6_GPIO_NUM; cfg.pin_d5 = Y7_GPIO_NUM;
  cfg.pin_d6 = Y8_GPIO_NUM; cfg.pin_d7 = Y9_GPIO_NUM;
  cfg.pin_xclk = XCLK_GPIO_NUM;  cfg.pin_pclk = PCLK_GPIO_NUM;
  cfg.pin_vsync = VSYNC_GPIO_NUM; cfg.pin_href = HREF_GPIO_NUM;
  cfg.pin_sscb_sda = SIOD_GPIO_NUM; cfg.pin_sscb_scl = SIOC_GPIO_NUM;
  cfg.pin_pwdn = PWDN_GPIO_NUM;   cfg.pin_reset = RESET_GPIO_NUM;
  cfg.xclk_freq_hz = 10000000;
  cfg.pixel_format = PIXFORMAT_JPEG;
  cfg.frame_size = FRAMESIZE_QVGA;
  cfg.jpeg_quality = 12;
  cfg.fb_count = 2;

  if (esp_camera_init(&cfg) != ESP_OK) {
    Serial.println("Camara FAIL — reset");
    delay(5000); ESP.restart();
  }
  Serial.println("Camara OK");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  wifiOK = true;
  Serial.println("WiFi OK");

  String path = String(WS_PATH) + "?type=camera";
  webSocket.beginSSL(WS_HOST, WS_PORT, path.c_str());
  webSocket.setReconnectInterval(5000);
  webSocket.onEvent([](WStype_t t, uint8_t*, size_t) {
    if (t == WStype_DISCONNECTED) Serial.println("WS off");
  });
}

void loop() {
  webSocket.loop();
  if (!wifiOK && millis() - lastWiFiRetry > 30000) {
    reconnectWiFi();
    lastWiFiRetry = millis();
  }
  if (webSocket.isConnected() && millis() - lastFrame > 100) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (fb) {
      webSocket.sendBIN(fb->buf, fb->len);
      esp_camera_fb_return(fb);
      lastFrame = millis();
    }
  }
}

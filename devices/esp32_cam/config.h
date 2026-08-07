#ifndef FIDAE_CONFIG_H
#define FIDAE_CONFIG_H

// WebSocket Server (Vercel deployment)
#define WS_HOST  "esp32-sv-publico-fidae.vercel.app"
#define WS_PORT  443
#define WS_PATH  "/api/socket"

// I2C
#define SLAVE_ADDR 0x08

// Servo Limits (grados)
#define PAN_MIN    0
#define PAN_MAX   180
#define TILT_MIN   90
#define TILT_MAX  160

// Posición centro
#define PAN_CENTER  90
#define TILT_CENTER 120

// Movement timing (ms — non-blocking con millis())
#define STEP_DELAY_BASE  15  // ponytail: 1 delay, suficiente para 90°/seg

#endif

// config.h para modo LOCAL
// ponytail: misma interfaz que el shared/config.h pero con IP local
#ifndef FIDAE_CONFIG_H
#define FIDAE_CONFIG_H

// WebSocket Server (IP LOCAL — encuentra tu IP con: ipconfig)
#define WS_HOST  "192.168.1.100"  // ← CAMBIA ESTO por tu IP local
#define WS_PORT  8080
#define WS_PATH  "/socket"

// I2C
#define SLAVE_ADDR 0x08

// Servo Limits
#define PAN_MIN    0
#define PAN_MAX   180
#define TILT_MIN   90
#define TILT_MAX  160
#define PAN_CENTER  90
#define TILT_CENTER 120

#define STEP_DELAY_BASE  15

#endif

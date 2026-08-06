#ifndef FIDAE_CONFIG_H
#define FIDAE_CONFIG_H

// ===== WebSocket Server (Vercel deployment) =====
// Cambia PROJECT_NAME por el nombre de tu proyecto Vercel
#define WS_HOST     "fidae-rebirth.vercel.app"
#define WS_PORT     443
#define WS_PATH     "/api/socket"

// ===== I2C =====
#define SLAVE_ADDR 0x08

// ===== Servo Limits (grados) =====
#define PAN_MIN       0
#define PAN_MAX       180
#define TILT_MIN      90   // límite físico inferior del soporte
#define TILT_MAX      160  // límite físico superior del soporte

// ===== Posición inicial =====
#define PAN_CENTER    90
#define TILT_CENTER   120

// ===== Movement timing (ms por paso) =====
#define STEP_DELAY_BASE   15    // ms entre pasos cuando está lejos
#define STEP_DELAY_SLOW   30    // ms entre pasos cuando está cerca (precisión)
#define ACCEL_THRESHOLD   20    // grados: por encima de esto va rápido

#endif

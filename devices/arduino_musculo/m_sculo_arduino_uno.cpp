#include <Wire.h>
#include <Servo.h>
#include "config.h"

Servo servoX;
Servo servoY;

// Posiciones actuales e iniciales
int currentX = PAN_CENTER;
int currentY = TILT_CENTER;

// Objetivos (volátiles porque se modifican en el ISR de I2C)
// uint8_t es ATÓMICO en Arduino Uno (lectura/escritura = 1 instrucción)
// esto evita "torn reads" desde loop()
volatile uint8_t targetX = PAN_CENTER;
volatile uint8_t targetY = TILT_CENTER;

// Timing para movimiento no bloqueante
unsigned long lastMoveTime = 0;

void setup() {
  Wire.begin(SLAVE_ADDR);
  Wire.onReceive(receiveEvent);

  servoX.attach(9);
  servoY.attach(10);

  servoX.write(currentX);
  servoY.write(currentY);

  Serial.begin(9600);
  Serial.println("Arduino Musculo Iniciado (non-blocking mode)");
}

void loop() {
  unsigned long now = millis();

  // Movimiento X (Izquierda - Derecha)
  if (now - lastMoveTime >= getStepDelay(currentX, targetX)) {
    if (currentX < targetX) {
      currentX++;
      servoX.write(currentX);
    } else if (currentX > targetX) {
      currentX--;
      servoX.write(currentX);
    }

    // Movimiento Y (Arriba - Abajo) — mismo tick
    if (currentY < targetY) {
      currentY++;
      servoY.write(currentY);
    } else if (currentY > targetY) {
      currentY--;
      servoY.write(currentY);
    }

    lastMoveTime = now;
  }

  // El loop no bloquea, así el ISR de I2C puede recibir nuevos comandos
  // incluso mientras los servos se mueven
}

static inline uint8_t getStepDelay(int current, uint8_t target) {
  uint8_t distance = abs(current - (int)target);
  if (distance > ACCEL_THRESHOLD) {
    return STEP_DELAY_BASE;  // rápido cuando está lejos
  }
  return STEP_DELAY_SLOW;    // lento cerca del objetivo (precisión)
}

void receiveEvent(int howMany) {
  if (howMany >= 2) {
    uint8_t tx = Wire.read();
    uint8_t ty = Wire.read();

    // Bounds checking: protege hardware de servos
    if (tx >= PAN_MIN && tx <= PAN_MAX) targetX = tx;
    if (ty >= TILT_MIN && ty <= TILT_MAX) targetY = ty;

    while (Wire.available()) Wire.read();  // limpiar overflow
  }
}

#include <Wire.h>
#include <Servo.h>
#include "config.h"

// ponytail: uint8_t = atómico en 8-bit (no race condition en ISR)
// ponytail: millis() instead of delay() → ISR I2C corre mientras servos se mueven
Servo servoX, servoY;

int currentX = PAN_CENTER, currentY = TILT_CENTER;
volatile uint8_t targetX = PAN_CENTER, targetY = TILT_CENTER;
unsigned long lastMove = 0;

void setup() {
  Wire.begin(SLAVE_ADDR);
  Wire.onReceive(receiveEvent);
  servoX.attach(9);
  servoY.attach(10);
  servoX.write(currentX);
  servoY.write(currentY);
  Serial.begin(9600);
  Serial.println("Musculo OK");
}

void loop() {
  if (millis() - lastMove >= STEP_DELAY_BASE) {
    if (currentX < targetX) servoX.write(++currentX);
    else if (currentX > targetX) servoX.write(--currentX);
    if (currentY < targetY) servoY.write(++currentY);
    else if (currentY > targetY) servoY.write(--currentY);
    lastMove = millis();
  }
}

void receiveEvent(int howMany) {
  if (howMany >= 2) {
    uint8_t tx = Wire.read(), ty = Wire.read();
    // ponytail: bounds en el ISR = protege hardware
    if (tx >= PAN_MIN && tx <= PAN_MAX) targetX = tx;
    if (ty >= TILT_MIN && ty <= TILT_MAX) targetY = ty;
    while (Wire.available()) Wire.read();
  }
}

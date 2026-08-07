# Sistema FIDAE — Rebirth

Sistema de visión y control de servos distribuido para FIDAE (proyecto escolar).
Un ESP32-CAM captura video, un Colab procesa con YOLOv8, y un Arduino controla
servos de pan/tilt vía I2C. Todo orquestado por un relay WebSocket en Vercel.

## Arquitectura

```
[ESP32-CAM] ──WS──→ [api/socket.js (Vercel)] ──WS──→ [Google Colab]
     ↓  (video raw)          ↓ (JSON coordenadas)      ↓ (pan/tilt)
[cámara QVGA]    →   [ESP32-WROOM] ──I2C──→ [Arduino Uno] ──PWM──→ [Servos]
                                              ↑ (video procesado)
                                          [web/index.html dashboard]
```

## Estructura de archivos

```
├── api/
│   └── socket.js              # Relay WebSocket (Vercel API route, Node.js)
├── web/
│   └── index.html             # Dashboard web (video + telemetría en tiempo real)
├── devices/
│   ├── esp32_cam/
│   │   └── ojo_esp32_cam.cpp    # Firmware cámara (video + WiFi + WS)
│   ├── esp32_wroom/
│   │   └── traductor_esp32_wroom.cpp  # Firmware traductor (WS → I2C)
│   └── arduino_musculo/
│       └── m_sculo_arduino_uno.cpp    # Control de servos (I2C → PWM)
├── colab/
│   ├── cerebro_colab.py       # YOLO tracking (envía coordenadas a servos)
│   └── sistema_de_vision_fidae.py  # Monitor pasivo (detección caras/OE/objetos)
├── shared/
│   ├── config.h               # Constantes del sistema (pines, límites, URL)
│   └── secrets.h.example      # Template: credenciales WiFi (NO subir a git)
├── vercel.json                # Configuración de routing
├── package.json               # Dependencias Node.js (ws)
├── requirements.txt           # → colab/ (solo para Colab, no Vercel)
└── README.md
```

## Configuración rápida

### 1. Credenciales WiFi (ESP32)

```bash
cp shared/secrets.h.example devices/esp32_cam/secrets.h
# Editar secrets.h con tus credenciales WiFi
cp devices/esp32_cam/secrets.h devices/esp32_wroom/secrets.h
```

### 2. URL del servidor WebSocket

Edita `shared/config.h` y cambia `WS_HOST` al hostname de tu despliegue Vercel:

```c
#define WS_HOST     "esp32-sv-publico-fidae.vercel.app"
```

### 3. Deploy en Vercel

1. Push a GitHub (o usa `vercel` CLI)
2. Vercel detecta `package.json` y `api/socket.js` automáticamente
3. El dashboard está disponible en `/`

### 4. Subir firmware

- **ESP32-CAM:** Arduino IDE → Board "AI-Thinker ESP32-CAM" → flash `devices/esp32_cam/ojo_esp32_cam.cpp`
- **ESP32-WROOM:** Arduino IDE → Board "ESP32 WROOM" → flash `devices/esp32_wroom/traductor_esp32_wroom.cpp`
- **Arduino Uno:** Arduino IDE → Board "Arduino Uno" → flash `devices/arduino_musculo/m_sculo_arduino_uno.cpp`

### 5. Colab

1. Abre `colab/cerebro_colab.py` en Colab
2. ¡Listo! (usa GPU por defecto)

## Correcciones aplicadas (Fidae Rebirth)

| Severidad | Componente | Fix |
|-----------|-----------|-----|
| 🔴 Crítica | credenciales | WiFi extraídas a `secrets.h` (gitignore) |
| 🔴 Crítica | cerebro_colab.py | Centro QVGA: `(160,120)` no `(320,240)` |
| 🔴 Crítica | cerebro_colab.py | Multi-objeto: se dibujan todas las cajas + tracking de personas |
| 🔴 Crítica | Arduino | Race condition I2C: `int`→`uint8_t` (átomico) |
| 🔴 Crítica | traductor_esp32_wroom | Bounds check `[0,180]` antes de I2C |
| 🔴 Crítica | ojo_esp32_cam | `fb_count=1`→`2` (frames no se pierden) |
| 🟠 Alta | todos ESP32 | WebSocket reconnection (`setReconnectInterval`) |
| 🟠 Alta | todos ESP32 | WiFi autoreconexión |
| 🟠 Alta | cerebro_colab.py | GPU: `device='cuda'` auto-detectado |
| 🟢 Media | Arduino | Movimiento non-blocking con `millis()` + aceleración |
| 🟢 Media | app.py→socket.js | Separados tipos de cliente (`?type=`) |

## Librerías Arduino necesarias

```
- ESP32 board package (Arduino IDE Boards Manager)
- arduinoWebSockets (v2.5.0+)
- ArduinoJson (v6.x)
```

## Deploy Vercel

```bash
npm install -g vercel
vercel --prod
```

O haz push a GitHub conectado a Vercel.

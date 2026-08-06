🏠 FIDAE Rebirth — Modo Local
=============================

Ejecuta TODO el sistema en tu red local, sin Vercel ni GitHub.

## 🚀 Inicio rápido

```bash
# 1. Inicia el servidor WebSocket
cd local/
npm install        # una vez (instala 'ws')
node server.js     # escucha en 0.0.0.0:8080

# 2. Configura los ESP32 con tu IP local
cp esp32_config.h ../devices/esp32_cam/config.h
cp esp32_config.h ../devices/esp32_wroom/config.h
# Edita esp32_config.h → WS_HOST = "192.168.X.X"

# 3. Sube firmware a ESP32 y Arduino
# (igual que en los docs setup_esp32_*.html)

# 4. Inicia el cerebro (YOLO local)
pip install ultralytics opencv-python websockets numpy
python local/cerebro_local.py
# → Ingresa tu IP local cuando se solicite
```

## 📡 Conexiones

| Componente | URL WebSocket |
|-----------|--------------|
| ESP32-CAM | `ws://TU_IP:8080/socket?type=camera` |
| ESP32-WROOM | `ws://TU_IP:8080/socket?type=translator` |
| Cerebro (Python) | `ws://TU_IP:8080/socket?type=colab` |
| Dashboard | `http://TU_IP:8080/` |

## 🔧 Encontrar tu IP local

- **Windows:** `ipconfig` → busca "Dirección IPv4"
- **Linux/Mac:** `ifconfig` o `ip a` → busca "inet"

## ⚠️ Notas

- El server.js escucha en `0.0.0.0` (todas las interfaces)
- El puerto 8080 debe estar libre (cierra otros servicios si hay conflicto)
- Si usas firewall de Windows, permite el puerto 8080
- El cerebro local usa CPU si no tienes GPU (YOLO es más lento pero funciona)

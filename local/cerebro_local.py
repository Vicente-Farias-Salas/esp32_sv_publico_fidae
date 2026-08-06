"""
Cerebro FIDAE — Modo Local
Ejecuta YOLOv8n localmente (CPU o CUDA) procesando frames del ESP32-CAM.
Reemplaza a Colab cuando corres el sistema sin Vercel.

Uso:
    python local/cerebro_local.py

El ESP32 debe apuntar a ws://TU_IP_LOCAL:8080/socket?type=camera
El WebSocket server debe estar corriendo:  node local/server.js
"""
import cv2
import numpy as np
import asyncio
import websockets
import json
import sys

WS_URL = "ws://TU_IP_LOCAL:8080/socket?type=colab"

FRAME_W, FRAME_H = 320, 240
CENTRO_X, CENTRO_Y = FRAME_W // 2, FRAME_H // 2
SUAVIZADAD = 25.0
PAN_MIN, PAN_MAX = 0, 180
TILT_MIN, TILT_MAX = 90, 160
CONF = 0.4

# ponytail: carga única, reutiliza si .to('cuda') falla
from ultralytics import YOLO
try:
    model = YOLO('yolov8n.pt').to('cuda')
    print("GPU: CUDA activada")
except Exception:
    model = YOLO('yolov8n.pt')
    print("GPU: usando CPU (más lento)")


async def run():
    coord_x, coord_y = 90.0, 125.0
    while True:
        try:
            async with websockets.connect(WS_URL, max_size=None) as ws:
                await ws.send(json.dumps({"type": "colab_connect", "role": "brain_local"}))
                print("Conectado al servidor local. Tracking...", flush=True)

                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    if isinstance(msg, str): continue

                    frame = cv2.imdecode(np.frombuffer(msg, np.uint8), cv2.IMREAD_COLOR)
                    if frame is None: continue

                    results = model.predict(frame, conf=CONF, verbose=False)
                    detected = False

                    for r in results:
                        # ponytail: prioriza personas, draw todas las cajas
                        best = None
                        for box in r.boxes:
                            cls = model.names[int(box.cls[0])]
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            color = (0, 255, 0) if cls == "person" else (0, 200, 255)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
                            cv2.putText(frame, cls, (x1, y1 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
                            if cls == "person" and best is None:
                                best = box

                        if best:
                            detected = True
                            x1, y1, x2, y2 = map(int, best.xyxy[0])
                            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                            coord_x -= (cx - CENTRO_X) / SUAVIZADAD
                            coord_y += (cy - CENTRO_Y) / SUAVIZADAD
                            coord_x = float(np.clip(coord_x, PAN_MIN, PAN_MAX))
                            coord_y = float(np.clip(coord_y, TILT_MIN, TILT_MAX))
                            cv2.line(frame, (CENTRO_X, CENTRO_Y), (int(cx), int(cy)), (0, 255, 255), 2)

                    cv2.putText(frame, f"X:{int(coord_x)} Y:{int(coord_y)}", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                    cv2.drawMarker(frame, (CENTRO_X, CENTRO_Y), (0, 255, 0), cv2.MARKER_CROSS, 15, 1)

                    if detected:
                        await ws.send(json.dumps({"pan": int(coord_x), "tilt": int(coord_y)}))

                    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    await ws.send(buf.tobytes())

                    cv2.imshow("FIDAE Local Brain", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'): sys.exit(0)

        except (websockets.ConnectionClosed, OSError) as e:
            print(f"Desconectado: {e}. Reconectando en 3s...", flush=True)
            await asyncio.sleep(3)


if __name__ == "__main__":
    print("Instrucciones:")
    print("  1. Encuentra tu IP local: ifconfig (Linux/Mac) o ipconfig (Windows)")
    print("  2. Edita WS_URL arriba con tu IP")
    print("  3. Inicia el server: node local/server.js")
    print("  4. Conecta los ESP32 a esa IP:8080")
    print("---")
    # ponytail: valida IP antes de conectar
    WS_URL = WS_URL.replace("TU_IP_LOCAL", input(" IP local de tu PC: "))
    asyncio.run(run())

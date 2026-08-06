!pip install ultralytics opencv-python-headless websockets numpy -q

import cv2
import numpy as np
import asyncio
import websockets
import json
import time
import nest_asyncio
from ultralytics import YOLO
from IPython.display import clear_output, display
from google.colab.patches import cv2_imshow

nest_asyncio.apply()

# ============================================================
# CONFIGURACIÓN — Ajusta estos valores según tu hardware
# ============================================================
WS_URL = "wss://TU-PROJECTO.vercel.app/api/socket?type=colab"
# WS_URL = "wss://esp32-sv-publico-fidae.onrender.com/colab"  # backup

FRAME_W, FRAME_H = 320, 240   # QVGA (ESP32-CAM config)
CENTRO_X, CENTRO_Y = FRAME_W // 2, FRAME_H // 2  # FIX: era (320, 240) — bug crítico
SUAVIDAD  = 25.0
PAN_MIN, PAN_MAX  = 0, 180
TILT_MIN, TILT_MAX = 90, 160
CONF_THRESH = 0.4
FPS_MOSTRAR = 5   # solo mostra imagen cada N frames (reduce flicker)

# Detectar GPU automáticamente
try:
    GPU = "cuda"
    model = YOLO('yolov8n.pt').to('cuda')
    print("GPU detectada: usando CUDA")
except Exception:
    GPU = "cpu"
    model = YOLO('yolov8n.pt')
    print("Sin GPU: usando CPU")


async def radar_yolo_servos():
    coord_x = float(PAN_MIN + (PAN_MAX - PAN_MIN) // 2)  # 90.0
    coord_y = float(TILT_MIN + (TILT_MAX - TILT_MIN) // 2)  # ~125.0
    frame_count = 0

    while True:
        try:
            print("Conectando WebSocket a Vercel...", flush=True)
            async with websockets.connect(WS_URL, max_size=None, ping_timeout=600) as ws:
                print("Conectado. Enviando identificacion...", flush=True)
                await ws.send(json.dumps({"type": "colab_connect", "role": "processor"}))

                while True:
                    try:
                        mensaje = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    except asyncio.TimeoutError:
                        print("Timeout esperando frames... reintentando", flush=True)
                        await asyncio.sleep(2)
                        break  # sale del inner while → reconectar outer while

                    if isinstance(mensaje, str):
                        continue  # ignorar ecos de texto

                    # Decodificar frame
                    nparr = np.frombuffer(mensaje, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    frame_count += 1
                    detectado = False

                    # YOLO en GPU (no stream=True para evitar overhead)
                    results = model.predict(frame, conf=CONF_THRESH, verbose=False, device=GPU)

                    for r in results:
                        mejor_distancia = float('inf')
                        mejor_caja = None

                        for box in r.boxes:
                            cls = int(box.cls[0])
                            cls_name = model.names[cls]

                            # Priorizar personas (cls == 0 "person")
                            if cls_name == "person":
                                dist = 0  # prioridad máxima
                            else:
                                dist = 1  # otras clases después

                            if dist < mejor_distancia:
                                mejor_distancia = dist
                                mejor_caja = box

                            # Dibujar TODAS las cajas detectadas (visualización completa)
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                            cv2.putText(frame, cls_name, (x1, y1 - 3),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)

                        if mejor_caja is not None:
                            detectado = True
                            x1, y1, x2, y2 = map(int, mejor_caja.xyxy[0])
                            cx = (x1 + x2) / 2.0
                            cy = (y1 + y2) / 2.0

                            error_x = cx - CENTRO_X
                            error_y = cy - CENTRO_Y

                            coord_x -= (error_x / SUAVIDAD)
                            coord_y += (error_y / SUAVIDAD)

                            coord_x = float(np.clip(coord_x, PAN_MIN, PAN_MAX))
                            coord_y = float(np.clip(coord_y, TILT_MIN, TILT_MAX))

                            cv2.line(frame, (int(CENTRO_X), int(CENTRO_Y)),
                                     (int(cx), int(cy)), (0, 255, 255), 2)

                    # HUD
                    cv2.putText(frame, f"X:{int(coord_x)} Y:{int(coord_y)}", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                    cv2.drawMarker(frame, (int(CENTRO_X), int(CENTRO_Y)),
                                   (0, 255, 0), cv2.MARKER_CROSS, 15, 1)

                    # Enviar coordenadas al translate (ESP32-WROOM)
                    if detectado:
                        await ws.send(json.dumps({
                            "pan": int(coord_x),
                            "tilt": int(coord_y)
                        }))

                    # Enviar frame procesado al viewer (dashboard)
                    success, buf = cv2.imencode('.jpg', frame,
                                                [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    if success:
                        await ws.send(buf.tobytes())

                    # Mostrar en Colab (limitado para reducir flicker)
                    if frame_count % FPS_MOSTRAR == 0:
                        clear_output(wait=True)
                        cv2_imshow(frame)
                        print(f"Frames: {frame_count} | Pan: {int(coord_x)} Tilt: {int(coord_y)}",
                              flush=True)

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"WebSocket desconectado: {e}. Reconectando en 3s...", flush=True)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Error critico: {e}. Reintentando...", flush=True)
            await asyncio.sleep(3)


try:
    asyncio.run(radar_yolo_servos())
except KeyboardInterrupt:
    print("\nCerebro detenido.")

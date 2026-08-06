!pip install ultralytics opencv-python-headless websockets numpy -q

import cv2
import numpy as np
import asyncio
import websockets
import json
import sys
import time
import nest_asyncio
from ultralytics import YOLO
from google.colab.patches import cv2_imshow

nest_asyncio.apply()

# ============================================================
# CONFIGURACIÓN
# ============================================================
WS_URL = "wss://TU-PROJECTO.vercel.app/api/socket?type=colab"

INVERTIR_CAMARA = False
CONF_THRESH = 0.45
JPEG_CALIDAD = 75
RECONNECT_BASE = 3  # segundos base para backoff de reconexión

# GPU auto-detect
try:
    DEVICE = "cuda"
    model_yolo = YOLO('yolov8n.pt').to('cuda')
    print("GPU: CUDA activada")
except Exception:
    DEVICE = "cpu"
    model_yolo = YOLO('yolov8n.pt')
    print("GPU: no disponible, usando CPU")

# Haar cascade para caras
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)


async def sistema_vision_fidae():
    print(f"Conectando a {WS_URL}...", flush=True)
    intento = 0

    while True:
        try:
            async with websockets.connect(WS_URL, ping_timeout=600, max_size=None) as ws:
                intento = 0  # resetear backoff
                await ws.send(json.dumps({"type": "colab_connect", "mode": "monitor"}))
                print("Monitor de vision ONLINE — analizando entorno", flush=True)

                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    except asyncio.TimeoutError:
                        print("Timeout esperando frames... reconectando", flush=True)
                        break  # sale inner while → reconectar

                    if isinstance(message, str):
                        continue  # ignorar ecos de texto

                    nparr = np.frombuffer(message, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    # Opcional: rotar cámara
                    if INVERTIR_CAMARA:
                        frame = cv2.flip(frame, -1)

                    h, w = frame.shape[:2]
                    cx, cy = w // 2, h // 2
                    overlay = frame.copy()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # --- 1. Detección de reflejos / objetos extraños (OE) ---
                    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
                    _, thresh = cv2.threshold(blurred, 230, 255, cv2.THRESH_BINARY)
                    cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)

                    for c in cnts:
                        if cv2.contourArea(c) > 8:
                            cv2.drawContours(overlay, [c], -1, (0, 0, 255), 2)
                            M = cv2.moments(c)
                            if M["m00"] != 0:
                                ox, oy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                                cv2.putText(overlay, "OE", (ox - 12, oy - 8),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

                    # --- 2. Detección de caras (Haar Cascade) ---
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                    for (x, y, fw, fh) in faces:
                        cv2.rectangle(overlay, (x, y), (x + fw, y + fh), (255, 0, 255), 1)
                        cv2.putText(overlay, "HUMANO", (x, y - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)

                    # --- 3. YOLOv8 (objetos y personas de cuerpo entero) ---
                    results = model_yolo(overlay, stream=True, verbose=False, device=DEVICE)
                    objetos = 0
                    for r in results:
                        for box in r.boxes:
                            if float(box.conf[0]) > CONF_THRESH:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cls = int(box.cls[0])
                                name = model_yolo.names[cls].upper()
                                objetos += 1
                                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), 1)
                                cv2.putText(overlay, name, (x1, y1 - 3),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)

                    # --- HUD ---
                    cv2.putText(overlay, "SISTEMA DE ANALISIS PASIVO", (10, 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    cv2.putText(overlay, f"Obj: {objetos} | Rostros: {len(faces)} | OE: {len(cnts)}",
                                (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                    cv2.drawMarker(overlay, (cx, cy), (150, 150, 150),
                                   cv2.MARKER_CROSS, 15, 1)

                    # Enviar frame procesado al viewer (dashboard)
                    _, buff = cv2.imencode('.jpg', overlay, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_CALIDAD])
                    await ws.send(buff.tobytes())

                    sys.stdout.write(
                        f"\rObj: {objetos} | Rost: {len(faces)} | OE: {len(cnts)}   "
                    )
                    sys.stdout.flush()

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            intento += 1
            delay = min(RECONNECT_BASE * intento, 30)
            print(f"\nDesconectado: {e}. Reconectando en {delay}s...", flush=True)
            await asyncio.sleep(delay)
        except Exception as e:
            print(f"\nError inesperado: {e}. Reintentando...", flush=True)
            await asyncio.sleep(RECONNECT_BASE)


try:
    asyncio.run(sistema_vision_fidae())
except KeyboardInterrupt:
    print("\nSistema detenido.")

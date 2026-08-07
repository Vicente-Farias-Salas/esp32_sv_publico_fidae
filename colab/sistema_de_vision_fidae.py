!pip install ultralytics opencv-python-headless websockets numpy -q

import cv2
import numpy as np
import asyncio
import websockets
import json
import sys
import nest_asyncio
from ultralytics import YOLO

nest_asyncio.apply()

WS_URL = "wss://esp32-sv-publico-fidae.vercel.app/api/socket?type=colab"
CONF = 0.45
JPEG_QUAL = 75

# ponytail: GPU auto-detect
try:
    model = YOLO('yolov8n.pt').to('cuda'); DEVICE = 'cuda'
except Exception:
    model = YOLO('yolov8n.pt'); DEVICE = 'cpu'

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

async def run():
    intento = 0
    while True:
        try:
            async with websockets.connect(WS_URL, max_size=None) as ws:
                intento = 0
                await ws.send(json.dumps({"type": "colab_connect", "mode": "monitor"}))
                print("Monitor ONLINE", flush=True)

                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    if isinstance(msg, str): continue

                    frame = cv2.imdecode(np.frombuffer(msg, np.uint8), cv2.IMREAD_COLOR)
                    if frame is None: continue

                    h, w = frame.shape[:2]
                    overlay = frame.copy()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # OE (reflejos)
                    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
                    _, thresh = cv2.threshold(blurred, 230, 255, cv2.THRESH_BINARY)
                    cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    for c in cnts:
                        if cv2.contourArea(c) > 8:
                            cv2.drawContours(overlay, [c], -1, (0, 0, 255), 2)

                    # Caras
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                    for (x, y, fw, fh) in faces:
                        cv2.rectangle(overlay, (x, y), (x + fw, y + fh), (255, 0, 255), 1)

                    # YOLO
                    results = model(overlay, stream=True, verbose=False, device=DEVICE)
                    objs = 0
                    for r in results:
                        for box in r.boxes:
                            if float(box.conf[0]) > CONF:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                name = model.names[int(box.cls[0])].upper()
                                objs += 1
                                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), 1)
                                cv2.putText(overlay, name, (x1, y1 - 3),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)

                    cv2.putText(overlay, "SISTEMA DE ANALISIS PASIVO", (10, 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    cv2.drawMarker(overlay, (w // 2, h // 2), (150, 150, 150),
                                   cv2.MARKER_CROSS, 15, 1)

                    _, buff = cv2.imencode('.jpg', overlay, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUAL])
                    await ws.send(buff.tobytes())

                    sys.stdout.write(f"\rObjs:{objs} Faces:{len(faces)} OE:{len(cnts)} ")
                    sys.stdout.flush()

        except (websockets.ConnectionClosed, OSError) as e:
            delay = min(3 * intento, 30); intento += 1
            print(f"\nDesconectado: {e}. Reconectar en {delay}s...", flush=True)
            await asyncio.sleep(delay)

try:
    asyncio.run(run())
except KeyboardInterrupt:
    print("\nDetenido.")

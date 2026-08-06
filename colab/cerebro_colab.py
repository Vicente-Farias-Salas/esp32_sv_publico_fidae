!pip install ultralytics opencv-python-headless websockets numpy -q

import cv2
import numpy as np
import asyncio
import websockets
import json
import nest_asyncio
from ultralytics import YOLO
from IPython.display import clear_output
from google.colab.patches import cv2_imshow

nest_asyncio.apply()

WS_URL = "wss://TU-PROJECTO.vercel.app/api/socket?type=colab"
FRAME_W, FRAME_H = 320, 240
CENTRO_X, CENTRO_Y = FRAME_W // 2, FRAME_H // 2   # FIX: (160, 120) no (320, 240)
SUAVIDAD = 25.0
PAN_MIN, PAN_MAX = 0, 180
TILT_MIN, TILT_MAX = 90, 160
CONF = 0.4

# ponytail: GPU auto-detect, una sola línea
try:
    model = YOLO('yolov8n.pt').to('cuda'); DEVICE = 'cuda'
except Exception:
    model = YOLO('yolov8n.pt'); DEVICE = 'cpu'

async def run():
    coord_x, coord_y = 90.0, 125.0

    while True:
        try:
            async with websockets.connect(WS_URL, max_size=None) as ws:
                await ws.send(json.dumps({"type": "colab_connect"}))
                print("Conectado. Tracking...", flush=True)

                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    if isinstance(msg, str): continue

                    frame = cv2.imdecode(np.frombuffer(msg, np.uint8), cv2.IMREAD_COLOR)
                    if frame is None: continue

                    results = model.predict(frame, conf=CONF, verbose=False, device=DEVICE)
                    detectado = False

                    for r in results:
                        # ponytail: priorizar personas, draw todas las cajas
                        best = min(r.boxes, key=lambda b: 0 if model.names[int(b.cls[0])] == 'person' else 1)
                        if best is not None:
                            detectado = True
                            x1, y1, x2, y2 = map(int, best.xyxy[0])
                            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                            coord_x -= (cx - CENTRO_X) / SUAVIDAD
                            coord_y += (cy - CENTRO_Y) / SUAVIDAD
                            coord_x = float(np.clip(coord_x, PAN_MIN, PAN_MAX))
                            coord_y = float(np.clip(coord_y, TILT_MIN, TILT_MAX))

                        for box in r.boxes:  # dibujar todas
                            cls = model.names[int(box.cls[0])]
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                            cv2.putText(frame, cls, (x1, y1 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)

                    cv2.putText(frame, f"X:{int(coord_x)} Y:{int(coord_y)}", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                    cv2.drawMarker(frame, (CENTRO_X, CENTRO_Y), (0, 255, 0), cv2.MARKER_CROSS, 15, 1)

                    if detectado:
                        await ws.send(json.dumps({"pan": int(coord_x), "tilt": int(coord_y)}))
                    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    await ws.send(buf.tobytes())

                    clear_output(wait=True); cv2_imshow(frame)

        except (websockets.ConnectionClosed, OSError) as e:
            print(f"Desconectado: {e}. Reconectando...", flush=True)
            await asyncio.sleep(3)

asyncio.run(run())

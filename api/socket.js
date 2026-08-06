import http from 'http';
import { WebSocketServer } from 'ws';

/**
 * Relay WebSocket para FIDAE — Vercel Node.js
 * ponytail: 1 Map en vez de 4 Sets = menos código, mismo comportamiento
 *
 * Query param ?type= identifica: camera | translator | colab | viewer
 */
const clients = new Map();  // ws → tipo de cliente

const server = http.createServer();
const wss = new WebSocketServer({ server });

wss.on('connection', (ws, request) => {
  const url = new URL(request.url || '', `http://${request.headers.host || 'localhost'}`);
  const type = url.searchParams.get('type') || 'unknown';
  clients.set(ws, type);

  ws.on('message', (data, isBinary) => {
    if (isBinary) {
      // camera → colab (video raw) | colab → viewer (video procesado)
      const target = (type === 'camera') ? 'colab' : 'viewer';
      for (const [c, t] of clients) {
        if (t === target && c.readyState === 1) c.send(data, { binary: true });
      }
    } else {
      // colab → translator (JSON pan/tilt) + viewer (telemetría)
      const text = data.toString();
      for (const [c, t] of clients) {
        if ((t === 'translator' || t === 'viewer') && c.readyState === 1) c.send(text);
      }
    }
  });

  ws.on('close', () => clients.delete(ws));
  ws.on('error', () => clients.delete(ws));
});

export default server;

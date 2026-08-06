import http from 'http';
import { WebSocketServer } from 'ws';
import { readFileSync, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 8080;

const clients = new Map();

const server = http.createServer((req, res) => {
  let path = req.url === '/' ? '/dashboard.html' : req.url;
  try {
    const content = readFileSync(`${__dirname}${path}`);
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(content);
  } catch {
    res.writeHead(404); res.end('Not found');
  }
});

const wss = new WebSocketServer({ server, path: '/socket' });
wss.on('connection', (ws, request) => {
  const qs = (request.url || '').split('?')[1] || '';
  const type = new URLSearchParams(qs).get('type') || 'unknown';
  clients.set(ws, type);

  ws.on('message', (data, isBinary) => {
    if (isBinary) {
      const target = type === 'camera' ? 'colab' : 'viewer';
      for (const [c, t] of clients) if (t === target && c.readyState === 1) c.send(data, { binary: true });
    } else {
      for (const [c, t] of clients) if ((t === 'translator' || t === 'viewer') && c.readyState === 1) c.send(data.toString());
    }
  });

  ws.on('close', () => clients.delete(ws));
  ws.on('error', () => clients.delete(ws));
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`\nServidor local FIDAE en http://TU_IP:8080\nWebSocket: ws://TU_IP:8080/socket?type=...\n`);
});

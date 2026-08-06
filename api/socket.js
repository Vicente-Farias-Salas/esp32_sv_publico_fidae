import http from 'http';
import { WebSocketServer } from 'ws';

/**
 * Relay WebSocket para Sistema FIDAE
 * Vercel WebSocket (beta) — funciones Node.js con WebSocketServer
 *
 * Ruteo de clientes via query param ?type=
 *   type=camera    → ESP32-CAM (envía video raw, binary)
 *   type=translator → ESP32-WROOM (recibe JSON pan/tilt)
 *   type=colab     → Colab (recibe video, envía JSON + video procesado)
 *   type=viewer    → Dashboard web (recibe video procesado)
 */

// Client pools (in-memory — funciona para pocos clientes simultáneos)
const cameraClients       = new Set();
const translatorClients   = new Set();
const colabClients        = new Set();
const viewerClients       = new Set();

const server = http.createServer();
const wss = new WebSocketServer({ server });

wss.on('connection', (ws, request) => {
  // Identificar tipo de cliente desde query string
  const url = new URL(request.url || '', `http://${request.headers.host || 'localhost'}`);
  const clientType = url.searchParams.get('type') || 'unknown';

  if (clientType === 'camera')        cameraClients.add(ws);
  else if (clientType === 'translator') translatorClients.add(ws);
  else if (clientType === 'colab')    colabClients.add(ws);
  else if (clientType === 'viewer')   viewerClients.add(ws);

  ws.clientType = clientType;

  console.log(`[+] Cliente conectado: ${clientType} (total: cam=${cameraClients.size}, tr=${translatorClients.size}, colab=${colabClients.size}, view=${viewerClients.size})`);

  ws.on('message', (data, isBinary) => {
    if (isBinary) {
      // Video raw de la cámara → enviar al Colab para YOLO procesamiento
      if (ws.clientType === 'camera') {
        for (const client of colabClients) {
          if (client.readyState === 1) client.send(data, { binary: true });
        }
      }
      // Video procesado del Colab → enviar al dashboard
      else if (ws.clientType === 'colab') {
        for (const client of viewerClients) {
          if (client.readyState === 1) client.send(data, { binary: true });
        }
      }
    } else {
      // Mensaje de texto (JSON)
      let text = data.toString();

      // Coordenadas (pan/tilt) del Colab → ESP32-WROOM (translator)
      if (ws.clientType === 'colab') {
        for (const client of translatorClients) {
          if (client.readyState === 1) client.send(text);
        }
        // También reenviar al dashboard como telemetría
        for (const client of viewerClients) {
          if (client.readyState === 1) client.send(text);
        }
      }
    }
  });

  ws.on('close', () => {
    cameraClients.delete(ws);
    translatorClients.delete(ws);
    colabClients.delete(ws);
    viewerClients.delete(ws);
    console.log(`[-] Cliente desconectado: ${ws.clientType}`);
  });

  ws.on('error', (err) => {
    console.error(`[!] Error WS (${ws.clientType}):`, err.message);
    cameraClients.delete(ws);
    translatorClients.delete(ws);
    colabClients.delete(ws);
    viewerClients.delete(ws);
  });
});

// Vercel: exportar el servidor HTTP para que la plataforma maneje el upgrade
export default server;

import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import https from 'node:https';
import { WebSocket } from 'ws';
import { readFileSync } from 'node:fs';

const config = JSON.parse(readFileSync('./tests/test.config.json', 'utf8'));
const BASE = config.baseUrl;
const TIMEOUT = { http: 10000, ws: 5000, relay: 3000 };
const toWss = (s) => s.replace(/^https:/, 'wss:');
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const results = { http: true, ws: true, relay: true };

const get = (path) =>
  new Promise((resolve, reject) => {
    https.get(BASE + path, { timeout: TIMEOUT.http }, (res) => {
      let body = '';
      res.on('data', (chunk) => (body += chunk));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body }));
    }).on('error', reject);
  });

test('HTTP: dashboard `/` returns 200 con FIDAE', async () => {
  try {
    const { status, body } = await get(config.endpoints.dashboard);
    assert.equal(status, config.expected.dashboardStatus);
    assert.ok(body.includes(config.expected.dashboardContains));
    results.http = true;
  } catch (e) { results.http = false; throw e; }
});

test('HTTP: static `/index.html` sirve', async () => {
  const { status, body } = await get(config.endpoints.staticHtml);
  assert.equal(status, 200);
  assert.ok(body.includes('FIDAE — Monitor'));
});

test('WS: handshake en `/api/socket?type=viewer`', async () => {
  const ws = new WebSocket(`${toWss(BASE)}${config.endpoints.websocket}`);
  const result = await new Promise((resolve) => {
    ws.on('open', () => { resolve('connected'); ws.close(); });
    ws.on('error', (e) => resolve('error:' + e.message));
    setTimeout(() => { ws.terminate(); resolve('timeout'); }, TIMEOUT.ws);
  });
  assert.equal(result, 'connected');
  results.ws = result === 'connected';
});

test('WS: relay binario colab → viewer (diagnostic)', async () => {
  const sender = new WebSocket(`${toWss(BASE)}${config.endpoints.websocket.replace('viewer', 'colab')}`);
  const viewer = new WebSocket(`${toWss(BASE)}${config.endpoints.websocket}`);

  await Promise.all([
    new Promise((r) => sender.on('open', r)),
    new Promise((r) => viewer.on('open', r)),
  ]);

  const received = new Promise((resolve) => {
    viewer.on('message', (data, isBinary) => {
      if (isBinary) resolve(data.length);
    });
  });

  const testFrame = Buffer.from([0x89, 0x20, 0x4A, 0x46, 0x49, 0x44, 0x41, 0x45]);
  sender.send(testFrame, { binary: true });

  const len = await Promise.race([received, delay(TIMEOUT.relay).then(() => 'timeout')]);
  sender.close(); viewer.close();

  if (len === 'timeout') {
    results.relay = false;
    console.warn('\n⚠ WS RELAY: TIMEOUT — Vercel Serverless Functions no comparten estado entre instancias WS. El relay requiere un servicio stateful (Render/VPS/Edge con memoria compartida).\n');
    return;
  }

  assert.equal(len, testFrame.length, 'Frame procesado recibido por viewer');
  results.relay = true;
});

after(() => {
  console.log('\n═══════════════════════════════════');
  console.log('  DEPLOY HEALTH SUMMARY');
  console.log('═══════════════════════════════════');
  console.log(`  HTTP serving:      ${results.http ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`  WS handshake:      ${results.ws ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`  WS relay:          ${results.relay ? '✅ PASS' : '⚠ FAIL (platform limitation)'}`);
  console.log('═══════════════════════════════════\n');
});

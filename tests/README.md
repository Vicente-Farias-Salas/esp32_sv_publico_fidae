# Deploy Validation Tests

Validan que un deploy de FIDAE funciona correctamente:

## Tests

| # | Test | Qué verifica |
|---|------|-------------|
| 1 | `HTTP: dashboard` | GET `/` → 200 con contenido "FIDAE" |
| 2 | `HTTP: static` | GET `/index.html` → 200 con dashboard |
| 3 | `WS: handshake` | WebSocket upgrade a `/api/socket?type=viewer` → conexión OK |
| 4 | `WS: relay` | Relay binario `colab → viewer` (diagnostic) |

## Uso

```bash
# Después de deploy
npm test

# O directamente
node tests/run_tests.js --test
```

## Interpretación

- `✅ PASS` = Funciona
- `⚠ FAIL (platform limitation)` = El relay WS no funciona en Vercel Serverless Functions (no comparten estado entre instancias). Requiere servicio stateful (Render/VPS) o Vercel Edge con memoria compartida.

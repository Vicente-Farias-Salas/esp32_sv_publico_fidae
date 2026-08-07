# Graph Report - .  (2026-08-06)

## Corpus Check
- Corpus is ~7,329 words - fits in a single context window. You may not need a graph.

## Summary
- 63 nodes · 52 edges · 14 communities (10 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- local/package.json
- package.json
- esp32_cam/config.h
- esp32_wroom/config.h
- server.js
- socket.js
- cerebro_local.py
- dependencies
- vercel.json

## God Nodes (most connected - your core abstractions)
1. `scripts` - 4 edges
2. `scripts` - 3 edges
3. `reconnectWiFi()` - 2 edges
4. `loop()` - 2 edges
5. `reconnectWiFi()` - 2 edges
6. `loop()` - 2 edges
7. `ws` - 2 edges
8. `engines` - 2 edges
9. `ws` - 2 edges
10. `engines` - 2 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (14 total, 4 thin omitted)

### Community 0 - "local/package.json"
Cohesion: 0.15
Nodes (12): dependencies, ws, engines, node, ws, name, private, scripts (+4 more)

### Community 1 - "package.json"
Cohesion: 0.18
Nodes (10): engines, node, name, private, scripts, dev, lint, start (+2 more)

### Community 5 - "server.js"
Cohesion: 0.40
Nodes (4): clients, __dirname, server, wss

### Community 6 - "socket.js"
Cohesion: 0.50
Nodes (3): clients, server, wss

### Community 8 - "dependencies"
Cohesion: 0.67
Nodes (3): dependencies, ws, ws

## Knowledge Gaps
- **26 isolated node(s):** `clients`, `server`, `wss`, `name`, `version` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dependencies` connect `dependencies` to `package.json`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **What connects `clients`, `server`, `wss` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
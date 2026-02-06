GCID Frontend — Quick Start

This frontend is a lightweight, production-ready real-time web client that connects to the GCID FastAPI WebSocket server.

Run locally:
1. Start the backend server (example using the provided `.venv`):
   ```bash
   .venv\Scripts\python -m uvicorn backend.app.main:app --port 8001 --app-dir backend
   ```

2. Serve the frontend (from project root) using the simple Python file server:
   ```bash
   cd frontend
   python -m http.server 8080
   ```

3. Open http://localhost:8080 in your browser. Set the WebSocket URL (default `ws://localhost:8001/ws`) and click Connect.

Notes:
- The server sends `frame` messages (base64 jpeg), `state` messages (JSON with canvas as base64), and `gestures` arrays.
- The frontend supports commands via JSON messages: `{type:"command", action:"undo"}` etc.
- For packaging as a desktop app, use Tauri (recommended for small distribution) or Electron.

Development tips:
- When testing locally you may need to allow mixed content if serving the frontend with https and the ws endpoint is ws (instead, use wss or use http).
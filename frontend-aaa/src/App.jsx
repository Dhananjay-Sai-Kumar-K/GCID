import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Hand,
  Palette,
  Eraser,
  Undo2,
  Redo2,
  Plus,
  Trash2,
  Download,
  Activity,
  Wifi,
  WifiOff,
  Settings,
  Maximize2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

function App() {
  const [wsUrl, setWsUrl] = useState('ws://localhost:8000/ws');
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('Disconnected');
  const [gestures, setGestures] = useState([]);
  const [tool, setTool] = useState('pen');
  const [pageInfo, setPageInfo] = useState({ current: 1, total: 1 });
  const [fps, setFps] = useState(0);
  const [color, setColor] = useState('#ff0000');
  const [thickness, setThickness] = useState(5);

  const wsRef = useRef(null);
  const canvasRef = useRef(null);
  const frameImgRef = useRef(null);
  const lastFrameTimeRef = useRef(performance.now());

  // WebSocket Connection
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setStatus('Connected');
    };

    ws.onclose = () => {
      setIsConnected(false);
      setStatus('Disconnected');
      setTimeout(connect, 1500);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('Error');
      ws.close();
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch (err) {
        console.warn('Non-JSON message:', err);
      }
    };
  }, [wsUrl]);

  const handleMessage = useCallback((msg) => {
    if (msg.type === 'frame') {
      // 1. Ignore msg.image (Camera Feed) - we don't want to see it

      // 2. Draw Landmarks on the overlay canvas
      if (msg.landmarks) {
        drawLandmarks(msg.landmarks);
      } else {
        // Clear landmarks if none (e.g. hand lost)
        const canvas = canvasRef.current;
        if (canvas) {
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }

      const now = performance.now();
      const calculatedFps = 1000 / (now - lastFrameTimeRef.current);
      lastFrameTimeRef.current = now;
      setFps(Math.round(calculatedFps));

    } else if (msg.type === 'state') {
      setTool(msg.tool || 'pen');
      setPageInfo({
        current: (msg.page_index || 0) + 1,
        total: msg.total_pages || 1
      });

      // 3. Display Whiteboard/UI in the main Image Element (Background)
      if (msg.canvas && frameImgRef.current) {
        frameImgRef.current.src = `data:image/jpeg;base64,${msg.canvas}`;
      }
    }

    if (msg.gestures) {
      setGestures(msg.gestures);
    }
  }, []);

  const drawLandmarks = useCallback((landmarks) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Use internal dimensions if image not loaded yet, or match container
    // The resize handler ensures width/height are correct
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = 'rgba(124, 58, 237, 0.9)';
    ctx.strokeStyle = 'rgba(167, 139, 250, 0.6)';
    ctx.lineWidth = 2;

    // We assume backend resized landmarks to 850x550, so we just map to canvas size
    // But canvas size is set to clientWidth/Height of the container/img

    // We need to know the SOURCE resolution (850x550) to scale correctly?
    // Actually FrameProcessor now resizes frame to 850x550.
    // Landmarks are returned as pixel coordinates (0..850, 0..550).
    // The canvas on screen might be responsive (e.g. 1200px wide).

    // So we need to scale landmarks from (850x550) to (canvas.width x canvas.height)
    const scaleX = canvas.width / 850;
    const scaleY = canvas.height / 550;

    Object.values(landmarks).forEach(([x, y]) => {
      ctx.beginPath();
      ctx.arc(x * scaleX, y * scaleY, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });
  }, []);

  // Removed drawCanvas as it is no longer needed (replaced by img.src)
  const sendCommand = useCallback((action, params = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'command', action, params }));
    }
  }, []);

  const hexToRgb = (hex) => {
    const bigint = parseInt(hex.slice(1), 16);
    return {
      r: (bigint >> 16) & 255,
      g: (bigint >> 8) & 255,
      b: bigint & 255
    };
  };

  const handleColorChange = (newColor) => {
    setColor(newColor);
    const rgb = hexToRgb(newColor);
    sendCommand('set_color', { color: [rgb.r, rgb.g, rgb.b] });
  };

  const handleThicknessChange = (newThickness) => {
    setThickness(newThickness);
    sendCommand('set_thickness', { thickness: parseInt(newThickness, 10) });
  };

  const downloadCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = 'gcid_canvas.png';
    link.click();
  };

  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      const frameImg = frameImgRef.current;
      if (canvas && frameImg) {
        canvas.width = frameImg.clientWidth;
        canvas.height = frameImg.clientHeight;
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (frameImgRef.current) {
      frameImgRef.current.onload = () => {
        const canvas = canvasRef.current;
        const frameImg = frameImgRef.current;
        if (canvas && frameImg) {
          canvas.width = frameImg.clientWidth;
          canvas.height = frameImg.clientHeight;
        }
      };
    }
  }, []);

  return (
    <div className="app">
      {/* Header */}
      <header className="header glass-effect">
        <div className="header-left">
          <div className="logo">
            <Hand className="logo-icon" />
            <h1 className="gradient-text">Gesture Craft</h1>
          </div>
        </div>

        <div className="header-center">
          <div className="connection-bar">
            <input
              type="text"
              className="input input-compact"
              value={wsUrl}
              onChange={(e) => setWsUrl(e.target.value)}
              placeholder="ws://localhost:8000/ws"
            />
            <button
              className={`btn ${isConnected ? 'btn-success' : 'btn-primary'} btn-compact`}
              onClick={connect}
            >
              {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
              {isConnected ? 'Connected' : 'Connect'}
            </button>
          </div>
        </div>

        <div className="header-right">
          <div className="status-badge">
            <Activity size={16} />
            <span>{fps} FPS</span>
          </div>
          <button
            className="btn btn-secondary btn-icon-only"
            onClick={downloadCanvas}
            title="Download Canvas"
          >
            <Download size={20} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content centered-layout">
        <div className="canvas-container glass-effect">
          <div className="canvas-wrapper">
            <img
              ref={frameImgRef}
              className="frame-img"
              alt="Whiteboard"
            />
            <canvas
              ref={canvasRef}
              className="overlay-canvas"
              width={850}
              height={550}
            />
          </div>
        </div>

        {/* Helper Instructions / Toast */}
        <div className="helper-toast">
          Use hand gestures to interact with buttons on the whiteboard.
        </div>
      </main>
    </div>
  );
}

export default App;

# 🎯 Gesture Craft - AAA-Grade Hand Tracking Studio

<div align="center">

![Gesture Craft](https://img.shields.io/badge/Gesture-Craft-7c3aed?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61dafb?style=for-the-badge&logo=react&logoColor=black)
![Electron](https://img.shields.io/badge/Electron-47848f?style=for-the-badge&logo=electron&logoColor=white)

**Industry-grade hand tracking and gesture recognition platform**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api-reference)

</div>

---

## 🌟 Features

### Core Capabilities
- **Real-time Hand Tracking** - MediaPipe-powered hand landmark detection at 30+ FPS
- **Gesture Recognition** - Detect palm open, fist, pinch, and custom gestures
- **Digital Canvas** - Draw, erase, and create with hand gestures
- **WebSocket Streaming** - Low-latency bidirectional communication
- **Multi-page Support** - Create and navigate multiple canvas pages
- **Undo/Redo System** - Full state management with history

### AAA-Grade Frontend
- **Premium UI/UX** - Glassmorphism, vibrant gradients, smooth animations
- **Electron Desktop App** - Native desktop experience
- **Real-time Visualization** - Live camera feed with landmark overlay
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Framer Motion Animations** - Buttery smooth 60 FPS animations

### Backend Excellence
- **FastAPI Framework** - High-performance async Python backend
- **OpenCV Integration** - Advanced image processing
- **MediaPipe Hands** - Google's state-of-the-art hand tracking
- **Modular Architecture** - Clean separation of concerns
- **WebSocket Protocol** - Real-time bidirectional communication

---

## 🏗️ Architecture

### Tech Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Electron Desktop App                                        │
│  ├── React 19 (UI Framework)                                │
│  ├── Framer Motion (Animations)                             │
│  ├── Lucide Icons (Icon System)                             │
│  └── Vite (Build Tool)                                      │
└─────────────────────────────────────────────────────────────┘
                            ↕ WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                             │
│  ├── WebSocket Handler (Real-time Communication)           │
│  ├── State Manager (Canvas & Drawing State)                │
│  ├── Gesture Engine (Gesture Recognition Logic)            │
│  └── Frame Processor (Camera & MediaPipe)                  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  Computer Vision Pipeline                                    │
│  ├── OpenCV (Image Processing)                              │
│  ├── MediaPipe Hands (Hand Tracking)                        │
│  ├── NumPy (Array Operations)                               │
│  └── Base64 Encoding (Image Streaming)                      │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### **Backend Components**

1. **Frame Processor** (`backend/app/core/frame_processor.py`)
   - Captures camera frames via OpenCV
   - Processes frames through MediaPipe Hands
   - Detects hand landmarks and gestures
   - Returns base64-encoded frames + gesture data

2. **State Manager** (`backend/app/core/state.py`)
   - Manages drawing canvas (NumPy arrays)
   - Handles undo/redo stacks
   - Stores tool settings (color, thickness, tool type)
   - Multi-page canvas support

3. **Gesture Engine** (`backend/app/core/gesture_engine.py`)
   - Maps gestures to actions
   - Processes gesture events
   - Triggers state changes

4. **WebSocket Handler** (`backend/app/api/ws.py`)
   - Accepts WebSocket connections
   - Streams frames at 30 FPS
   - Receives commands from frontend
   - Sends state updates

#### **Frontend Components**

1. **App Component** (`frontend-aaa/src/App.jsx`)
   - Main application container
   - WebSocket connection management
   - Real-time state synchronization
   - UI event handling

2. **Design System** (`frontend-aaa/src/index.css`)
   - CSS custom properties (design tokens)
   - Dark theme with vibrant accents
   - Glassmorphism effects
   - Animation utilities

3. **Electron Wrapper** (`frontend-aaa/electron-main.js`)
   - Desktop application shell
   - Window management
   - Native OS integration

---

## 📦 Installation

### Prerequisites

- **Python 3.9+** - Backend runtime
- **Node.js 18+** - Frontend build tools
- **Webcam** - For hand tracking
- **Git** - Version control

### Backend Setup

```bash
# Navigate to project root
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend-aaa

# Install dependencies
npm install

# Install additional dev tools (if needed)
npm install concurrently wait-on electron-builder --save-dev
```

---

## 🚀 Usage

### Running the Application

#### Option 1: Web Browser Mode

**Terminal 1 - Start Backend:**
```bash
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID
.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend-aaa
npm run dev
```

Then open `http://localhost:5173` in your browser.

#### Option 2: Electron Desktop App

**Terminal 1 - Start Backend:**
```bash
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID
.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Electron:**
```bash
cd frontend-aaa
npm run electron:dev
```

### Building for Production

**Backend:**
```bash
# Backend runs as-is, no build needed
# For deployment, use gunicorn or uvicorn with production settings
```

**Frontend:**
```bash
cd frontend-aaa
npm run build
npm run electron:build
```

---

## 🎮 Controls

### UI Controls

| Control | Action |
|---------|--------|
| **Connect Button** | Establish WebSocket connection to backend |
| **Pen Tool** | Switch to drawing mode |
| **Eraser Tool** | Switch to eraser mode |
| **Color Picker** | Select drawing color |
| **Thickness Slider** | Adjust brush thickness (1-20px) |
| **Undo** | Revert last action |
| **Redo** | Restore undone action |
| **New Page** | Create new canvas page |
| **Erase All** | Clear current canvas |
| **Download** | Export canvas as PNG |

### Gesture Controls

| Gesture | Detection | Action |
|---------|-----------|--------|
| **Open Palm** | All fingers extended | Trigger palm-based actions |
| **Fist** | All fingers closed | Stop drawing |
| **Pinch** | Thumb + Index touching | Precision control |
| **Thumb-Pinky** | Thumb + Pinky touching | Special action trigger |

---

## 🔌 API Reference

### WebSocket Endpoint

**URL:** `ws://localhost:8000/ws`

#### Client → Server Messages

**Set Tool:**
```json
{
  "type": "command",
  "action": "set_tool",
  "params": {
    "tool": "pen" | "eraser"
  }
}
```

**Set Color:**
```json
{
  "type": "command",
  "action": "set_color",
  "params": {
    "color": [255, 0, 0]  // RGB array
  }
}
```

**Set Thickness:**
```json
{
  "type": "command",
  "action": "set_thickness",
  "params": {
    "thickness": 5  // 1-20
  }
}
```

**Undo/Redo:**
```json
{
  "type": "command",
  "action": "undo" | "redo"
}
```

**Page Management:**
```json
{
  "type": "command",
  "action": "new_page" | "erase_all"
}
```

#### Server → Client Messages

**Frame Update:**
```json
{
  "type": "frame",
  "image": "base64_encoded_jpeg",
  "landmarks": {
    "thumb_tip": [x, y],
    "index_finger_tip": [x, y],
    // ... other landmarks
  },
  "gestures": ["OPEN_PALM", "PINCH"]
}
```

**State Update:**
```json
{
  "type": "state",
  "tool": "pen",
  "color": [255, 0, 0],
  "thickness": 5,
  "page_index": 0,
  "total_pages": 3,
  "canvas": "base64_encoded_canvas"
}
```

---

## 📁 Project Structure

```
GCID/
├── backend/
│   └── app/
│       ├── api/
│       │   ├── ws.py              # WebSocket handler
│       │   └── health.py          # Health check endpoint
│       ├── core/
│       │   ├── frame_processor.py # Camera & MediaPipe
│       │   ├── gesture_engine.py  # Gesture recognition
│       │   └── state.py           # State management
│       ├── models/                # Data models
│       ├── utils/                 # Utilities
│       ├── config.py              # Configuration
│       └── main.py                # FastAPI app
├── frontend-aaa/
│   ├── src/
│   │   ├── App.jsx               # Main React component
│   │   ├── App.css               # Component styles
│   │   ├── index.css             # Design system
│   │   └── main.jsx              # React entry point
│   ├── electron-main.js          # Electron entry point
│   ├── index.html                # HTML template
│   ├── package.json              # Node dependencies
│   └── vite.config.js            # Vite configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🛠️ Development

### Adding New Gestures

1. **Define gesture detection logic** in `backend/app/core/frame_processor.py`:
```python
@staticmethod
def _is_my_gesture(hand_landmarks) -> bool:
    # Your detection logic here
    return True
```

2. **Add to gesture detection** in `read_frame()` method:
```python
if self._is_my_gesture(hand_landmarks):
    gestures.append("MY_GESTURE")
```

3. **Map gesture to action** in `backend/app/core/gesture_engine.py`:
```python
def process(self, gestures: List[str]):
    if "MY_GESTURE" in gestures:
        # Trigger action
        pass
```

### Customizing UI

- **Colors**: Edit CSS variables in `frontend-aaa/src/index.css`
- **Layout**: Modify `frontend-aaa/src/App.jsx`
- **Animations**: Adjust Framer Motion configs in components

---

## 🎯 Performance Optimization

### Backend
- Frame processing runs at 30 FPS (configurable in `ws.py`)
- MediaPipe confidence thresholds tuned for accuracy/speed balance
- NumPy arrays for efficient canvas operations

### Frontend
- Framer Motion for GPU-accelerated animations
- Canvas rendering optimized with `globalAlpha`
- WebSocket auto-reconnect with exponential backoff

---

## 🔒 Security Considerations

### Production Deployment

1. **CORS**: Update `allow_origins` in `backend/app/main.py` to specific domains
2. **WebSocket**: Add authentication/authorization layer
3. **HTTPS/WSS**: Use secure protocols in production
4. **Rate Limiting**: Implement request throttling
5. **Input Validation**: Validate all client commands

---

## 📊 System Requirements

### Minimum
- **CPU**: Dual-core 2.0 GHz
- **RAM**: 4 GB
- **GPU**: Integrated graphics
- **Camera**: 720p webcam
- **OS**: Windows 10, macOS 10.15, Ubuntu 20.04

### Recommended
- **CPU**: Quad-core 3.0 GHz
- **RAM**: 8 GB
- **GPU**: Dedicated GPU (for better performance)
- **Camera**: 1080p webcam
- **OS**: Windows 11, macOS 12+, Ubuntu 22.04

---

## 🐛 Troubleshooting

### Camera Not Working
```bash
# Check camera permissions
# Windows: Settings > Privacy > Camera
# macOS: System Preferences > Security & Privacy > Camera
```

### WebSocket Connection Failed
```bash
# Ensure backend is running
# Check firewall settings
# Verify WebSocket URL in frontend
```

### MediaPipe Import Error
```bash
# Reinstall MediaPipe
pip uninstall mediapipe
pip install mediapipe
```

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👥 Contributors

- **Dhananjay Sai Kumar K** - Lead Developer

---

## 🙏 Acknowledgments

- **MediaPipe** - Google's hand tracking solution
- **FastAPI** - Modern Python web framework
- **React** - UI library
- **Electron** - Desktop app framework
- **Framer Motion** - Animation library

---

<div align="center">

**Built with ❤️ using AAA-grade technologies**

[⬆ Back to Top](#-gesture-craft---aaa-grade-hand-tracking-studio)

</div>

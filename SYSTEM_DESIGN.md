# Gesture Craft - System Design Document
## AAA-Grade Hand Tracking Studio

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Component Design](#component-design)
5. [Data Flow](#data-flow)
6. [Communication Protocol](#communication-protocol)
7. [State Management](#state-management)
8. [Performance Optimization](#performance-optimization)
9. [Security Considerations](#security-considerations)
10. [Scalability](#scalability)

---

## Executive Summary

**Gesture Craft** is an industry-grade hand tracking and gesture recognition platform built using the **AAA Stack** (Python Backend + Web Frontend + Electron/Tauri wrapper). The system provides real-time hand tracking, gesture recognition, and a digital canvas interface for creating drawings using hand gestures.

### Key Objectives
- **Real-time Performance**: 30+ FPS hand tracking with <50ms latency
- **AAA-Grade UX**: Premium UI with glassmorphism, animations, and responsive design
- **Modular Architecture**: Clean separation of concerns for maintainability
- **Cross-Platform**: Desktop app via Electron, web app via browser

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Electron Desktop App                       │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │         React Application (Vite)                 │  │    │
│  │  │  • UI Components (Framer Motion)                │  │    │
│  │  │  • WebSocket Client                             │  │    │
│  │  │  • Canvas Renderer                              │  │    │
│  │  │  • State Management (React Hooks)              │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↕ WebSocket (ws://)
┌─────────────────────────────────────────────────────────────────┐
│                        SERVER LAYER                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              FastAPI Application                        │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  WebSocket Handler                               │  │    │
│  │  │  • Connection Management                         │  │    │
│  │  │  • Message Routing                               │  │    │
│  │  │  • Frame Streaming (30 FPS)                      │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  Core Engine                                     │  │    │
│  │  │  • Frame Processor (MediaPipe + OpenCV)         │  │    │
│  │  │  • Gesture Engine (Pattern Recognition)         │  │    │
│  │  │  • State Manager (Canvas + History)             │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                     PROCESSING LAYER                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Computer Vision Pipeline                              │    │
│  │  • Camera Capture (OpenCV VideoCapture)               │    │
│  │  • Hand Detection (MediaPipe Hands)                   │    │
│  │  • Landmark Extraction (21 points per hand)           │    │
│  │  • Gesture Classification (Heuristic Rules)           │    │
│  │  • Image Encoding (Base64 JPEG)                       │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Patterns

1. **Client-Server Pattern**: Clear separation between frontend (React) and backend (FastAPI)
2. **Event-Driven Architecture**: WebSocket-based real-time communication
3. **Pipeline Pattern**: Frame processing through sequential stages
4. **State Machine**: Gesture recognition and canvas state management
5. **Observer Pattern**: Frontend subscribes to backend state changes

---

## Technology Stack

### Backend Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI | High-performance async web framework |
| **Vision** | MediaPipe Hands | Hand landmark detection |
| **Image Processing** | OpenCV | Camera capture, image manipulation |
| **Numerical** | NumPy | Array operations, canvas storage |
| **Protocol** | WebSocket | Real-time bidirectional communication |
| **Encoding** | Base64 | Image serialization for transmission |

### Frontend Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI Framework** | React 19 | Component-based UI |
| **Build Tool** | Vite | Fast development server, optimized builds |
| **Desktop Wrapper** | Electron | Native desktop application |
| **Animations** | Framer Motion | Smooth, GPU-accelerated animations |
| **Icons** | Lucide React | Modern icon system |
| **Styling** | CSS3 + Custom Properties | Design system, glassmorphism |

### Development Tools

- **Python 3.9+**: Backend runtime
- **Node.js 18+**: Frontend build tools
- **Git**: Version control
- **npm**: Package management

---

## Component Design

### Backend Components

#### 1. Frame Processor (`backend/app/core/frame_processor.py`)

**Responsibilities:**
- Capture frames from webcam via OpenCV
- Process frames through MediaPipe Hands
- Extract hand landmarks (21 points per hand)
- Detect gestures using heuristic rules
- Encode frames as base64 JPEG

**Key Methods:**
```python
class FrameProcessor:
    def __init__(self, camera_index: int = 0)
    def read_frame() -> Tuple[str, Dict, List[str]]
    def _is_palm_open(hand_landmarks) -> bool
    def _is_fist(hand_landmarks) -> bool
    def _is_pinch(hand_landmarks) -> bool
    def _thumb_pinky_touch(hand_landmarks) -> bool
    def release()
```

**Gesture Detection Logic:**
- **Open Palm**: All fingertips above their respective PIP joints
- **Fist**: All fingertips below their respective PIP joints
- **Pinch**: Thumb tip and index finger tip distance < 0.06
- **Thumb-Pinky Touch**: Thumb tip and pinky tip distance < 0.08

#### 2. State Manager (`backend/app/core/state.py`)

**Responsibilities:**
- Manage canvas pages (NumPy arrays, 550x850x3 BGR)
- Handle undo/redo stacks
- Store drawing tool settings (color, thickness, tool type)
- Serialize state for transmission

**Key Methods:**
```python
class State:
    def __init__()
    def save_state()  # Save to undo stack
    def undo()
    def redo()
    def add_new_page()
    def switch_page(direction: str)
    def erase_all()
    def set_tool(tool: str)
    def set_color(color: Tuple[int, int, int])
    def set_thickness(value: int)
    def cycle_color()
    def serialize() -> Dict[str, Any]
```

**State Structure:**
```python
{
    "tool": "pen" | "eraser",
    "color": (R, G, B),  # 0-255
    "thickness": 1-20,
    "pages": [np.ndarray, ...],  # List of canvas pages
    "current_page_index": 0,
    "undo_stack": [np.ndarray, ...],
    "redo_stack": [np.ndarray, ...]
}
```

#### 3. Gesture Engine (`backend/app/core/gesture_engine.py`)

**Responsibilities:**
- Map gestures to actions
- Process gesture events
- Trigger state changes

**Key Methods:**
```python
class GestureEngine:
    def __init__(self, state: State)
    def process(self, gestures: List[str])
```

#### 4. WebSocket Handler (`backend/app/api/ws.py`)

**Responsibilities:**
- Accept WebSocket connections
- Stream frames at 30 FPS
- Receive commands from frontend
- Send state updates

**Key Functions:**
```python
async def websocket_endpoint(ws: WebSocket)
async def _receive_commands(ws: WebSocket, state: State)
```

**Message Flow:**
1. Client connects to `/ws`
2. Server creates `State`, `GestureEngine`, `FrameProcessor`
3. Server starts frame streaming loop (30 FPS)
4. Server starts command receiver task
5. Client sends commands, server updates state
6. Server sends frame + state updates to client

### Frontend Components

#### 1. App Component (`frontend-aaa/src/App.jsx`)

**Responsibilities:**
- WebSocket connection management
- Real-time state synchronization
- UI event handling
- Canvas rendering

**Key State:**
```javascript
{
  wsUrl: string,
  isConnected: boolean,
  status: string,
  gestures: string[],
  tool: string,
  pageInfo: { current: number, total: number },
  fps: number,
  color: string,
  thickness: number
}
```

**Key Methods:**
```javascript
connect()
handleMessage(msg)
drawLandmarks(landmarks)
drawCanvas(base64Canvas)
sendCommand(action, params)
downloadCanvas()
```

#### 2. Design System (`frontend-aaa/src/index.css`)

**CSS Custom Properties:**
- **Colors**: Dark theme with vibrant accents
- **Spacing**: 8-point grid system
- **Typography**: Inter (sans), JetBrains Mono (mono)
- **Shadows**: Layered elevation system
- **Animations**: Fade, slide, pulse, spin

**Utility Classes:**
- `.gradient-text`: Gradient text effect
- `.glass-effect`: Glassmorphism background
- `.glow-effect`: Glowing box shadow
- `.animate-*`: Animation utilities

#### 3. Electron Wrapper (`frontend-aaa/electron-main.js`)

**Responsibilities:**
- Create native window
- Load React app (dev or production)
- Handle window lifecycle

---

## Data Flow

### Frame Streaming Flow

```
┌─────────────┐
│   Camera    │
└──────┬──────┘
       │ Raw frame (BGR)
       ▼
┌─────────────────┐
│ OpenCV Capture  │
└──────┬──────────┘
       │ Flipped frame
       ▼
┌─────────────────┐
│ MediaPipe Hands │
└──────┬──────────┘
       │ Hand landmarks (21 points)
       ▼
┌─────────────────┐
│ Gesture Engine  │
└──────┬──────────┘
       │ Detected gestures
       ▼
┌─────────────────┐
│ Base64 Encoder  │
└──────┬──────────┘
       │ Encoded JPEG
       ▼
┌─────────────────┐
│ WebSocket Send  │
└──────┬──────────┘
       │ JSON message
       ▼
┌─────────────────┐
│ React Frontend  │
└──────┬──────────┘
       │ Display frame
       ▼
┌─────────────────┐
│ Canvas Render   │
└─────────────────┘
```

### Command Flow

```
┌─────────────────┐
│ User Interaction│
│ (Button Click)  │
└──────┬──────────┘
       │ UI event
       ▼
┌─────────────────┐
│ sendCommand()   │
└──────┬──────────┘
       │ JSON command
       ▼
┌─────────────────┐
│ WebSocket Send  │
└──────┬──────────┘
       │ ws.send()
       ▼
┌─────────────────┐
│ Backend Handler │
└──────┬──────────┘
       │ Parse command
       ▼
┌─────────────────┐
│ State Manager   │
└──────┬──────────┘
       │ Update state
       ▼
┌─────────────────┐
│ State Serialize │
└──────┬──────────┘
       │ JSON state
       ▼
┌─────────────────┐
│ WebSocket Send  │
└──────┬──────────┘
       │ State update
       ▼
┌─────────────────┐
│ React Frontend  │
└──────┬──────────┘
       │ Update UI
       ▼
┌─────────────────┐
│ Re-render       │
└─────────────────┘
```

---

## Communication Protocol

### WebSocket Protocol

**Endpoint:** `ws://localhost:8000/ws`

**Connection Lifecycle:**
1. Client initiates WebSocket connection
2. Server accepts connection
3. Server creates isolated state for this connection
4. Server starts frame streaming (30 FPS)
5. Server starts command receiver task
6. Client sends commands, server responds with state updates
7. On disconnect, server cleans up resources

### Message Types

#### Client → Server

**Command Message:**
```json
{
  "type": "command",
  "action": "set_tool" | "set_color" | "set_thickness" | "undo" | "redo" | "new_page" | "erase_all",
  "params": {
    // Action-specific parameters
  }
}
```

#### Server → Client

**Frame Message:**
```json
{
  "type": "frame",
  "image": "base64_encoded_jpeg",
  "landmarks": {
    "thumb_tip": [x, y],
    "index_finger_tip": [x, y],
    "middle_finger_tip": [x, y],
    "ring_finger_tip": [x, y],
    "pinky_tip": [x, y]
  },
  "gestures": ["OPEN_PALM", "PINCH"]
}
```

**State Message:**
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

## State Management

### Backend State

**Scope:** Per WebSocket connection

**Storage:**
- Canvas pages: NumPy arrays (550x850x3 BGR)
- Undo/redo stacks: Lists of NumPy arrays
- Tool settings: In-memory variables

**Persistence:** None (ephemeral, per-session)

### Frontend State

**Scope:** React component state (hooks)

**Storage:**
- Connection state: `useState`
- UI state: `useState`
- Refs: `useRef` for canvas, image, WebSocket

**Synchronization:** Server is source of truth, frontend mirrors state

---

## Performance Optimization

### Backend Optimizations

1. **Frame Rate Limiting**: 30 FPS cap to balance performance and responsiveness
2. **MediaPipe Confidence Thresholds**: Tuned for accuracy/speed balance
3. **NumPy Operations**: Efficient array operations for canvas
4. **Async I/O**: FastAPI async handlers for non-blocking operations
5. **Base64 Encoding**: JPEG compression for smaller payloads

### Frontend Optimizations

1. **Framer Motion**: GPU-accelerated animations
2. **Canvas Rendering**: `globalAlpha` for efficient overlay
3. **WebSocket Auto-Reconnect**: Exponential backoff
4. **React Hooks**: `useCallback` to prevent unnecessary re-renders
5. **Lazy Loading**: Components loaded on demand

---

## Security Considerations

### Current Implementation (Development)

- **CORS**: Allow all origins (`allow_origins=["*"]`)
- **WebSocket**: No authentication
- **Input Validation**: Minimal

### Production Recommendations

1. **CORS**: Restrict to specific domains
2. **Authentication**: JWT tokens for WebSocket connections
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Validate all client commands
5. **HTTPS/WSS**: Secure protocols
6. **Content Security Policy**: Prevent XSS attacks

---

## Scalability

### Current Limitations

- **Single Connection**: One camera per WebSocket connection
- **In-Memory State**: No persistence
- **Single Server**: No load balancing

### Scaling Strategies

1. **Horizontal Scaling**: Load balancer + multiple backend instances
2. **State Persistence**: Redis for shared state
3. **Message Queue**: RabbitMQ/Kafka for async processing
4. **CDN**: Serve static assets from CDN
5. **Database**: Store canvas history, user sessions

---

## Conclusion

Gesture Craft demonstrates the **AAA Stack** approach to building industry-grade applications. The architecture prioritizes:

- **Performance**: 30+ FPS real-time hand tracking
- **User Experience**: Premium UI with smooth animations
- **Maintainability**: Clean, modular codebase
- **Scalability**: Foundation for future enhancements

This design document serves as a blueprint for understanding, extending, and deploying the Gesture Craft platform.

---

**Document Version:** 1.0  
**Last Updated:** February 5, 2026  
**Author:** Dhananjay Sai Kumar K

# GestureCraft – Architecture & System Design

## 1. System Philosophy

GestureCraft is structured around **tools, commands, and intent**, not modes and hacks.

Every action must be:
- Explicit
- Reversible
- Predictable

---

## 2. High-Level Architecture

### Core Layers

1. Input Layer
   - MediaPipe hand landmarks
   - Raw hand positions

2. Gesture Interpreter
   - Converts raw landmarks into intent events
   - Examples:
     - PINCH_START
     - PINCH_HOLD
     - PINCH_END
     - PALM_OPEN

3. Tool System
   - Exactly one active tool
   - Tools respond to gesture events

4. Command System
   - Each action is a command
   - Commands are undoable and replayable

5. Renderer
   - Replays commands to produce canvas
   - Handles previews and overlays

---

## 3. Tool Interface (Conceptual)

Each tool must implement:

- on_start(x, y)
- on_update(x, y)
- on_end(x, y)
- draw_preview(canvas)

Tools must NOT:
- Modify global state directly
- Interfere with other tools

---

## 4. Undo System

- Command-based undo (no image snapshots)
- Canvas is derived from command history
- Undo/redo never mutate commands

---

## 5. Smoothness System

### Cursor
- Light smoothing
- Low latency

### Stroke
- Speed-adaptive smoothing
- Higher clarity

Smoothness must be computed dynamically based on movement speed.

---

## 6. Rendering Rules

- White background
- High-contrast strokes
- Minimal UI overlays
- Presenter-friendly visuals

---

## 7. Explicitly Disallowed Patterns

- Global state mutations without commands
- time.sleep() in interaction logic
- Frame-dependent gesture hacks
- Automatic corrections without confirmation

---

## 8. Agent Responsibilities

Any agent interacting with this codebase must:
- Respect the PRD
- Avoid adding features that increase cognitive load
- Preserve teaching flow above all else
- Prefer deletion over addition

---

## 9. Evolution Strategy

New features must pass:
1. Does it interrupt speaking?
2. Can it fail silently?
3. Does it surprise the user?

If YES to any → reject.

<!-- Control-layer stabilization milestone -->

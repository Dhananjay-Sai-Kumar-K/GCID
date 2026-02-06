# GestureCraft – Product Requirements Document (PRD)

## 1. Product Overview

GestureCraft is an intelligent, gesture-driven whiteboard designed for **live teaching, explanation, and classroom demonstrations**.

It enables presenters to explain ideas visually **without breaking cognitive or speaking flow**, using natural hand movements instead of a mouse, pen, or complex UI.

GestureCraft prioritizes:
- Smoothness
- Predictability
- Visual clarity for viewers
- User confidence during live explanation

This is NOT an art tool, design tool, or general-purpose drawing application.

---

## 2. Target Users

### Primary User
- Teachers
- Tutors
- Students explaining concepts
- Presenters / demonstrators

### Environment
- Classroom projector
- Online teaching (Zoom / Meet)
- Live demos or explanations
- Audience is watching while the user speaks

---

## 3. Core User Goal

> “I want to explain an idea visually, in real time, without stopping to think about tools.”

---

## 4. Non-Goals (Explicit Exclusions)

GestureCraft will NOT attempt to:
- Compete with professional drawing tools
- Provide artistic brushes or effects
- Support complex gesture grammars
- Perform automatic corrections without confirmation
- Provide infinite feature customization during live use

---

## 5. Core Design Principles (Non-Negotiable)

1. **Speech First**  
   Drawing must never interrupt speaking.

2. **No Surprises**  
   The system must never act without explicit user intent.

3. **Forgiving Interaction**  
   Errors must be easy to undo and never destructive.

4. **Low Cognitive Load**  
   Users should not think about modes, settings, or gestures.

5. **Viewer Clarity > User Control**  
   Clean, readable diagrams matter more than precision.

---

## 6. Canvas Rules

- Default background is **white**.
- No dynamic or accidental background changes.
- Canvas appearance must be projector-friendly.
- High contrast strokes only.

---

## 7. Interaction Model

### Tools (Only One Active at a Time)
- Pen Tool
- Eraser Tool
- Shape Tool
- Pointer Tool

There must never be overlapping tool behaviors.

---

## 8. Gesture Philosophy

- Minimal gestures
- Context-aware interpretation
- No gesture overload
- No gesture that causes destructive actions without confirmation

---

## 9. Smoothness & Input Behavior

- Cursor smoothing: light, responsive
- Stroke smoothing: stronger, clarity-focused
- Smoothness must be **speed-adaptive**
- No static smoothing parameters exposed during live teaching

---

## 10. Undo / Redo

- Undo must be instant
- Undo must be unlimited (within session)
- Undo must never lag or fail
- Undo restores user confidence

---

## 11. Shape Handling

- Live preview before committing shapes
- Shape refinement is **suggestive only**
- No automatic replacement without confirmation

---

## 12. Success Criteria

GestureCraft is successful if:
- A teacher can explain continuously for 10+ minutes
- No accidental erasing occurs
- Undo is trusted
- The user never stops speaking due to the tool
- Viewers can clearly understand diagrams

---

## 13. Failure Conditions

GestureCraft fails if:
- The user must “think about gestures”
- Actions feel unpredictable
- Corrections happen without permission
- Latency breaks flow

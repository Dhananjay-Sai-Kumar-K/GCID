
from abc import ABC, abstractmethod
import cv2
import numpy as np
from gesture_interpreter import GestureType, GestureState
from smoother import SpeedAdaptiveSmoother


# --- Commands ---

class Command(ABC):
    @abstractmethod
    def execute(self, state):
        pass

class DrawStrokeCommand(Command):
    def __init__(self, start_point, end_point, color, thickness):
        self.start = start_point
        self.end = end_point
        self.color = color
        self.thickness = thickness

    def execute(self, state):
        steps = 20
        
        if self.start:
            for i in range(steps):
                x = int(self.start[0] + (self.end[0] - self.start[0]) * i / steps)
                y = int(self.start[1] + (self.end[1] - self.start[1]) * i / steps)
                cv2.circle(state.canvas, (x, y), self.thickness, self.color, -1)
            
        state.pages[state.current_page_index] = state.canvas.copy()

class EraseCommand(Command):
    def __init__(self, center, radius=30):
        self.center = center
        self.radius = radius

    def execute(self, state):
        cv2.circle(state.canvas, self.center, self.radius, (255, 255, 255), -1)
        state.pages[state.current_page_index] = state.canvas.copy()

class DrawShapeCommand(Command):
    def __init__(self, shape_type, start_point, end_point, color, thickness):
        self.shape_type = shape_type
        self.start_point = start_point
        self.end_point = end_point
        self.color = color
        self.thickness = thickness

    def execute(self, state):
        canvas = state.pages[state.current_page_index]
        
        if self.shape_type == "Circle":
            radius = int(np.sqrt((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2))
            cv2.circle(canvas, self.start_point, radius, self.color, self.thickness)
        
        elif self.shape_type == "Oval":
            width = abs(self.end_point[0] - self.start_point[0])
            height = abs(self.end_point[1] - self.start_point[1])
            center = (min(self.start_point[0], self.end_point[0]) + width//2, 
                      min(self.start_point[1], self.end_point[1]) + height//2)
            axes = (max(width//2, 1), max(height//2, 1))
            cv2.ellipse(canvas, center, axes, 0, 0, 360, self.color, self.thickness)
        
        elif self.shape_type == "Square":
            side = max(abs(self.end_point[0] - self.start_point[0]), abs(self.end_point[1] - self.start_point[1]))
            x_direction = 1 if self.end_point[0] >= self.start_point[0] else -1
            y_direction = 1 if self.end_point[1] >= self.start_point[1] else -1
            end_x = self.start_point[0] + (side * x_direction)
            end_y = self.start_point[1] + (side * y_direction)
            cv2.rectangle(canvas, self.start_point, (end_x, end_y), self.color, self.thickness)
        
        elif self.shape_type == "Triangle":
            x1, y1 = self.start_point
            x2, y2 = self.end_point
            x3 = (x1 + x2) // 2
            y3 = y1
            pts = np.array([[x3, y3], [x1, y2], [x2, y2]], np.int32)
            cv2.polylines(canvas, [pts], isClosed=True, color=self.color, thickness=self.thickness)

        state.canvas = canvas.copy()


# --- Tools ---
# FIX 2: Tools react ONLY to GestureEvents, never inspect raw landmarks

class Tool(ABC):
    @abstractmethod
    def on_event(self, event, x, y, state):
        """Handle gesture event. Returns True if event was consumed."""
        pass
    
    @abstractmethod
    def draw_overlay(self, canvas, x, y, state):
        """Draw tool-specific overlays (cursors, previews)."""
        pass


class PenTool(Tool):
    """
    FIX 2 & 5: Drawing ONLY happens with explicit PINCH intent.
    - PINCH_START -> begin stroke, save undo state
    - PINCH_HOLD -> append points (fires every frame)
    - PINCH_END -> commit stroke, clear last_point
    
    Does NOT:
    - Inspect raw landmarks
    - Re-check finger counts
    - Cancel drawing based on pose
    """
    def __init__(self):
        # Dedicated stroke smoother: Very smooth at low speed, responsive at high speed
        self.stroke_smoother = SpeedAdaptiveSmoother(min_alpha=0.1, max_alpha=0.8, min_speed=50.0, max_speed=2000.0)

    def on_event(self, event, x, y, state):
        # FIX 2: Only react to PINCH gestures for drawing
        if event.type == GestureType.PINCH:
            # Re-calculate raw screen coordinates from normalized event
            h, w = state.canvas.shape[:2]
            raw_x = int(event.x * w)
            raw_y = int(event.y * h)
            
            if event.state == GestureState.START:
                # Start of stroke - Reset smoother and Save Undo
                state.save_state()
                sx, sy = self.stroke_smoother.reset(raw_x, raw_y)
                state.last_point = (sx, sy)
                
            elif event.state == GestureState.HOLD:
                # Continuous drawing - fires EVERY frame while pinched
                sx, sy = self.stroke_smoother.update(raw_x, raw_y)
                
                if state.last_point:
                    cmd = DrawStrokeCommand(state.last_point, (sx, sy), state.get_current_color(), state.default_thickness)
                    cmd.execute(state)
                    state.last_point = (sx, sy)
                else:
                    state.last_point = (sx, sy)
                    
            elif event.state == GestureState.END:
                # Stroke completed - clear state
                state.last_point = None
        else:
            # Non-pinch gesture (POINTING, OPEN_PALM, etc.) - just clear last_point
            # FIX 5: OPEN_PALM pauses drawing but doesn't cancel intent
            if event.state == GestureState.START:
                state.last_point = None

    def draw_overlay(self, canvas, x, y, state):
        # Draw Pen Cursor - color indicates current drawing color
        color = state.get_current_color()
        cv2.circle(canvas, (x, y), 5, color, -1)
        cv2.circle(canvas, (x, y), state.default_thickness // 2 + 2, color, 1)


class EraserTool(Tool):
    """
    FIX 3: Eraser is ONLY activated via explicit UI selection.
    OPEN_PALM does NOT activate eraser.
    """
    def on_event(self, event, x, y, state):
        # Only erase on explicit PINCH gesture
        if event.type == GestureType.PINCH:
             if event.state == GestureState.START:
                 state.save_state()
                 
             if event.state == GestureState.START or event.state == GestureState.HOLD:
                 cmd = EraseCommand((x, y), radius=30)
                 cmd.execute(state)

    def draw_overlay(self, canvas, x, y, state):
        cv2.circle(canvas, (x, y), 30, (0, 0, 0), 2)
        cv2.putText(canvas, "Eraser", (x + 35, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)


class ShapeTool(Tool):
    """
    FIX 2: Shape tool contract enforcement.
    - PINCH_START -> set anchor, save undo
    - PINCH_HOLD -> update preview (via draw_overlay using current x,y)
    - PINCH_END -> commit shape
    
    Does NOT react to POINTING or OPEN_PALM for shape commit.
    """
    def __init__(self, shape_type):
        self.shape_type = shape_type
        self.start_point = None
        self.current_end_point = None  # Track end point for commit

    def on_event(self, event, x, y, state):
        if event.type == GestureType.PINCH:
            if event.state == GestureState.START:
                # Begin shape - set anchor
                state.save_state()
                self.start_point = (x, y)
                self.current_end_point = (x, y)
                
            elif event.state == GestureState.HOLD:
                # Update preview position (draw_overlay will use this)
                self.current_end_point = (x, y)
                
            elif event.state == GestureState.END:
                # FIX 2: Commit shape on PINCH_END
                if self.start_point:
                    cmd = DrawShapeCommand(self.shape_type, self.start_point, 
                                          self.current_end_point, 
                                          state.get_current_color(), 
                                          state.default_thickness)
                    cmd.execute(state)
                    self.start_point = None
                    self.current_end_point = None
        
        # Non-pinch gestures: don't commit, just clear if needed
        # FIX 5: OPEN_PALM pauses but doesn't cancel shape in progress

    def draw_overlay(self, canvas, x, y, state):
        if self.start_point:
            # Live Shape Preview using current cursor position
            color = (128, 128, 128)  # Gray preview
            thickness = 2
            line_type = cv2.LINE_4
            
            sp = self.start_point
            ep = (x, y)
            
            if self.shape_type == "Circle":
                radius = int(np.sqrt((ep[0] - sp[0])**2 + (ep[1] - sp[1])**2))
                if radius > 0:
                    cv2.circle(canvas, sp, radius, color, thickness, line_type)
                
            elif self.shape_type == "Oval":
                width = abs(ep[0] - sp[0])
                height = abs(ep[1] - sp[1])
                center = (min(sp[0], ep[0]) + width//2, 
                          min(sp[1], ep[1]) + height//2)
                axes = (max(width//2, 1), max(height//2, 1))
                cv2.ellipse(canvas, center, axes, 0, 0, 360, color, thickness, line_type)
                
            elif self.shape_type == "Square":
                side = max(abs(ep[0] - sp[0]), abs(ep[1] - sp[1]))
                x_direction = 1 if ep[0] >= sp[0] else -1
                y_direction = 1 if ep[1] >= sp[1] else -1
                end_x = sp[0] + (side * x_direction)
                end_y = sp[1] + (side * y_direction)
                cv2.rectangle(canvas, sp, (end_x, end_y), color, thickness, line_type)
                
            elif self.shape_type == "Triangle":
                x1, y1 = sp
                x2, y2 = ep
                x3 = (x1 + x2) // 2
                y3 = y1
                pts = np.array([[x3, y3], [x1, y2], [x2, y2]], np.int32)
                cv2.polylines(canvas, [pts], isClosed=True, color=color, thickness=thickness, lineType=line_type)

            # Draw start anchor for clarity
            cv2.circle(canvas, sp, 3, (0, 0, 255), -1)
                 
        else:
            # Cursor indicating shape mode when not drawing
            cv2.putText(canvas, self.shape_type, (x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
            cv2.circle(canvas, (x, y), 5, (0, 0, 255), -1)


class PointerTool(Tool):
    """Default tool for cursor movement and selection."""
    def on_event(self, event, x, y, state):
        # Handle Freedom Selection (Select & Move)
        if state.selecting:
            if event.type == GestureType.PINCH and event.state == GestureState.START:
                state.update_selection(x, y)
        
        if state.selected_region is not None:
             if event.type == GestureType.PINCH:
                if event.state == GestureState.START:
                     state.drag_start_pos = (x, y)
                     state.original_selection_pos = state.selection_start
                     state.save_state()
                elif event.state == GestureState.HOLD and state.drag_start_pos:
                     state.update_selection_position(x, y)
                elif event.state == GestureState.END:
                     state.drag_start_pos = None
                     state.last_drag_pos = None

    def draw_overlay(self, canvas, x, y, state):
        # Draw default cursor (Blue dot for visibility - FIX 6)
        cv2.circle(canvas, (x, y), 5, (255, 0, 0), -1)
        
        if state.selecting:
             cv2.putText(canvas, "Selecting...", (x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,100,0), 1)
             if len(state.current_selection) > 0:
                 # Draw polygon in progress
                 pts = np.array(state.current_selection + [(x, y)], np.int32)
                 pts = pts.reshape((-1, 1, 2))
                 cv2.polylines(canvas, [pts], isClosed=False, color=(0, 255, 255), thickness=1)

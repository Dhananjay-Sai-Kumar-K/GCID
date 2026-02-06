import cv2
import mediapipe as mp
import numpy as np
import time
from tkinter import Tk, messagebox
from gesture_interpreter import GestureInterpreter, GestureType, GestureState, HandLandmark
from tools import PenTool, EraserTool, ShapeTool, PointerTool


from smoother import SpeedAdaptiveSmoother


class State:
    def __init__(self):
        self.drawing_mode_active = False
        self.eraser_mode_active = False
        self.pause_drawing = False
        self.last_point = None
        self.canvas = np.ones((550, 850, 3), dtype=np.uint8) * 255  # White canvas
        self.fist_start_time = None
        self.palm_open_start_time = None
        self.fist_detection_duration = 1.5
        self.palm_open_detection_duration = 1.0
        self.control_panel_exists = False
        self.control_panel_exists = False
        # Cursor Smoother: High responsiveness (0.6 - 0.9) to feel "fast" but stable enough for UI clicks
        self.smoother = SpeedAdaptiveSmoother(min_alpha=0.6, max_alpha=0.9, min_speed=50.0, max_speed=1000.0)

        self.pages = [np.ones((550, 850, 3), dtype=np.uint8) * 255]  # List of pages
        self.current_page_index = 0
        self.undo_stack = []
        self.redo_stack = []
        self.shape_mode_active = False
        self.selected_shape = None
        self.shape_start_point = None
        self.default_color = (0, 255, 0)  # Default drawing color (BGR format)
        self.default_thickness = 5
        self.smoothing_factor = 0.5
        
        # VIBGYOR Color cycling
        self.total_pages = 1
        self.vibgyor_colors = [
            (148, 0, 211),    # Violet
            (75, 0, 130),     # Indigo
            (255, 0, 0),      # Blue
            (0, 255, 0),      # Green
            (0, 255, 255),    # Yellow
            (0, 165, 255),    # Orange
            (0, 0, 255)       # Red
        ]
        self.color_names = ["Violet", "Indigo", "Blue", "Green", "Yellow", "Orange", "Red"]
        self.current_color_index = 0
        self.color_change_start_time = None
        self.color_change_duration = 0.5
        self.using_vibgyor = False

        # Control Panel Attributes
        self.background_r = 255  # Background color (Red component)
        self.background_g = 255  # Background color (Green component)
        self.background_b = 255  # Background color (Blue component)
        self.control_panel_visible = False  # Control panel visibility
        self.selecting = False
        self.selection_start = None
        self.selection_mask = None
        self.selected_region = None
        self.current_selection = []
        self.drag_start_pos = None
        self.drag_start_pos = None
        self.original_selection_pos = None
        
        # Gesture Engine
        # Gesture Engine
        self.gesture_interpreter = GestureInterpreter()
        
        # Tools
        self.active_tool = PointerTool()
        self.intent_owner = None # None, "UI", "TOOL"
        self.shape_palette_open = False
        
    def set_tool(self, tool):
        self.active_tool = tool
        # Auto-configure flags for legacy compatibility (if needed by UI drawing helpers)
        if isinstance(tool, PenTool):
             self.drawing_mode_active = True
             self.eraser_mode_active = False
             self.shape_mode_active = False
        elif isinstance(tool, EraserTool):
             self.drawing_mode_active = False
             self.eraser_mode_active = True
             self.shape_mode_active = False
        elif isinstance(tool, ShapeTool):
             self.drawing_mode_active = False
             self.eraser_mode_active = False
             self.shape_mode_active = True
             self.selected_shape = tool.shape_type
        else:
             self.drawing_mode_active = False
             self.eraser_mode_active = False
             self.shape_mode_active = False

    def get_composite_image(self):
        """Return the current page's canvas."""
        return self.pages[self.current_page_index].copy()

    def get_current_color(self):
        """Return the current drawing color."""
        return self.vibgyor_colors[self.current_color_index] if self.using_vibgyor else self.default_color

    def add_new_page(self):
        """Add a new page to the canvas."""
        self.pages.append(np.ones((550, 850, 3), dtype=np.uint8) * 255)
        self.current_page_index = len(self.pages) - 1
        self.total_pages = len(self.pages)
        self.canvas = self.pages[self.current_page_index]

    def save_state(self):
        """Save the current state before modifying."""
        self.undo_stack.append(self.canvas.copy())
        self.redo_stack.clear()  # Clear redo history on new change

    def undo(self):
        """Undo the last action."""
        if self.undo_stack:
            self.redo_stack.append(self.canvas.copy())
            self.canvas = self.undo_stack.pop()
            self.pages[self.current_page_index] = self.canvas

    def redo(self):
        """Redo the last undone action."""
        if self.redo_stack:
            self.undo_stack.append(self.canvas.copy())
            self.canvas = self.redo_stack.pop()
            self.pages[self.current_page_index] = self.canvas

    def switch_page(self, direction):
        """Switch to the next or previous page."""
        if direction == "next":
            if self.current_page_index < len(self.pages) - 1:
                self.current_page_index += 1
        elif direction == "prev":
            if self.current_page_index > 0:
                self.current_page_index -= 1
        self.canvas = self.pages[self.current_page_index]

    def get_current_color_name(self):
        """Return the name of the current color."""
        return self.color_names[self.current_color_index] if self.using_vibgyor else f"Custom: BGR{self.default_color}"

    def update_canvas_background(self):
        """Update the canvas background color based on the current background_r, background_g, background_b values."""
        for page in self.pages:
            page[:] = (self.background_b, self.background_g, self.background_r)

    def start_selection(self, x, y):
        """Start a new selection at the given coordinates."""
        self.selecting = True
        self.selection_start = (x, y)
        self.selection_mask = np.zeros_like(self.canvas[:, :, 0], dtype=np.uint8)
        self.current_selection = []
        self.save_state()  # Save state before selection

    def update_selection(self, x, y):
        """Update the current selection with a new point."""
        if self.selection_start is None:
            self.selection_start = (x, y)
        self.current_selection.append((x, y))
        if len(self.current_selection) > 1:
            pts = np.array(self.current_selection, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(self.selection_mask, [pts], 255)

    def complete_selection(self):
        """Complete the selection and extract the selected region."""
        if len(self.current_selection) > 2:
            pts = np.array(self.current_selection, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(self.selection_mask, [pts], 255)
            self.selected_region = self.canvas.copy()
            self.selected_region[self.selection_mask == 0] = 0
            self.current_selection = []
            self.save_state()  # Save state after selection
        else:
            self.cancel_selection()

    def cancel_selection(self):
        """Cancel the current selection."""
        self.selecting = False
        self.selection_start = None
        self.selection_mask = None
        self.current_selection = []
        self.selected_region = None

    def move_selection(self, hand_landmarks, canvas_width, canvas_height):
        if self.selected_region is None or self.selection_mask is None:
            return

        # Get thumb and index finger positions
        thumb_tip = hand_landmarks.landmark[HandLandmark.THUMB_TIP.value]
        index_tip = hand_landmarks.landmark[HandLandmark.INDEX_FINGER_TIP.value]
        
        thumb_x = int(thumb_tip.x * canvas_width)
        thumb_y = int(thumb_tip.y * canvas_height)
        index_x = int(index_tip.x * canvas_width)
        index_y = int(index_tip.y * canvas_height)
        
        # Calculate distance between thumb and index finger
        distance = np.sqrt((thumb_x - index_x)**2 + (thumb_y - index_y)**2)
        
        if distance < 30:  # Select gesture detected
            # Use midpoint between thumb and index as control point
            control_x = (thumb_x + index_x) // 2
            control_y = (thumb_y + index_y) // 2
            
            if not hasattr(self, 'drag_start_pos'):
                self.drag_start_pos = (control_x, control_y)
                self.original_selection_pos = self.selection_start
                self.save_state()
            
            # Calculate movement offset
            offset_x = control_x - self.drag_start_pos[0]
            offset_y = control_y - self.drag_start_pos[1]
            
            # Create new empty canvas for the moved selection
            new_canvas = self.canvas.copy()
            
            # Clear the original selected area
            new_canvas[self.selection_mask > 0] = (255, 255, 255)  # White out original
            
            # Calculate new position
            rows, cols = np.where(self.selection_mask > 0)
            new_rows = np.clip(rows + offset_y, 0, self.canvas.shape[0]-1)
            new_cols = np.clip(cols + offset_x, 0, self.canvas.shape[1]-1)
            
            # Copy the selected pixels to new position
            selected_pixels = self.selected_region[self.selection_mask > 0]
            new_canvas[new_rows, new_cols] = selected_pixels
            
            # Update the canvas and mask
            self.canvas = new_canvas
            self.pages[self.current_page_index] = self.canvas.copy()
            
            # Update selection mask position
            new_mask = np.zeros_like(self.selection_mask)
            new_mask[new_rows, new_cols] = 255
            self.selection_mask = new_mask
            self.selection_start = (self.original_selection_pos[0] + offset_x, 
                                   self.original_selection_pos[1] + offset_y)
        else:
            if hasattr(self, 'drag_start_pos'):
                del self.drag_start_pos
                del self.original_selection_pos

    def update_selection_position(self, x, y):
        """Move the selection based on the current cursor position."""
        if self.selected_region is None or self.selection_mask is None or self.drag_start_pos is None:
            return

        # Calculate movement offset
        offset_x = x - self.drag_start_pos[0]
        offset_y = y - self.drag_start_pos[1]
        
        # Create new empty canvas for the moved selection
        new_canvas = self.pages[self.current_page_index].copy() # Start from clean page?? 
        # Wait, original code: new_canvas = self.canvas.copy(). 
        # But self.canvas might have trails? 
        # Original: new_canvas[self.selection_mask > 0] = (255, 255, 255) (White out original)
        # We should use the logic that works.
        new_canvas = self.canvas.copy() # Use current canvas which has the hole? No.
        # Actually, in original code, self.canvas IS the canvas.
        # We need to erase the old selection from the canvas first?
        # The original code logic was:
        # new_canvas = self.canvas.copy()
        # new_canvas[self.selection_mask > 0] = white
        # This assumes self.canvas has the selection in the OLD position provided by self.selection_mask.
        # But if we do this every frame, we act on the *already moved* canvas?
        # Original code updated self.canvas = new_canvas continuously.
        # So self.selection_mask also updated continuously.
        # So it works incrementally.
        
        new_canvas[self.selection_mask > 0] = (255, 255, 255)
        
        rows, cols = np.where(self.selection_mask > 0)
        new_rows = np.clip(rows + offset_y, 0, self.canvas.shape[0]-1)
        new_cols = np.clip(cols + offset_x, 0, self.canvas.shape[1]-1)
        
        # We need to ensure we don't index out of bounds if offset is large
        # The clip handles the destination, but we need to match the source pixels.
        # Original code: selected_pixels = self.selected_region[self.selection_mask > 0]
        # This works if selected_region is static (the original cutout).
        
        # But wait, if we clip new_rows, the shape might change?
        # If new_rows has fewer pixels than rows (because of clip), assignment fails.
        # Original code didn't handle this clip limit well?
        # Actually: 'new_rows' might be same size as 'rows' if we just add offset.
        # np.clip returns same shape.
        # So it squashes pixels to the edge. It might look weird but it won't crash on shape mismatch.
        
        selected_pixels = self.selected_region[self.selection_mask > 0]
        new_canvas[new_rows, new_cols] = selected_pixels
        
        self.canvas = new_canvas
        self.pages[self.current_page_index] = self.canvas.copy()
        
        # Update selection mask position
        new_mask = np.zeros_like(self.selection_mask)
        new_mask[new_rows, new_cols] = 255
        self.selection_mask = new_mask
        
        # We need to update drag_start_pos? 
        # No, offset is relative to drag_start_pos. 
        # BUT original code was: offset from drag_start, applied to original_pos?
        # Original: offset = control - drag_start.
        # New Position = original + offset.
        # But then it updated self.canvas. 
        # If we calculate offset from START every time, we should arguably clear the *Original* mask?
        # But self.canvas keeps changing.
        # Original code:
        # 1. White out current mask.
        # 2. Draw at new position (calculated from offset of START).
        # 3. Update mask to new position.
        # This works.
        
        # However, in my new method, 'x, y' is current. 'self.drag_start_pos' is start.
        # So offset is total displacement.
        # But 'self.selection_mask' is currently at the *previous frame's* position (because we update it).
        # So we white out *current* position, then draw at *new* position?
        # Wait. 'offset' is defined as `current - start`.
        # So `pos = start_pos + offset`.
        # But `self.selection_mask` is at `last_pos`.
        # So we should white out `last_pos`.
        # And draw at `start_pos + offset`.
        # But if we update `selection_mask` to `new_cols`, then in next frame, that is `last_pos`.
        # So yes, it works.
        
        # One catch: `offset_x` in original was `control - drag_start`.
        # But we are updating `drag_start_pos` in the main loop?
        # No, in main loop I put `state.drag_start_pos = ...`.
        # So I need to use `x - self.drag_start_pos[0]`.
        # But `self.drag_start_pos` should remain constant during the drag.
        # My main loops updates it only on PINCH_START. Correct.
        
        # HOWEVER: `offset_x` in original code was used to calculate `new_rows` from `rows` (of mask).
        # But `mask` is UPDATED every frame to new position.
        # So `rows` (indices of mask) are *already shifted*.
        # If we add `offset` (total displacement) to `rows` (current shifted position), we double count!
        # Original code:
        # `rows, cols = np.where(self.selection_mask > 0)` -> These are current positions.
        # `new_rows = rows + offset` -> Use offset from start?
        # If mask is at P1. Start was P0. Current is P2. Offset is P2-P0.
        # We want to move from P1 to P2?
        # No, we want to move from ?? 
        # Actually original code had:
        # `new_rows = rows + offset`
        # `OFFSET` was `control - drag_start`.
        # This implies `rows` were expected to be at `drag_start`?
        # OR: The original code was BUGGY/WEIRD?
        # If `selection_mask` is updated, `rows` changes.
        # If I hold and move +10. `rows` shifts +10.
        # Next frame, move +11 (total). Offset = 11. `rows` is at +10.
        # `new_rows` = 10 + 11 = 21.
        # Result: Exponential fly-away!
        
        # The user said "The system works but feels fragile and messy".
        # This implies it might have worked by luck or I am misreading.
        # Let's check `move_selection` in `26_03_2025V1.py` again.
        # It calculates offset.
        # It updates `self.selection_mask = new_mask`.
        # It updates `self.selection_start`.
        # It resets `drag_start_pos` ?? No.
        # It does NOT update `drag_start_pos`.
        # So `offset` keeps growing.
        # So `new_rows = rows + offset` DOES cause fly-away if `rows` follows `mask`.
        # UNLESS `self.selection_mask` was NOT updated?
        # Line 219: `self.selection_mask = new_mask`.
        # So it WAS updated.
        # So the original code likely had the fly-away bug or I am misunderstanding.
        # Wait, maybe `rows` are relative to something else? No `np.where` returns indices.
        
        # FIX: We should calculate `delta` from last frame.
        # `delta_x = x - self.last_x`.
        # `new_rows = rows + delta`.
        # This is robust.
        # I will implement the robust version.
        
        delta_x = x - self.last_point[0] if self.last_point else 0
        delta_y = y - self.last_point[1] if self.last_point else 0
        
        # But `state.last_point` is used for drawing. I shouldn't rely on it.
        # I'll track `self.last_drag_pos`.
        
        if not hasattr(self, 'last_drag_pos') or self.last_drag_pos is None:
             self.last_drag_pos = self.drag_start_pos
             
        delta_x = x - self.last_drag_pos[0]
        delta_y = y - self.last_drag_pos[1]
        self.last_drag_pos = (x, y)
        
        new_canvas = self.canvas.copy()
        new_canvas[self.selection_mask > 0] = (255, 255, 255)
        
        rows, cols = np.where(self.selection_mask > 0)
        new_rows = np.clip(rows + delta_y, 0, self.canvas.shape[0]-1)
        new_cols = np.clip(cols + delta_x, 0, self.canvas.shape[1]-1)
        
        selected_pixels = self.selected_region[self.selection_mask > 0]
        # Size mismatch check?
        if len(new_rows) == len(selected_pixels):
             new_canvas[new_rows, new_cols] = selected_pixels
             self.canvas = new_canvas
             self.pages[self.current_page_index] = self.canvas.copy()
             
             new_mask = np.zeros_like(self.selection_mask)
             new_mask[new_rows, new_cols] = 255
             self.selection_mask = new_mask



def on_trackbar_change(*args):
    pass

def draw_control_panel_button(canvas):

    button_x, button_y, button_w, button_h       =       20, canvas.shape[0] - 70, 40, 40 
    cv2.rectangle(canvas, (button_x, button_y), 
                         (button_x + button_w, button_y + button_h), 
                         (46, 40, 219), -1)
    cv2.putText(canvas, 'C', (button_x + 13, button_y + 25), 
                cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 255, 255), 2)
    return (button_x, button_y, button_x + button_w, button_y + button_h)

def draw_drawing_mode_button(canvas):
    # Position in left middle of screen
    button_w, button_h = 40, 40
    button_x = 20  # Left margin
    button_y = canvas.shape[0] - 190  # lower Middle of screen height
    
    # Draw the button with different colors based on drawing mode status
    if state.drawing_mode_active:
        # Green background when drawing is active
        cv2.rectangle(canvas, (button_x, button_y), 
                            (button_x + button_w, button_y + button_h), 
                            (0, 200, 0), -1)
    else:
        # Red background when drawing is inactive
        cv2.rectangle(canvas, (button_x, button_y), 
                            (button_x + button_w, button_y + button_h), 
                            (0, 0, 200), -1)
    
    cv2.putText(canvas, 'D', (button_x + 13, button_y + 25), 
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255), 2)
    
    return (button_x, button_y, button_x + button_w, button_y + button_h)

def draw_navigation_buttons(canvas):
    button_x, button_w, button_h = 20, 40, 40
    
    # ↓ Previous Page Button (Downward Triangle)
    prev_button_y = canvas.shape[0] - 250
    prev_triangle = np.array([
        [button_x + button_w // 2, prev_button_y + button_h - 10],
        [button_x + 10, prev_button_y + 10],
        [button_x + button_w - 10, prev_button_y + 10]
    ])
    cv2.fillPoly(canvas, [prev_triangle], (46, 40, 219))

    # + New Page Button (Square with '+')
    new_button_y = prev_button_y - 50
    cv2.rectangle(canvas, (button_x, new_button_y),
                  (button_x + button_w, new_button_y + button_h),
                  (46, 40, 219), -1)
    cv2.putText(canvas, '+', (button_x + 13, new_button_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # ↑ Next Page Button (Upward Triangle)
    next_button_y = new_button_y - 50
    next_triangle = np.array([
        [button_x + button_w // 2, next_button_y + 10],
        [button_x + 10, next_button_y + button_h - 10],
        [button_x + button_w - 10, next_button_y + button_h - 10]
    ])
    cv2.fillPoly(canvas, [next_triangle], (46, 40, 219))

    return {
        "prev": (button_x, prev_button_y, button_x + button_w, prev_button_y + button_h),
        "new": (button_x, new_button_y, button_x + button_w, new_button_y + button_h),
        "next": (button_x, next_button_y, button_x + button_w, next_button_y + button_h)
    }


import time
last_click_time = 0  # To track the last click time


def draw_shapes_button(canvas):
    # Main Shape Button Position
    button_x, button_y = canvas.shape[1] - 50, canvas.shape[0] // 2 - 100  
    button_w, button_h = 35, 35
    
    shape_bounds = {}
    
    # 1. Main Toggle Button (Icon: Triangle/Circle combo or just "S")
    # Active if palette is open OR a shape is selected
    is_active = state.shape_palette_open or isinstance(state.active_tool, ShapeTool)
    fill_color = (46, 40, 219) if not is_active else (0, 128, 255)
    
    cv2.rectangle(canvas, (button_x, button_y), 
                  (button_x + button_w, button_y + button_h), 
                  fill_color, -1)
    
    # Icon: Simple shapes
    cv2.circle(canvas, (button_x + 10, button_y + 10), 5, (255, 255, 255), 1)
    cv2.rectangle(canvas, (button_x + 20, button_y + 20), (button_x + 28, button_y + 28), (255, 255, 255), 1)
    
    shape_bounds["MAIN_TOGGLE"] = (button_x, button_y, button_x + button_w, button_y + button_h)

    # 2. Palette (if open)
    if state.shape_palette_open:
        shapes = ["Oval", "Circle", "Square", "Triangle"]
        
        # Expand downwards
        current_y = button_y + button_h + 10
        
        for shape in shapes:
            shape_button_y = current_y
            
            # Highlight selected shape
            is_selected = state.selected_shape == shape
            bg_color = (60, 60, 60) if not is_selected else (0, 200, 0) # Dark gray vs Green
            
            # Background
            cv2.rectangle(canvas, (button_x, shape_button_y), 
                          (button_x + button_w, shape_button_y + button_h), 
                          bg_color, -1)
            
            # Center for icon
            center = (button_x + button_w // 2, shape_button_y + button_h // 2)

            # Draw Icons
            if shape == "Oval":
                cv2.ellipse(canvas, center, (12, 6), 0, 0, 360, (255, 255, 255), 2)
            elif shape == "Circle":
                cv2.circle(canvas, center, 8, (255, 255, 255), 2)
            elif shape == "Square":
                cv2.rectangle(canvas, (center[0] - 8, center[1] - 8), 
                              (center[0] + 8, center[1] + 8), 
                              (255, 255, 255), 2)
            elif shape == "Triangle":
                pts = np.array([[center[0], center[1] - 8], 
                                [center[0] - 8, center[1] + 8], 
                                [center[0] + 8, center[1] + 8]], np.int32)
                cv2.polylines(canvas, [pts], isClosed=True, color=(255, 255, 255), thickness=2)

            shape_bounds[shape] = (button_x, shape_button_y, button_x + button_w, shape_button_y + button_h)
            
            current_y += button_h + 5 # Spacing

    return shape_bounds

def draw_shape(canvas, shape_type, start_point, end_point, color, thickness=2):
    if shape_type == "Circle":
        radius = int(np.sqrt((end_point[0] - start_point[0])**2 + (end_point[1] - start_point[1])**2))
        cv2.circle(canvas, start_point, radius, color, thickness)
    
    elif shape_type == "Oval":
        # Calculate width and height for the oval
        width = abs(end_point[0] - start_point[0])
        height = abs(end_point[1] - start_point[1])
        center = (min(start_point[0], end_point[0]) + width//2, 
                  min(start_point[1], end_point[1]) + height//2)
        axes = (max(width//2, 1), max(height//2, 1))  # Avoid zero values
        cv2.ellipse(canvas, center, axes, 0, 0, 360, color, thickness)
    
    elif shape_type == "Square":
        # Make it a perfect square based on the larger dimension
        side = max(abs(end_point[0] - start_point[0]), abs(end_point[1] - start_point[1]))
        x_direction = 1 if end_point[0] >= start_point[0] else -1
        y_direction = 1 if end_point[1] >= start_point[1] else -1
        
        end_x = start_point[0] + (side * x_direction)
        end_y = start_point[1] + (side * y_direction)
        
        cv2.rectangle(canvas, start_point, (end_x, end_y), color, thickness)
    
    elif shape_type == "Triangle":
        # Create an isosceles triangle with the base parallel to the x-axis
        x1, y1 = start_point
        x2, y2 = end_point
        
        # The apex of the triangle is at the midpoint of the x-coordinates and at the y-coordinate of the starting point
        x3 = (x1 + x2) // 2
        y3 = y1
        
        pts = np.array([[x3, y3], [x1, y2], [x2, y2]], np.int32)
        cv2.polylines(canvas, [pts], isClosed=True, color=color, thickness=thickness)


def is_thumb_index_click_near_button(hand_landmarks, button_bounds, canvas_width, canvas_height, distance_threshold=40, cooldown=0.1):
    global last_click_time
    current_time = time.time()
    
    # Check if the cooldown period has passed
    if current_time - last_click_time < cooldown:
        return False

    # Get the coordinates of the thumb and index finger tips
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb_x, thumb_y = int(thumb_tip.x * canvas_width), int(thumb_tip.y * canvas_height)
    index_x, index_y = int(index_tip.x * canvas_width), int(index_tip.y * canvas_height)

    # Calculate squared distance between thumb and index finger tips
    distance_sq = (thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2
    threshold_sq = distance_threshold ** 2

    # Unpack button boundaries
    x1, y1, x2, y2 = button_bounds

    # Check if the index finger is within button bounds and distance is below threshold
    if x1 <= index_x <= x2 and y1 <= index_y <= y2 and distance_sq < threshold_sq:
        last_click_time = current_time  # Update the last click time
        return True
    return False


def draw_erase_all_button(canvas):
    button_w, button_h = 40, 40  # Increased width for a rectangular shape
    button_x = 20  # Left margin, same as 'C' button
    button_y = canvas.shape[0] - 130  # Just above the 'C' button
    cv2.rectangle(canvas, (button_x, button_y), 
                         (button_x + button_w, button_y + button_h), 
                         (46, 40, 219), -1)  
    cv2.putText(canvas, 'EA', (button_x + 8, button_y + 25), 
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1,(255, 255, 255), 2)
    return (button_x, button_y, button_x + button_w, button_y + button_h)


def update_control_panel_values(state):
    if state.control_panel_exists:
        try:
            r = cv2.getTrackbarPos('Background R', 'Control Panel')
            g = cv2.getTrackbarPos('Background G', 'Control Panel')
            b = cv2.getTrackbarPos('Background B', 'Control Panel')
            if not state.using_vibgyor:
                b = cv2.getTrackbarPos('Draw B', 'Control Panel')
                g = cv2.getTrackbarPos('Draw G', 'Control Panel')
                r = cv2.getTrackbarPos('Draw R', 'Control Panel')
                state.default_color = (b, g, r)
            state.default_thickness = max(1, cv2.getTrackbarPos('Thickness', 'Control Panel'))
            state.smoothing_factor = cv2.getTrackbarPos('Smoothing', 'Control Panel') / 10.0
        except cv2.error as e:
            print(f"Failed to update control panel values: {e}")

def create_control_panel():
    try:
        cv2.namedWindow('Control Panel', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Control Panel', 400, 400)
        control_panel_img = np.ones((400, 400, 3), dtype=np.uint8) * 200
        cv2.imshow('Control Panel', control_panel_img)
        cv2.waitKey(1)  
        cv2.createTrackbar('Background R', 'Control Panel', 255, 255, on_trackbar_change)
        cv2.createTrackbar('Background G', 'Control Panel', 255, 255, on_trackbar_change)
        cv2.createTrackbar('Background B', 'Control Panel', 255, 255, on_trackbar_change)
        cv2.createTrackbar('Draw R', 'Control Panel', 0, 255, on_trackbar_change)
        cv2.createTrackbar('Draw G', 'Control Panel', 255, 255, on_trackbar_change)
        cv2.createTrackbar('Draw B', 'Control Panel', 0, 255, on_trackbar_change)
        cv2.createTrackbar('Thickness', 'Control Panel', 5, 20, on_trackbar_change)
        cv2.createTrackbar('Smoothing', 'Control Panel', 5, 10, on_trackbar_change)
        state.control_panel_exists = True
        return True
    except cv2.error as e:
        print(f"Failed to create Control Panel: {e}")
        state.control_panel_exists = False
        return False

def interpolate_line(start, end, steps=15, color=(0, 0, 255), thickness=3):
    for i in range(steps):
        x = int(start[0] + (end[0] - start[0]) * i / steps)
        y = int(start[1] + (end[1] - start[1]) * i / steps)
        cv2.circle(state.canvas, (x, y), thickness, color, -1)

def erase_area(canvas, center, radius=30):
    """Erase an area and save the state before erasing."""
    state.undo_stack.append(state.canvas.copy())  # Save current state before erasing
    state.redo_stack.clear()  # Clear redo stack since new changes invalidate redo
    cv2.circle(canvas, center, radius, (255, 255, 255), -1)

def draw_smooth_line(start, end, color=(0, 0, 255), thickness=3):
    """Draw a smooth line and save the state before drawing."""
    state.undo_stack.append(state.canvas.copy())  # Save the current state before drawing
    state.redo_stack.clear()  # Clear redo stack since new changes invalidate redo
    interpolate_line(start, end, steps=20, color=color, thickness=thickness)

def draw_ui(canvas):
    cv2.putText(canvas, 'Gesture Craft Intelligent Drawing', (10, 30), 
                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 255), 1)

def draw_visual_indicator(canvas):
    if state.shape_mode_active:
        mode_text = f"Shape Mode: {state.selected_shape}"
    else:
        mode_text = "Eraser Mode" if state.eraser_mode_active else (
            "Drawing Mode" if state.drawing_mode_active else "Paused")
    
    cv2.putText(canvas, f"Mode: {mode_text}", (10, 55), 
                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 255), 1)
    
    if (state.drawing_mode_active or state.shape_mode_active) and not state.eraser_mode_active:
        color_str = f"Color: {state.get_current_color_name()}"
        current_color = state.get_current_color()
        cv2.putText(canvas, color_str, (10, 70), 
                    cv2.FONT_HERSHEY_TRIPLEX, 0.6, current_color, 1)

def is_palm_open(hand_landmarks):
    fingertips_extended = all(
        hand_landmarks.landmark[tip.value].y < hand_landmarks.landmark[(tip.value)-2].y 
        for tip in [
            HandLandmark.THUMB_TIP, 
            HandLandmark.INDEX_FINGER_TIP,
            HandLandmark.MIDDLE_FINGER_TIP,
            HandLandmark.RING_FINGER_TIP,
            HandLandmark.PINKY_TIP
        ]
    )
    return fingertips_extended

def check_thumb_pinky_touch(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[HandLandmark.THUMB_TIP.value]
    pinky_tip = hand_landmarks.landmark[HandLandmark.PINKY_TIP.value]
    
    distance = np.sqrt(
        (thumb_tip.x - pinky_tip.x)**2 + 
        (thumb_tip.y - pinky_tip.y)**2 +
        (thumb_tip.z - pinky_tip.z)**2
    )
    
    return distance < 0.07

def draw_undo_redo_buttons(canvas):
    button_x = canvas.shape[1] - 50
    button_w, button_h = 35, 35  # Button dimensions
    font_scale, thickness = 1, 2  # Font settings
    
    buttons = {"undo": "U", "redo": "R"}
    button_y_positions = {
        "undo": canvas.shape[0] - 130,
        "redo": canvas.shape[0] - 190
    }

    button_bounds = {}

    for key, text in buttons.items():
        button_y = button_y_positions[key]
        
        # Draw button
        cv2.rectangle(canvas, (button_x, button_y),
                      (button_x + button_w, button_y + button_h),
                      (46, 40, 219), -1)
        
        # Get text size
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        text_x = button_x + (button_w - text_size[0]) // 2
        text_y = button_y + (button_h + text_size[1]) // 2

        # Draw centered text
        cv2.putText(canvas, text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)

        button_bounds[key] = (button_x, button_y, button_x + button_w, button_y + button_h)

    return button_bounds

def draw_control_panel(canvas):
    """Draw the control panel on the canvas if it is visible."""
    if state.control_panel_visible:
        panel_width = 200
        panel_height = 400
        panel_x = canvas.shape[1] - panel_width - 20  # Right side of the canvas
        panel_y = 20  # Top of the canvas

        # Draw the control panel background
        cv2.rectangle(canvas, (panel_x, panel_y), 
                             (panel_x + panel_width, panel_y + panel_height), 
                             (200, 200, 200), -1)

        # Draw sliders for color and thickness
        slider_x = panel_x + 10
        slider_y = panel_y + 20
        slider_width = 180
        slider_height = 20

        # Background color sliders
        cv2.putText(canvas, "Background R", (slider_x, slider_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + slider_width, slider_y + 10 + slider_height), 
                             (255, 255, 255), -1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + int(state.background_r * slider_width / 255), slider_y + 10 + slider_height), 
                             (0, 0, 255), -1)

        slider_y += 50
        cv2.putText(canvas, "Background G", (slider_x, slider_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + slider_width, slider_y + 10 + slider_height), 
                             (255, 255, 255), -1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + int(state.background_g * slider_width / 255), slider_y + 10 + slider_height), 
                             (0, 255, 0), -1)

        slider_y += 50
        cv2.putText(canvas, "Background B", (slider_x, slider_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + slider_width, slider_y + 10 + slider_height), 
                             (255, 255, 255), -1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + int(state.background_b * slider_width / 255), slider_y + 10 + slider_height), 
                             (255, 0, 0), -1)

        # Drawing color sliders
        slider_y += 50
        cv2.putText(canvas, "Draw R", (slider_x, slider_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + slider_width, slider_y + 10 + slider_height), 
                             (255, 255, 255), -1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + int(state.default_color[2] * slider_width / 255), slider_y + 10 + slider_height), 
                             (0, 0, 255), -1)

        slider_y += 50
        cv2.putText(canvas, "Draw G", (slider_x, slider_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + slider_width, slider_y + 10 + slider_height), 
                             (255, 255, 255), -1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + int(state.default_color[1] * slider_width / 255), slider_y + 10 + slider_height), 
                             (0, 255, 0), -1)

        slider_y += 50
        cv2.putText(canvas, "Draw B", (slider_x, slider_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + slider_width, slider_y + 10 + slider_height), 
                             (255, 255, 255), -1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + int(state.default_color[0] * slider_width / 255), slider_y + 10 + slider_height), 
                             (255, 0, 0), -1)

        # Thickness slider
        slider_y += 50
        cv2.putText(canvas, "Thickness", (slider_x, slider_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + slider_width, slider_y + 10 + slider_height), 
                             (255, 255, 255), -1)
        cv2.rectangle(canvas, (slider_x, slider_y + 10), 
                             (slider_x + int(state.default_thickness * slider_width / 20), slider_y + 10 + slider_height), 
                             (0, 0, 0), -1)

        return panel_x, panel_y, panel_width, panel_height
    return None, None, None, None

def update_control_panel_values(state, index_x, index_y, panel_x, panel_y, panel_width, panel_height):
    """Update the control panel values based on hand position."""
    if panel_x <= index_x <= panel_x + panel_width and panel_y <= index_y <= panel_y + panel_height:
        relative_x = index_x - panel_x
        slider_width = 180

        # Background R
        if panel_y + 20 <= index_y <= panel_y + 50:
            state.background_r = int((relative_x / slider_width) * 255)
            state.update_canvas_background()  # Update the canvas background
        # Background G
        elif panel_y + 70 <= index_y <= panel_y + 100:
            state.background_g = int((relative_x / slider_width) * 255)
            state.update_canvas_background()  # Update the canvas background
        # Background B
        elif panel_y + 120 <= index_y <= panel_y + 150:
            state.background_b = int((relative_x / slider_width) * 255)
            state.update_canvas_background()  # Update the canvas background
        # Draw R
        elif panel_y + 170 <= index_y <= panel_y + 200:
            state.default_color = (state.default_color[0], state.default_color[1], int((relative_x / slider_width) * 255))
        # Draw G
        elif panel_y + 220 <= index_y <= panel_y + 250:
            state.default_color = (state.default_color[0], int((relative_x / slider_width) * 255), state.default_color[2])
        # Draw B
        elif panel_y + 270 <= index_y <= panel_y + 300:
            state.default_color = (int((relative_x / slider_width) * 255), state.default_color[1], state.default_color[2])
        # Thickness
        elif panel_y + 320 <= index_y <= panel_y + 350:
            state.default_thickness = int((relative_x / slider_width) * 20)

def draw_freedom_select_button(canvas):
    button_x, button_y = 20, 100
    button_w, button_h = 150, 40
    cv2.rectangle(canvas, (button_x, button_y), 
                         (button_x + button_w, button_y + button_h), 
                         (0, 255, 0) if state.selecting else (0, 200, 200), -1)
    cv2.putText(canvas, 'Freedom Select', (button_x + 10, button_y + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    return (button_x, button_y, button_x + button_w, button_y + button_h)


def is_point_in_rect(point, rect):
    x, y = point
    rx1, ry1, rx2, ry2 = rect
    return rx1 <= x <= rx2 and ry1 <= y <= ry2

def main():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("Could not open video capture device")

        cv2.namedWindow('Drawing Canvas')

        while True:
            success, frame = cap.read()
            if not success:
                print("Failed to grab frame")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe Tasks API
            results = None
            if hand_landmarker is not None:
                try:
                    # Ensure proper image format
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb_frame))
                    detection_result = hand_landmarker.detect(mp_image)
                    
                    # Convert Tasks API result to legacy format for compatibility
                    if detection_result.hand_landmarks:
                        class LegacyResults:
                            def __init__(self, landmarks_list):
                                self.multi_hand_landmarks = landmarks_list
                        
                        class LegacyLandmarks:
                            def __init__(self, task_landmarks):
                                self.landmark = task_landmarks
                        
                        legacy_landmarks = [LegacyLandmarks(detection_result.hand_landmarks[0])]
                        results = LegacyResults(legacy_landmarks)
                except Exception as e:
                    # Silently handle detection errors to keep app running
                    pass

            canvas = state.get_composite_image()
            control_button_bounds = draw_control_panel_button(canvas)
            erase_all_button_bounds = draw_erase_all_button(canvas)
            nav_buttons = draw_navigation_buttons(canvas)
            shape_buttons = draw_shapes_button(canvas)
            drawing_button_bounds = draw_drawing_mode_button(canvas)
            undo_redo_buttons = draw_undo_redo_buttons(canvas)
            freedom_select_bounds = draw_freedom_select_button(canvas)

            # Freedom Select handling moved under results processing to avoid undefined variables

            # Then continue with your existing hand landmark processing:
            
            # Draw the control panel on the canvas if it is visible
            panel_x, panel_y, panel_width, panel_height = draw_control_panel(canvas)

            if results and hasattr(results, 'multi_hand_landmarks') and results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                h, w, _ = canvas.shape
                
                # ==============================================================================
                # 1. Process Gesture & Raw Data
                # ==============================================================================
                event = state.gesture_interpreter.process(hand_landmarks)
                
                # Extract Hand Confidence
                hand_confidence = 1.0
                try:
                     if 'detection_result' in locals() and detection_result and detection_result.handedness:
                         hand_confidence = detection_result.handedness[0][0].score
                except:
                     pass

                # COMPUTE RAW CURSOR POSITION (REQUIRED FOR UI HIT TEST)
                # We use event.x/y (Midpoint during pinch) rather than index tip to align with visual cursor location
                cursor_raw_x, cursor_raw_y = int(event.x * w), int(event.y * h)
                
                # DEBUG LOGS (REQUIRED)
                if event.type == GestureType.PINCH and event.state == GestureState.START:
                     print(f"PINCH_START at {cursor_raw_x}, {cursor_raw_y}")

                # ==============================================================================
                # 2. UI HANDLING (STRICT PRIORITY)
                # MUST BE EVALUATED BEFORE ANY TOOL LOGIC
                # ==============================================================================
                
                # Helper: Smart Inward Expansion
                def expand_hitbox(rect, padding=25):
                    x1, y1, x2, y2 = rect
                    center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
                    
                    # Determine expansion direction based on quadrant
                    if center_x < w / 3: x2 += padding
                    elif center_x > 2 * w / 3: x1 -= padding
                    
                    if center_y > 2 * h / 3: y1 -= padding
                    elif center_y < h / 3: y2 += padding
                    
                    margin = 5
                    return (x1 - margin, y1 - margin, x2 + margin, y2 + margin)

                # Identify UI Targets for Hit Testing
                ui_targets = [
                    ('CONTROL', expand_hitbox(control_button_bounds)),
                    ('DRAWING', expand_hitbox(drawing_button_bounds)),
                    ('ERASE_ALL', expand_hitbox(erase_all_button_bounds)),
                    ('FREEDOM', expand_hitbox(freedom_select_bounds))
                ]
                for name, bounds in nav_buttons.items():
                    ui_targets.append((f'NAV_{name}', expand_hitbox(bounds)))
                for name, bounds in undo_redo_buttons.items():
                    ui_targets.append((f'UNDO_{name}', expand_hitbox(bounds)))
                for name, bounds in shape_buttons.items():
                    ui_targets.append((f'SHAPE_{name}', expand_hitbox(bounds)))
                
                if state.control_panel_visible and panel_width > 0:
                    ui_targets.append(('PANEL', (panel_x, panel_y, panel_x + panel_width, panel_y + panel_height)))

                # Determine UI Hit using RAW CURSOR COORDINATES
                hit_ui_id = None
                for uid, rect in ui_targets:
                    if rect and is_point_in_rect((cursor_raw_x, cursor_raw_y), rect):
                        hit_ui_id = uid
                        break
                
                ui_consumed = False

                # FIX: Check for UI Interaction (Global Override)
                # Ignore all locks if a NEW pinch starts on UI
                if event.type == GestureType.PINCH and event.state == GestureState.START and hit_ui_id:
                     print(f"UI HIT {hit_ui_id}")
                     print("UI CLICK FIRED")
                     
                     # Consumed immediately
                     ui_consumed = True
                     
                     # Execute Actions
                     if hit_ui_id == 'CONTROL':
                         state.control_panel_visible = not state.control_panel_visible
                     elif hit_ui_id == 'DRAWING':
                         if isinstance(state.active_tool, PenTool):
                             state.set_tool(PointerTool())
                             state.selecting = False
                             state.cancel_selection()
                         else:
                             state.set_tool(PenTool())
                     elif hit_ui_id == 'ERASE_ALL':
                         state.canvas = np.ones((550, 850, 3), dtype=np.uint8) * 255
                         state.pages[state.current_page_index] = state.canvas.copy()
                     elif hit_ui_id == 'FREEDOM':
                         state.set_tool(PointerTool())
                         if state.selecting:
                             state.complete_selection()
                         else:
                             state.start_selection(cursor_raw_x, cursor_raw_y)
                     elif hit_ui_id.startswith('NAV_'):
                         action = hit_ui_id.replace('NAV_', '')
                         if action == 'new': state.add_new_page()
                         elif action == 'next': state.switch_page("next")
                         elif action == 'prev': state.switch_page("prev")
                     elif hit_ui_id.startswith('UNDO_'):
                         action = hit_ui_id.replace('UNDO_', '')
                         if action == 'undo': state.undo()
                         elif action == 'redo': state.redo()
                     
                     elif hit_ui_id.startswith('SHAPE_'):
                         shape_action = hit_ui_id.replace('SHAPE_', '')
                         
                         if shape_action == "MAIN_TOGGLE":
                             state.shape_palette_open = not state.shape_palette_open
                         else:
                             state.set_tool(ShapeTool(shape_action))
                             state.selecting = False
                             state.cancel_selection()
                             state.shape_palette_open = False # Auto-close
                     
                     # Always lock intent to UI to consume HOLD frames (Debounce)
                     state.intent_owner = "UI"
                
                # Handle existing UI Intent (Dragging Sliders)
                elif state.intent_owner == "UI":
                    if event.type == GestureType.PINCH:
                         if event.state == GestureState.HOLD:
                             if state.control_panel_visible and panel_width > 0:
                                 # Use RAW for slider responsiveness as well
                                 update_control_panel_values(state, cursor_raw_x, cursor_raw_y, panel_x, panel_y, panel_width, panel_height)
                         elif event.state == GestureState.END:
                             state.intent_owner = None
                    ui_consumed = True

                # ==============================================================================
                # 3. Tool Routing (Only if UI didn't consume)
                # ==============================================================================
                
                # Default for drawing cursor
                smoothed_x, smoothed_y = cursor_raw_x, cursor_raw_y

                if not ui_consumed:
                    # Smoothing Logic (Only update smoother if active)
                    cursor_raw_x, cursor_raw_y = int(event.x * w), int(event.y * h)
                
                    should_update_cursor = True
                    if hand_confidence < 0.5: 
                         should_update_cursor = False
                    
                    if state.last_point and should_update_cursor:
                         dist = np.sqrt((cursor_raw_x - state.smoother.last_x)**2 + (cursor_raw_y - state.smoother.last_y)**2)
                         if dist > 300: # Extreme jump prevention
                             should_update_cursor = False
                    
                    if should_update_cursor:
                         smoothed_x, smoothed_y = state.smoother.update(cursor_raw_x, cursor_raw_y, w, h)
                    else:
                         smoothed_x = int(state.smoother.prev_smoothed_x) if state.smoother.prev_smoothed_x else cursor_raw_x
                         smoothed_y = int(state.smoother.prev_smoothed_y) if state.smoother.prev_smoothed_y else cursor_raw_y

                    # Route to Tool
                    if state.intent_owner is None:
                        # Try to assign to Tool
                        if event.type == GestureType.PINCH and event.state == GestureState.START:
                            state.intent_owner = "TOOL"
                            state.active_tool.on_event(event, smoothed_x, smoothed_y, state)
                        
                        else:
                            # Hover / Global Gestures
                            is_hovering_ui = (hit_ui_id is not None)
                            
                            if not is_hovering_ui:
                                if check_thumb_pinky_touch(hand_landmarks):
                                    if state.color_change_start_time is None:
                                        state.color_change_start_time = time.time()
                                    elif time.time() - state.color_change_start_time >= state.color_change_duration:
                                        state.using_vibgyor = True
                                        state.current_color_index = (state.current_color_index + 1) % len(state.vibgyor_colors)
                                        state.color_change_start_time = None
                                else:
                                    state.color_change_start_time = None

                                # Safe to update cursor/tool
                                state.active_tool.on_event(event, smoothed_x, smoothed_y, state)
                            
                    elif state.intent_owner == "TOOL":
                        # Forward Pinch Events
                        if event.type == GestureType.PINCH:
                            state.active_tool.on_event(event, smoothed_x, smoothed_y, state)
                            if event.state == GestureState.END:
                                state.intent_owner = None

                # 4. Draw Visual Feedback (Cursors, Overlays)
                # Ensure cursor is drawn even if UI was triggered (for feedback)
                state.active_tool.draw_overlay(canvas, smoothed_x, smoothed_y, state)

                # Freedom Selection Move visualization
                if state.selected_region is not None:
                    contours, _ = cv2.findContours(state.selection_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cv2.drawContours(canvas, contours, -1, (0, 255, 0), 2)

                # Additional Freedom Select drawing when actively selecting
                if state.selecting:
                    if len(state.current_selection) > 1:
                        pts = np.array(state.current_selection, np.int32)
                        pts = pts.reshape((-1, 1, 2))
                        cv2.polylines(canvas, [pts], isClosed=False, color=(0, 255, 255), thickness=2)


            # Draw UI elements
            draw_ui(canvas)
            draw_visual_indicator(canvas)
            cv2.putText(canvas, f"Page: {state.current_page_index + 1}/{state.total_pages}", (10, 90),
                        cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 255), 1)
            
            # Display the canvas
            cv2.imshow('Drawing Canvas', canvas)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Quit the program
                break
            elif key == ord('c'):  # Toggle control panel visibility
                state.control_panel_visible = not state.control_panel_visible
                
            elif key == ord('e'):  # Toggle Eraser Tool (FIX 3: Eraser requires explicit selection)
                if isinstance(state.active_tool, EraserTool):
                    state.set_tool(PointerTool())  # Toggle off
                else:
                    state.set_tool(EraserTool())
                state.selecting = False
                state.cancel_selection()

            elif key == ord('d'):  # Toggle drawing mode (Pen Tool)
                if isinstance(state.active_tool, PenTool):
                    state.set_tool(PointerTool())  # Toggle off
                else:
                    state.set_tool(PenTool())
                state.selecting = False
                state.cancel_selection()

     
            elif key == ord('n'):  # Add new page
                state.add_new_page()
            elif key == ord('p'):  # Previous page
                state.switch_page("prev")
            elif key == ord('l'):  # Next page
                state.switch_page("next")
            elif key == ord('z'):  # Undo
                state.undo()
            elif key == ord('y'):  # Redo
                state.redo()            
            elif key == ord('f'):  # Toggle freedom selection mode
                if state.selecting:
                    state.complete_selection()
                    state.selecting = False
                else:
                    state.start_selection(state.smoother.last_x, state.smoother.last_y)

    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")

    finally:
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()

# Initialize MediaPipe Hands with Tasks API
hands = None
hand_landmarker = None
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    from mediapipe import tasks
    import os
    import urllib.request
    
    # Download hand landmarker model if not present
    model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
    if not os.path.exists(model_path):
        print("Downloading hand landmarker model...")
        model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
        urllib.request.urlretrieve(model_url, model_path)
        print("Model downloaded successfully.")
    
    # Create hand landmarker
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6
    )
    hand_landmarker = vision.HandLandmarker.create_from_options(options)
    print("Hand tracking initialized successfully.")
except Exception as e:
    print(f"MediaPipe initialization failed: {e}")
    print("Running without hand tracking.")

state = State()

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    main()

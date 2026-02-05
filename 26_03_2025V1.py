import cv2
import mediapipe as mp
import numpy as np
import time
from tkinter import Tk, messagebox

class LandmarkSmoother:
    def __init__(self, alpha=0.7):
        self.alpha = alpha
        self.last_x = None
        self.last_y = None

    def smooth(self, x, y):
        if self.last_x is None or self.last_y is None:
            self.last_x, self.last_y = x, y
        else:
            self.last_x = int(self.alpha * x + (1 - self.alpha) * self.last_x)
            self.last_y = int(self.alpha * y + (1 - self.alpha) * self.last_y)
        return self.last_x, self.last_y

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
        self.smoother = LandmarkSmoother(alpha=0.7)
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
        self.original_selection_pos = None

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
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
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
    button_x, button_y = canvas.shape[1] - 50, canvas.shape[0] // 2 - 100  
    button_w, button_h = 35, 35  # Adjust button size if needed

    shape_bounds = {}

    shapes = ["Oval", "Circle", "Square", "Triangle"]

    for i, shape in enumerate(shapes):
        shape_button_y = button_y + i * (button_h + 10)
        
        # Correct placement of center calculation
        center = (button_x + button_w // 2, shape_button_y + button_h // 2)  # Center the shape

        # Button background
        fill_color = (46, 40, 219)  
        if state.shape_mode_active and state.selected_shape == shape:
            fill_color = (0, 128, 255)  

        cv2.rectangle(canvas, (button_x, shape_button_y), 
                      (button_x + button_w, shape_button_y + button_h), 
                      fill_color, -1)

        # Draw centered, smaller shapes
        if shape == "Oval":
            cv2.ellipse(canvas, center, (12, 6), 0, 0, 360, (255, 255, 255), 2)  # Smaller Oval
        elif shape == "Circle":
            cv2.circle(canvas, center, 8, (255, 255, 255), 2)  # Smaller Circle
        elif shape == "Square":
            cv2.rectangle(canvas, (center[0] - 8, center[1] - 8), 
                          (center[0] + 8, center[1] + 8), 
                          (255, 255, 255), 2)  # Smaller Square
        elif shape == "Triangle":
            pts = np.array([[center[0], center[1] - 8], 
                            [center[0] - 8, center[1] + 8], 
                            [center[0] + 8, center[1] + 8]], np.int32)
            cv2.polylines(canvas, [pts], isClosed=True, color=(255, 255, 255), thickness=2)  # Smaller Triangle

        shape_bounds[shape] = (button_x, shape_button_y, button_x + button_w, shape_button_y + button_h)

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
        hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip-2].y 
        for tip in [
            mp_hands.HandLandmark.THUMB_TIP, 
            mp_hands.HandLandmark.INDEX_FINGER_TIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            mp_hands.HandLandmark.RING_FINGER_TIP,
            mp_hands.HandLandmark.PINKY_TIP
        ]
    )
    return fingertips_extended

def check_thumb_pinky_touch(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    
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
            results = hands.process(rgb_frame)

            canvas = state.get_composite_image()
            control_button_bounds = draw_control_panel_button(canvas)
            erase_all_button_bounds = draw_erase_all_button(canvas)
            nav_buttons = draw_navigation_buttons(canvas)
            shape_buttons = draw_shapes_button(canvas)
            drawing_button_bounds = draw_drawing_mode_button(canvas)
            undo_redo_buttons = draw_undo_redo_buttons(canvas)
            freedom_select_bounds = draw_freedom_select_button(canvas)

            # Add the Freedom Select handling code HERE:
            if state.selecting:
                if is_thumb_index_click_near_button(hand_landmarks, (0, 0, w, h), w, h):
                    if state.selection_start is not None:
                        state.complete_selection()
                else:
                    state.update_selection(smoothed_x, smoothed_y)
                
                if len(state.current_selection) > 1:
                    pts = np.array(state.current_selection, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(canvas, [pts], isClosed=False, color=(0, 255, 255), thickness=2)

            if state.selected_region is not None:
                state.move_selection(hand_landmarks, w, h)
                contours, _ = cv2.findContours(state.selection_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(canvas, contours, -1, (0, 255, 0), 2)

            # Then continue with your existing hand landmark processing:
            
            # Draw the control panel on the canvas if it is visible
            panel_x, panel_y, panel_width, panel_height = draw_control_panel(canvas)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                h, w, _ = canvas.shape
                
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                index_dip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP]
                index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
                index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
                smoothed_x, smoothed_y = state.smoother.smooth(index_x, index_y)

                # Draw the cursor (index finger) on the canvas
                cv2.circle(canvas, (smoothed_x, smoothed_y), 10, (255, 0, 0), -1)

                # Update control panel values based on hand position if the control panel is visible
                if state.control_panel_visible:
                    update_control_panel_values(state, smoothed_x, smoothed_y, panel_x, panel_y, panel_width, panel_height)

                # Check for C button click to toggle control panel visibility
                if is_thumb_index_click_near_button(hand_landmarks, control_button_bounds, w, h):
                    state.control_panel_visible = not state.control_panel_visible
                    time.sleep(0.3)  # Add a small delay to prevent multiple toggles

                # Check for D button click to toggle drawing mode
                if is_thumb_index_click_near_button(hand_landmarks, drawing_button_bounds, w, h):
                    state.drawing_mode_active = not state.drawing_mode_active
                    if state.drawing_mode_active:
                        state.eraser_mode_active = False
                        state.selecting = False  # Add this line
                        state.cancel_selection()  # Add this line
                    time.sleep(0.3)  # Add a small delay to prevent multiple toggles
                
                # Check for new page button click
                if is_thumb_index_click_near_button(hand_landmarks, nav_buttons["new"], w, h):
                    state.add_new_page()
                    time.sleep(0.3)  # Add a small delay to prevent multiple activations

                # Check for next page button click
                if is_thumb_index_click_near_button(hand_landmarks, nav_buttons["next"], w, h):
                    state.switch_page("next")
                    time.sleep(0.3)  # Add a small delay to prevent multiple activations

                # Check for previous page button click
                if is_thumb_index_click_near_button(hand_landmarks, nav_buttons["prev"], w, h):
                    state.switch_page("prev")
                    time.sleep(0.3)  # Add a small delay to prevent multiple activations

                # Check for undo button click
                if is_thumb_index_click_near_button(hand_landmarks, undo_redo_buttons["undo"], w, h):
                    state.undo()
                    time.sleep(0.01)
                
                # Check for redo button click
                if is_thumb_index_click_near_button(hand_landmarks, undo_redo_buttons["redo"], w, h):
                    state.redo()
                    time.sleep(0.01)

                # Check for erase all button click
                if is_thumb_index_click_near_button(hand_landmarks, erase_all_button_bounds, w, h):
                    state.canvas = np.ones((550, 850, 3), dtype=np.uint8) * 255
                    state.pages[state.current_page_index] = state.canvas.copy()
                    time.sleep(0.3)  # Add a small delay to prevent multiple activations

                if is_thumb_index_click_near_button(hand_landmarks, freedom_select_bounds, w, h):
                    if state.selecting:
                        state.complete_selection()
                        state.selecting = False
                    else:
                        state.start_selection(smoothed_x, smoothed_y)
                    time.sleep(1)

                # Check for shape button clicks
                for shape_name, shape_bounds in shape_buttons.items():
                    if is_thumb_index_click_near_button(hand_landmarks, shape_bounds, w, h):
                        # Toggle shape mode off if already in shape mode with same shape
                        if state.shape_mode_active and state.selected_shape == shape_name:
                            state.shape_mode_active = False
                            state.selected_shape = None
                            state.selecting = False  # Add this line
                            state.cancel_selection()  # Add this line
                        else:
                            # Turn off other modes and enable shape mode
                            state.drawing_mode_active = False
                            state.eraser_mode_active = False
                            state.shape_mode_active = True
                            state.selected_shape = shape_name
                            state.selecting = False  # Add this line
                            state.cancel_selection()  # Add this line

                        break

                # Handle shape drawing
                if state.shape_mode_active and state.selected_shape:
                    if is_thumb_index_click_near_button(hand_landmarks, (0, 0, w, h), w, h):
                        if state.shape_start_point is None:
                            state.save_state()
                            state.shape_start_point = (smoothed_x, smoothed_y)
                        else:
                            draw_shape(state.pages[state.current_page_index], state.selected_shape, 
                                      state.shape_start_point, (smoothed_x, smoothed_y), 
                                      state.get_current_color(), state.default_thickness)
                            state.shape_start_point = None
                            state.canvas = state.pages[state.current_page_index].copy()  # Update canvas to reflect current page

                # Check for thumb-pinky touch to cycle VIBGYOR colors
                if check_thumb_pinky_touch(hand_landmarks):
                    if state.color_change_start_time is None:
                        state.color_change_start_time = time.time()
                    elif time.time() - state.color_change_start_time >= state.color_change_duration:
                        state.using_vibgyor = True
                        state.current_color_index = (state.current_color_index + 1) % len(state.vibgyor_colors)
                        state.color_change_start_time = None
                else:
                    state.color_change_start_time = None

                # Check for palm open gesture to toggle eraser mode
                if is_palm_open(hand_landmarks):
                    if state.palm_open_start_time is None:
                        state.palm_open_start_time = time.time()
                    elif time.time() - state.palm_open_start_time >= state.palm_open_detection_duration:
                        state.drawing_mode_active = False
                        state.eraser_mode_active = not state.eraser_mode_active
                        state.selecting = False  # Add this line
                        state.cancel_selection()  # Add this line
                        state.palm_open_start_time = None
                else:
                    state.palm_open_start_time = None

                # Check for pause drawing gesture
                if index_tip.y < index_dip.y and middle_tip.y < index_dip.y:
                    state.pause_drawing = True
                else:
                    state.pause_drawing = False

                # Only draw if drawing mode is active and not paused
                if (state.drawing_mode_active or state.eraser_mode_active) and not state.pause_drawing:
                    if state.last_point is None:
                        state.last_point = (smoothed_x, smoothed_y)
                    
                    if state.drawing_mode_active:
                        draw_smooth_line(state.last_point, 
                                      (smoothed_x, smoothed_y), 
                                      color=state.get_current_color(),
                                      thickness=state.default_thickness)
                    elif state.eraser_mode_active:
                        erase_area(state.canvas, (smoothed_x, smoothed_y))
                        cv2.circle(canvas, (smoothed_x, smoothed_y), 30, (0, 0, 0), 2)
                    
                    # Update the page data to save the changes
                    state.pages[state.current_page_index] = state.canvas.copy()
                    state.last_point = (smoothed_x, smoothed_y)
                else:
                    state.last_point = None

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
                
            elif key == ord('e'):  # Erase all
                state.canvas = np.ones((550, 850, 3), dtype=np.uint8) * 255
                state.pages[state.current_page_index] = state.canvas.copy()
                state.eraser_mode_active = True
                state.drawing_mode_active = False
                state.selecting = False
                state.cancel_selection()

            elif key == ord('d'):  # Toggle drawing mode
                state.drawing_mode_active = not state.drawing_mode_active
                if state.drawing_mode_active:
                    state.eraser_mode_active = False
                    state.selecting = False  # Add this line
                    state.cancel_selection()  # Add this line
     
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

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)

state = State()

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    main()

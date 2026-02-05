from typing import List, Dict, Tuple
import time
import math

class GestureEngine:
    def __init__(self, state):
        self.state = state
        self.last_click_time = 0
        self.click_cooldown = 0.5
        self.W, self.H = state.CANVAS_SIZE[:2] # 850, 550
        # Swap W, H because cv2 shape is (H, W) -> (550, 850)
        self.H, self.W = 550, 850

    def _is_clicked(self, landmarks, x1, y1, x2, y2):
        """Check if index finger is in box and we are pinching (click)."""
        idx = landmarks.get('index_finger_tip')
        thumb = landmarks.get('thumb_tip')
        
        if not idx or not thumb: return False
        
        # Check if index finger is inside bounds
        ix, iy = idx
        if not (x1 <= ix <= x2 and y1 <= iy <= y2):
            return False

        # Check pinch (distance between thumb and index)
        dist = math.sqrt((ix - thumb[0])**2 + (iy - thumb[1])**2)
        if dist < 40: # Threshold in pixels
            if time.time() - self.last_click_time > self.click_cooldown:
                self.last_click_time = time.time()
                return True
        return False

    def process(self, gestures: List[str], landmarks: Dict[str, Tuple[int, int]]):
        """Process gestures and landmarks for UI interaction."""
        
        # 1. UI Interactions (if landmarks available)
        if landmarks:
            # Control Panel Button (C)
            # x, y, w, h = 20, 550-70, 40, 40 -> y = 480
            if self._is_clicked(landmarks, 20, 480, 60, 520):
                self.state.control_panel_visible = not self.state.control_panel_visible
                
            # Drawing Mode Button (D) - y = 550-190 = 360
            if self._is_clicked(landmarks, 20, 360, 60, 400):
                # Toggle logic: simple tool switch for now
                if self.state.tool == 'pen': 
                    self.state.set_tool('eraser')
                else: 
                    self.state.set_tool('pen')

            # Erase All (EA) - y = 550-130 = 420
            if self._is_clicked(landmarks, 20, 420, 60, 460):
                self.state.erase_all()

            # Undo (U) - x = 850-50 = 800, y = 420
            if self._is_clicked(landmarks, 800, 420, 835, 455):
                self.state.undo()

            # Redo (R) - x = 800, y = 360
            if self._is_clicked(landmarks, 800, 360, 835, 395):
                self.state.redo()

            # Navigation
            # Prev: y = 300
            # New: y = 250
            # Next: y = 200
            if self._is_clicked(landmarks, 20, 300, 60, 340): self.state.switch_page("prev")
            if self._is_clicked(landmarks, 20, 250, 60, 290): self.state.add_new_page()
            if self._is_clicked(landmarks, 20, 200, 60, 240): self.state.switch_page("next")
            
            # Shapes (Right side center)
            # Center y = 275 (half of 550) - 100 = 175
            # x = 800
            shapes = ["Oval", "Circle", "Square", "Triangle"]
            for i, shape in enumerate(shapes):
                sy = 175 + i * 45
                if self._is_clicked(landmarks, 800, sy, 835, sy+35):
                    self.state.shape_mode_active = True
                    self.state.selected_shape = shape
                    self.state.tool = 'shape' # Implicit tool switch

        # 2. Drawing Logic
        if landmarks:
            idx_tip = landmarks.get('index_finger_tip')
            if idx_tip:
                ix, iy = idx_tip
                
                # Check D button again: if we are in drawing mode (and not hovering a button), draw
                if self.state.tool == 'pen' or self.state.tool == 'eraser':
                    # Simple smoothing could go here, for now direct draw
                    color = self.state.color if self.state.tool == 'pen' else self.state.background_color
                    thickness = self.state.thickness if self.state.tool == 'pen' else 30
                    
                    import cv2
                    if self.state.last_point:
                        cv2.line(self.state.canvas, self.state.last_point, (ix, iy), color, thickness)
                    
                    # Store last point
                    self.state.last_point = (ix, iy)
                else:
                    self.state.last_point = None
            else:
                self.state.last_point = None

        # 3. Global Gestures (Backwards compatibility)
        for g in gestures:
            if g == "FIST":
                # Maybe stop drawing? handled by frontend usually, but backend state has 'tool'
                self.state.last_point = None # Stop stripe
            elif g == "THUMB_PINKY":
                if time.time() - self.last_click_time > self.click_cooldown:
                    self.state.cycle_color()
                    self.last_click_time = time.time()

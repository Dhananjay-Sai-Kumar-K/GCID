
import numpy as np
import time
from enum import Enum, IntEnum, auto

class GestureType(Enum):
    NO_HAND = auto()
    IDLE = auto()      # Hand detected but no specific intent
    POINTING = auto()  # Default state: Index finger guiding the cursor
    PINCH = auto()     # Action state: Drawing / Selecting
    OPEN_PALM = auto() # Command state: Pause (NOT erasing)

class GestureState(Enum):
    START = auto() # Frame 0 of the gesture
    HOLD = auto()  # Frame 1+ of the gesture
    END = auto()   # When transitioning away from a gesture

class GestureEvent:
    """
    Represents a high-level user intent.
    Decouples 'what the hand is doing' from 'what the app triggers'.
    """
    def __init__(self, gesture_type, state, x=0.0, y=0.0, landmarks=None):
        self.type = gesture_type
        self.state = state
        self.x = x  # Normalized (0.0 - 1.0)
        self.y = y  # Normalized (0.0 - 1.0)
        self.time = time.time()
        self.landmarks = landmarks

    def __repr__(self):
        return f"Event({self.type.name}, {self.state.name}, x={self.x:.2f}, y={self.y:.2f})"


# Hand landmark indices (MediaPipe standard)
# Using IntEnum to allow both direct integer access and .value compatibility
class HandLandmark(IntEnum):
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


class GestureInterpreter:
    """
    Stateful gesture interpreter with pinch latching.
    
    Key principles (FIX 1):
    - PINCH_START fires ONCE when thumb-index pinch is detected
    - PINCH_HOLD fires EVERY frame while pinch is active
    - PINCH_END fires ONLY when pinch is clearly released
    - Pinch is NOT cancelled by other fingers, jitter, or hand rotation
    """
    
    def __init__(self):
        self.current_gesture = GestureType.NO_HAND
        self.state_start_time = 0
        
        # --- Pinch Latching State Machine (FIX 1) ---
        self._pinch_latched = False
        self._pinch_release_frames = 0  # Counter for consistent release detection
        
        # --- Configurable Thresholds (Normalized) ---
        # Hysteresis for stable pinch detection
        self.PINCH_ENTER_THRESH = 0.045   # Strict to enter pinch (tighter)
        self.PINCH_EXIT_THRESH = 0.10     # Loose to exit pinch (more forgiving)
        
        # Debounce: Require consistent release for N frames before ending pinch
        self.PINCH_RELEASE_FRAMES_REQUIRED = 3
        
        # Safety buffer for state switching
        self.min_state_duration = 0.05 # 50ms stability required
        
        # Track last valid position for stability
        self._last_valid_x = 0.5
        self._last_valid_y = 0.5

    def process(self, hand_landmarks) -> GestureEvent:
        """
        Main pipeline: Raw Landmarks -> Intent Event
        
        FIX 1: Implements proper pinch latching with debounce
        """
        if not hand_landmarks:
            # Hand lost - if we were pinching, send END event
            if self._pinch_latched:
                self._pinch_latched = False
                self._pinch_release_frames = 0
                return GestureEvent(GestureType.PINCH, GestureState.END, 
                                   self._last_valid_x, self._last_valid_y)
            return self._transition_to(GestureType.NO_HAND, 0.0, 0.0)

        # 1. Extract Key Coordinates using numeric indices
        thumb_tip = hand_landmarks.landmark[HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[HandLandmark.INDEX_FINGER_TIP]

        # 2. Analyze Geometry
        pinch_dist = np.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        is_palm_open = self._check_palm_open(hand_landmarks)
        
        # Calculate cursor position (midpoint for pinch, index_tip otherwise)
        if self._pinch_latched or pinch_dist < self.PINCH_ENTER_THRESH:
            # Use midpoint for precision during pinch
            target_x = (thumb_tip.x + index_tip.x) / 2
            target_y = (thumb_tip.y + index_tip.y) / 2
        else:
            target_x, target_y = index_tip.x, index_tip.y
        
        # Store last valid position for END events
        self._last_valid_x = target_x
        self._last_valid_y = target_y
        
        # 3. Pinch State Machine (FIX 1: Latching with Debounce)
        if self._pinch_latched:
            # Currently in pinch - check for release
            if pinch_dist > self.PINCH_EXIT_THRESH:
                self._pinch_release_frames += 1
                
                # Only end pinch after consistent release
                if self._pinch_release_frames >= self.PINCH_RELEASE_FRAMES_REQUIRED:
                    self._pinch_latched = False
                    self._pinch_release_frames = 0
                    return GestureEvent(GestureType.PINCH, GestureState.END, 
                                       target_x, target_y, hand_landmarks)
            else:
                # Still pinching - reset release counter
                self._pinch_release_frames = 0
            
            # Continue pinch HOLD - this fires EVERY FRAME while pinched
            return GestureEvent(GestureType.PINCH, GestureState.HOLD, 
                               target_x, target_y, hand_landmarks)
        else:
            # Not currently pinching - check for entry
            if pinch_dist < self.PINCH_ENTER_THRESH:
                self._pinch_latched = True
                self._pinch_release_frames = 0
                self.current_gesture = GestureType.PINCH
                self.state_start_time = time.time()
                return GestureEvent(GestureType.PINCH, GestureState.START, 
                                   target_x, target_y, hand_landmarks)
        
        # 4. Non-pinch gesture detection (only when not latched)
        # FIX 3: OPEN_PALM does NOT trigger eraser - it's just detected for pause functionality
        if is_palm_open:
            return self._transition_to(GestureType.OPEN_PALM, target_x, target_y, hand_landmarks)
        
        # Default: Pointing (cursor movement)
        return self._transition_to(GestureType.POINTING, target_x, target_y, hand_landmarks)

    def _check_palm_open(self, landmarks):
        """
        Checks if all fingers are extended relative to their PIP joints.
        Used for 'Pause' gesture - NOT for erasing (FIX 3).
        """
        fingers = [
            (HandLandmark.INDEX_FINGER_TIP, HandLandmark.INDEX_FINGER_PIP),
            (HandLandmark.MIDDLE_FINGER_TIP, HandLandmark.MIDDLE_FINGER_PIP),
            (HandLandmark.RING_FINGER_TIP, HandLandmark.RING_FINGER_PIP),
            (HandLandmark.PINKY_TIP, HandLandmark.PINKY_PIP)
        ]
        
        extended_count = 0
        for tip_idx, pip_idx in fingers:
            if landmarks.landmark[tip_idx].y < landmarks.landmark[pip_idx].y:
                extended_count += 1
                
        return extended_count >= 4

    def _transition_to(self, new_gesture, x, y, landmarks=None):
        """
        Manages state integrity. Ensures we send START/HOLD/END correctly.
        """
        current_time = time.time()
        
        if new_gesture != self.current_gesture:
            # Gesture changed - send START for new gesture
            self.current_gesture = new_gesture
            self.state_start_time = current_time
            return GestureEvent(new_gesture, GestureState.START, x, y, landmarks)
            
        return GestureEvent(new_gesture, GestureState.HOLD, x, y, landmarks)
    
    def is_pinch_active(self):
        """Helper to check pinch latch status from external code."""
        return self._pinch_latched
    
    def force_end_pinch(self):
        """Force end pinch state (e.g., when tool is switched)."""
        self._pinch_latched = False
        self._pinch_release_frames = 0

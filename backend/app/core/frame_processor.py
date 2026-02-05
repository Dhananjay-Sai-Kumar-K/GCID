import cv2
import numpy as np
from typing import Tuple, Dict, List
from app.utils.encoding import frame_to_base64

# mediapipe is optional for the server to start; gracefully degrade if not available
try:
    import mediapipe as mp
except Exception:
    mp = None


class FrameProcessor:
    """Read frames from camera, run MediaPipe hands and detect simple gestures.

    read_frame() -> Tuple[str, Dict[str, Tuple[float,float]], List[str]]
    returns (base64_frame, landmarks_dict, gestures_list)
    """

    def __init__(self, camera_index: int = 0):
        self.cap = cv2.VideoCapture(camera_index)

        if mp is not None:
            try:
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    max_num_hands=1,
                    min_detection_confidence=0.6,
                    min_tracking_confidence=0.6
                )
            except AttributeError:
                print("Warning: MediaPipe solutions not found. Hand tracking will be disabled.")
                self.mp_hands = None
                self.hands = None
        else:
            self.mp_hands = None
            self.hands = None

    # --- simple gesture detectors ---
    @staticmethod
    def _is_palm_open(hand_landmarks) -> bool:
        try:
            tips = [
                hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP],
                hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP],
            ]
            # fingertips are above their respective tip-2 landmarks in an open palm
            return all(tip.y < hand_landmarks.landmark[idx - 2].y for idx, tip in [
                (self.mp_hands.HandLandmark.THUMB_TIP, tips[0]),
                (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, tips[1]),
                (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, tips[2]),
                (self.mp_hands.HandLandmark.RING_FINGER_TIP, tips[3]),
                (self.mp_hands.HandLandmark.PINKY_TIP, tips[4]),
            ])
        except Exception:
            return False

    @staticmethod
    def _thumb_pinky_touch(hand_landmarks) -> bool:
        thumb = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        pinky = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        d = np.sqrt((thumb.x - pinky.x) ** 2 + (thumb.y - pinky.y) ** 2 + (thumb.z - pinky.z) ** 2)
        return d < 0.08

    @staticmethod
    def _is_pinch(hand_landmarks) -> bool:
        thumb = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        d = np.sqrt((thumb.x - index.x) ** 2 + (thumb.y - index.y) ** 2)
        return d < 0.06

    @staticmethod
    def _is_fist(hand_landmarks) -> bool:
        # simplified heuristic: fingertip y greater (lower) than pip for fingers
        tips = [
            hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP],
        ]
        try:
            return all(tip.y > hand_landmarks.landmark[i - 2].y for i, tip in [
                (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, tips[0]),
                (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, tips[1]),
                (self.mp_hands.HandLandmark.RING_FINGER_TIP, tips[2]),
                (self.mp_hands.HandLandmark.PINKY_TIP, tips[3]),
            ])
        except Exception:
            return False

    def _landmarks_dict(self, hand_landmarks, img_w: int, img_h: int) -> Dict[str, Tuple[int, int]]:
        d = {}
        for name in [
            'THUMB_TIP', 'INDEX_FINGER_TIP', 'MIDDLE_FINGER_TIP', 'RING_FINGER_TIP', 'PINKY_TIP'
        ]:
            lm = hand_landmarks.landmark[getattr(self.mp_hands.HandLandmark, name)]
            d[name.lower()] = (int(lm.x * img_w), int(lm.y * img_h))
        return d

    def read_frame(self) -> Tuple[str, Dict[str, Tuple[int, int]], List[str]]:
        success, frame = self.cap.read()
        if not success:
            # Create a black placeholder image (480x640)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Camera Error", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # return None, {}, []  <-- Don't disconnect


        frame = cv2.flip(frame, 1)
        # Resize to match canvas size (850x550)
        frame = cv2.resize(frame, (850, 550))
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.hands:
            results = self.hands.process(rgb)
        else:
            results = type('obj', (object,), {'multi_hand_landmarks': None})

        gestures = []
        landmarks = {}

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            landmarks = self._landmarks_dict(hand_landmarks, w, h)

            if self._is_palm_open(hand_landmarks):
                gestures.append("OPEN_PALM")
            if self._is_fist(hand_landmarks):
                gestures.append("FIST")
            if self._thumb_pinky_touch(hand_landmarks):
                gestures.append("THUMB_PINKY")
            if self._is_pinch(hand_landmarks):
                gestures.append("PINCH")

        encoded = frame_to_base64(frame)
        return encoded, landmarks, gestures

    def release(self):
        self.cap.release()

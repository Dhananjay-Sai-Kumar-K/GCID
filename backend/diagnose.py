import cv2
import sys
import time

print("--- DIAGNOSTIC START ---")
print(f"Python Version: {sys.version}")

try:
    import mediapipe as mp
    print("✅ MediaPipe imported successfully.")
    print(f"MediaPipe Version: {mp.__version__}")
except ImportError as e:
    print(f"❌ MediaPipe Import Failed: {e}")
    sys.exit(1)

try:
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        max_num_hands=1
    )
    print("✅ MediaPipe Hands initialized.")
except Exception as e:
    print(f"❌ MediaPipe Hands Init Failed: {e}")
    # If attribute error, it might be the version issue
    if "solutions" in str(e):
        print("💡 Hint: Try 'pip install mediapipe --upgrade'")
    sys.exit(1)

print("\n--- CAMERA TEST ---")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Could not open camera (Index 0). Trying Index 1...")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("❌ Could not open camera (Index 1). Exiting.")
        sys.exit(1)

print("✅ Camera opened successfully.")

print("\n--- VISUAL TEST (Press 'q' to quit) ---")
print("Attempts to detect hands... Show your hand to the camera!")

frame_count = 0
detect_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame.")
        break

    # Flip for mirror view
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    # Convert to RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process
    results = hands.process(rgb)
    
    if results.multi_hand_landmarks:
        detect_count += 1
        status = "HAND DETECTED!"
        color = (0, 255, 0)
        
        # Draw landmarks
        for hand_landmarks in results.multi_hand_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Print index finger tip coordinates
            idx_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            status += f" Index: ({int(idx_tip.x*w)}, {int(idx_tip.y*h)})"

    else:
        status = "No Hand..."
        color = (0, 0, 255)

    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.imshow('GCID Diagnostic (Press q to quit)', frame)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break
    
    frame_count += 1
    if frame_count % 30 == 0:
        print(f"Frame {frame_count}: {status}")

cap.release()
cv2.destroyAllWindows()
print(f"\n--- REPORT ---")
print(f"Total Frames: {frame_count}")
print(f"Hand Detections: {detect_count}")
if detect_count == 0:
    print("❌ NO HANDS DETECTED. Check lighting or camera position.")
else:
    print("✅ HANDS DETECTED successfully.")

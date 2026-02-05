import mediapipe as mp
try:
    print(f"MediaPipe version: {mp.__version__}")
    print(f"Solutions: {dir(mp.solutions)}")
    hands = mp.solutions.hands
    print("Hands module found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

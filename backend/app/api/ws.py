from fastapi import APIRouter, WebSocket
import asyncio
import json
from typing import Any

from app.core.state import State
from app.core.gesture_engine import GestureEngine
from app.core.frame_processor import FrameProcessor

router = APIRouter()


async def _receive_commands(ws: WebSocket, state: State):
    """Background task that receives client messages and applies commands to state."""
    try:
        while True:
            msg = await ws.receive_text()
            try:
                payload = json.loads(msg)
            except Exception:
                continue

            if payload.get("type") == "command":
                action = payload.get("action")
                params = payload.get("params", {})

                # Standard commands
                if action == "undo":
                    state.undo()
                elif action == "redo":
                    state.redo()
                elif action == "new_page":
                    state.add_new_page()
                elif action == "erase_all":
                    state.erase_all()
                elif action == "set_tool":
                    state.set_tool(params.get("tool"))
                elif action == "set_color":
                    state.set_color(tuple(params.get("color", state.color)))
                elif action == "set_thickness":
                    state.set_thickness(params.get("thickness", state.thickness))

    except Exception:
        # When client disconnects, receive loop will raise; we exit silently
        return


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    state = State()
    gesture_engine = GestureEngine(state)
    processor = FrameProcessor()

    # Start receiver task
    receiver_task = asyncio.create_task(_receive_commands(ws, state))

    try:
        while True:
            frame_b64, landmarks, gestures = processor.read_frame()

            if frame_b64 is None:
                break

            # Apply gestures to state
            if gestures or landmarks:
                gesture_engine.process(gestures, landmarks)

            # Send frame + lightweight state
            await ws.send_json({
                "type": "frame",
                "image": frame_b64,
                "landmarks": landmarks,
                "gestures": gestures,
            })

            await ws.send_json({
                "type": "state",
                **state.serialize()
            })

            await asyncio.sleep(1 / 30)

    except Exception as e:
        print("WebSocket closed:", e)

    finally:
        receiver_task.cancel()
        processor.release()
        processor.release()
        try:
            await ws.close()
        except RuntimeError:
            pass  # Already closed

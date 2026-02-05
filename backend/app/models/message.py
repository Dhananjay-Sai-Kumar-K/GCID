from pydantic import BaseModel
from typing import List, Any, Dict


class FrameMessage(BaseModel):
    type: str = "frame"
    image: str   # base64 encoded image
    landmarks: Dict[str, Any] = {}
    gestures: List[str] = []


class StateMessage(BaseModel):
    type: str = "state"
    tool: str
    color: List[int]
    thickness: int
    page_index: int
    total_pages: int
    canvas: str  # base64 encoded canvas


class CommandMessage(BaseModel):
    type: str = "command"
    action: str
    params: Dict[str, Any] = {}

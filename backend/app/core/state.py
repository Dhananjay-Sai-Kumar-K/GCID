import numpy as np
from typing import Tuple, Dict, Any
from app.utils.encoding import frame_to_base64


class State:
    """Server-side representation of the drawing state.

    Stores lightweight canvas pages (as numpy arrays), undo/redo stacks,
    drawing tool, color and thickness. Provides methods to manipulate
    the canvas and a JSON-serializable `serialize()` method.
    """

    CANVAS_SIZE = (550, 850, 3)

    def __init__(self):
        self.tool: str = "pen"
        self.color: Tuple[int, int, int] = (255, 0, 0)
        self.thickness: int = 5

        # Canvas pages are stored as numpy arrays (BGR)
        self.pages = [np.ones(self.CANVAS_SIZE, dtype=np.uint8) * 255]
        self.current_page_index = 0

        # Undo/redo stacks store copies of pages
        self.undo_stack = []
        self.redo_stack = []

        # Simple color palette for cycles
        self.palette = [
            (148, 0, 211),    # Violet
            (75, 0, 130),     # Indigo
            (255, 0, 0),      # Blue
            (0, 255, 0),      # Green
            (0, 255, 255),    # Yellow
            (0, 165, 255),    # Orange
            (0, 0, 255)       # Red
        ]
        self._palette_index = 0

        # --- Advanced Features (from V1) ---
        self.shape_mode_active = False
        self.selected_shape = None
        self.shape_start_point = None
        self.last_point = None  # Track last drawing point
        
        # Selection / Freedom Select
        self.selecting = False
        self.selection_start = None
        self.selection_mask = None
        self.selected_region = None
        self.current_selection = []
        self.drag_start_pos = None
        self.original_selection_pos = None

        # Control Panel State
        self.control_panel_visible = False
        self.background_color = (255, 255, 255) # BGR
        self.smoothing_factor = 0.5

    # --- Canvas helpers ---
    @property
    def canvas(self) -> np.ndarray:
        return self.pages[self.current_page_index]

    def save_state(self) -> None:
        self.undo_stack.append(self.canvas.copy())
        self.redo_stack.clear()

    def undo(self) -> None:
        if self.undo_stack:
            self.redo_stack.append(self.canvas.copy())
            self.pages[self.current_page_index] = self.undo_stack.pop()

    def redo(self) -> None:
        if self.redo_stack:
            self.undo_stack.append(self.canvas.copy())
            self.pages[self.current_page_index] = self.redo_stack.pop()

    def add_new_page(self) -> None:
        self.pages.append(np.ones(self.CANVAS_SIZE, dtype=np.uint8) * 255)
        self.current_page_index = len(self.pages) - 1

    def switch_page(self, direction: str) -> None:
        if direction == "next" and self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
        elif direction == "prev" and self.current_page_index > 0:
            self.current_page_index -= 1

    def erase_all(self) -> None:
        self.save_state()
        self.pages[self.current_page_index][:] = 255

    # --- Tool setters ---
    def set_tool(self, tool: str) -> None:
        self.tool = tool

    def set_color(self, color) -> None:
        self.color = color

    def set_thickness(self, value: int) -> None:
        self.thickness = max(1, int(value))

    def cycle_color(self) -> None:
        self._palette_index = (self._palette_index + 1) % len(self.palette)
        self.color = self.palette[self._palette_index]

    # --- Serialization ---
    def get_canvas_base64(self) -> str:
        # Create a copy of the canvas for display
        display_canvas = self.canvas.copy()
        
        # Draw UI elements on top (imported locally to avoid circular imports)
        from app.core.ui_drawer import draw_all_ui
        draw_all_ui(display_canvas, self)
        
        # Convert composite canvas to base64
        return frame_to_base64(display_canvas)

    def serialize(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "color": list(self.color),
            "thickness": self.thickness,
            "page_index": self.current_page_index,
            "total_pages": len(self.pages),
            "canvas": self.get_canvas_base64(),
            "shape_mode": self.shape_mode_active,
            "selected_shape": self.selected_shape,
            "control_panel": self.control_panel_visible
        }

    # --- Advanced Logic ---
    def update_background(self, b, g, r):
        """Update canvas background color."""
        self.background_color = (b, g, r)
        for page in self.pages:
            # Only update pixels that were originally white/background?
            # For simplicity in this implementation, we might just flood fill or set all
            pass # Creating a true layer system is complex, for now we store the attribute

    def start_selection(self, x, y):
        self.selecting = True
        self.selection_start = (x, y)
        self.selection_mask = np.zeros(self.CANVAS_SIZE[:2], dtype=np.uint8)
        self.current_selection = []
        self.save_state()

    def update_selection(self, x, y):
        import cv2
        if self.selection_start is None:
            self.selection_start = (x, y)
        self.current_selection.append((x, y))
        # Draw on mask if multiple points
        if len(self.current_selection) > 1:
            pts = np.array(self.current_selection, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(self.selection_mask, [pts], 255)

    def complete_selection(self):
        import cv2
        if len(self.current_selection) > 2:
            pts = np.array(self.current_selection, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(self.selection_mask, [pts], 255)
            self.selected_region = self.canvas.copy()
            # Mask out non-selected area in the region buffer
            self.selected_region[self.selection_mask == 0] = 0 
            self.current_selection = []
            self.save_state()
        else:
            self.cancel_selection()

    def cancel_selection(self):
        self.selecting = False
        self.selection_start = None
        self.selection_mask = None
        self.current_selection = []
        self.selected_region = None

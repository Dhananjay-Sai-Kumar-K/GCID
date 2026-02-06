import cv2
import numpy as np

COLOR_BUTTON = (46, 40, 219)
COLOR_TEXT = (255, 255, 255)

def draw_control_panel_button(canvas, state):
    button_x, button_y = 20, canvas.shape[0] - 70
    button_w, button_h = 40, 40 
    cv2.rectangle(canvas, (button_x, button_y), 
                         (button_x + button_w, button_y + button_h), 
                         COLOR_BUTTON, -1)
    cv2.putText(canvas, 'C', (button_x + 13, button_y + 25), 
                cv2.FONT_HERSHEY_TRIPLEX, 1, COLOR_TEXT, 2)
    return (button_x, button_y, button_x + button_w, button_y + button_h)

def draw_drawing_mode_button(canvas, state):
    button_w, button_h = 40, 40
    button_x = 20
    button_y = canvas.shape[0] - 190
    
    color = (0, 200, 0) if state.shape_mode_active or True else (0, 0, 200) # Simplified logic
    
    cv2.rectangle(canvas, (button_x, button_y), 
                        (button_x + button_w, button_y + button_h), 
                        color, -1)
    
    cv2.putText(canvas, 'D', (button_x + 13, button_y + 25), 
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, COLOR_TEXT, 2)
    
    return (button_x, button_y, button_x + button_w, button_y + button_h)

def draw_erase_all_button(canvas, state):
    button_w, button_h = 40, 40
    button_x = 20
    button_y = canvas.shape[0] - 130
    cv2.rectangle(canvas, (button_x, button_y), 
                         (button_x + button_w, button_y + button_h), 
                         COLOR_BUTTON, -1)  
    cv2.putText(canvas, 'EA', (button_x + 8, button_y + 25), 
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, COLOR_TEXT, 2)
    return (button_x, button_y, button_x + button_w, button_y + button_h)

def draw_undo_redo_buttons(canvas, state):
    button_x = canvas.shape[1] - 50
    button_w, button_h = 35, 35
    font_scale, thickness = 1, 2
    
    buttons = {"undo": "U", "redo": "R"}
    button_y_positions = {
        "undo": canvas.shape[0] - 130,
        "redo": canvas.shape[0] - 190
    }
    button_bounds = {}

    for key, text in buttons.items():
        button_y = button_y_positions[key]
        cv2.rectangle(canvas, (button_x, button_y),
                      (button_x + button_w, button_y + button_h),
                      COLOR_BUTTON, -1)
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        text_x = button_x + (button_w - text_size[0]) // 2
        text_y = button_y + (button_h + text_size[1]) // 2
        cv2.putText(canvas, text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLOR_TEXT, thickness)
        button_bounds[key] = (button_x, button_y, button_x + button_w, button_y + button_h)

    return button_bounds

def draw_navigation_buttons(canvas, state):
    button_x, button_w, button_h = 20, 40, 40
    prev_button_y = canvas.shape[0] - 250
    
    # Prev
    prev_triangle = np.array([
        [button_x + button_w // 2, prev_button_y + button_h - 10],
        [button_x + 10, prev_button_y + 10],
        [button_x + button_w - 10, prev_button_y + 10]
    ])
    cv2.fillPoly(canvas, [prev_triangle], COLOR_BUTTON)

    # New
    new_button_y = prev_button_y - 50
    cv2.rectangle(canvas, (button_x, new_button_y),
                  (button_x + button_w, new_button_y + button_h),
                  COLOR_BUTTON, -1)
    cv2.putText(canvas, '+', (button_x + 13, new_button_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 2)

    # Next
    next_button_y = new_button_y - 50
    next_triangle = np.array([
        [button_x + button_w // 2, next_button_y + 10],
        [button_x + 10, next_button_y + button_h - 10],
        [button_x + button_w - 10, next_button_y + button_h - 10]
    ])
    cv2.fillPoly(canvas, [next_triangle], COLOR_BUTTON)

    return {
        "prev": (button_x, prev_button_y, button_x + button_w, prev_button_y + button_h),
        "new": (button_x, new_button_y, button_x + button_w, new_button_y + button_h),
        "next": (button_x, next_button_y, button_x + button_w, next_button_y + button_h)
    }

def draw_shapes_button(canvas, state):
    button_x, button_y = canvas.shape[1] - 50, canvas.shape[0] // 2 - 100  
    button_w, button_h = 35, 35
    shape_bounds = {}
    shapes = ["Oval", "Circle", "Square", "Triangle"]

    for i, shape in enumerate(shapes):
        shape_button_y = button_y + i * (button_h + 10)
        center = (button_x + button_w // 2, shape_button_y + button_h // 2)
        fill_color = COLOR_BUTTON
        if state.shape_mode_active and state.selected_shape == shape:
            fill_color = (0, 128, 255)
            
        cv2.rectangle(canvas, (button_x, shape_button_y), 
                      (button_x + button_w, shape_button_y + button_h), 
                      fill_color, -1)

        if shape == "Oval":
            cv2.ellipse(canvas, center, (12, 6), 0, 0, 360, (255, 255, 255), 2)
        elif shape == "Circle":
            cv2.circle(canvas, center, 8, (255, 255, 255), 2)
        elif shape == "Square":
            cv2.rectangle(canvas, (center[0] - 8, center[1] - 8), 
                          (center[0] + 8, center[1] + 8), (255, 255, 255), 2)
        elif shape == "Triangle":
            pts = np.array([[center[0], center[1] - 8], 
                            [center[0] - 8, center[1] + 8], 
                            [center[0] + 8, center[1] + 8]], np.int32)
            cv2.polylines(canvas, [pts], isClosed=True, color=(255, 255, 255), thickness=2)
            
        shape_bounds[shape] = (button_x, shape_button_y, button_x + button_w, shape_button_y + button_h)

    return shape_bounds

def draw_control_panel(canvas, state):
    if state.control_panel_visible:
        panel_width, panel_height = 200, 400
        panel_x = canvas.shape[1] - panel_width - 20
        panel_y = 20
        cv2.rectangle(canvas, (panel_x, panel_y), 
                             (panel_x + panel_width, panel_y + panel_height), 
                             (200, 200, 200), -1)
        # (Simplified control panel drawing - full implementation would reproduce all sliders)
        cv2.putText(canvas, "Controls", (panel_x + 10, panel_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
        return (panel_x, panel_y, panel_width, panel_height)
    return None

def draw_all_ui(canvas, state):
    """Draws all UI elements onto the provided canvas."""
    draw_control_panel_button(canvas, state)
    draw_drawing_mode_button(canvas, state)
    draw_erase_all_button(canvas, state)
    draw_undo_redo_buttons(canvas, state)
    draw_navigation_buttons(canvas, state)
    draw_shapes_button(canvas, state)
    draw_control_panel(canvas, state)
    
    # Mode Indicator
    mode_text = "Drawing"
    if state.shape_mode_active: mode_text = f"Shape: {state.selected_shape}"
    elif state.tool == 'eraser': mode_text = "Eraser"
    
    cv2.putText(canvas, f"Mode: {mode_text}", (10, 55), 
                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 255), 1)
    
    # Page Info
    cv2.putText(canvas, f"Page: {state.current_page_index + 1}/{len(state.pages)}", (10, 30), 
                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 255), 1)

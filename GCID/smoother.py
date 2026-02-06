
import time
import math

class SpeedAdaptiveSmoother:
    def __init__(self, min_alpha=0.1, max_alpha=0.9, min_speed=50.0, max_speed=1000.0):
        """
        Adaptive Exponential Moving Average Smoother.
        
        Args:
            min_alpha: Alpha at low speeds (smoothing factor). Lower = more smoothing.
            max_alpha: Alpha at high speeds (responsiveness). Higher = less lag.
            min_speed: Speed (pixels/sec) below which min_alpha is used.
            max_speed: Speed (pixels/sec) above which max_alpha is used.
        """
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.min_speed = min_speed
        self.max_speed = max_speed
        
        self.last_x = None
        self.last_y = None
        self.last_time = None
        self.prev_smoothed_x = None
        self.prev_smoothed_y = None

    def reset(self, x, y):
        """Snap to a position, confusing history."""
        self.last_x = x
        self.last_y = y
        self.last_time = time.time()
        self.prev_smoothed_x = x
        self.prev_smoothed_y = y
        return x, y

    def update(self, x, y, canvas_w=None, canvas_h=None):
        current_time = time.time()
        
        if self.prev_smoothed_x is None:
            return self.reset(x, y)
            
        dt = current_time - self.last_time
        if dt <= 0:
            return int(self.prev_smoothed_x), int(self.prev_smoothed_y)
            
        # 1. Calculate raw speed (pixels per second)
        dx = x - self.last_x
        dy = y - self.last_y
        dist = math.sqrt(dx*dx + dy*dy)
        speed = dist / dt
        
        # 2. Map speed to alpha
        # Clamp speed to range
        speed_factor = (speed - self.min_speed) / (self.max_speed - self.min_speed)
        speed_factor = max(0.0, min(1.0, speed_factor))
        
        # Interpolate alpha (Base Alpha)
        alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * speed_factor
        
        # 3. EDGE-AWARE TUNING (Critical Fix 1)
        if canvas_w and canvas_h:
            # Normalize position (0 to 1)
            nx = x / canvas_w
            ny = y / canvas_h
            
            # Distance to nearest edge (0.0 = on edge, 0.5 = center)
            edge_dist_x = min(nx, 1.0 - nx)
            edge_dist_y = min(ny, 1.0 - ny)
            min_edge_dist = min(edge_dist_x, edge_dist_y)
            
            # Threshold: 15% (0.15)
            EDGE_THRESHOLD = 0.15
            
            if min_edge_dist < EDGE_THRESHOLD:
                # We are near an edge -> Ramp down alpha
                # factor goes 0.0 (at edge) to 1.0 (at threshold)
                edge_factor = min_edge_dist / EDGE_THRESHOLD
                
                # Apply penalty: Reduce alpha by up to 70% at the very edge
                # But ensure we don't go below absolute min stability value (e.g. 0.05)
                edge_multiplier = 0.3 + (0.7 * edge_factor) 
                alpha *= edge_multiplier
                
        # 4. Apply EMA
        smoothed_x = alpha * x + (1 - alpha) * self.prev_smoothed_x
        smoothed_y = alpha * y + (1 - alpha) * self.prev_smoothed_y
        
        # Update state
        self.last_x = x
        self.last_y = y
        self.last_time = current_time
        self.prev_smoothed_x = smoothed_x
        self.prev_smoothed_y = smoothed_y
        
        return int(smoothed_x), int(smoothed_y)

import time
import math

class Tracker:
    def __init__(self):
        # Dict: text_id -> { 'bbox': [], 'last_seen': float, 'center': (x,y) }
        self.targets = {}
        self.grace_period = 0.5 # Seconds to keep target "alive" after losing visual
        
        # Frame dimensions (Assumed from Pi default, can be updated)
        self.width = 640
        self.height = 480
        
    def update(self, detections):
        """
        Update tracker with new detections from CV.
        detections: List of dicts {'text': str, 'bbox': [[x,y]...]}
        """
        now = time.time()
        
        # Mark all as not seen (we rely on timestamp to know if it's current)
        # We don't delete immediately, we let get_active handle the filtering
        
        for det in detections:
            text_id = det['text']
            bbox = det['bbox']
            
            # Calculate Center
            if len(bbox) == 4:
                # Average of 4 corners
                cx = sum(p[0] for p in bbox) / 4
                cy = sum(p[1] for p in bbox) / 4
                
                self.targets[text_id] = {
                    'bbox': bbox,
                    'center': (cx, cy),
                    'last_seen': now
                }
                
    def get_active_targets(self):
        """Returns list of targets that are currently visible or within grace period."""
        now = time.time()
        active = []
        
        # Prune old targets
        to_remove = []
        
        for text_id, data in self.targets.items():
            if now - data['last_seen'] < self.grace_period:
                active.append({
                    'id': text_id,
                    **data
                })
            else:
                # Optional: Remove extremely old targets to keep memory clean
                if now - data['last_seen'] > 5.0:
                    to_remove.append(text_id)
                    
        for tr in to_remove:
            del self.targets[tr]
            
        return active

    def get_crosshair_targets(self, threshold=50):
        """
        Returns list of targets currently under the crosshair.
        threshold: pixels from center
        """
        active = self.get_active_targets()
        targeted = []
        
        frame_cx = self.width / 2
        frame_cy = self.height / 2
        
        for t in active:
            tx, ty = t['center']
            dist = math.hypot(tx - frame_cx, ty - frame_cy)
            
            if dist < threshold:
                targeted.append(t)
                
        return targeted

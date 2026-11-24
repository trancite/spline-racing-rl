
import numpy as np
from core.config import GameConfig
# Class for managint the road maker
class RoadMakerManager:
    def __init__(self):
        self.checkpoints = []
        self.is_periodic = False
        self.thickness = 15 
        self.radius = GameConfig.CHECKPOINT_RADIUS
        self.degree = 0

    def handle_input(self, x, y):
        idx = self.detect_near_checkpoint(x, y)
        if idx != -1:
            self.remove_checkpoint(idx)
            return "REMOVED"
        self.checkpoints.append(np.array([x,y]))
        

    def remove_checkpoint(self, index):
        if 0 <= index < len(self.checkpoints):
            self.checkpoints.pop(index)

    def detect_near_checkpoint(self, x, y, radius = GameConfig.CHECKPOINT_RADIUS):
        if not self.checkpoints:
            return -1
        distances = np.linalg.norm(np.array([x,y]) - self.checkpoints, axis = 1)
        idx = np.argmin(distances)
        return idx if distances[idx] < 1.5 * GameConfig.DETECTION_RADIUS * radius else -1
    
    def set_degree(self, k):
        self.degree = np.min([k, len(self.checkpoints) - 1])
        return self.degree
    
    def set_periodic(self, periodic: bool):
        self.is_periodic = periodic
    
    def toggle_periodic(self):
        self.is_periodic = not self.is_periodic
        return self.is_periodic
    
    def _get_points_for_export(self):
        if not self.checkpoints:
            return []
        points = [{"x": float(p[0]), "y": float(p[1])} for p in self.checkpoints]
        if self.is_periodic and len(self.checkpoints) >= 2:
            # Append first point to close the loop
            points.append({"x": float(self.checkpoints[0][0]), "y": float(self.checkpoints[0][1])})
        return points
    
    def get_road_data(self):
        if not self.checkpoints:
            return None
        return {
            "points": self._get_points_for_export(),
            "thickness": self.thickness,
            "degree": self.degree,
            "is_periodic": self.is_periodic
        }
    
    def _calculate_approx_length(self):
        if len(self.checkpoints) < 2:
            return 0.0
        
        diffs = np.diff(self.checkpoints, axis=0)
        dist = np.sum(np.sqrt(np.sum(diffs**2, axis=1)))
        
        if self.is_periodic:
            dist += np.linalg.norm(self.checkpoints[-1] - self.checkpoints[0])
            
        return float(round(dist, 2))
    
    def _get_points_for_export(self):
        if not self.checkpoints:
            return []
        points = [{"x": float(p[0]), "y": float(p[1])} for p in self.checkpoints]
        if self.is_periodic and len(self.checkpoints) >= 2:
            # Repeat the first point at the end to close the loop.
            points.append({"x": float(self.checkpoints[0][0]), "y": float(self.checkpoints[0][1])})
        return points
    

    def return_data_to_saved(self, circuit_name="Custom Created Circuit"):
        if not self.checkpoints:
            return None

        data = {
            "roads": [
                {
                    "id": circuit_name,
                    "points": self._get_points_for_export(),
                    "thickness": self.thickness,
                    "color": "#1a1a1a", # Default road color
                    "degree": self.degree,
                    "approx_length": self._calculate_approx_length(),
                }
            ]
        }
        return data
    
    def finalize_road(self):
        if not self.checkpoints:
            return None
        return {
            "points": self._get_points_for_export(),
            "thickness": self.thickness,
            "degree": self.degree,
            "is_periodic": self.is_periodic
        }
        

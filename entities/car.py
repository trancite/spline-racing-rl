

import numpy as np
import math
import uuid
from entities.car_physics import CarPhysics
from entities.car_renderer import CarRenderer

# Default car proportions: 5 by 1.8.
class Car:
    def __init__(self, canvas, data: dict, initial_angle: float = 0.0):
        self.canvas = canvas
        
        # Generate unique ID for the car (use data id if provided)
        self.car_id = data.get("id", str(uuid.uuid4())[:8])
        
        self.is_player = data.get("is_player", False)
        self.is_ai = data.get("is_AI", False)
        
        control_scheme = data.get("controls", "arrows")
        if control_scheme == "wasd":
            self.controls = {"Accelerate": "w", "Brake": "s", "Left": "a", "Right": "d"}
        else: 
            self.controls = {"Accelerate": "Up", "Brake": "Down", "Left": "Left", "Right": "Right"}
        
        # Create physics and renderer components
        self.physics = CarPhysics(data, initial_angle)
        self.renderer = CarRenderer(canvas, data, self.physics)

        self._init_compatibility_properties(data)

    def _init_compatibility_properties(self, data: dict):
        self.width = data.get('width', 4)
        self.height = data.get('height', 2)

    @property
    def pos(self) -> np.ndarray:
        return self.physics.pos
    
    @pos.setter
    def pos(self, value):
        self.physics.pos = np.array(value, dtype=float)

    @property
    def angle(self) -> float:
        return self.physics.angle
    
    @angle.setter
    def angle(self, value: float):
        self.physics.angle = value

    @property
    def velocity(self) -> np.ndarray:
        return self.physics.velocity
        
    @property
    def speed(self) -> float:
        return self.physics.speed
    
    
    def get_observations(self, circuit, race_manager):
        
        # angles to detect road
        lidar_angles = [-90, -60, -30, 0, 30, 60, 90]
        lidar_distances = []
        # max ray detection
        max_ray_len = 500.0

        # step size
        step_size = 2 
        
        front_ray_end_pos = self.physics.pos.copy()

        for angle_deg in lidar_angles:
            # current angle
            rad = self.physics.angle + math.radians(angle_deg)
            dx, dy = math.cos(rad), math.sin(rad)
            dist = 0.0
            tx, ty = self.physics.pos[0], self.physics.pos[1]
            while dist < max_ray_len:
                dist += step_size
                tx = self.physics.pos[0] + dx * dist
                ty = self.physics.pos[1] + dy * dist
                if not circuit.is_inside((tx, ty)):
                    break
            if angle_deg == 0: 
                front_ray_end_pos = np.array([tx, ty])
            lidar_distances.append(np.clip(dist / max_ray_len, 0.0, 1.0))

        forward_vel = np.dot(self.physics.velocity, self.physics.forward)
        norm_forward_speed = np.clip(forward_vel / self.physics.max_speed, -1.0, 1.0)
        
        norm_angular_vel = np.clip(self.physics.actual_yaw_rate / self.physics.turn_speed, -1.0, 1.0)


        lateral_vel = np.dot(self.physics.velocity, self.physics.right)
        norm_lateral_vel = np.clip(lateral_vel / (self.physics.max_speed * 0.5), -1.0, 1.0)

        idx, dist_from_center, tangent = circuit.roads[0].get_nearest_info(self.physics.pos)
        
        road_angle = math.atan2(tangent[1], tangent[0])
        road_err = (road_angle - self.physics.angle + math.pi) % (2 * math.pi) - math.pi
        norm_road_angle_error = road_err / math.pi

        road_center_pos = circuit.roads[0].smooth_points[idx]
        to_car = self.physics.pos - road_center_pos
        cross = tangent[0] * to_car[1] - tangent[1] * to_car[0]
        sign = 1.0 if cross >= 0 else -1.0
        norm_lateral_pos = np.clip(sign * dist_from_center / (race_manager.get_thickness()/2), -1.0, 1.0)

        _, _, future_tangent = circuit.roads[0].get_nearest_info(front_ray_end_pos)
        future_road_angle = math.atan2(future_tangent[1], future_tangent[0])
        curve_ahead = (future_road_angle - road_angle + math.pi) % (2 * math.pi) - math.pi
        norm_curve_ahead = curve_ahead / math.pi

        return np.array(lidar_distances + [
            norm_forward_speed,             # [7]
            norm_angular_vel,               # [8]
            norm_lateral_vel,               # [9]
            norm_road_angle_error,          # [10]
            norm_lateral_pos,               # [11]
            norm_curve_ahead                # [12]
        ], dtype=np.float32)
    
    
    def handle_input(self, keys: set):
        if self.controls["Accelerate"] in keys:
            self.physics.accelerate(1.0)
        if self.controls["Brake"] in keys:
            self.physics.brake(1.0)
        if self.controls["Left"] in keys:
            self.physics.turn(1.0)
        if self.controls["Right"] in keys:
            self.physics.turn(-1.0)
            
    def step(self, on_road: bool = True):
        self.physics.step(on_road)
        
    def show(self, wv):
        self.renderer.render(wv)
        
    def transform_points(self, local_points: np.ndarray) -> np.ndarray:
        return self.renderer._transform_points(local_points)
        
    def destroy(self):
        self.renderer.destroy()

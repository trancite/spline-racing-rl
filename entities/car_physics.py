import math
import numpy as np

from core.config import PhysicsConfig


class CarPhysics:
    def __init__(self, data: dict, initial_angle: float = 0.0):
        self.dt = PhysicsConfig.DT

        # Position        
        self.pos = np.array([
            float(data['start_position']['x']),
            float(data['start_position']['y'])
        ], dtype=float)
        
        # Angle
        if "angle" in data:
            self.angle = math.radians(data.get('angle', 0.0))
        else:
            self.angle = initial_angle
        
        # Angle in previous frame 
        self.prev_angle = self.angle
        self.velocity = np.array([0.0, 0.0], dtype=float)
        
        self.width = data.get('width', 4.5)
        self.height = data.get('height', 2.0)
        
        # Speed in m/s
        self.max_speed = PhysicsConfig.speed_kmh_to_ms(
            data.get('max_speed', PhysicsConfig.DEFAULT_MAX_SPEED)
        )
        
        # Acceleration in s to achieve 100 km/h
        self.acceleration = PhysicsConfig.acceleration_0_100_s_to_ms2(
            data.get('acceleration', PhysicsConfig.DEFAULT_ACCELERATION)
        )

        # Turn speed in radians per second
        self.turn_speed = data.get('turn_speed', PhysicsConfig.DEFAULT_TURN_SPEED)
        
        # Grip. It will be MAPPED to a more interpretable vaulue
        # f(x) = x/(1-x) maps [0, inf) to [0,1] and is an increasing function
        self.grip = data.get('grip', PhysicsConfig.DEFAULT_GRIP)

        if self.grip == 1:
            self.grip = np.inf
        else:
            self.grip /= (1 - self.grip)

        # Minimum % of maximum speed to be able to turn 
        self.min_speed_for_turn = self.max_speed * data.get('min_speed_for_turn', PhysicsConfig.MIN_SPEED_FOR_TURN)
        
        # Input state that player creates. All movements and updates are done in the step 
        # throttle = accelerate
        self.throttle_input = 0.0
        self.brake_input = 0.0
        self.steer_input = 0.0
        
        # State flags
        self.is_accelerating = False
        self.is_braking = False
        self.is_drifting = False
        self.drift_angle = 0.0

        # Debug info
        self.effective_grip = self.grip
        self.effective_turn = self.turn_speed
        self.forward_speed = 0.0
        self.a_lat_max = 0.0
        self.requested_yaw_rate = 0.0
        self.actual_yaw_rate = 0.0
        self.speed_factor = 0.0
        self.high_speed_penalty = 0.0
    
    @property
    def speed(self) -> float:
        return np.linalg.norm(self.velocity)
    
    @property
    def speed_ratio(self) -> float:
        return min(1.0, self.speed / self.max_speed) if self.max_speed > 0 else 0.0
    
    # Yaw rate in radians per second
    @property
    def yaw_rate(self) -> float:
        delta = self.angle - self.prev_angle
        delta = (delta + math.pi) % (2 * math.pi) - math.pi
        return delta / self.dt
    
    # Direction
    @property
    def forward(self) -> np.ndarray:
        return np.array([np.cos(self.angle), np.sin(self.angle)])
    
    # Right vector
    @property
    def right(self) -> np.ndarray:
        return np.array([np.cos(self.angle + math.pi/2), np.sin(self.angle + math.pi/2)])
    
    # Direction (redundant with forward but it does not matter)
    @property
    def direction(self) -> np.ndarray:
        return self.forward
    
    # Centripetal acceleration
    @property
    def centripetal_acceleration(self) -> float:
        return abs(self.speed * self.yaw_rate)
    
    # Accelerate
    def accelerate(self, intensity: float = 1.0): 
        self.throttle_input = max(0.0, min(1.0, intensity))
    
    def brake(self, intensity: float = 1.0):
        self.brake_input = max(0.0, min(1.0, intensity))
    
    def turn(self, direction: float):
        self.steer_input = max(-1.0, min(1.0, direction))
    
    def step(self, on_road: bool = True, dt: float = None):
        dt = dt or self.dt
        
        # Surface grip and road
        friction = PhysicsConfig.ROAD_FRICTION if on_road else PhysicsConfig.OFF_ROAD_FRICTION
        surface_grip = PhysicsConfig.ROAD_GRIP if on_road else PhysicsConfig.OFF_ROAD_GRIP
        
        # Update flags
        self.is_accelerating = self.throttle_input > 0
        self.is_braking = self.brake_input > 0
        
        # Apply throttle
        if self.is_accelerating:
            accel_force = self.acceleration * self.throttle_input
            self.velocity += self.forward * accel_force * dt
        
        # Apply brakes
        if self.is_braking:
            brake_force = self.acceleration * PhysicsConfig.BRAKING_POWER * self.brake_input
            self.velocity -= self.forward * brake_force * dt
        
        # Apply friction
        # Friction is the % of speed retained per second
        # We make it frame-rate independent. dt * (number of dt in a second) = 1
        self.velocity *= (friction ** dt)
        
        # Calculate grip
        # is the product of the surface grip and the car grip
        # Now, the max acceleration is a_lat_max = effective_grip * g
        self.effective_grip = surface_grip * self.grip
        # This is make it for the drifting
        self.a_lat_max = self.effective_grip * PhysicsConfig.G
        
        # Calculate turning
        current_speed = self.speed
        speed_factor = max(0.0, min(1.0, current_speed / self.min_speed_for_turn))
        high_speed_penalty = 1.0 - self.speed_ratio * PhysicsConfig.ROTATION_PENALTY
        self.high_speed_penalty = 1 - high_speed_penalty
        requested_yaw_rate = self.steer_input * self.turn_speed * speed_factor * high_speed_penalty
        self.requested_yaw_rate = requested_yaw_rate
        self.effective_turn = abs(requested_yaw_rate)
        
        self.actual_yaw_rate = requested_yaw_rate
        
        # Update angle
        self.prev_angle = self.angle
        self.angle += self.actual_yaw_rate * dt
        
        # Calculate velocity components
        self.forward_speed = np.dot(self.velocity, self.forward)
        lateral_speed = np.dot(self.velocity, self.right)

        # Apply lateral grip
        tau = 1.0 / max(PhysicsConfig.K, 1e-9)
        alpha = np.exp(-dt/tau)
        a_lat_needed = (alpha * lateral_speed - lateral_speed) / dt
        
        if abs(a_lat_needed) > self.a_lat_max:
            a_lat_applied = np.sign(a_lat_needed) * self.a_lat_max
            new_lateral_speed = lateral_speed + a_lat_applied * dt
            self.is_drifting = True
        else:
            a_lat_applied = a_lat_needed
            new_lateral_speed = alpha * lateral_speed
            self.is_drifting = False
        
        # Reconstruct velocity
        self.velocity = self.forward * self.forward_speed + self.right * new_lateral_speed
        
        # Calculate drift angle
        self.drift_angle = math.atan2(new_lateral_speed, abs(self.forward_speed) + 0.1)
        
        # Clamp to max speed
        current_speed = self.speed
        if current_speed > self.max_speed:
            self.velocity = (self.velocity / current_speed) * self.max_speed
        
        # Update position
        self.pos += self.velocity * dt
        
        # Reset inputs for next frame
        self.throttle_input = 0.0
        self.brake_input = 0.0
        self.steer_input = 0.0

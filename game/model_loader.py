from pathlib import Path
from typing import Optional, Tuple
from collections import deque
import numpy as np

from stable_baselines3 import PPO
from training.training_code.model_config import ModelConfig


MODEL_DATA_PATH = Path(__file__).parent.parent / "training" / "models"
DONE_MODELS_PATH = Path(__file__).parent.parent / "training" / "done_models"


class AIController:
    def __init__(
        self, 
        model_name: str,
        car,
        default_n_stack: int = 4,
        default_obs_method: str = "get_observations"
    ):
        self.car = car
        self.model: Optional[PPO] = None
        self.config: Optional[ModelConfig] = None
        
        self.n_stack = default_n_stack
        self.obs_method = default_obs_method
        
        self.frame_stack = deque(maxlen=default_n_stack)
        
        self._load_model(model_name)
    
    def _load_model(self, model_name: str) -> bool:
        model_name = model_name.replace(".zip", "")
        
        paths_to_try = [
            MODEL_DATA_PATH / f"{model_name}.zip",
            DONE_MODELS_PATH / f"{model_name}.zip",
        ]
        
        model_path = None
        for path in paths_to_try:
            print(f"Trying to load model from: {path}")
            if path.exists():
                model_path = path
                break
        
        if model_path is None:
            print(f"❌ Model not found: {model_name}")
            return False
        
        try:
            custom_objects = {
                "clip_range": 0.2,  
                "lr_schedule": lambda _: 3e-4,  
            }
            self.model = PPO.load(str(model_path), custom_objects=custom_objects)
            print(f"✅ Model loaded: {model_name}")
            
            self.config = ModelConfig.load(model_path)
            if self.config:
                self.n_stack = self.config.n_stack
                self.obs_method = self.config.observation_method
                print(f"   Config: stack={self.n_stack}, obs={self.obs_method}")
            else:
                print(f"   Using defaults: stack={self.n_stack}")
            
            self.frame_stack = deque(maxlen=self.n_stack)
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def reset(self):
        self.frame_stack.clear()
    
    def get_action(self, circuit, race_manager, verbose = False) -> Optional[Tuple[float, float, float]]:
        if self.model is None or self.car is None:
            return None
        
        obs_method = getattr(self.car, self.obs_method, None)
        if obs_method is None:
            obs_method = self.car.get_observations
        
        current_obs = obs_method(circuit, race_manager)
        
        if len(self.frame_stack) == 0:
            for _ in range(self.n_stack):
                self.frame_stack.append(current_obs)
        else:
            self.frame_stack.append(current_obs)
        
        if self.n_stack > 1:
            stacked_obs = np.array(self.frame_stack).reshape(1, -1)
        else:
            stacked_obs = current_obs.reshape(1, -1)
        
        obs = self.frame_stack[-1]
        action, _ = self.model.predict(stacked_obs, deterministic=True)
        
        if self.n_stack > 1:
            steer, raw_accel, raw_brake = action[0]
        else:
            steer, raw_accel, raw_brake = action
        
        acceleration = (raw_accel + 1) / 2
        brake = (raw_brake + 1) / 2
        
        return steer, acceleration, brake
    
    def apply_action(self, circuit, race_manager):
        action = self.get_action(circuit, race_manager)
        if action is None:
            return
        
        steer, acceleration, brake = action
        
        # because I use the convention I want
        self.car.physics.turn(-steer)
        self.car.physics.accelerate(acceleration)
        self.car.physics.brake(brake)


def load_model_with_config(
    model_name: str
) -> Tuple[Optional[PPO], Optional[ModelConfig]]:
    model_name = model_name.replace(".zip", "")
    
    # Try multiple paths
    paths_to_try = [
        MODEL_DATA_PATH / f"{model_name}.zip",
        DONE_MODELS_PATH / f"{model_name}.zip",
    ]
    
    for path in paths_to_try:
        if path.exists():
            try:
                model = PPO.load(str(path))
                config = ModelConfig.load(path)
                return model, config
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
    
    print(f"❌ Model not found: {model_name}")
    return None, None


def get_model_info(model_name: str) -> Optional[ModelConfig]:
    model_name = model_name.replace(".zip", "")
    
    paths_to_try = [
        MODEL_DATA_PATH / f"{model_name}.json",
        DONE_MODELS_PATH / f"{model_name}.json",
    ]
    
    for path in paths_to_try:
        if path.exists():
            return ModelConfig.load(path)
    
    return None


def list_available_models() -> list:
    models = []
    
    for path in [MODEL_DATA_PATH, DONE_MODELS_PATH]:
        if path.exists():
            models.extend([f.stem for f in path.glob("*.zip")])
    
    return sorted(set(models))

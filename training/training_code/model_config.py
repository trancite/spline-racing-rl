
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from core.config import PhysicsConfig

# Class for organizing model training configuration
@dataclass
class ModelConfig:
    model_name: str = "unnamed_model"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Environment configuration
    n_stack: int = 4  
    n_actions: int = 3  
    n_observations: int = 13  
    observation_method: str = "get_observations"  
    
    # Training configuration used by default
    car_name: str = "simple_car"
    circuit_names: List[str] = field(default_factory=lambda: ["triangle"])
    
    # Training hyperparameters (for reference)
    n_envs: int = 10
    total_timesteps: int = 0
    learning_rate: float = 1e-4
    n_steps: int = 1024
    batch_size: int = 256
    ent_coef: float = 0.1
    gamma: float = 0.999
    
    # Training statistics
    circuit_success_stats: Dict[str, int] = field(default_factory=dict)  # Successes per circuit

    # Background
    road_friction: float = PhysicsConfig.ROAD_FRICTION
    off_road_friction: float = PhysicsConfig.OFF_ROAD_FRICTION
    road_grip: float = PhysicsConfig.ROAD_GRIP
    off_road_grip: float = PhysicsConfig.OFF_ROAD_GRIP
    
    # Additional metadata
    notes: str = ""
    
    @property
    def stacked_obs_size(self) -> int:
        return self.n_stack * self.n_observations
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)
    
    def save(self, path: Path) -> None:
        path = Path(path)
        if path.suffix == ".zip":
            path = path.with_suffix(".json")
        elif not path.suffix:
            path = path.with_suffix(".json")
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"📋 Model config saved: {path.name}")
    
    @classmethod
    def load(cls, path: Path) -> Optional["ModelConfig"]:
        path = Path(path)
        if path.suffix == ".zip":
            path = path.with_suffix(".json")
        elif not path.suffix:
            path = Path(str(path) + ".json")
            
        if not path.exists():
            print(f"⚠️ No config found at {path}, using defaults")
            return None
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            config = cls.from_dict(data)
            print(f"✅ Model config loaded: {path.name}")
            return config
        except Exception as e:
            print(f"❌ Error loading config {path}: {e}")
            return None


def get_default_config() -> ModelConfig:
    return ModelConfig()


def create_config_for_model(
    model_name: str,
    car_name: str,
    circuit_names: List[str],
    n_stack: int = 4,
    n_actions: int = 3,
    n_observations: int = 13,
    observation_method: str = "get_observations",
    **training_params
) -> ModelConfig:

    return ModelConfig(
        model_name=model_name,
        car_name=car_name,
        circuit_names=circuit_names,
        n_stack=n_stack,
        n_actions=n_actions,
        n_observations=n_observations,
        observation_method=observation_method,
        n_envs=training_params.get("n_envs", 10),
        total_timesteps=training_params.get("total_timesteps", 0),
        learning_rate=training_params.get("learning_rate", 0.0003),
        n_steps=training_params.get("n_steps", 1024),
        batch_size=training_params.get("batch_size", 256),
        circuit_success_stats=training_params.get("circuit_success_stats", {}),
        road_friction=training_params.get("road_friction", PhysicsConfig.ROAD_FRICTION),
        off_road_friction=training_params.get("off_road_friction", PhysicsConfig.OFF_ROAD_FRICTION),
        road_grip=training_params.get("road_grip", PhysicsConfig.ROAD_GRIP),
        off_road_grip=training_params.get("off_road_grip", PhysicsConfig.OFF_ROAD_GRIP),
        notes=training_params.get("notes", ""),
    )

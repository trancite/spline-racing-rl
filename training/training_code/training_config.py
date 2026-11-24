from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict

TRAINING_CODE_DIR = Path(__file__).resolve().parent
TRAINING_DIR = TRAINING_CODE_DIR.parent
PROJECT_ROOT = TRAINING_DIR.parent

TRAINING_DATA_PATH = TRAINING_DIR / "training_data"
CARS_FOR_TRAINING_PATH = TRAINING_DATA_PATH / "cars_for_training"
CIRCUITS_FOR_TRAINING_PATH = TRAINING_DATA_PATH / "circuits_for_training"

MODELS_PATH = TRAINING_DIR / "models"
DONE_MODELS_PATH = TRAINING_DIR / "done_models"

MODELS_PATH.mkdir(exist_ok=True)
DONE_MODELS_PATH.mkdir(exist_ok=True)


@dataclass
class TrainingConfig:
    car_name: str = "simple_car"
    circuit_names: List[str] = None  
    
    output_model_name: Optional[str] = None
    
    n_envs: int = 10  # Number of parallel environments
    n_stack: int = 4  
    
    learning_rate: float = 3e-4
    n_steps: int = 2048  
    batch_size: int = 128
    total_timesteps: int = 5_000_000
    gamma  : float = 0.999  
    ent_coef: float = 0.005
    gae_lambda: float = 0.95
    
    device: str = "cpu"
    
    circuit_max_steps: Dict[str, int] = None
    
    def __post_init__(self):
        if self.circuit_names is None:
            self.circuit_names = ["triangle"]
    
    @property
    def car_path(self) -> Path:
        return CARS_FOR_TRAINING_PATH / f"{self.car_name}.json"
    
    @property
    def circuit_paths(self) -> List[Path]:
        return [
            CIRCUITS_FOR_TRAINING_PATH / f"{name}.json"
            for name in self.circuit_names
        ]
    
    def get_output_name(self) -> str:
        if self.output_model_name:
            return self.output_model_name
        circuits_str = "_".join(self.circuit_names[:3])  # Limit name length
        if len(self.circuit_names) > 3:
            circuits_str += f"_+{len(self.circuit_names) - 3}more"
        return f"ppo_{self.car_name}_{circuits_str}"
    
    def validate(self) -> bool:
        if not self.car_path.exists():
            print(f"❌ Car config not found: {self.car_path}")
            return False
        
        for path in self.circuit_paths:
            if not path.exists():
                print(f"❌ Circuit not found: {path}")
                return False
        
        return True


def list_available_cars() -> List[str]:
    return [f.stem for f in CARS_FOR_TRAINING_PATH.glob("*.json")]


def list_available_circuits() -> List[str]:
    return [f.stem for f in CIRCUITS_FOR_TRAINING_PATH.glob("*.json")]


def list_saved_models() -> List[str]:
    return [f.stem for f in MODELS_PATH.glob("*.zip")]


def list_done_models() -> List[str]:
    return [f.stem for f in DONE_MODELS_PATH.glob("*.zip")]

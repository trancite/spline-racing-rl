import json
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv, VecFrameStack

from training.training_code.training_config import (
    TrainingConfig, 
    MODELS_PATH,
)
from training.training_code.model_config import ModelConfig, create_config_for_model
from training.training_code.env import CarEnv, MultiCircuitCarEnv, create_env_factory


class Trainer:
    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        self.model: Optional[PPO] = None
        self.env = None
        self.model_config: Optional[ModelConfig] = None
        
    def _load_data(self) -> tuple:
        with open(self.config.car_path, "r") as f:
            car_data = json.load(f)["cars"][0]
        
        circuit_data_list = []
        for circuit_path in self.config.circuit_paths:
            with open(circuit_path, "r") as f:
                circuit_data_list.append(json.load(f))
        
        return car_data, circuit_data_list
    
    def _create_env(self, car_data: dict, circuit_data_list: list):
        multi_circuit = len(circuit_data_list) > 1
        
        make_env = create_env_factory(
            circuit_data_list=circuit_data_list,
            car_data=car_data,
            n_observations=13,
            observation_method="get_observations",
            multi_circuit=multi_circuit,
            circuit_change_mode="weighted",  
            circuit_max_steps=self.config.circuit_max_steps,
            circuit_names=self.config.circuit_names  
        )

        env = make_vec_env(
            make_env, 
            n_envs=self.config.n_envs, 
            vec_env_cls=SubprocVecEnv if self.config.n_envs > 1 else None
        )
        
        if self.config.n_stack > 1:
            env = VecFrameStack(env, n_stack=self.config.n_stack)
        
        return env
        
    
    def _get_circuit_success_stats(self) -> Dict[str, int]:
        combined_stats = {}
        
        try:
            base_env = self.env
            if hasattr(base_env, 'venv'):
                base_env = base_env.venv
            
            if hasattr(base_env, 'get_attr'):
                try:
                    all_stats = base_env.get_attr('circuit_success_count')
                    for stats in all_stats:
                        if stats:
                            for circuit, count in stats.items():
                                combined_stats[circuit] = combined_stats.get(circuit, 0) + count
                except Exception:
                    pass  
        except Exception as e:
            print(f"⚠️ Could not gather circuit stats: {e}")
        
        return combined_stats
    
    def _create_model_config(self, total_timesteps: int) -> ModelConfig:
        circuit_stats = self._get_circuit_success_stats()
        
        return create_config_for_model(
            model_name=self.config.get_output_name(),
            car_name=self.config.car_name,
            circuit_names=self.config.circuit_names,
            n_stack=self.config.n_stack,
            n_actions=3,
            n_observations=13,
            observation_method="get_observations",
            n_envs=self.config.n_envs,
            total_timesteps=total_timesteps,
            learning_rate=self.config.learning_rate,
            n_steps=self.config.n_steps,
            batch_size=self.config.batch_size,
            circuit_success_stats=circuit_stats,
        )
    
    def _save_model(self, name: str, timesteps: int):
        save_path = MODELS_PATH / name
        
        self.model.save(save_path)
        print(f"✅ Model saved: {save_path}.zip")
        
        model_config = self._create_model_config(timesteps)
        
        if model_config.circuit_success_stats:
            print(f"📊 Final circuit success stats: {model_config.circuit_success_stats}")
        
        model_config.save(save_path)
    
    def start(self) -> None:
        if not self.config.validate():
            raise ValueError("Invalid training configuration")
        
        print("\n" + "=" * 50)
        print("🚀 STARTING NEW TRAINING SESSION")
        print("=" * 50)
        print(f"  Car: {self.config.car_name}")
        print(f"  Circuits: {self.config.circuit_names}")
        print(f"  Envs: {self.config.n_envs}")
        print(f"  Frame Stack: {self.config.n_stack}")
        print(f"  Timesteps: {self.config.total_timesteps:,}")
        print("=" * 50 + "\n")
        
        car_data, circuit_data_list = self._load_data()
        
        self.env = self._create_env(car_data, circuit_data_list)
        
        self.model = PPO(
            "MlpPolicy",
            self.env,
            device=self.config.device,
            verbose=1,
            learning_rate=self.config.learning_rate,
            n_steps=self.config.n_steps,
            batch_size=self.config.batch_size,
        )
        
        interrupted = False
        try:
            self.model.learn(total_timesteps=self.config.total_timesteps)
        except KeyboardInterrupt:
            interrupted = True
            import io
            sys.stderr = io.StringIO()
            print("\n\n🛑 Training interrupted by user. Saving model...")
        finally:
            import io
            if not interrupted:
                stderr_backup = sys.stderr
            sys.stderr = io.StringIO()
            
            try:
                self.env.close()
            except:
                pass
            
            sys.stderr = sys.__stderr__
            
            print(f"🧠 Saving model: {self.config.get_output_name()}")
            output_name = self.config.get_output_name()
            if interrupted:
                output_name = f"{output_name}_interrupted"
            self._save_model(output_name, self.config.total_timesteps)
            print("✅ Done!")
    
    def resume(
        self, 
        model_name: str, 
        extra_timesteps: int = 1_000_000, 
    ) -> None:

        model_name = model_name.replace(".zip", "")
        model_path = MODELS_PATH / f"{model_name}.zip"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print("\n" + "=" * 50)
        print("🧠 RESUMING TRAINING")
        print("=" * 50)
        print(f"  Model: {model_name}")
        print(f"  Extra timesteps: {extra_timesteps:,}")
        
        existing_config = ModelConfig.load(model_path)
        if existing_config:
            print(f"  Using saved n_stack={existing_config.n_stack}")
            self.config.n_stack = existing_config.n_stack
            print(f"  Original circuits: {existing_config.circuit_names}")
            print(f"  New circuits: {self.config.circuit_names}")
        
        print("=" * 50 + "\n")
        
        if not self.config.validate():
            raise ValueError("Invalid training configuration")
        
        car_data, circuit_data_list = self._load_data()
        
        self.env = self._create_env(car_data, circuit_data_list)
        
        self.model = PPO.load(
            model_path, 
            env=self.env, 
            device=self.config.device,
            learning_rate=self.config.learning_rate,
            n_steps=self.config.n_steps,
            batch_size=self.config.batch_size,
            ent_coef=self.config.ent_coef,
        )
        
        print(f"  📊 Using hyperparameters from config:")
        print(f"     learning_rate: {self.config.learning_rate}")
        print(f"     n_steps: {self.config.n_steps}")
        print(f"     batch_size: {self.config.batch_size}")
        print(f"     ent_coef: {self.config.ent_coef}")
        
        interrupted = False
        try:
            self.model.learn(
                total_timesteps=extra_timesteps, 
                reset_num_timesteps=False
            )
        except KeyboardInterrupt:
            interrupted = True
            import io
            sys.stderr = io.StringIO()
            print("\n\n🛑 Training interrupted by user. Saving model...")
        finally:
            import io
            sys.stderr = io.StringIO()
            try:
                self.env.close()
            except:
                pass
            sys.stderr = sys.__stderr__
            
            new_name = f"{model_name}_resumed"
            if interrupted:
                new_name = f"{model_name}_resumed_interrupted"
            self._save_model(new_name, extra_timesteps)
            print("✅ Done!")



def start_training(
    car_name: str = "simple_car",
    circuit_name: str = "triangle",
    output_model_name: Optional[str] = None,
    circuit_names: Optional[List[str]] = None,
    n_stack: int = 4,
    n_envs: int = 10,
    total_timesteps: int = 7_500_000,
    circuit_max_steps: dict = None,  
):

    if circuit_names is None:
        circuit_names = [circuit_name]
    
    config = TrainingConfig(
        car_name=car_name,
        circuit_names=circuit_names,
        output_model_name=output_model_name,
        n_envs=n_envs,
        n_stack=n_stack,
        total_timesteps=total_timesteps,
        circuit_max_steps=circuit_max_steps,
    )
    
    trainer = Trainer(config)
    trainer.start()


def resume_training(
    car_name: str,
    circuit_name: str,
    model_zip_name: str,
    extra_timesteps: int = 1_000_000,
    circuit_names: Optional[List[str]] = None,
    circuit_max_steps: dict = None,  # {"triangle": 4000, "square": 5000}
    learning_rate: float = 0.0003,
    n_steps: int = 1024,
    batch_size: int = 256,
    ent_coef: float = 0.05,
):

    if circuit_names is None:
        circuit_names = [circuit_name]
    
    config = TrainingConfig(
        car_name=car_name,
        circuit_names=circuit_names,
        circuit_max_steps=circuit_max_steps,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        ent_coef=ent_coef,
    )
    
    trainer = Trainer(config)
    trainer.resume(model_zip_name, extra_timesteps)


if __name__ == "__main__":


    import glob
    import os
    CIRCUIT_DIR = os.path.join(os.path.dirname(__file__), '../training_data/circuits_for_training')
    circuit_files = glob.glob(os.path.join(CIRCUIT_DIR, '*.json'))
    circuit_names = []
    circuit_max_steps = {}
    for circuit_file in circuit_files:
        name = os.path.splitext(os.path.basename(circuit_file))[0]
        if name == "hard_angles":
            continue  # skip hard_angles for this training
        with open(circuit_file, 'r') as f:
            data = json.load(f)
            road = data['roads'][0]
            length = road['approx_length']
            circuit_max_steps[name] = int(length * 10)
        circuit_names.append(name)

    start_training(
        car_name="default_ai",
        circuit_name="triangle",
        circuit_names=circuit_names,
        output_model_name="ppo_all_circuits_default_ai",
        total_timesteps=8_000_000,
        circuit_max_steps=circuit_max_steps
    )
    


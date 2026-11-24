import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from typing import List, Dict, Any, Optional, Tuple
from entities.circuit import Circuit
from entities.car import Car
from game.race_manager import RaceManager


class CarEnv(gym.Env):
    metadata = {"render_modes": ["human"]}
    
    # Default max iterations if there is not a specific value
    DEFAULT_MAX_STEPS = 20_000
    
    # Map circuit names to their max steps (fallback defaults)
    CIRCUIT_MAX_STEPS = {
        "triangle": 4000,
        "hard_angles": 10000,
        "hard_zig_zag": 6000,
        "hard_smooth_shape": 6000,
        "hard_random_circuit": 20000,
        "ovalo": 4000,
        "infinity": 6000,
        "test_circuit": 6000,
    }
    
    def __init__(
        self, 
        circuit, 
        car_data: Dict[str, Any],
        n_observations: int = 13,
        observation_method: str = "get_observations",
        max_steps: int = None,  
        circuit_max_steps: Dict[str, int] = None  
    ):

        super().__init__()
        
        self.circuit = circuit
        self.car_data = car_data
        self.car = Car(None, car_data)
        self.race_manager = RaceManager(self.circuit)
        
        self.n_observations = n_observations
        self.observation_method = observation_method
        self._max_steps_override = max_steps
        self._circuit_max_steps = circuit_max_steps if circuit_max_steps else self.CIRCUIT_MAX_STEPS
        
        self.action_space = spaces.Box(
            low=-1, high=1, shape=(3,), dtype=np.float32
        )
        self.observation_space = spaces.Box(
            low=-1, high=1, shape=(n_observations,), dtype=np.float32
        )
        
        self.step_count = 0
        self.prev_ratio = 0.0
    
    # max number of steps in this moment (depends on the current circuit)
    @property
    def max_steps(self) -> int:
        circuit_name = self.current_circuit_name.lower()
        for key, steps in self._circuit_max_steps.items():
            if key.lower() in circuit_name:
                return steps
        
        if self._max_steps_override is not None:
            return self._max_steps_override
        
        return self.DEFAULT_MAX_STEPS
    
    @property
    def current_circuit_name(self) -> str:
        return getattr(self.circuit, 'name', 'unknown')

    def _get_obs(self) -> np.ndarray:
        method = getattr(self.car, self.observation_method)
        return method(self.circuit, self.race_manager)

    def reset(
        self, 
        seed: Optional[int] = None, 
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)
        self.race_manager.reset()
        self.step_count = 0
        
        start_pos = self.circuit.global_checkpoints[0]
        self.car.physics.pos = np.array(start_pos, dtype=float)
        self.car.physics.angle = self.circuit.initial_angle
        self.car.physics.velocity.fill(0.0)
        self.prev_ratio = 0
        
        self.race_manager.update([self.car])
        
        obs = self._get_obs()
        
        return obs, {}

        
    def _get_reward(self, obs, race_status, on_road):
        reward = 0
        if not on_road:
            return -200, True
        current_ratio = self.race_manager.fraction_completed(self.car)
        delta = current_ratio - self.prev_ratio
        self.prev_ratio = current_ratio
        reward += delta * 100 * (0.5 + obs[7])
        time_penalty =  1
        reward -= time_penalty

        if race_status == 1:
            print(f"✅ Checkpoint in {self.circuit.name} in step {self.step_count}!")
        if race_status >= 2:
            print(f"🏁 Finished circuit {self.circuit.name} in step {self.step_count}!")
            return reward, True    
        return reward, False
  

    def step(
        self, 
        action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        self.step_count += 1
        
        steer, accel, brake = np.asarray(action, dtype=np.float32)
        
        gas_input = (accel + 1) / 2
        brake_input = (brake + 1) / 2

        self.car.physics.turn(-steer)
        self.car.physics.accelerate(gas_input)
        self.car.physics.brake(brake_input)
        
        was_on_road = self.circuit.is_inside(self.car.physics.pos)
        self.car.step(on_road=was_on_road)
        
        race_status = self.race_manager.update([self.car])
        is_on_road_now = self.circuit.is_inside(self.car.pos)
        
        obs = self._get_obs()
        reward, terminated = self._get_reward(obs, race_status, is_on_road_now)
        
        truncated = self.step_count >= self.max_steps
        if truncated and not terminated:
            print(f"⏱️ Max time ({self.max_steps}) reached on {self.current_circuit_name}.")
        info = {
        "circuit_name": self.current_circuit_name,
        "is_success": (race_status >= 2)
    }
        
        return obs, reward, terminated, truncated, info


class MultiCircuitCarEnv(CarEnv):
    def __init__(
        self,
        circuits: List,  
        car_data: Dict[str, Any],
        n_observations: int = 13,
        observation_method: str = "get_observations",
        # Modes: random, sequential or weighted. Weighted favors circuits with fewer successes.
        circuit_change_mode: str = "random",  
        circuit_max_steps: Dict[str, int] = None
    ):
        if not circuits:
            raise ValueError("At least one circuit is required")
        
        self.circuits = circuits
        self.circuit_change_mode = circuit_change_mode
        self.circuit_index = 0
        
        # dictionary of successes per circuit 
        self.circuit_success_count = {c.name: 0 for c in circuits}
        
        super().__init__(
            circuit=circuits[0],
            car_data=car_data,
            n_observations=n_observations,
            observation_method=observation_method,
            circuit_max_steps=circuit_max_steps
        )
    
    def _select_circuit(self) -> None:
        if len(self.circuits) == 1:
            return
        
        if self.circuit_change_mode == "random":
            self.circuit_index = random.randint(0, len(self.circuits) - 1)
        elif self.circuit_change_mode == "sequential":
            self.circuit_index = (self.circuit_index + 1) % len(self.circuits)
        elif self.circuit_change_mode == "weighted":
            weights = []
            for c in self.circuits:
                success = self.circuit_success_count.get(c.name, 0)
                weights.append(1.0 / (success + 1))
            
            total = sum(weights)
            probabilities = [w / total for w in weights]
            
            self.circuit_index = random.choices(
                range(len(self.circuits)), 
                weights=probabilities, 
                k=1
            )[0]
        
        self.circuit = self.circuits[self.circuit_index]
        self.race_manager = RaceManager(self.circuit)
    
    def _record_success(self, circuit_name: str) -> None:
        if circuit_name in self.circuit_success_count:
            self.circuit_success_count[circuit_name] += 1
            print(f"📊 Success stats: {self.circuit_success_count}")
    
    def step(
        self, 
        action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        obs, reward, terminated, truncated, info = super().step(action)
        
        if info.get("is_success", False):
            self._record_success(self.current_circuit_name)
        
        return obs, reward, terminated, truncated, info
    
    def reset(
        self, 
        seed: Optional[int] = None, 
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        if options and "circuit_index" in options:
            self.circuit_index = options["circuit_index"] % len(self.circuits)
            self.circuit = self.circuits[self.circuit_index]
            self.race_manager = RaceManager(self.circuit)
        else:
            self._select_circuit()
        
        return super().reset(seed=seed, options=options)

def create_env_factory(
    circuit_data_list: List[Dict],
    car_data: Dict[str, Any],
    n_observations: int = 13,
    observation_method: str = "get_observations",
    multi_circuit: bool = False,
    circuit_change_mode: str = "random",
    circuit_max_steps: Dict[str, int] = None,
    circuit_names: List[str] = None  
):

    def make_env():
        try:
            circuits = []
            for i, circuit_data in enumerate(circuit_data_list):
                name = circuit_names[i] if circuit_names and i < len(circuit_names) else f"TrainingCircuit_{i}"
                circuit = Circuit(None, name)
                circuit.load_data(circuit_data)
                circuits.append(circuit)
            
            if multi_circuit and len(circuits) > 1:
                return MultiCircuitCarEnv(
                    circuits=circuits,
                    car_data=car_data,
                    n_observations=n_observations,
                    observation_method=observation_method,
                    circuit_change_mode=circuit_change_mode,
                    circuit_max_steps=circuit_max_steps
                )
            else:
                return CarEnv(
                    circuit=circuits[0],
                    car_data=car_data,
                    n_observations=n_observations,
                    observation_method=observation_method,
                    circuit_max_steps=circuit_max_steps
                )
        except Exception as e:
            import traceback
            print(f"❌ Error creating environment: {e}")
            traceback.print_exc()
            raise
    
    return make_env

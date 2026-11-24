"""Race progress management module."""

import numpy as np

from core.config import GameConfig


class RaceManager:
    def __init__(self, circuit=None):
        self._record = {}
        self.checkpoints = np.array([])
        self.required_laps = 1
        self.is_periodic = False
        self.thickness = 15.0 
        self.circuit = None

        if circuit:
            self.load_circuit(circuit)

    def load_circuit(self, circuit):
        self.circuit = circuit
        self.checkpoints = np.array(circuit.global_checkpoints)
        self.thickness = circuit.road_thickness()
        self.required_laps = circuit.required_laps
        self.is_periodic = circuit.is_periodic

    def update(self, cars: list) -> int:
        max_status = 0
        last_checkpoint_idx = len(self.checkpoints) - 1

        # Prevent errors if no checkpoints are loaded
        if len(self.checkpoints) == 0:
            return max_status

        for car in cars:
            car_id = car.car_id

            if car_id not in self._record:
                # start before the first checkpoint: next_idx = 1 (we expect to go to checkpoint 1)
                self._record[car_id] = {"next_idx": 1, "laps": 0}
                continue

            progress = self._record[car_id]
            next_idx = progress["next_idx"]

            # Prevent out-of-bounds access
            if next_idx < 0 or next_idx >= len(self.checkpoints):
                next_idx = 0 if self.is_periodic else last_checkpoint_idx

            target_checkpoint = self.checkpoints[next_idx]
            distance = float(np.linalg.norm(np.array(car.pos) - np.array(target_checkpoint)))

            if distance < GameConfig.CHECKPOINT_RADIUS * GameConfig.DETECTION_RADIUS:
                current_status = 1

                if self.is_periodic:
                    if next_idx == 0:
                        progress["laps"] += 1
                        current_status = 2
                        if progress["laps"] >= self.required_laps:
                            current_status = 3  # race finished

                    progress["next_idx"] = (next_idx + 1) % len(self.checkpoints)

                else:
                    if next_idx == last_checkpoint_idx:
                        progress["laps"] = 1
                        current_status = 3
                    else:
                        progress["next_idx"] = next_idx + 1

                max_status = max(max_status, current_status)

        return max_status

    @property
    def record(self) -> dict:
        return self._record

    def fraction_completed(self, car):
        circuit = self.circuit
        if circuit is None:
            return 0.0, 0.0, 0.0

        if car.car_id not in self._record:
            total_m = circuit.get_total_distance() * circuit.required_laps
            return 0.0, total_m, 0.0

        progress = self._record[car.car_id]
        next_idx = progress["next_idx"]
        prev_idx = (next_idx - 1) % len(circuit.global_checkpoints)

        # Distance accumulated up to previous checkpoint (meters)
        dist_before = circuit.distance_from_start_to_checkpoint(prev_idx)

        # Fraction of the current segment (0..1)
        frac = circuit.percent_along_segment(car.pos, prev_idx, next_idx)

        # Segment length (meters)
        seg_len = circuit.distance_between_checkpoints(prev_idx, next_idx)

        # Laps already completed
        laps_done = progress.get("laps", 0)

        # Progress in meters including laps
        progress_m = dist_before + frac * seg_len + laps_done * circuit.get_total_distance()

        total_m = circuit.get_total_distance() * circuit.required_laps

        percent = min(1.0, progress_m / total_m) if total_m > 0 else 0.0

        return float(percent)

    # Forward to circuit methods for consistency
    def distance_to_next_checkpoint(self, car) -> float:
        car_id = car.car_id
        if car_id not in self._record:
            print("Car ID not found in race record.")
            return float('inf')

        progress = self._record[car_id]
        next_idx = progress["next_idx"]

        # Normalize next_idx for periodic/non-periodic cases
        if next_idx >= len(self.checkpoints):
            next_idx = 0 if self.is_periodic else len(self.checkpoints) - 1

        # Delegate to circuit for consistent metric
        return float(self.circuit.distance_to_next_checkpoint(car.pos, next_idx))

    def distance_between_checkpoints(self, idx1: int, idx2: int) -> float:
        # Delegate to circuit for consistent distances along path
        return float(self.circuit.distance_between_checkpoints(idx1, idx2))

    def distance_along_path(self, car) -> float:
        car_id = car.car_id
        if car_id not in self._record:
            # default to distance between checkpoint 0 and 1
            return max(1.0, float(self.circuit.distance_between_checkpoints(0, 1)))

        next_idx = self._record[car_id]["next_idx"]
        prev_idx = (next_idx - 1) if next_idx > 0 else (len(self.checkpoints) - 1)
        dist = float(self.circuit.distance_between_checkpoints(prev_idx, next_idx))
        return max(dist, 1.0)

    def get_thickness(self) -> float:
        return self.thickness

    def reset(self):
        self._record = {}

from entities.roads.spline_road import SplineRoad
import numpy as np


class Circuit:
    def __init__(self, canvas, name: str, data: dict = None):
        self.canvas = canvas
        self.name = name
        self.roads = []
        self.global_checkpoints = []
        self.required_laps = 1

        # Distance from checkpoint i to i+1
        self.checkpoint_distances = np.array([], dtype=float)
        
        # Distance from checkpoint 0 to checkpoint i
        self.cumulative_checkpoint_distances = np.array([0.0], dtype=float)

        self.total_distance = 0.0
        self.is_periodic = False

        if data:
            self.load_data(data)

    def load_data(self, data: dict, name = None):
        if name:
            self.name = name
        self.required_laps = data.get("laps", 1)
        self.roads = []
        self.global_checkpoints = []
        self.total_distance = 0.0

        for road_data in data.get("roads", []):
            road = SplineRoad(self.canvas, road_data)
            self.roads.append(road)
            # Extend checkpoints of current road
            self.global_checkpoints.extend(road.checkpoints)
            # Accumulate approximate road length (from smooth_points)
            if hasattr(road, "length") and len(road.smooth_points) > 1:
                self.total_distance += float(road.length)

        if len(self.global_checkpoints) > 0:
            self.global_checkpoints = np.array(self.global_checkpoints, dtype=float)
        else:
            self.global_checkpoints = np.array([], dtype=float)

        if len(self.global_checkpoints) > 1:
            self.is_periodic = np.allclose(self.global_checkpoints[0], self.global_checkpoints[-1])
        else:
            self.is_periodic = False

        # Compute per-checkpoint distances and cumulative sums
        self._compute_checkpoint_distances()

        print(f"  └─ {len(self.roads)} road segment(s)")
        print(f"  └─ {len(self.global_checkpoints)} checkpoint(s)")

    # function to compute some distances
    # I am aware this duplicates some code in SplineRoad, but is better to have it here.
    # It is a thing that is computed only when loading a circuit, so it is not a problem.
    def _compute_checkpoint_distances(self):
        pts = self.global_checkpoints
        n = len(pts)
        if n < 2:
            self.checkpoint_distances = np.array([], dtype=float)
            self.cumulative_checkpoint_distances = np.array([0.0], dtype=float)
            raise ValueError("Not enough checkpoints to compute distances.")

        # Distances from one checkpoint to the next
        diffs = np.diff(pts, axis=0)
        dists = np.sqrt(np.sum(diffs**2, axis=1)).astype(float)

        if self.is_periodic:
            last_to_first = float(np.linalg.norm(pts[0] - pts[-1]))
            dists = np.concatenate([dists, np.array([last_to_first], dtype=float)])

        self.checkpoint_distances = dists

        # Cummulative distances
        cum = np.concatenate([[0.0], np.cumsum(dists)])
        self.cumulative_checkpoint_distances = cum

        # If total_distance (from roads) is zero, fallback to checkpoint sum
        sum_dists = float(np.sum(dists)) if dists.size > 0 else 0.0
        if self.total_distance <= 0.0:
            self.total_distance = sum_dists
        else:
            # keep road-based total_distance when available, but ensure it's > 0
            pass

    @property
    def initial_angle(self) -> float:
        if len(self.roads) > 0:
            return self.roads[0].initial_angle
        return 0.0
    
    def corners(self) -> tuple:
        x_min, y_min = float('inf'), float('inf')
        x_max, y_max = float('-inf'), float('-inf')
        for road in self.roads:
            points = road.get_points()
            x_min, y_min = min(x_min, np.min(points[:, 0])), min(y_min, np.min(points[:, 1]))
            x_max, y_max = max(x_max, np.max(points[:, 0])), max(y_max, np.max(points[:, 1]))
        width = x_max - x_min
        height = y_max - y_min
        # Add some padding
        padding = 50
        width += padding
        height += padding
        distance = max(width, height)
        centre = [(x_min + x_max) / 2, (y_min + y_max) / 2]
        return centre, distance, distance
    
    def get_total_distance(self) -> float:
        return float(self.total_distance)

    def is_inside(self, pos) -> bool:
        return any(road.is_inside(pos) for road in self.roads)

    def get_checkpoint(self, index: int):
        if 0 <= index < len(self.global_checkpoints):
            return self.global_checkpoints[index]
        return None

    def road_thickness(self, idx_road=0) -> float:
        return self.roads[idx_road].thickness

    def get_tangent_at(self, pos):
        return self.roads[0].get_tangent_at_pos(pos)

    def distance_to_next_checkpoint(self, pos, next_checkpoint_idx: int) -> float:
        checkpoint = self.get_checkpoint(next_checkpoint_idx)
        if checkpoint is None:
            return float('inf')
        return float(np.linalg.norm(np.array(pos) - np.array(checkpoint)))

    @property
    def checkpoints(self) -> list:
        return list(self.global_checkpoints)

    def show(self, wv, race_data=None):
        for road in self.roads:
            road.show(wv)

    def destroy(self):
        for road in self.roads:
            road.destroy()
        self.roads = []
        self.global_checkpoints = []
        self.checkpoint_distances = np.array([], dtype=float)
        self.cumulative_checkpoint_distances = np.array([0.0], dtype=float)
        self.total_distance = 0.0
        self.is_periodic = False


    def distance_between_checkpoints(self, idx1: int, idx2: int) -> float:
        number_of_checkpoints = len(self.global_checkpoints)
        if number_of_checkpoints == 0:
            return float('inf')

        # bounds check
        if not (0 <= idx1 < number_of_checkpoints) or not (0 <= idx2 < number_of_checkpoints):
            return float('inf')

        if idx1 == idx2:
            return 0.0

        # If checkpoint_distances length equals number_of_checkpoints (periodic), distances[i] is i->i+1 (mod N)
        # If non-periodic, checkpoint_distances length is number_of_checkpoints-1 and distances[i] is i->i+1 for i=0..N-2
        dists = self.checkpoint_distances
        if dists.size == 0:
            return float('inf')

        if idx2 > idx1:
            # sum distances idx1 -> idx2 (not including idx2->next)
            return float(np.sum(dists[idx1:idx2]))
        else:
            if self.is_periodic:
                part1 = np.sum(dists[idx1:])  
                part2 = np.sum(dists[:idx2])  
                return float(part1 + part2)
            else:
                part1 = np.sum(dists[idx1:]) if idx1 < dists.size else 0.0
                part2 = np.sum(dists[:idx2]) if idx2 > 0 else 0.0
                return float(part1 + part2)

    def distance_from_start_to_checkpoint(self, idx: int) -> float:
        if idx <= 0:
            return 0.0
        if idx >= len(self.cumulative_checkpoint_distances):
            return float(self.cumulative_checkpoint_distances[-1])
        return float(self.cumulative_checkpoint_distances[idx])

    def percent_along_segment(self, pos, prev_idx: int, next_idx: int) -> float:
        p_prev = self.get_checkpoint(prev_idx)
        p_next = self.get_checkpoint(next_idx)
        if p_prev is None or p_next is None:
            return 0.0

        seg_vec = np.array(p_next) - np.array(p_prev)
        seg_len = np.linalg.norm(seg_vec)
        if seg_len <= 1e-6:
            return 0.0

        vec = np.array(pos) - np.array(p_prev)
        proj = float(np.dot(vec, seg_vec) / seg_len) 
        frac = np.clip(proj / seg_len, 0.0, 1.0)
        return float(frac)

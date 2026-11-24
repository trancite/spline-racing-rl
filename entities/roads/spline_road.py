import numpy as np
import math
from scipy.interpolate import CubicSpline, make_interp_spline
from worldview.WPoint import WPoint
from core.config import GameConfig, Colors

# Fundamental class
# It manages the roads. 
class SplineRoad:
    def __init__(self, canvas, data: dict, k: int = 3):
        self.canvas = canvas
        # Coordinates
        self.w_points = np.array([[p["x"], p["y"]] for p in data["points"]])
        # Checkpoints. A checkpoint is a node of the spline
        self.checkpoints = self.w_points
        self.checkpoint_radius = GameConfig.CHECKPOINT_RADIUS
        self.thickness = data["thickness"]
        self.color = data.get("color", Colors.ROAD_ASPHALT)
        self.dash_offset = 0
        
        # Spline attributes
        self.spline = None
        # Amount of points in the smooth spline
        self.num_points = 0
        self.degree = data.get("degree", k)
        
        # I make this to avoid atribute error
        self.smooth_points = np.array([], dtype=np.float32)
        self.tangents = np.array([], dtype=np.float32)
        self.length = 0.0

        # If the last point is the first one, is periodic
        self.road_type = "natural"
        if len(self.w_points) > 2 and np.allclose(self.w_points[0], self.w_points[-1]):
            self.road_type = "periodic"

        # Points for the worldview
        self.WPoints = [WPoint(p[0], p[1]) for p in self.w_points]

        # Computation of points and tangents (tangents only for the AI)
        self.smooth_points = self._calculate_spline()

        self.initial_angle = np.arctan2(self.tangents[0][1], self.tangents[0][0])

        # Graphical elements (only if there is a canvas)
        if self.canvas:
            self._create_canvas_elements()

    # FUNDAMENTAL FUNCTION
    def _calculate_spline(self) -> np.ndarray:
        # Checkpoints
        n_points = len(self.w_points)
        
        # We need at least 2
        if n_points < 2:
            self.tangents = np.array([[1.0, 0.0]], dtype=np.float32)
            raise ValueError("It is needed at least two points to create a road. What do you want me to connect?")

        # Computation to get t
        # t is a list of how many points we are going to store of the road

        # t is a parameter that goes from 0 to total approximately the total length of the path
        diffs = np.diff(self.w_points, axis=0)
        distances = np.sqrt(np.sum(diffs**2, axis=1))
        # at position i it has the distance from point 0 to i
        t = np.concatenate(([0], np.cumsum(distances)))
        self.length = t[-1]
        
        # This is not necessary (we raise error with less than 2 points). I leave it for safety
        if self.length == 0:
            self.tangents = np.zeros((n_points, 2), dtype=np.float32)
            self.tangents[:, 0] = 1.0
            return self.w_points

        # Needed for the spline functions
        t_norm = t / self.length

        # Step_size we make in the real road. 
        step_size = max(self.thickness / 4, 1.0)

        num_points = int(self.length / step_size)
        num_points = max(200, min(num_points, 2000))
        self.num_points = num_points
        
        # Set upper bound for degree 
        max_degree = n_points - 1
        actual_degree = min(self.degree, max_degree)

        # Generate the spline object (CubicSpline or InterpSpline).
        # As far as I know InterpSpline is not exactly the same with degree = 3 as CubicSpline
        # However, I suppose there are pretty similar

        try:
            if actual_degree == 3 and self.road_type == "natural":
                cs = CubicSpline(t_norm, self.w_points, bc_type="natural")
            elif self.road_type == "periodic" and n_points > actual_degree:
                cs = make_interp_spline(t_norm, self.w_points, k=actual_degree, bc_type="periodic")
            else:
                cs = make_interp_spline(t_norm, self.w_points, k=actual_degree)
        except Exception as e:
            print(f"⚠️ Could not calculate a degree-{actual_degree} spline: {e}")
            # Try degree 3 when possible, otherwise fall back to degree 1.
            new_k = 3 if n_points > 3 else 1
            print(f"Falling back to degree {new_k}")
            cs = make_interp_spline(t_norm, self.w_points, k=new_k)

        self.spline = cs
        t_smooth = np.linspace(0, 1, num_points)
        
        # points is an array of shape (num_points, 2)
        points = cs(t_smooth).astype(np.float32)
        
        # nu=1 is the first derivative (tangent)
        derivatives = cs(t_smooth, nu=1)
        norms = np.linalg.norm(derivatives, axis=1, keepdims=True)
        # Normalize with an epsilon to avoid division by zero
        self.tangents = (derivatives / (norms + 1e-9)).astype(np.float32)
        
        return points
    
    def get_points(self) -> np.ndarray:
        return self.smooth_points

    def get_nearest_info(self, pos):
        # pos is a numpy array of shape (2,). Used for lidiars in AI
        if self.smooth_points.size == 0:
            return 0, 9999.9, np.array([1.0, 0.0], dtype=np.float32)

        # index of point nearest to pos (used for the car position and lidiars)
        # distance to next part of the road
        # tangent at that point
        deltas = self.smooth_points - pos
        dist_sq = np.sum(deltas**2, axis=1)
        idx = np.argmin(dist_sq)

        return idx, math.sqrt(dist_sq[idx]), self.tangents[idx]

    def is_inside(self, pos) -> bool:
        _, dist, _ = self.get_nearest_info(pos)
        return dist < (self.thickness / 2.0)

    def get_tangent_at_pos(self, pos):
        _, _, tangent = self.get_nearest_info(pos)
        return tangent

    def _create_canvas_elements(self):
        self.outer_glow_id = self.canvas.create_line(0, 0, 0, 0, fill=Colors.ROAD_EDGE_GLOW, capstyle="round", joinstyle="round")
        self.border_id = self.canvas.create_line(0, 0, 0, 0, fill=Colors.ROAD_BORDER, capstyle="round", joinstyle="round")
        self.asphalt_id = self.canvas.create_line(0, 0, 0, 0, fill=Colors.ROAD_ASPHALT, capstyle="round", joinstyle="round")
        self.inner_stripe_id = self.canvas.create_line(0, 0, 0, 0, fill=Colors.ROAD_EDGE_GLOW, capstyle="round", joinstyle="round", stipple='gray50')
        self.center_line_id = self.canvas.create_line(0, 0, 0, 0, fill=Colors.ROAD_CENTER_LINE, capstyle="round", joinstyle="round")
        self.node_ids = [self.canvas.create_oval(0, 0, 0, 0, fill=Colors.CHECKPOINT_GLOW, outline=Colors.UI_ACCENT, width=2) for _ in self.WPoints]

    def show(self, wv):
        if not self.canvas or len(self.smooth_points) < 2:
            return

        world_x = self.smooth_points[:, 0]
        world_y = self.smooth_points[:, 1]

        view_x = (world_x - wv.wMin.p[0]) * wv.scale_x + wv.vMin.p[0]
        view_y = (wv.wMax.p[1] - world_y) * wv.scale_y + wv.vMin.p[1]

        flat_coords = np.stack((view_x, view_y), axis=-1).flatten().tolist()
        road_w = self.thickness * wv.scale_x
        
        self.canvas.coords(self.outer_glow_id, *flat_coords)
        self.canvas.itemconfig(self.outer_glow_id, width=road_w * 1.25)
        self.canvas.coords(self.border_id, *flat_coords)
        self.canvas.itemconfig(self.border_id, width=road_w * 1.15)
        self.canvas.coords(self.asphalt_id, *flat_coords)
        self.canvas.itemconfig(self.asphalt_id, width=road_w)
        self.canvas.coords(self.inner_stripe_id, *flat_coords)
        self.canvas.itemconfig(self.inner_stripe_id, width=road_w * 0.9)
        self.canvas.coords(self.center_line_id, *flat_coords)
        self.canvas.itemconfig(self.center_line_id, width=max(2, road_w * 0.06), dashoffset = 0)

        scale = wv.scale_x
        node_radius = self.checkpoint_radius * scale
        for i, wp in enumerate(self.WPoints):
            v_p = wv.worldToViewXY(wp.p[0], wp.p[1])
            self.canvas.coords(self.node_ids[i], v_p.x - node_radius, v_p.y - node_radius, v_p.x + node_radius, v_p.y + node_radius)
            self.canvas.tag_raise(self.node_ids[i])

    def destroy(self):
        if not self.canvas: return
        for pid in [self.outer_glow_id, self.border_id, self.asphalt_id, self.inner_stripe_id, self.center_line_id]:
            self.canvas.delete(pid)
        for node_id in self.node_ids:
            self.canvas.delete(node_id)

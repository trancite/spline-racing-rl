import math
import numpy as np

from core.config import Colors


class CarRenderer:
    def __init__(self, canvas, data: dict, physics):
        self.canvas = canvas
        self.physics = physics
        
        self.width = data.get('width', 4.5)
        self.height = data.get('height', 2)
        
        is_player = data.get('is_player', False)
        if not canvas:
            return 
        
        base_color = data.get('color', Colors.CAR_BODY_PLAYER if is_player else Colors.CAR_BODY_AI)
        self.body_color = base_color
        
        self._create_canvas_elements(base_color)
        
        self._init_particle_systems()
        
    def _create_canvas_elements(self, base_color: str):

        self.glow_id = self.canvas.create_polygon(
            0, 0, 0, 0,
            fill='', outline=base_color, width=6, stipple='gray50'
        )
        
        self.body_id = self.canvas.create_polygon(
            0, 0, 0, 0,
            fill=base_color, outline=Colors.CAR_OUTLINE, width=2
        )
        
        self.underglow_id = self.canvas.create_line(
            0, 0, 0, 0,
            fill=Colors.NEON_CYAN, width=3, stipple='gray50'
        )
        
        self.window_id = self.canvas.create_polygon(
            0, 0, 0, 0,
            fill=Colors.CAR_WINDOW, outline="#0088aa", width=1
        )
        
        self.light_l_id = self.canvas.create_polygon(
            0, 0, 0, 0, fill=Colors.CAR_HEADLIGHT_ON
        )
        self.light_r_id = self.canvas.create_polygon(
            0, 0, 0, 0, fill=Colors.CAR_HEADLIGHT_ON
        )
        
        self.tail_l_id = self.canvas.create_polygon(
            0, 0, 0, 0, fill=Colors.CAR_TAILLIGHT_OFF
        )
        self.tail_r_id = self.canvas.create_polygon(
            0, 0, 0, 0, fill=Colors.CAR_TAILLIGHT_OFF
        )
        
    def _init_particle_systems(self):
        self.trail_particles = []
        self.max_trail_particles = 200
        
        self.spark_particles = []
        self.max_sparks = 50
        
        self.speed_lines = []
        self.max_speed_lines = 20
        
        self.ghost_trail = []
        self.max_ghosts = 5
        self.ghost_timer = 0
        
        self.smoke_particles = []
        
    def _transform_points(self, local_points: np.ndarray) -> np.ndarray:
        c, s = np.cos(self.physics.angle), np.sin(self.physics.angle)
        rotation_matrix = np.array([[c, -s], [s, c]])
        return np.dot(local_points, rotation_matrix.T) + self.physics.pos
    
    def _draw_polygon(self, poly_id, local_pts: np.ndarray, wv):
        world_pts = self._transform_points(local_pts)
        view_coords = []
        for p in world_pts:
            vp = wv.worldToViewXY(p[0], p[1])
            view_coords.extend([vp.x, vp.y])
        self.canvas.coords(poly_id, *view_coords)
        
    def _update_lights(self):
        tail_color = Colors.CAR_TAILLIGHT_ON if self.physics.is_braking else Colors.CAR_TAILLIGHT_OFF
        self.canvas.itemconfig(self.tail_l_id, fill=tail_color)
        self.canvas.itemconfig(self.tail_r_id, fill=tail_color)
        
        if self.physics.speed_ratio > 0.8:
            intensity = int(255 * (0.9 + 0.1 * math.sin(np.random.random() * math.pi)))
            headlight_color = f'#{intensity:02x}{intensity:02x}00'
            self.canvas.itemconfig(self.light_l_id, fill=headlight_color)
            self.canvas.itemconfig(self.light_r_id, fill=headlight_color)
            
    def _update_glow(self):
        if self.physics.speed_ratio > 0.6:
            glow_width = 4 + int(self.physics.speed_ratio * 4)
            self.canvas.itemconfig(self.glow_id, width=glow_width, outline=self.body_color)
        else:
            self.canvas.itemconfig(self.glow_id, outline='')
    
    def _update_underglow(self, wv):
        w, h = self.width / 2, self.height / 2
        left_pt = self._transform_points(np.array([[-w * 0.8, 0]]))[0]
        right_pt = self._transform_points(np.array([[w * 0.8, 0]]))[0]
        
        vp1 = wv.worldToViewXY(left_pt[0], left_pt[1])
        vp2 = wv.worldToViewXY(right_pt[0], right_pt[1])
        
        self.canvas.coords(self.underglow_id, vp1.x, vp1.y, vp2.x, vp2.y)
        
        if self.physics.speed_ratio > 0.3:
            width = 2 + int(self.physics.speed_ratio * 4)
            self.canvas.itemconfig(self.underglow_id, width=width, fill=Colors.NEON_CYAN)
        else:
            self.canvas.itemconfig(self.underglow_id, width=2, fill=Colors.NEON_CYAN)
    
    def _spawn_drift_sparks(self, wv):
        if not self.physics.is_drifting or len(self.spark_particles) >= self.max_sparks:
            return
        
        w, h = self.width / 2, self.height / 2
        wheel_positions = [
            np.array([-w * 0.8, h * 0.9]),
            np.array([-w * 0.8, -h * 0.9])
        ]
        
        for local_pos in wheel_positions:
            if np.random.random() > 0.5:
                world_pos = self._transform_points(np.array([local_pos]))[0]
                
                spark_vel = np.array([
                    np.random.uniform(-3, 3),
                    np.random.uniform(-3, 3)
                ]) - self.physics.velocity * 0.1
                
                vp = wv.worldToViewXY(world_pos[0], world_pos[1])
                size = np.random.uniform(2, 4)
                
                colors = [Colors.NEON_YELLOW, Colors.NEON_ORANGE, '#ffffff']
                color = np.random.choice(colors)
                
                spark_id = self.canvas.create_oval(
                    vp.x - size, vp.y - size, vp.x + size, vp.y + size,
                    fill=color, outline=''
                )
                
                self.spark_particles.append({
                    'id': spark_id,
                    'pos': world_pos.copy(),
                    'vel': spark_vel,
                    'life': 0.3,
                    'max_life': 0.3,
                    'size': size
                })
    
    def _update_sparks(self, wv):
        remaining = []
        dt = self.physics.dt
        
        for spark in self.spark_particles:
            spark['life'] -= dt
            spark['pos'] += spark['vel'] * dt
            spark['vel'][1] += 15 * dt  # gravity
            
            if spark['life'] > 0:
                alpha = spark['life'] / spark['max_life']
                size = spark['size'] * alpha
                vp = wv.worldToViewXY(spark['pos'][0], spark['pos'][1])
                self.canvas.coords(
                    spark['id'],
                    vp.x - size, vp.y - size, vp.x + size, vp.y + size
                )
                remaining.append(spark)
            else:
                self.canvas.delete(spark['id'])
        
        self.spark_particles = remaining
    
    def _spawn_speed_lines(self, wv):
        if self.physics.speed_ratio < 0.7 or len(self.speed_lines) >= self.max_speed_lines:
            return
        
        if np.random.random() > 0.3:
            return
        
        w, h = self.width / 2, self.height / 2
        
        side = np.random.choice([-1, 1])
        local_start = np.array([
            np.random.uniform(-w, w * 0.5),
            side * h * np.random.uniform(1.2, 2.0)
        ])
        
        world_start = self._transform_points(np.array([local_start]))[0]
        line_length = 1.5 + self.physics.speed_ratio * 3
        world_end = world_start - self.physics.direction * line_length
        
        vp1 = wv.worldToViewXY(world_start[0], world_start[1])
        vp2 = wv.worldToViewXY(world_end[0], world_end[1])
        
        line_id = self.canvas.create_line(
            vp1.x, vp1.y, vp2.x, vp2.y,
            fill='#ffffff', width=2, stipple='gray50'
        )
        
        self.speed_lines.append({
            'id': line_id,
            'start': world_start.copy(),
            'end': world_end.copy(),
            'life': 0.15,
            'max_life': 0.15
        })
    
    def _update_speed_lines(self, wv):
        remaining = []
        dt = self.physics.dt
        
        for line in self.speed_lines:
            line['life'] -= dt
            line['start'] -= self.physics.velocity * dt * 0.5
            line['end'] -= self.physics.velocity * dt * 0.5
            
            if line['life'] > 0:
                alpha = line['life'] / line['max_life']
                vp1 = wv.worldToViewXY(line['start'][0], line['start'][1])
                vp2 = wv.worldToViewXY(line['end'][0], line['end'][1])
                self.canvas.coords(line['id'], vp1.x, vp1.y, vp2.x, vp2.y)
                stipple = 'gray25' if alpha < 0.5 else 'gray50'
                self.canvas.itemconfig(line['id'], stipple=stipple)
                remaining.append(line)
            else:
                self.canvas.delete(line['id'])
        
        self.speed_lines = remaining
    
    def _update_ghost_trail(self, wv):
        dt = self.physics.dt
        self.ghost_timer += dt
        
        if self.physics.speed_ratio > 0.5 and self.ghost_timer > 0.05:
            self.ghost_timer = 0
            
            if len(self.ghost_trail) >= self.max_ghosts:
                old = self.ghost_trail.pop(0)
                self.canvas.delete(old['id'])
            
            w, h = self.width / 2, self.height / 2
            body_pts = np.array([[w, h], [w, -h], [-w, -h], [-w, h]])
            world_pts = self._transform_points(body_pts)
            
            view_coords = []
            for p in world_pts:
                vp = wv.worldToViewXY(p[0], p[1])
                view_coords.extend([vp.x, vp.y])
            
            ghost_id = self.canvas.create_polygon(
                *view_coords,
                fill=self.body_color, outline='', stipple='gray25'
            )
            self.canvas.tag_lower(ghost_id)
            
            self.ghost_trail.append({
                'id': ghost_id,
                'life': 0.2,
                'max_life': 0.2,
                'points': world_pts.copy()
            })
        
        remaining = []
        for ghost in self.ghost_trail:
            ghost['life'] -= dt
            if ghost['life'] > 0:
                view_coords = []
                for p in ghost['points']:
                    vp = wv.worldToViewXY(p[0], p[1])
                    view_coords.extend([vp.x, vp.y])
                self.canvas.coords(ghost['id'], *view_coords)
                
                alpha = ghost['life'] / ghost['max_life']
                stipple = 'gray12' if alpha < 0.3 else 'gray25' if alpha < 0.6 else 'gray50'
                self.canvas.itemconfig(ghost['id'], stipple=stipple)
                remaining.append(ghost)
            else:
                self.canvas.delete(ghost['id'])
        
        self.ghost_trail = remaining
    
    def _spawn_trail_particle(self, wv):
        if self.physics.speed_ratio > 0.6 and len(self.trail_particles) < self.max_trail_particles:
            offset = self.physics.direction * (-self.width * 0.6)
            spawn_pos = self.physics.pos + offset
            
            lateral_spread = self.height * 0.4
            spawn_pos += np.array([
                np.random.uniform(-lateral_spread, lateral_spread),
                np.random.uniform(-lateral_spread, lateral_spread)
            ])
            
            vp = wv.worldToViewXY(spawn_pos[0], spawn_pos[1])
            base_size = max(2, min(self.height * 0.3, 8))
            size = base_size * np.random.uniform(0.5, 1.2)
            particle_id = self.canvas.create_oval(
                vp.x - size, vp.y - size, vp.x + size, vp.y + size,
                fill=Colors.SPEED_TRAIL, outline=''
            )
            
            self.trail_particles.append({
                'id': particle_id,
                'life': 0.5,
                'max_life': 0.5,
                'pos': spawn_pos.copy(),
                'size': size
            })
            
    def _update_particles(self, wv):
        remaining = []
        dt = self.physics.dt
        for particle in self.trail_particles:
            particle['life'] -= dt
            if particle['life'] > 0:
                alpha = particle['life'] / particle.get('max_life', 0.5)
                size = particle.get('size', 5) * alpha
                vp = wv.worldToViewXY(particle['pos'][0], particle['pos'][1])
                self.canvas.coords(
                    particle['id'],
                    vp.x - size, vp.y - size, vp.x + size, vp.y + size
                )
                remaining.append(particle)
            else:
                self.canvas.delete(particle['id'])
        self.trail_particles = remaining
        
    def render(self, wv):
        w, h = self.width / 2, self.height / 2
        
        body_pts = np.array([[w, h], [w, -h], [-w, -h], [-w, h]])
        self._draw_polygon(self.glow_id, body_pts * 1.1, wv)
        self._draw_polygon(self.body_id, body_pts, wv)
        
        win_pts = np.array([
            [0.5*w, 0.75*h], [0.5*w, -0.75*h],
            [0.0*w, -0.85*h], [0.0*w, 0.85*h]
        ])
        self._draw_polygon(self.window_id, win_pts, wv)
        
        l_front = np.array([[w, 0.85*h], [w, 0.5*h], [0.85*w, 0.45*h], [0.85*w, 0.9*h]])
        r_front = np.array([[w, -0.85*h], [w, -0.5*h], [0.85*w, -0.45*h], [0.85*w, -0.9*h]])
        self._draw_polygon(self.light_l_id, l_front, wv)
        self._draw_polygon(self.light_r_id, r_front, wv)
        
        l_back = np.array([[-0.9*w, 0.9*h], [-0.9*w, 0.55*h], [-w, 0.55*h], [-w, 0.9*h]])
        r_back = np.array([[-0.9*w, -0.9*h], [-0.9*w, -0.55*h], [-w, -0.55*h], [-w, -0.9*h]])
        self._draw_polygon(self.tail_l_id, l_back, wv)
        self._draw_polygon(self.tail_r_id, r_back, wv)
        
        self._update_lights()
        self._update_glow()
        self._update_underglow(wv)
        self._update_ghost_trail(wv)
        self._spawn_drift_sparks(wv)
        self._update_sparks(wv)
        self._spawn_speed_lines(wv)
        self._update_speed_lines(wv)
        self._spawn_trail_particle(wv)
        self._update_particles(wv)
        
    def destroy(self):
        for pid in [self.glow_id, self.body_id, self.underglow_id, self.window_id,
                    self.light_l_id, self.light_r_id,
                    self.tail_l_id, self.tail_r_id]:
            self.canvas.delete(pid)
        for p in self.trail_particles:
            self.canvas.delete(p['id'])
        for s in self.spark_particles:
            self.canvas.delete(s['id'])
        for l in self.speed_lines:
            self.canvas.delete(l['id'])
        for g in self.ghost_trail:
            self.canvas.delete(g['id'])

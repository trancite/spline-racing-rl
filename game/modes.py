import time
import math
from entities.RoadMaker import RoadMaker
from entities.roads import SplineRoad
from core.config import *
from game.race_manager import RaceManager
from pathlib import Path
import os
from pathlib import Path
import json
from entities import Circuit, Car 
import tkinter.font as tkfont
from game.model_loader import AIController


DATA_PATH = Path(__file__).parent.parent / "data"
CAMPAING_CIRCUITS_PATH = DATA_PATH / "campaing_circuits"
CUSTOM_CIRCUITS_PATH = DATA_PATH / "custom_circuits"

TRAINING_DATA_PATH = Path(__file__).parent.parent / "training" / "training_data"
BASE_DIR = Path(__file__).resolve().parent     
ROOT_DIR = BASE_DIR.parent                    
TARGET_DIR = ROOT_DIR / "data" / "custom_circuits" 
MODEL_DATA_PATH = Path(__file__).parent.parent / "training" / "models"
AI_BOT = "ppo_all_circuits_default_ai_interrupted.zip"


class BaseMode:
    def __init__(self, canvas):
        self.canvas = canvas
        self.circuit = Circuit(canvas, "Circuit")
        self.race_manager = RaceManager()
        self.cars = []
        self.circuit_files = []
        self.current_idx = 0
        self.start_time = 0
        self._loading_next = False
        self.camera_x, self.camera_y = 0, 0
        self.absolute_camera = False

    def sort_circuits(self):
        with_num, without_num = [], []
        for f in self.circuit_files:
            idx = Path(f).stem.rsplit("_", 1)[-1]
            if idx.isdigit(): with_num.append((int(idx), f))
            else: without_num.append(f)
        with_num.sort(key=lambda x: x[0])
        self.circuit_files = [f for _, f in with_num] + without_num

    def clear_entities(self):
        for car in self.cars: car.destroy()
        self.cars = []
        self.circuit.destroy()

    def _apply_smooth_camera(self, controller, car):
        if not car: return
        target_x, target_y = car.pos
        factor = 1.0 - math.exp(-GameConfig.CAMERA_SMOOTHING * controller.dt)
        self.camera_x += (target_x - self.camera_x) * factor
        self.camera_y += (target_y - self.camera_y) * factor
        controller.wv.center(self.camera_x, self.camera_y, 
                            GameConfig.CAMERA_FOLLOW_WIDTH, GameConfig.CAMERA_FOLLOW_HEIGHT)


class MenuMode:
    def __init__(self, canvas):
        self.canvas = canvas
        self.font_main = tkfont.Font(family="Liberation Sans", size=24, weight="bold")
        self.font_sub = tkfont.Font(family="Liberation Sans", size=10, weight="bold")
        self.font_warning = tkfont.Font(family="Liberation Sans", size=12, weight="bold")
        self.options = [
            ("1 - Campaign Single Player", GameState.RACING),
            ("2 - Campaign Multiplayer", GameState.RACING_MULTIPLAYER),
            ("3 - Creating Mode", GameState.CREATING),
            ("4 - Your Custom Circuits", GameState.RACING_CUSTOM),
            ("5 - Training Mode (AI Demo)", GameState.TRAINING),
            ("6 - Player vs AI", GameState.PLAYER_VS_AI),
        ]
        self.selected_index, self.warning_timer = 0, 0

    def _has_custom(self):
        if not CUSTOM_CIRCUITS_PATH.exists(): return False
        return any(f.endswith(".json") for f in os.listdir(CUSTOM_CIRCUITS_PATH))

    def enter(self, controller, from_state):
        for m in controller.modes.values():
            if hasattr(m, 'clear_entities'): m.clear_entities()
        controller.wv.center(GameConfig.WORLD_MAX_X//2, GameConfig.WORLD_MAX_Y//2, GameConfig.WORLD_MAX_X, GameConfig.WORLD_MAX_Y)

    def update(self, controller, keys):
        self.warning_timer = max(0, self.warning_timer - 1)
        if "Up" in keys: self.selected_index = (self.selected_index - 1) % len(self.options); keys.discard("Up")
        if "Down" in keys: self.selected_index = (self.selected_index + 1) % len(self.options); keys.discard("Down")
        
        target_state = None
        if "Return" in keys:
            label, target_state = self.options[self.selected_index]
            if "Custom" in label and not self._has_custom(): target_state = None; self.warning_timer = 100
            keys.discard("Return")

        for k, state in {"1":0,"2":1,"3":2,"4":3,"5":4,"6":5}.items():
            if k in keys:
                if k == "4" and not self._has_custom(): self.warning_timer = 100
                else: target_state = self.options[state][1]
                keys.discard(k)
        
        if target_state: controller.set_state(target_state)

    def render(self, controller):
        cx, cy = GameConfig.WINDOW_WIDTH // 2, GameConfig.WINDOW_HEIGHT // 2
        
        controller.canvas.create_text(
            cx + 3, cy - 177, 
            text="CAR RACING GAME", 
            fill="#004422", font=self.font_main, tags="road_marker"
        )
        controller.canvas.create_text(
            cx, cy - 180, 
            text="CAR RACING GAME", 
            fill="#00FF88", font=self.font_main, tags="road_marker"
        )

        controls_top = "Arrows to Navigate • Enter to Select • 1-6 Quick Load"
        controller.canvas.create_text(
            cx, cy - 135, 
            text=controls_top,
            fill="#888888", font=("Arial", 9, "bold"), tags="road_marker"
        )

        for i, (label, _) in enumerate(self.options):
            y_pos = cy - 40 + i * 45
            is_selected = (i == self.selected_index)
            
            if is_selected:
                controller.canvas.create_rectangle(
                    cx - 180, y_pos - 18, cx + 180, y_pos + 18,
                    outline="#FFEA00", fill="#1a1a1a", width=2, tags="road_marker"
                )
                color = "#FFEA00"
                text_label = f"»  {label.upper()}  «"
                font_style = self.font_sub 
            else:
                color = "#AAAAAA"
                text_label = label
                font_style = self.font_sub

            controller.canvas.create_text(
                cx, y_pos, 
                text=text_label, 
                fill=color, font=font_style, tags="road_marker"
            )

        if self.warning_timer > 0:
            controller.canvas.create_rectangle(
                cx - 150, cy + 210, cx + 150, cy + 240,
                fill="#330000", outline="#FF4444", tags="road_marker"
            )
            controller.canvas.create_text(
                cx, cy + 225, 
                text="NO CUSTOM MAPS FOUND!", 
                fill="#FF4444", font=("Arial", 10, "bold"), tags="road_marker"
            )

        controller.canvas.create_line(cx - 200, cy + 260, cx + 200, cy + 260, fill="#333333", tags="road_marker")
        
        info_text = (
            "Every .json is editable! Change speed, grip, and friction.\n"
            "Compete in the Leaderboard against friends and AI. Have fun!"
        )
        controller.canvas.create_text(
            cx, cy + 290, 
            text=info_text,
            fill="#FFFFFF", font=("Arial", 9, "italic"), justify="center", tags="road_marker"
        )

        secondary_controls = "ESC: Menu | V: Camera | P1: Arrows | P2: WASD"
        controller.canvas.create_text(
            cx, cy + 340, 
            text=secondary_controls,
            fill="#FFFFFF", font=("Arial", 8), tags="road_marker"
        )

class RacingMode(BaseMode):
    def __init__(self, canvas, submode="default", players=1):
        super().__init__(canvas)
        self.submode, self.players_count = submode, players
        self.cars_config = "one_player.json" if players == 1 else "two_players.json"
        self.is_test_drive = False

    def enter(self, controller, from_state):
        controller.hud.reset()
        self.race_manager.reset()
        self._loading_next = False
        if from_state == GameState.CREATING:
            self.is_test_drive = True
        else:
            self.is_test_drive = False
            path = CUSTOM_CIRCUITS_PATH if self.submode == "custom" else CAMPAING_CIRCUITS_PATH
            self.circuit_files = [f for f in os.listdir(path) if f.endswith('.json')]
            self.sort_circuits()
            self._load_level_data()
        
        self._setup_cars()
        self.start_time = time.time()
        if self.player_car:
            self.camera_x, self.camera_y = self.player_car.pos

    def _load_level_data(self):
        path = (CUSTOM_CIRCUITS_PATH if self.submode == "custom" else CAMPAING_CIRCUITS_PATH) / self.circuit_files[self.current_idx]
        if not self.is_test_drive:
            with open(path, "r") as f: data = json.load(f)
            self.circuit.destroy(); self.circuit.load_data(data, self.circuit_files[self.current_idx][:-5]); self.race_manager.load_circuit(self.circuit)
            return
        self.circuit.destroy(); self.circuit.load_data(data, self.circuit_files[self.current_idx][:-5]); self.race_manager.load_circuit(self.circuit)

    def _setup_cars(self):
        for c in self.cars: c.destroy()
        self.cars = []
        with open(DATA_PATH / "cars" / self.cars_config, 'r') as f:
            for d in json.load(f)["cars"]:
                car = Car(self.canvas, data=d, initial_angle=self.circuit.initial_angle)
                if len(self.circuit.global_checkpoints) > 0: car.pos = self.circuit.global_checkpoints[0].copy()
                self.cars.append(car)
        self.player_car = self.cars[0] if self.cars else None

    def update(self, controller, keys):
        #print(self.race_manager.checkpoints)
        status = self.race_manager.update(self.cars)
        elapsed = time.time() - self.start_time
        
        if status == 3 and not self._loading_next:
            self._loading_next = True
            controller.canvas.after(3000, lambda: self._next_level(controller))

        for car in self.cars:
            if car.is_player:
                car.handle_input(keys)
                controller.hud.update(self.race_manager, car, elapsed_ms=elapsed)
            car.step(on_road=self.circuit.is_inside(car.pos))

        if "v" in keys or "V" in keys: self.absolute_camera = not self.absolute_camera; keys.discard("v"); keys.discard("V")
        if "Escape" in keys: controller.set_state(GameState.MENU); keys.discard("Escape")
        self._manage_camera(controller)

    def _next_level(self, controller):
        self._loading_next = False
        self.race_manager.reset()
        if self.is_test_drive: controller.set_state(GameState.MENU); return
        self.current_idx = (self.current_idx + 1) % len(self.circuit_files)
        controller.hud.reset(); self._load_level_data(); self._setup_cars()
        self.start_time = time.time()
        if self.player_car: self.camera_x, self.camera_y = self.player_car.pos

    def render(self, controller):
        self.circuit.show(controller.wv); [c.show(controller.wv) for c in self.cars]; controller.hud.refresh()

    def _manage_camera(self, controller):
        if not self.cars: return
        if self.absolute_camera:
            c, w, h = self.circuit.corners(); controller.wv.center(c[0], c[1], w, h)
        elif self.players_count == 1:
            self._apply_smooth_camera(controller, self.player_car)
        else:
            controller.wv.centre_around_points(self.cars[0].pos, self.cars[1].pos)

class CreatingMode:
    def __init__(self, canvas):
        self.canvas, self.road_maker = canvas, RoadMaker(canvas)
        self.degree, self.is_periodic = 1, False

    def enter(self, controller, from_state):
        controller.hud.reset()
        self.road_maker.cleanup()
        controller.wv.center(GameConfig.WORLD_MAX_X//2, GameConfig.WORLD_MAX_Y//2, GameConfig.WORLD_MAX_X, GameConfig.WORLD_MAX_Y)

    def handle_click(self, controller, event):
        w_pos = controller.wv.viewToWorldXY(event.x, event.y)
        self.road_maker.on_click(w_pos.x, w_pos.y, self.degree)

    def update(self, controller, keys):
        for k in list(keys):
            if k.isdigit():
                self.degree = self.road_maker.manager.set_degree(int(k))
                self.road_maker.renderer.update_visuals(self.road_maker.manager.get_road_data()); keys.discard(k)
        if "p" in keys or "P" in keys:
            self.is_periodic = self.road_maker.manager.toggle_periodic()
            self.road_maker.renderer.update_visuals(self.road_maker.manager.get_road_data()); keys.discard("p"); keys.discard("P")
        
        if "Return" in keys:
            data = self.road_maker.get_final_data()
            if data and len(data.get("points", [])) >= 2:
                rm = controller.modes[GameState.RACING]
                rm.clear_entities()
                new_road = SplineRoad(self.canvas, data)
                rm.circuit.roads, rm.circuit.global_checkpoints = [new_road], list(new_road.checkpoints)
                rm.race_manager.load_circuit(rm.circuit)
                self.road_maker.cleanup()
                controller.set_state(GameState.RACING)
            keys.discard("Return")
        if "S" in keys or "s" in keys:
            name = input("Enter a name for your custom circuit: ")
            if not name.strip():
                name = f"custom_circuit_{int(time.time())}.json"
            else:
                name = f"{name}.json"
            filepath = TARGET_DIR / name
            TARGET_DIR.mkdir(parents=True, exist_ok=True)
            self.road_maker.save_to_file(filepath)
            print(f"Custom circuit saved to {filepath}")
            keys.discard("S"); keys.discard("s")
        if "Escape" in keys: controller.set_state(GameState.MENU); keys.discard("Escape")

    def render(self, controller):
        self.road_maker.render(controller.wv)
        for p in self.road_maker.manager.checkpoints:
            v = controller.wv.worldToViewXY(p[0], p[1])
            controller.canvas.create_oval(v.x-8, v.y-8, v.x+8, v.y+8, fill="#FF6B6B", tags="road_marker")
        cx = GameConfig.WINDOW_WIDTH // 2
        controller.canvas.create_rectangle(0, 0, GameConfig.WINDOW_WIDTH, 50, fill="#000000", stipple="gray50", tags="road_marker")
        controller.canvas.create_text(cx, 18, text="Click: Points | 1-9: Degree | P: Periodic | S: Save | Enter: Test drive", fill="white", font=("Arial", 10, "bold"), tags="road_marker")
        controller.canvas.create_text(cx, 38, text=f"Degree: {self.degree} | Periodic: {self.is_periodic}", fill="#00FF88", font=("Arial", 10), tags="road_marker")

    def clear_entities(self): self.road_maker.cleanup()

class TrainingMode(BaseMode):
    def enter(self, controller, from_state):
        self.race_manager.reset()
        controller.hud.reset()
        if not self.circuit_files:
            self.circuit_files = [f for f in os.listdir(CAMPAING_CIRCUITS_PATH) if f.endswith('.json')]
            self.sort_circuits()
        self._loading_next = False; self._load_everything()
        self.start_time = time.time()
        if self.cars: self.camera_x, self.camera_y = self.cars[0].pos

    def _load_everything(self):
        path = CAMPAING_CIRCUITS_PATH / self.circuit_files[self.current_idx]
        with open(path, "r") as f: data = json.load(f)
        self.circuit.destroy(); self.circuit.load_data(data, self.circuit_files[self.current_idx][:-5]); self.race_manager.load_circuit(self.circuit)
        if self.cars: self.cars[0].destroy()
        with open(TRAINING_DATA_PATH / "cars_for_training/default_ai.json", 'r') as f:
            d = json.load(f); car_data = d["cars"][0] if "cars" in d else d
            car = Car(self.canvas, data=car_data, initial_angle=self.circuit.initial_angle)
            if len(self.circuit.global_checkpoints) > 0: car.pos = self.circuit.global_checkpoints[0].copy()
            self.cars = [car]
        self.ai_controller = AIController(AI_BOT, self.cars[0])

    def update(self, controller, keys):
        if self.cars and self.ai_controller:
            self.ai_controller.apply_action(self.circuit, self.race_manager)
            status = self.race_manager.update(self.cars)
            elapsed = time.time() - self.start_time
            controller.hud.update(self.race_manager, self.cars[0], elapsed_ms=elapsed)
            self.cars[0].step(on_road=self.circuit.is_inside(self.cars[0].pos))
            if status == 3 and not self._loading_next:
                self._loading_next = True
                controller.canvas.after(3000, lambda: self._next_level(controller))
        if "Escape" in keys: controller.set_state(GameState.MENU); keys.discard("Escape")
        self._apply_smooth_camera(controller, self.cars[0] if self.cars else None)

    def _next_level(self, controller):
        self.race_manager.reset()
        self._loading_next = False
        self.current_idx = (self.current_idx + 1) % len(self.circuit_files)
        controller.hud.reset(); self._load_everything()
        self.start_time = time.time()
        if self.cars: self.camera_x, self.camera_y = self.cars[0].pos

    def render(self, controller):
        self.circuit.show(controller.wv); self.cars[0].show(controller.wv); controller.hud.refresh()

class PlayerVsAiMode(BaseMode):
    def enter(self, controller, from_state):
        self.race_manager.reset()
        controller.hud.reset()
        if not self.circuit_files:
            self.circuit_files = [f for f in os.listdir(CAMPAING_CIRCUITS_PATH) if f.endswith('.json')]
            self.sort_circuits()
        self._loading_next = False; self._load_everything()
        self.start_time = time.time()
        if self.cars: self.camera_x, self.camera_y = self.cars[0].pos

    def _load_everything(self):
        path = CAMPAING_CIRCUITS_PATH / self.circuit_files[self.current_idx]
        with open(path, "r") as f: data = json.load(f)
        self.circuit.destroy(); self.circuit.load_data(data, self.circuit_files[self.current_idx][:-5]); self.race_manager.load_circuit(self.circuit)
        for c in self.cars: c.destroy()
        with open(DATA_PATH / "cars/one_player.json", 'r') as f: p_data = json.load(f)["cars"][0]
        with open(TRAINING_DATA_PATH / "cars_for_training/default_ai.json", 'r') as f: 
            a_d = json.load(f); a_data = a_d["cars"][0] if "cars" in a_d else a_d
        self.cars = [Car(self.canvas, p_data, initial_angle=self.circuit.initial_angle), Car(self.canvas, a_data, initial_angle=self.circuit.initial_angle)]
        self.ai_controller = AIController(AI_BOT, self.cars[1])
        for c in self.cars: 
            if len(self.circuit.global_checkpoints) > 0: c.pos = self.circuit.global_checkpoints[0].copy()

    def update(self, controller, keys):
        if len(self.cars) < 2: return
        self.cars[0].handle_input(keys); self.ai_controller.apply_action(self.circuit, self.race_manager)
        status = self.race_manager.update(self.cars)
        elapsed = time.time() - self.start_time
        for c in self.cars:
            if c.is_player or True: controller.hud.update(self.race_manager, c, elapsed_ms=elapsed)
            c.step(on_road=self.circuit.is_inside(c.pos))
        if status == 3 and not self._loading_next:
            self._loading_next = True
            controller.canvas.after(3000, lambda: self._next_level(controller))
        if "Escape" in keys: controller.set_state(GameState.MENU); keys.discard("Escape"); return
        controller.wv.centre_around_points(self.cars[0].pos, self.cars[1].pos)

    def _next_level(self, controller):
        self.race_manager.reset()
        self._loading_next = False
        self.current_idx = (self.current_idx + 1) % len(self.circuit_files)
        controller.hud.reset(); self._load_everything()
        self.start_time = time.time()

    def render(self, controller):
        self.circuit.show(controller.wv); [c.show(controller.wv) for c in self.cars]; controller.hud.refresh()

    def _manage_camera(self, controller):
        if not self.cars: return
        if self.absolute_camera:
            c, w, h = self.circuit.corners(); controller.wv.center(c[0], c[1], w, h)
        elif self.players_count == 1:
            self._apply_smooth_camera(controller, self.player_car)
        else:
            controller.wv.centre_around_points(self.cars[0].pos, self.cars[1].pos)

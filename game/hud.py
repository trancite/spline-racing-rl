import math
from pathlib import Path
import tkinter as tk
import tkinter.font as tkfont
from core.config import Colors, GameConfig
import json
import os
DATA_PATH = Path(__file__).parent.parent / "data"
RECORD_PATH = DATA_PATH / "records" / "leaderboard.json"
CAMPAING_CIRCUITS_PATH = DATA_PATH / "campaing_circuits"
CUSTOM_CIRCUITS_PATH = DATA_PATH / "custom_circuits"

class Speedometer:
    def __init__(self, canvas, x: int, y: int, radius: int = 60):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.font_main = tkfont.Font(family="Liberation Sans", size=24, weight="bold")
        self.font_sub = tkfont.Font(family="Liberation Sans", size=10, weight="bold")
        self.bg_arc = canvas.create_arc(
            x - radius, y - radius, x + radius, y + radius,
            start=225, extent=-270,
            style='arc', outline=Colors.UI_SECONDARY, width=8
        )
        
        self.speed_arc = canvas.create_arc(
            x - radius, y - radius, x + radius, y + radius,
            start=225, extent=0,
            style='arc', outline=Colors.UI_SPEEDOMETER_FILL, width=10
        )
        
        self.glow_arc = canvas.create_arc(
            x - radius - 2, y - radius - 2, x + radius + 2, y + radius + 2,
            start=225, extent=0,
            style='arc', outline=Colors.UI_PRIMARY, width=2, stipple='gray50'
        )
        
        self.speed_text = canvas.create_text(
            x, y - 5,
            text="0", font=self.font_main,
            fill=Colors.UI_TEXT
        )
        
        self.unit_text = canvas.create_text(
            x, y + 20,
            text="KM/H", font=self.font_sub,
            fill=Colors.UI_ACCENT
        )

    def update(self, current_speed: float, max_speed: float):
        speed_kmh = abs(current_speed) * 3.6
        speed_ratio = current_speed / max_speed if max_speed > 0 else 0
        extent = -270 * min(1.0, speed_ratio)
        
        self.canvas.itemconfig(self.speed_arc, extent=extent)
        self.canvas.itemconfig(self.glow_arc, extent=extent)

        display_speed = int(speed_kmh)
        self.canvas.itemconfig(self.speed_text, text=str(display_speed))
            
        if speed_ratio > 0.8:
            self.canvas.itemconfig(self.speed_arc, outline="#ff0040")
            self.canvas.itemconfig(self.speed_text, fill="#ff0040")
        elif speed_ratio > 0.6:
            self.canvas.itemconfig(self.speed_arc, outline="#ff6600")
            self.canvas.itemconfig(self.speed_text, fill=Colors.UI_TEXT)
        else:
            self.canvas.itemconfig(self.speed_arc, outline=Colors.UI_SPEEDOMETER_FILL)
            self.canvas.itemconfig(self.speed_text, fill=Colors.UI_TEXT)

    def show(self):
        for item in [self.bg_arc, self.speed_arc, self.glow_arc,
                     self.speed_text, self.unit_text]:
            self.canvas.itemconfig(item, state='normal')
            self.canvas.tag_raise(item)
            
    def hide(self):
        for item in [self.bg_arc, self.speed_arc, self.glow_arc,
                     self.speed_text, self.unit_text]:
            self.canvas.itemconfig(item, state='hidden')


class Leaderboard:    
    def __init__(self, canvas, x: int, y: int):
        self.canvas = canvas
        self.x = x
        self.y = y
        
        self.bg_rect = canvas.create_rectangle(
            x - 10, y - 10, x + 200, y + 90,
            fill="#000000", outline=Colors.UI_SECONDARY,
            stipple='gray50', width=1
        )
        
        self.title = canvas.create_text(
            x, y,
            text="TOP RANKING", font=("Liberation Sans", 10, "bold"),
            fill=Colors.UI_ACCENT, anchor="nw"
        )

        self.rows = []
        for i in range(3):
            row_id = canvas.create_text(
                x, y + 25 + (i * 20),
                text="", font=("Liberation Mono", 10, "bold"),
                fill=Colors.UI_TEXT, anchor="nw"
            )
            self.rows.append(row_id)

    def update(self, race_manager):
        sorted_cars = sorted(
            race_manager.record.items(),
            key=lambda item: (item[1]['laps'], item[1]['next_idx']),
            reverse=True
        )
        
        for i in range(3):
            if i < len(sorted_cars):
                car_id, data = sorted_cars[i]
                lap = data['laps']
                chk = data['next_idx']
                
                text = f"{i+1}. {car_id[:8]:<8} L:{lap} C:{chk:02d}"
                self.canvas.itemconfig(self.rows[i], text=text)
                
                color = Colors.UI_ACCENT if i == 0 else Colors.UI_TEXT
                self.canvas.itemconfig(self.rows[i], fill=color)
            else:
                self.canvas.itemconfig(self.rows[i], text="")

    def show(self):
        items = [self.bg_rect, self.title] + self.rows
        for item in items:
            self.canvas.itemconfig(item, state='normal')
            self.canvas.tag_raise(item)

    def hide(self):
        items = [self.bg_rect, self.title] + self.rows
        for item in items:
            self.canvas.itemconfig(item, state='hidden')


class StatusMessage:
    def __init__(self, canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height

        self.bg_id = self.canvas.create_rectangle(
            0, 0, 0, 0,
            fill="#000000",
            outline=Colors.UI_ACCENT,
            stipple='gray50',
            state='hidden',
            width=2
        )
        
        self.text_id = canvas.create_text(
            width // 2, height // 2,
            text="",
            font=("Liberation Sans", 20, "bold"),
            fill=Colors.UI_ACCENT,
            state='hidden',
            justify="center"
        )
        
    def show_message(self, text: str, color: str = None, duration: int = 3000):
        if color:
            self.canvas.itemconfig(self.text_id, fill=color)
            self.canvas.itemconfig(self.bg_id, outline=color)

        self.canvas.itemconfig(self.text_id, text=text, state='normal')
        
        self.canvas.update_idletasks()

        bbox = self.canvas.bbox(self.text_id)
        if bbox:
            x1, y1, x2, y2 = bbox
            self.canvas.coords(self.bg_id, x1-30, y1-15, x2+30, y2+15)
        
        self.canvas.itemconfig(self.bg_id, state='normal')
        self.canvas.tag_raise(self.bg_id)
        self.canvas.tag_raise(self.text_id)
        
        self.canvas.after(duration, self._hide)

    def _hide(self):
        try:
            self.canvas.itemconfig(self.text_id, state='hidden')
            self.canvas.itemconfig(self.bg_id, state='hidden')
        except:
            pass


class LapRecord:
    def __init__(self, canvas, x: int, y: int):
        self.canvas = canvas
        self.x = x
        self.y = y
        
        self.bg_rect = canvas.create_rectangle(
            x - 10, y - 10, x + 180, y + 70,
            fill="#000000", outline=Colors.UI_PRIMARY,
            stipple='gray50', width=1
        )

        self.lap_shadow = canvas.create_text(
            x + 42, y - 3,
            text="1", font=("Liberation Sans", 26, "bold"),
            fill=Colors.UI_PRIMARY, anchor="nw"
        )
        
        self.label_lap = canvas.create_text(
            x, y,
            text="LAP", font=("Liberation Sans", 12, "bold"),
            fill=Colors.UI_ACCENT, anchor="nw"
        )
        
        self.lap_text = canvas.create_text(
            x + 40, y - 5,
            text="1", font=("Liberation Sans", 26, "bold"),
            fill=Colors.UI_TEXT, anchor="nw"
        )
        
        self.checkpoint_text = canvas.create_text(
            x, y + 38,
            text="CHECKPOINT: 0 / 0", font=("Liberation Mono", 11, "bold"),
            fill=Colors.UI_SECONDARY, anchor="nw"
        )

        self.line = canvas.create_line(
            x, y + 60, x + 170, y + 60,
            fill=Colors.UI_PRIMARY, width=3
        )
        self.line_glow = canvas.create_line(
            x, y + 60, x + 170, y + 60,
            fill=Colors.UI_ACCENT, width=1
        )

    def update(self, current_lap: int, current_checkpoint: int, total_checkpoints: int):
        self.canvas.itemconfig(self.lap_text, text=str(current_lap))
        self.canvas.itemconfig(self.lap_shadow, text=str(current_lap))
        
        chk_str = f"CHK » {current_checkpoint:02d} | {total_checkpoints:02d}"
        self.canvas.itemconfig(self.checkpoint_text, text=chk_str)
        
        if current_checkpoint == total_checkpoints:
            self.canvas.itemconfig(self.checkpoint_text, fill=Colors.UI_ACCENT)
            self.canvas.itemconfig(self.bg_rect, outline=Colors.UI_ACCENT)
        else:
            self.canvas.itemconfig(self.checkpoint_text, fill=Colors.UI_SECONDARY)
            self.canvas.itemconfig(self.bg_rect, outline=Colors.UI_PRIMARY)

    def show(self):
        items = [self.bg_rect, self.lap_shadow, self.label_lap,
                 self.lap_text, self.checkpoint_text, self.line, self.line_glow]
        for item in items:
            self.canvas.itemconfig(item, state='normal')
            self.canvas.tag_raise(item)

    def hide(self):
        items = [self.bg_rect, self.lap_shadow, self.label_lap,
                 self.lap_text, self.checkpoint_text, self.line, self.line_glow]
        for item in items:
            self.canvas.itemconfig(item, state='hidden')


class HUD:
    def __init__(self, canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height
        
        self.speedometer = Speedometer(canvas, width - 80, height - 80, radius=55)
        self.lap_record = LapRecord(canvas, 30, 30)
        self.leaderboard = Leaderboard(canvas, width - 220, 30)
        self.status = StatusMessage(canvas, width, height)
        self._lap_complete_shown = False
        
        
        self.title = canvas.create_text(
            width // 2, height - 30,
            text="🏎️ NEON RACING PRO",
            font=("Liberation Sans", 10, "bold"),
            fill=Colors.UI_ACCENT
        )
        
        self.hints = canvas.create_text(
            150, height - 15,
            text="P1: ↑↓←→  |  P2: WASD",
            font=("Liberation Sans", 9),
            fill=Colors.UI_SECONDARY
        )
        self.hide()
        
    def update(self, race_manager, car=None, elapsed_ms: int = 0, lap: int = 0, position: int = 1):
        if car:
            self.speedometer.update(car.physics.speed, car.physics.max_speed)
            progress = race_manager.record.get(car.car_id)
            if progress:
                self.lap_record.update(
                    current_lap=progress['laps'],
                    current_checkpoint=progress['next_idx'],
                    total_checkpoints=len(race_manager.checkpoints)
                )
            self.leaderboard.update(race_manager)
            if race_manager.record[car.car_id]["laps"] == race_manager.required_laps:
                if car.is_player and not self._lap_complete_shown:
                    self._lap_complete_shown = True
                    self.show_lap_complete(elapsed_ms, is_ai=False, id=car.car_id, circuit = race_manager.circuit.name)
                elif car.is_ai and not self._lap_complete_shown:
                    self._lap_complete_shown = True
                    self.show_lap_complete(elapsed_ms, is_ai=True, id=car.car_id, circuit = race_manager.circuit.name)
    def show_countdown(self, number: int):
        if number > 0:
            self.status.show_message(str(number), Colors.UI_PRIMARY)
        else:
            self.status.show_message("GO!", Colors.UI_ACCENT)
            
    def show_lap_complete(self, lap_time_seconds: float, is_ai: bool = False, id = None, circuit = None):            
        self.update_record(RECORD_PATH, circuit, id, lap_time_seconds)
        if not is_ai:
            self.status.show_message(f"{id} COMPLETED A LAP IN {lap_time_seconds:.2f}s ON {circuit}", Colors.UI_ACCENT)
        else:
            self.status.show_message(f"{id} COMPLETED A LAP IN {lap_time_seconds:.2f}s ON {circuit}", Colors.UI_ACCENT)


    def update_record(self, record_path, circuit, car_id, lap_time_seconds):
        record_path.parent.mkdir(parents=True, exist_ok=True)

        if os.path.exists(record_path):
            with open(record_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}

        circuit_data = data.setdefault(circuit, {})

        if car_id not in circuit_data or lap_time_seconds < circuit_data[car_id]:
            circuit_data[car_id] = lap_time_seconds

        with open(record_path, "w") as f:
            json.dump(data, f, indent=4)



    
    def reset(self):
        self._lap_complete_shown = False
    
    def hide(self):
        self.speedometer.hide()
        self.lap_record.hide()
        self.leaderboard.hide()
        self.canvas.itemconfig(self.title, state='hidden')
        self.canvas.itemconfig(self.hints, state='hidden')
        self.status._hide() 
        
    def refresh(self):
        self.speedometer.show()
        self.lap_record.show()
        self.leaderboard.show()
        self.canvas.tag_raise(self.title)
        if self.status.canvas.itemcget(self.status.text_id, 'state') == 'normal':
            self.canvas.tag_raise(self.status.bg_id)
            self.canvas.tag_raise(self.status.text_id)
            
        self.canvas.tag_raise(self.title)
        self.canvas.tag_raise(self.hints)

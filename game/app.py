import tkinter as tk
import time

from worldview.WPoint import WPoint
from worldview.VPoint import VPoint
from worldview.WorldView import WorldView
from game.controller import GameController
from core.config import *



class GameApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(GameConfig.GAME_TITLE)
        self.root.geometry(f"{GameConfig.WINDOW_WIDTH}x{GameConfig.WINDOW_HEIGHT}")
        self.root.resizable(True, True)
        self.root.configure(bg=Colors.GRASS)
        
        self.smoothness_fps_counter = 0.1
        self.last_time = time.time()
        self.fps = PhysicsConfig.TARGET_FPS
        
        self._center_window()
        
        self.canvas = tk.Canvas(
            self.root,
            width=GameConfig.WINDOW_WIDTH,
            height=GameConfig.WINDOW_HEIGHT,
            bg=Colors.GRASS,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        self._draw_background_pattern()
        
        wMin = WPoint(GameConfig.WORLD_MIN_X, GameConfig.WORLD_MIN_Y)
        wMax = WPoint(GameConfig.WORLD_MAX_X, GameConfig.WORLD_MAX_Y)
        vMin = VPoint(0, 0)
        vMax = VPoint(GameConfig.WINDOW_WIDTH, GameConfig.WINDOW_HEIGHT)
        self.wv = WorldView(wMin, wMax, vMin, vMax)
        
        self.controller = GameController(self.canvas, self.wv)
        
        
        self.pressed_keys = set()
        self._setup_bindings()
        
        self.running = True
        self.frame_count = 0
        self.game_loop()

    def _center_window(self):
        self.root.update_idletasks()
        width = GameConfig.WINDOW_WIDTH
        height = GameConfig.WINDOW_HEIGHT
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _draw_background_pattern(self):
        spacing = 50
        for i in range(0, GameConfig.WINDOW_WIDTH + spacing, spacing):
            self.canvas.create_line(
                i, 0, i, GameConfig.WINDOW_HEIGHT,
                fill=Colors.GRASS_PATTERN, width=1, stipple='gray25'
            )

        for i in range(0, GameConfig.WINDOW_HEIGHT + spacing, spacing):
            self.canvas.create_line(
                0, i, GameConfig.WINDOW_WIDTH, i,
                fill=Colors.GRASS_PATTERN, width=1, stipple='gray25'
            )


    def _setup_bindings(self):
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.canvas.bind("<Button-1>", self._on_mouse_click)
        self.canvas.focus_set()

    def _on_mouse_click(self, event):
        self.controller.handle_click(event)

    def _on_key_press(self, event):
        self.pressed_keys.add(event.keysym)

    def _on_key_release(self, event):
        if event.keysym in self.pressed_keys:
            self.pressed_keys.discard(event.keysym)

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def game_loop(self):
        if not self.running:
            return
        
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        if dt > 0:
            instant_fps = 1.0 / dt
            self.fps = (1.0 - self.smoothness_fps_counter) * self.fps + self.smoothness_fps_counter * instant_fps

        if self.frame_count % 60 == 0: 
            print(f"FPS: {self.fps:.1f}")
            pass
            
        self.frame_count += 1
        
        self.controller.update_physics(self.pressed_keys)
        self.controller.render()
        
        self.root.after(GameConfig.FRAME_DELAY_MS, self.game_loop)

    def run(self):
        print("Starting game...")
        print("Controls: Arrow keys or WASD")
        print("-" * 40)
        self.root.mainloop()

if __name__ == "__main__":
    app = GameApp()
    app.run()
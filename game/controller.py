from game.modes import MenuMode, RacingMode, CreatingMode, TrainingMode, PlayerVsAiMode
from game.hud import HUD
from core.config import *
from core.states import GameState

class GameController:    
    def __init__(self, canvas, worldview):
        self.canvas = canvas
        self.wv = worldview
        self.dt = PhysicsConfig.DT
        self.hud = HUD(self.canvas, GameConfig.WINDOW_WIDTH, GameConfig.WINDOW_HEIGHT)
        
        self.modes = {
            GameState.MENU: MenuMode(canvas),
            GameState.RACING: RacingMode(canvas),
            GameState.RACING_MULTIPLAYER: RacingMode(canvas, players=2),
            GameState.RACING_CUSTOM: RacingMode(canvas, submode="custom"),
            GameState.CREATING: CreatingMode(canvas),
            GameState.TRAINING: TrainingMode(canvas),
            GameState.PLAYER_VS_AI: PlayerVsAiMode(canvas),
        }
        self.state = None
        self.current_mode = None
        self.set_state(GameConfig.FIRST_MODE)

    def set_state(self, new_state: GameState):
        if self.state == new_state: return
        if hasattr(self, 'hud'):
            self.hud.hide()
        
        old_state = self.state
        self.state = new_state
        self.current_mode = self.modes.get(new_state)

        if self.current_mode:
            self.current_mode.enter(self, old_state)

    def update_physics(self, keys: set):
        if self.current_mode:
            self.current_mode.update(self, keys)

    def render(self):
        self.canvas.delete("road_marker")
        if self.current_mode:
            self.current_mode.render(self)

    def handle_click(self, event):
        if hasattr(self.current_mode, "handle_click"):
            self.current_mode.handle_click(self, event)


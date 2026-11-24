from dataclasses import dataclass
from typing import Tuple
from core.states import GameState

@dataclass
class Colors:
    GRASS = "#1a472a"
    GRASS_PATTERN = "#205030"
    ROAD_BORDER = "#1a1a2e"
    ROAD_ASPHALT = "#16213e"
    ROAD_CENTER_LINE = "#e94560"
    ROAD_EDGE_GLOW = "#0f3460"
    CHECKPOINT_GLOW = "#00ff88"
    CAR_BODY_PLAYER = "#ff006e"
    CAR_BODY_AI = "#3a86ff"
    CAR_WINDOW = "#00b4d8"
    CAR_HEADLIGHT_ON = "#ffea00"
    CAR_HEADLIGHT_OFF = "#666600"
    CAR_TAILLIGHT_ON = "#ff0000"
    CAR_TAILLIGHT_OFF = "#660000"
    CAR_OUTLINE = "#ffffff"
    SPEED_TRAIL = "#ff006e"
    BOOST_EFFECT = "#00ffff"
    DRIFT_SMOKE = "#cccccc"
    UI_PRIMARY = "#e94560"
    UI_SECONDARY = "#0f3460"
    UI_TEXT = "#ffffff"
    UI_ACCENT = "#00ff88"
    UI_SPEEDOMETER_BG = "#1a1a2e"
    UI_SPEEDOMETER_FILL = "#ff006e"

    NEON_MAGENTA = "#ff00ff"
    NEON_CYAN = "#00ffff"
    NEON_LIME = "#39ff14"
    NEON_YELLOW = "#fff01f"
    NEON_ORANGE = "#ff6700"
    NEON_PURPLE = "#bc13fe"
    NEON_BLUE = "#001fff"
    NEON_RED = "#ff0033"
    NEON_PINK = "#ff69b4"
    NEON_VIOLET = "#8f00ff"
    NEON_TURQUOISE = "#08d9d6"
    NEON_GREEN = "#adff2f"
    
    RACING_RED = "#ff2800"
    RACING_ORANGE = "#ff8700"
    RACING_GREEN = "#004225"
    RACING_BLUE = "#003399"
    RACING_YELLOW = "#fff500"
    RACING_SILVER = "#c0c0c0"
    RACING_CARBON = "#1a1a1a"
    RACING_PURPLE = "#2d1b33"
    RACING_GULF_BLUE = "#8abdff"
    RACING_GULF_ORANGE = "#f7941d"
    RACING_WHITE = "#f5f5f5"
    RACING_GOLD = "#d4af37"
    RACING_BRONZE = "#cd7f32"

    UI_SUCCESS = "#00ff88"
    UI_WARNING = "#ffcc00"
    UI_ERROR = "#ff4444"
    UI_INFO = "#00d1ff"
    UI_DISABLED = "#444444"
    UI_DARK_BG = "#0d1117"
    UI_CARD_BG = "#161b22"
    UI_BORDER = "#30363d"
    UI_SHADOW = "#010409"
    UI_GLOW_PINK = "#ff0055"
    UI_GLOW_BLUE = "#00aaff"

    ENV_DEEP_GRASS = "#0a2e1a"
    ENV_MUD = "#4d3a24"
    ENV_SAND = "#c2b280"
    ENV_WATER = "#0077be"
    ENV_AUTUMN = "#d84a05"
    ENV_NIGHT_SKY = "#0b0d17"
    ENV_SNOW = "#ffffff"
    ENV_FOREST = "#0b6623"
    ENV_ROCK = "#5a5a5a"
    ENV_DIRT = "#3b2f2f"
    ENV_LAVA = "#cf1020"
    ENV_ICE = "#a5f2f3"

    WHITE = "#ffffff"
    OFF_WHITE = "#f8f9fa"
    SILVER = "#c0c0c0"
    GRAY_LIGHT = "#a0a0a0"
    GRAY = "#808080"
    GRAY_DARK = "#404040"
    GRAY_DEEP = "#212529"
    BLACK = "#000000"
    BLACK_SOFT = "#121212"
    BLACK_JET = "#0a0a0a"

    AMETHYST = "#9966cc"
    EMERALD = "#50c878"
    SAPPHIRE = "#0f52ba"
    RUBY = "#e0115f"
    AMBER = "#ffbf00"
    CORAL = "#ff7f50"
    SLATE = "#708090"
    CRIMSON = "#dc143c"
    INDIGO = "#4b0082"
    TEAL = "#008080"
    MINT = "#98ff98"
    COBALT = "#0047ab"
    SUNSET = "#ff4e50"
    MIDNIGHT = "#191970"





@dataclass
class PhysicsConfig:
    TARGET_FPS = 60
    DT = 1.0 / TARGET_FPS
    

    ROAD_FRICTION = 0.95
    OFF_ROAD_FRICTION = 0.2
    
    ROAD_GRIP = 0.95
    OFF_ROAD_GRIP = 0.7

    G = 9.81
    K = 5
    
    # Car physics defaults
    DEFAULT_MAX_SPEED = 200          
    DEFAULT_ACCELERATION = 3        
    DEFAULT_TURN_SPEED = 3.0        
    DEFAULT_GRIP = 1.0               
    
    # Physics modifiers

    # Fraction of acceleration applied when braking
    BRAKING_POWER = 0.5              

    # Penalty to turning ability at high speeds. Maximum reduction is 0.7.
    ROTATION_PENALTY = 0.0           

    # Drift mechanics
    DRIFT_ANGLE_THRESHOLD = 15.0 

    # Minimum speed (m/s) to initiate a turn    
    MIN_SPEED_FOR_TURN = 0.05
    
    @classmethod
    def speed_kmh_to_ms(cls, speed_kmh: float) -> float:
        return speed_kmh / 3.6
    
    @classmethod
    def acceleration_0_100_s_to_ms2(cls, time_needed: float) -> float:
        return 27.78 / time_needed



@dataclass 
class GameConfig:
    FIRST_MODE = GameState.MENU
    CAMERA_FOLLOWING = True
    WINDOW_WIDTH = 900
    WINDOW_HEIGHT = 900
    GAME_TITLE = "Racing Game: Play alone, with a friend or against AI!"
    
    WORLD_MIN_X = 0
    WORLD_MIN_Y = 0
    WORLD_MAX_X = 2000
    WORLD_MAX_Y = 2000
    
    CAMERA_FOLLOW_WIDTH = 100
    CAMERA_FOLLOW_HEIGHT = 100
    CAMERA_SMOOTHING = 100 
    
    TARGET_FPS = PhysicsConfig.TARGET_FPS
    FRAME_DELAY_MS = int(1000/PhysicsConfig.TARGET_FPS)  
    
    CHECKPOINT_RADIUS = 1
    DETECTION_RADIUS_FOR_REMOVING = 8
    DETECTION_RADIUS = 16
    ENABLE_PARTICLES = True
    ENABLE_SPEED_LINES = True
    ENABLE_GLOW_EFFECTS = True
    MAX_PARTICLES = 50
    
    SHOW_SPEEDOMETER = True
    SHOW_MINIMAP = True
    SHOW_LAP_TIMER = True

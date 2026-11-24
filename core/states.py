from enum import Enum


class GameState(Enum):
    MENU = "menu"
    COUNTDOWN = "countdown"
    RACING = "racing"
    RACING_MULTIPLAYER = "racing_multiplayer"
    RACING_CUSTOM = "racing_custom"
    CREATING = "creating"
    TRAINING = "training"
    PLAYER_VS_AI = "player_vs_ai"
    PAUSED = "paused"
    FINISHED = "finished"

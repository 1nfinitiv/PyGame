import pygame
from enum import Enum

# Размеры экрана
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
GRID_SIZE = 64
BORDER_OFFSET = GRID_SIZE * 2

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)

# Состояния игры
class GameState(Enum):
    MENU = 0
    BUILD = 1
    BATTLE = 2
    WIN = 3
    LOSE = 4
    HELP = 5

# Уровни сложности
class Difficulty(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2

# Типы зданий
class BuildingType(Enum):
    TOWN_HALL = 0
    BARRACKS = 1
    GOLD_MINE = 2
    WALL = 3

# Типы юнитов
class UnitType(Enum):
    WARRIOR = 0
    ARCHER = 1
    GIANT = 2
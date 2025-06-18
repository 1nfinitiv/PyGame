import pygame
import random
import math
import sys
from enum import Enum

# Initialize pygame
pygame.init()

pygame.mixer.init()  # Инициализация аудио модуля

# Game constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
GRID_SIZE = 64
BORDER_OFFSET = GRID_SIZE * 2

# Colors
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


def load_texture(path, size=None):
    texture = pygame.image.load(path)
    if size:
        texture = pygame.transform.scale(texture, size)
    return texture


textures = {
    'background': load_texture('texture/grass.png', (SCREEN_WIDTH, SCREEN_HEIGHT)),
    'menu_background': load_texture('texture/menu_bg.jpg', (SCREEN_WIDTH, SCREEN_HEIGHT)),
    'town_hall': load_texture('texture/house1.png', (GRID_SIZE * 2, GRID_SIZE * 2)),
    'barracks': load_texture('texture/barracks.png', (GRID_SIZE * 2, GRID_SIZE * 2)),
    'gold_mine': load_texture('texture/Gold_Mine.png', (GRID_SIZE, GRID_SIZE)),
    'wall': load_texture('texture/Wall.png', (GRID_SIZE, GRID_SIZE)),
    'wall_broken': load_texture('texture/wall_broken.png', (GRID_SIZE, GRID_SIZE)),
    'warrior': load_texture('texture/warrior.png', (30, 30)),
    'archer': load_texture('texture/archer.png', (30, 30)),
    'giant': load_texture('texture/giant.png', (50, 50)),
    'warrior_enemy': load_texture('texture/warrior_enemy.png', (30, 30)),
    'archer_enemy': load_texture('texture/archer_enemy.png', (30, 30)),
    'giant_enemy': load_texture('texture/giant.png', (50, 50))
}

# Загрузка музыки (добавьте это в раздел загрузки ресурсов)
try:
    pygame.mixer.music.load('music/Linkin_Park_-_Somewhere_I_Belong.mp3')  # Укажите путь к вашему музыкальному файлу
    music_loaded = True
except:
    print("Не удалось загрузить музыку")
    music_loaded = False


# Game states
class GameState(Enum):
    MENU = 0
    BUILD = 1
    BATTLE = 2
    WIN = 3
    LOSE = 4
    HELP = 5


class Difficulty(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2


class BuildingType(Enum):
    TOWN_HALL = 0
    BARRACKS = 1
    GOLD_MINE = 2
    WALL = 3


class UnitType(Enum):
    WARRIOR = 0
    ARCHER = 1
    GIANT = 2


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)  # Border

        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click


class Building:
    def __init__(self, x, y, building_type, difficulty=Difficulty.EASY):
        self.x = x
        self.y = y
        self.type = building_type
        self.level = 1
        self.is_broken = False
        self.difficulty = difficulty

        if building_type == BuildingType.TOWN_HALL:
            self.health = 500
            self.max_health = 500
            self.width = 2
            self.height = 2
        elif building_type == BuildingType.BARRACKS:
            self.health = 200  # Теперь у бараков есть здоровье
            self.max_health = 200
            self.width = 2
            self.height = 2
            self.spawn_timer = 0
            self.spawn_interval = 8000
            self.gold_reserve = 0  # Золотой запас для найма войск
            self.hire_cost = 20  # Стоимость найма одного война
        elif building_type == BuildingType.GOLD_MINE:
            self.health = 150  # Здоровье шахты
            self.max_health = 150
            self.width = 1
            self.height = 1
            self.gold_timer = 0
            self.gold_interval = 5000  # Интервал генерации золота (5 секунд)
            self.gold_amount = 25  # Количество золота за интервал
            self.depletion_rate = 5  # На сколько уменьшается здоровье при добыче
        elif building_type == BuildingType.WALL:
            self.health = 300
            self.max_health = 300
            self.width = 1
            self.height = 1
            self.repair_cost = 50

    def update(self, dt, game):
        if self.type == BuildingType.WALL and self.health <= 0:
            self.is_broken = True
        else:
            self.is_broken = False

        if self.type == BuildingType.BARRACKS and game.state == GameState.BATTLE:
            # Проверяем, есть ли враги на поле боя и достаточно ли золота
            enemies_exist = any(not unit.is_defender for unit in game.units)

            if enemies_exist and self.gold_reserve >= self.hire_cost:
                self.spawn_timer += dt
                if self.spawn_timer >= self.spawn_interval:
                    self.spawn_timer = 0
                    self.gold_reserve -= self.hire_cost
                    game.units.append(Unit(self.x + self.width * GRID_SIZE // 2,
                                           self.y + self.height * GRID_SIZE // 2,
                                           UnitType.WARRIOR, True, game.difficulty))

        # Добавляем генерацию золота для шахты
        elif self.type == BuildingType.GOLD_MINE and self.health > 0:
            self.gold_timer += dt
            if self.gold_timer >= self.gold_interval:
                self.gold_timer = 0
                game.gold += self.gold_amount
                self.health -= self.depletion_rate  # Уменьшаем здоровье шахты

                if self.health <= 0:
                    self.health = 0  # Шахта истощена

    def repair(self, game):
        if self.type == BuildingType.WALL and self.health <= 0 and game.gold >= self.repair_cost:
            # Для разрушенной стены - создаем новую на том же месте
            game.buildings.remove(self)
            new_wall = Building(self.x, self.y, BuildingType.WALL, self.difficulty)
            game.buildings.append(new_wall)
            game.gold -= self.repair_cost
            return True
        return False

    def refill_gold(self, game, amount):
        if game.gold >= amount:
            game.gold -= amount
            self.gold_reserve += amount
            return True
        return False

    def draw(self, screen):
        if self.type == BuildingType.TOWN_HALL:
            screen.blit(textures['town_hall'], (self.x, self.y))
        elif self.type == BuildingType.BARRACKS:
            screen.blit(textures['barracks'], (self.x, self.y))
        elif self.type == BuildingType.GOLD_MINE:
            screen.blit(textures['gold_mine'], (self.x, self.y))
        elif self.type == BuildingType.WALL:
            if self.health <= 0:
                screen.blit(textures['wall_broken'], (self.x, self.y))
            else:
                screen.blit(textures['wall'], (self.x, self.y))

        # Health bar для всех зданий
        if self.health != float('inf'):
            health_ratio = self.health / self.max_health
            pygame.draw.rect(screen, RED,
                             (self.x, self.y - 10, self.width * GRID_SIZE, 5))
            pygame.draw.rect(screen, GREEN,
                             (self.x, self.y - 10, int(self.width * GRID_SIZE * health_ratio), 5))

        # Отображение золотого запаса для бараков
        if self.type == BuildingType.BARRACKS:
            font = pygame.font.SysFont(None, 20)
            text = font.render(f"Gold: {self.gold_reserve}", True, YELLOW)
            screen.blit(text, (self.x + 5, self.y + 5))

        # Отображение состояния шахты
        if self.type == BuildingType.GOLD_MINE:
            font = pygame.font.SysFont(None, 20)
            status = "Depleted" if self.health <= 0 else "Active"
            text = font.render(status, True, YELLOW if self.health > 0 else RED)
            screen.blit(text, (self.x + 5, self.y + 5))


class Unit:
    def __init__(self, x, y, unit_type, is_defender=False, difficulty=Difficulty.EASY):
        self.x = x
        self.y = y
        self.type = unit_type
        self.is_defender = is_defender
        self.difficulty = difficulty

        # Замедленная скорость для всех юнитов
        base_speed = {
            UnitType.WARRIOR: 0.8,
            UnitType.ARCHER: 0.6,
            UnitType.GIANT: 0.4
        }

        self.speed = base_speed[unit_type]

        # Характеристики юнитов
        self.health = {
            UnitType.WARRIOR: 100,
            UnitType.ARCHER: 60,
            UnitType.GIANT: 500
        }[unit_type]

        self.max_health = self.health
        self.attack_damage = {
            UnitType.WARRIOR: 10,
            UnitType.ARCHER: 8,
            UnitType.GIANT: 25
        }[unit_type]

        self.attack_range = 50 if unit_type != UnitType.ARCHER else 120
        self.attack_cooldown = 1500
        self.last_attack = 0
        self.target = None
        self.target_wall = None
        self.radius = {
            UnitType.WARRIOR: 15,
            UnitType.ARCHER: 12,
            UnitType.GIANT: 25
        }[unit_type]

    def find_town_hall(self, game):
        for building in game.buildings:
            if building.type == BuildingType.TOWN_HALL:
                return building
        return None

    def find_closest_wall(self, game, town_hall):
        closest_wall = None
        min_dist = float('inf')

        town_hall_center_x = town_hall.x + town_hall.width * GRID_SIZE // 2
        town_hall_center_y = town_hall.y + town_hall.height * GRID_SIZE // 2

        for building in game.buildings:
            if building.type == BuildingType.WALL and building.health > 0:
                wall_center_x = building.x + building.width * GRID_SIZE // 2
                wall_center_y = building.y + building.height * GRID_SIZE // 2

                # Проверяем, лежит ли стена на линии между юнитом и Town Hall
                line_distance = self._distance_to_line(
                    self.x, self.y,
                    town_hall_center_x, town_hall_center_y,
                    wall_center_x, wall_center_y
                )

                # Если стена близко к линии, считаем её целью
                if line_distance < GRID_SIZE // 2:
                    dist_to_wall = math.sqrt((self.x - wall_center_x) ** 2 + (self.y - wall_center_y) ** 2)
                    if dist_to_wall < min_dist:
                        min_dist = dist_to_wall
                        closest_wall = building

        return closest_wall

    def _distance_to_line(self, x1, y1, x2, y2, px, py):
        """Вычисляет расстояние от точки (px, py) до линии (x1,y1)-(x2,y2)"""
        line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if line_length == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        return abs((py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)) / line_length

    def update(self, dt, game):
        if self.is_defender:
            # Логика защитников
            closest_enemy = None
            min_dist = float('inf')
            for enemy in game.units:
                if not enemy.is_defender:
                    dist = math.sqrt((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_enemy = enemy
            if closest_enemy:
                if min_dist <= self.attack_range:
                    self.last_attack += dt
                    if self.last_attack >= self.attack_cooldown:
                        self.last_attack = 0
                        closest_enemy.health -= self.attack_damage
                        if closest_enemy.health <= 0:
                            game.units.remove(closest_enemy)
                else:
                    angle = math.atan2(closest_enemy.y - self.y, closest_enemy.x - self.x)
                    self.x += self.speed * math.cos(angle)
                    self.y += self.speed * math.sin(angle)
        else:
            # ЛОГИКА ДЛЯ ВРАГОВ
            closest_defender = None
            min_defender_dist = float('inf')

            # Ищем ближайшего защитника в радиусе обнаружения
            for defender in game.units:
                if defender.is_defender:
                    dist = math.sqrt((self.x - defender.x) ** 2 + (self.y - defender.y) ** 2)
                    if dist < min_defender_dist:
                        min_defender_dist = dist
                        closest_defender = defender

            # Если нашли защитника в радиусе атаки
            if closest_defender and min_defender_dist <= self.attack_range:
                self.target = closest_defender
                self.last_attack += dt
                if self.last_attack >= self.attack_cooldown:
                    self.last_attack = 0
                    closest_defender.health -= self.attack_damage
                    if closest_defender.health <= 0:
                        game.units.remove(closest_defender)
                return

            # Если защитник в увеличенном радиусе, двигаемся к нему
            if closest_defender and min_defender_dist <= self.attack_range * 2:
                angle = math.atan2(closest_defender.y - self.y, closest_defender.x - self.x)
                self.x += self.speed * math.cos(angle)
                self.y += self.speed * math.sin(angle)
                return

            # Если нет защитников поблизости, продолжаем стандартное поведение
            town_hall = self.find_town_hall(game)
            if not town_hall:
                return

            town_hall_center_x = town_hall.x + town_hall.width * GRID_SIZE // 2
            town_hall_center_y = town_hall.y + town_hall.height * GRID_SIZE // 2

            # Если мы уже сломали стену и идем через проход
            if hasattr(self, 'broken_wall') and self.broken_wall:
                # Проверяем дошли ли до центра сломанной стены
                wall_center_x = self.broken_wall.x + self.broken_wall.width * GRID_SIZE // 2
                wall_center_y = self.broken_wall.y + self.broken_wall.height * GRID_SIZE // 2
                dist_to_wall = math.sqrt((self.x - wall_center_x) ** 2 + (self.y - wall_center_y) ** 2)

                if dist_to_wall < 10:  # Достаточно близко к центру прохода
                    self.broken_wall = None  # Проход пройден
                else:
                    # Продолжаем идти к центру сломанной стены
                    angle = math.atan2(wall_center_y - self.y, wall_center_x - self.x)
                    self.x += self.speed * math.cos(angle)
                    self.y += self.speed * math.sin(angle)
                    return

            # Если атакуем стену
            if hasattr(self, 'target_wall') and self.target_wall:
                if self.target_wall.health > 0:
                    wall_center_x = self.target_wall.x + self.target_wall.width * GRID_SIZE // 2
                    wall_center_y = self.target_wall.y + self.target_wall.height * GRID_SIZE // 2
                    dist_to_wall = math.sqrt((self.x - wall_center_x) ** 2 + (self.y - wall_center_y) ** 2)

                    if dist_to_wall <= self.attack_range:
                        # Атакуем стену
                        self.last_attack += dt
                        if self.last_attack >= self.attack_cooldown:
                            self.last_attack = 0
                            self.target_wall.health -= self.attack_damage

                            # Если стену сломали
                            if self.target_wall.health <= 0:
                                self.broken_wall = self.target_wall  # Запоминаем сломанную стену
                                self.target_wall = None
                    else:
                        # Двигаемся к стене
                        angle = math.atan2(wall_center_y - self.y, wall_center_x - self.x)
                        self.x += self.speed * math.cos(angle)
                        self.y += self.speed * math.sin(angle)
                    return

            # Проверяем прямой путь к Town Hall
            if not self.is_path_blocked(game, town_hall):
                dist_to_town_hall = math.sqrt((self.x - town_hall_center_x) ** 2 + (self.y - town_hall_center_y) ** 2)

                if dist_to_town_hall <= self.attack_range:
                    # Атакуем Town Hall
                    self.last_attack += dt
                    if self.last_attack >= self.attack_cooldown:
                        self.last_attack = 0
                        town_hall.health -= self.attack_damage
                        if town_hall.health <= 0:
                            game.state = GameState.LOSE
                else:
                    angle = math.atan2(town_hall_center_y - self.y, town_hall_center_x - self.x)
                    self.x += self.speed * math.cos(angle)
                    self.y += self.speed * math.sin(angle)
                return

            # Ищем лучший путь: через сломанную стену или ломать новую
            closest_wall = None
            closest_broken_wall = None
            min_wall_dist = float('inf')
            min_broken_wall_dist = float('inf')

            for building in game.buildings:
                if building.type == BuildingType.WALL:
                    wall_center_x = building.x + building.width * GRID_SIZE // 2
                    wall_center_y = building.y + building.height * GRID_SIZE // 2
                    dist = math.sqrt((self.x - wall_center_x) ** 2 + (self.y - wall_center_y) ** 2)

                    if building.health > 0:
                        # Целая стена - проверяем, что она на пути к Town Hall
                        if self.is_wall_on_path(building, town_hall) and dist < min_wall_dist:
                            min_wall_dist = dist
                            closest_wall = building
                    else:
                        # Сломанная стена - проверяем, что через нее есть путь к Town Hall
                        if self.is_good_passage(building, town_hall, game) and dist < min_broken_wall_dist:
                            min_broken_wall_dist = dist
                            closest_broken_wall = building

            # Выбираем стратегию
            if closest_broken_wall and (not closest_wall or min_broken_wall_dist < min_wall_dist * 1.5):
                # Идем к сломанной стене
                self.broken_wall = closest_broken_wall
                target_x = closest_broken_wall.x + closest_broken_wall.width * GRID_SIZE // 2
                target_y = closest_broken_wall.y + closest_broken_wall.height * GRID_SIZE // 2
            elif closest_wall:
                # Атакуем ближайшую стену на пути
                self.target_wall = closest_wall
                target_x = closest_wall.x + closest_wall.width * GRID_SIZE // 2
                target_y = closest_wall.y + closest_wall.height * GRID_SIZE // 2
            else:
                # Если стен нет - идем к Town Hall
                target_x = town_hall_center_x
                target_y = town_hall_center_y

            # Двигаемся к выбранной цели
            angle = math.atan2(target_y - self.y, target_x - self.x)
            self.x += self.speed * math.cos(angle)
            self.y += self.speed * math.sin(angle)

    def is_wall_on_path(self, wall, town_hall):
        """Проверяет, находится ли стена на прямой линии к Town Hall"""
        town_hall_center = (town_hall.x + town_hall.width * GRID_SIZE // 2,
                            town_hall.y + town_hall.height * GRID_SIZE // 2)
        self_center = (self.x, self.y)
        wall_rect = pygame.Rect(wall.x, wall.y, wall.width * GRID_SIZE, wall.height * GRID_SIZE)
        return self.line_intersects_rect(self_center, town_hall_center, wall_rect)

    def is_good_passage(self, broken_wall, town_hall, game):
        """Проверяет, ведет ли сломанная стена к Town Hall без других препятствий"""
        # Проверяем путь от себя к сломанной стене
        if self.is_path_blocked_to_wall(game, broken_wall):
            return False

        # Проверяем путь от сломанной стены к Town Hall
        town_hall_center = (town_hall.x + town_hall.width * GRID_SIZE // 2,
                            town_hall.y + town_hall.height * GRID_SIZE // 2)
        wall_center = (broken_wall.x + broken_wall.width * GRID_SIZE // 2,
                       broken_wall.y + broken_wall.height * GRID_SIZE // 2)

        for building in game.buildings:
            if building.type == BuildingType.WALL and building.health > 0 and building != broken_wall:
                wall_rect = pygame.Rect(building.x, building.y,
                                        building.width * GRID_SIZE, building.height * GRID_SIZE)
                if self.line_intersects_rect(wall_center, town_hall_center, wall_rect):
                    return False
        return True

    def is_path_blocked_to_wall(self, game, target_wall):
        """Проверяет, есть ли стены на пути к целевой стене"""
        wall_center = (target_wall.x + target_wall.width * GRID_SIZE // 2,
                       target_wall.y + target_wall.height * GRID_SIZE // 2)
        self_center = (self.x, self.y)

        for building in game.buildings:
            if building.type == BuildingType.WALL and building.health > 0 and building != target_wall:
                wall_rect = pygame.Rect(building.x, building.y,
                                        building.width * GRID_SIZE, building.height * GRID_SIZE)
                if self.line_intersects_rect(self_center, wall_center, wall_rect):
                    return True
        return False

    def is_path_blocked(self, game, town_hall):
        """Проверяет, есть ли стены на прямой линии к Town Hall"""
        town_hall_center = (town_hall.x + town_hall.width * GRID_SIZE // 2,
                            town_hall.y + town_hall.height * GRID_SIZE // 2)
        self_center = (self.x, self.y)

        for building in game.buildings:
            if building.type == BuildingType.WALL and building.health > 0:
                wall_rect = pygame.Rect(building.x, building.y,
                                        building.width * GRID_SIZE, building.height * GRID_SIZE)
                if self.line_intersects_rect(self_center, town_hall_center, wall_rect):
                    return True
        return False

    def line_intersects_rect(self, p1, p2, rect):
        """Проверяет, пересекает ли линия p1-p2 прямоугольник rect"""

        # Алгоритм Liang-Barsky для проверки пересечения линии и прямоугольника
        def clip(denom, numer, t0, t1):
            if denom == 0:
                return numer <= 0
            t = numer / denom
            if denom > 0:
                if t > t1:
                    return False
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return False
                if t < t1:
                    t1 = t
            return True, t0, t1

        x1, y1 = p1
        x2, y2 = p2
        t0, t1 = 0, 1
        dx = x2 - x1
        dy = y2 - y1

        # Проверяем каждую границу прямоугольника
        if not clip(-dx, x1 - rect.left, t0, t1):
            return False
        if not clip(dx, rect.right - x1, t0, t1):
            return False
        if not clip(-dy, y1 - rect.top, t0, t1):
            return False
        if not clip(dy, rect.bottom - y1, t0, t1):
            return False

        return True

    def draw(self, screen):
        if self.type == UnitType.WARRIOR:
            texture = textures['warrior'] if self.is_defender else textures['warrior_enemy']
        elif self.type == UnitType.ARCHER:
            texture = textures['archer'] if self.is_defender else textures['archer_enemy']
        elif self.type == UnitType.GIANT:
            texture = textures['giant'] if self.is_defender else textures['giant_enemy']

        screen.blit(texture, (int(self.x - texture.get_width() // 2), int(self.y - texture.get_height() // 2)))

        # Если юнит атакует и есть цель, рисуем индикатор атаки
        if self.last_attack < 100 and hasattr(self, 'target') and self.target is not None:
            attack_color = RED if not self.is_defender else YELLOW
            pygame.draw.line(screen, attack_color,
                             (int(self.x), int(self.y)),
                             (int(self.target.x), int(self.target.y)),
                             2)

        # Health bar
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, RED,
                         (int(self.x - self.radius), int(self.y - self.radius - 10),
                          int(2 * self.radius), 5))
        pygame.draw.rect(screen, GREEN,
                         (int(self.x - self.radius), int(self.y - self.radius - 10),
                          int(2 * self.radius * health_ratio), 5))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Clash of Berserk")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.difficulty = Difficulty.EASY
        self.build_time = 3000  # 3 минуты на строительство
        self.build_timer = 0
        self.wave = 0
        self.wave_timer = 0
        self.wave_interval = 3000  # 40 секунд между волнами
        self.gold = 500
        self.selected_building = None
        self.buildings = []
        self.units = []
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        self.selected_wall = None
        self.selected_barracks = None
        self.selected_mine = None

        # Кнопки
        self.help_button = Button(SCREEN_WIDTH - 120, 20, 100, 40, "Помощь", LIGHT_BLUE, BLUE, BLACK)
        self.back_button = Button(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 80, 100, 40, "Назад", LIGHT_BLUE, BLUE, BLACK)
        self.easy_button = Button(300, 200, 200, 50, "Легко", GREEN, DARK_GREEN, BLACK)
        self.medium_button = Button(300, 300, 200, 50, "Средне", YELLOW, (200, 200, 0), BLACK)
        self.hard_button = Button(300, 400, 200, 50, "Сложно", RED, (200, 0, 0), BLACK)

        self.init_village()

    def init_village(self):
        self.buildings = []
        self.units = []

        town_hall = Building(SCREEN_WIDTH // 2 - GRID_SIZE, SCREEN_HEIGHT // 2 - GRID_SIZE, BuildingType.TOWN_HALL,
                             self.difficulty)
        self.buildings.append(town_hall)

        self.create_perimeter_walls()

    def create_perimeter_walls(self):
        for x in range(BORDER_OFFSET, SCREEN_WIDTH - BORDER_OFFSET, GRID_SIZE):
            self.buildings.append(Building(x, BORDER_OFFSET, BuildingType.WALL, self.difficulty))
            self.buildings.append(
                Building(x, SCREEN_HEIGHT - BORDER_OFFSET - GRID_SIZE, BuildingType.WALL, self.difficulty))

        for y in range(BORDER_OFFSET + GRID_SIZE, SCREEN_HEIGHT - BORDER_OFFSET - GRID_SIZE, GRID_SIZE):
            self.buildings.append(Building(BORDER_OFFSET, y, BuildingType.WALL, self.difficulty))
            self.buildings.append(
                Building(SCREEN_WIDTH - BORDER_OFFSET - GRID_SIZE, y, BuildingType.WALL, self.difficulty))

    def spawn_wave(self):
        self.units = [unit for unit in self.units if unit.is_defender]

        wave_multiplier = 1 + self.wave * 0.5
        difficulty_multiplier = 1 + self.difficulty.value * 0.3

        if self.wave == 0:
            count = int(6 * wave_multiplier * difficulty_multiplier)
            for _ in range(count):
                self.spawn_enemy(UnitType.WARRIOR)

        elif self.wave == 1:
            count = int(9 * wave_multiplier * difficulty_multiplier)
            for _ in range(count):
                unit_type = random.choice([UnitType.WARRIOR, UnitType.ARCHER])
                self.spawn_enemy(unit_type)

        elif self.wave == 2:
            count = int(7 * wave_multiplier * difficulty_multiplier)
            for _ in range(count):
                self.spawn_enemy(UnitType.WARRIOR)

            boss = self.spawn_enemy(UnitType.GIANT)
            boss.health = int(800 * difficulty_multiplier)
            boss.max_health = boss.health
            boss.attack_damage = int(40 * difficulty_multiplier)

    def spawn_enemy(self, unit_type):
        spawn_options = [
            lambda: (random.randint(0, BORDER_OFFSET), random.randint(0, SCREEN_HEIGHT)),
            lambda: (random.randint(SCREEN_WIDTH - BORDER_OFFSET, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
            lambda: (random.randint(0, SCREEN_WIDTH), random.randint(0, BORDER_OFFSET)),
            lambda: (random.randint(0, SCREEN_WIDTH), random.randint(SCREEN_HEIGHT - BORDER_OFFSET, SCREEN_HEIGHT))
        ]

        spawn_func = random.choice(spawn_options)
        x, y = spawn_func()
        enemy = Unit(x, y, unit_type, False, self.difficulty)
        self.units.append(enemy)
        return enemy

    def draw_help_screen(self):
        # Полупрозрачный фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Заголовок
        title = self.font.render("Управление и помощь", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # Управление
        controls = [
            "Управление в меню:",
            "- ЛКМ: Выбрать уровень сложности",
            "",
            "Управление в игре:",
            "- 1: Выбрать казармы (100 золота)",
            "- 2: Выбрать шахту (75 золота)",
            "- 3: Выбрать стену (50 золота)",
            "- ЛКМ: Построить/Выбрать здание",
            "- ПКМ: Отменить выбор здания",
            "- F: Пополнить запас выбранного барака (50 золота)",
            "- R: Восстановить шахту (75 золота)",
            "- M: Включить/выключить музыку",
            "- +: Увеличить громкость",
            "- -: Уменьшить громкость",
            "",
            "Цель игры:",
            "- Защитите Town Hall от 3 волн врагов",
            "- Используйте стены для защиты",
            "- Шахты дают золото для строительства",
            "- Казармы автоматически нанимают войска"
        ]

        for i, line in enumerate(controls):
            if line:  # Пропускаем пустые строки
                text = self.small_font.render(line, True, WHITE)
                self.screen.blit(text, (100, 120 + i * 30))

        # Кнопка назад
        self.back_button.draw(self.screen, self.font)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        right_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левый клик
                    mouse_click = True
                elif event.button == 3:  # Правый клик
                    right_click = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:  # M - вкл/выкл музыку
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                elif event.key == pygame.K_PLUS:  # + - увеличить громкость
                    vol = min(1.0, pygame.mixer.music.get_volume() + 0.1)
                    pygame.mixer.music.set_volume(vol)
                elif event.key == pygame.K_MINUS:  # - - уменьшить громкость
                    vol = max(0.0, pygame.mixer.music.get_volume() - 0.1)
                    pygame.mixer.music.set_volume(vol)
                elif event.key == pygame.K_f:  # F - пополнить запас выбранного барака
                    if self.selected_barracks:
                        self.selected_barracks.refill_gold(self, 50)
                elif event.key == pygame.K_r:  # R - восстановить шахту
                    if self.selected_mine and self.selected_mine.health <= 0:
                        self.buildings.remove(self.selected_mine)
                        new_mine = Building(self.selected_mine.x, self.selected_mine.y,
                                            BuildingType.GOLD_MINE, self.difficulty)
                        self.buildings.append(new_mine)
                        self.selected_mine = new_mine
                elif event.key == pygame.K_ESCAPE:  # ESC - вернуться из меню помощи
                    if self.state == GameState.HELP:
                        self.state = GameState.BUILD if self.build_timer < self.build_time else GameState.BATTLE
                elif event.key == pygame.K_1 and self.state in [GameState.BUILD, GameState.BATTLE]:
                    self.selected_building = BuildingType.BARRACKS
                    self.selected_barracks = None
                    self.selected_mine = None
                elif event.key == pygame.K_2 and self.state in [GameState.BUILD, GameState.BATTLE]:
                    self.selected_building = BuildingType.GOLD_MINE
                    self.selected_barracks = None
                    self.selected_mine = None
                elif event.key == pygame.K_3 and self.state in [GameState.BUILD, GameState.BATTLE]:
                    self.selected_building = BuildingType.WALL
                    self.selected_barracks = None
                    self.selected_mine = None

        # Проверка кнопок
        if self.state == GameState.MENU:
            self.easy_button.check_hover(mouse_pos)
            self.medium_button.check_hover(mouse_pos)
            self.hard_button.check_hover(mouse_pos)

            if mouse_click:
                if self.easy_button.is_clicked(mouse_pos, mouse_click):
                    self.difficulty = Difficulty.EASY
                    self.gold = 500
                    self.state = GameState.BUILD
                elif self.medium_button.is_clicked(mouse_pos, mouse_click):
                    self.difficulty = Difficulty.MEDIUM
                    self.gold = 400
                    self.state = GameState.BUILD
                elif self.hard_button.is_clicked(mouse_pos, mouse_click):
                    self.difficulty = Difficulty.HARD
                    self.gold = 300
                    self.state = GameState.BUILD

        elif self.state == GameState.HELP:
            self.back_button.check_hover(mouse_pos)
            if mouse_click and self.back_button.is_clicked(mouse_pos, mouse_click):
                self.state = GameState.BUILD if self.build_timer < self.build_time else GameState.BATTLE

        elif self.state in [GameState.BUILD, GameState.BATTLE]:
            self.help_button.check_hover(mouse_pos)
            if mouse_click and self.help_button.is_clicked(mouse_pos, mouse_click):
                self.state = GameState.HELP

            if right_click:  # Обработка ПКМ для отмены выбора
                self.selected_building = None
                self.selected_barracks = None
                self.selected_mine = None

            if mouse_click:
                if self.selected_building:
                    grid_x = (mouse_pos[0] // GRID_SIZE) * GRID_SIZE
                    grid_y = (mouse_pos[1] // GRID_SIZE) * GRID_SIZE

                    valid_position = True
                    new_width = 2 if self.selected_building in [BuildingType.TOWN_HALL, BuildingType.BARRACKS] else 1
                    new_height = 2 if self.selected_building in [BuildingType.TOWN_HALL, BuildingType.BARRACKS] else 1

                    if (grid_x < BORDER_OFFSET or
                            grid_x + new_width * GRID_SIZE > SCREEN_WIDTH - BORDER_OFFSET or
                            grid_y < BORDER_OFFSET or
                            grid_y + new_height * GRID_SIZE > SCREEN_HEIGHT - BORDER_OFFSET):
                        valid_position = False

                    for building in self.buildings:
                        if (grid_x < building.x + building.width * GRID_SIZE and
                                grid_x + new_width * GRID_SIZE > building.x and
                                grid_y < building.y + building.height * GRID_SIZE and
                                grid_y + new_height * GRID_SIZE > building.y):
                            valid_position = False
                            break

                    if valid_position:
                        cost = 0
                        if self.selected_building == BuildingType.BARRACKS:
                            cost = 100
                        elif self.selected_building == BuildingType.GOLD_MINE:
                            cost = 75
                        elif self.selected_building == BuildingType.WALL:
                            cost = 50

                        if self.gold >= cost:
                            self.gold -= cost
                            new_building = Building(grid_x, grid_y, self.selected_building, self.difficulty)
                            self.buildings.append(new_building)
                            # После размещения здания сбрасываем выбор
                            self.selected_building = None
                else:
                    # Сброс выбора
                    self.selected_barracks = None
                    self.selected_mine = None

                    # Выбор здания для взаимодействия
                    for building in self.buildings:
                        if (building.x <= mouse_pos[0] <= building.x + building.width * GRID_SIZE and
                                building.y <= mouse_pos[1] <= building.y + building.height * GRID_SIZE):
                            if building.type == BuildingType.WALL and building.health <= 0:
                                building.repair(self)
                            elif building.type == BuildingType.BARRACKS:
                                self.selected_barracks = building
                            elif building.type == BuildingType.GOLD_MINE:
                                self.selected_mine = building
                            break

        elif self.state in [GameState.WIN, GameState.LOSE]:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.__init__()

    def update(self):
        dt = self.clock.get_time()

        if self.state == GameState.BUILD:
            self.build_timer += dt
            if self.build_timer >= self.build_time:
                self.state = GameState.BATTLE
                self.wave = 0
                self.spawn_wave()

        elif self.state == GameState.BATTLE:
            enemies_remaining = any(not unit.is_defender for unit in self.units)

            if not enemies_remaining:
                self.wave_timer += dt
                if self.wave_timer >= self.wave_interval:
                    self.wave_timer = 0
                    self.wave += 1
                    if self.wave < 3:
                        self.spawn_wave()
                    else:
                        self.state = GameState.WIN

        # Обновляем здания (включая казармы и шахты)
        for building in self.buildings:
            building.update(dt, self)

        # Обновляем юнитов
        for unit in self.units[:]:
            unit.update(dt, self)
            if unit.health <= 0 and unit in self.units:
                self.units.remove(unit)

    def draw(self):
        if self.state == GameState.MENU:
            self.screen.blit(textures['menu_background'], (0, 0))

            title = self.font.render("Clash of Pygame", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

            self.easy_button.draw(self.screen, self.font)
            self.medium_button.draw(self.screen, self.font)
            self.hard_button.draw(self.screen, self.font)

            instructions = self.small_font.render("Выберите уровень сложности", True, WHITE)
            self.screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 500))

        elif self.state == GameState.HELP:
            self.draw_help_screen()

        elif self.state in [GameState.BUILD, GameState.BATTLE]:
            self.screen.blit(textures['background'], (0, 0))

            if self.state == GameState.BUILD:
                for x in range(0, SCREEN_WIDTH, GRID_SIZE):
                    pygame.draw.line(self.screen, GRAY, (x, 0), (x, SCREEN_HEIGHT), 1)
                for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
                    pygame.draw.line(self.screen, GRAY, (0, y), (SCREEN_WIDTH, y), 1)

            for building in self.buildings:
                building.draw(self.screen)

            for unit in self.units:
                unit.draw(self.screen)

            time_left = max(0, (self.build_time - self.build_timer) // 1000) if self.state == GameState.BUILD else 0
            timer_text = self.font.render(
                f"Build Time: {time_left}s" if self.state == GameState.BUILD else f"Wave: {self.wave + 1}/3", True,
                BLACK)
            self.screen.blit(timer_text, (20, 20))

            gold_text = self.font.render(f"Gold: {self.gold}", True, YELLOW)
            self.screen.blit(gold_text, (20, 60))

            if self.state == GameState.BUILD:
                instructions = self.small_font.render("Press 1: Barracks (100g), 2: Gold Mine (75g), 3: Wall (50g)",
                                                      True,
                                                      BLACK)
                self.screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 20))

                repair_text = self.small_font.render(
                    "Left-click: select/interact, Right-click: cancel, F: fund barrack, R: restore mine", True, BLACK)
                self.screen.blit(repair_text, (SCREEN_WIDTH // 2 - repair_text.get_width() // 2, 60))

            # Подсветка выбранного здания
            if self.selected_barracks:
                pygame.draw.rect(self.screen, BLUE,
                                 (self.selected_barracks.x - 2, self.selected_barracks.y - 2,
                                  self.selected_barracks.width * GRID_SIZE + 4,
                                  self.selected_barracks.height * GRID_SIZE + 4), 2)

                status_text = self.small_font.render(f"Press F to fund (50g)", True, BLUE)
                self.screen.blit(status_text, (self.selected_barracks.x, self.selected_barracks.y - 30))

            if self.selected_mine:
                pygame.draw.rect(self.screen, YELLOW,
                                 (self.selected_mine.x - 2, self.selected_mine.y - 2,
                                  self.selected_mine.width * GRID_SIZE + 4,
                                  self.selected_mine.height * GRID_SIZE + 4), 2)

                if self.selected_mine.health <= 0:
                    status_text = self.small_font.render(f"Press R to restore (75g)", True, YELLOW)
                    self.screen.blit(status_text, (self.selected_mine.x, self.selected_mine.y - 30))

            if self.selected_building:
                mouse_pos = pygame.mouse.get_pos()
                grid_x = (mouse_pos[0] // GRID_SIZE) * GRID_SIZE
                grid_y = (mouse_pos[1] // GRID_SIZE) * GRID_SIZE

                width = 2 if self.selected_building in [BuildingType.TOWN_HALL, BuildingType.BARRACKS] else 1
                height = 2 if self.selected_building in [BuildingType.TOWN_HALL, BuildingType.BARRACKS] else 1

                # Прозрачная поверхность для предпросмотра
                preview = pygame.Surface((width * GRID_SIZE, height * GRID_SIZE), pygame.SRCALPHA)
                preview.fill((255, 255, 255, 128))

                if self.selected_building == BuildingType.BARRACKS:
                    preview.blit(pygame.transform.scale(textures['barracks'], (width * GRID_SIZE, height * GRID_SIZE)),
                                 (0, 0))
                elif self.selected_building == BuildingType.GOLD_MINE:
                    preview.blit(pygame.transform.scale(textures['gold_mine'], (width * GRID_SIZE, height * GRID_SIZE)),
                                 (0, 0))
                elif self.selected_building == BuildingType.WALL:
                    preview.blit(pygame.transform.scale(textures['wall'], (width * GRID_SIZE, height * GRID_SIZE)),
                                 (0, 0))

                self.screen.blit(preview, (grid_x, grid_y))

            # Кнопка помощи
            self.help_button.draw(self.screen, self.font)

        elif self.state == GameState.WIN:
            self.screen.blit(textures['background'], (0, 0))
            win_text = self.font.render("Victory! Press R to restart", True, GREEN)
            self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                                        SCREEN_HEIGHT // 2 - win_text.get_height() // 2))

        elif self.state == GameState.LOSE:
            self.screen.blit(textures['background'], (0, 0))
            lose_text = self.font.render("Defeat! Press R to restart", True, RED)
            self.screen.blit(lose_text, (SCREEN_WIDTH // 2 - lose_text.get_width() // 2,
                                         SCREEN_HEIGHT // 2 - lose_text.get_height() // 2))

        pygame.display.flip()

    def run(self):
        # Воспроизведение музыки
        if music_loaded:
            pygame.mixer.music.play(-1)  # -1 означает бесконечный цикл
            pygame.mixer.music.set_volume(0.5)  # Громкость от 0.0 до 1.0

        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
import pygame
import math
from constants import GRID_SIZE, RED, GREEN, YELLOW
from enum import Enum


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
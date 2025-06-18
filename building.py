import pygame
import math

from unit import Unit
from constants import GRID_SIZE, RED, GREEN, YELLOW, Difficulty, BuildingType, GameState, UnitType
from enum import Enum

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

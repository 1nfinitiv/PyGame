import math
import pygame
from enum import Enum
import random


class BuildingType(Enum):
    TOWN_HALL = 0
    HOUSE = 1
    FARM = 2
    MINE = 3
    BARRACKS = 4
    WALL = 5
    TOWER = 6
    

class EnemyType(Enum):
    BANDIT = 0
    ARCHER = 1
    SIEGE = 2
    BOSS = 3

class Enemy:
    def select_target(self, buildings, units):
        """Умный выбор цели для врагов с учетом типа"""
        # 1. Фильтрация доступных целей
        available_targets = []

        # Для осадных орудий - только здания
        if self.type == EnemyType.SIEGE:
            available_targets = [(b, math.hypot(self.x - b.x, self.y - b.y))
                                 for b in buildings if b.hp > 0]
        # Для остальных - все цели
        else:
            available_targets = [(u, math.hypot(self.x - u.x, self.y - u.y))
                                 for u in units if u.hp > 0]
            available_targets += [(b, math.hypot(self.x - b.x, self.y - b.y))
                                  for b in buildings if b.hp > 0]

        # 2. Стратегия выбора в зависимости от типа
        if not available_targets:
            return None

        if self.type == EnemyType.BANDIT:
            # Бандиты атакуют самое слабое
            available_targets.sort(key=lambda x: x[0].hp)
            return available_targets[0][0]

        elif self.type == EnemyType.BOSS:
            # Босс целенаправленно идет к ратуше
            town_hall = next((b for b in buildings
                              if b.type == BuildingType.TOWN_HALL), None)
            if town_hall:
                return town_hall
            # Если ратуша разрушена - атакует случайную цель
            return random.choice(available_targets)[0]

        elif self.type == EnemyType.SIEGE:
            # Осадные орудия ломают стены, затем башни
            walls = [b for b in buildings
                     if b.type == BuildingType.WALL and b.hp > 0]
            if walls:
                walls.sort(key=lambda x: math.hypot(self.x - x.x, self.y - x.y))
                return walls[0]

            towers = [b for b in buildings
                      if b.type == BuildingType.TOWER and b.hp > 0]
            if towers:
                towers.sort(key=lambda x: math.hypot(self.x - x.x, self.y - x.y))
                return towers[0]

            return available_targets[0][0]

        # По умолчанию - ближайшая цель
        available_targets.sort(key=lambda x: x[1])
        return available_targets[0][0]
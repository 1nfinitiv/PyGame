import pygame
import sys
import random
import math
from enum import Enum

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
TILE_SIZE = 64

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
GRAY = (100, 100, 100)

# Создание экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Деревенская Оборона")
clock = pygame.time.Clock()


# Загрузка изображений (заглушки)
def load_image(name, size=None):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(BLUE if "water" in name else BROWN if "wall" in name else GREEN)
    if size:
        surf = pygame.transform.scale(surf, size)
    return surf


# Загрузка звуков
def load_sound(name):
    return None  # В реальной игре нужно добавить звуковые файлы


# Перечисления
class BuildingType(Enum):
    TOWN_HALL = 0
    HOUSE = 1
    FARM = 2
    MINE = 3
    BARRACKS = 4
    WALL = 5
    TOWER = 6


class UnitType(Enum):
    VILLAGER = 0
    WARRIOR = 1
    ARCHER = 2
    HERO = 3


class EnemyType(Enum):
    BANDIT = 0
    ARCHER = 1
    SIEGE = 2
    BOSS = 3


# Класс здания
class Building:
    def __init__(self, x, y, building_type):
        self.x = x
        self.y = y
        self.type = building_type
        self.hp = self.get_max_hp()
        self.level = 1
        self.progress = 0

    def get_max_hp(self):
        return {
            BuildingType.TOWN_HALL: 500,
            BuildingType.HOUSE: 200,
            BuildingType.FARM: 150,
            BuildingType.MINE: 200,
            BuildingType.BARRACKS: 250,
            BuildingType.WALL: 300,
            BuildingType.TOWER: 200
        }[self.type]

    def update(self):
        if self.type == BuildingType.FARM:
            self.progress += 0.1
            if self.progress >= 100:
                self.progress = 0
                return "food"
        elif self.type == BuildingType.MINE:
            self.progress += 0.05
            if self.progress >= 100:
                self.progress = 0
                return random.choice(["stone", "gold"])
        return None

    def draw(self, surface):
        color = {
            BuildingType.TOWN_HALL: (200, 150, 0),
            BuildingType.HOUSE: (180, 100, 0),
            BuildingType.FARM: (0, 150, 0),
            BuildingType.MINE: (100, 100, 100),
            BuildingType.BARRACKS: (70, 70, 70),
            BuildingType.WALL: (120, 80, 40),
            BuildingType.TOWER: (80, 80, 80)
        }[self.type]

        pygame.draw.rect(surface, color, (self.x, self.y, TILE_SIZE, TILE_SIZE))

        # Рисуем HP
        hp_ratio = self.hp / self.get_max_hp()
        pygame.draw.rect(surface, RED, (self.x, self.y - 10, TILE_SIZE, 5))
        pygame.draw.rect(surface, GREEN, (self.x, self.y - 10, TILE_SIZE * hp_ratio, 5))


# Класс юнита
class Unit:
    def __init__(self, x, y, unit_type):
        self.x = x
        self.y = y
        self.type = unit_type
        self.hp = self.get_max_hp()
        self.target = None
        self.cooldown = 0

    def get_max_hp(self):
        return {
            UnitType.VILLAGER: 50,
            UnitType.WARRIOR: 100,
            UnitType.ARCHER: 60,
            UnitType.HERO: 200
        }[self.type]

    def get_damage(self):
        return {
            UnitType.VILLAGER: 2,
            UnitType.WARRIOR: 15,
            UnitType.ARCHER: 8,
            UnitType.HERO: 30
        }[self.type]

    def get_range(self):
        return {
            UnitType.VILLAGER: 1,
            UnitType.WARRIOR: 1,
            UnitType.ARCHER: 3,
            UnitType.HERO: 1.5
        }[self.type]

    def update(self, enemies, buildings):
        if self.cooldown > 0:
            self.cooldown -= 1

        if self.type == UnitType.VILLAGER:
            # Крестьяне работают на ближайшем здании
            closest_building = None
            min_dist = float('inf')
            for building in buildings:
                dist = math.hypot(self.x - building.x, self.y - building.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_building = building

            if closest_building and min_dist > TILE_SIZE:
                # Двигаемся к зданию
                angle = math.atan2(closest_building.y - self.y, closest_building.x - self.x)
                speed = 1
                self.x += math.cos(angle) * speed
                self.y += math.sin(angle) * speed
        else:
            # Воины ищут врагов
            closest_enemy = None
            min_dist = float('inf')
            for enemy in enemies:
                dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy

            if closest_enemy:
                if min_dist <= self.get_range() * TILE_SIZE:
                    # Атакуем врага
                    if self.cooldown <= 0:
                        closest_enemy.hp -= self.get_damage()
                        self.cooldown = 30  # Задержка между атаками
                else:
                    # Двигаемся к врагу
                    angle = math.atan2(closest_enemy.y - self.y, closest_enemy.x - self.x)
                    speed = 0.8 if self.type == UnitType.WARRIOR else 1.2
                    self.x += math.cos(angle) * speed
                    self.y += math.sin(angle) * speed

    def draw(self, surface):
        color = {
            UnitType.VILLAGER: (200, 150, 100),
            UnitType.WARRIOR: (70, 70, 200),
            UnitType.ARCHER: (100, 200, 100),
            UnitType.HERO: (255, 215, 0)
        }[self.type]

        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 10)

        # Рисуем HP
        hp_ratio = self.hp / self.get_max_hp()
        pygame.draw.rect(surface, RED, (self.x - 10, self.y - 20, 20, 3))
        pygame.draw.rect(surface, GREEN, (self.x - 10, self.y - 20, 20 * hp_ratio, 3))


# Класс врага
class Enemy:
    def __init__(self, x, y, enemy_type, wave):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.hp = self.get_max_hp() * (1 + wave * 0.1)
        self.speed = self.get_speed()
        self.damage = self.get_damage() * (1 + wave * 0.05)
        self.target = None
        self.cooldown = 0

    def get_max_hp(self):
        return {
            EnemyType.BANDIT: 40,
            EnemyType.ARCHER: 30,
            EnemyType.SIEGE: 80,
            EnemyType.BOSS: 500
        }[self.type]

    def get_damage(self):
        return {
            EnemyType.BANDIT: 5,
            EnemyType.ARCHER: 8,
            EnemyType.SIEGE: 25,
            EnemyType.BOSS: 40
        }[self.type]

    def get_speed(self):
        return {
            EnemyType.BANDIT: 1.5,
            EnemyType.ARCHER: 1.2,
            EnemyType.SIEGE: 0.5,
            EnemyType.BOSS: 0.8
        }[self.type]

    def get_range(self):
        return {
            EnemyType.BANDIT: 1,
            EnemyType.ARCHER: 3,
            EnemyType.SIEGE: 4,
            EnemyType.BOSS: 1.5
        }[self.type]

    def update(self, buildings, units):
        # Ищем ближайшую цель (здания имеют приоритет)
        targets = buildings + units
        closest_target = None
        min_dist = float('inf')

        for target in targets:
            dist = math.hypot(self.x - target.x, self.y - target.y)
            if dist < min_dist:
                min_dist = dist
                closest_target = target

        if closest_target:
            if min_dist <= self.get_range() * TILE_SIZE:
                # Атакуем цель
                if self.cooldown <= 0:
                    closest_target.hp -= self.damage
                    self.cooldown = 30
            else:
                # Двигаемся к цели
                angle = math.atan2(closest_target.y - self.y, closest_target.x - self.x)
                self.x += math.cos(angle) * self.speed
                self.y += math.sin(angle) * self.speed

    def draw(self, surface):
        color = {
            EnemyType.BANDIT: (150, 0, 0),
            EnemyType.ARCHER: (150, 50, 0),
            EnemyType.SIEGE: (50, 50, 50),
            EnemyType.BOSS: (200, 0, 0)
        }[self.type]

        size = {
            EnemyType.BANDIT: 12,
            EnemyType.ARCHER: 10,
            EnemyType.SIEGE: 20,
            EnemyType.BOSS: 25
        }[self.type]

        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)

        # Рисуем HP
        hp_ratio = self.hp / self.get_max_hp()
        bar_width = size * 2
        pygame.draw.rect(surface, RED, (self.x - bar_width / 2, self.y - size - 10, bar_width, 5))
        pygame.draw.rect(surface, GREEN, (self.x - bar_width / 2, self.y - size - 10, bar_width * hp_ratio, 5))


# Класс снаряда
class Projectile:
    def __init__(self, x, y, target, damage, speed=5):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.speed = speed
        self.active = True

    def update(self):
        if not self.active or not self.target:
            return

        angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed

        # Проверка попадания
        if math.hypot(self.x - self.target.x, self.y - self.target.y) < 10:
            self.target.hp -= self.damage
            self.active = False

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), 3)


# Класс игры
class Game:
    def __init__(self):
        self.resources = {
            "wood": 100,
            "stone": 50,
            "food": 50,
            "gold": 30
        }

        self.buildings = []
        self.units = []
        self.enemies = []
        self.projectiles = []
        self.traps = []

        # Создаем начальные здания
        town_hall = Building(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BuildingType.TOWN_HALL)
        self.buildings.append(town_hall)

        # Настройки игры
        self.wave = 0
        self.wave_timer = 0
        self.wave_cooldown = 60 * 30  # 30 секунд между волнами
        self.game_state = "build"  # или "attack"
        self.selected_building = None
        self.worker_distribution = {
            "farmers": 40,
            "miners": 30,
            "soldiers": 30
        }

        # Герой
        self.hero_active = False
        self.hero_timer = 0
        self.hero_cooldown = 60 * 60  # 60 секунд перезарядки

        # Шрифты
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 48)

    def spawn_wave(self):
        self.wave += 1
        self.game_state = "attack"

        # Определяем количество и тип врагов в зависимости от волны
        enemy_count = 5 + self.wave * 2
        enemy_types = [EnemyType.BANDIT]

        if self.wave >= 2:
            enemy_types.append(EnemyType.ARCHER)
        if self.wave >= 3:
            enemy_types.append(EnemyType.SIEGE)
        if self.wave >= 5:
            enemy_types.append(EnemyType.BOSS)

        # Спавним врагов по краям карты
        for _ in range(enemy_count):
            side = random.randint(0, 3)
            if side == 0:  # Верх
                x = random.randint(0, SCREEN_WIDTH)
                y = -50
            elif side == 1:  # Право
                x = SCREEN_WIDTH + 50
                y = random.randint(0, SCREEN_HEIGHT)
            elif side == 2:  # Низ
                x = random.randint(0, SCREEN_WIDTH)
                y = SCREEN_HEIGHT + 50
            else:  # Лево
                x = -50
                y = random.randint(0, SCREEN_HEIGHT)

            enemy_type = random.choice(enemy_types)
            self.enemies.append(Enemy(x, y, enemy_type, self.wave))

    def update(self):
        # Обновляем здания
        for building in self.buildings:
            resource = building.update()
            if resource:
                self.resources[resource] += 1

        # Обновляем юнитов
        for unit in self.units:
            unit.update(self.enemies, self.buildings)

        # Обновляем врагов
        for enemy in self.enemies[:]:
            enemy.update(self.buildings, self.units)
            if enemy.hp <= 0:
                self.enemies.remove(enemy)
                self.resources["gold"] += 5  # Награда за убийство

        # Обновляем снаряды
        for projectile in self.projectiles[:]:
            projectile.update()
            if not projectile.active:
                self.projectiles.remove(projectile)

        # Проверяем условия победы/поражения
        if self.game_state == "attack" and not self.enemies:
            self.game_state = "build"
            self.wave_timer = self.wave_cooldown

        # Уменьшаем таймер между волнами
        if self.game_state == "build":
            if self.wave_timer > 0:
                self.wave_timer -= 1
            else:
                self.spawn_wave()

        # Уменьшаем таймер героя
        if self.hero_active:
            self.hero_timer -= 1
            if self.hero_timer <= 0:
                self.hero_active = False
        elif self.hero_cooldown > 0:
            self.hero_cooldown -= 1

        # Автоматическое создание юнитов
        self.auto_spawn_units()

        # Проверяем разрушение ратуши
        town_hall = next((b for b in self.buildings if b.type == BuildingType.TOWN_HALL), None)
        if town_hall and town_hall.hp <= 0:
            return "lose"

        return "continue"

    def auto_spawn_units(self):
        # Создаем крестьян из домов
        houses = [b for b in self.buildings if b.type == BuildingType.HOUSE]
        max_villagers = len(houses) * 2
        current_villagers = len([u for u in self.units if u.type == UnitType.VILLAGER])

        if current_villagers < max_villagers and self.resources["food"] >= 10:
            self.resources["food"] -= 10
            house = random.choice(houses)
            self.units.append(Unit(house.x, house.y, UnitType.VILLAGER))

        # Создаем воинов из казарм
        barracks = [b for b in self.buildings if b.type == BuildingType.BARRACKS]
        if barracks and self.resources["food"] >= 20 and self.resources["gold"] >= 10:
            soldier_percent = self.worker_distribution["soldiers"] / 100
            if random.random() < soldier_percent * 0.05:  # 5% шанс за кадр
                self.resources["food"] -= 20
                self.resources["gold"] -= 10
                barrack = random.choice(barracks)
                unit_type = random.choice([UnitType.WARRIOR, UnitType.ARCHER])
                self.units.append(Unit(barrack.x, barrack.y, unit_type))

    def draw(self, surface):
        # Рисуем фон
        surface.fill((50, 150, 50))

        # Рисуем здания
        for building in self.buildings:
            building.draw(surface)

        # Рисуем юнитов
        for unit in self.units:
            unit.draw(surface)

        # Рисуем врагов
        for enemy in self.enemies:
            enemy.draw(surface)

        # Рисуем снаряды
        for projectile in self.projectiles:
            projectile.draw(surface)

        # Рисуем UI
        self.draw_ui(surface)

        # Сообщения о волнах
        if self.game_state == "attack":
            wave_text = self.big_font.render(f"Волна {self.wave}", True, RED)
            surface.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 20))
        else:
            time_left = self.wave_timer // 60
            if time_left > 0:
                wave_text = self.big_font.render(f"До следующей волны: {time_left}", True, BLUE)
                surface.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 20))

    def draw_ui(self, surface):
        # Панель ресурсов
        y_offset = 10
        for resource, amount in self.resources.items():
            text = self.font.render(f"{resource}: {amount}", True, WHITE)
            surface.blit(text, (10, y_offset))
            y_offset += 25

        # Панель строительства
        pygame.draw.rect(surface, (70, 70, 70), (SCREEN_WIDTH - 150, 10, 140, 200))
        build_text = self.font.render("Строить (1-7):", True, WHITE)
        surface.blit(build_text, (SCREEN_WIDTH - 140, 15))

        buildings = [
            ("1. Ратуша", "town_hall"),
            ("2. Дом", "house"),
            ("3. Ферма", "farm"),
            ("4. Шахта", "mine"),
            ("5. Казармы", "barracks"),
            ("6. Стена", "wall"),
            ("7. Башня", "tower"),
            ("8. Начало игры")
        ]

        for i, (name, _) in enumerate(buildings):
            text = self.font.render(name, True, WHITE)
            surface.blit(text, (SCREEN_WIDTH - 140, 40 + i * 20))

        # Распределение рабочих
        pygame.draw.rect(surface, (70, 70, 70), (SCREEN_WIDTH - 150, 220, 140, 100))
        worker_text = self.font.render("Рабочие:", True, WHITE)
        surface.blit(worker_text, (SCREEN_WIDTH - 140, 225))

        farmer_text = self.font.render(f"Фермеры: {self.worker_distribution['farmers']}%", True, WHITE)
        miner_text = self.font.render(f"Шахтеры: {self.worker_distribution['miners']}%", True, WHITE)
        soldier_text = self.font.render(f"Солдаты: {self.worker_distribution['soldiers']}%", True, WHITE)

        surface.blit(farmer_text, (SCREEN_WIDTH - 140, 250))
        surface.blit(miner_text, (SCREEN_WIDTH - 140, 270))
        surface.blit(soldier_text, (SCREEN_WIDTH - 140, 290))

        # Кнопка героя
        if not self.hero_active and self.hero_cooldown <= 0:
            pygame.draw.rect(surface, (0, 100, 0), (SCREEN_WIDTH - 150, 330, 140, 40))
            hero_text = self.font.render("Вызвать героя", True, WHITE)
            surface.blit(hero_text, (SCREEN_WIDTH - 140, 340))
        else:
            pygame.draw.rect(surface, (100, 100, 100), (SCREEN_WIDTH - 150, 330, 140, 40))
            if self.hero_active:
                hero_text = self.font.render(f"Герой: {self.hero_timer // 60}", True, WHITE)
            else:
                hero_text = self.font.render(f"Перезарядка: {self.hero_cooldown // 60}", True, WHITE)
            surface.blit(hero_text, (SCREEN_WIDTH - 140, 340))

    def build(self, building_type, x, y):
        costs = {
            BuildingType.TOWN_HALL: {"wood": 100, "stone": 50},
            BuildingType.HOUSE: {"wood": 20, "stone": 5},
            BuildingType.FARM: {"wood": 15, "stone": 0},
            BuildingType.MINE: {"wood": 25, "stone": 15},
            BuildingType.BARRACKS: {"wood": 30, "stone": 20},
            BuildingType.WALL: {"wood": 10, "stone": 5},
            BuildingType.TOWER: {"wood": 20, "stone": 10}
        }

        # Проверяем достаточно ли ресурсов
        can_build = True
        for resource, amount in costs[building_type].items():
            if self.resources[resource] < amount:
                can_build = False
                break

        if can_build:
            # Проверяем нет ли здания на этом месте
            for building in self.buildings:
                if abs(building.x - x) < TILE_SIZE and abs(building.y - y) < TILE_SIZE:
                    return False

            # Строим
            for resource, amount in costs[building_type].items():
                self.resources[resource] -= amount

            self.buildings.append(Building(x, y, building_type))
            return True
        return False

    def activate_hero(self):
        if not self.hero_active and self.hero_cooldown <= 0:
            self.hero_active = True
            self.hero_timer = 60 * 20  # 20 секунд
            self.hero_cooldown = 60 * 60  # 60 секунд перезарядки

            # Создаем героя у ратуши
            town_hall = next((b for b in self.buildings if b.type == BuildingType.TOWN_HALL), None)
            if town_hall:
                self.units.append(Unit(town_hall.x, town_hall.y, UnitType.HERO))
            return True
        return False

    def change_worker_distribution(self, worker_type, change):
        total = sum(self.worker_distribution.values())
        if total + change <= 100 and self.worker_distribution[worker_type] + change >= 0:
            self.worker_distribution[worker_type] += change


# Основной игровой цикл
def main():
    game = Game()
    running = True

    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ
                    x, y = event.pos

                    # Проверяем клик по UI
                    if SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 10 and 330 <= y <= 370:
                        game.activate_hero()
                    elif SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 10 and y >= 220:
                        # Изменяем распределение рабочих
                        if 250 <= y <= 270:  # Фермеры
                            game.change_worker_distribution("farmers", 10)
                        elif 270 <= y <= 290:  # Шахтеры
                            game.change_worker_distribution("miners", 10)
                        elif 290 <= y <= 310:  # Солдаты
                            game.change_worker_distribution("soldiers", 10)
                    else:
                        # Строительство
                        if game.selected_building:
                            game.build(game.selected_building, x - TILE_SIZE // 2, y - TILE_SIZE // 2)

            if event.type == pygame.KEYDOWN:
                # Выбор здания для строительства
                if event.key == pygame.K_1:
                    game.selected_building = BuildingType.TOWN_HALL
                elif event.key == pygame.K_2:
                    game.selected_building = BuildingType.HOUSE
                elif event.key == pygame.K_3:
                    game.selected_building = BuildingType.FARM
                elif event.key == pygame.K_4:
                    game.selected_building = BuildingType.MINE
                elif event.key == pygame.K_5:
                    game.selected_building = BuildingType.BARRACKS
                elif event.key == pygame.K_6:
                    game.selected_building = BuildingType.WALL
                elif event.key == pygame.K_7:
                    game.selected_building = BuildingType.TOWER

        # Обновление игры
        result = game.update()
        if result == "lose":
            print("Игра окончена! Ваша деревня разрушена!")
            running = False

        # Отрисовка
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
import pygame
import sys
import math
import random
from pygame.locals import *

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
GRID_SIZE = 40
ZOOM_FACTOR = 1.1
SCROLL_SPEED = 20
BUILD_MODE = 0
ATTACK_MODE = 1

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
DARK_GREEN = (0, 100, 0)
LIGHT_GREEN = (144, 238, 144)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GREEN = (0,128,0)

# Настройки экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Clash of Clans Minimalist Remake")
clock = pygame.time.Clock()


class Building:
    def __init__(self, x, y, type_id):
        self.x = x
        self.y = y
        self.type_id = type_id
        self.health = 100
        self.max_health = 100
        self.size = 1  # В клетках

        # Определение свойств здания по типу
        if type_id == 0:  # Ратуша
            self.color = (200, 200, 0)
            self.size = 3
        elif type_id == 1:  # Казармы
            self.color = (0, 200, 200)
        elif type_id == 2:  # Золотой рудник
            self.color = (255, 215, 0)
        elif type_id == 3:  # Эликсир коллектор
            self.color = (255, 0, 255)
        elif type_id == 4:  # Пушка
            self.color = (200, 0, 0)
            self.attack_power = 10
        elif type_id == 5:  # Стена
            self.color = BROWN
            self.health = 50
            self.max_health = 50

    def draw(self, surface, camera_x, camera_y, zoom):
        screen_x = (self.x * GRID_SIZE - camera_x) * zoom + SCREEN_WIDTH // 2
        screen_y = (self.y * GRID_SIZE - camera_y) * zoom + SCREEN_HEIGHT // 2
        size = self.size * GRID_SIZE * zoom

        pygame.draw.rect(surface, self.color, (screen_x, screen_y, size, size))
        pygame.draw.rect(surface, BLACK, (screen_x, screen_y, size, size), 1)

        # Отображение здоровья
        health_bar_width = size * (self.health / self.max_health)
        pygame.draw.rect(surface, RED, (screen_x, screen_y - 10 * zoom, size, 5 * zoom))
        pygame.draw.rect(surface, GREEN, (screen_x, screen_y - 10 * zoom, health_bar_width, 5 * zoom))


class Troop:
    def __init__(self, x, y, type_id):
        self.x = x
        self.y = y
        self.type_id = type_id
        self.health = 100
        self.max_health = 100
        self.speed = 1.0
        self.attack_power = 10
        self.attack_range = 1.5
        self.target = None
        self.path = []

        # Определение свойств войск по типу
        if type_id == 0:  # Варвар
            self.color = (139, 69, 19)
            self.size = 0.8
        elif type_id == 1:  # Лучник
            self.color = (0, 100, 0)
            self.size = 0.7
            self.attack_range = 3.0
        elif type_id == 2:  # Гигант
            self.color = (255, 165, 0)
            self.size = 1.5
            self.health = 300
            self.max_health = 300
            self.speed = 0.5
        elif type_id == 3:  # Гоблин
            self.color = (0, 255, 0)
            self.size = 0.6
            self.speed = 1.5
        elif type_id == 4:  # Разрушитель стен
            self.color = (70, 70, 70)
            self.size = 0.9
            self.speed = 0.8
        elif type_id == 5:  # Воздушный шар
            self.color = (255, 0, 0)
            self.size = 1.2
            self.speed = 0.4

    def find_target(self, buildings):
        if self.type_id == 2 or self.type_id == 5:  # Гиганты и воздушные шары атакуют оборону
            defenses = [b for b in buildings if b.type_id == 4 or b.type_id == 0]  # Пушки и ратуша
            if defenses:
                self.target = min(defenses, key=lambda b: math.hypot(b.x - self.x, b.y - self.y))
                return
        elif self.type_id == 3:  # Гоблины атакуют ресурсы
            resources = [b for b in buildings if b.type_id == 2 or b.type_id == 3]  # Рудники и коллекторы
            if resources:
                self.target = min(resources, key=lambda b: math.hypot(b.x - self.x, b.y - self.y))
                return

        # Для всех остальных - ближайшее здание
        if buildings:
            self.target = min(buildings, key=lambda b: math.hypot(b.x - self.x, b.y - self.y))

    def move(self, buildings, walls, delta_time):
        if not self.target or self.target.health <= 0:
            self.find_target(buildings)
            if not self.target:
                return

        # Простой поиск пути (упрощенный)
        dx = self.target.x + self.target.size / 2 - self.x
        dy = self.target.y + self.target.size / 2 - self.y
        dist = math.hypot(dx, dy)

        if dist < self.attack_range:
            # Атаковать цель
            self.target.health -= self.attack_power * delta_time
        else:
            # Двигаться к цели
            if dist > 0:
                dx, dy = dx / dist, dy / dist
                self.x += dx * self.speed * delta_time
                self.y += dy * self.speed * delta_time

    def draw(self, surface, camera_x, camera_y, zoom):
        screen_x = (self.x * GRID_SIZE - camera_x) * zoom + SCREEN_WIDTH // 2
        screen_y = (self.y * GRID_SIZE - camera_y) * zoom + SCREEN_HEIGHT // 2
        size = self.size * GRID_SIZE * zoom

        pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), int(size / 2))
        pygame.draw.circle(surface, BLACK, (int(screen_x), int(screen_y)), int(size / 2), 1)

        # Отображение здоровья
        health_bar_width = size * (self.health / self.max_health)
        pygame.draw.rect(surface, RED, (screen_x - size / 2, screen_y - size / 2 - 10 * zoom, size, 5 * zoom))
        pygame.draw.rect(surface, GREEN,
                         (screen_x - size / 2, screen_y - size / 2 - 10 * zoom, health_bar_width, 5 * zoom))


class Game:
    def __init__(self):
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.mode = BUILD_MODE
        self.buildings = []
        self.troops = []
        self.selected_troop_type = 0
        self.selected_building_type = 0
        self.resources = {"gold": 1000, "elixir": 1000}
        self.building_limits = {0: 1, 1: 1, 2: 3, 3: 3, 4: 2, 5: 20}
        self.building_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # Создаем начальную базу
        self.buildings.append(Building(0, 0, 0))  # Ратуша
        self.building_counts[0] += 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_TAB:
                    self.mode = ATTACK_MODE if self.mode == BUILD_MODE else BUILD_MODE
                elif event.key in (K_0, K_1, K_2, K_3, K_4, K_5):
                    if self.mode == ATTACK_MODE:
                        self.selected_troop_type = event.key - K_0
                    else:
                        self.selected_building_type = event.key - K_0

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    grid_x, grid_y = self.screen_to_world(mouse_x, mouse_y)

                    if self.mode == BUILD_MODE:
                        if self.can_place_building(grid_x, grid_y, self.selected_building_type):
                            self.buildings.append(Building(grid_x, grid_y, self.selected_building_type))
                            self.building_counts[self.selected_building_type] += 1
                    else:  # ATTACK_MODE
                        self.troops.append(Troop(grid_x, grid_y, self.selected_troop_type))

            elif event.type == MOUSEWHEEL:
                if pygame.key.get_mods() & KMOD_LCTRL:
                    # Масштабирование
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    world_x, world_y = self.screen_to_world(mouse_x, mouse_y)

                    if event.y > 0:
                        self.zoom *= ZOOM_FACTOR
                    else:
                        self.zoom /= ZOOM_FACTOR

                    # Корректировка камеры для масштабирования к курсору
                    new_world_x, new_world_y = self.screen_to_world(mouse_x, mouse_y)
                    self.camera_x += (new_world_x - world_x) * GRID_SIZE
                    self.camera_y += (new_world_y - world_y) * GRID_SIZE
                else:
                    # Прокрутка карты
                    self.camera_x -= event.y * SCROLL_SPEED / self.zoom
                    self.camera_y -= event.y * SCROLL_SPEED / self.zoom

    def screen_to_world(self, screen_x, screen_y):
        """Преобразует экранные координаты в мировые"""
        world_x = (screen_x - SCREEN_WIDTH // 2) / (GRID_SIZE * self.zoom) + self.camera_x / GRID_SIZE
        world_y = (screen_y - SCREEN_HEIGHT // 2) / (GRID_SIZE * self.zoom) + self.camera_y / GRID_SIZE
        return world_x, world_y

    def can_place_building(self, x, y, building_type):
        """Проверяет, можно ли разместить здание в данной позиции"""
        # Проверка лимитов
        if self.building_counts.get(building_type, 0) >= self.building_limits.get(building_type, 0):
            return False

        # Проверка на выход за границы карты (упрощенно)
        size = 3 if building_type == 0 else 1  # Ратуша больше

        # Проверка на пересечение с другими зданиями
        new_building_rect = pygame.Rect(x, y, size, size)
        for building in self.buildings:
            building_rect = pygame.Rect(building.x, building.y, building.size, building.size)
            if new_building_rect.colliderect(building_rect):
                return False

        return True

    def update(self, delta_time):
        # Обновление войск
        for troop in self.troops:
            troop.move([b for b in self.buildings if b.health > 0],
                       [b for b in self.buildings if b.type_id == 5],
                       delta_time)

        # Удаление уничтоженных зданий и войск
        self.buildings = [b for b in self.buildings if b.health > 0]
        self.troops = [t for t in self.troops if t.health > 0]

    def draw(self, surface):
        surface.fill(LIGHT_GREEN)

        # Рисуем сетку
        for x in range(-20, 20):
            for y in range(-20, 20):
                screen_x = (x * GRID_SIZE - self.camera_x) * self.zoom + SCREEN_WIDTH // 2
                screen_y = (y * GRID_SIZE - self.camera_y) * self.zoom + SCREEN_HEIGHT // 2
                pygame.draw.rect(surface, GRAY, (screen_x, screen_y, GRID_SIZE * self.zoom, GRID_SIZE * self.zoom), 1)

        # Рисуем здания
        for building in sorted(self.buildings, key=lambda b: b.y):  # Сортировка по Y для правильного отображения
            building.draw(surface, self.camera_x, self.camera_y, self.zoom)

        # Рисуем войска
        for troop in self.troops:
            troop.draw(surface, self.camera_x, self.camera_y, self.zoom)

        # Рисуем панель инструментов
        pygame.draw.rect(surface, GRAY, (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 60))

        if self.mode == BUILD_MODE:
            # Панель строительства
            for i in range(6):
                color = (200, 200, 200) if self.building_counts.get(i, 0) < self.building_limits.get(i, 0) else (
                100, 100, 100)
                pygame.draw.rect(surface, color, (10 + i * 70, SCREEN_HEIGHT - 50, 50, 50))
                pygame.draw.rect(surface, BLACK, (10 + i * 70, SCREEN_HEIGHT - 50, 50, 50), 2)

                if i == self.selected_building_type:
                    pygame.draw.rect(surface, YELLOW, (10 + i * 70, SCREEN_HEIGHT - 50, 50, 50), 3)

                # Отображение количества
                font = pygame.font.SysFont(None, 20)
                count_text = font.render(f"{self.building_counts.get(i, 0)}/{self.building_limits.get(i, 0)}", True,
                                         BLACK)
                surface.blit(count_text, (15 + i * 70, SCREEN_HEIGHT - 45))
        else:
            # Панель атаки
            for i in range(6):
                color = (200, 200, 200)
                pygame.draw.rect(surface, color, (10 + i * 70, SCREEN_HEIGHT - 50, 50, 50))
                pygame.draw.rect(surface, BLACK, (10 + i * 70, SCREEN_HEIGHT - 50, 50, 50), 2)

                if i == self.selected_troop_type:
                    pygame.draw.rect(surface, YELLOW, (10 + i * 70, SCREEN_HEIGHT - 50, 50, 50), 3)

        # Отображение режима
        font = pygame.font.SysFont(None, 30)
        mode_text = font.render("BUILD MODE" if self.mode == BUILD_MODE else "ATTACK MODE", True, BLACK)
        surface.blit(mode_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50))

        # Отображение ресурсов
        res_text = font.render(f"Gold: {self.resources['gold']} Elixir: {self.resources['elixir']}", True, BLACK)
        surface.blit(res_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50))

        pygame.display.flip()


# Основной игровой цикл
def main():
    game = Game()
    last_time = pygame.time.get_ticks()

    while True:
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - last_time) / 1000.0  # В секундах
        last_time = current_time

        game.handle_events()
        game.update(delta_time)
        game.draw(screen)
        clock.tick(60)


if __name__ == "__main__":
    main()
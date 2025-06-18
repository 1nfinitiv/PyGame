import pygame
import math
from constants import GRID_SIZE, RED, GREEN, YELLOW
from enum import Enum

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

            title = self.font.render("Clash of Berserk", True, WHITE)
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

                status_text = self.small_font.render(f"Нажмите F чтобы востановить (50g)", True, BLUE)
                self.screen.blit(status_text, (self.selected_barracks.x, self.selected_barracks.y - 30))

            if self.selected_mine:
                pygame.draw.rect(self.screen, YELLOW,
                                 (self.selected_mine.x - 2, self.selected_mine.y - 2,
                                  self.selected_mine.width * GRID_SIZE + 4,
                                  self.selected_mine.height * GRID_SIZE + 4), 2)

                if self.selected_mine.health <= 0:
                    status_text = self.small_font.render(f"Нажмите R чтобы востановить (75g)", True, YELLOW)
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
            win_text = self.font.render("Победа!", True, GREEN)
            self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                                        SCREEN_HEIGHT // 2 - win_text.get_height() // 2))

        elif self.state == GameState.LOSE:
            self.screen.blit(textures['background'], (0, 0))
            lose_text = self.font.render("Поражение!", True, RED)
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
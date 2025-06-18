import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE


class AssetsManager:
    def __init__(self):
        self.textures = {}
        self.music_loaded = False

    def load_assets(self):
        # Load textures
        self.textures['background'] = self.load_texture('texture/grass.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.textures['menu_background'] = self.load_texture('texture/menu_bg.jpg', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.textures['town_hall'] = self.load_texture('texture/house1.png', (GRID_SIZE * 2, GRID_SIZE * 2))
        self.textures['barracks'] = self.load_texture('texture/barracks.png', (GRID_SIZE * 2, GRID_SIZE * 2))
        self.textures['gold_mine'] = self.load_texture('texture/Gold_Mine.png', (GRID_SIZE, GRID_SIZE))
        self.textures['wall'] = self.load_texture('texture/Wall.png', (GRID_SIZE, GRID_SIZE))
        self.textures['wall_broken'] = self.load_texture('texture/wall_broken.png', (GRID_SIZE, GRID_SIZE))
        self.textures['warrior'] = self.load_texture('texture/warrior.png', (30, 30))
        self.textures['archer'] = self.load_texture('texture/archer.png', (30, 30))
        self.textures['giant'] = self.load_texture('texture/giant.png', (50, 50))
        self.textures['warrior_enemy'] = self.load_texture('texture/warrior_enemy.png', (30, 30))
        self.textures['archer_enemy'] = self.load_texture('texture/archer_enemy.png', (30, 30))
        self.textures['giant_enemy'] = self.load_texture('texture/giant.png', (50, 50))

        # Load music
        try:
            pygame.mixer.music.load('music/Linkin_Park_-_Somewhere_I_Belong.mp3')
            self.music_loaded = True
        except:
            print("Failed to load music")
            self.music_loaded = False

    def load_texture(self, path, size=None):
        texture = pygame.image.load(path)
        if size:
            texture = pygame.transform.scale(texture, size)
        return texture
import os
import sys
import json
import math
import random

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

SAVE_PATH = 'data/save.json'

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('ninja game')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)

        self.clouds = Clouds(self.assets['clouds'], count=16)

        self.player = Player(self, (50, 50), (8, 15))

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        self.num_levels = len(os.listdir('data/maps'))
        self.screenshake = 0

        # Save system
        self.cleared_maps = self.load_save()

        # State machine: 'menu', 'level_select', 'game'
        self.state = 'menu'
        self.menu_timer = 0
        self.selected_level = 0

        # Fonts
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 16)

    def load_save(self):
        try:
            with open(SAVE_PATH, 'r') as f:
                data = json.load(f)
                return set(data.get('cleared', []))
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return set()

    def save_progress(self):
        with open(SAVE_PATH, 'w') as f:
            json.dump({'cleared': list(self.cleared_maps)}, f)

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        self.movement = [False, False]
        self.player.velocity = [0, 0]
        self.player.dashing = 0

    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while True:
            if self.state == 'menu':
                self.run_menu()
            elif self.state == 'level_select':
                self.run_level_select()
            elif self.state == 'game':
                self.run_game()

            pygame.display.update()
            self.clock.tick(60)

    def run_menu(self):
        self.menu_timer += 1

        self.display_2.blit(self.assets['background'], (0, 0))

        self.clouds.update()
        self.clouds.render(self.display_2, offset=(0, 0))

        # Title
        title_surf = self.font_large.render('NINJA GAME', True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(160, 80))

        # Title shadow
        shadow_surf = self.font_large.render('NINJA GAME', True, (40, 40, 40))
        self.display_2.blit(shadow_surf, (title_rect.x + 2, title_rect.y + 2))
        self.display_2.blit(title_surf, title_rect)

        # Pulsing "Press ENTER to Start"
        alpha = int(155 + 100 * math.sin(self.menu_timer * 0.05))
        start_surf = self.font_medium.render('Press ENTER to Start', True, (255, 255, 255))
        start_alpha_surf = pygame.Surface(start_surf.get_size(), pygame.SRCALPHA)
        start_alpha_surf.fill((255, 255, 255, alpha))
        start_surf.set_alpha(alpha)
        start_rect = start_surf.get_rect(center=(160, 150))
        self.display_2.blit(start_surf, start_rect)

        # Controls hint
        controls_surf = self.font_small.render('Arrows: Move/Jump  X: Dash  ESC: Back', True, (180, 180, 180))
        controls_rect = controls_surf.get_rect(center=(160, 210))
        self.display_2.blit(controls_surf, controls_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = 'level_select'
                    self.selected_level = 0

        self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), (0, 0))

    def run_level_select(self):
        self.display_2.blit(self.assets['background'], (0, 0))

        self.clouds.update()
        self.clouds.render(self.display_2, offset=(0, 0))

        # Header
        header_surf = self.font_large.render('SELECT LEVEL', True, (255, 255, 255))
        header_rect = header_surf.get_rect(center=(160, 40))
        shadow_surf = self.font_large.render('SELECT LEVEL', True, (40, 40, 40))
        self.display_2.blit(shadow_surf, (header_rect.x + 2, header_rect.y + 2))
        self.display_2.blit(header_surf, header_rect)

        # Level entries
        for i in range(self.num_levels):
            y = 90 + i * 35
            is_selected = (i == self.selected_level)
            is_cleared = (i in self.cleared_maps)

            # Highlight bar for selected level
            if is_selected:
                highlight = pygame.Surface((200, 26), pygame.SRCALPHA)
                highlight.fill((255, 255, 255, 40))
                self.display_2.blit(highlight, (60, y - 5))

            # Level name
            color = (255, 255, 100) if is_selected else (255, 255, 255)
            label = f'Map {i + 1}'

            # Arrow indicator
            if is_selected:
                arrow_surf = self.font_medium.render('>', True, (255, 255, 100))
                self.display_2.blit(arrow_surf, (65, y))

            level_surf = self.font_medium.render(label, True, color)
            self.display_2.blit(level_surf, (80, y))

            # Cleared status
            if is_cleared:
                cleared_surf = self.font_small.render('CLEARED', True, (100, 255, 100))
                self.display_2.blit(cleared_surf, (160, y + 2))

        # Navigation hint
        hint_surf = self.font_small.render('UP/DOWN: Select  ENTER: Play  ESC: Back', True, (180, 180, 180))
        hint_rect = hint_surf.get_rect(center=(160, 215))
        self.display_2.blit(hint_surf, hint_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_level = (self.selected_level - 1) % self.num_levels
                elif event.key == pygame.K_DOWN:
                    self.selected_level = (self.selected_level + 1) % self.num_levels
                elif event.key == pygame.K_RETURN:
                    self.level = self.selected_level
                    self.load_level(self.level)
                    self.state = 'game'
                elif event.key == pygame.K_ESCAPE:
                    self.state = 'menu'

        self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), (0, 0))

    def run_game(self):
        self.display.fill((0, 0, 0, 0))
        self.display_2.blit(self.assets['background'], (0, 0))

        self.screenshake = max(0, self.screenshake - 1)

        if not len(self.enemies):
            self.transition += 1
            if self.transition > 30:
                # Mark map as cleared and save
                self.cleared_maps.add(self.level)
                self.save_progress()
                # Check if all maps are cleared
                if len(self.cleared_maps) >= self.num_levels:
                    self.state = 'menu'
                    return
                else:
                    self.state = 'level_select'
                    return
        if self.transition < 0:
            self.transition += 1

        if self.dead:
            self.dead += 1
            if self.dead >= 10:
                self.transition = min(30, self.transition + 1)
            if self.dead > 40:
                self.load_level(self.level)

        self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
        self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

        for rect in self.leaf_spawners:
            if random.random() * 49999 < rect.width * rect.height:
                pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

        self.clouds.update()
        self.clouds.render(self.display_2, offset=render_scroll)

        self.tilemap.render(self.display, offset=render_scroll)

        for enemy in self.enemies.copy():
            kill = enemy.update(self.tilemap, (0, 0))
            enemy.render(self.display, offset=render_scroll)
            if kill:
                self.enemies.remove(enemy)

        if not self.dead:
            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.display, offset=render_scroll)

        # [[x, y], direction, timer]
        for projectile in self.projectiles.copy():
            projectile[0][0] += projectile[1]
            projectile[2] += 1
            img = self.assets['projectile']
            self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
            if self.tilemap.solid_check(projectile[0]):
                self.projectiles.remove(projectile)
                for i in range(4):
                    self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
            elif projectile[2] > 360:
                self.projectiles.remove(projectile)
            elif abs(self.player.dashing) < 50:
                if self.player.rect().collidepoint(projectile[0]):
                    self.projectiles.remove(projectile)
                    self.dead += 1
                    self.sfx['hit'].play()
                    self.screenshake = max(16, self.screenshake)
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                        self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

        for spark in self.sparks.copy():
            kill = spark.update()
            spark.render(self.display, offset=render_scroll)
            if kill:
                self.sparks.remove(spark)

        display_mask = pygame.mask.from_surface(self.display)
        display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.display_2.blit(display_sillhouette, offset)

        for particle in self.particles.copy():
            kill = particle.update()
            particle.render(self.display, offset=render_scroll)
            if particle.type == 'leaf':
                particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
            if kill:
                self.particles.remove(particle)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.movement[0] = True
                if event.key == pygame.K_RIGHT:
                    self.movement[1] = True
                if event.key == pygame.K_UP:
                    if self.player.jump():
                        self.sfx['jump'].play()
                if event.key == pygame.K_x:
                    self.player.dash()
                if event.key == pygame.K_ESCAPE:
                    self.state = 'level_select'
                    return
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.movement[0] = False
                if event.key == pygame.K_RIGHT:
                    self.movement[1] = False

        if self.transition:
            transition_surf = pygame.Surface(self.display.get_size())
            pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
            transition_surf.set_colorkey((255, 255, 255))
            self.display.blit(transition_surf, (0, 0))

        self.display_2.blit(self.display, (0, 0))

        screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
        self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)

Game().run()

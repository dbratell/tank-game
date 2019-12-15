#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import random

import pygame

GAME_SIZE = (600, 400)
GAME_NAME = "Tanks"
TEAM_1 = "Team 1"
TEAM_2 = "Team 2"
TEAM_COLORS = {
    TEAM_1: (255, 0, 0),
    TEAM_2: (0, 0, 255)
}
GAME_COLOR = (0, 0, 0)
BLOCK_COLOR = (70, 70, 70)
TANK_SIZE = (60, 40)
BULLET_COLOR = (200, 200, 255)
BULLET_SPEED = 80  # 80 pixels per second
BULLET_SIZE = (2, 2)
HULL_LINE_WIDTH = 2
TURRET_SIZE = (20, 20)
GUN_SIZE = (34, 4)
FPS = 60

SPAWN_BULLET_EVENT = pygame.USEREVENT + 1

def rotate_square_surface(surface, rotation):
    # Using rotozoom instead of rotate because rotozoom does antialias,
    # rotate doesn't.
    # This will grow the surface. Need to find the original image's position
    # inside.
    surface_size = surface.get_size()
    assert surface_size[0] == surface_size[1]
    rotated_surface = pygame.transform.rotozoom(surface, rotation, 1)
    rotated_size = rotated_surface.get_size()
    rotation_growth = rotated_size[0] - surface_size[0]
    clipped_rotated_surface = rotated_surface.subsurface(
        rotated_surface.get_rect().inflate(-rotation_growth,
                                           -rotation_growth))
    return clipped_rotated_surface

class Block(pygame.sprite.Sprite):
    def __init__(self, position_and_size):
        pygame.sprite.Sprite.__init__(self)
#        self.position_and_size = position_and_size
        self.image = pygame.Surface(position_and_size.size)
        self.image.fill(BLOCK_COLOR)
        self.rect = position_and_size

    # def draw(self, screen):
    #      pygame.draw.rect(screen,
    #                       BLOCK_COLOR,
    #                       pygame.Rect(self.position_and_size))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, position, rotation):
        pygame.sprite.Sprite.__init__(self)
        self.position = position
        self.rect = pygame.Rect(self.position, BULLET_SIZE)
        self.image = pygame.Surface(self.rect.size)
        self.image.fill(BULLET_COLOR)
        self.rotation = rotation  # degrees, 0 is straight to the
                                  # right, counter-clockwise

    def update_position(self):
        cos_angle = math.cos(self.rotation / 360 * 2 * math.pi)
        sin_angle = math.sin(self.rotation / 360 * 2 * math.pi)
        speed_x = cos_angle * BULLET_SPEED
        speed_y = -sin_angle * BULLET_SPEED

        new_pos = (self.position[0] + speed_x / FPS,
                   self.position[1] + speed_y / FPS)
        self.rect = pygame.Rect(new_pos, BULLET_SIZE)
        self.position = new_pos
        if not pygame.Rect((0, 0), GAME_SIZE).collidepoint(new_pos):
            self.kill()


class Tank(pygame.sprite.Sprite):
    def __init__(self, team):
        pygame.sprite.Sprite.__init__(self)
        self.team = team
        self.pos = (100, 390)  # Center of the tank
        self.rotation = -15
        self.turret_rotation = 30
        self.speed = 30  # 30 pixels per second

    def draw(self, screen):
        # # Hull
        # pygame.draw.rect(screen,
        #                  (0, 255, 0),
        #                  pygame.Rect(self.pos, TANK_SIZE),
        #                  2)

        # Tank
        max_radius = max(math.sqrt((TANK_SIZE[0] / 2) ** 2 +
                                   (TANK_SIZE[1] / 2) ** 2),
                         math.sqrt((GUN_SIZE[0] / 2) ** 2 +
                                   (GUN_SIZE[1] / 2) ** 2))
        tank_image_size = (max_radius * 2, max_radius * 2)
        tank_image = pygame.Surface(tank_image_size, pygame.SRCALPHA)

        hull_pos_in_image = (tank_image_size[0] / 2 - TANK_SIZE[0] / 2,
                             tank_image_size[1] / 2 - TANK_SIZE[1] / 2)
        hull_rect_with_room_for_external_border = pygame.Rect(
            hull_pos_in_image, TANK_SIZE
        ).inflate(-HULL_LINE_WIDTH * 2,
                  -HULL_LINE_WIDTH * 2)
        pygame.draw.rect(tank_image,
                         TEAM_COLORS[self.team],
                         hull_rect_with_room_for_external_border,
                         HULL_LINE_WIDTH)

        turret_image_size = (GUN_SIZE[0] * 2, GUN_SIZE[0] * 2)
        turret = pygame.Surface(turret_image_size,
                                pygame.SRCALPHA)
        # Turret
        pygame.draw.rect(turret,
                         TEAM_COLORS[self.team],
                         pygame.Rect(
                             (turret_image_size[0] / 2 - TURRET_SIZE[0] / 2,
                              turret_image_size[1] / 2 - TURRET_SIZE[1] / 2),
                             TURRET_SIZE))

        # Gun
        pygame.draw.rect(turret,
                         TEAM_COLORS[self.team],
                         pygame.Rect(
                             turret_image_size[0] / 2,
                             turret_image_size[1] / 2 - GUN_SIZE[1] / 2,
                             GUN_SIZE[0],
                             GUN_SIZE[1]))
        rotated_turret = rotate_square_surface(turret, self.turret_rotation)
        tank_image.blit(
            rotated_turret,
            (tank_image_size[0] / 2 - turret_image_size[0] / 2,
             tank_image_size[1] / 2 - turret_image_size[1] / 2))

        rotated_tank = rotate_square_surface(tank_image, self.rotation)
        screen.blit(
            rotated_tank,
            (self.pos[0] - tank_image_size[0] / 2,
             self.pos[1] - tank_image_size[1] / 2))

    def update_position(self):
        cos_angle = math.cos(self.rotation / 360 * 2 * math.pi)
        sin_angle = math.sin(self.rotation / 360 * 2 * math.pi)
        speed_x = cos_angle * self.speed
        speed_y = -sin_angle * self.speed

        self.pos = (self.pos[0] + speed_x / FPS,
                    self.pos[1] + speed_y / FPS)

        def rotate_point(point):
            rotated_x = point[0] * cos_angle - point[1] * sin_angle
            rotated_y = -(point[0] * sin_angle + point[1] * cos_angle)

            if abs(point[0] ** 2 + point[1] ** 2 -
                   rotated_x ** 2 - rotated_y ** 2) >= 0.001:
                print("Angle", self.rotation)
                print("In", point[0] ** 2 + point[1] ** 2)
                print("Out", rotated_x ** 2 + rotated_y ** 2)
                print(point)
                print(rotated_x, rotated_y)
                print(cos_angle, sin_angle)
                assert False
            return (rotated_x, rotated_y)

        # rotate_point((0, 1))
        # rotate_point((0, -1))
        # rotate_point((1, 0))
        # rotate_point((-1, 0))

        # Check that no hull corners ended up outside the game area.
        for corner in ((-TANK_SIZE[0] / 2, -TANK_SIZE[1] / 2),
                       (TANK_SIZE[0] / 2, -TANK_SIZE[1] / 2),
                       (-TANK_SIZE[0] / 2, TANK_SIZE[1] / 2),
                       (TANK_SIZE[0] / 2, TANK_SIZE[1] / 2)):
            rotated_corner = rotate_point(corner)
            if self.pos[0] + rotated_corner[0] < 0:
                self.pos = (-rotated_corner[0], self.pos[1])
            if self.pos[0] + rotated_corner[0] > GAME_SIZE[0]:
                self.pos = (GAME_SIZE[0] - rotated_corner[0], self.pos[1])
            if self.pos[1] + rotated_corner[1] < 0:
                self.pos = (self.pos[0], -rotated_corner[1])
            if self.pos[1] + rotated_corner[1] > GAME_SIZE[1]:
                self.pos = (self.pos[0], GAME_SIZE[1] - rotated_corner[1])

    def ai(self):
        self.turret_rotation = (self.turret_rotation + 1) % 360
        self.rotation = (self.rotation - 0.3) % 360

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.tanks = []
        self.blocks = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()

        a_tank = Tank(TEAM_1)
        self.tanks.append(a_tank)

        a_block = Block(pygame.Rect(300, 140, 30, 50))
        self.blocks.add(a_block)
        a_block = Block(pygame.Rect(80, 70, 40, 40))
        self.blocks.add(a_block)
        a_block = Block(pygame.Rect(540, 50, 20, 80))
        self.blocks.add(a_block)
        a_block = Block(pygame.Rect(200, 300, 100, 30))
        self.blocks.add(a_block)

        pygame.time.set_timer(SPAWN_BULLET_EVENT, 1000)

        self.run = True
        self.clock = pygame.time.Clock()

    def handle_events(self):
        for event in pygame.event.get():
            print(event)
            if event.type == pygame.QUIT:
                self.run = False
            elif event.type == SPAWN_BULLET_EVENT:
                bullet = Bullet((random.randrange(0, GAME_SIZE[0]),
                                 random.randrange(0, GAME_SIZE[1])),
                                random.randrange(0, 360))
                self.bullets.add(bullet)
                print(len(self.bullets))

    def ai(self):
        for tank in self.tanks:
            tank.ai()

    def update_positions(self):
        for tank in self.tanks:
            tank.update_position()

        for bullet in self.bullets:
            bullet.update_position()

    def draw(self):
        self.screen.fill(GAME_COLOR)

        self.blocks.draw(self.screen)
        self.bullets.draw(self.screen)
        for tank in self.tanks:
            tank.draw(self.screen)

    def handle_collisions(self):
        pygame.sprite.groupcollide(self.blocks,
                                   self.bullets,
                                   False,  # Blocks survive
                                   True,  # Bullets die
                                   None)
                                   

    def mainloop(self):
        while self.run:
            self.handle_events()
            self.ai()
            self.update_positions()
            self.handle_collisions()
            self.draw()
            pygame.display.update()
            self.clock.tick(FPS)

def main():
    pygame.init()
    screen = pygame.display.set_mode(GAME_SIZE)
    pygame.display.set_caption(GAME_NAME)

    game = Game(screen)
    game.mainloop()


if __name__ == "__main__":
    main()

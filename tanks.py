#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math

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
TANK_SIZE = (60, 40)
HULL_LINE_WIDTH = 2
TURRET_SIZE = (20, 20)
GUN_SIZE = (34, 4)
FPS = 60

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


class Tank:
    def __init__(self, team):
        self.team = team
        self.pos = (100, 100)  # Center of the tank
        self.hull_rotation = -15
        self.turret_rotation = 30
        self.speed = 30  # 20 pixels per second

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

        rotated_tank = rotate_square_surface(tank_image, self.hull_rotation)
        screen.blit(
            rotated_tank,
            (self.pos[0] - tank_image_size[0] / 2,
             self.pos[1] - tank_image_size[1] / 2))
        
    def ai(self):
        self.turret_rotation = (self.turret_rotation + 1) % 360
        self.hull_rotation = (self.hull_rotation - 0.3) % 360

        speed_x = math.cos(self.hull_rotation / 360 * 2 * math.pi) * self.speed
        speed_y = -math.sin(self.hull_rotation / 360 * 2 * math.pi) * self.speed

        self.pos = (self.pos[0] + speed_x / FPS,
                    self.pos[1] + speed_y / FPS)

#        self.pos = (min(max(0, self.pos[0] + speed_x / FPS), GAME_SIZE[0]),
#                    min(max(0, self.pos[1] + speed_y / FPS), GAME_SIZE[1]))

        
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.tanks = []

        a_tank = Tank(TEAM_1)
        self.tanks.append(a_tank)
        self.run = True
        self.clock = pygame.time.Clock()

    def handle_events(self):
        for event in pygame.event.get():
            print(event)
            if event.type == pygame.QUIT:
                self.run = False

    def ai(self):
        for tank in self.tanks:
            tank.ai()

    def update_positions(self):
        for tank in self.tanks:
            tank.update_positions()

    def draw(self):
        self.screen.fill(GAME_COLOR)
        for tank in self.tanks:
            tank.draw(self.screen)

    def mainloop(self):
        while self.run:
            self.handle_events()
            self.ai()
            self.update_positions()
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

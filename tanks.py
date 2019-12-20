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
BULLET_SPEED = 120  # 80 pixels per second
BULLET_SIZE = (2, 2)
HULL_LINE_WIDTH = 2
TURRET_SIZE = (20, 20)
GUN_SIZE = (34, 4)
FPS = 60

def darker_color(color):
    return (color[0] // 2, color[1] // 2, color[2] // 2)

def random_position():
    return (random.randrange(0, GAME_SIZE[0]),
            random.randrange(0, GAME_SIZE[1]))

def calc_sin_cos(angle):
    sin_angle = math.sin(angle / 360 * 2 * math.pi)
    cos_angle = math.cos(angle / 360 * 2 * math.pi)
    return (sin_angle, cos_angle)

def rotate_point(point, angle):
    sin_angle, cos_angle = calc_sin_cos(angle)
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

def random_angle():
    return random.randrange(360)

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
        # Without SRCALPHA, mask_from_surface won't do the right thing
        # when presented with a solid filled area.
        self.image = pygame.Surface(position_and_size.size, pygame.SRCALPHA)
        self.image.fill(BLOCK_COLOR)
        self.rect = position_and_size

        # Needed for collision detection
        self.mask = pygame.mask.from_surface(self.image)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, position, rotation):
        pygame.sprite.Sprite.__init__(self)
        self.position = position
        self.rect = pygame.Rect(self.position, BULLET_SIZE)
        # Without SRCALPHA, mask_from_surface won't do the right thing
        # when presented with a solid filled area.
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.image.fill(BULLET_COLOR)
        self.rotation = rotation  # degrees, 0 is straight to the
                                  # right, counter-clockwise

        # Needed for collision detection
        self.mask = pygame.mask.from_surface(self.image)

    def update_position(self):
        sin_angle, cos_angle = calc_sin_cos(self.rotation)
        speed_x = cos_angle * BULLET_SPEED
        speed_y = -sin_angle * BULLET_SPEED

        new_pos = (self.position[0] + speed_x / FPS,
                   self.position[1] + speed_y / FPS)
        self.rect = pygame.Rect(new_pos, BULLET_SIZE)
        self.position = new_pos


class Tank(pygame.sprite.Sprite):
    def __init__(self, team, position=(100, 390), rotation=-15):
        pygame.sprite.Sprite.__init__(self)
        self.team = team
        self.pos = position  # Center of the tank
        self.rotation = rotation  # degrees, 0 is straight to the
                                  # right, counter-clockwise
        self.turret_rotation = 30
        self.turret_turn_ratio = 60  # 60 degrees per second
        self.turret_turn_direction = -1  # Clockwise

        self.max_speed = 30  # 30 pixels per second
        self.throttle_mode = 1  # Full speed ahead

        self.turn_ratio = 18  # 18 degrees per second
        self.turn_direction = 1  # Counter clockwise

        # Used by collision detection
        self.mask = pygame.mask.Mask((0, 0))
        self.rect = pygame.Rect((0, 0), (0, 0))

        # Used to reset position after a collision
        self.prev_pos = self.pos
        self.prev_rotation = self.rotation
        self.prev_turret_rotation = self.rotation

        self.collided = False

    def store_safe_position(self):
        self.prev_rotation = self.rotation
        self.prev_pos = self.pos
        self.prev_turret_rotation = self.turret_rotation

    def restore_safe_position(self):
        self.pos = self.prev_pos
        self.rotation = self.prev_rotation
        self.turret_rotation = self.prev_turret_rotation
        self.image = None
        self.rect = None

    def get_gun_position_and_angle(self):
        gun_length = GUN_SIZE[0]
        angle = self.turret_rotation + self.rotation
        rel_gun_tip = rotate_point((gun_length, 0), angle)

        return (self.pos[0] + rel_gun_tip[0],
                self.pos[1] + rel_gun_tip[1]), angle

    def update_image(self):
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
                         darker_color(TEAM_COLORS[self.team]),
                         hull_rect_with_room_for_external_border)
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

        self.image = rotate_square_surface(tank_image, self.rotation)

        # For collision detection
        self.rect = pygame.Rect(
            (self.pos[0] - tank_image_size[0] / 2,
             self.pos[1] - tank_image_size[1] / 2),
            self.image.get_size())

#        pygame.draw.rect(screen, (0, 255, 0), self.rect, 1)
        self.mask = pygame.mask.from_surface(self.image)
#        olist = self.mask.outline()
#        pygame.draw.lines(screen, (200,150,150),
#                          1, olist)
#        print(olist)



    def draw(self, screen):
        if self.image is None:
            self.update_image()
        tank_image_size = self.image.get_size()
        screen.blit(
            self.image,
            (self.pos[0] - tank_image_size[0] / 2,
             self.pos[1] - tank_image_size[1] / 2))

#        olist = self.mask.outline()
#        pygame.draw.lines(screen, (200,150,150),
#                          1, olist)
#        print(olist)

    def update_position(self):
        sin_angle, cos_angle = calc_sin_cos(self.rotation)
        speed_x = cos_angle * self.max_speed * self.throttle_mode
        speed_y = -sin_angle * self.max_speed * self.throttle_mode

        self.turret_rotation = (
            self.turret_rotation +
            self.turret_turn_direction * self.turret_turn_ratio / FPS) % 360
        self.rotation = (self.rotation +
                         self.turn_direction * self.turn_ratio / FPS) % 360
        self.image = None  # Needs to be updated
        self.rect = None

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
        if self.collided or random.randrange(100 * FPS) < 10:
            self.turn_direction = random.choice((-1, 0, 1))
            print("Turned tank")

        if self.collided or random.randrange(100 * FPS) < 30:
            print("Swinging turret differently")
            self.turret_turn_direction = random.choice(
                (-1, -0.5, 0, 0, 0, 0, 0, 0, 0, 0.5, 1))

        if self.collided:
            print("Dramatically changing throttle")
            self.throttle_mode = random.choice((-0.3, 1))
        elif random.randrange(100 * FPS) < 30:
            print("Changing throttle")
            self.throttle_mode = random.choice(
                (-0.3, 0, 0.3, 0.6, 0.8, 1, 1, 1, 1, 1))


        self.collided = False

        fire_gun = random.randrange(100 * FPS) < 30

        return fire_gun

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.tanks = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()

        a_tank = Tank(TEAM_1)
        self.tanks.add(a_tank)

        for _ in range(3):
            self.tanks.add(Tank(TEAM_2, random_position(), random_angle()))

        for block_rect in (
                (300, 140, 30, 50),
                (80, 70, 40, 40),
                (540, 50, 20, 80),
                (200, 300, 100, 30),
        ):
            self.blocks.add(Block(pygame.Rect(block_rect)))

        self.run = True
        self.clock = pygame.time.Clock()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(event)
                self.run = False
            else:
                print(event)

    def ai(self):
        for tank in self.tanks:
            shoot_gun = tank.ai()
            if shoot_gun:
                gun_pos, gun_angle = tank.get_gun_position_and_angle()
                self.bullets.add(Bullet(gun_pos, gun_angle))


    def update_positions(self):
        for tank in self.tanks:
            tank.update_position()

        for bullet in self.bullets:
            bullet.update_position()
            if not pygame.Rect((0, 0), GAME_SIZE).colliderect(bullet.rect):
                bullet.kill()

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
                                   True)  # Bullets die

        for tank in self.tanks:
            if tank.image is None:
                tank.update_image()

        for tank in self.tanks:
            bullets_hitting = pygame.sprite.spritecollide(
                tank,
                self.bullets,
                True,  # Kill bullets that hit.
                pygame.sprite.collide_mask)
            if bullets_hitting:
                for _ in bullets_hitting:
                    print("Poof")
                tank.kill()
                continue

            blocks_hit = pygame.sprite.spritecollide(
                tank,
                self.blocks,
                False,  # Blocks survive
                pygame.sprite.collide_mask)

            if blocks_hit:
                for block in blocks_hit:
                    tank.restore_safe_position()
                    tank.update_image()
                    tank.collided = True
                    assert not pygame.sprite.collide_mask(tank, block)
    #                print("Ouch")
            else:
                tank.store_safe_position()

            # Nice O(n^2) algorithm
            for other_tank in self.tanks:
                if other_tank is tank:
                    continue
                if pygame.sprite.collide_mask(tank, other_tank):
#                    print("That will leave a dent")
                    pass

    def mainloop(self):
        while self.run:
            self.handle_events()
            self.ai()
            self.update_positions()
            self.draw()
            tanks_before_count = len(self.tanks)
            self.handle_collisions()
            if tanks_before_count > 1:
                if len(self.tanks) <= 1:
                    # No more tanks. Quit in 2 seconds.
                    print("Out of tanks!")
                    if len(self.tanks) == 1:
                        print("Gz survivor")
                    else:
                        print("Draw")
                    pygame.time.set_timer(pygame.QUIT, 2000)
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

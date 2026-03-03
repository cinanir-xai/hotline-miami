"""Map creation and enemy placement."""

from __future__ import annotations

import random

from hotline_miami import config
from hotline_miami.entities.enemy import Enemy
from hotline_miami.world.walls import Wall
from hotline_miami.world.doors import Door


def create_map(walls: list, doors: list, enemies: list) -> dict:
    """Populate walls, doors, and enemies. Returns building bounds."""
    main_x, main_y = 1000, 200
    main_w, main_h = 1200, 1000
    wall_thickness = 28
    door_width = 76
    door_height = 120

    door_n = (main_x + 540, door_width)
    door_s = (main_x + 540, door_width)
    door_w = (main_y + 430, door_height)
    door_e = (main_y + 430, door_height)

    walls.append(Wall(main_x, main_y, door_n[0] - main_x, wall_thickness))
    walls.append(
        Wall(
            door_n[0] + door_n[1],
            main_y,
            main_w - (door_n[0] - main_x) - door_n[1],
            wall_thickness,
        )
    )
    doors.append(Door(door_n[0], main_y, door_n[1], wall_thickness, hinge_left=True))

    walls.append(Wall(main_x, main_y + main_h - wall_thickness, door_s[0] - main_x, wall_thickness))
    walls.append(
        Wall(
            door_s[0] + door_s[1],
            main_y + main_h - wall_thickness,
            main_w - (door_s[0] - main_x) - door_s[1],
            wall_thickness,
        )
    )
    doors.append(
        Door(
            door_s[0],
            main_y + main_h - wall_thickness,
            door_s[1],
            wall_thickness,
            hinge_left=False,
        )
    )

    walls.append(Wall(main_x, main_y, wall_thickness, door_w[0] - main_y))
    walls.append(
        Wall(
            main_x,
            door_w[0] + door_w[1],
            wall_thickness,
            main_h - (door_w[0] - main_y) - door_w[1],
        )
    )
    doors.append(Door(main_x, door_w[0], wall_thickness, door_w[1], hinge_left=True))

    walls.append(
        Wall(main_x + main_w - wall_thickness, main_y, wall_thickness, door_e[0] - main_y)
    )
    walls.append(
        Wall(
            main_x + main_w - wall_thickness,
            door_e[0] + door_e[1],
            wall_thickness,
            main_h - (door_e[0] - main_y) - door_e[1],
        )
    )
    doors.append(
        Door(main_x + main_w - wall_thickness, door_e[0], wall_thickness, door_e[1], hinge_left=False)
    )

    main_building = (main_x, main_y, main_w, main_h)

    walls.append(Wall(main_x + 320, main_y + wall_thickness, wall_thickness, 300))
    walls.append(Wall(main_x + 320, main_y + 520, wall_thickness, 460))
    doors.append(Door(main_x + 320, main_y + 340, wall_thickness, door_height, hinge_left=True))

    walls.append(Wall(main_x + wall_thickness, main_y + 440, 280, wall_thickness))
    walls.append(Wall(main_x + 320 + wall_thickness, main_y + 440, 820, wall_thickness))
    doors.append(Door(main_x + 320, main_y + 440, door_width, wall_thickness, hinge_left=True))

    walls.append(Wall(main_x + 720, main_y + wall_thickness, wall_thickness, 250))
    walls.append(Wall(main_x + 720, main_y + 540, wall_thickness, 430))
    doors.append(Door(main_x + 720, main_y + 310, wall_thickness, door_height, hinge_left=False))

    walls.append(Wall(main_x + 720 + wall_thickness, main_y + 310, 220, wall_thickness))
    doors.append(Door(main_x + 720 + wall_thickness, main_y + 310, door_width, wall_thickness, hinge_left=True))

    doors.append(Door(main_x + 520, main_y + 440, door_width, wall_thickness, hinge_left=False))
    doors.append(Door(main_x + 920, main_y + 440, door_width, wall_thickness, hinge_left=True))

    small_x, small_y = 150, 250
    small_w, small_h = 600, 500

    s_door_n = (small_x + 250, door_width)
    s_door_s = (small_x + 250, door_width)
    s_door_w = (small_y + 200, door_height)
    s_door_e = (small_y + 200, door_height)

    walls.append(Wall(small_x, small_y, s_door_n[0] - small_x, wall_thickness))
    walls.append(
        Wall(
            s_door_n[0] + s_door_n[1],
            small_y,
            small_w - (s_door_n[0] - small_x) - s_door_n[1],
            wall_thickness,
        )
    )
    doors.append(Door(s_door_n[0], small_y, s_door_n[1], wall_thickness, hinge_left=True))

    walls.append(Wall(small_x, small_y + small_h - wall_thickness, s_door_s[0] - small_x, wall_thickness))
    walls.append(
        Wall(
            s_door_s[0] + s_door_s[1],
            small_y + small_h - wall_thickness,
            small_w - (s_door_s[0] - small_x) - s_door_s[1],
            wall_thickness,
        )
    )
    doors.append(
        Door(
            s_door_s[0],
            small_y + small_h - wall_thickness,
            s_door_s[1],
            wall_thickness,
            hinge_left=False,
        )
    )

    walls.append(Wall(small_x, small_y, wall_thickness, s_door_w[0] - small_y))
    walls.append(
        Wall(
            small_x,
            s_door_w[0] + s_door_w[1],
            wall_thickness,
            small_h - (s_door_w[0] - small_y) - s_door_w[1],
        )
    )
    doors.append(Door(small_x, s_door_w[0], wall_thickness, s_door_w[1], hinge_left=True))

    walls.append(
        Wall(small_x + small_w - wall_thickness, small_y, wall_thickness, s_door_e[0] - small_y)
    )
    walls.append(
        Wall(
            small_x + small_w - wall_thickness,
            s_door_e[0] + s_door_e[1],
            wall_thickness,
            small_h - (s_door_e[0] - small_y) - s_door_e[1],
        )
    )
    doors.append(
        Door(
            small_x + small_w - wall_thickness,
            s_door_e[0],
            wall_thickness,
            s_door_e[1],
            hinge_left=False,
        )
    )

    small_building = (small_x, small_y, small_w, small_h)

    walls.append(Wall(small_x + wall_thickness, small_y + 250, 240, wall_thickness))
    walls.append(Wall(small_x + 350, small_y + 250, 210, wall_thickness))
    doors.append(Door(small_x + 270, small_y + 250, door_width, wall_thickness, hinge_left=True))

    for pos in [
        (main_x + 120, main_y + 120),
        (main_x + 420, main_y + 140),
        (main_x + 680, main_y + 200),
        (main_x + 980, main_y + 200),
        (main_x + 300, main_y + 700),
        (main_x + 520, main_y + 800),
        (main_x + 840, main_y + 700),
        (main_x + 1050, main_y + 520),
        (main_x + 200, main_y + 900),
        (main_x + 900, main_y + 900),
    ]:
        enemy = Enemy(*pos)
        roll = random.random()
        if roll < config.PIPE_SPAWN_CHANCE:
            enemy.has_pipe = True
            enemy.pipe_durability = config.PIPE_DURABILITY
        elif roll < config.PIPE_SPAWN_CHANCE + config.BAT_SPAWN_CHANCE:
            enemy.has_bat = True
            enemy.bat_durability = config.BAT_DURABILITY
        enemies.append(enemy)

    for pos in [
        (small_x + 120, small_y + 120),
        (small_x + 400, small_y + 120),
        (small_x + 200, small_y + 360),
        (small_x + 460, small_y + 380),
    ]:
        enemy = Enemy(*pos)
        roll = random.random()
        if roll < config.PIPE_SPAWN_CHANCE:
            enemy.has_pipe = True
            enemy.pipe_durability = config.PIPE_DURABILITY
        elif roll < config.PIPE_SPAWN_CHANCE + config.BAT_SPAWN_CHANCE:
            enemy.has_bat = True
            enemy.bat_durability = config.BAT_DURABILITY
        enemies.append(enemy)

    for pos in [(700, 900), (900, 1050), (600, 450), (800, 300)]:
        enemy = Enemy(*pos)
        roll = random.random()
        if roll < config.PIPE_SPAWN_CHANCE:
            enemy.has_pipe = True
            enemy.pipe_durability = config.PIPE_DURABILITY
        elif roll < config.PIPE_SPAWN_CHANCE + config.BAT_SPAWN_CHANCE:
            enemy.has_bat = True
            enemy.bat_durability = config.BAT_DURABILITY
        enemies.append(enemy)

    return {"main": main_building, "small": small_building}

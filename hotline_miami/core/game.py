"""Main game loop and state management."""

from __future__ import annotations

import math
import random
import pygame

from hotline_miami import config
from hotline_miami.core.math_utils import angle_difference
from hotline_miami.effects.weapon_break import BatBreakPiece
from hotline_miami.entities.corpse import Corpse
from hotline_miami.entities.enemy import Enemy
from hotline_miami.entities.player import Player
from hotline_miami.items.weapons import BatItem, BatProjectile, BulletProjectile, PistolItem
from hotline_miami.rendering.environment import draw_building_floors, draw_dirt_ground
from hotline_miami.world.doors import Door
from hotline_miami.world.map_loader import create_map
from hotline_miami.world.walls import Wall


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Hotline Miami - Basic")
        self.clock = pygame.time.Clock()
        self.running = True

        self.reset_game()

    def reset_game(self) -> None:
        self.player = Player(300, 900)
        self.enemies = []
        self.walls = []
        self.doors = []
        self.props = []
        self.corpses = []
        self.boss_enemy = None
        self.bat_items = []
        self.pistol_items = []
        self.bat_projectiles = []
        self.bullet_projectiles = []
        self.bat_breaks = []
        self.player_has_bat = False
        self.player_has_pipe = False
        self.player_has_pistol = False
        self.player_bat_durability = config.BAT_DURABILITY
        self.player_pipe_durability = config.PIPE_DURABILITY
        self.player_pistol_ammo = config.PISTOL_AMMO
        self.player_pistol_cooldown = 0.0
        self.player_pistol_firing = False
        self.throw_charge = 0.0
        self.throw_charging = False
        self.throw_cooldown = 0.0
        self.camera_offset = pygame.Vector2(0, 0)
        self.impact_flashes = []
        random.seed()
        buildings = create_map(self.walls, self.doors, self.enemies, self.props)
        self.main_building = buildings["main"]
        self.small_building = buildings["small"]
        self.large_building = buildings["large"]
        self.boss_arena = buildings["arena"]
        boss_spawn = buildings["boss_spawn"]
        self.boss_enemy = Enemy(boss_spawn[0], boss_spawn[1], is_boss=True)
        self.boss_enemy.has_smg = True
        self.enemies.append(self.boss_enemy)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.player_attack()
                elif event.button == 3:
                    if self.player_has_bat or self.player_has_pipe or self.player_has_pistol:
                        if self.throw_cooldown <= 0:
                            self.throw_charging = True
                            self.throw_charge = 0.0
                    else:
                        self.try_pickup_weapon()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    if self.throw_charging:
                        self.throw_charging = False
                        if self.player_has_bat or self.player_has_pipe:
                            if self.throw_charge >= config.BAT_THROW_CHARGE and self.throw_cooldown <= 0:
                                self.throw_weapon()
                                self.throw_cooldown = config.WEAPON_THROW_COOLDOWN
                        elif self.player_has_pistol:
                            if self.throw_charge >= config.PISTOL_THROW_CHARGE and self.throw_cooldown <= 0:
                                self.throw_weapon()
                                self.throw_cooldown = config.WEAPON_THROW_COOLDOWN
                        else:
                            self.try_pickup_weapon()

    def player_attack(self) -> None:
        if self.player_has_pistol:
            self.player_shoot()
            return
        self.player_punch()

    def player_punch(self) -> None:
        if self.player.punch(self.player_has_bat or self.player_has_pipe):
            px, py = self.player.get_punch_hitbox()
            punch_angle = self.player.facing_angle

            has_weapon = self.player_has_bat or self.player_has_pipe
            if has_weapon:
                self.apply_weapon_attack(self.player.x, self.player.y, punch_angle, source_is_player=True)
                for door in self.doors:
                    if door.is_open:
                        continue
                    door_center = pygame.Vector2(door.x + door.width / 2, door.y + door.height / 2)
                    to_door = door_center - pygame.Vector2(self.player.x, self.player.y)
                    if to_door.length() > config.DOOR_PUNCH_RANGE:
                        continue
                    door_angle = math.atan2(to_door.y, to_door.x)
                    if abs(angle_difference(door_angle, punch_angle)) > config.DOOR_PUNCH_ANGLE / 2:
                        continue
                    door.force_open()
                    break
                return

            for enemy in self.enemies:
                if enemy.alive:
                    dx = enemy.x - px
                    dy = enemy.y - py
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < enemy.radius + 15:
                        enemy.hp -= 1
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.corpses.append(Corpse(enemy.x, enemy.y, enemy.radius, is_boss=enemy.is_boss))
                            drop_offset = pygame.Vector2(random.uniform(-16, 16), random.uniform(-16, 16))
                            self.drop_enemy_weapons(enemy, drop_offset)

            for door in self.doors:
                if door.is_open:
                    continue
                door_center = pygame.Vector2(door.x + door.width / 2, door.y + door.height / 2)
                to_door = door_center - pygame.Vector2(self.player.x, self.player.y)
                if to_door.length() > config.DOOR_PUNCH_RANGE:
                    continue
                door_angle = math.atan2(to_door.y, to_door.x)
                if abs(angle_difference(door_angle, punch_angle)) > config.DOOR_PUNCH_ANGLE / 2:
                    continue
                door.force_open()

                for target in [self.player] + [e for e in self.enemies if e.alive]:
                    if not target.alive:
                        continue
                    vec = pygame.Vector2(target.x, target.y) - door_center
                    if vec.length() > config.DOOR_PUNCH_RANGE:
                        continue
                    target_angle = math.atan2(vec.y, vec.x)
                    if abs(angle_difference(target_angle, door_angle)) <= config.DOOR_PUNCH_ANGLE / 2:
                        target.hp -= config.DOOR_PUNCH_DAMAGE
                        if target.hp <= 0 and target.alive:
                            target.alive = False
                            is_player = isinstance(target, Player)
                            self.corpses.append(Corpse(target.x, target.y, target.radius, is_player))
                break

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.camera_offset.x = max(
            0,
            min(self.player.x - config.SCREEN_WIDTH / 2, config.WORLD_WIDTH - config.SCREEN_WIDTH),
        )
        self.camera_offset.y = max(
            0,
            min(self.player.y - config.SCREEN_HEIGHT / 2, config.WORLD_HEIGHT - config.SCREEN_HEIGHT),
        )
        mouse_pos = pygame.mouse.get_pos()
        world_mouse = (mouse_pos[0] + self.camera_offset.x, mouse_pos[1] + self.camera_offset.y)

        self.player.update(dt, keys, world_mouse)
        self.player.move(dt, self.walls, self.doors, self.props)
        if self.player_pistol_cooldown > 0:
            self.player_pistol_cooldown -= dt
        self.player_pistol_firing = False

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            dist = math.hypot(dx, dy)
            min_dist = self.player.radius + enemy.radius
            if dist > 0 and dist < min_dist:
                push = (min_dist - dist) / 2
                nx = dx / dist
                ny = dy / dist
                self.player.x += nx * push
                self.player.y += ny * push
                enemy.x -= nx * push
                enemy.y -= ny * push

        self.player.x = max(self.player.radius, min(config.WORLD_WIDTH - self.player.radius, self.player.x))
        self.player.y = max(self.player.radius, min(config.WORLD_HEIGHT - self.player.radius, self.player.y))

        if self.throw_cooldown > 0:
            self.throw_cooldown -= dt
        if self.throw_charging:
            self.throw_charge += dt

        for projectile in list(self.bat_projectiles):
            projectile.update(dt, self.walls, self.doors)
            if not projectile.alive:
                if projectile.durability > 0:
                    self.bat_items.append(
                        BatItem(projectile.x, projectile.y, projectile.durability, is_pipe=projectile.is_pipe)
                    )
                else:
                    self.spawn_bat_break(projectile.x, projectile.y)
                self.bat_projectiles.remove(projectile)
                continue
            for enemy in self.enemies:
                if enemy.alive:
                    dist = math.hypot(enemy.x - projectile.x, enemy.y - projectile.y)
                    if dist <= enemy.radius + 8:
                        damage = config.PIPE_DAMAGE if projectile.is_pipe else config.BAT_DAMAGE
                        enemy.hp -= damage
                        projectile.durability -= 1
                        projectile.alive = False
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.corpses.append(Corpse(enemy.x, enemy.y, enemy.radius, is_boss=enemy.is_boss))
                            drop_offset = pygame.Vector2(random.uniform(-16, 16), random.uniform(-16, 16))
                            self.drop_enemy_weapons(enemy, drop_offset)
                        if projectile.durability <= 0:
                            self.spawn_bat_break(projectile.x, projectile.y)
                        break

        for bullet in list(self.bullet_projectiles):
            bullet.update(dt, self.walls, self.doors)
            if not bullet.alive:
                self.bullet_projectiles.remove(bullet)
                continue
            if bullet.source_is_player:
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                    dist = math.hypot(enemy.x - bullet.x, enemy.y - bullet.y)
                    if dist <= enemy.radius + 6:
                        enemy.hp -= config.PISTOL_DAMAGE
                        bullet.alive = False
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.corpses.append(Corpse(enemy.x, enemy.y, enemy.radius, is_boss=enemy.is_boss))
                            drop_offset = pygame.Vector2(random.uniform(-16, 16), random.uniform(-16, 16))
                            self.drop_enemy_weapons(enemy, drop_offset)
                        break
            else:
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                    if bullet.owner_id is not None and id(enemy) == bullet.owner_id:
                        continue
                    dist = math.hypot(enemy.x - bullet.x, enemy.y - bullet.y)
                    if dist <= enemy.radius + 6:
                        enemy.hp -= config.PISTOL_DAMAGE
                        bullet.alive = False
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.corpses.append(Corpse(enemy.x, enemy.y, enemy.radius, is_boss=enemy.is_boss))
                            drop_offset = pygame.Vector2(random.uniform(-16, 16), random.uniform(-16, 16))
                            self.drop_enemy_weapons(enemy, drop_offset)
                        break
                if bullet.alive:
                    dist = math.hypot(self.player.x - bullet.x, self.player.y - bullet.y)
                    if dist <= self.player.radius + 6:
                        self.player.hp -= config.PISTOL_DAMAGE
                        self.impact_flashes.append(config.BAT_IMPACT_FLASH)
                        bullet.alive = False
                        if self.player.hp <= 0 and self.player.alive:
                            self.player.alive = False
                            self.corpses.append(Corpse(self.player.x, self.player.y, self.player.radius, True))

        for piece in list(self.bat_breaks):
            piece.update(dt)
            if piece.life <= 0:
                self.bat_breaks.remove(piece)

        self.impact_flashes = [t - dt for t in self.impact_flashes if t - dt > 0]

        for door in self.doors:
            if door.collides_with_circle(self.player.x, self.player.y, self.player.radius):
                door.push(self.player.x, self.player.y)
            door.update(dt)

        for enemy in self.enemies:
            enemy.update(dt, self.player, self.walls, self.doors)
            enemy.move(dt, self.walls, self.doors, self.props)

            for other in self.enemies:
                if other is enemy or not other.alive or not enemy.alive:
                    continue
                dx = enemy.x - other.x
                dy = enemy.y - other.y
                dist = math.hypot(dx, dy)
                min_dist = enemy.radius + other.radius
                if dist > 0 and dist < min_dist:
                    push = (min_dist - dist) / 2
                    nx = dx / dist
                    ny = dy / dist
                    enemy.x += nx * push
                    enemy.y += ny * push
                    other.x -= nx * push
                    other.y -= ny * push

            if enemy.can_shoot(self.player):
                facing = math.atan2(self.player.y - enemy.y, self.player.x - enemy.x)
                enemy.shoot()
                if enemy.has_pistol:
                    enemy.pistol_ammo -= 1
                self.spawn_bullet(enemy.x, enemy.y, facing, source_is_player=False, owner_id=id(enemy))

            if enemy.can_punch(self.player):
                facing = math.atan2(self.player.y - enemy.y, self.player.x - enemy.x)
                enemy.punch(facing)
                if enemy.has_bat or enemy.has_pipe:
                    self.apply_weapon_attack(enemy.x, enemy.y, facing, source_is_player=False, attacker=enemy)
                else:
                    self.player.hp -= 1
                    self.impact_flashes.append(config.BAT_IMPACT_FLASH)
                if self.player.hp <= 0 and self.player.alive:
                    self.player.alive = False
                    self.corpses.append(Corpse(self.player.x, self.player.y, self.player.radius, True))

    def try_pickup_weapon(self) -> None:
        if self.player_has_bat or self.player_has_pipe or self.player_has_pistol:
            return
        for pistol in list(self.pistol_items):
            dist = math.hypot(pistol.x - self.player.x, pistol.y - self.player.y)
            if dist <= config.PISTOL_PICKUP_RANGE + config.WEAPON_PICKUP_EXTRA:
                self.player_has_pistol = True
                self.player_pistol_ammo = pistol.ammo
                self.pistol_items.remove(pistol)
                return
        for bat in list(self.bat_items):
            dist = math.hypot(bat.x - self.player.x, bat.y - self.player.y)
            if dist <= config.BAT_PICKUP_RANGE + config.WEAPON_PICKUP_EXTRA:
                if bat.is_pipe:
                    self.player_has_pipe = True
                    self.player_pipe_durability = bat.durability
                else:
                    self.player_has_bat = True
                    self.player_bat_durability = bat.durability
                self.bat_items.remove(bat)
                return

    def throw_weapon(self) -> None:
        direction = pygame.Vector2(math.cos(self.player.facing_angle), math.sin(self.player.facing_angle))
        if self.player_has_pistol:
            pistol = PistolItem(self.player.x, self.player.y, self.player_pistol_ammo)
            pistol.x += direction.x * 10
            pistol.y += direction.y * 10
            self.pistol_items.append(pistol)
            self.player_has_pistol = False
            self.player_pistol_ammo = config.PISTOL_AMMO
            return
        if not (self.player_has_bat or self.player_has_pipe):
            return
        is_pipe = self.player_has_pipe
        speed = config.PIPE_THROW_SPEED if is_pipe else config.BAT_THROW_SPEED
        durability = self.player_pipe_durability if is_pipe else self.player_bat_durability
        velocity = direction * speed
        projectile = BatProjectile(self.player.x, self.player.y, velocity, durability, is_pipe=is_pipe)
        self.bat_projectiles.append(projectile)
        self.player_has_bat = False
        self.player_has_pipe = False
        self.player_bat_durability = config.BAT_DURABILITY
        self.player_pipe_durability = config.PIPE_DURABILITY

    def spawn_bat_break(self, x: float, y: float) -> None:
        for _ in range(3):
            self.bat_breaks.append(BatBreakPiece(x, y))

    def spawn_bullet(
        self,
        x: float,
        y: float,
        angle: float,
        source_is_player: bool,
        owner_id: int | None = None,
    ) -> None:
        direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        velocity = direction * config.PISTOL_BULLET_SPEED
        bullet = BulletProjectile(x + direction.x * 8, y + direction.y * 8, velocity, source_is_player, owner_id)
        self.bullet_projectiles.append(bullet)

    def player_shoot(self) -> None:
        if not self.player_has_pistol:
            return
        if self.player_pistol_cooldown > 0:
            return
        if self.player_pistol_ammo <= 0:
            return
        self.player_pistol_cooldown = config.PISTOL_PLAYER_COOLDOWN
        self.player_pistol_firing = True
        self.player_pistol_ammo -= 1
        self.spawn_bullet(self.player.x, self.player.y, self.player.facing_angle, source_is_player=True)

    def drop_enemy_weapons(self, enemy: Enemy, drop_offset: pygame.Vector2) -> None:
        if enemy.has_bat:
            self.bat_items.append(BatItem(enemy.x + drop_offset.x, enemy.y + drop_offset.y, enemy.bat_durability))
            enemy.has_bat = False
        if enemy.has_pipe:
            self.bat_items.append(
                BatItem(
                    enemy.x + drop_offset.x,
                    enemy.y + drop_offset.y,
                    enemy.pipe_durability,
                    is_pipe=True,
                )
            )
            enemy.has_pipe = False
        if enemy.has_pistol:
            self.pistol_items.append(
                PistolItem(enemy.x + drop_offset.x, enemy.y + drop_offset.y, enemy.pistol_ammo)
            )
            enemy.has_pistol = False
        if enemy.has_smg:
            self.pistol_items.append(PistolItem(enemy.x + drop_offset.x, enemy.y + drop_offset.y, ammo=config.SMG_AMMO))
            enemy.has_smg = False

    def apply_weapon_attack(
        self,
        attacker_x: float,
        attacker_y: float,
        facing_angle: float,
        source_is_player: bool,
        attacker: Enemy | None = None,
    ) -> None:
        targets = [self.player] + [e for e in self.enemies if e.alive]
        hit_any = False
        hit_player = False
        is_pipe = False
        if source_is_player:
            is_pipe = self.player_has_pipe
        elif attacker:
            is_pipe = attacker.has_pipe
        damage = config.PIPE_DAMAGE if is_pipe else config.BAT_DAMAGE
        swing_arc = config.PIPE_SWING_ARC if is_pipe else config.BAT_ARC

        for target in targets:
            if not target.alive:
                continue
            if source_is_player and target is self.player:
                continue
            vec = pygame.Vector2(target.x - attacker_x, target.y - attacker_y)
            if vec.length() > config.BAT_RANGE:
                continue
            target_angle = math.atan2(vec.y, vec.x)
            if abs(angle_difference(target_angle, facing_angle)) <= swing_arc / 2:
                target.hp -= damage
                hit_any = True
                if isinstance(target, Player):
                    hit_player = True
                if target.hp <= 0:
                    target.alive = False
                    is_player = isinstance(target, Player)
                    self.corpses.append(Corpse(target.x, target.y, target.radius, is_player, is_boss=isinstance(target, Enemy) and target.is_boss))
                    if isinstance(target, Enemy) and (target.has_bat or target.has_pipe or target.has_smg):
                        drop_offset = pygame.Vector2(random.uniform(-16, 16), random.uniform(-16, 16))
                        if target.has_bat:
                            self.bat_items.append(
                                BatItem(target.x + drop_offset.x, target.y + drop_offset.y, target.bat_durability)
                            )
                            target.has_bat = False
                        if target.has_pipe:
                            self.bat_items.append(
                                BatItem(
                                    target.x + drop_offset.x,
                                    target.y + drop_offset.y,
                                    target.pipe_durability,
                                    is_pipe=True,
                                )
                            )
                            target.has_pipe = False
                        if target.has_smg:
                            self.pistol_items.append(PistolItem(target.x + drop_offset.x, target.y + drop_offset.y, ammo=config.SMG_AMMO))
                            target.has_smg = False
        if hit_player:
            self.impact_flashes.append(config.BAT_IMPACT_FLASH)
        if source_is_player and hit_any:
            if self.player_has_pipe:
                self.player_pipe_durability -= 1
                if self.player_pipe_durability <= 0:
                    self.player_has_pipe = False
                    self.spawn_bat_break(attacker_x, attacker_y)
            elif self.player_has_bat:
                self.player_bat_durability -= 1
                if self.player_bat_durability <= 0:
                    self.player_has_bat = False
                    self.spawn_bat_break(attacker_x, attacker_y)
        elif not source_is_player and attacker and hit_any:
            if attacker.has_pipe:
                attacker.pipe_durability -= 1
                if attacker.pipe_durability <= 0:
                    attacker.has_pipe = False
                    self.spawn_bat_break(attacker_x, attacker_y)
            elif attacker.has_bat:
                attacker.bat_durability -= 1
                if attacker.bat_durability <= 0:
                    attacker.has_bat = False
                    self.spawn_bat_break(attacker_x, attacker_y)

    def draw(self) -> None:
        self.screen.fill(config.BLACK)

        self.camera_offset.x = max(
            0,
            min(self.player.x - config.SCREEN_WIDTH / 2, config.WORLD_WIDTH - config.SCREEN_WIDTH),
        )
        self.camera_offset.y = max(
            0,
            min(self.player.y - config.SCREEN_HEIGHT / 2, config.WORLD_HEIGHT - config.SCREEN_HEIGHT),
        )

        draw_dirt_ground(self.screen, self.camera_offset)
        draw_building_floors(
            self.screen,
            self.camera_offset,
            self.main_building,
            self.small_building,
            self.large_building,
            self.boss_arena,
        )

        for bat in self.bat_items:
            bat.draw(self.screen, self.camera_offset)
        for pistol in self.pistol_items:
            pistol.draw(self.screen, self.camera_offset)
        for projectile in self.bat_projectiles:
            projectile.draw(self.screen, self.camera_offset)
        for bullet in self.bullet_projectiles:
            bullet.draw(self.screen, self.camera_offset)
        for piece in self.bat_breaks:
            piece.draw(self.screen, self.camera_offset)

        for door in self.doors:
            door.draw(self.screen, self.camera_offset)

        for wall in self.walls:
            wall.draw(self.screen, self.camera_offset)

        for prop in self.props:
            prop.draw(self.screen, self.camera_offset)

        for corpse in self.corpses:
            corpse.draw(self.screen, self.camera_offset)

        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_offset)

        self.player.draw(
            self.screen,
            self.camera_offset,
            self.player_has_bat,
            self.player_has_pipe,
            self.player_has_pistol,
            self.player_pistol_firing,
        )

        font = pygame.font.SysFont(None, 24)
        hp_text = font.render(f"HP: {self.player.hp}/{config.PLAYER_HP}", True, config.WHITE)
        self.screen.blit(hp_text, (10, 10))

        enemy_count = sum(1 for e in self.enemies if e.alive)
        enemy_text = font.render(f"Enemies: {enemy_count}", True, config.WHITE)
        self.screen.blit(enemy_text, (10, 35))

        if self.player_has_pistol:
            pistol_text = font.render(f"Pistol Ammo: {self.player_pistol_ammo}", True, config.WHITE)
            self.screen.blit(pistol_text, (10, 60))
        elif self.player_has_bat:
            bat_text = font.render(f"Bat Durability: {self.player_bat_durability}", True, config.WHITE)
            self.screen.blit(bat_text, (10, 60))
        elif self.player_has_pipe:
            pipe_text = font.render(f"Pipe Durability: {self.player_pipe_durability}", True, config.WHITE)
            self.screen.blit(pipe_text, (10, 60))
        elif self.throw_charging:
            charge_text = font.render("Charging throw...", True, config.WHITE)
            self.screen.blit(charge_text, (10, 60))

        if self.throw_charging and (self.player_has_bat or self.player_has_pipe or self.player_has_pistol):
            charge_duration = config.PISTOL_THROW_CHARGE if self.player_has_pistol else config.BAT_THROW_CHARGE
            charge_pct = min(1.0, self.throw_charge / charge_duration)
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)
            radius = config.WEAPON_CHARGE_RADIUS + 8 * pulse
            center = (int(self.player.x - self.camera_offset.x), int(self.player.y - self.camera_offset.y))
            ring_surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            ring_color = (255, 255, 255, int(120 + 100 * charge_pct))
            pygame.draw.circle(ring_surface, ring_color, (radius + 2, radius + 2), int(radius), 3)
            self.screen.blit(ring_surface, (center[0] - radius - 2, center[1] - radius - 2))

            charge_text = font.render(f"Throw Charge: {int(charge_pct * 100)}%", True, config.WHITE)
            self.screen.blit(charge_text, (10, 85))

        if not self.player.alive:
            over_font = pygame.font.SysFont(None, 72)
            over_text = over_font.render("GAME OVER", True, config.RED)
            rect = over_text.get_rect(center=(config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2))
            self.screen.blit(over_text, rect)

        reset_hint = font.render("Press R to reset", True, config.LIGHT_GRAY)
        self.screen.blit(reset_hint, (10, 130))

        if self.impact_flashes:
            intensity = min(180, int(255 * max(self.impact_flashes)))
            flash = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, intensity))
            self.screen.blit(flash, (0, 0))

        mouse_x, mouse_y = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, config.WHITE, (mouse_x, mouse_y), 6, 1)
        pygame.draw.line(self.screen, config.WHITE, (mouse_x - 10, mouse_y), (mouse_x - 3, mouse_y), 1)
        pygame.draw.line(self.screen, config.WHITE, (mouse_x + 3, mouse_y), (mouse_x + 10, mouse_y), 1)
        pygame.draw.line(self.screen, config.WHITE, (mouse_x, mouse_y - 10), (mouse_x, mouse_y - 3), 1)
        pygame.draw.line(self.screen, config.WHITE, (mouse_x, mouse_y + 3), (mouse_x, mouse_y + 10), 1)

        pygame.display.flip()

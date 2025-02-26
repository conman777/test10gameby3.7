import pygame
import random
import math
from constants import *
from projectiles import HomingMissile, ExplosiveBullet

class Enemy:
    def __init__(self, x, y, enemy_type="basic"):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(x - self.width/2, y - self.height/2, self.width, self.height)
        self.enemy_type = enemy_type
        self.vel_x = 0
        self.vel_y = 0
        self.health = 100
        self.max_health = 100
        self.move_speed = 200
        self.shoot_cooldown = 0
        self.shoot_delay = 1.0
        self.facing_right = True
        self.animation_state = 0
        self.animation_timer = 0
        self.damaged_timer = 0
        self.damage_flash_duration = 0.1
        self.points_value = 100
        self.on_ground = False  # Add the missing on_ground attribute
        
        # Different stats based on enemy type
        if enemy_type == "runner":
            self.move_speed = 300
            self.health = 50
            self.points_value = 75
        elif enemy_type == "tank":
            self.move_speed = 100
            self.health = 200
            self.width = 50
            self.height = 50
            self.points_value = 150
        elif enemy_type == "shooter":
            self.move_speed = 150
            self.health = 75
            self.shoot_delay = 0.75
            self.points_value = 125
    
    def update(self, dt, player, platforms, enemy_bullets):
        # Update damaged timer
        if self.damaged_timer > 0:
            self.damaged_timer -= dt
        
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        
        # Update position based on enemy type
        if self.enemy_type == "runner":
            self.update_runner(dt, player, platforms)
        elif self.enemy_type == "tank":
            self.update_tank(dt, player, platforms)
        elif self.enemy_type == "shooter":
            self.update_shooter(dt, player, platforms, enemy_bullets)
        else:
            self.update_basic(dt, player, platforms)
        
        # Update animation
        self.update_animation(dt)
        
        # Update rectangle position
        self.rect.x = self.x - self.width/2
        self.rect.y = self.y - self.height/2
    
    def update_basic(self, dt, player, platforms):
        # Move towards player with simple AI
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 50:  # Don't get too close
            self.vel_x = (dx/dist) * self.move_speed
            
            # Simple platform navigation
            # Check if there's ground ahead
            ground_check_x = self.x + self.vel_x * dt + (self.width/2 * (1 if self.vel_x > 0 else -1))
            ground_check_rect = pygame.Rect(ground_check_x, self.y + self.height, 5, 50)
            
            has_ground = False
            for platform in platforms:
                if platform.rect.colliderect(ground_check_rect):
                    has_ground = True
                    break
            
            if not has_ground:
                self.vel_x = -self.vel_x
        
        # Apply gravity
        self.vel_y += GRAVITY * dt
        
        # Cap falling speed
        if self.vel_y > 800:
            self.vel_y = 800
        
        # Update position
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Update facing direction
        if self.vel_x > 0:
            self.facing_right = True
        elif self.vel_x < 0:
            self.facing_right = False
        
        # Handle collisions with platforms
        self.handle_platform_collisions(platforms)
    
    def update_runner(self, dt, player, platforms):
        # Faster movement and more aggressive pursuit
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 30:
            self.vel_x = (dx/dist) * self.move_speed
            
            # Jump if near a wall or gap
            ground_check_x = self.x + self.vel_x * dt + (self.width/2 * (1 if self.vel_x > 0 else -1))
            ground_check_rect = pygame.Rect(ground_check_x, self.y + self.height, 5, 50)
            wall_check_rect = pygame.Rect(ground_check_x, self.y, 5, self.height)
            
            should_jump = False
            for platform in platforms:
                if platform.rect.colliderect(wall_check_rect):
                    should_jump = True
                    break
            
            has_ground = False
            for platform in platforms:
                if platform.rect.colliderect(ground_check_rect):
                    has_ground = True
                    break
            
            if should_jump or not has_ground:
                if self.on_ground:
                    self.vel_y = -500  # Jump!
        
        # Rest of physics similar to basic
        self.update_basic(dt, player, platforms)
    
    def update_tank(self, dt, player, platforms):
        # Slower movement but takes more hits
        dx = player.x - self.x
        dist_x = abs(dx)
        
        # Try to maintain optimal distance
        optimal_distance = 200
        if dist_x > optimal_distance + 50:
            self.vel_x = self.move_speed * (1 if dx > 0 else -1)
        elif dist_x < optimal_distance - 50:
            self.vel_x = -self.move_speed * (1 if dx > 0 else -1)
        else:
            self.vel_x = 0
        
        # Rest of physics similar to basic
        self.update_basic(dt, player, platforms)
    
    def update_shooter(self, dt, player, platforms, enemy_bullets):
        # Try to maintain distance and shoot at player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Update facing direction based on player position
        self.facing_right = dx > 0
        
        # Try to maintain optimal shooting distance
        optimal_distance = 300
        if dist > optimal_distance + 50:
            self.vel_x = (dx/dist) * self.move_speed
        elif dist < optimal_distance - 50:
            self.vel_x = -(dx/dist) * self.move_speed
        else:
            self.vel_x = 0
            # Shoot if cooldown is ready
            if self.shoot_cooldown <= 0:
                self.shoot(player, enemy_bullets)
        
        # Rest of physics similar to basic
        self.update_basic(dt, player, platforms)
    
    def handle_platform_collisions(self, platforms):
        # Reset ground status
        self.on_ground = False
        
        # Check each platform
        for platform in platforms:
            if platform.rect.colliderect(self.rect):
                # Get the collision depth on each axis
                dx_left = self.rect.right - platform.rect.left
                dx_right = platform.rect.right - self.rect.left
                dy_top = self.rect.bottom - platform.rect.top
                dy_bottom = platform.rect.bottom - self.rect.top
                
                # Find the shallowest penetration
                min_dx = min(dx_left, dx_right)
                min_dy = min(dy_top, dy_bottom)
                
                if min_dx < min_dy:
                    # Horizontal collision
                    if dx_left < dx_right:
                        self.x = platform.rect.left - self.width/2
                    else:
                        self.x = platform.rect.right + self.width/2
                    self.vel_x = 0
                else:
                    # Vertical collision
                    if dy_top < dy_bottom:
                        self.y = platform.rect.top - self.height/2
                        self.vel_y = 0
                        self.on_ground = True
                    else:
                        self.y = platform.rect.bottom + self.height/2
                        self.vel_y = 0
    
    def update_animation(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 0.1:  # Update every 0.1 seconds
            self.animation_state = (self.animation_state + 1) % 4
            self.animation_timer = 0
    
    def take_damage(self, amount):
        self.health -= amount
        self.damaged_timer = self.damage_flash_duration
        return self.health <= 0
    
    def shoot(self, target, enemy_bullets):
        if self.enemy_type == "shooter":
            # Create a homing missile
            dir_x = target.x - self.x
            dir_y = target.y - self.y
            dist = math.sqrt(dir_x*dir_x + dir_y*dir_y)
            
            missile = HomingMissile(
                self.x,
                self.y,
                (dir_x/dist) * 300,
                (dir_y/dist) * 300,
                (255, 100, 100),
                target
            )
            enemy_bullets.append(missile)
            self.shoot_cooldown = self.shoot_delay
    
    def draw(self, surface):
        # Flash red when damaged
        color = RED if self.damaged_timer > 0 else self.get_color()
        
        # Draw enemy body
        if self.enemy_type == "basic":
            self.draw_basic(surface, color)
        elif self.enemy_type == "runner":
            self.draw_runner(surface, color)
        elif self.enemy_type == "tank":
            self.draw_tank(surface, color)
        elif self.enemy_type == "shooter":
            self.draw_shooter(surface, color)
        
        # Draw health bar
        self.draw_health_bar(surface)
    
    def get_color(self):
        if self.enemy_type == "runner":
            return (200, 50, 50)  # Red
        elif self.enemy_type == "tank":
            return (50, 150, 50)  # Green
        elif self.enemy_type == "shooter":
            return (50, 50, 200)  # Blue
        else:
            return (150, 150, 150)  # Gray
    
    def draw_basic(self, surface, color):
        # Simple square with eyes
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # Eyes
        eye_x = self.x + (10 if self.facing_right else -10)
        pygame.draw.circle(surface, WHITE, (int(eye_x), int(self.y)), 5)
        pygame.draw.circle(surface, BLACK, (int(eye_x + (2 if self.facing_right else -2)), int(self.y)), 2)
    
    def draw_runner(self, surface, color):
        # Triangular shape for speed appearance
        points = [
            (self.x + (self.width/2 if self.facing_right else -self.width/2), self.y),
            (self.x + (-self.width/2 if self.facing_right else self.width/2), self.y - self.height/2),
            (self.x + (-self.width/2 if self.facing_right else self.width/2), self.y + self.height/2)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, BLACK, points, 2)
        
        # Eye
        eye_x = self.x + (10 if self.facing_right else -10)
        pygame.draw.circle(surface, WHITE, (int(eye_x), int(self.y)), 4)
        pygame.draw.circle(surface, BLACK, (int(eye_x + (2 if self.facing_right else -2)), int(self.y)), 2)
    
    def draw_tank(self, surface, color):
        # Heavier, armored appearance
        pygame.draw.rect(surface, color, self.rect)
        
        # Armor plates
        plate_spacing = 10
        for i in range(3):
            plate_y = self.rect.y + i * plate_spacing
            pygame.draw.line(surface, BLACK, 
                           (self.rect.left, plate_y),
                           (self.rect.right, plate_y), 3)
        
        # Viewport
        viewport_width = 20
        viewport_x = self.x + (viewport_width/2 if self.facing_right else -viewport_width/2)
        viewport_rect = pygame.Rect(viewport_x - viewport_width/2, self.y - 5, viewport_width, 10)
        pygame.draw.rect(surface, (200, 0, 0), viewport_rect)
        pygame.draw.rect(surface, BLACK, viewport_rect, 2)
    
    def draw_shooter(self, surface, color):
        # Base body
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # Cannon
        cannon_length = 20
        cannon_x = self.x + (cannon_length if self.facing_right else -cannon_length)
        pygame.draw.line(surface, BLACK,
                        (self.x, self.y),
                        (cannon_x, self.y), 6)
        
        # Energy core
        core_pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 200)
        core_radius = 8 + 2 * core_pulse
        pygame.draw.circle(surface, (100, 100, 255), (int(self.x), int(self.y)), int(core_radius))
    
    def draw_health_bar(self, surface):
        bar_width = 40
        bar_height = 5
        bar_x = self.x - bar_width/2
        bar_y = self.rect.y - 10
        
        # Background
        pygame.draw.rect(surface, (50, 50, 50),
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Health fill
        health_percent = self.health / self.max_health
        if health_percent > 0:
            health_color = GREEN
            if health_percent < 0.5:
                health_color = YELLOW
            if health_percent < 0.25:
                health_color = RED
            
            pygame.draw.rect(surface, health_color,
                           (bar_x, bar_y, bar_width * health_percent, bar_height))
    
    def check_collision(self, entity):
        """Check collision with another entity"""
        return self.rect.colliderect(entity.rect)


class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "boss")
        self.width = 80
        self.height = 80
        self.rect = pygame.Rect(x - self.width/2, y - self.height/2, self.width, self.height)
        self.health = 500
        self.max_health = 500
        self.move_speed = 150
        self.shoot_delay = 2.0
        self.shoot_cooldown = 0
        self.points_value = 1000
        self.phase = 1
        self.total_phases = 3
        self.attack_pattern = 0
        self.attack_timer = 0
        self.shield_active = False
        self.shield_health = 100
        self.shield_max = 100
        self.minions = []
        self.minion_spawn_timer = 0
        self.rage_mode = False
        self.charge_target = None
        self.charge_speed = 500
    
    def update(self, dt, player, platforms, enemy_bullets):
        super().update(dt, player, platforms, enemy_bullets)
        
        # Update attack timer
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.start_new_attack(player)
        
        # Update minion spawn timer
        self.minion_spawn_timer -= dt
        if self.minion_spawn_timer <= 0 and len(self.minions) < 3:
            self.spawn_minion()
        
        # Update shield
        if self.shield_active and self.shield_health <= 0:
            self.shield_active = False
            self.take_damage(50)  # Bonus damage when shield breaks
        
        # Update phase based on health
        current_phase = self.get_current_phase()
        if current_phase != self.phase:
            self.phase = current_phase
            self.on_phase_change()
        
        # Update minions
        for minion in self.minions[:]:
            minion.update(dt, player, platforms, enemy_bullets)
            if minion.health <= 0:
                self.minions.remove(minion)
    
    def get_current_phase(self):
        health_percent = self.health / self.max_health
        if health_percent > 0.66:
            return 1
        elif health_percent > 0.33:
            return 2
        else:
            return 3
    
    def on_phase_change(self):
        # Activate rage mode in final phase
        if self.phase == 3:
            self.rage_mode = True
            self.move_speed = 200
            self.shoot_delay *= 0.7
        
        # Spawn minions and activate shield
        self.shield_active = True
        self.shield_health = self.shield_max
        self.minion_spawn_timer = 0  # Spawn minions immediately
    
    def start_new_attack(self, player):
        self.attack_pattern = (self.attack_pattern + 1) % 3
        
        if self.attack_pattern == 0:
            # Missile barrage
            self.shoot_missile_barrage(player, 5)
            self.attack_timer = 3.0
        elif self.attack_pattern == 1:
            # Charge attack
            self.start_charge_attack(player)
            self.attack_timer = 4.0
        else:
            # Ground pound
            self.start_ground_pound()
            self.attack_timer = 5.0
    
    def shoot_missile_barrage(self, target, count):
        angle_step = math.pi / (count - 1)
        base_angle = math.atan2(target.y - self.y, target.x - self.x)
        
        for i in range(count):
            angle = base_angle - (math.pi/4) + (i * angle_step)
            missile = HomingMissile(
                self.x,
                self.y,
                math.cos(angle) * 300,
                math.sin(angle) * 300,
                (255, 50, 50),
                target
            )
            # Fix: Use the enemy_bullets parameter instead of self.enemy_bullets
            if hasattr(self, 'enemy_bullets'):
                self.enemy_bullets.append(missile)
            else:
                # This will be the parameter from the update method
                from main import enemy_bullets
                enemy_bullets.append(missile)
    
    def start_charge_attack(self, target):
        self.charge_target = target.x
        # Implementation of charge behavior would go in update
    
    def start_ground_pound(self):
        self.vel_y = -400  # Jump up
        # Ground pound behavior would be implemented in update
    
    def spawn_minion(self):
        minion = Enemy(self.x + random.randint(-100, 100),
                      self.y - 50,
                      "shooter" if random.random() < 0.5 else "runner")
        self.minions.append(minion)
        self.minion_spawn_timer = 10.0  # Time until next spawn
    
    def take_damage(self, amount):
        if self.shield_active:
            self.shield_health -= amount
            return False
        else:
            return super().take_damage(amount)
    
    def draw(self, surface):
        # Draw minions
        for minion in self.minions:
            minion.draw(surface)
        
        # Base enemy drawing
        super().draw(surface)
        
        # Draw shield if active
        if self.shield_active:
            shield_radius = max(self.width, self.height) * 0.75
            shield_surface = pygame.Surface((shield_radius*2, shield_radius*2), pygame.SRCALPHA)
            shield_alpha = int(255 * (self.shield_health / self.shield_max))
            pygame.draw.circle(shield_surface, (100, 200, 255, shield_alpha),
                             (shield_radius, shield_radius), shield_radius)
            surface.blit(shield_surface, (self.x - shield_radius, self.y - shield_radius))
        
        # Draw phase indicator
        phase_text = f"Phase {self.phase}"
        font = pygame.font.SysFont('arial', 24)
        text_surface = font.render(phase_text, True, WHITE)
        surface.blit(text_surface, (self.x - text_surface.get_width()/2, self.rect.top - 40))
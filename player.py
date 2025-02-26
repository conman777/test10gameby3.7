import pygame
import math
from constants import *

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.vel_x = 0
        self.vel_y = 0
        self.jump_power = -700
        self.move_speed = 350
        self.gravity = 1500
        self.on_ground = False
        self.health = 100
        self.max_health = 100
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invulnerable_duration = 1.5  # seconds
        self.color = (50, 150, 250)
        self.shape_points = []
        self.update_shape()
        self.double_jump = False
        self.can_double_jump = True
        self.shoot_cooldown = 0
        self.shoot_delay = 0.25
        self.bullet_speed = 800
        self.special_power = None
        self.special_timer = 0
        self.dash_available = True
        self.dash_cooldown = 0
        self.dash_power = 800
        self.dash_duration = 0.15
        self.dashing = False
        self.dash_timer = 0
        self.facing_right = True
        self.animation_state = 0
        self.animation_timer = 0
        self.wall_sliding = False
        self.wall_jump_cooldown = 0
    
    def update_shape(self):
        # Update player shape points based on current position
        self.rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, 
                               self.width, self.height)
        
        # Create a more interesting player shape
        self.shape_points = []
        
        # Main body - torso
        torso_width = self.width * 0.8
        torso_height = self.height * 0.4
        torso_left = self.x - torso_width // 2
        torso_top = self.y - torso_height // 2 - self.height * 0.1
        
        # Head
        head_radius = self.width * 0.35
        head_y = torso_top - head_radius
        
        # Legs
        leg_width = self.width * 0.2
        leg_height = self.height * 0.35
        leg_left_x = self.x - torso_width // 2 + leg_width // 2
        leg_right_x = self.x + torso_width // 2 - leg_width // 2
        leg_top = self.y + self.height * 0.05
        
        # Arms
        arm_width = self.width * 0.2
        arm_height = self.height * 0.3
        arm_left_x = self.x - torso_width // 2 - arm_width // 2
        arm_right_x = self.x + torso_width // 2 + arm_width // 2
        arm_top = self.y - self.height * 0.2
        
        # Store shape info for drawing
        self.shape_info = {
            'torso': (torso_left, torso_top, torso_width, torso_height),
            'head': (self.x, head_y, head_radius),
            'legs': [(leg_left_x, leg_top, leg_width, leg_height),
                    (leg_right_x, leg_top, leg_width, leg_height)],
            'arms': [(arm_left_x, arm_top, arm_width, arm_height),
                    (arm_right_x, arm_top, arm_width, arm_height)]
        }
    
    def update(self, platforms, dt):
        # Handle invulnerability timer
        if self.invulnerable:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
        
        # Handle special power timer
        if self.special_power:
            self.special_timer -= dt
            if self.special_timer <= 0:
                self.deactivate_power()
        
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        
        # Update dash cooldown
        if not self.dash_available and not self.dashing:
            self.dash_cooldown -= dt
            if self.dash_cooldown <= 0:
                self.dash_available = True
        
        # Handle dash state
        if self.dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.dashing = False
                self.vel_x = self.vel_x * 0.3  # Slow down after dash
        
        # Update wall jump cooldown
        if self.wall_jump_cooldown > 0:
            self.wall_jump_cooldown -= dt
        
        # Apply gravity if not dashing
        if not self.dashing:
            self.vel_y += self.gravity * dt
        
        # Cap falling speed
        if self.vel_y > 1000:
            self.vel_y = 1000
        
        # Get keyboard input
        keys = pygame.key.get_pressed()
        
        # Reset horizontal movement if not dashing
        if not self.dashing:
            # Handle left/right movement
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -self.move_speed
                self.facing_right = False
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = self.move_speed
                self.facing_right = True
            else:
                self.vel_x = 0
        
        # Handle dash
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.dash_available and not self.dashing:
            self.dashing = True
            self.dash_available = False
            self.dash_timer = self.dash_duration
            self.dash_cooldown = 1.0
            
            # Dash in the direction the player is facing
            if self.facing_right:
                self.vel_x = self.dash_power
            else:
                self.vel_x = -self.dash_power
            
            # Slight vertical boost during dash
            self.vel_y = -200
        
        # Move the player
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Flag to check if player was on ground before collision checks
        was_on_ground = self.on_ground
        self.on_ground = False
        self.wall_sliding = False
        
        # Check for collisions with platforms
        for platform in platforms:
            if self.check_collision_with_platform(platform):
                self.handle_platform_collision(platform)
        
        # Reset double jump if player has landed
        if self.on_ground and not was_on_ground:
            self.can_double_jump = True
        
        # Screen bounds checking
        if self.x < self.width / 2:
            self.x = self.width / 2
        elif self.x > SCREEN_WIDTH - self.width / 2:
            self.x = SCREEN_WIDTH - self.width / 2
        
        # Update animation state
        self.update_animation(dt)
        
        # Update player shape
        self.update_shape()
    
    def update_animation(self, dt):
        self.animation_timer += dt
        
        # Change animation state every 0.1 seconds while moving
        if abs(self.vel_x) > 50 and self.on_ground:
            if self.animation_timer > 0.1:
                self.animation_state = (self.animation_state + 1) % 4
                self.animation_timer = 0
        else:
            self.animation_state = 0
            self.animation_timer = 0
    
    def check_collision_with_platform(self, platform):
        # Simple rectangle collision check
        return platform.rect.colliderect(self.rect)
    
    def handle_platform_collision(self, platform):
        # Get the collision depth on each axis
        dx_left = self.rect.right - platform.rect.left
        dx_right = platform.rect.right - self.rect.left
        dy_top = self.rect.bottom - platform.rect.top
        dy_bottom = platform.rect.bottom - self.rect.top
        
        # Find the shallowest penetration
        min_dx = min(dx_left, dx_right)
        min_dy = min(dy_top, dy_bottom)
        
        # Resolve the collision along the shallowest penetration axis
        if min_dx < min_dy:
            # Horizontal collision
            if dx_left < dx_right:
                self.x = platform.rect.left - self.width / 2
                
                # Wall slide mechanics
                if self.vel_y > 0 and not self.on_ground:
                    self.wall_sliding = True
                    self.vel_y = min(self.vel_y, 150)  # Cap falling speed during wall slide
                    if self.wall_jump_cooldown <= 0 and (pygame.key.get_pressed()[pygame.K_SPACE]):
                        self.vel_y = self.jump_power * 0.8
                        self.vel_x = self.move_speed * 1.2  # Jump away from wall
                        self.wall_jump_cooldown = 0.3
            else:
                self.x = platform.rect.right + self.width / 2
                
                # Wall slide mechanics for right wall
                if self.vel_y > 0 and not self.on_ground:
                    self.wall_sliding = True
                    self.vel_y = min(self.vel_y, 150)  # Cap falling speed during wall slide
                    if self.wall_jump_cooldown <= 0 and (pygame.key.get_pressed()[pygame.K_SPACE]):
                        self.vel_y = self.jump_power * 0.8
                        self.vel_x = -self.move_speed * 1.2  # Jump away from wall
                        self.wall_jump_cooldown = 0.3
            self.vel_x = 0
        else:
            # Vertical collision
            if dy_top < dy_bottom:
                # Landed on top of platform
                self.y = platform.rect.top - self.height / 2
                self.vel_y = 0
                self.on_ground = True
            else:
                # Hit the bottom of platform
                self.y = platform.rect.bottom + self.height / 2
                self.vel_y = 0
    
    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
        elif self.wall_sliding:
            if self.wall_jump_cooldown <= 0:
                # Wall jump logic is handled in the platform collision
                pass
        elif self.can_double_jump:
            self.vel_y = self.jump_power * 0.8  # Slightly weaker double jump
            self.can_double_jump = False
    
    def shoot(self, bullets_list):
        if self.shoot_cooldown <= 0:
            # Create a new bullet
            from projectiles import Bullet  # Local import to avoid circular dependency
            
            # Calculate bullet position based on player orientation
            if self.facing_right:
                bullet_x = self.x + self.width / 2
                bullet_vel_x = self.bullet_speed
            else:
                bullet_x = self.x - self.width / 2
                bullet_vel_x = -self.bullet_speed
            
            # Create the bullet
            bullet = Bullet(
                bullet_x, 
                self.y - 5,  # Slight offset to make it appear from chest
                bullet_vel_x,
                0,  # No vertical velocity initially
                (0, 200, 255)  # Bullet color
            )
            
            # Add bullet to the list
            bullets_list.append(bullet)
            
            # Set cooldown
            self.shoot_cooldown = self.shoot_delay
    
    def take_damage(self):
        if not self.invulnerable:
            self.health -= 20
            self.invulnerable = True
            self.invulnerable_timer = self.invulnerable_duration
            
            # Damage knockback
            self.vel_y = -400
            
            # Health cannot go below zero
            if self.health < 0:
                self.health = 0
    
    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)
    
    def activate_power(self, power_type, duration=5.0):
        self.special_power = power_type
        self.special_timer = duration
        
        # Apply power-up effects
        if power_type == "speed":
            self.move_speed *= 1.5
        elif power_type == "jump":
            self.jump_power *= 1.3
        elif power_type == "shield":
            self.invulnerable = True
            self.invulnerable_timer = duration
    
    def deactivate_power(self):
        # Restore base stats when power-up ends
        if self.special_power == "speed":
            self.move_speed = 350
        elif self.special_power == "jump":
            self.jump_power = -700
        
        self.special_power = None
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.update_shape()
    
    def check_collision(self, entity):
        # Check collision with another entity
        return self.rect.colliderect(entity.rect)
    
    def is_invulnerable(self):
        return self.invulnerable
    
    def draw(self, surface):
        # Draw the player character using geometric shapes
        
        # Extract shape info
        torso = self.shape_info['torso']
        head = self.shape_info['head']
        legs = self.shape_info['legs']
        arms = self.shape_info['arms']
        
        # If invulnerable, flash the player
        if self.invulnerable and (pygame.time.get_ticks() % 200) < 100:
            alpha = 128
            color_mod = 50
        else:
            alpha = 255
            color_mod = 0
        
        # Draw legs with animation
        for i, leg in enumerate(legs):
            leg_x, leg_y, leg_w, leg_h = leg
            
            # Animate legs when walking
            if self.animation_state in [1, 3] and i == 0:
                leg_y -= 5
            elif self.animation_state in [1, 3] and i == 1:
                leg_y += 5
            elif self.animation_state in [0, 2] and i == 0:
                leg_y += 5
            elif self.animation_state in [0, 2] and i == 1:
                leg_y -= 5
            
            leg_color = (max(0, self.color[0] - 30 + color_mod), 
                        max(0, self.color[1] - 30 + color_mod), 
                        max(0, self.color[2] - 30 + color_mod))
            pygame.draw.rect(surface, leg_color, (leg_x, leg_y, leg_w, leg_h))
            pygame.draw.rect(surface, BLACK, (leg_x, leg_y, leg_w, leg_h), 2)
        
        # Draw torso
        torso_x, torso_y, torso_w, torso_h = torso
        pygame.draw.rect(surface, self.color, (torso_x, torso_y, torso_w, torso_h))
        pygame.draw.rect(surface, BLACK, (torso_x, torso_y, torso_w, torso_h), 2)
        
        # Draw arms with animation
        for i, arm in enumerate(arms):
            arm_x, arm_y, arm_w, arm_h = arm
            
            # Animate arms when walking
            if self.animation_state in [1, 3] and i == 0:
                arm_y += 5
            elif self.animation_state in [1, 3] and i == 1:
                arm_y -= 5
            elif self.animation_state in [0, 2] and i == 0:
                arm_y -= 5
            elif self.animation_state in [0, 2] and i == 1:
                arm_y += 5
            
            # Adjust arm positions when facing left/right
            if (self.facing_right and i == 1) or (not self.facing_right and i == 0):
                # Draw arm in shooting position if cooldown is low
                if self.shoot_cooldown < self.shoot_delay * 0.5:
                    arm_y = torso_y + torso_h * 0.2
                    
            arm_color = (max(0, self.color[0] - 20 + color_mod), 
                        max(0, self.color[1] - 20 + color_mod), 
                        max(0, self.color[2] - 20 + color_mod))
            pygame.draw.rect(surface, arm_color, (arm_x, arm_y, arm_w, arm_h))
            pygame.draw.rect(surface, BLACK, (arm_x, arm_y, arm_w, arm_h), 2)
        
        # Draw head
        head_x, head_y, head_r = head
        pygame.draw.circle(surface, (max(0, self.color[0] + 20 + color_mod), 
                                    max(0, self.color[1] + 20 + color_mod), 
                                    max(0, self.color[2] + 20 + color_mod)), 
                          (int(head_x), int(head_y)), int(head_r))
        pygame.draw.circle(surface, BLACK, (int(head_x), int(head_y)), int(head_r), 2)
        
        # Draw eyes
        eye_offset = 5 if self.facing_right else -5
        pygame.draw.circle(surface, WHITE, (int(head_x + eye_offset), int(head_y - 2)), 5)
        pygame.draw.circle(surface, BLACK, (int(head_x + eye_offset*1.5), int(head_y - 2)), 2)
        
        # Draw special effects
        if self.dashing:
            # Draw dash trail
            for i in range(5):
                alpha = 50 - i * 10
                offset = -i * 10 if self.facing_right else i * 10
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                s.fill((255, 255, 255, alpha))
                surface.blit(s, (self.x - self.width//2 + offset, self.y - self.height//2))
        
        # Draw power-up effects
        if self.special_power:
            if self.special_power == "speed":
                # Speed lines
                for i in range(10):
                    start_x = self.x - 30 - random.randint(0, 20)
                    start_y = self.y - 20 + random.randint(0, 40)
                    end_x = start_x - 20 - random.randint(0, 30)
                    end_y = start_y + random.randint(-10, 10)
                    pygame.draw.line(surface, YELLOW, (start_x, start_y), (end_x, end_y), 2)
            
            elif self.special_power == "jump":
                # Jump sparkles under feet
                for i in range(8):
                    sparkle_x = self.x - 15 + random.randint(0, 30)
                    sparkle_y = self.y + self.height/2 + random.randint(0, 10)
                    pygame.draw.circle(surface, CYAN, (int(sparkle_x), int(sparkle_y)), random.randint(1, 3))
            
            elif self.special_power == "shield":
                # Shield bubble
                shield_radius = self.width + 10
                shield_surface = pygame.Surface((shield_radius*2, shield_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(shield_surface, (100, 200, 255, 100), (shield_radius, shield_radius), shield_radius)
                pygame.draw.circle(shield_surface, (150, 220, 255, 150), (shield_radius, shield_radius), shield_radius, 3)
                surface.blit(shield_surface, (self.x - shield_radius, self.y - shield_radius))
        
        # Draw health bar above head
        health_width = 50
        health_height = 5
        health_x = self.x - health_width/2
        health_y = head_y - head_r - 15
        
        # Health bar background
        pygame.draw.rect(surface, (50, 50, 50), (health_x, health_y, health_width, health_height))
        
        # Health bar
        health_percent = self.health / self.max_health
        if health_percent > 0:
            health_color = GREEN
            if health_percent < 0.5:
                health_color = YELLOW
            if health_percent < 0.25:
                health_color = RED
                
            pygame.draw.rect(surface, health_color, 
                            (health_x, health_y, health_width * health_percent, health_height))
        
        # Debug: Draw collision box
        # pygame.draw.rect(surface, (255, 0, 0), self.rect, 1)
import pygame
import math
import random
from constants import *

class Bullet:
    def __init__(self, x, y, vel_x, vel_y, color):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.radius = 6
        self.color = color
        self.rect = pygame.Rect(x - self.radius, y - self.radius, 
                              self.radius * 2, self.radius * 2)
        self.lifespan = 2.0  # seconds
        self.trail_points = []
        self.max_trail_length = 10
        
    def update(self, dt):
        # Update position
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Update rect
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius
        
        # Add current position to trail
        self.trail_points.append((self.x, self.y))
        
        # Limit trail length
        if len(self.trail_points) > self.max_trail_length:
            self.trail_points.pop(0)
        
        # Decrease lifespan
        self.lifespan -= dt
    
    def is_off_screen(self):
        return (self.x < -50 or self.x > SCREEN_WIDTH + 50 or
                self.y < -50 or self.y > SCREEN_HEIGHT + 50 or
                self.lifespan <= 0)
    
    def check_collision(self, entity):
        return self.rect.colliderect(entity.rect)
    
    def draw(self, surface):
        # Draw trail
        if len(self.trail_points) > 1:
            for i in range(len(self.trail_points) - 1):
                trail_alpha = int(255 * (i / len(self.trail_points)))
                trail_width = 1 + int(3 * (i / len(self.trail_points)))
                
                pygame.draw.line(surface, 
                               (self.color[0], self.color[1], self.color[2]), 
                               self.trail_points[i], 
                               self.trail_points[i+1], 
                               trail_width)
        
        # Draw glow effect
        glow_radius = self.radius * 2
        glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color, 50), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surface, (self.x - glow_radius, self.y - glow_radius))
        
        # Draw main bullet
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
        # Draw highlight
        highlight_color = (min(255, self.color[0] + 150), 
                         min(255, self.color[1] + 150), 
                         min(255, self.color[2] + 150))
        pygame.draw.circle(surface, highlight_color, 
                         (int(self.x - self.radius/3), int(self.y - self.radius/3)), 
                         self.radius // 3)


class HomingMissile(Bullet):
    def __init__(self, x, y, vel_x, vel_y, color, target=None):
        super().__init__(x, y, vel_x, vel_y, color)
        self.target = target
        self.turn_speed = 5.0  # radians per second
        self.speed = 300
        self.lifespan = 5.0
        self.max_trail_length = 20
        self.wave_angle = 0
    
    def update(self, dt):
        # If we have a target, adjust velocity to track it
        if self.target and self.target.health > 0:
            # Calculate direction to target
            target_dx = self.target.x - self.x
            target_dy = self.target.y - self.y
            target_angle = math.atan2(target_dy, target_dx)
            
            # Calculate current velocity angle
            current_angle = math.atan2(self.vel_y, self.vel_x)
            
            # Find the shortest angle to rotate
            angle_diff = target_angle - current_angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            # Limit rotation by turn speed
            if angle_diff > self.turn_speed * dt:
                angle_diff = self.turn_speed * dt
            elif angle_diff < -self.turn_speed * dt:
                angle_diff = -self.turn_speed * dt
            
            # Apply rotation
            new_angle = current_angle + angle_diff
            
            # Add snake-like movement
            self.wave_angle += 10 * dt
            wave_intensity = 0.4  # How much it wiggles
            new_angle += math.sin(self.wave_angle) * wave_intensity
            
            # Update velocity
            self.vel_x = math.cos(new_angle) * self.speed
            self.vel_y = math.sin(new_angle) * self.speed
        
        # Call the parent update method
        super().update(dt)
    
    def draw(self, surface):
        # Draw trail with more vibrant colors
        if len(self.trail_points) > 1:
            for i in range(len(self.trail_points) - 1):
                trail_alpha = int(255 * (i / len(self.trail_points)))
                trail_width = 1 + int(4 * (i / len(self.trail_points)))
                
                # Calculate angle for smoke effect
                if i < len(self.trail_points) - 2:
                    dx = self.trail_points[i+1][0] - self.trail_points[i][0]
                    dy = self.trail_points[i+1][1] - self.trail_points[i][1]
                    angle = math.atan2(dy, dx)
                    
                    # Add smoke particles perpendicular to trail
                    perp_x = 3 * math.sin(angle)
                    perp_y = -3 * math.cos(angle)
                    
                    # Random smoke "puffs"
                    if random.random() < 0.3:
                        smoke_size = random.randint(2, 4)
                        offset = random.randint(-5, 5)
                        smoke_x = self.trail_points[i][0] + perp_x * offset
                        smoke_y = self.trail_points[i][1] + perp_y * offset
                        smoke_color = (150, 150, 150, 100)
                        
                        smoke_surface = pygame.Surface((smoke_size*2, smoke_size*2), pygame.SRCALPHA)
                        pygame.draw.circle(smoke_surface, smoke_color, (smoke_size, smoke_size), smoke_size)
                        surface.blit(smoke_surface, (smoke_x - smoke_size, smoke_y - smoke_size))
                
                # Main trail
                pygame.draw.line(surface, 
                               (self.color[0], self.color[1], self.color[2]), 
                               self.trail_points[i], 
                               self.trail_points[i+1], 
                               trail_width)
        
        # Draw missile body
        # Calculate angle based on velocity
        angle = math.atan2(self.vel_y, self.vel_x)
        
        # Calculate points for missile polygon
        length = self.radius * 3
        width = self.radius * 1.5
        
        # Nose point
        nose_x = self.x + math.cos(angle) * length
        nose_y = self.y + math.sin(angle) * length
        
        # Back points
        back_x = self.x - math.cos(angle) * length
        back_y = self.y - math.sin(angle) * length
        
        # Wing points
        wing1_x = back_x + math.sin(angle) * width
        wing1_y = back_y - math.cos(angle) * width
        
        wing2_x = back_x - math.sin(angle) * width
        wing2_y = back_y + math.cos(angle) * width
        
        # Draw the missile body
        pygame.draw.polygon(surface, self.color, [
            (nose_x, nose_y),
            (wing1_x, wing1_y),
            (back_x, back_y),
            (wing2_x, wing2_y)
        ])
        
        # Draw flame effect
        flame_length = random.randint(int(length*0.8), int(length*1.2))
        flame_x = back_x - math.cos(angle) * flame_length
        flame_y = back_y - math.sin(angle) * flame_length
        
        flame_color = (255, 128, 0)  # Orange flame
        pygame.draw.line(surface, flame_color, (back_x, back_y), (flame_x, flame_y), 3)
        
        # Add a little smoke at the back
        smoke_size = random.randint(3, 6)
        smoke_surface = pygame.Surface((smoke_size*2, smoke_size*2), pygame.SRCALPHA)
        pygame.draw.circle(smoke_surface, (100, 100, 100, 150), (smoke_size, smoke_size), smoke_size)
        surface.blit(smoke_surface, (back_x - smoke_size, back_y - smoke_size))


class ExplosiveBullet(Bullet):
    def __init__(self, x, y, vel_x, vel_y, color):
        super().__init__(x, y, vel_x, vel_y, color)
        self.radius = 8
        self.explosion_radius = 80
        self.has_exploded = False
        self.explosion_duration = 0.3
        self.explosion_timer = 0
    
    def explode(self):
        self.has_exploded = True
        self.explosion_timer = self.explosion_duration
        self.vel_x = 0
        self.vel_y = 0
    
    def update(self, dt):
        if self.has_exploded:
            self.explosion_timer -= dt
            if self.explosion_timer <= 0:
                self.lifespan = 0
        else:
            super().update(dt)
    
    def draw(self, surface):
        if self.has_exploded:
            # Calculate explosion progress
            progress = 1.0 - (self.explosion_timer / self.explosion_duration)
            current_radius = self.explosion_radius * progress
            
            # Draw explosion shockwave
            for i in range(3):
                radius = current_radius * (0.7 + i*0.15)
                alpha = int(255 * (1.0 - progress) * (0.8 - i*0.2))
                color = (255, 200 - i*50, 0, alpha)
                
                explosion_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(explosion_surface, color, (radius, radius), radius)
                surface.blit(explosion_surface, (self.x - radius, self.y - radius))
            
            # Draw some explosion particles
            for _ in range(10):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, current_radius)
                particle_x = self.x + math.cos(angle) * distance
                particle_y = self.y + math.sin(angle) * distance
                particle_size = random.randint(1, 3)
                
                pygame.draw.circle(surface, (255, 255, 0), 
                                 (int(particle_x), int(particle_y)), particle_size)
        else:
            # Draw regular bullet with pulsating effect
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 100)
            glow_radius = self.radius * (1.5 + pulse)
            
            glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*self.color, 100), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surface, (self.x - glow_radius, self.y - glow_radius))
            
            # Inner core
            pygame.draw.circle(surface, (255, 200, 0), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 255, 200), (int(self.x - 2), int(self.y - 2)), self.radius // 2)
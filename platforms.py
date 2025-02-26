import pygame
import random
import math
from constants import *

class Platform:
    def __init__(self, x, y, width, height, color=None, platform_type="normal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.platform_type = platform_type
        
        # Set color based on platform type if not specified
        if color is None:
            if platform_type == "normal":
                self.color = (100, 100, 100)  # Default gray
            elif platform_type == "bounce":
                self.color = (255, 150, 0)  # Orange for bounce platforms
            elif platform_type == "moving":
                self.color = (0, 150, 150)  # Teal for moving platforms
            elif platform_type == "falling":
                self.color = (150, 0, 150)  # Purple for falling platforms
            elif platform_type == "crumbling":
                self.color = (150, 150, 0)  # Yellow for crumbling platforms
            else:
                self.color = (100, 100, 100)  # Default gray
        else:
            self.color = color
        
        # Special platform properties
        self.original_position = (x, y)
        self.move_direction = 1
        self.move_counter = 0
        self.move_speed = 100  # pixels per second
        self.move_distance = 200  # pixels
        self.fall_speed = 0
        self.fall_acceleration = 500  # pixels per second squared
        self.is_active = True
        self.crumble_timer = 0
        self.crumble_delay = 0.5  # seconds
        self.crumble_state = 0
        self.bounce_power = -1000  # For bounce platforms
        
        # Visual effects
        self.outline_color = (50, 50, 50)
        self.time_offset = random.random() * 10  # For animation effects
        self.decoration_points = []
        self.generate_decoration_points()
    
    def generate_decoration_points(self):
        """Generate decoration points for platform details"""
        self.decoration_points = []
        
        # Number of points depends on platform size
        num_points = int((self.width * self.height) / 1000)
        
        for _ in range(num_points):
            x = random.randint(5, self.width - 5)
            y = random.randint(5, self.height - 5)
            size = random.randint(2, 5)
            shade = random.randint(-30, 30)
            
            # Ensure color components are valid
            r = max(0, min(255, self.color[0] + shade))
            g = max(0, min(255, self.color[1] + shade))
            b = max(0, min(255, self.color[2] + shade))
            
            self.decoration_points.append({
                'x': x,
                'y': y,
                'size': size,
                'color': (r, g, b)
            })
    
    def update(self, dt):
        """Update platform state"""
        if not self.is_active:
            return
        
        if self.platform_type == "moving":
            # Calculate movement
            move_amount = self.move_speed * dt * self.move_direction
            
            # Update position
            self.x += move_amount
            self.move_counter += abs(move_amount)
            
            # Check if we need to change direction
            if self.move_counter >= self.move_distance:
                self.move_direction *= -1
                self.move_counter = 0
            
            # Update rect position
            self.rect.x = self.x
        
        elif self.platform_type == "falling":
            # Check if platform is falling
            if self.fall_speed > 0:
                # Apply gravity
                self.fall_speed += self.fall_acceleration * dt
                self.y += self.fall_speed * dt
                self.rect.y = self.y
                
                # Deactivate if off screen
                if self.y > SCREEN_HEIGHT + 100:
                    self.is_active = False
        
        elif self.platform_type == "crumbling":
            if self.crumble_timer > 0:
                self.crumble_timer -= dt
                
                # Update crumble state for visual effect
                progress = 1.0 - (self.crumble_timer / self.crumble_delay)
                self.crumble_state = min(3, int(progress * 4))
                
                # Deactivate when timer runs out
                if self.crumble_timer <= 0:
                    self.is_active = False
    
    def trigger_fall(self):
        """Make a falling platform start falling"""
        if self.platform_type == "falling" and self.fall_speed == 0:
            self.fall_speed = 50  # Initial fall speed
    
    def trigger_crumble(self):
        """Start the crumbling process for a crumbling platform"""
        if self.platform_type == "crumbling" and self.crumble_timer == 0:
            self.crumble_timer = self.crumble_delay
    
    def apply_bounce(self, entity):
        """Apply bounce effect to an entity that collides with this platform"""
        if self.platform_type == "bounce":
            entity.vel_y = self.bounce_power
    
    def draw(self, surface):
        if not self.is_active:
            return
        
        # Get time for animation effects
        t = pygame.time.get_ticks() / 1000 + self.time_offset
        
        # Base shape
        if self.platform_type == "normal":
            # Draw the main platform
            pygame.draw.rect(surface, self.color, self.rect)
            
            # Draw a slight 3D effect (top highlight)
            highlight = (
                min(255, self.color[0] + 30),
                min(255, self.color[1] + 30),
                min(255, self.color[2] + 30)
            )
            pygame.draw.rect(surface, highlight, 
                           (self.rect.x, self.rect.y, self.rect.width, 5))
            
            # Draw a slight 3D effect (bottom shadow)
            shadow = (
                max(0, self.color[0] - 30),
                max(0, self.color[1] - 30),
                max(0, self.color[2] - 30)
            )
            pygame.draw.rect(surface, shadow, 
                           (self.rect.x, self.rect.y + self.rect.height - 5, 
                            self.rect.width, 5))
        
        elif self.platform_type == "bounce":
            # Draw the main platform
            pygame.draw.rect(surface, self.color, self.rect)
            
            # Draw bounce arrows
            arrow_spacing = 40
            for i in range(int(self.width / arrow_spacing)):
                x_pos = self.rect.x + i * arrow_spacing + arrow_spacing / 2
                base_y = self.rect.y + self.rect.height / 2
                
                # Animate the arrows
                offset = 3 * math.sin(t * 5 + i * 0.5)
                
                # Draw arrow
                pygame.draw.polygon(surface, WHITE, [
                    (x_pos, base_y - 10 + offset),
                    (x_pos - 7, base_y + offset),
                    (x_pos + 7, base_y + offset)
                ])
        
        elif self.platform_type == "moving":
            # Draw the main platform
            pygame.draw.rect(surface, self.color, self.rect)
            
            # Draw movement indicators
            indicator_color = (255, 255, 255)
            
            # Draw dots along the platform to indicate movement
            dot_spacing = 20
            for i in range(int(self.width / dot_spacing)):
                x_pos = self.rect.x + i * dot_spacing + dot_spacing / 2
                base_y = self.rect.y + self.rect.height / 2
                
                # Calculate dot position with animation
                x_offset = 5 * math.sin(t * 3 + i * 0.7)
                
                # Draw dot
                pygame.draw.circle(surface, indicator_color, 
                                 (int(x_pos + x_offset), int(base_y)), 3)
        
        elif self.platform_type == "falling":
            # Draw the main platform with a shaking effect if falling
            shake_x = 0
            shake_y = 0
            
            if self.fall_speed > 0:
                shake_x = random.randint(-2, 2)
                shake_y = random.randint(-2, 2)
            
            rect_with_shake = pygame.Rect(
                self.rect.x + shake_x,
                self.rect.y + shake_y,
                self.rect.width,
                self.rect.height
            )
            pygame.draw.rect(surface, self.color, rect_with_shake)
            
            # Add warning cracks
            for i in range(5):
                start_x = self.rect.x + random.randint(10, int(self.width - 10))
                end_x = start_x + random.randint(-20, 20)
                
                start_y = self.rect.y + random.randint(5, int(self.height - 5))
                end_y = start_y + random.randint(-5, 5)
                
                pygame.draw.line(surface, self.outline_color, 
                               (start_x, start_y), (end_x, end_y), 2)
        
        elif self.platform_type == "crumbling":
            # Draw the main platform with a crumbling effect
            if self.crumble_state == 0:
                pygame.draw.rect(surface, self.color, self.rect)
                
                # Draw warning cracks
                for i in range(3):
                    start_x = self.rect.x + random.randint(10, int(self.width - 10))
                    end_x = start_x + random.randint(-20, 20)
                    
                    start_y = self.rect.y + random.randint(5, int(self.height - 5))
                    end_y = start_y + random.randint(-5, 5)
                    
                    pygame.draw.line(surface, self.outline_color, 
                                  (start_x, start_y), (end_x, end_y), 1)
            else:
                # Draw crumbling state
                chunk_size = 10
                for x in range(0, self.width, chunk_size):
                    for y in range(0, self.height, chunk_size):
                        # Skip some chunks based on crumble state
                        if random.random() > (self.crumble_state * 0.2):
                            chunk_rect = pygame.Rect(
                                self.rect.x + x,
                                self.rect.y + y,
                                chunk_size,
                                chunk_size
                            )
                            pygame.draw.rect(surface, self.color, chunk_rect)
        
        # Draw decoration points for all platform types
        for point in self.decoration_points:
            pygame.draw.circle(surface, point['color'], 
                             (int(self.rect.x + point['x']), 
                              int(self.rect.y + point['y'])), 
                             point['size'])
        
        # Draw outline
        pygame.draw.rect(surface, self.outline_color, self.rect, 2)

def create_platform_layout(level_num, theme):
    """Create a platform layout for a specific level"""
    platforms = []
    
    # Base platform (always present)
    ground_height = 50
    platforms.append(Platform(0, SCREEN_HEIGHT - ground_height, 
                            SCREEN_WIDTH, ground_height, 
                            platform_type="normal"))
    
    # Add platform configurations based on level number
    if level_num == 0:  # Level 1
        # Simple platforms for the first level
        platforms.extend([
            Platform(100, 600, 200, 20, platform_type="normal"),
            Platform(400, 500, 200, 20, platform_type="normal"),
            Platform(700, 400, 200, 20, platform_type="normal"),
            Platform(400, 300, 200, 20, platform_type="normal"),
            Platform(100, 200, 200, 20, platform_type="normal")
        ])
        
    elif level_num == 1:  # Level 2
        # Add moving platforms
        platforms.extend([
            Platform(300, 600, 150, 20, platform_type="normal"),
            Platform(600, 500, 150, 20, platform_type="moving"),
            Platform(300, 400, 150, 20, platform_type="normal"),
            Platform(600, 300, 150, 20, platform_type="moving"),
            Platform(300, 200, 150, 20, platform_type="normal")
        ])
        
        # Set custom movement patterns
        platforms[-4].move_distance = 300
        platforms[-4].move_speed = 120
        platforms[-2].move_distance = 300
        platforms[-2].move_speed = 150
        
    elif level_num == 2:  # Level 3
        # Add bounce platforms
        platforms.extend([
            Platform(200, 600, 150, 20, platform_type="bounce"),
            Platform(500, 450, 150, 20, platform_type="normal"),
            Platform(800, 400, 150, 20, platform_type="normal"),
            Platform(500, 250, 150, 20, platform_type="bounce"),
            Platform(200, 150, 150, 20, platform_type="normal")
        ])
        
    elif level_num == 3:  # Level 4
        # Add falling/crumbling platforms
        platforms.extend([
            Platform(200, 600, 150, 20, platform_type="normal"),
            Platform(400, 500, 150, 20, platform_type="falling"),
            Platform(600, 400, 150, 20, platform_type="crumbling"),
            Platform(800, 300, 150, 20, platform_type="falling"),
            Platform(600, 200, 150, 20, platform_type="normal"),
            Platform(400, 150, 150, 20, platform_type="normal"),
            Platform(200, 100, 150, 20, platform_type="crumbling")
        ])
        
    elif level_num == 4:  # Level 5 (boss level)
        # Create a boss arena with a mix of platform types
        platforms.extend([
            # Bottom platforms
            Platform(200, 600, 200, 20, platform_type="normal"),
            Platform(500, 600, 200, 20, platform_type="normal"),
            Platform(800, 600, 200, 20, platform_type="normal"),
            
            # Middle platforms
            Platform(300, 450, 150, 20, platform_type="moving"),
            Platform(700, 450, 150, 20, platform_type="moving"),
            
            # Top platforms
            Platform(200, 300, 150, 20, platform_type="normal"),
            Platform(500, 300, 200, 20, platform_type="bounce"),
            Platform(800, 300, 150, 20, platform_type="normal"),
        ])
    
    # Apply theme-specific colors to all platforms
    apply_theme_colors(platforms, theme)
    
    return platforms

def apply_theme_colors(platforms, theme):
    """Apply color scheme based on level theme"""
    
    if theme == "forest":
        base_color = (76, 153, 0)  # Green
        accent_color = (102, 51, 0)  # Brown
    elif theme == "ice":
        base_color = (173, 216, 230)  # Light blue
        accent_color = (240, 248, 255)  # White-blue
    elif theme == "desert":
        base_color = (210, 180, 140)  # Tan
        accent_color = (244, 164, 96)  # Sandy brown
    elif theme == "volcano":
        base_color = (139, 0, 0)  # Dark red
        accent_color = (255, 69, 0)  # Red-orange
    elif theme == "tech":
        base_color = (70, 130, 180)  # Steel blue
        accent_color = (211, 211, 211)  # Light gray
    else:
        base_color = (100, 100, 100)  # Default gray
        accent_color = (150, 150, 150)  # Lighter gray
    
    # Apply colors based on platform type
    for platform in platforms:
        if platform.platform_type == "normal":
            platform.color = base_color
        elif platform.platform_type == "moving":
            # Slightly lighter than base
            platform.color = (
                min(255, base_color[0] + 20),
                min(255, base_color[1] + 20),
                min(255, base_color[2] + 20)
            )
        elif platform.platform_type == "bounce":
            platform.color = accent_color
        elif platform.platform_type == "falling":
            # Darker than base
            platform.color = (
                max(0, base_color[0] - 30),
                max(0, base_color[1] - 30),
                max(0, base_color[2] - 30)
            )
        elif platform.platform_type == "crumbling":
            platform.color = (
                max(0, base_color[0] - 15),
                max(0, base_color[1] - 15),
                max(0, base_color[2] - 15)
            )
        
        # Regenerate decoration points to match new colors
        platform.generate_decoration_points()
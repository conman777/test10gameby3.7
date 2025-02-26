import pygame
import random
import math
import sys
from enum import Enum

# Initialize Pygame
pygame.init()

# Import constants
from constants import *

# Game states
class GameState(Enum):
    TITLE = 0
    PLAYING = 1
    LEVEL_COMPLETE = 2
    GAME_OVER = 3
    PAUSE = 4
    VICTORY = 5
    BOSS_INTRO = 6

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Epic Platformer Adventure")
clock = pygame.time.Clock()

# Font setup
title_font = pygame.font.SysFont('comicsansms', 72)
large_font = pygame.font.SysFont('comicsansms', 48)
medium_font = pygame.font.SysFont('comicsansms', 32)
small_font = pygame.font.SysFont('comicsansms', 24)

# Game variables
current_level = 0
total_levels = 5
score = 0
lives = 3
game_state = GameState.TITLE
last_time = pygame.time.get_ticks()

# Import game components after initialization
from player import Player
from platforms import Platform, create_platform_layout
from projectiles import Bullet, HomingMissile, ExplosiveBullet
from enemies import Enemy, Boss

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def update(self, dt):
        # Update particles and remove dead ones
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def add_particle(self, particle):
        self.particles.append(particle)
    
    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
    
    def create_explosion(self, x, y, color, count=20):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            size = random.randint(2, 6)
            lifetime = random.uniform(0.5, 1.5)
            
            self.add_particle(Particle(x, y, vel_x, vel_y, color, size, lifetime))
    
    def create_trail(self, x, y, color, direction, count=5):
        for _ in range(count):
            angle = random.uniform(-0.5, 0.5) + direction
            speed = random.uniform(10, 30)
            vel_x = -math.cos(angle) * speed  # Negative to go opposite of direction
            vel_y = -math.sin(angle) * speed
            size = random.randint(1, 3)
            lifetime = random.uniform(0.3, 0.7)
            
            self.add_particle(Particle(x, y, vel_x, vel_y, color, size, lifetime))

class Particle:
    def __init__(self, x, y, vel_x, vel_y, color, size, lifetime):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.size = size
        self.initial_size = size
        self.lifetime = lifetime
        self.initial_lifetime = lifetime
        self.gravity = random.uniform(50, 150)
    
    def update(self, dt):
        # Update position
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Apply gravity
        self.vel_y += self.gravity * dt
        
        # Reduce lifetime
        self.lifetime -= dt
        
        # Return True if still alive, False if should be removed
        return self.lifetime > 0
    
    def draw(self, surface):
        # Fade out as lifetime decreases
        alpha = int(255 * (self.lifetime / self.initial_lifetime))
        
        # Shrink as lifetime decreases
        current_size = self.initial_size * (self.lifetime / self.initial_lifetime)
        
        # Create surface for semi-transparent particle
        particle_surface = pygame.Surface((int(current_size * 2), int(current_size * 2)), pygame.SRCALPHA)
        
        # Draw particle with alpha
        pygame.draw.circle(particle_surface, (*self.color, alpha), 
                         (int(current_size), int(current_size)), int(current_size))
        
        # Blit to screen
        surface.blit(particle_surface, 
                    (int(self.x - current_size), int(self.y - current_size)))

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.rect = pygame.Rect(x - 15, y - 15, 30, 30)
        self.power_type = power_type  # "health", "speed", "jump", "shield"
        self.collected = False
        self.bob_offset = 0
        self.bob_speed = 2
        self.rotation = 0
        self.rotation_speed = 60
        
        # Set color based on power type
        if power_type == "health":
            self.color = RED
        elif power_type == "speed":
            self.color = YELLOW
        elif power_type == "jump":
            self.color = CYAN
        elif power_type == "shield":
            self.color = PURPLE
        else:
            self.color = WHITE
    
    def update(self, dt):
        if self.collected:
            return
        
        # Bobbing animation
        self.bob_offset = 5 * math.sin(pygame.time.get_ticks() / 300)
        
        # Rotation animation
        self.rotation += self.rotation_speed * dt
        if self.rotation >= 360:
            self.rotation -= 360
    
    def draw(self, surface):
        if self.collected:
            return
        
        # Draw power-up with bobbing effect and rotation
        adjusted_y = self.y + self.bob_offset
        
        # Create a surface for the power-up
        power_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw the base shape
        if self.power_type == "health":
            # Draw health cross
            pygame.draw.rect(power_surface, self.color, (10, 5, 10, 20))
            pygame.draw.rect(power_surface, self.color, (5, 10, 20, 10))
        elif self.power_type == "speed":
            # Draw speed arrow
            points = [(5, 15), (20, 5), (20, 10), (25, 10), (25, 20), (20, 20), (20, 25), (5, 15)]
            pygame.draw.polygon(power_surface, self.color, points)
        elif self.power_type == "jump":
            # Draw jump spring
            pygame.draw.rect(power_surface, self.color, (10, 5, 10, 15))
            pygame.draw.rect(power_surface, self.color, (5, 20, 20, 5))
        elif self.power_type == "shield":
            # Draw shield bubble
            pygame.draw.circle(power_surface, self.color, (15, 15), 10, 2)
            pygame.draw.circle(power_surface, self.color, (15, 15), 5)
        
        # Draw glow effect
        glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color, 100), (self.width//2 + 5, self.height//2 + 5), self.width//2 + 5)
        
        # Draw glow
        rotated_glow = pygame.transform.rotate(glow_surface, self.rotation)
        glow_rect = rotated_glow.get_rect(center=(self.x, adjusted_y))
        surface.blit(rotated_glow, glow_rect)
        
        # Rotate and draw the power-up
        rotated_surface = pygame.transform.rotate(power_surface, self.rotation)
        rotated_rect = rotated_surface.get_rect(center=(self.x, adjusted_y))
        surface.blit(rotated_surface, rotated_rect)
        
        # Draw sparkles
        t = pygame.time.get_ticks() / 1000
        for i in range(3):
            spark_x = self.x + 15 * math.cos(t * 2 + i * 2)
            spark_y = adjusted_y + 15 * math.sin(t * 2 + i * 2)
            size = 2 + math.sin(t * 5 + i) * 1
            pygame.draw.circle(surface, WHITE, (int(spark_x), int(spark_y)), int(size))
    
    def check_collision(self, player):
        return self.rect.colliderect(player.rect)
    
    def collect(self, player):
        if self.collected:
            return
        
        self.collected = True
        
        # Apply power-up effect
        if self.power_type == "health":
            player.heal(20)
        elif self.power_type == "speed" or self.power_type == "jump" or self.power_type == "shield":
            player.activate_power(self.power_type)
        
        return 50  # Score for collecting

# Create game objects
player = None
platforms = []
enemies = []
bullets = []
enemy_bullets = []
powerups = []
particle_system = ParticleSystem()
level_themes = ["forest", "ice", "desert", "volcano", "tech"]

def initialize_game():
    """Initialize or reset the game state"""
    global player, platforms, enemies, bullets, enemy_bullets, powerups, current_level, score, lives
    
    # Reset game variables
    if game_state == GameState.TITLE:
        current_level = 0
        score = 0
        lives = 3
    
    # Create player
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
    
    # Create platforms for the current level
    theme = level_themes[current_level % len(level_themes)]
    platforms = create_platform_layout(current_level, theme)
    
    # Clear other objects
    bullets = []
    enemy_bullets = []
    powerups = []
    
    # Add some powerups
    add_powerups()
    
    # Add enemies for the level
    add_enemies()

def add_powerups():
    """Add power-ups to the level"""
    global powerups
    powerups = []
    
    # Add 2-3 random powerups
    num_powerups = random.randint(2, 3)
    power_types = ["health", "speed", "jump", "shield"]
    
    for _ in range(num_powerups):
        # Find a platform to place the powerup on
        if len(platforms) > 1:  # Skip the ground platform
            platform = random.choice(platforms[1:])
            
            # Place powerup on top of the platform
            power_x = platform.x + random.randint(20, platform.width - 20)
            power_y = platform.y - 20
            
            # Choose random power type
            power_type = random.choice(power_types)
            
            powerups.append(PowerUp(power_x, power_y, power_type))

def add_enemies():
    """Add enemies based on the current level"""
    global enemies
    enemies = []
    
    if current_level < total_levels - 1:
        # Regular levels
        num_enemies = 2 + current_level
        
        for _ in range(num_enemies):
            # Randomly choose enemy type based on level progress
            if current_level == 0:
                enemy_type = "basic"  # Only basic enemies in first level
            elif current_level == 1:
                enemy_type = random.choice(["basic", "runner"])
            elif current_level == 2:
                enemy_type = random.choice(["basic", "runner", "tank"])
            else:
                enemy_type = random.choice(["basic", "runner", "tank", "shooter"])
            
            # Find a suitable platform to spawn the enemy
            if len(platforms) > 1:  # Skip ground platform
                platform = random.choice(platforms[1:])
                spawn_x = platform.x + random.randint(20, platform.width - 20)
                spawn_y = platform.y - 30
                
                enemies.append(Enemy(spawn_x, spawn_y, enemy_type))
    else:
        # Boss level
        boss_x = SCREEN_WIDTH // 2
        boss_y = SCREEN_HEIGHT // 2
        enemies.append(Boss(boss_x, boss_y))

def update_game(dt):
    """Update game logic"""
    global score, lives, game_state
    
    # Get keyboard input for player movement
    keys = pygame.key.get_pressed()
    
    # Handle horizontal movement
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.vel_x = -player.move_speed
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.vel_x = player.move_speed
    else:
        # Only reset horizontal velocity if not dashing
        if not player.dashing:
            player.vel_x = 0
    
    # Handle dash
    if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and player.dash_available and not player.dashing:
        player.dashing = True
        player.dash_available = False
        player.dash_timer = player.dash_duration
        player.dash_cooldown = 1.0
        
        # Dash in the direction the player is facing
        if player.facing_right:
            player.vel_x = player.dash_power
        else:
            player.vel_x = -player.dash_power
        
        # Slight vertical boost during dash
        player.vel_y = -200
    
    # Update player
    player.update(platforms, dt)
    
    # Update platforms
    for platform in platforms:
        platform.update(dt)
        
        # Check for special platform interactions with player
        if platform.platform_type == "bounce" and player.check_collision_with_platform(platform):
            if player.vel_y > 0:  # Only bounce if player is moving downward
                platform.apply_bounce(player)
        
        elif platform.platform_type == "falling" and player.check_collision_with_platform(platform):
            if player.vel_y > 0:  # Only trigger if player lands on platform
                platform.trigger_fall()
        
        elif platform.platform_type == "crumbling" and player.check_collision_with_platform(platform):
            if player.vel_y > 0:  # Only trigger if player lands on platform
                platform.trigger_crumble()
    
    # Update bullets and check collisions with enemies
    for bullet in bullets[:]:
        bullet.update(dt)
        if bullet.is_off_screen():
            bullets.remove(bullet)
        else:
            for enemy in enemies[:]:
                if bullet.check_collision(enemy):
                    # Create explosion effect
                    particle_system.create_explosion(bullet.x, bullet.y, bullet.color, 15)
                    
                    # If it's an explosive bullet, trigger explosion
                    if isinstance(bullet, ExplosiveBullet) and not bullet.has_exploded:
                        bullet.explode()
                        # Check for other enemies in blast radius
                        for other_enemy in enemies:
                            if other_enemy != enemy:
                                dx = other_enemy.x - bullet.x
                                dy = other_enemy.y - bullet.y
                                dist = math.sqrt(dx*dx + dy*dy)
                                if dist < bullet.explosion_radius:
                                    if other_enemy.take_damage(30):  # Splash damage
                                        score += other_enemy.points_value
                                        enemies.remove(other_enemy)
                                        particle_system.create_explosion(other_enemy.x, other_enemy.y, RED, 20)
                    else:
                        bullets.remove(bullet)
                    
                    # Apply damage to enemy
                    if enemy.take_damage(50):  # Returns True if enemy died
                        score += enemy.points_value
                        enemies.remove(enemy)
                        particle_system.create_explosion(enemy.x, enemy.y, RED, 20)
                    break
    
    # Update enemy bullets
    for bullet in enemy_bullets[:]:
        bullet.update(dt)
        if bullet.is_off_screen():
            enemy_bullets.remove(bullet)
        elif bullet.check_collision(player) and not player.is_invulnerable():
            player.take_damage()
            particle_system.create_explosion(bullet.x, bullet.y, (255, 0, 0), 10)
            enemy_bullets.remove(bullet)
    
    # Update enemies
    for enemy in enemies[:]:
        enemy.update(dt, player, platforms, enemy_bullets)
        
        # Check for collision with player
        if enemy.check_collision(player) and not player.is_invulnerable():
            player.take_damage()
            particle_system.create_explosion(player.x, player.y, RED, 15)
    
    # Update powerups
    for powerup in powerups[:]:
        powerup.update(dt)
        if powerup.check_collision(player):
            score_value = powerup.collect(player)
            if score_value:
                score += score_value
            particle_system.create_explosion(powerup.x, powerup.y, powerup.color, 15)
            powerups.remove(powerup)
    
    # Update particles
    particle_system.update(dt)
    
    # Check for level completion (no more enemies)
    if len(enemies) == 0 and current_level < total_levels - 1:
        game_state = GameState.LEVEL_COMPLETE
    
    # Check for game over
    if player.health <= 0:
        lives -= 1
        if lives > 0:
            # Reset the current level
            initialize_game()
        else:
            game_state = GameState.GAME_OVER

def draw_game():
    """Draw the game state"""
    # Fill background with sky color based on level theme
    theme = level_themes[current_level % len(level_themes)]
    if theme == "forest":
        bg_color = (135, 206, 235)  # Sky blue
    elif theme == "ice":
        bg_color = (200, 230, 255)  # Light blue
    elif theme == "desert":
        bg_color = (255, 230, 180)  # Sandy yellow
    elif theme == "volcano":
        bg_color = (70, 20, 20)  # Dark red
    elif theme == "tech":
        bg_color = (20, 20, 40)  # Dark blue-gray
    else:
        bg_color = (135, 206, 235)  # Default sky blue
    
    screen.fill(bg_color)
    
    # Draw platforms
    for platform in platforms:
        platform.draw(screen)
    
    # Draw bullets
    for bullet in bullets:
        bullet.draw(screen)
    
    # Draw enemy bullets
    for bullet in enemy_bullets:
        bullet.draw(screen)
    
    # Draw powerups
    for powerup in powerups:
        powerup.draw(screen)
    
    # Draw enemies
    for enemy in enemies:
        enemy.draw(screen)
    
    # Draw player
    player.draw(screen)
    
    # Draw particles
    particle_system.draw(screen)
    
    # Draw HUD
    draw_hud()

def draw_hud():
    """Draw heads-up display with score, lives, etc."""
    # Draw score
    score_text = small_font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (20, 20))
    
    # Draw lives
    lives_text = small_font.render(f"Lives: {lives}", True, WHITE)
    screen.blit(lives_text, (20, 50))
    
    # Draw level
    level_text = small_font.render(f"Level: {current_level + 1}", True, WHITE)
    screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 20, 20))
    
    # Draw dash cooldown indicator
    if player.dash_available:
        dash_color = GREEN
    else:
        dash_color = (100, 100, 100)
    
    pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH - 120, 50, 100, 10))
    dash_width = 100 * (1 - (player.dash_cooldown / 1.0)) if not player.dash_available else 100
    pygame.draw.rect(screen, dash_color, (SCREEN_WIDTH - 120, 50, dash_width, 10))
    dash_text = small_font.render("Dash", True, WHITE)
    screen.blit(dash_text, (SCREEN_WIDTH - dash_text.get_width() - 130, 45))

def draw_title_screen():
    """Draw the title screen"""
    # Background
    screen.fill((20, 30, 60))
    
    # Title
    title_text = title_font.render("Epic Platformer", True, GOLD)
    subtitle_text = large_font.render("Adventure", True, SILVER)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
    screen.blit(subtitle_text, (SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2, 230))
    
    # Instructions
    start_text = medium_font.render("Press SPACE to Start", True, WHITE)
    screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 350))
    
    controls_text = small_font.render("WASD/Arrows: Move   SPACE: Jump   SHIFT: Dash   LEFT MOUSE: Shoot", True, WHITE)
    screen.blit(controls_text, (SCREEN_WIDTH // 2 - controls_text.get_width() // 2, 450))
    
    # Version
    version_text = small_font.render("v1.0", True, WHITE)
    screen.blit(version_text, (SCREEN_WIDTH - version_text.get_width() - 20, SCREEN_HEIGHT - 30))

def draw_level_complete():
    """Draw level complete screen"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    complete_text = large_font.render("Level Complete!", True, GOLD)
    screen.blit(complete_text, (SCREEN_WIDTH // 2 - complete_text.get_width() // 2, 200))
    
    score_text = medium_font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 270))
    
    next_text = medium_font.render("Press SPACE for next level", True, WHITE)
    screen.blit(next_text, (SCREEN_WIDTH // 2 - next_text.get_width() // 2, 350))

def draw_game_over():
    """Draw game over screen"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    
    gameover_text = title_font.render("GAME OVER", True, RED)
    screen.blit(gameover_text, (SCREEN_WIDTH // 2 - gameover_text.get_width() // 2, 180))
    
    score_text = large_font.render(f"Final Score: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 280))
    
    restart_text = medium_font.render("Press SPACE to restart", True, WHITE)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 380))

def draw_pause_screen():
    """Draw pause screen"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    pause_text = large_font.render("PAUSED", True, WHITE)
    screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 200))
    
    resume_text = medium_font.render("Press ESC to resume", True, WHITE)
    screen.blit(resume_text, (SCREEN_WIDTH // 2 - resume_text.get_width() // 2, 300))

def draw_victory_screen():
    """Draw victory screen"""
    screen.fill((20, 40, 80))
    
    victory_text = title_font.render("VICTORY!", True, GOLD)
    screen.blit(victory_text, (SCREEN_WIDTH // 2 - victory_text.get_width() // 2, 150))
    
    congrats_text = large_font.render("Congratulations!", True, WHITE)
    screen.blit(congrats_text, (SCREEN_WIDTH // 2 - congrats_text.get_width() // 2, 250))
    
    score_text = medium_font.render(f"Final Score: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 320))
    
    restart_text = medium_font.render("Press SPACE to play again", True, WHITE)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 400))

def handle_events():
    """Handle pygame events"""
    global game_state, current_level
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == GameState.PLAYING:
                    game_state = GameState.PAUSE
                elif game_state == GameState.PAUSE:
                    game_state = GameState.PLAYING
            
            elif event.key == pygame.K_SPACE:
                if game_state == GameState.TITLE:
                    game_state = GameState.PLAYING
                    initialize_game()
                elif game_state == GameState.LEVEL_COMPLETE:
                    current_level += 1
                    if current_level >= total_levels:
                        game_state = GameState.VICTORY
                    else:
                        game_state = GameState.PLAYING
                        initialize_game()
                elif game_state == GameState.GAME_OVER or game_state == GameState.VICTORY:
                    game_state = GameState.TITLE
            
            # Jump when pressing space in playing mode
            if game_state == GameState.PLAYING and (event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP):
                player.jump()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == GameState.PLAYING and event.button == 1:  # Left mouse button
                player.shoot(bullets)

# Main game loop
while True:
    # Calculate delta time
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0  # Convert to seconds
    last_time = current_time
    
    # Cap delta time to avoid physics issues on lag
    dt = min(dt, 0.1)
    
    handle_events()
    
    if game_state == GameState.PLAYING:
        update_game(dt)
        draw_game()
    elif game_state == GameState.TITLE:
        draw_title_screen()
    elif game_state == GameState.LEVEL_COMPLETE:
        draw_game()
        draw_level_complete()
    elif game_state == GameState.GAME_OVER:
        draw_game()
        draw_game_over()
    elif game_state == GameState.PAUSE:
        draw_game()
        draw_pause_screen()
    elif game_state == GameState.VICTORY:
        draw_victory_screen()
    
    # Update the display
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(FPS)
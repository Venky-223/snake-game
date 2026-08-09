import pygame
import random
import math
import time

# Snake Game v3
# Features:
# - Center obstacles/walls
# - Collision with walls = game over
# - Normal eggs = +1 score
# - Every 5 normal eggs, a golden egg appears
# - Golden egg is available for 5 seconds and gives +5 score
# - Snake changes color after every 5 normal eggs
# - Death animation
# - Pause / restart
# - Keyboard + on-screen controls
# - Resizable window

pygame.init()

WIDTH, HEIGHT = 720, 820
MIN_SIZE = 520
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Snake Game v3")
clock = pygame.time.Clock()

FONT = pygame.font.Font(None, 30)
SMALL_FONT = pygame.font.Font(None, 24)
BIG_FONT = pygame.font.Font(None, 64)

SNAKE_COLORS = [
    (50, 205, 50),
    (255, 210, 31),
    (0, 217, 255),
    (255, 92, 138),
    (181, 108, 255),
    (255, 140, 66),
]

BG = (10, 14, 18)
BOARD_BG = (17, 24, 32)
WHITE = (245, 245, 245)
WALL_COLOR = (160, 90, 55)
WALL_EDGE = (220, 135, 70)
GOLD = (255, 196, 30)

GRID = 30
SPEED = 0.105

DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}
OPPOSITE = {
    "UP": "DOWN",
    "DOWN": "UP",
    "LEFT": "RIGHT",
    "RIGHT": "LEFT",
}


def board_rect():
    margin = max(12, int(min(screen.get_width(), screen.get_height() - 150) * 0.04))
    size = min(screen.get_width() - 2 * margin, screen.get_height() - 170)
    size = max(300, size)
    x = (screen.get_width() - size) // 2
    y = 115
    return pygame.Rect(x, y, size, size)


def cell_size():
    return board_rect().width / GRID


def cell_center(pos):
    r = board_rect()
    c = cell_size()
    return r.x + (pos[0] + 0.5) * c, r.y + (pos[1] + 0.5) * c


def create_obstacles():
    # Decorative battle/wall blocks in the middle of the screen.
    # They form several barriers with small gaps so the player can navigate.
    patterns = [
        # Horizontal upper-middle wall
        [(x, 11) for x in range(9, 14)] +
        [(x, 11) for x in range(16, 21)],

        # Horizontal lower-middle wall
        [(x, 18) for x in range(9, 13)] +
        [(x, 18) for x in range(17, 21)],

        # Vertical left-middle wall
        [(10, y) for y in range(12, 18)],

        # Vertical right-middle wall
        [(19, y) for y in range(12, 18)],
    ]

    walls = set()
    for group in patterns:
        walls.update(group)

    return walls


def random_free_position(snake, walls, extra=None):
    occupied = set(snake) | set(walls)
    if extra:
        occupied |= set(extra)

    free = [
        (x, y)
        for y in range(GRID)
        for x in range(GRID)
        if (x, y) not in occupied
    ]
    return random.choice(free) if free else (1, 1)


def draw_text(text, font, pos, color=WHITE, center=False):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    screen.blit(surface, rect)


def draw_egg(pos, golden=False, pulse=0):
    cx, cy = cell_center(pos)
    c = cell_size()

    scale = 1.0 + (0.07 * math.sin(pulse * 6.0)) if golden else 1.0
    w = c * 0.48 * scale
    h = c * 0.66 * scale

    # Shadow
    pygame.draw.ellipse(
        screen,
        (0, 0, 0),
        (cx - w * 0.72, cy + h * 0.25, w * 1.45, h * 0.35),
    )

    # Egg shape using polygon points
    points = []
    for i in range(32):
        a = math.pi * 2 * i / 32
        # Egg: narrower at top, wider toward lower half
        t = (math.sin(a) + 1) / 2
        rx = w * (0.72 + 0.28 * t)
        ry = h
        points.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))

    if golden:
        # Outer glow
        for extra in (8, 5, 2):
            pygame.draw.ellipse(
                screen,
                (255, 210, 50),
                (cx - w - extra, cy - h - extra,
                 2 * (w + extra), 2 * (h + extra)),
                width=2,
            )
        pygame.draw.polygon(screen, GOLD, points)
        pygame.draw.polygon(screen, (255, 235, 120), points, 2)
        draw_text("★", SMALL_FONT, (cx, cy), (255, 255, 220), center=True)
    else:
        pygame.draw.polygon(screen, (245, 235, 205), points)
        pygame.draw.polygon(screen, (130, 110, 75), points, 2)
        for i in range(7):
            a = i * 2.3
            sx = cx + math.cos(a) * w * 0.45
            sy = cy + math.sin(a) * h * 0.55
            pygame.draw.circle(screen, (180, 155, 105), (int(sx), int(sy)), max(1, int(c * 0.018)))


def draw_wall(pos):
    r = board_rect()
    c = cell_size()
    x = int(r.x + pos[0] * c)
    y = int(r.y + pos[1] * c)
    rect = pygame.Rect(x + 2, y + 2, int(c - 4), int(c - 4))

    pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=max(3, int(c * 0.12)))
    pygame.draw.rect(screen, WALL_EDGE, rect, width=2, border_radius=max(3, int(c * 0.12)))

    # Battle-wall details
    pygame.draw.line(
        screen, (100, 55, 40),
        (rect.left + rect.width * 0.25, rect.top + rect.height * 0.25),
        (rect.right - rect.width * 0.2, rect.bottom - rect.height * 0.25),
        2
    )


def draw_snake(snake, color):
    c = cell_size()
    for i, (xg, yg) in enumerate(snake):
        cx, cy = cell_center((xg, yg))
        rect = pygame.Rect(
            int(cx - c * 0.43),
            int(cy - c * 0.43),
            int(c * 0.86),
            int(c * 0.86),
        )
        pygame.draw.rect(screen, color, rect, border_radius=max(4, int(c * 0.16)))
        pygame.draw.rect(screen, (0, 0, 0), rect, width=2, border_radius=max(4, int(c * 0.16)))

        if i == 0:
            # Eyes based on direction
            pygame.draw.circle(screen, (15, 15, 15), (int(cx - c * 0.16), int(cy - c * 0.16)), max(2, int(c * 0.07)))
            pygame.draw.circle(screen, (15, 15, 15), (int(cx + c * 0.16), int(cy - c * 0.16)), max(2, int(c * 0.07)))


def draw_board(walls):
    r = board_rect()
    pygame.draw.rect(screen, BOARD_BG, r, border_radius=14)
    pygame.draw.rect(screen, WHITE, r, width=3, border_radius=14)

    c = cell_size()
    for i in range(1, GRID):
        x = int(r.x + i * c)
        y = int(r.y + i * c)
        pygame.draw.line(screen, (28, 36, 45), (x, r.top), (x, r.bottom), 1)
        pygame.draw.line(screen, (28, 36, 45), (r.left, y), (r.right, y), 1)

    for wall in walls:
        draw_wall(wall)


def draw_controls():
    # Touch/click controls at bottom
    w = screen.get_width()
    h = screen.get_height()
    y = h - 70
    size = min(52, max(42, w // 12))
    gap = 8
    total = size * 3 + gap * 2
    x = (w - total) // 2

    buttons = [
        ("▲", pygame.Rect(x + size + gap, y, size, size), "UP"),
        ("◀", pygame.Rect(x, y, size, size), "LEFT"),
        ("▼", pygame.Rect(x + size + gap, y, size, size), "DOWN"),
        ("▶", pygame.Rect(x + 2 * (size + gap), y, size, size), "RIGHT"),
    ]

    for label, rect, _ in buttons:
        pygame.draw.rect(screen, (42, 50, 60), rect, border_radius=10)
        pygame.draw.rect(screen, (110, 120, 130), rect, width=2, border_radius=10)
        draw_text(label, FONT, rect.center, WHITE, center=True)


def draw_death_animation(progress, snake, color):
    # Explosion/shatter effect centered around the snake head
    if snake:
        hx, hy = cell_center(snake[0])

        for i in range(24):
            angle = (i / 24) * math.pi * 2
            radius = progress * (20 + (i % 6) * 8)
            px = hx + math.cos(angle) * radius
            py = hy + math.sin(angle) * radius
            alpha_size = max(2, int(6 * (1 - progress) + 2))
            pygame.draw.circle(screen, color, (int(px), int(py)), alpha_size)

        pygame.draw.circle(
            screen,
            (255, 90, 50),
            (int(hx), int(hy)),
            max(2, int(45 * (1 - progress))),
            width=3,
        )


def draw_game(snake, egg, golden_egg, walls, score, eggs_count, color_index,
              paused, game_over, death_progress):
    screen.fill(BG)

    draw_text("🐍 Snake Game v3", BIG_FONT, (screen.get_width() // 2, 35), WHITE, center=True)
    draw_text(
        f"Score: {score}   |   Eggs: {eggs_count}/5",
        FONT,
        (screen.get_width() // 2, 82),
        WHITE,
        center=True,
    )

    draw_board(walls)

    pulse = time.time()
    draw_egg(egg, golden=False, pulse=pulse)

    if golden_egg is not None:
        draw_egg(golden_egg, golden=True, pulse=pulse)

    draw_snake(snake, SNAKE_COLORS[color_index])

    if game_over:
        draw_death_animation(death_progress, snake, SNAKE_COLORS[color_index])
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(125 * death_progress)))
        screen.blit(overlay, (0, 0))
        draw_text("GAME OVER", BIG_FONT, (screen.get_width() // 2, screen.get_height() // 2 - 20), WHITE, center=True)
        draw_text("Press R or Restart", FONT, (screen.get_width() // 2, screen.get_height() // 2 + 35), WHITE, center=True)

    elif paused:
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        draw_text("PAUSED", BIG_FONT, (screen.get_width() // 2, screen.get_height() // 2), WHITE, center=True)

    draw_controls()
    pygame.display.flip()


def new_game():
    walls = create_obstacles()
    snake = [(15, 15), (14, 15), (13, 15)]
    direction = "RIGHT"
    next_direction = "RIGHT"
    score = 0
    eggs_count = 0
    color_index = 0
    egg = random_free_position(snake, walls)
    golden_egg = None
    golden_spawn_time = None
    paused = False
    game_over = False
    death_start = None
    status = "Eat 5 eggs: then a golden egg appears!"
    return (snake, direction, next_direction, score, eggs_count, color_index,
            egg, golden_egg, golden_spawn_time, paused, game_over,
            death_start, walls, status)


state = new_game()


def set_direction(new_direction):
    global state
    snake, direction, next_direction, score, eggs_count, color_index, egg, golden_egg, golden_spawn_time, paused, game_over, death_start, walls, status = state

    if new_direction != OPPOSITE[direction]:
        next_direction = new_direction

    state = (snake, direction, next_direction, score, eggs_count, color_index,
             egg, golden_egg, golden_spawn_time, paused, game_over,
             death_start, walls, status)


def update_game():
    global state

    (snake, direction, next_direction, score, eggs_count, color_index,
     egg, golden_egg, golden_spawn_time, paused, game_over,
     death_start, walls, status) = state

    if paused or game_over:
        return

    # Golden egg expires after 5 seconds
    if golden_egg is not None and golden_spawn_time is not None:
        if time.time() - golden_spawn_time >= 5:
            golden_egg = None
            golden_spawn_time = None
            status = "Golden egg expired. Eat 5 more eggs for another!"

    direction = next_direction
    dx, dy = DIRECTIONS[direction]
    hx, hy = snake[0]
    head = (hx + dx, hy + dy)

    hit_boundary = (
        head[0] < 0 or head[0] >= GRID or
        head[1] < 0 or head[1] >= GRID
    )
    hit_wall = head in walls
    hit_self = head in snake

    if hit_boundary or hit_wall or hit_self:
        game_over = True
        death_start = time.time()
        status = f"Game Over! Final score: {score}"
        state = (snake, direction, next_direction, score, eggs_count, color_index,
                 egg, golden_egg, golden_spawn_time, paused, game_over,
                 death_start, walls, status)
        return

    snake = [head] + snake

    if head == egg:
        score += 1
        eggs_count += 1

        if eggs_count >= 5 and golden_egg is None:
            # Spawn golden egg after every 5 normal eggs.
            eggs_count = 0
            golden_egg = random_free_position(snake, walls, [egg])
            golden_spawn_time = time.time()
            color_index = (color_index + 1) % len(SNAKE_COLORS)
            status = "⭐ GOLDEN EGG! Eat it within 5 seconds for +5 points!"
        else:
            status = f"Egg eaten! {5 - eggs_count} more normal eggs."
        egg = random_free_position(snake, walls, [golden_egg] if golden_egg else None)

    elif golden_egg is not None and head == golden_egg:
        score += 5
        golden_egg = None
        golden_spawn_time = None
        status = "🏆 Golden egg eaten! +5 points!"
        egg = random_free_position(snake, walls)

    else:
        snake.pop()

    state = (snake, direction, next_direction, score, eggs_count, color_index,
             egg, golden_egg, golden_spawn_time, paused, game_over,
             death_start, walls, status)


running = True
last_move = time.time()
while running:
    now = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            new_w = max(MIN_SIZE, event.w)
            new_h = max(MIN_SIZE, event.h)
            screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)

        elif event.type == pygame.KEYDOWN:
            key_map = {
                pygame.K_UP: "UP",
                pygame.K_w: "UP",
                pygame.K_DOWN: "DOWN",
                pygame.K_s: "DOWN",
                pygame.K_LEFT: "LEFT",
                pygame.K_a: "LEFT",
                pygame.K_RIGHT: "RIGHT",
                pygame.K_d: "RIGHT",
            }

            if event.key in key_map:
                set_direction(key_map[event.key])

            elif event.key in (pygame.K_p, pygame.K_SPACE):
                vals = list(state)
                if not vals[10]:
                    vals[9] = not vals[9]
                state = tuple(vals)

            elif event.key == pygame.K_r:
                state = new_game()
                last_move = time.time()

            elif event.key == pygame.K_ESCAPE:
                running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            h = screen.get_height()
            w = screen.get_width()
            size = min(52, max(42, w // 12))
            gap = 8
            total = size * 3 + gap * 2
            x = (w - total) // 2
            y = h - 70

            controls = [
                (pygame.Rect(x + size + gap, y, size, size), "UP"),
                (pygame.Rect(x, y, size, size), "LEFT"),
                (pygame.Rect(x + size + gap, y, size, size), "DOWN"),
                (pygame.Rect(x + 2 * (size + gap), y, size, size), "RIGHT"),
            ]

            for rect, direction_name in controls:
                if rect.collidepoint(mx, my):
                    set_direction(direction_name)

    if now - last_move >= SPEED:
        update_game()
        last_move = now

    vals = state
    (snake, direction, next_direction, score, eggs_count, color_index,
     egg, golden_egg, golden_spawn_time, paused, game_over,
     death_start, walls, status) = vals

    # Status text
    if game_over:
        status_color = (255, 100, 100)
    elif golden_egg is not None:
        remaining = max(0, 5 - (time.time() - golden_spawn_time))
        status = f"⭐ GOLDEN EGG ACTIVE: {remaining:.1f}s | +5 points"
        status_color = GOLD
    else:
        status_color = WHITE

    # Draw
    draw_game(
        snake, egg, golden_egg, walls, score, eggs_count, color_index,
        paused, game_over,
        min(1.0, (time.time() - death_start) / 1.2) if game_over and death_start else 0
    )

    # Status line above controls
    draw_text(
        status,
        SMALL_FONT,
        (screen.get_width() // 2, screen.get_height() - 105),
        status_color,
        center=True,
    )
    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()


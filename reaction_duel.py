import pygame
import random
import time as time_module  # Rename to avoid conflicts
import sys
import os
import ctypes
from ctypes import wintypes


# Initialize Pygame
pygame.init()


###############
# DEBUG CONFIG
###############
# Single authoritative debug flag (removed duplicate block). Set to False for release.
DEBUG = False
# Toggle use of Win32 APIs (ShowWindow/SetWindowPos). Set False to avoid
# platform-specific calls that can crash or reposition the window on some setups.
USE_WIN32 = True if sys.platform.startswith('win') else False
LOG_PATH = os.path.join(os.path.dirname(__file__), "reaction_debug.log")
debug_messages = []  # recent messages for on-screen overlay
# Polling windows and rates for input detection
AGGRESSIVE_POLLING = True
AGGRESSIVE_WINDOW = 0.8  # seconds (increased for better late press detection)
# Toggle use of Win32 APIs (ShowWindow/SetWindowPos). Set False to avoid
# platform-specific calls that can crash or reposition the window on some setups.
# Enable by default on Windows so the Maximize button behaves natively; if you
# see repositioning issues set this to False.
USE_WIN32 = True if sys.platform.startswith('win') else False
LOG_PATH = os.path.join(os.path.dirname(__file__), "reaction_debug.log")
debug_messages = []  # recent messages for on-screen overlay
# Polling windows and rates for input detection
# Keep aggressive polling on by default to reduce input lag
AGGRESSIVE_POLLING = True
AGGRESSIVE_WINDOW = 0.8  # seconds (increased for better late press detection)
TICK_RATE = 480  # Increased polling rate
CHECK_INTERVAL = 0.002  # 2ms check interval for more frequent sampling


def debug_log(msg: str):
    ts = time_module.time()
    line = f"{ts:.6f} {msg}"
    # write to file
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    # print to console when DEBUG
    if DEBUG:
        print(f"[DEBUG] {line}")
    # keep an in-memory overlay buffer
    debug_messages.append(line)
    if len(debug_messages) > 6:
        debug_messages.pop(0)


def draw_debug_overlay():
    if not DEBUG:
        return
    # draw semi-transparent background
    overlay = pygame.Surface((WIDTH, 140), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    WIN.blit(overlay, (10, 10))
    for i, line in enumerate(debug_messages):
        # show only time+msg (truncate the timestamp if needed)
        try:
            _, rest = line.split(' ', 1)
        except Exception:
            rest = line
        txt = TINY.render(rest, True, WHITE)
        WIN.blit(txt, (20, 20 + i * 20))


# Window setup
WIDTH, HEIGHT = 1024, 600  # Increased default size for better visibility
MIN_WIDTH, MIN_HEIGHT = 800, 400  # Minimum window dimensions


# Center the window on startup
os.environ['SDL_VIDEO_CENTERED'] = '1'
WIN = pygame.display.set_mode((WIDTH, HEIGHT),
                            pygame.RESIZABLE |
                            pygame.DOUBLEBUF |
                            pygame.HWSURFACE)
pygame.display.set_caption("Reaction Duel")


# Fonts and colors - Modern sleek design
FONT = pygame.font.SysFont("segoe ui", 64, bold=True)
SMALL = pygame.font.SysFont("segoe ui", 28)
TINY = pygame.font.SysFont("segoe ui", 18)


# Modern color palette
WHITE = (255, 255, 255)
BLACK = (15, 15, 20)  # Slightly softer than pure black
DARK_BG = (20, 24, 35)  # Deep blue-black background
CARD_BG = (30, 35, 50)  # Card/button background
ACCENT_BLUE = (64, 156, 255)  # Bright modern blue
ACCENT_CYAN = (0, 229, 255)  # Vibrant cyan
ACCENT_GREEN = (16, 185, 129)  # Modern teal-green
ACCENT_PURPLE = (139, 92, 246)  # Modern purple
ACCENT_ORANGE = (251, 146, 60)  # Modern orange
ACCENT_RED = (239, 68, 68)  # Modern red
ACCENT_YELLOW = (250, 204, 21)  # Modern yellow
TEXT_GRAY = (156, 163, 175)  # Muted text
HOVER_HIGHLIGHT = (50, 58, 82)  # Subtle hover state


# Legacy color aliases for compatibility
RED = ACCENT_RED
GREEN = ACCENT_GREEN
BLUE = ACCENT_BLUE
YELLOW = ACCENT_YELLOW
ORANGE = ACCENT_ORANGE


# Game settings
class GameSettings:
    def __init__(self):
        self.points_to_win = 10
        self.num_players = 2
        # Default keys for all possible players
        self.default_keys = [
            pygame.K_a,    # Player 1: A
            pygame.K_l,    # Player 2: L
            pygame.K_q,    # Player 3: Q
            pygame.K_p,    # Player 4: P
            pygame.K_z,    # Player 5: Z
            pygame.K_m,    # Player 6: M
            pygame.K_c,    # Player 7: C
            pygame.K_k     # Player 8: K
        ]
        self.player_keys = self.default_keys[:2]  # Start with 2 players
        self.player_key_names = [pygame.key.name(key).upper() for key in self.player_keys]
        self.fullscreen = False
        self.paused = False
        self.windowed_size = (WIDTH, HEIGHT)
       
    def add_player(self):
        if self.num_players < 8:
            self.num_players += 1
            self.player_keys.append(self.default_keys[self.num_players - 1])
            self.player_key_names.append(pygame.key.name(self.default_keys[self.num_players - 1]).upper())
           
    def remove_player(self):
        if self.num_players > 2:
            self.num_players -= 1
            self.player_keys.pop()
            self.player_key_names.pop()
           
    def toggle_fullscreen(self):
        global WIDTH, HEIGHT, WIN
        # Simpler, more reliable fullscreen toggle using SDL fullscreen/scaling.
        info = pygame.display.Info()
        if not self.fullscreen:
            # Prefer SDL FULLSCREEN|SCALED so the window fills the screen and
            # scaling preserves aspect ratio. If that fails, fall back to a
            # borderless NOFRAME window sized to the display.
            self.windowed_size = (WIDTH, HEIGHT)
            screen_w, screen_h = info.current_w, info.current_h
            try:
                WIN = pygame.display.set_mode((screen_w, screen_h), pygame.FULLSCREEN | pygame.SCALED)
                WIDTH, HEIGHT = screen_w, screen_h
                self.fullscreen = True
            except Exception:
                try:
                    WIN = pygame.display.set_mode((screen_w, screen_h), pygame.NOFRAME)
                    # Try to position at 0,0 when possible
                    if os.name == 'nt' and USE_WIN32:
                        try:
                            hwnd = pygame.display.get_wm_info().get('window')
                            if hwnd:
                                user32 = ctypes.windll.user32
                                SWP_NOZORDER = 0x0004
                                user32.SetWindowPos(hwnd, 0, 0, 0, screen_w, screen_h, SWP_NOZORDER)
                        except Exception as e:
                            debug_log(f"toggle_fullscreen SetWindowPos failed: {e}")
                    WIDTH, HEIGHT = screen_w, screen_h
                    self.fullscreen = True
                except Exception:
                    debug_log("toggle_fullscreen: failed to enter fullscreen")
        else:
            # Exit fullscreen and restore previous window size
            WIDTH, HEIGHT = getattr(self, 'windowed_size', (1024, 600))
            WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            pygame.display.set_caption("Reaction Duel")
            self.fullscreen = False
        # Allow the system to process the mode change
        pygame.event.pump()
        pygame.display.flip()
        debug_log(f"toggle_fullscreen: fullscreen={self.fullscreen}, WIDTH={WIDTH}, HEIGHT={HEIGHT}")
        return WIN
   
    def maximize_window(self):
        """Maximize the window (non-fullscreen) using Windows API when available.
        This uses ShowWindow(SW_MAXIMIZE) to give a native maximize behavior on Windows.
        """
        global WIDTH, HEIGHT, WIN
        try:
            info = pygame.display.Info()
            # Try Windows-specific maximize via user32
            if os.name == 'nt':
                hwnd = pygame.display.get_wm_info().get('window')
                if hwnd and USE_WIN32:
                    user32 = ctypes.windll.user32
                    SW_MAXIMIZE = 3
                    # Use native maximize without recreating the SDL window. Recreating
                    # the window after ShowWindow can cause it to reappear at the
                    # default position (top-left) which was causing the reported issue.
                    user32.ShowWindow(hwnd, SW_MAXIMIZE)
                    # Allow the system to process the resize
                    pygame.event.pump()
                    # Update our stored size to match the new window size without
                    # calling set_mode again (avoids moving the window)
                    try:
                        WIDTH, HEIGHT = pygame.display.get_window_size()
                    except Exception:
                        WIDTH, HEIGHT = info.current_w, info.current_h
                    # Don't recreate the window surface here; just flip to ensure
                    # the content is updated in the maximized window.
                    try:
                        pygame.display.flip()
                    except Exception:
                        pass
                    debug_log(f"maximize_window: maximized WIDTH={WIDTH}, HEIGHT={HEIGHT}")
                    return WIN
        except Exception as e:
            debug_log(f"maximize_window failed: {e}")
        # Fallback: resize to display size (may include taskbar)
        try:
            WIDTH, HEIGHT = info.current_w, info.current_h
            # Fallback: recreate window at display size if native maximize failed
            WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            pygame.event.pump()
            debug_log(f"maximize_window fallback: WIDTH={WIDTH}, HEIGHT={HEIGHT}")
        except Exception as e:
            debug_log(f"maximize_window fallback failed: {e}")
        return WIN


settings = GameSettings()


# Button class for menu
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.action = action


    def draw(self, surface):
        try:
            # Modern card-style button with shadow
            shadow_rect = self.rect.copy()
            shadow_rect.y += 3
            pygame.draw.rect(surface, (0, 0, 0, 60), shadow_rect, border_radius=12)
           
            # Draw button with modern styling
            pygame.draw.rect(surface, self.current_color, self.rect, border_radius=12)
           
            # Subtle border for depth
            border_color = tuple(min(255, c + 30) for c in self.current_color)
            pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=12)


            # Draw centered text with slight boldness
            text_surface = SMALL.render(self.text, True, WHITE)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
        except Exception as e:
            debug_log(f"Button draw error: {e}")


    def handle_event(self, event):
        """Handle hover and left-click; return action result or None."""
        try:
            if not hasattr(event, "type"):
                debug_log("Event has no type attribute")
                return None


            # Hover handling
            if event.type == pygame.MOUSEMOTION:
                try:
                    if hasattr(event, "pos") and self.rect.collidepoint(event.pos):
                        self.current_color = self.hover_color
                    else:
                        self.current_color = self.color
                except Exception as e:
                    debug_log(f"Button hover error: {e}")
                    self.current_color = self.color
                return None


            # Left-click handling
            if event.type == pygame.MOUSEBUTTONDOWN:
                try:
                    if getattr(event, "button", 1) != 1:
                        return None
                    if not hasattr(event, "pos") or not self.rect.collidepoint(event.pos):
                        return None
                    if self.action:
                        try:
                            result = self.action()
                            debug_log(f"Button '{self.text}' action returned: {result}")
                            return result
                        except Exception as e:
                            debug_log(f"Button '{self.text}' action error: {e}")
                            return None
                except Exception as e:
                    debug_log(f"Button click handling error: {e}")
                    return None


            return None
        except Exception as e:
            debug_log(f"Button handle_event error: {e}")
            return None


clock = pygame.time.Clock()


def draw_gradient_background(surface, color1, color2):
    """Draw a smooth vertical gradient background."""
    for y in range(HEIGHT):
        blend = y / HEIGHT
        r = int(color1[0] * (1 - blend) + color2[0] * blend)
        g = int(color1[1] * (1 - blend) + color2[1] * blend)
        b = int(color1[2] * (1 - blend) + color2[2] * blend)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))


def draw_text(text, color, y_offset=0, size="normal"):
    font = TINY if size == "tiny" else (SMALL if size == "small" else FONT)
    text_surface = font.render(text, True, color, None)
    text_surface.set_alpha(255)
    text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    WIN.blit(text_surface, text_rect)


def show_rules():
    draw_gradient_background(WIN, DARK_BG, (25, 30, 45))
    draw_text("Game Rules", ACCENT_CYAN, -180)
    rules = [
        "1. Press your key only when 'GO!' is GREEN.",
        "2. A non-GREEN 'GO!' is a trap — pressing it costs 1 point.",
        "3. Pressing during 'Wait for it...' is a false start (-1 point).",
        "4. On GREEN 'GO!', the fastest player scores 1 point.",
        "5. Exact ties or no response: no points awarded.",
        "6. First to reach the target points wins. Press ESC to pause.",
    ]
    for i, rule in enumerate(rules):
        draw_text(rule, TEXT_GRAY, -100 + (i * 38), "small")
    draw_text("Press ENTER to return", ACCENT_PURPLE, 180, "small")
    pygame.display.flip()
   
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False
        clock.tick(30)


def get_key_name(key):
    name = pygame.key.name(key).upper()
    if len(name) == 1:
        return name
    return name.split('_')[-1]


def wait_for_key():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key not in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE]:
                    return event.key
        clock.tick(30)


def show_controls():
    global WIN
    draw_gradient_background(WIN, DARK_BG, (25, 30, 45))
    draw_text("Game Controls", ACCENT_CYAN, -180)
    controls = [
        "ESC - Pause Game",
        f"Player Keys: {', '.join(settings.player_key_names)}",
        "SPACE - Continue/Next Round",
        "During Menu:",
        "Left Click - Select Options",
        "Up/Down - Adjust Values"
    ]
    for i, control in enumerate(controls):
        draw_text(control, TEXT_GRAY, -100 + (i * 38), "small")
    draw_text("Press ENTER to return", ACCENT_PURPLE, 180, "small")
    pygame.display.flip()
   
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False
        clock.tick(30)


def show_menu():
    global WIN, WIDTH, HEIGHT
    menu_state = "main"
    buttons = []
   
    def create_main_buttons():
        button_w, button_h = 280, 52  # Modern proportions
        start_y = HEIGHT // 2 - 180
        spacing = 62
        return [
            Button(WIDTH//2 - button_w//2, start_y, button_w, button_h,
                  f"Points to Win: {settings.points_to_win}", CARD_BG, HOVER_HIGHLIGHT,
                  lambda: "points"),
            Button(WIDTH//2 - button_w//2, start_y + spacing, button_w, button_h,
                  f"Players: {settings.num_players}", CARD_BG, HOVER_HIGHLIGHT,
                  lambda: "players"),
            Button(WIDTH//2 - button_w//2, start_y + spacing*2, button_w, button_h,
                  "Set Player Keys", CARD_BG, HOVER_HIGHLIGHT,
                  lambda: "keys"),
            Button(WIDTH//2 - button_w//2, start_y + spacing*3, button_w, button_h,
                  "View Rules", CARD_BG, HOVER_HIGHLIGHT,
                  show_rules),
            Button(WIDTH//2 - button_w//2, start_y + spacing*4, button_w, button_h,
                  "View Controls", CARD_BG, HOVER_HIGHLIGHT,
                  show_controls),
            Button(WIDTH//2 - button_w//2, start_y + spacing*5, button_w, button_h,
                "Start Game", ACCENT_GREEN, (20, 160, 110),
                lambda: "start"),
            Button(WIDTH//2 - button_w//2, start_y + spacing*6, button_w, button_h,
                "Quit Game", ACCENT_RED, (200, 50, 50),
                lambda: "quit")
        ]
   
    while True:
        # Keep our stored size in sync with the real window in case user used
        # OS controls (maximize/restore) outside of pygame events.
        sync_window_size()
        draw_gradient_background(WIN, DARK_BG, (15, 20, 35))
       
        if menu_state == "main":
            buttons = create_main_buttons()
            # Title with modern styling
            draw_text("REACTION DUEL", ACCENT_CYAN, -260)
            current_keys = " | ".join([f"P{i+1}: {key}" for i, key in enumerate(settings.player_key_names)])
            draw_text(current_keys, TEXT_GRAY, -210, "tiny")
           
            # Draw all buttons
            for button in buttons:
                button.draw(WIN)
               
            # draw debug overlay if enabled
            draw_debug_overlay()
            pygame.display.flip()


            for event in pygame.event.get():
                # Global event handling
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()


                # Keyboard shortcuts
                if event.type == pygame.KEYDOWN:
                    # Fullscreen removed: ignore F11
                    if event.key == pygame.K_F11:
                        pass
                    elif event.key == pygame.K_1:
                        menu_state = "points"
                    elif event.key == pygame.K_2:
                        menu_state = "players"
                    elif event.key == pygame.K_3:
                        menu_state = "keys"
                    elif event.key == pygame.K_4:
                        show_rules()
                    elif event.key == pygame.K_SPACE:
                        return True
                    elif event.key == pygame.K_ESCAPE:
                        return False


                # Handle mouse/button events
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    for button in buttons:
                        result = button.handle_event(event)
                        if result:
                            if result == 'start':
                                return True
                            elif result == 'quit':
                                pygame.quit()
                                sys.exit()
                            elif result == 'points':
                                menu_state = 'points'
                            elif result == 'players':
                                menu_state = 'players'
                            elif result == 'keys':
                                menu_state = 'keys'
                            # fullscreen button removed — ignore
                            elif result == 'maximize':
                                WIN = settings.maximize_window()
                                buttons = create_main_buttons()


        elif menu_state == "points":
            # Compact modal for editing points to win
            def edit_points():
                current = str(settings.points_to_win)
                while True:
                    sync_window_size()
                    draw_gradient_background(WIN, DARK_BG, (20, 25, 40))
                    draw_text("Points to Win", ACCENT_CYAN, -130)
                    draw_text("Type a number (1-99)", TEXT_GRAY, -90, "tiny")


                    # Value display (compact modern)
                    button_w, button_h = 140, 56
                    center_x = WIDTH // 2
                    value_y = HEIGHT // 2 - 20
                    value_text = current + "_" if current else "_"
                    value_button = Button(center_x - button_w//2, value_y, button_w, button_h,
                                          value_text, CARD_BG, HOVER_HIGHLIGHT, None)


                    confirm_button = Button(center_x - 115, value_y + 90, 105, 44,
                                            "Done", ACCENT_GREEN, (20, 160, 110), lambda: "done")
                    cancel_button = Button(center_x + 10, value_y + 90, 105, 44,
                                           "Cancel", ACCENT_RED, (200, 50, 50), lambda: "cancel")


                    for btn in (value_button, confirm_button, cancel_button):
                        btn.draw(WIN)
                    pygame.display.flip()


                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()
                        if event.type == pygame.KEYDOWN:
                            try:
                                if event.key == pygame.K_RETURN:
                                    if current:
                                        try:
                                            val = max(1, min(99, int(current)))
                                            return val
                                        except Exception:
                                            pass
                                elif event.key == pygame.K_ESCAPE:
                                    return None
                                elif event.key == pygame.K_BACKSPACE:
                                    current = current[:-1]
                                else:
                                    ch = event.unicode
                                    if ch and ch.isnumeric() and len(current) < 2:
                                        current += ch
                            except Exception as e:
                                debug_log(f"edit_points key handling error: {e}")
                        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                            for btn in (confirm_button, cancel_button):
                                res = btn.handle_event(event)
                                if res == "done":
                                    if current:
                                        try:
                                            val = max(1, min(99, int(current)))
                                            return val
                                        except Exception:
                                            pass
                                elif res == "cancel":
                                    return None


                    clock.tick(60)


            new_value = edit_points()
            if new_value is not None:
                settings.points_to_win = new_value
            menu_state = "main"


        elif menu_state == "players":
            # Compact modal for editing number of players (2-8)
            def edit_players():
                current = str(settings.num_players)
                while True:
                    sync_window_size()
                    draw_gradient_background(WIN, DARK_BG, (20, 25, 40))
                    draw_text("Number of Players", ACCENT_CYAN, -130)
                    draw_text("(2-8 players)", TEXT_GRAY, -90, "tiny")


                    # Value display (compact modern)
                    button_w, button_h = 120, 52
                    center_x = WIDTH // 2
                    value_y = HEIGHT // 2 - 20
                    value_text = current + "_" if current else "_"
                    value_button = Button(center_x - button_w//2, value_y, button_w, button_h,
                                          value_text, CARD_BG, HOVER_HIGHLIGHT, None)


                    inc_button = Button(center_x + button_w//2 + 10, value_y, 48, 48, "+", ACCENT_BLUE, (50, 130, 220), lambda: "inc")
                    dec_button = Button(center_x - button_w//2 - 58, value_y, 48, 48, "-", ACCENT_BLUE, (50, 130, 220), lambda: "dec")
                    done_button = Button(center_x - 115, value_y + 90, 105, 42, "Done", ACCENT_GREEN, (20, 160, 110), lambda: "done")
                    cancel_button = Button(center_x + 10, value_y + 90, 105, 42, "Cancel", ACCENT_RED, (200, 50, 50), lambda: "cancel")


                    for btn in (value_button, inc_button, dec_button, done_button, cancel_button):
                        btn.draw(WIN)
                    pygame.display.flip()


                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_RETURN:
                                try:
                                    v = max(2, min(8, int(current)))
                                    return v
                                except Exception:
                                    pass
                            elif event.key == pygame.K_ESCAPE:
                                return None
                            elif event.key == pygame.K_UP:
                                cur = int(current)
                                if cur < 8:
                                    current = str(cur + 1)
                            elif event.key == pygame.K_DOWN:
                                cur = int(current)
                                if cur > 2:
                                    current = str(cur - 1)
                            elif event.unicode.isnumeric():
                                # single digit only
                                current = event.unicode
                        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                            for btn in (inc_button, dec_button, done_button, cancel_button):
                                res = btn.handle_event(event)
                                if res == "inc":
                                    cur = int(current)
                                    if cur < 8:
                                        current = str(cur + 1)
                                elif res == "dec":
                                    cur = int(current)
                                    if cur > 2:
                                        current = str(cur - 1)
                                elif res == "done":
                                    try:
                                        v = max(2, min(8, int(current)))
                                        return v
                                    except Exception:
                                        pass
                                elif res == "cancel":
                                    return None


                    clock.tick(60)


            new_num = edit_players()
            if new_num is not None and new_num != settings.num_players:
                # Adjust player keys list when number changes
                old = settings.num_players
                settings.num_players = new_num
                if new_num > old:
                    # add defaults
                    for i in range(old, new_num):
                        settings.player_keys.append(settings.default_keys[i])
                        settings.player_key_names.append(pygame.key.name(settings.default_keys[i]).upper())
                else:
                    # trim lists
                    settings.player_keys = settings.player_keys[:new_num]
                    settings.player_key_names = settings.player_key_names[:new_num]
            menu_state = "main"


        elif menu_state == "keys":
            # Compact modal for editing player keys
            def edit_keys():
                while True:
                    sync_window_size()
                    draw_gradient_background(WIN, DARK_BG, (20, 25, 40))
                    button_w, button_h = 260, 46
                    center_x = WIDTH // 2
                    # Dynamic spacing to prevent cutoff with many players
                    start_y = max(HEIGHT // 2 - (settings.num_players * 26), 120)
                    # Place header above the first button with safe margin
                    header_y = start_y - 60
                    draw_text("Player Keys", ACCENT_CYAN, header_y - (HEIGHT // 2))


                    buttons = []
                    player_colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_ORANGE, ACCENT_CYAN, ACCENT_YELLOW, ACCENT_RED, (100, 200, 255)]
                    for i in range(settings.num_players):
                        y_pos = start_y + (i * 54)
                        text = f"Player {i+1}: {settings.player_key_names[i]}"
                        color = player_colors[i % len(player_colors)]
                        hover = tuple(max(0, c - 30) for c in color)
                        btn = Button(center_x - button_w//2, y_pos, button_w, button_h, text, color, hover, lambda i=i: i)
                        buttons.append(btn)


                    done_btn = Button(center_x - 90, start_y + settings.num_players * 54 + 20, 180, 44, "Done", ACCENT_GREEN, (20, 160, 110), lambda: "done")
                    for btn in buttons:
                        btn.draw(WIN)
                    done_btn.draw(WIN)
                    pygame.display.flip()


                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                            return
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            return
                        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                            for idx, btn in enumerate(buttons):
                                res = btn.handle_event(event)
                                if isinstance(res, int):
                                    # Enter key-capture mode for this player
                                    player_idx = res
                                    assigned = capture_key_for_player(player_idx)
                                    if assigned is not None:
                                        settings.player_keys[player_idx] = assigned
                                        settings.player_key_names[player_idx] = pygame.key.name(assigned).upper()
                            if done_btn.handle_event(event) == "done":
                                return


                    clock.tick(60)


            def capture_key_for_player(player_idx):
                # Prompt and wait for a key press (or ESC to cancel)
                prompt_shown = False
                while True:
                    sync_window_size()
                    if not prompt_shown:
                        draw_gradient_background(WIN, DARK_BG, (20, 25, 40))
                        draw_text(f"Press new key for Player {player_idx + 1}", ACCENT_CYAN, -50, "small")
                        draw_text("Press ESC to cancel", TEXT_GRAY, 10, "tiny")
                        pygame.display.flip()
                        prompt_shown = True


                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                return None
                            if event.key != pygame.K_RETURN:
                                # Prevent duplicate assignment
                                if event.key in settings.player_keys:
                                    debug_log(f"Key {pygame.key.name(event.key)} already assigned")
                                    return None
                                return event.key
                    clock.tick(60)


            edit_keys()
            menu_state = "main"


        clock.tick(30)


def wait_for_go(round_num, scores):
    """Pre-round phase. Waits a randomized time, detects false starts.
    Returns a tuple (result, key) where result is one of:
      - "menu" (user requested menu)
      - "false_start" (a player pressed early; key is the pygame key pressed)
      - "go" (safe to proceed to reaction phase; key is None)
    """
    sync_window_size()
    draw_gradient_background(WIN, DARK_BG, (25, 15, 35))
    draw_text(f"Round {round_num}", ACCENT_PURPLE, -140)
    draw_text("Wait for it...", ACCENT_YELLOW, -90, "small")
    pygame.display.flip()


    # Random waiting interval (players must NOT press during this time)
    wait_time = random.uniform(1.0, 2.2)
    start = time_module.perf_counter()
    while time_module.perf_counter() - start < wait_time:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if show_pause_menu() == "menu":
                        return ("menu", None)
                if event.key in settings.player_keys:
                    # False start detected
                    return ("false_start", event.key)
            handle_window_events(event)
        clock.tick(120)


    # Show GO with color variation (80% green safe, 20% trap colors)
    is_trap = random.random() < 0.2
    if is_trap:
        trap_colors = [
            ((80, 10, 40), (120, 20, 60), ACCENT_RED, "GO!"),      # Red trap
            ((80, 60, 10), (120, 100, 20), ACCENT_ORANGE, "GO!"),  # Orange trap
            ((10, 10, 80), (20, 20, 120), ACCENT_BLUE, "GO!"),     # Blue trap
            ((80, 10, 80), (120, 20, 120), ACCENT_PURPLE, "GO!"),  # Purple trap
        ]
        bg1, bg2, text_color, text = random.choice(trap_colors)
        draw_gradient_background(WIN, bg1, bg2)
        draw_text(text, text_color, -50)
        go_color = text_color  # Track the color for reaction_phase
    else:
        # Safe green GO
        draw_gradient_background(WIN, (10, 80, 40), (20, 120, 60))
        draw_text("GO!", ACCENT_GREEN, -50)
        go_color = ACCENT_GREEN
   
    pygame.display.flip()
    # small pause so GO is visible before reaction_phase begins
    time_module.sleep(0.08)
    return ("go", go_color)


def reaction_phase(round_num, scores, go_color=None):
    """Handles the reaction timing after GO. Returns (status, players, reaction_time)
    status: 'winner', 'tie', 'fault', 'no_response', or 'menu'
    players: list of player indices (for winner/fault) or None
    reaction_time: float time (for winner/fault)
    go_color: the color shown (GREEN is safe, others are traps)
    """
    # Screen already drawn by wait_for_go, just start timing
    reaction_start = time_module.perf_counter()
    player_times = [None] * settings.num_players
    EPS = 0.0006
   
    # Determine if this was a safe round or trap
    if go_color is None:
        go_color = ACCENT_GREEN  # Default to safe


    last_check = reaction_start
    timeout = 2.0  # no response timeout


    while True:
        # Event handling for immediate keydown detection
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if show_pause_menu() == "menu":
                        return ("menu", None, None)
                if event.key in settings.player_keys:
                    idx = settings.player_keys.index(event.key)
                    if player_times[idx] is None:
                        player_times[idx] = time_module.perf_counter() - reaction_start
                        debug_log(f"KEYDOWN detected for P{idx+1} at {player_times[idx]:.6f}")
            handle_window_events(event)


        # Polling to catch held keys
        current_time = time_module.perf_counter()
        if current_time - last_check >= CHECK_INTERVAL:
            last_check = current_time
            keys = pygame.key.get_pressed()
            now = current_time - reaction_start
            for i, k in enumerate(settings.player_keys):
                if player_times[i] is None and keys[k]:
                    player_times[i] = now
                    debug_log(f"POLL detected for P{i+1} at {now:.6f}")


            pressed = [(i, t) for i, t in enumerate(player_times) if t is not None]
            pressed_count = len(pressed)


            # No presses yet: handle timeouts
            elapsed = current_time - reaction_start
            if pressed_count == 0 and elapsed > timeout:
                return ("no_response", None, None)


            if pressed_count > 0:
                # Check if this was a trap round (non-green GO)
                if go_color != ACCENT_GREEN:
                    # Trap round: anyone who pressed gets a fault
                    faulted = [i for i, _ in pressed]
                    if len(faulted) == 1:
                        return ("fault", faulted, pressed[0][1])
                    else:
                        # Multiple faulted: find slowest (last to press loses point)
                        times = [t for _, t in pressed]
                        max_time = max(times)
                        slowest = [i for i, t in pressed if abs(t - max_time) < EPS]
                        if len(slowest) > 1:
                            return ("tie", None, None)
                        else:
                            return ("fault", slowest, max_time)
                else:
                    # Safe green round: determine fastest
                    times = [(i, t) for i, t in pressed]
                    min_time = min(t for _, t in times)
                    fastest = [i for i, t in times if abs(t - min_time) < EPS]
                    if len(fastest) > 1:
                        return ("tie", None, None)
                    else:
                        return ("winner", fastest, min_time)


        # adapt sleeping
        elapsed = time_module.perf_counter() - reaction_start
        if elapsed < AGGRESSIVE_WINDOW:
            pygame.event.pump()
            time_module.sleep(0.001)
        else:
            clock.tick(TICK_RATE)




def show_round_winner(winners, reaction_time=None, false_start=False, wait_for_input=True):
    global WIN
    draw_gradient_background(WIN, DARK_BG, (30, 20, 40))
    if false_start:
        # winners may be a key value, a player index, or a list containing the index
        player_idx = None
        if isinstance(winners, list) and len(winners) > 0:
            # assume list of indices
            player_idx = winners[0]
        else:
            try:
                # if winners is a key code, map to index
                player_idx = settings.player_keys.index(winners)
            except Exception:
                player_idx = None
        if player_idx is not None:
            player_num = player_idx + 1
            draw_text(f"Player {player_num} False Start!", ACCENT_RED, -60)
        else:
            draw_text("False Start!", ACCENT_RED, -60)
    else:
        # Treat an empty list as an explicit tie/no-points result
        if isinstance(winners, list) and len(winners) == 0:
            draw_text("Tie! No points awarded.", ACCENT_YELLOW, -60)
        elif winners is None:
            draw_text("No Response!", ACCENT_ORANGE, -60)
        else:
            if len(winners) == 1:
                player_num = winners[0] + 1
                player_colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_ORANGE, ACCENT_CYAN]
                color = player_colors[winners[0] % len(player_colors)]
                draw_text(f"Player {player_num} Wins!", color, -70)
                if reaction_time is not None:
                    draw_text(f"{reaction_time:.3f}s", ACCENT_CYAN, 10, "small")
            else:
                winners_text = ", ".join([f"P{w+1}" for w in winners])
                draw_text(f"{winners_text} Win!", ACCENT_YELLOW, -60)
               
    draw_text("Press SPACE for next round", TEXT_GRAY, 160, "tiny")
    draw_text("Press ESC to pause", TEXT_GRAY, 190, "tiny")
    pygame.display.flip()


    # Wait for restart (or auto-advance when wait_for_input is False)
    if not wait_for_input:
        # Briefly show the result then continue automatically
        pygame.display.flip()
        time_module.sleep(1.2)
        return "continue"


    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_ESCAPE and not settings.paused:
                    settings.paused = True
                    result = show_pause_menu()
                    if result == "menu":
                        return "menu"
                    settings.paused = False
            handle_window_events(event)
        clock.tick(30)
    return "continue"


def show_match_winner(scores):
    global WIN
    pygame.event.clear()  # Clear any pending events
    draw_gradient_background(WIN, (30, 20, 50), (50, 30, 70))
    max_score = max(scores)
    winners = [i+1 for i, score in enumerate(scores) if score == max_score]


    if len(winners) == 1:
        player_colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_ORANGE, ACCENT_CYAN]
        color = player_colors[(winners[0] - 1) % len(player_colors)]
        draw_text(f"🏆 Player {winners[0]} Wins! 🏆", color, -100)
    else:
        winners_text = ", ".join([f"P{w}" for w in winners])
        draw_text(f"It's a Draw! {winners_text}", ACCENT_YELLOW, -100)


    score_text = " | ".join([f"P{i+1}: {score}" for i, score in enumerate(scores)])
    draw_text(f"Final Scores: {score_text}", WHITE, -20, "small")
    draw_text("Press SPACE to Play Again", ACCENT_GREEN, 80, "small")
    draw_text("Press ENTER to Return to Menu", TEXT_GRAY, 120, "tiny")
    pygame.display.flip()


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pygame.event.clear()
                    return False  # Start new game
                elif event.key == pygame.K_RETURN:
                    pygame.event.clear()
                    return True  # Return to menu
            handle_window_events(event)
        clock.tick(30)
def show_pause_menu():
    global WIN
    try:
        # Store current screen content
        old_screen = WIN.copy()


        # Create modern pause overlay with blur effect (simulated)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 20, 30, 200))  # Deep semi-transparent overlay


        # Clear all pending events and wait a moment
        pygame.event.clear()
        time_module.sleep(0.2)  # Longer delay to ensure key release


        paused = True
        while paused:
            # Draw pause menu
            try:
                WIN.blit(old_screen, (0, 0))  # Restore background
            except Exception:
                # If the surface can't be blitted, fill dark as fallback
                draw_gradient_background(WIN, DARK_BG, (25, 30, 45))
            WIN.blit(overlay, (0, 0))  # Add overlay
            draw_text("PAUSED", ACCENT_CYAN, -60)
            draw_text("Press ESC to Resume", ACCENT_GREEN, 20, "small")
            draw_text("Press M for Menu", TEXT_GRAY, 60, "small")
            pygame.display.flip()


            # Wait for a key press
            event = pygame.event.wait()


            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = False
                elif event.key == pygame.K_m:
                    # Clear events and return to menu
                    pygame.event.clear()
                    # Ensure paused flag is cleared globally
                    settings.paused = False
                    return "menu"


        # Clear events before resuming
        pygame.event.clear()
        # Restore the screen
        WIN.blit(old_screen, (0, 0))
        pygame.display.flip()
        return "resume"
    except Exception as e:
        # Log and recover: return to menu to avoid getting stuck
        debug_log(f"show_pause_menu exception: {e}")
        try:
            pygame.event.clear()
        except Exception:
            pass
        settings.paused = False
        return "menu"


def handle_window_events(event):
    global WIN, WIDTH, HEIGHT
    if event.type == pygame.VIDEORESIZE:
        if not settings.fullscreen:
            # Enforce minimum size
            WIDTH = max(event.w, MIN_WIDTH)
            HEIGHT = max(event.h, MIN_HEIGHT)
            # Set new window size (avoid setting SDL env vars at runtime)
            WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            if DEBUG:
                debug_log(f"VIDEORESIZE -> WIDTH={WIDTH}, HEIGHT={HEIGHT}")
    # Note: Some pygame builds don't expose WINDOWEVENT — manual maximize is handled via VIDEORESIZE
    elif event.type == pygame.KEYDOWN:
        # Fullscreen toggle removed — do not handle F11 here
        pass


def sync_window_size():
    """Detect when the OS/resizer changes the real window size (e.g. manual maximize)
    and update WIDTH/HEIGHT accordingly without recreating the window surface.
    Returns True if a size change was synced.
    """
    global WIDTH, HEIGHT, WIN
    try:
        # Some SDL builds expose get_window_size; fallback to surface size
        try:
            w, h = pygame.display.get_window_size()
        except Exception:
            surf = pygame.display.get_surface()
            if surf:
                w, h = surf.get_size()
            else:
                return False


        # Only update when not fullscreen (we manage fullscreen separately)
        if not settings.fullscreen and (w != WIDTH or h != HEIGHT):
            WIDTH = max(w, MIN_WIDTH)
            HEIGHT = max(h, MIN_HEIGHT)
            debug_log(f"sync_window_size: detected external size change -> WIDTH={WIDTH}, HEIGHT={HEIGHT}")
            return True
    except Exception as e:
        debug_log(f"sync_window_size failed: {e}")
    return False


def main():
    while True:
        # Show menu
        if not show_menu():
            pygame.quit()
            sys.exit()
       
        # Initialize scores for all players
        scores = [0] * settings.num_players
        round_num = 1
       
        # Main game loop
        while True:
            # Keep our stored size synced when entering a new round
            sync_window_size()
            # Wait for the GO signal
            result, go_color = wait_for_go(round_num, scores)


            if result == "menu":
                break


            if result == "false_start":
                # Find which player false started
                if go_color in settings.player_keys:
                    false_starter = settings.player_keys.index(go_color)
                    # Deduct a point from the offending player (not below 0)
                    scores[false_starter] = max(0, scores[false_starter] - 1)


                    # If this round causes the match to end, skip round screen and show match winner
                    match_over = max(scores) >= settings.points_to_win
                    if match_over:
                        return_to_menu = show_match_winner(scores)
                        if return_to_menu:
                            break
                        else:
                            # Start new match immediately (reset scores and continue)
                            scores = [0] * settings.num_players
                            round_num = 1
                            continue
                    else:
                        action = show_round_winner([false_starter], None, True)
                        if action == "menu":
                            break


            else:
                # Regular round (pass go_color to reaction_phase)
                status, players, reaction_time = reaction_phase(round_num, scores, go_color)
                if status == "menu":
                    break


                if status == "no_response":
                    # No one responded in time
                    action = show_round_winner(None, None, False)
                    if action == "menu":
                        break
                elif status == "tie":
                    # Exact tie -- no points awarded
                    action = show_round_winner([], None, False)
                    if action == "menu":
                        break
                elif status == "winner":
                    # Award point(s) to winner(s)
                    for winner in players:
                        scores[winner] += 1
                    match_over = max(scores) >= settings.points_to_win
                    if match_over:
                        return_to_menu = show_match_winner(scores)
                        if return_to_menu:
                            break
                        else:
                            scores = [0] * settings.num_players
                            round_num = 1
                            continue
                    else:
                        action = show_round_winner(players, reaction_time, False)
                        if action == "menu":
                            break
                elif status == "fault":
                    # Deduct a point from the offending player(s)
                    for offender in players:
                        scores[offender] = max(0, scores[offender] - 1)
                    match_over = max(scores) >= settings.points_to_win
                    if match_over:
                        return_to_menu = show_match_winner(scores)
                        if return_to_menu:
                            break
                        else:
                            scores = [0] * settings.num_players
                            round_num = 1
                            continue
                    else:
                        # Show fault screen
                        action = show_round_winner(players, reaction_time, True)
                        if action == "menu":
                            break


            round_num += 1
       
        # End of match (multi-player logic handled above)


if __name__ == "__main__":
    main()



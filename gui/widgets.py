import pygame
from typing import Callable, Optional, Tuple

# UI Dark Theme Palette (Smart City Aesthetic)
COLOR_BG_DARK = (18, 22, 32)
COLOR_PANEL_BG = (28, 34, 48)
COLOR_CARD_BG = (36, 44, 62)
COLOR_TEXT_WHITE = (240, 244, 250)
COLOR_TEXT_MUTED = (140, 155, 175)
COLOR_ACCENT_BLUE = (0, 162, 255)
COLOR_ACCENT_GREEN = (0, 220, 130)
COLOR_ACCENT_RED = (255, 75, 75)
COLOR_ACCENT_ORANGE = (255, 160, 40)
COLOR_ACCENT_PURPLE = (180, 90, 240)

class Button:
    def __init__(self, rect: Tuple[int, int, int, int], text: str, callback: Optional[Callable] = None,
                 bg_color=COLOR_CARD_BG, hover_color=COLOR_ACCENT_BLUE, text_color=COLOR_TEXT_WHITE):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.active = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.hover_color if (self.is_hovered or self.active) else self.bg_color

        # Draw rounded rectangle
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (60, 75, 100), self.rect, width=1, border_radius=8)

        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

class Slider:
    def __init__(self, rect: Tuple[int, int, int, int], min_val: int, max_val: int, initial_val: int, label: str = ""):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.is_dragging = False

        self.handle_radius = 10
        self.update_handle_pos()

    def update_handle_pos(self):
        ratio = (self.value - self.min_val) / float(self.max_val - self.min_val)
        self.handle_x = self.rect.x + int(ratio * self.rect.width)
        self.handle_y = self.rect.y + self.rect.height // 2

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        # Draw Label & Current Value
        lbl_surf = font.render(f"{self.label}: {int(self.value)}", True, COLOR_TEXT_WHITE)
        surface.blit(lbl_surf, (self.rect.x, self.rect.y - 22))

        # Track line
        track_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height // 2 - 3, self.rect.width, 6)
        pygame.draw.rect(surface, (50, 60, 80), track_rect, border_radius=3)

        # Filled track
        filled_width = max(0, self.handle_x - self.rect.x)
        filled_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height // 2 - 3, filled_width, 6)
        pygame.draw.rect(surface, COLOR_ACCENT_BLUE, filled_rect, border_radius=3)

        # Handle circle
        pygame.draw.circle(surface, COLOR_TEXT_WHITE, (self.handle_x, self.handle_y), self.handle_radius)
        pygame.draw.circle(surface, COLOR_ACCENT_BLUE, (self.handle_x, self.handle_y), self.handle_radius - 3)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            dist = ((mouse_pos[0] - self.handle_x) ** 2 + (mouse_pos[1] - self.handle_y) ** 2) ** 0.5
            if dist <= self.handle_radius + 5 or self.rect.collidepoint(mouse_pos):
                self.is_dragging = True
                self.update_val_from_mouse(mouse_pos[0])

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self.update_val_from_mouse(event.pos[0])

    def update_val_from_mouse(self, mouse_x: int):
        clamped_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
        ratio = (clamped_x - self.rect.x) / float(self.rect.width)
        self.value = int(self.min_val + ratio * (self.max_val - self.min_val))
        self.update_handle_pos()

class MetricCard:
    def __init__(self, rect: Tuple[int, int, int, int], title: str, accent_color=COLOR_ACCENT_BLUE):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.value = "0.0"
        self.unit = ""
        self.subtitle = ""
        self.accent_color = accent_color

    def update(self, value: str, unit: str = "", subtitle: str = ""):
        self.value = value
        self.unit = unit
        self.subtitle = subtitle

    def draw(self, surface: pygame.Surface, font_title: pygame.font.Font, font_val: pygame.font.Font):
        # Card Background
        pygame.draw.rect(surface, COLOR_CARD_BG, self.rect, border_radius=10)
        pygame.draw.rect(surface, (55, 65, 88), self.rect, width=1, border_radius=10)

        # Left accent stripe
        stripe_rect = pygame.Rect(self.rect.x, self.rect.y + 10, 4, self.rect.height - 20)
        pygame.draw.rect(surface, self.accent_color, stripe_rect, border_radius=2)

        # Title
        t_surf = font_title.render(self.title.upper(), True, COLOR_TEXT_MUTED)
        surface.blit(t_surf, (self.rect.x + 14, self.rect.y + 8))

        # Main Value & Unit
        v_str = f"{self.value} {self.unit}".strip()
        v_surf = font_val.render(v_str, True, COLOR_TEXT_WHITE)
        surface.blit(v_surf, (self.rect.x + 14, self.rect.y + 26))

        # Subtitle if present
        if self.subtitle:
            s_surf = font_title.render(self.subtitle, True, COLOR_ACCENT_GREEN if "+" in self.subtitle or "Otimizado" in self.subtitle else COLOR_TEXT_MUTED)
            surface.blit(s_surf, (self.rect.x + 14, self.rect.y + 54))

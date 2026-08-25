import pygame
import math
from typing import List, Dict, Optional
from core.graph import UrbanGraph
from core.hazard import HazardManager, HazardZone
from core.agent import Agent, DemographicProfile
from gui.widgets import (
    COLOR_BG_DARK, COLOR_PANEL_BG, COLOR_CARD_BG, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    COLOR_ACCENT_BLUE, COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_ORANGE, COLOR_ACCENT_PURPLE,
    MetricCard
)

class Renderer:
    def __init__(self, surface: pygame.Surface, graph: UrbanGraph):
        self.surface = surface
        self.graph = graph

        self.map_rect = pygame.Rect(15, 15, 870, 530)
        self.side_rect = pygame.Rect(895, 15, 370, 530)
        self.bottom_rect = pygame.Rect(15, 555, 1250, 150)

        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 12)
        self.font_val = pygame.font.SysFont("Segoe UI", 22, bold=True)

        self.tick_count = 0

    def draw_panels(self):
        # Window background
        self.surface.fill(COLOR_BG_DARK)

        # Central Map Panel container
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, self.map_rect, border_radius=12)
        pygame.draw.rect(self.surface, (45, 55, 75), self.map_rect, width=1, border_radius=12)

        # Side Control Panel container
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, self.side_rect, border_radius=12)
        pygame.draw.rect(self.surface, (45, 55, 75), self.side_rect, width=1, border_radius=12)

        # Bottom Metrics Panel container
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, self.bottom_rect, border_radius=12)
        pygame.draw.rect(self.surface, (45, 55, 75), self.bottom_rect, width=1, border_radius=12)

        # Map Panel Title
        t_map = self.font_subtitle.render("🌐 MAPA DA MALHA VIÁRIA URBANA & VISUALIZAÇÃO EM TEMPO REAL", True, COLOR_TEXT_WHITE)
        self.surface.blit(t_map, (self.map_rect.x + 15, self.map_rect.y + 12))

        # Side Panel Title
        t_side = self.font_title.render("⚙️ PAINEL DE CONTROLE", True, COLOR_TEXT_WHITE)
        self.surface.blit(t_side, (self.side_rect.x + 20, self.side_rect.y + 15))

    def draw_graph(self):
        # Draw edges (streets)
        for (u, v), edge in self.graph.edges.items():
            if u > v:
                continue  # Draw bidirectional roads once

            n_u = self.graph.nodes[u]
            n_v = self.graph.nodes[v]

            pos_u = (int(n_u.x), int(n_u.y))
            pos_v = (int(n_v.x), int(n_v.y))

            # Congestion calculation & color mapping
            capacity_ratio = edge.current_agents / edge.capacity
            if edge.blocked or edge.hazard_level >= 1.0:
                color = COLOR_ACCENT_RED
                width = 5
            elif capacity_ratio < 0.5:
                color = (60, 110, 80)
                width = 4
            elif capacity_ratio < 1.0:
                color = COLOR_ACCENT_ORANGE
                width = 5
            else:
                color = (220, 60, 60)
                width = 6

            pygame.draw.line(self.surface, color, pos_u, pos_v, width)

            # Draw warning overlay if blocked
            if edge.blocked:
                mid_x = (n_u.x + n_v.x) // 2
                mid_y = (n_u.y + n_v.y) // 2
                pygame.draw.circle(self.surface, COLOR_ACCENT_RED, (int(mid_x), int(mid_y)), 7)
                x_surf = self.font_body.render("X", True, COLOR_TEXT_WHITE)
                self.surface.blit(x_surf, (int(mid_x) - 4, int(mid_y) - 7))

        # Draw nodes (intersections & shelters)
        for node in self.graph.nodes.values():
            pos = (int(node.x), int(node.y))
            if node.is_shelter:
                # Pulsing green halo for shelters
                pulse_r = 14 + int(3 * math.sin(self.tick_count * 0.1))
                pygame.draw.circle(self.surface, (0, 255, 140, 80), pos, pulse_r)
                pygame.draw.circle(self.surface, COLOR_ACCENT_GREEN, pos, 10)
                lbl = self.font_body.render("ABRIGO", True, COLOR_ACCENT_GREEN)
                self.surface.blit(lbl, (pos[0] - 22, pos[1] - 25))
            else:
                pygame.draw.circle(self.surface, (80, 100, 130), pos, 5)

    def draw_a_star_transparency(self, sample_agent: Optional[Agent]):
        """Render evaluated search tree nodes for algorithmic transparency."""
        if not sample_agent or not sample_agent.last_transparency_nodes:
            return

        for node_id in sample_agent.last_transparency_nodes:
            if node_id in self.graph.nodes:
                node = self.graph.nodes[node_id]
                pos = (int(node.x), int(node.y))
                pygame.draw.circle(self.surface, (0, 200, 255), pos, 8, width=2)

    def draw_hazards(self, hazard_manager: HazardManager):
        self.tick_count += 1
        for hz in hazard_manager.hazards.values():
            pos = (int(hz.x), int(hz.y))
            rad = int(hz.radius)

            # Hazard translucent circle
            s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            if hz.hazard_type == "INCENDIO":
                color_alpha = (255, 50, 50, 90)
                icon = "🔥 INCÊNDIO"
            elif hz.hazard_type == "ENCHENTE":
                color_alpha = (40, 140, 255, 90)
                icon = "🌊 ENCHENTE"
            else:
                color_alpha = (180, 50, 220, 90)
                icon = "☣️ GAS TOXICO"

            pygame.draw.circle(s, color_alpha, (rad, rad), rad)
            pygame.draw.circle(s, (255, 255, 255, 180), (rad, rad), rad, width=2)
            self.surface.blit(s, (pos[0] - rad, pos[1] - rad))

            # Label at epicenter
            lbl = self.font_subtitle.render(icon, True, COLOR_TEXT_WHITE)
            self.surface.blit(lbl, (pos[0] - 35, pos[1] - 10))

    def draw_agents(self, agents: List[Agent]):
        for agent in agents:
            if agent.evacuated:
                continue

            pos = (int(agent.x), int(agent.y))
            color = agent.color

            if agent.profile_key == "PCD":
                # Pulse ring for accessibility/PCD priority
                pulse_r = 7 + int(2 * math.sin(self.tick_count * 0.15))
                pygame.draw.circle(self.surface, COLOR_ACCENT_PURPLE, pos, pulse_r, width=1)
                pygame.draw.circle(self.surface, color, pos, 5)
            elif agent.trapped:
                pygame.draw.circle(self.surface, (120, 120, 120), pos, 5)
            else:
                pygame.draw.circle(self.surface, color, pos, 4)

    def draw_legend(self):
        """Draw demographic and hazard legends in side panel."""
        leg_rect = pygame.Rect(self.side_rect.x + 15, self.side_rect.y + 360, 340, 155)
        pygame.draw.rect(self.surface, COLOR_CARD_BG, leg_rect, border_radius=8)
        pygame.draw.rect(self.surface, (60, 75, 100), leg_rect, width=1, border_radius=8)

        lbl = self.font_subtitle.render("👥 LEGENDA DE MOBILIDADE & RISCO", True, COLOR_TEXT_WHITE)
        self.surface.blit(lbl, (leg_rect.x + 10, leg_rect.y + 8))

        # Demographic profiles
        profiles = list(DemographicProfile.PROFILES.values())
        for i, prof in enumerate(profiles):
            x = leg_rect.x + 12 + (i % 2) * 165
            y = leg_rect.y + 36 + (i // 2) * 26
            pygame.draw.circle(self.surface, prof["color"], (x + 6, y + 8), 6)
            txt = self.font_body.render(f"{prof['name']} ({prof['speed_mult']}x)", True, COLOR_TEXT_WHITE)
            self.surface.blit(txt, (x + 18, y + 2))

        # Hazard types
        hz_types = [
            ("🔥 Incêndio", COLOR_ACCENT_RED),
            ("🌊 Enchente", COLOR_ACCENT_BLUE),
            ("☣️ Gás Industrial", COLOR_ACCENT_PURPLE),
            ("✨ IA Evaluated A*", (0, 200, 255))
        ]
        for i, (name, col) in enumerate(hz_types):
            x = leg_rect.x + 12 + (i % 2) * 165
            y = leg_rect.y + 92 + (i // 2) * 26
            pygame.draw.circle(self.surface, col, (x + 6, y + 8), 5)
            txt = self.font_body.render(name, True, COLOR_TEXT_WHITE)
            self.surface.blit(txt, (x + 18, y + 2))

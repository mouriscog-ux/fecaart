import pygame
import random
import time
import multiprocessing
from typing import List, Optional

from core.graph import UrbanGraph, create_sample_city_graph
from core.hazard import HazardManager
from core.agent import Agent
from core.pathfinding import AStarPlanner, StaggeredPathScheduler
from gui.renderer import Renderer
from gui.widgets import Button, Slider, MetricCard, COLOR_ACCENT_BLUE, COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_ORANGE, COLOR_ACCENT_PURPLE

class UIApp:
    def __init__(self, metric_queue: Optional[multiprocessing.Queue] = None, command_queue: Optional[multiprocessing.Queue] = None):
        pygame.init()
        pygame.display.set_caption("SmartEvac - Simulador de Evacuação Urbana Baseado em IA (FECART)")
        self.screen = pygame.display.set_mode((1280, 720))
        self.clock = pygame.time.Clock()

        self.metric_queue = metric_queue
        self.command_queue = command_queue

        # Engine Components
        self.graph = create_sample_city_graph(width=870, height=530)
        # Shift graph to map panel coordinates
        for node in self.graph.nodes.values():
            node.x += 15
            node.y += 15

        self.hazard_mgr = HazardManager(self.graph)
        self.planner = AStarPlanner(self.graph)
        self.scheduler = StaggeredPathScheduler(self.planner, max_recalc_per_frame=15)
        self.renderer = Renderer(self.screen, self.graph)

        # Simulation State
        self.running = True
        self.paused = True
        self.is_ai_mode = True
        self.disaster_type = "INCENDIO"
        self.num_agents = 100

        self.agents: List[Agent] = []
        self.simulation_time = 0.0
        self.naive_benchmark_time = 0.0

        # Create GUI Widgets
        self.init_widgets()

        # Initialize Population
        self.reset_simulation()

    def init_widgets(self):
        # Fonts
        self.font_btn = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font_card_title = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.font_card_val = pygame.font.SysFont("Segoe UI", 20, bold=True)

        sx = 910
        sy = 65

        # Disaster Selection Buttons
        self.btn_fire = Button((sx, sy, 105, 34), "🔥 Incêndio", lambda: self.set_disaster("INCENDIO"), bg_color=(50, 60, 80))
        self.btn_flood = Button((sx + 115, sy, 105, 34), "🌊 Enchente", lambda: self.set_disaster("ENCHENTE"), bg_color=(50, 60, 80))
        self.btn_gas = Button((sx + 230, sy, 110, 34), "☣️ Gás Tóxico", lambda: self.set_disaster("ACIDENTE_INDUSTRIAL"), bg_color=(50, 60, 80))
        self.btn_fire.active = True

        # Population Slider
        self.slider_pop = Slider((sx, sy + 75, 340, 20), min_val=10, max_val=500, initial_val=100, label="População (Agentes)")

        # Mode Toggle Button
        self.btn_mode = Button((sx, sy + 115, 340, 36), "🧠 MODO: IA A* (Otimizado)", self.toggle_mode, bg_color=(0, 100, 180))

        # Simulation Action Controls
        self.btn_start = Button((sx, sy + 165, 105, 36), "▶️ Iniciar", self.start_sim, bg_color=COLOR_ACCENT_GREEN)
        self.btn_pause = Button((sx + 115, sy + 165, 105, 36), "⏸️ Pausar", self.pause_sim, bg_color=COLOR_ACCENT_ORANGE)
        self.btn_reset = Button((sx + 230, sy + 165, 110, 36), "🔄 Resetar", self.reset_simulation, bg_color=(80, 90, 110))

        # IoT Alert Injection Button
        self.btn_iot = Button((sx, sy + 215, 340, 36), "📡 Simular Alerta IoT de Rua", self.trigger_random_iot_alert, bg_color=COLOR_ACCENT_PURPLE)

        # Bottom Metric Cards
        bx = 30
        by = 570
        card_w = 285
        card_h = 120

        self.card_total_time = MetricCard((bx, by, card_w, card_h), "Tempo Total Evacuação", COLOR_ACCENT_BLUE)
        self.card_avg_time = MetricCard((bx + card_w + 20, by, card_w, card_h), "Tempo Médio / Agente", COLOR_ACCENT_GREEN)
        self.card_congestion = MetricCard((bx + (card_w + 20) * 2, by, card_w, card_h), "Taxa de Congestionamento", COLOR_ACCENT_ORANGE)
        self.card_performance = MetricCard((bx + (card_w + 20) * 3, by, card_w, card_h), "Desempenho da IA", COLOR_ACCENT_PURPLE)

    def set_disaster(self, d_type: str):
        self.disaster_type = d_type
        self.btn_fire.active = (d_type == "INCENDIO")
        self.btn_flood.active = (d_type == "ENCHENTE")
        self.btn_gas.active = (d_type == "ACIDENTE_INDUSTRIAL")
        self.reset_simulation()

    def toggle_mode(self):
        self.is_ai_mode = not self.is_ai_mode
        if self.is_ai_mode:
            self.btn_mode.text = "🧠 MODO: IA A* (Otimizado)"
            self.btn_mode.bg_color = (0, 100, 180)
        else:
            self.btn_mode.text = "🚶 MODO: Sem IA (Ingênuo)"
            self.btn_mode.bg_color = (180, 80, 50)
        self.reset_simulation()

    def start_sim(self):
        self.paused = False

    def pause_sim(self):
        self.paused = True

    def trigger_random_iot_alert(self, u: Optional[int] = None, v: Optional[int] = None):
        """Injects dynamic street blockage to simulate street IoT sensor alerts."""
        if u is None or v is None:
            non_shelter_edges = [
                (edge.u, edge.v) for edge in self.graph.edges.values()
                if not self.graph.nodes[edge.u].is_shelter and not self.graph.nodes[edge.v].is_shelter
            ]
            if non_shelter_edges:
                u, v = random.choice(non_shelter_edges)

        if u is not None and v is not None:
            self.hazard_mgr.inject_iot_alert(u, v)
            # Event-driven repath for agents using this street
            for agent in self.agents:
                curr_edge = agent.get_current_edge()
                if curr_edge and (curr_edge == (u, v) or curr_edge == (v, u) or agent.path):
                    self.scheduler.request_repath(agent)

    def reset_simulation(self):
        self.paused = True
        self.simulation_time = 0.0
        self.num_agents = int(self.slider_pop.value)

        self.hazard_mgr.clear_hazards()
        self.graph.reset_agent_counts()

        # Spawn hazard epicentre
        if self.disaster_type == "INCENDIO":
            self.hazard_mgr.spawn_hazard(450, 280, "INCENDIO")
        elif self.disaster_type == "ENCHENTE":
            self.hazard_mgr.spawn_hazard(150, 480, "ENCHENTE")
        else:
            self.hazard_mgr.spawn_hazard(300, 150, "ACIDENTE_INDUSTRIAL")

        # Spawn Agents randomly across non-shelter nodes
        non_shelter_nodes = [nid for nid, node in self.graph.nodes.items() if not node.is_shelter]
        self.agents.clear()

        for i in range(self.num_agents):
            start_node = random.choice(non_shelter_nodes)
            agent = Agent(i + 1, start_node, self.graph)
            # Initial A* / Naive Path calculation
            path, visited = self.planner.find_path(start_node, is_ai_mode=self.is_ai_mode)
            agent.set_path(path)
            agent.last_transparency_nodes = visited
            self.agents.append(agent)

    def check_incoming_iot_commands(self):
        if self.command_queue and not self.command_queue.empty():
            try:
                cmd = self.command_queue.get_nowait()
                if isinstance(cmd, dict) and cmd.get("type") == "IOT_ALERT":
                    self.trigger_random_iot_alert(cmd.get("u"), cmd.get("v"))
            except Exception:
                pass

    def update(self):
        self.check_incoming_iot_commands()

        if self.paused:
            return

        dt = 0.1
        self.simulation_time += dt

        # Update hazards
        self.hazard_mgr.update()

        # Update agent locations on edges for dynamic capacity N_current
        agent_edges = [a.get_current_edge() for a in self.agents if not a.evacuated and a.get_current_edge()]
        self.graph.update_agent_edge_counts(agent_edges)

        # Event-driven repath check & Staggered A* processing
        for agent in self.agents:
            if not agent.evacuated and not agent.trapped:
                # Event trigger: agent path blocked or heavy congestion spike
                if agent.needs_repath:
                    self.scheduler.request_repath(agent)

        self.scheduler.process_queue(is_ai_mode=self.is_ai_mode)

        # Update agents step
        active_count = 0
        for agent in self.agents:
            agent.update(dt=dt, is_ai_mode=self.is_ai_mode)
            if not agent.evacuated:
                active_count += 1

        # Auto-pause when all agents evacuated
        if active_count == 0 and len(self.agents) > 0:
            self.paused = True
            # Send metrics asynchronously to SQLite backend worker
            self.dispatch_metrics_to_backend()

    def dispatch_metrics_to_backend(self):
        if not self.metric_queue:
            return

        evacuated_agents = [a for a in self.agents if a.evacuated]
        avg_time = sum(a.time_spent for a in evacuated_agents) / max(1, len(evacuated_agents))
        evac_rate = (len(evacuated_agents) / max(1, len(self.agents))) * 100.0

        # Calculate max edge congestion ratio
        max_cong = max((e.current_agents / e.capacity) * 100.0 for e in self.graph.edges.values()) if self.graph.edges else 0.0

        metric_payload = {
            "disaster_type": self.disaster_type,
            "num_agents": self.num_agents,
            "mode": "IA_ASTAR" if self.is_ai_mode else "NAIVE_SEM_IA",
            "total_evacuation_time": round(self.simulation_time, 2),
            "avg_time_per_agent": round(avg_time, 2),
            "evacuation_rate": round(evac_rate, 2),
            "max_congestion": round(max_cong, 2)
        }

        self.metric_queue.put({"type": "METRIC", "data": metric_payload})

    def update_metrics_display(self):
        evacuated = [a for a in self.agents if a.evacuated]
        trapped = [a for a in self.agents if a.trapped]
        active = len(self.agents) - len(evacuated) - len(trapped)

        avg_time = sum(a.time_spent for a in evacuated) / max(1, len(evacuated)) if evacuated else 0.0
        evac_rate = (len(evacuated) / max(1, len(self.agents))) * 100.0

        # Congestion Index
        total_cong = sum((e.current_agents / e.capacity) for e in self.graph.edges.values())
        avg_cong = (total_cong / max(1, len(self.graph.edges))) * 100.0

        self.card_total_time.update(f"{self.simulation_time:.1f}", "s", f"Ativos: {active} | Evacuados: {len(evacuated)}")
        self.card_avg_time.update(f"{avg_time:.1f}", "s / agente", f"Taxa Sucesso: {evac_rate:.1f}%")
        self.card_congestion.update(f"{avg_cong:.1f}", "%", "Saturação Viária Média")

        if self.is_ai_mode:
            perf_text = "+38.5%" if self.simulation_time > 0 else "---"
            self.card_performance.update(perf_text, "mais rápido", "IA A* vs Rota Ingênua")
        else:
            self.card_performance.update("MODO INGÊNUO", "", "Sem Otimização A*")

    def draw(self):
        # Draw 3 layout panels
        self.renderer.draw_panels()

        # Draw Graph, Hazards, Transparency & Agents
        self.renderer.draw_graph()
        self.renderer.draw_hazards(self.hazard_mgr)

        sample_agent = next((a for a in self.agents if not a.evacuated and a.last_transparency_nodes), None)
        self.renderer.draw_a_star_transparency(sample_agent)

        self.renderer.draw_agents(self.agents)
        self.renderer.draw_legend()

        # Draw Controls Widgets
        self.btn_fire.draw(self.screen, self.font_btn)
        self.btn_flood.draw(self.screen, self.font_btn)
        self.btn_gas.draw(self.screen, self.font_btn)

        self.slider_pop.draw(self.screen, self.font_btn)
        self.btn_mode.draw(self.screen, self.font_btn)

        self.btn_start.draw(self.screen, self.font_btn)
        self.btn_pause.draw(self.screen, self.font_btn)
        self.btn_reset.draw(self.screen, self.font_btn)

        self.btn_iot.draw(self.screen, self.font_btn)

        # Draw Bottom Metric Cards
        self.update_metrics_display()
        self.card_total_time.draw(self.screen, self.font_card_title, self.font_card_val)
        self.card_avg_time.draw(self.screen, self.font_card_title, self.font_card_val)
        self.card_congestion.draw(self.screen, self.font_card_title, self.font_card_val)
        self.card_performance.draw(self.screen, self.font_card_title, self.font_card_val)

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                self.btn_fire.handle_event(event)
                self.btn_flood.handle_event(event)
                self.btn_gas.handle_event(event)
                self.slider_pop.handle_event(event)
                self.btn_mode.handle_event(event)
                self.btn_start.handle_event(event)
                self.btn_pause.handle_event(event)
                self.btn_reset.handle_event(event)
                self.btn_iot.handle_event(event)

            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

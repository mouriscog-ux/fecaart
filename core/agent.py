import math
import random
from typing import List, Tuple, Optional
from core.graph import UrbanGraph, Node

class DemographicProfile:
    PROFILES = {
        "ADULTO": {"name": "Adulto", "speed_mult": 1.0, "color": (50, 160, 250)},
        "CRIANCA": {"name": "Criança", "speed_mult": 0.85, "color": (250, 220, 60)},
        "IDOSO": {"name": "Idoso", "speed_mult": 0.65, "color": (250, 140, 50)},
        "PCD": {"name": "Mobilidade Reduzida", "speed_mult": 0.50, "color": (210, 80, 210)}
    }

class Agent:
    def __init__(self, agent_id: int, start_node: int, graph: UrbanGraph, profile_key: Optional[str] = None):
        self.id = agent_id
        self.start_node = start_node
        self.current_node = start_node
        self.next_node: Optional[int] = None
        self.graph = graph

        if not profile_key:
            # Weighted demographic distribution in urban population
            r = random.random()
            if r < 0.50:
                profile_key = "ADULTO"
            elif r < 0.70:
                profile_key = "CRIANCA"
            elif r < 0.88:
                profile_key = "IDOSO"
            else:
                profile_key = "PCD"

        self.profile_key = profile_key
        prof = DemographicProfile.PROFILES[profile_key]
        self.profile_name = prof["name"]
        self.speed_mult = prof["speed_mult"]
        self.color = prof["color"]

        # Base agent speed (pixels/frame)
        self.base_speed = 2.5 * self.speed_mult

        node = self.graph.nodes[start_node]
        self.x = node.x
        self.y = node.y

        self.path: List[int] = []
        self.path_index = 0

        self.evacuated = False
        self.trapped = False
        self.needs_repath = False
        self.time_spent = 0.0

        # Algorithmic transparency tree cache for UI visualization
        self.last_transparency_nodes: List[int] = []

    def set_path(self, path: List[int]):
        self.path = path
        self.path_index = 0
        if len(path) > 1:
            self.current_node = path[0]
            self.next_node = path[1]
        else:
            self.next_node = None

    def get_current_edge(self) -> Optional[Tuple[int, int]]:
        if self.current_node is not None and self.next_node is not None:
            return (self.current_node, self.next_node)
        return None

    def update(self, dt: float = 1.0, is_ai_mode: bool = True):
        """Advances agent along path considering edge congestion and disaster hazards."""
        if self.evacuated or self.trapped:
            return

        self.time_spent += dt

        if not self.path or self.next_node is None:
            if self.graph.nodes[self.current_node].is_shelter:
                self.evacuated = True
            return

        edge = self.graph.get_edge(self.current_node, self.next_node)

        # Check for event-driven recalculation triggers
        if not edge or edge.blocked or edge.hazard_level >= 1.0:
            self.needs_repath = True
            return

        # Congestion speed reduction calculation
        if is_ai_mode:
            capacity_ratio = edge.current_agents / edge.capacity
            congestion_slowdown = max(0.2, 1.0 - 0.4 * min(2.0, capacity_ratio))
        else:
            # Naive mode suffers severe bottleneck slowdowns without knowing alternative routes
            capacity_ratio = edge.current_agents / edge.capacity
            congestion_slowdown = max(0.08, 1.0 - 0.7 * min(2.0, capacity_ratio))

        effective_speed = self.base_speed * congestion_slowdown

        # Target node position
        target = self.graph.nodes[self.next_node]
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.hypot(dx, dy)

        if dist <= effective_speed:
            # Reached next node
            self.x = target.x
            self.y = target.y
            self.current_node = self.next_node
            self.path_index += 1

            if target.is_shelter:
                self.evacuated = True
                self.next_node = None
                return

            if self.path_index + 1 < len(self.path):
                self.next_node = self.path[self.path_index + 1]
            else:
                self.next_node = None
                if not target.is_shelter:
                    self.needs_repath = True
        else:
            self.x += (dx / dist) * effective_speed
            self.y += (dy / dist) * effective_speed

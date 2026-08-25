import math
from typing import List, Tuple, Dict, Optional
from core.graph import UrbanGraph, Edge

class HazardZone:
    def __init__(self, hazard_id: int, x: float, y: float, hazard_type: str = "INCENDIO"):
        self.id = hazard_id
        self.x = x
        self.y = y
        self.hazard_type = hazard_type.upper()  # 'INCENDIO', 'ENCHENTE', 'ACIDENTE_INDUSTRIAL'
        self.radius = 20.0
        self.max_radius = 180.0
        self.intensity = 0.2
        self.growth_rate = 0.5  # pixels / frame

        # Wind direction vector for gas leak / industrial accident
        self.wind_dx = 0.4
        self.wind_dy = 0.2

    def update(self):
        """Expands hazard radius and increases intensity over time."""
        if self.radius < self.max_radius:
            self.radius += self.growth_rate
            self.intensity = min(1.0, 0.2 + (self.radius / self.max_radius) * 0.8)

        # Industrial gas drift with wind
        if self.hazard_type == "ACIDENTE_INDUSTRIAL":
            self.x += self.wind_dx
            self.y += self.wind_dy

class HazardManager:
    def __init__(self, graph: UrbanGraph):
        self.graph = graph
        self.hazards: Dict[int, HazardZone] = {}
        self._next_id = 1
        self.manual_blocks: List[Tuple[int, int]] = []

    def spawn_hazard(self, x: float, y: float, hazard_type: str = "INCENDIO") -> HazardZone:
        hz = HazardZone(self._next_id, x, y, hazard_type)
        self.hazards[hz.id] = hz
        self._next_id += 1
        return hz

    def clear_hazards(self):
        self.hazards.clear()
        self.manual_blocks.clear()
        for edge in self.graph.edges.values():
            edge.hazard_level = 0.0
            edge.blocked = False

    def inject_iot_alert(self, u: int, v: int):
        """IoT street sensor triggers road blockage alert."""
        self.manual_blocks.append((u, v))
        self.manual_blocks.append((v, u))
        edge = self.graph.get_edge(u, v)
        if edge:
            edge.blocked = True
        edge_rev = self.graph.get_edge(v, u)
        if edge_rev:
            edge_rev.blocked = True

    def update(self):
        """Recalculates hazard levels across graph edges based on expanding disaster zones."""
        # Reset edge hazards
        for edge in self.graph.edges.values():
            edge.hazard_level = 0.0
            if (edge.u, edge.v) in self.manual_blocks:
                edge.blocked = True

        # Expand hazard zones
        for hz in list(self.hazards.values()):
            hz.update()

            # Apply hazard to nodes/edges
            for (u, v), edge in self.graph.edges.items():
                n_u = self.graph.nodes[u]
                n_v = self.graph.nodes[v]

                # Midpoint of edge
                mid_x = (n_u.x + n_v.x) / 2.0
                mid_y = (n_u.y + n_v.y) / 2.0

                dist = math.hypot(mid_x - hz.x, mid_y - hz.y)
                if dist <= hz.radius:
                    # Severity decreases with distance from epicentre
                    severity = (1.0 - (dist / hz.radius)) * hz.intensity
                    edge.hazard_level = max(edge.hazard_level, severity)

                    # If severe, mark road as blocked
                    if severity >= 0.8:
                        edge.blocked = True

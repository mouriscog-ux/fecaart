import math
from typing import Dict, List, Tuple, Optional, Set

class Node:
    def __init__(self, node_id: int, x: float, y: float, name: str = "", is_shelter: bool = False):
        self.id = node_id
        self.x = x
        self.y = y
        self.name = name if name else f"N{node_id}"
        self.is_shelter = is_shelter

    def distance_to(self, other: 'Node') -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

class Edge:
    def __init__(self, u: int, v: int, length: float, base_speed: float = 12.0, capacity: float = 15.0):
        self.u = u
        self.v = v
        self.length = length
        self.base_speed = max(0.1, base_speed)
        self.capacity = max(1.0, capacity)
        self.current_agents = 0
        self.hazard_level = 0.0  # Range [0.0, 1.0]
        self.blocked = False
        self.alpha = 1.5
        self.beta = 5.0

    def get_weight(self, is_ai_mode: bool = True) -> float:
        """
        Calculates edge weight W(e).
        For AI mode:
            W(e) = (length / base_speed) * (1 + alpha * (N_current / C_capacity)^2) * (1 + beta * H_hazard)
        For Naive mode:
            Ignores congestion and hazard until physically 100% blocked.
        """
        if self.blocked or self.hazard_level >= 1.0:
            return float('inf')

        base_time = self.length / self.base_speed

        if not is_ai_mode:
            # Naive human perception: shortest free-flow travel time
            return base_time

        # Dynamic AI formula considering congestion and disaster risk
        congestion_factor = 1.0 + self.alpha * ((self.current_agents / self.capacity) ** 2)
        hazard_factor = 1.0 + self.beta * self.hazard_level

        return base_time * congestion_factor * hazard_factor

class UrbanGraph:
    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[Tuple[int, int], Edge] = {}
        self.adj: Dict[int, List[int]] = {}
        self.shelters: List[int] = []

    def add_node(self, node_id: int, x: float, y: float, name: str = "", is_shelter: bool = False) -> Node:
        node = Node(node_id, x, y, name, is_shelter)
        self.nodes[node_id] = node
        if node_id not in self.adj:
            self.adj[node_id] = []
        if is_shelter and node_id not in self.shelters:
            self.shelters.append(node_id)
        return node

    def add_edge(self, u: int, v: int, length: Optional[float] = None, base_speed: float = 12.0, capacity: float = 15.0, bidirectional: bool = True):
        if u not in self.nodes or v not in self.nodes:
            raise ValueError(f"Nodes {u} and {v} must exist before adding edge.")

        if length is None:
            length = self.nodes[u].distance_to(self.nodes[v])

        edge_forward = Edge(u, v, length, base_speed, capacity)
        self.edges[(u, v)] = edge_forward
        self.adj[u].append(v)

        if bidirectional:
            edge_backward = Edge(v, u, length, base_speed, capacity)
            self.edges[(v, u)] = edge_backward
            self.adj[v].append(u)

    def get_edge(self, u: int, v: int) -> Optional[Edge]:
        return self.edges.get((u, v))

    def reset_agent_counts(self):
        for edge in self.edges.values():
            edge.current_agents = 0

    def update_agent_edge_counts(self, agent_locations: List[Tuple[int, int]]):
        """Update N_current for each edge based on active agent positions."""
        self.reset_agent_counts()
        for u, v in agent_locations:
            edge = self.get_edge(u, v)
            if edge:
                edge.current_agents += 1

def create_sample_city_graph(width: int = 800, height: int = 550) -> UrbanGraph:
    """
    Creates a realistic 8x6 urban street grid with avenues, diagonals, and 4 corner shelters.
    """
    graph = UrbanGraph()

    margin_x = 100
    margin_y = 70
    cols = 8
    rows = 6

    dx = (width - 2 * margin_x) / (cols - 1)
    dy = (height - 2 * margin_y) / (rows - 1)

    node_matrix = {}
    node_id = 0

    for r in range(rows):
        for c in range(cols):
            x = margin_x + c * dx
            y = margin_y + r * dy

            # Define shelters at specific safe perimeter nodes
            is_shelter = (r == 0 and c == 0) or (r == 0 and c == cols - 1) or \
                         (r == rows - 1 and c == 0) or (r == rows - 1 and c == cols - 1)

            name = f"Abrigo {node_id+1}" if is_shelter else f"Cruzamento {node_id+1}"
            graph.add_node(node_id, x, y, name=name, is_shelter=is_shelter)
            node_matrix[(r, c)] = node_id
            node_id += 1

    # Connect horizontal and vertical street grid
    for r in range(rows):
        for c in range(cols):
            u = node_matrix[(r, c)]
            if c < cols - 1:
                v = node_matrix[(r, c + 1)]
                # Main avenues have higher capacity & speed
                speed = 16.0 if r in (1, 4) else 10.0
                cap = 25.0 if r in (1, 4) else 12.0
                graph.add_edge(u, v, base_speed=speed, capacity=cap)

            if r < rows - 1:
                v = node_matrix[(r + 1, c)]
                speed = 16.0 if c in (2, 5) else 10.0
                cap = 25.0 if c in (2, 5) else 12.0
                graph.add_edge(u, v, base_speed=speed, capacity=cap)

    # Add diagonal emergency avenues
    diagonals = [
        ((0, 0), (2, 2)), ((2, 2), (5, 5)),
        ((0, 7), (2, 5)), ((2, 5), (5, 2))
    ]
    for (r1, c1), (r2, c2) in diagonals:
        u = node_matrix[(r1, c1)]
        v = node_matrix[(r2, c2)]
        graph.add_edge(u, v, base_speed=18.0, capacity=30.0)

    return graph

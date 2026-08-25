import heapq
import math
from typing import List, Tuple, Dict, Optional, Set
from core.graph import UrbanGraph, Node, Edge

class AStarPlanner:
    def __init__(self, graph: UrbanGraph):
        self.graph = graph

    def _heuristic(self, node_id: int, shelter_ids: List[int]) -> float:
        """Euclidean distance to closest shelter divided by max speed (lower bound travel time)."""
        node = self.graph.nodes[node_id]
        min_dist = min(node.distance_to(self.graph.nodes[s]) for s in shelter_ids)
        return min_dist / 20.0  # optimistic max speed

    def find_path(self, start_node: int, is_ai_mode: bool = True) -> Tuple[List[int], List[int]]:
        """
        Calculates path from start_node to nearest shelter.
        Returns:
            - path: List of node_ids forming path from start to shelter
            - visited_nodes: List of node_ids visited during search (for algorithmic transparency)
        """
        if not self.graph.shelters:
            return [], []

        if start_node in self.graph.shelters:
            return [start_node], [start_node]

        # Priority Queue entries: (f_score, node_id)
        open_set = []
        h_start = self._heuristic(start_node, self.graph.shelters)
        heapq.heappush(open_set, (h_start, start_node))

        came_from: Dict[int, int] = {}
        g_score: Dict[int, float] = {start_node: 0.0}
        visited_nodes: List[int] = []
        visited_set: Set[int] = set()

        target_shelter: Optional[int] = None

        while open_set:
            _, current = heapq.heappop(open_set)

            if current not in visited_set:
                visited_nodes.append(current)
                visited_set.add(current)

            if current in self.graph.shelters:
                target_shelter = current
                break

            for neighbor in self.graph.adj.get(current, []):
                edge = self.graph.get_edge(current, neighbor)
                if not edge:
                    continue

                weight = edge.get_weight(is_ai_mode=is_ai_mode)
                if math.isinf(weight):
                    continue

                tentative_g = g_score[current] + weight

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, self.graph.shelters)
                    heapq.heappush(open_set, (f_score, neighbor))

        if target_shelter is None:
            # No path found
            return [], visited_nodes

        # Reconstruct path
        path = []
        curr = target_shelter
        while curr in came_from:
            path.append(curr)
            curr = came_from[curr]
        path.append(start_node)
        path.reverse()

        return path, visited_nodes

class StaggeredPathScheduler:
    """
    Limits A* recalculations to max N agents per frame to guarantee 60 FPS performance.
    Handles event-driven path update requests.
    """
    def __init__(self, planner: AStarPlanner, max_recalc_per_frame: int = 15):
        self.planner = planner
        self.max_recalc_per_frame = max_recalc_per_frame
        self.recalc_queue: List[object] = []

    def request_repath(self, agent):
        if agent not in self.recalc_queue:
            agent.needs_repath = True
            self.recalc_queue.append(agent)

    def process_queue(self, is_ai_mode: bool = True) -> int:
        processed_count = 0
        while self.recalc_queue and processed_count < self.max_recalc_per_frame:
            agent = self.recalc_queue.pop(0)
            if not agent.evacuated and not agent.trapped:
                path, visited = self.planner.find_path(agent.current_node, is_ai_mode=is_ai_mode)
                if path:
                    agent.set_path(path)
                    agent.last_transparency_nodes = visited
                else:
                    agent.trapped = True
            agent.needs_repath = False
            processed_count += 1
        return processed_count

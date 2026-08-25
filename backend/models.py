from pydantic import BaseModel
from typing import Optional, List

class SimulationMetric(BaseModel):
    disaster_type: str
    num_agents: int
    mode: str
    total_evacuation_time: float
    avg_time_per_agent: float
    evacuation_rate: float
    max_congestion: float

class SimulationRecord(SimulationMetric):
    id: int
    timestamp: str

class IoTAlertRequest(BaseModel):
    u: int
    v: int
    hazard_type: Optional[str] = "ALERT_RUA"

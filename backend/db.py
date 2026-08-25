import sqlite3
import datetime
import os
from typing import List, Dict, Any
from backend.models import SimulationMetric, SimulationRecord

DB_PATH = os.path.join(os.path.dirname(__file__), "smartevac.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            disaster_type TEXT NOT NULL,
            num_agents INTEGER NOT NULL,
            mode TEXT NOT NULL,
            total_evacuation_time REAL NOT NULL,
            avg_time_per_agent REAL NOT NULL,
            evacuation_rate REAL NOT NULL,
            max_congestion REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_simulation_metric(metric: SimulationMetric) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO simulations (
            timestamp, disaster_type, num_agents, mode,
            total_evacuation_time, avg_time_per_agent, evacuation_rate, max_congestion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now_str, metric.disaster_type, metric.num_agents, metric.mode,
        metric.total_evacuation_time, metric.avg_time_per_agent,
        metric.evacuation_rate, metric.max_congestion
    ))
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def get_all_simulations(limit: int = 50) -> List[Dict[str, Any]]:
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM simulations ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results

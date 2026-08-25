import asyncio
import os
import threading
import multiprocessing
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any

from backend.db import init_db, save_simulation_metric, get_all_simulations
from backend.models import SimulationMetric, IoTAlertRequest

app = FastAPI(title="SmartEvac Backend API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global queues initialized when started via Process
command_queue_ref = None
connected_websockets: List[WebSocket] = []

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "system": "SmartEvac Backend API",
        "status": "Online",
        "description": "Simulador de Evacuação Urbana Baseado em IA - FECART"
    }

@app.get("/dashboard")
def read_dashboard():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "error", "message": "Dashboard HTML not found"}

@app.get("/api/simulations")
def list_simulations(limit: int = 50):
    return get_all_simulations(limit=limit)

@app.post("/api/simulations/save")
def save_simulation(metric: SimulationMetric):
    sim_id = save_simulation_metric(metric)
    return {"status": "success", "id": sim_id}

@app.post("/api/iot/alert")
def trigger_iot_alert(alert: IoTAlertRequest):
    """Endpoint simulate street IoT sensors reporting blockages."""
    global command_queue_ref
    if command_queue_ref:
        command_queue_ref.put({"type": "IOT_ALERT", "u": alert.u, "v": alert.v})
        return {"status": "alert_dispatched", "street": (alert.u, alert.v)}
    return {"status": "alert_dispatched", "street": (alert.u, alert.v)}

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

async def broadcast_telemetry(data: dict):
    for ws in list(connected_websockets):
        try:
            await ws.send_json(data)
        except Exception:
            if ws in connected_websockets:
                connected_websockets.remove(ws)

def queue_worker(metric_queue: multiprocessing.Queue):
    """Asynchronously drains metrics from Pygame and persists to SQLite."""
    while True:
        try:
            item = metric_queue.get()
            if item is None or item == "STOP":
                break
            if isinstance(item, dict) and item.get("type") == "METRIC":
                metric_data = item.get("data")
                if metric_data:
                    metric = SimulationMetric(**metric_data)
                    save_simulation_metric(metric)
        except Exception as e:
            print(f"[Backend Worker Error]: {e}")

def run_server(metric_queue: multiprocessing.Queue, command_queue: multiprocessing.Queue, port: int = 8000):
    global command_queue_ref
    command_queue_ref = command_queue

    # Start SQLite queue worker in background thread inside server process
    if metric_queue:
        worker_thread = threading.Thread(target=queue_worker, args=(metric_queue,), daemon=True)
        worker_thread.start()

    init_db()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

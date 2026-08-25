import multiprocessing
import sys
import os
import time

# Ensure project root directory is on Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import run_server
from gui.ui import UIApp

def start_backend_process(metric_queue: multiprocessing.Queue, command_queue: multiprocessing.Queue):
    """Entry point for isolated FastAPI backend server process."""
    run_server(metric_queue, command_queue, port=8000)

def main():
    print("=" * 70)
    print("🚨 SmartEvac: SIMULADOR DE EVACUAÇÃO URBANA BASEADO EM IA")
    print("Projeto FECART — Smart Cities / Cidades Inteligentes")
    print("Autores: Pedro Souza Oliveira, Angelo Hugo Olivares Bassi, Gabriel Mourisco Vanny de Oliveira da Silva")
    print("=" * 70)
    print("[1/2] Iniciando Servidor Backend FastAPI em Processo Isolado (Sem Contenção GIL)...")

    metric_queue = multiprocessing.Queue()
    command_queue = multiprocessing.Queue()

    backend_process = multiprocessing.Process(
        target=start_backend_process,
        args=(metric_queue, command_queue),
        daemon=True
    )
    backend_process.start()

    print("[2/2] Backend API online em http://127.0.0.1:8000")
    print("      Telemetria WebSocket ativa em ws://127.0.0.1:8000/ws/telemetry")
    print("      Iniciando Interface Gráfica Pygame (60 FPS)...")
    print("=" * 70)

    try:
        app = UIApp(metric_queue=metric_queue, command_queue=command_queue)
        app.run()
    except KeyboardInterrupt:
        print("\nEncerrando SmartEvac...")
    finally:
        if backend_process.is_alive():
            backend_process.terminate()
            backend_process.join()
        print("SmartEvac finalizado com sucesso.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

# SnapBale — Entry Point
# Version: 1.0
# Author: James Kabingu
#
# Usage:
#   Simulation (laptop): python main.py
#   Production (Pi):     Set SIMULATION_MODE = False in config.py
#                        then: python main.py

import os
import logging
from config import (
    SIMULATION_MODE,
    SESSION_BASE_PATH,
    DATABASE_PATH,
    TEMP_PATH,
    LOG_PATH,
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG
)

def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler()
        ]
    )

def setup_directories():
    dirs = [
        SESSION_BASE_PATH,
        os.path.dirname(DATABASE_PATH),
        TEMP_PATH,
        os.path.dirname(LOG_PATH)
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logging.info(f"Directory ready: {d}")

def initialize_hardware():
    if SIMULATION_MODE:
        logging.info("SIMULATION MODE — hardware control disabled")
        logging.info("All hardware calls will print to console")
    else:
        logging.info("Initializing hardware — Raspberry Pi mode")
        from hardware.led_controller import LEDController
        from hardware.belt_controller import BeltController
        from hardware.sensor_controller import SensorController
        from hardware.camera_controller import CameraController
        leds = LEDController()
        leds.standby()
        logging.info("LEDs initialized — standby mode")

def main():
    setup_logging()
    logging.info("SnapBale starting...")
    logging.info(f"Mode: {'SIMULATION' if SIMULATION_MODE else 'PRODUCTION'}")

    setup_directories()
    logging.info("Directories ready")

    initialize_hardware()

    from storage.storage_manager import StorageManager
    storage = StorageManager()
    storage.initialize_database()
    logging.info("Database ready")

    from server.app import create_app
    app, socketio = create_app()

    logging.info(f"Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    logging.info("Trader interface available at http://192.168.4.1:5000")
    logging.info("Simulation: open http://localhost:5000 in your browser")

    socketio.run(
        app,
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        use_reloader=False
    )

if __name__ == "__main__":
    main()

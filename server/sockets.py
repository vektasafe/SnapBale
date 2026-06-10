# SnapBale — SocketIO Events
# Version: 1.0
# Author: James Kabingu

import logging
from flask_socketio import emit

logger = logging.getLogger(__name__)

_session_manager = None


def set_session_manager(manager):
    global _session_manager
    _session_manager = manager


def register_sockets(socketio):

    @socketio.on("connect")
    def on_connect():
        logger.info("Trader phone connected to SnapBale interface")
        emit("connected", {"message": "Imeunganishwa na SnapBale"})

    @socketio.on("disconnect")
    def on_disconnect():
        logger.info("Trader phone disconnected")

    @socketio.on("start_session")
    def on_start_session():
        if _session_manager:
            import threading
            thread = threading.Thread(
                target=_session_manager.start_session
            )
            thread.daemon = True
            thread.start()
            emit("session_starting", {
                "message": "Kipindi kinaanza..."
            })
        else:
            emit("session_error", {
                "message": "Session manager not ready"
            })

    @socketio.on("end_session")
    def on_end_session():
        if _session_manager:
            _session_manager.end_session()
        else:
            emit("session_error", {
                "message": "No active session"
            })

    @socketio.on("simulate_item")
    def on_simulate_item():
        # Only active in simulation mode
        # Triggers a simulated item passing through the unit
        from config import SIMULATION_MODE
        if SIMULATION_MODE and _session_manager:
            import threading
            def trigger():
                import time
                _session_manager.sensors.simulate_trigger("entry")
                time.sleep(0.1)
                _session_manager.sensors.simulate_clear("entry")
                time.sleep(0.5)
                _session_manager.sensors.simulate_trigger("capture")
                time.sleep(0.5)
                _session_manager.sensors.simulate_clear("capture")
                time.sleep(0.3)
                _session_manager.sensors.simulate_trigger("flipboard")
                time.sleep(0.3)
                _session_manager.sensors.simulate_clear("flipboard")
                time.sleep(0.5)
                _session_manager.sensors.simulate_trigger("capture")
                time.sleep(0.5)
                _session_manager.sensors.simulate_clear("capture")
                time.sleep(0.3)
                _session_manager.sensors.simulate_trigger("exit")
                time.sleep(0.1)
                _session_manager.sensors.simulate_clear("exit")
            thread = threading.Thread(target=trigger)
            thread.daemon = True
            thread.start()
            emit("simulation_triggered", {
                "message": "Simulated item triggered"
            })

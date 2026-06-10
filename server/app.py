# SnapBale — Flask Application
# Version: 1.0
# Author: James Kabingu

import logging
from flask import Flask
from flask_socketio import SocketIO
from config import SIMULATION_MODE

logger = logging.getLogger(__name__)

socketio = SocketIO()


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = "snapbale-v1-secret"
    app.config["SIMULATION_MODE"] = SIMULATION_MODE

    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet")

    from server.routes import register_routes
    register_routes(app, socketio)

    from server.sockets import register_sockets
    register_sockets(socketio)

    logger.info("Flask app created")
    return app, socketio

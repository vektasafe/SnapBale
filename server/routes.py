# SnapBale — Flask Routes
# Version: 1.0
# Author: James Kabingu

import os
import io
import zipfile
import logging
from flask import (
    render_template,
    jsonify,
    send_file,
    request,
    current_app
)
from storage.storage_manager import StorageManager
from server.sockets import set_session_manager
from session.session_manager import SessionManager

logger = logging.getLogger(__name__)

_session_manager = None
_storage = StorageManager()


def register_routes(app, socketio):
    global _session_manager, _storage

    _session_manager = SessionManager(socketio=socketio)
    set_session_manager(_session_manager)

    @app.route("/")
    def connect_screen():
        free, total = _storage.get_storage_free()
        free_gb = round(free / (1024**3), 1)
        incomplete = _storage.check_incomplete_sessions()
        return render_template(
            "connect.html",
            free_gb=free_gb,
            incomplete_sessions=incomplete,
            simulation=current_app.config["SIMULATION_MODE"]
        )

    @app.route("/session")
    def session_screen():
        return render_template(
            "session.html",
            simulation=current_app.config["SIMULATION_MODE"]
        )

    @app.route("/complete/<session_id>")
    def complete_screen(session_id):
        session, items = _storage.get_session_summary(session_id)
        flagged = _storage.get_flagged_items(session_id)
        return render_template(
            "complete.html",
            session=session,
            items=items,
            flagged_count=len(flagged),
            simulation=current_app.config["SIMULATION_MODE"]
        )

    @app.route("/gallery/<session_id>")
    def gallery_screen(session_id):
        session, items = _storage.get_session_summary(session_id)
        return render_template(
            "gallery.html",
            session=session,
            items=items,
            simulation=current_app.config["SIMULATION_MODE"]
        )

    @app.route("/item/<session_id>/<int:item_number>")
    def item_detail_screen(session_id, item_number):
        session, items = _storage.get_session_summary(session_id)
        item = next(
            (i for i in items if i["item_number"] == item_number),
            None
        )
        return render_template(
            "item_detail.html",
            session=session,
            item=item,
            simulation=current_app.config["SIMULATION_MODE"]
        )

    @app.route("/api/image/<path:image_path>")
    def serve_image(image_path):
        full_path = "/" + image_path
        if os.path.exists(full_path):
            return send_file(full_path, mimetype="image/jpeg")
        return jsonify({"error": "Image not found"}), 404

    @app.route("/api/download/<session_id>")
    def download_session(session_id):
        session, items = _storage.get_session_summary(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in items:
                front = item["front_edited"]
                back = item["back_edited"]
                num = item["item_number"]
                if front and os.path.exists(front):
                    zf.write(front, f"item_{num:03d}_front.jpg")
                if back and os.path.exists(back):
                    zf.write(back, f"item_{num:03d}_back.jpg")

        zip_buffer.seek(0)
        filename = f"SnapBale_{session_id}.zip"
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=filename
        )

    @app.route("/api/storage")
    def storage_status():
        free, total = _storage.get_storage_free()
        return jsonify({
            "free_gb": round(free / (1024**3), 1),
            "total_gb": round(total / (1024**3), 1),
            "percent_used": round(((total - free) / total) * 100, 1)
        })

    @app.route("/api/sessions")
    def list_sessions():
        conn = _storage._connect()
        sessions = conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT 20"
        ).fetchall()
        conn.close()
        return jsonify([dict(s) for s in sessions])

# SnapBale — Session Manager
# Version: 1.0
# Author: James Kabingu

import time
import logging
from config import SIMULATION_MODE, BELT_CAPTURE_DELAY
from hardware.belt_controller import BeltController
from hardware.led_controller import LEDController
from hardware.sensor_controller import SensorController
from hardware.camera_controller import CameraController
from hardware.flipboard_controller import FlipBoardController
from processing.image_processor import ImageProcessor
from storage.storage_manager import StorageManager

logger = logging.getLogger(__name__)


class SessionState:
    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


class SessionManager:

    def __init__(self, socketio=None):
        self.state = SessionState.IDLE
        self.session_id = None
        self.session_path = None
        self.item_counter = 0
        self.socketio = socketio

        self.belt = BeltController()
        self.leds = LEDController()
        self.sensors = SensorController()
        self.camera = CameraController()
        self.flipboard = FlipBoardController()
        self.processor = ImageProcessor()
        self.storage = StorageManager()

        self.leds.pulse()
        logger.info("Session manager ready")

    def start_session(self):
        if self.state != SessionState.IDLE:
            logger.warning("Cannot start session — not in idle state")
            return False

        self.session_id, self.session_path = self.storage.create_session()
        self.item_counter = 0
        self.state = SessionState.ACTIVE
        self.leds.on()

        logger.info(f"Session started: {self.session_id}")
        self._emit("session_started", {
            "session_id": self.session_id,
            "message": "Kipindi kimeanza"
        })
        self._run_conveyor_loop()
        return True

    def _run_conveyor_loop(self):
        logger.info("Conveyor loop running — waiting for items")
        while self.state == SessionState.ACTIVE:
            if self.sensors.entry_detected():
                self._process_item()
            time.sleep(0.05)

    def _process_item(self):
        self.state = SessionState.PROCESSING
        self.item_counter += 1
        item_number = self.item_counter
        logger.info(f"Item {item_number:03d} detected at entry")

        self._emit("item_detected", {"item_number": item_number})

        paths = self.storage.get_item_paths(self.session_id, item_number)

        try:
            # Move item to capture zone
            self.belt.forward()
            self._wait_for_sensor("capture", timeout=30)
            self.belt.stop()
            time.sleep(BELT_CAPTURE_DELAY)

            # Front capture
            logger.info(f"Item {item_number:03d} — front capture")
            self.camera.capture_pair(
                paths["front_original"],
                paths["back_original"]
            )

            # Move item to flip board
            self.belt.forward()
            self._wait_for_sensor("flipboard", timeout=15)
            self.belt.stop()

            # Flip item
            self.flipboard.execute_flip_sequence()

            # Move flipped item to capture zone
            self.belt.forward()
            self._wait_for_sensor("capture", timeout=15)
            self.belt.stop()
            time.sleep(BELT_CAPTURE_DELAY)

            # Back capture
            logger.info(f"Item {item_number:03d} — back capture")
            self.camera.capture_back(paths["back_original"])

            # Move item to exit
            self.belt.forward()
            self._wait_for_sensor("exit", timeout=15)
            self.belt.stop()

            logger.info(f"Item {item_number:03d} — exited unit")
            self._emit("counter_update", {"item_number": item_number})

            # Process images in background
            results = self.processor.process_item(
                paths["front_original"],
                paths["back_original"],
                paths["front_edited"],
                paths["back_edited"],
                paths["preview"]
            )

            # Save to database
            self.storage.save_item_record(
                self.session_id,
                item_number,
                paths,
                results["quality_front"],
                results["quality_back"],
                results["flagged"],
                results["flag_reason"],
                results["processing_time_ms"]
            )

            # Push preview to trader phone
            self._emit("item_captured", {
                "item_number": item_number,
                "preview_path": paths["preview"],
                "quality_front": results["quality_front"],
                "quality_back": results["quality_back"],
                "flagged": results["flagged"],
                "flag_reason": results["flag_reason"]
            })

            if results["flagged"]:
                self._emit("item_flagged", {
                    "item_number": item_number,
                    "reason": results["flag_reason"]
                })

        except TimeoutError as e:
            logger.error(f"Item {item_number:03d} — sensor timeout: {e}")
            self.belt.stop()
            self._emit("session_error", {
                "message": str(e),
                "item_number": item_number
            })

        except Exception as e:
            logger.error(f"Item {item_number:03d} — error: {e}")
            self.belt.stop()
            self._emit("session_error", {
                "message": f"Error on item {item_number}: {str(e)}",
                "item_number": item_number
            })

        finally:
            self.state = SessionState.ACTIVE

    def _wait_for_sensor(self, sensor, timeout=30):
        start = time.time()
        while True:
            triggered = False
            if sensor == "entry":
                triggered = self.sensors.entry_detected()
            elif sensor == "capture":
                triggered = self.sensors.capture_detected()
            elif sensor == "flipboard":
                triggered = self.sensors.flipboard_detected()
            elif sensor == "exit":
                triggered = self.sensors.exit_detected()

            if triggered:
                return True

            if time.time() - start > timeout:
                raise TimeoutError(
                    f"Sensor '{sensor}' timeout after {timeout}s"
                )
            time.sleep(0.05)

    def end_session(self):
        if self.state not in [SessionState.ACTIVE, SessionState.PROCESSING]:
            return False

        self.state = SessionState.COMPLETE
        self.belt.stop()
        self.leds.standby()
        self.storage.complete_session(self.session_id)

        session, items = self.storage.get_session_summary(self.session_id)
        flagged = self.storage.get_flagged_items(self.session_id)

        self._emit("session_complete", {
            "session_id": self.session_id,
            "item_count": self.item_counter,
            "flagged_count": len(flagged)
        })

        logger.info(
            f"Session complete: {self.session_id} "
            f"— {self.item_counter} items"
        )

        self.state = SessionState.IDLE
        return True

    def check_storage(self):
        free, total = self.storage.get_storage_free()
        percent_used = ((total - free) / total) * 100
        if percent_used > 80:
            self._emit("storage_warning", {
                "free_gb": round(free / (1024**3), 1),
                "percent_used": round(percent_used, 1)
            })

    def _emit(self, event, data):
        if self.socketio:
            self.socketio.emit(event, data)
        else:
            logger.info(f"[SOCKET] {event}: {data}")

    def cleanup(self):
        self.belt.cleanup()
        self.camera.cleanup()
        self.flipboard.cleanup()
        self.sensors.cleanup()
        self.leds.off()
        logger.info("Session manager cleaned up")

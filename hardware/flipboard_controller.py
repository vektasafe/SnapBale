# SnapBale — Flip Board Controller
# Version: 1.0
# Author: James Kabingu
#
# DESIGN MARKER: Flip board mechanism is pending
# resolution in mechanical design phase.
# Current implementation is based on the clamshell
# hypothesis. Subject to revision.

import time
import logging
from config import SIMULATION_MODE, FLIPBOARD_SERVO_PIN

logger = logging.getLogger(__name__)


class FlipBoardController:

    ANGLE_OPEN = 0
    ANGLE_CLOSED = 90
    ANGLE_FLIPPED = 180

    def __init__(self):
        if not SIMULATION_MODE:
            import pigpio
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("pigpio daemon not running")
            logger.info("Flip board controller initialized — hardware mode")
        else:
            self._position = self.ANGLE_OPEN
            logger.info("Flip board controller initialized — simulation mode")

    def _set_angle(self, angle):
        if not SIMULATION_MODE:
            pulse_width = 500 + (angle / 180.0) * 2000
            self.pi.set_servo_pulsewidth(FLIPBOARD_SERVO_PIN, pulse_width)
        else:
            self._position = angle
            logger.info(f"[SIM] Flip board angle: {angle} degrees")

    def close(self):
        logger.info("Flip board closing — sandwiching item")
        self._set_angle(self.ANGLE_CLOSED)
        time.sleep(0.5)

    def flip(self):
        logger.info("Flip board rotating 180 degrees")
        self._set_angle(self.ANGLE_FLIPPED)
        time.sleep(1.0)

    def open(self):
        logger.info("Flip board opening — item back-side up")
        self._set_angle(self.ANGLE_OPEN)
        time.sleep(0.5)

    def home(self):
        logger.info("Flip board returning to home position")
        self._set_angle(self.ANGLE_OPEN)
        time.sleep(0.3)

    def execute_flip_sequence(self):
        logger.info("Executing full flip sequence")
        self.close()
        self.flip()
        self.open()
        logger.info("Flip sequence complete")

    def cleanup(self):
        self.home()
        if not SIMULATION_MODE:
            self.pi.set_servo_pulsewidth(FLIPBOARD_SERVO_PIN, 0)
            self.pi.stop()

# SnapBale — Sensor Controller
# Version: 1.0
# Author: James Kabingu

import logging
from config import (
    SIMULATION_MODE,
    ENTRY_SENSOR_PIN,
    CAPTURE_SENSOR_PIN,
    FLIPBOARD_SENSOR_PIN,
    EXIT_SENSOR_PIN
)

logger = logging.getLogger(__name__)


class SensorController:

    def __init__(self):
        if not SIMULATION_MODE:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
            for pin in [
                ENTRY_SENSOR_PIN,
                CAPTURE_SENSOR_PIN,
                FLIPBOARD_SENSOR_PIN,
                EXIT_SENSOR_PIN
            ]:
                self.GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.info("Sensor controller initialized — hardware mode")
        else:
            self._sim_states = {
                "entry": False,
                "capture": False,
                "flipboard": False,
                "exit": False
            }
            logger.info("Sensor controller initialized — simulation mode")

    def entry_detected(self):
        if not SIMULATION_MODE:
            return not self.GPIO.input(ENTRY_SENSOR_PIN)
        return self._sim_states["entry"]

    def capture_detected(self):
        if not SIMULATION_MODE:
            return not self.GPIO.input(CAPTURE_SENSOR_PIN)
        return self._sim_states["capture"]

    def flipboard_detected(self):
        if not SIMULATION_MODE:
            return not self.GPIO.input(FLIPBOARD_SENSOR_PIN)
        return self._sim_states["flipboard"]

    def exit_detected(self):
        if not SIMULATION_MODE:
            return not self.GPIO.input(EXIT_SENSOR_PIN)
        return self._sim_states["exit"]

    def simulate_trigger(self, sensor):
        # Only used in simulation mode for testing
        if SIMULATION_MODE and sensor in self._sim_states:
            self._sim_states[sensor] = True
            logger.info(f"[SIM] Sensor triggered: {sensor}")

    def simulate_clear(self, sensor):
        if SIMULATION_MODE and sensor in self._sim_states:
            self._sim_states[sensor] = False

    def cleanup(self):
        if not SIMULATION_MODE:
            self.GPIO.cleanup()

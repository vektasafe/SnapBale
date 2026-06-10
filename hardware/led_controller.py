# SnapBale — LED Controller
# Version: 1.0
# Author: James Kabingu

import logging
from config import (
    SIMULATION_MODE,
    LED_DATA_PIN,
    LED_COUNT,
    LED_BRIGHTNESS,
    LED_COLOR_R,
    LED_COLOR_G,
    LED_COLOR_B
)

logger = logging.getLogger(__name__)


class LEDController:

    def __init__(self):
        if not SIMULATION_MODE:
            from rpi_ws281x import PixelStrip, Color
            self.PixelStrip = PixelStrip
            self.Color = Color
            self.strip = PixelStrip(
                LED_COUNT,
                LED_DATA_PIN,
                800000,
                10,
                False,
                LED_BRIGHTNESS,
                0
            )
            self.strip.begin()
            logger.info("LED controller initialized — hardware mode")
        else:
            logger.info("LED controller initialized — simulation mode")

    def on(self):
        if not SIMULATION_MODE:
            color = self.Color(LED_COLOR_R, LED_COLOR_G, LED_COLOR_B)
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, color)
            self.strip.show()
        else:
            logger.info("[SIM] LEDs ON — full brightness 6500K white")

    def off(self):
        if not SIMULATION_MODE:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.Color(0, 0, 0))
            self.strip.show()
        else:
            logger.info("[SIM] LEDs OFF")

    def standby(self):
        if not SIMULATION_MODE:
            r = LED_COLOR_R // 5
            g = LED_COLOR_G // 5
            b = LED_COLOR_B // 5
            color = self.Color(r, g, b)
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, color)
            self.strip.show()
        else:
            logger.info("[SIM] LEDs STANDBY — 20% brightness")

    def pulse(self):
        if not SIMULATION_MODE:
            self.on()
            import time
            time.sleep(0.2)
            self.off()
            time.sleep(0.1)
            self.on()
            time.sleep(0.2)
            self.standby()
        else:
            logger.info("[SIM] LEDs PULSE — ready signal")

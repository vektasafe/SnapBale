# SnapBale — Belt Controller
# Version: 1.0
# Author: James Kabingu

import logging
from config import (
    SIMULATION_MODE,
    MOTOR_FORWARD_PIN,
    MOTOR_BACKWARD_PIN,
    MOTOR_SPEED_PIN,
    BELT_DEFAULT_SPEED
)

logger = logging.getLogger(__name__)


class BeltController:

    def __init__(self):
        self.speed = BELT_DEFAULT_SPEED
        self.running = False
        self.direction = None
        if not SIMULATION_MODE:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setup(MOTOR_FORWARD_PIN, GPIO.OUT)
            self.GPIO.setup(MOTOR_BACKWARD_PIN, GPIO.OUT)
            self.pwm = self.GPIO.PWM(MOTOR_SPEED_PIN, 1000)
            self.pwm.start(0)
            logger.info("Belt controller initialized — hardware mode")
        else:
            logger.info("Belt controller initialized — simulation mode")

    def forward(self):
        self.running = True
        self.direction = "forward"
        if not SIMULATION_MODE:
            self.GPIO.output(MOTOR_FORWARD_PIN, self.GPIO.HIGH)
            self.GPIO.output(MOTOR_BACKWARD_PIN, self.GPIO.LOW)
            self.pwm.ChangeDutyCycle(self.speed)
        else:
            logger.info(f"[SIM] Belt running forward at {self.speed}%")

    def reverse(self):
        self.running = True
        self.direction = "reverse"
        if not SIMULATION_MODE:
            self.GPIO.output(MOTOR_FORWARD_PIN, self.GPIO.LOW)
            self.GPIO.output(MOTOR_BACKWARD_PIN, self.GPIO.HIGH)
            self.pwm.ChangeDutyCycle(self.speed)
        else:
            logger.info(f"[SIM] Belt running reverse at {self.speed}%")

    def stop(self):
        self.running = False
        self.direction = None
        if not SIMULATION_MODE:
            self.GPIO.output(MOTOR_FORWARD_PIN, self.GPIO.LOW)
            self.GPIO.output(MOTOR_BACKWARD_PIN, self.GPIO.LOW)
            self.pwm.ChangeDutyCycle(0)
        else:
            logger.info("[SIM] Belt stopped")

    def set_speed(self, percent):
        self.speed = max(0, min(100, percent))
        if not SIMULATION_MODE and self.running:
            self.pwm.ChangeDutyCycle(self.speed)
        else:
            logger.info(f"[SIM] Belt speed set to {self.speed}%")

    def cleanup(self):
        self.stop()
        if not SIMULATION_MODE:
            self.pwm.stop()
            self.GPIO.cleanup()

# SnapBale — Camera Controller
# Version: 1.0
# Author: James Kabingu

import os
import logging
from config import (
    SIMULATION_MODE,
    CAMERA_RESOLUTION,
    PREVIEW_RESOLUTION
)

logger = logging.getLogger(__name__)


class CameraController:

    def __init__(self):
        if not SIMULATION_MODE:
            from picamera2 import Picamera2
            self.cam_top = Picamera2(0)
            self.cam_front = Picamera2(1)
            config = self.cam_top.create_still_configuration(
                main={"size": CAMERA_RESOLUTION}
            )
            self.cam_top.configure(config)
            self.cam_top.start()
            logger.info("Camera controller initialized — hardware mode")
        else:
            logger.info("Camera controller initialized — simulation mode")

    def capture_pair(self, front_path, back_path):
        os.makedirs(os.path.dirname(front_path), exist_ok=True)
        if not SIMULATION_MODE:
            self.cam_top.capture_file(front_path)
            logger.info(f"Captured top-down: {front_path}")
        else:
            self._create_sim_image(front_path, "FRONT CAPTURE")
            logger.info(f"[SIM] Simulated capture: {front_path}")

    def capture_back(self, back_path):
        os.makedirs(os.path.dirname(back_path), exist_ok=True)
        if not SIMULATION_MODE:
            self.cam_top.capture_file(back_path)
            logger.info(f"Captured back: {back_path}")
        else:
            self._create_sim_image(back_path, "BACK CAPTURE")
            logger.info(f"[SIM] Simulated back capture: {back_path}")

    def _create_sim_image(self, path, label):
        # Creates a placeholder image for simulation testing
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", CAMERA_RESOLUTION, (230, 230, 230))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 3956, 2940], fill=(200, 200, 200))
        draw.text((1800, 1500), label, fill=(100, 100, 100))
        img.save(path, "JPEG", quality=85)

    def cleanup(self):
        if not SIMULATION_MODE:
            self.cam_top.stop()
            self.cam_front.stop()

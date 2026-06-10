# SnapBale — Image Processor
# Version: 1.0
# Author: James Kabingu

import os
import time
import logging
import shutil
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import cv2
import numpy as np
from config import BLUR_THRESHOLD, MIN_ITEM_COVERAGE

logger = logging.getLogger(__name__)


class ImageProcessor:

    def __init__(self):
        self.rembg_available = self._check_rembg()

    def _check_rembg(self):
        try:
            import rembg
            logger.info("rembg available — background removal enabled")
            return True
        except ImportError:
            logger.warning("rembg not available — background removal disabled")
            return False

    def process_item(self, front_raw_path, back_raw_path,
                     front_edited_path, back_edited_path,
                     preview_path):
        start_time = time.time()
        results = {
            "quality_front": "pass",
            "quality_back": "pass",
            "flagged": False,
            "flag_reason": None,
            "processing_time_ms": 0
        }

        try:
            # Process front image
            logger.info(f"Processing front: {front_raw_path}")
            front_quality = self._process_single(
                front_raw_path,
                front_edited_path
            )

            # Process back image
            logger.info(f"Processing back: {back_raw_path}")
            back_quality = self._process_single(
                back_raw_path,
                back_edited_path
            )

            results["quality_front"] = front_quality["status"]
            results["quality_back"] = back_quality["status"]

            # Flag item if either image fails quality check
            if front_quality["status"] == "fail" or \
               back_quality["status"] == "fail":
                results["flagged"] = True
                reasons = []
                if front_quality["status"] == "fail":
                    reasons.append(f"Front: {front_quality['reason']}")
                if back_quality["status"] == "fail":
                    reasons.append(f"Back: {back_quality['reason']}")
                results["flag_reason"] = " | ".join(reasons)
                logger.warning(f"Item flagged: {results['flag_reason']}")

            # Generate preview composite
            self._generate_preview(
                front_edited_path,
                back_edited_path,
                preview_path
            )

        except Exception as e:
            logger.error(f"Processing error: {e}")
            # Save originals as edited if processing fails
            # Trader still gets images even if processing fails
            if os.path.exists(front_raw_path):
                shutil.copy2(front_raw_path, front_edited_path)
            if os.path.exists(back_raw_path):
                shutil.copy2(back_raw_path, back_edited_path)
            results["flagged"] = True
            results["flag_reason"] = f"Processing error: {str(e)}"

        results["processing_time_ms"] = int(
            (time.time() - start_time) * 1000
        )
        logger.info(
            f"Processing complete in {results['processing_time_ms']}ms"
        )
        return results

    def _process_single(self, input_path, output_path):
        quality = {"status": "pass", "reason": None}

        if not os.path.exists(input_path):
            return {"status": "fail", "reason": "Image file not found"}

        img = Image.open(input_path).convert("RGB")

        # Step 1 — Background removal
        if self.rembg_available:
            img = self._remove_background(img)
        else:
            logger.warning("Skipping background removal — rembg unavailable")

        # Step 2 — Auto correction
        img = self._auto_correct(img)

        # Step 3 — Crop and center
        img = self._crop_and_center(img)

        # Step 4 — Save edited copy
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "JPEG", quality=95)

        # Step 5 — Quality check on saved file
        quality = self._quality_check(output_path)

        return quality

    def _remove_background(self, img):
        try:
            from rembg import remove
            img_bytes = img.tobytes()
            # rembg works on bytes, convert back to PIL
            import io
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            output_bytes = remove(buffer.read())
            result = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            # Replace transparent background with white
            background = Image.new("RGBA", result.size, (255, 255, 255, 255))
            background.paste(result, mask=result.split()[3])
            return background.convert("RGB")
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return img

    def _auto_correct(self, img):
        # Auto contrast
        img = ImageOps.autocontrast(img, cutoff=0.5)
        # Slight sharpness enhancement
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        # Slight color enhancement
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.1)
        return img

    def _crop_and_center(self, img):
        # Convert to numpy for OpenCV processing
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        # Find non-white pixels (item pixels)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        coords = cv2.findNonZero(thresh)
        if coords is None:
            return img
        x, y, w, h = cv2.boundingRect(coords)
        # Add 5% padding around item
        pad_x = int(w * 0.05)
        pad_y = int(h * 0.05)
        x = max(0, x - pad_x)
        y = max(0, y - pad_y)
        w = min(img_array.shape[1] - x, w + 2 * pad_x)
        h = min(img_array.shape[0] - y, h + 2 * pad_y)
        cropped = img.crop((x, y, x + w, y + h))
        # Place on square white canvas
        size = max(w, h)
        canvas = Image.new("RGB", (size, size), (255, 255, 255))
        offset_x = (size - w) // 2
        offset_y = (size - h) // 2
        canvas.paste(cropped, (offset_x, offset_y))
        return canvas

    def _quality_check(self, image_path):
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            return {"status": "fail", "reason": "Cannot read saved image"}

        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Blur check — Laplacian variance
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < BLUR_THRESHOLD:
            return {
                "status": "fail",
                "reason": f"Image too blurry (score: {blur_score:.1f})"
            }

        # Item coverage check
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        item_pixels = cv2.countNonZero(thresh)
        total_pixels = gray.shape[0] * gray.shape[1]
        coverage = item_pixels / total_pixels

        if coverage < MIN_ITEM_COVERAGE:
            return {
                "status": "fail",
                "reason": f"Item too small in frame (coverage: {coverage:.1%})"
            }

        return {"status": "pass", "reason": None}

    def _generate_preview(self, front_path, back_path, preview_path):
        try:
            preview_width = 800
            preview_height = 400
            canvas = Image.new("RGB", (preview_width, preview_height),
                               (245, 245, 245))

            if os.path.exists(front_path):
                front = Image.open(front_path)
                front.thumbnail((390, 380))
                canvas.paste(front, (5, 10))

            if os.path.exists(back_path):
                back = Image.open(back_path)
                back.thumbnail((390, 380))
                canvas.paste(back, (405, 10))

            os.makedirs(os.path.dirname(preview_path), exist_ok=True)
            canvas.save(preview_path, "JPEG", quality=75)
            logger.info(f"Preview saved: {preview_path}")

        except Exception as e:
            logger.error(f"Preview generation failed: {e}")

    def test_with_sample_image(self, image_path):
        # For simulation testing — process a single real image
        # and verify the pipeline works end to end
        logger.info(f"Testing processor with: {image_path}")
        test_output = image_path.replace(".jpg", "_processed.jpg")
        test_preview = image_path.replace(".jpg", "_preview.jpg")
        results = self.process_item(
            image_path, image_path,
            test_output, test_output,
            test_preview
        )
        logger.info(f"Test results: {results}")
        return results

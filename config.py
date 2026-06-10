# SnapBale Configuration
# Version: 1.0
# Author: James Kabingu

# -----------------------------------------------
# SIMULATION MODE
# Set to True when running on laptop without Pi
# Set to False when running on Raspberry Pi 4
# -----------------------------------------------
SIMULATION_MODE = True

# -----------------------------------------------
# HARDWARE PINS (GPIO BCM numbering)
# Only used when SIMULATION_MODE = False
# -----------------------------------------------
MOTOR_FORWARD_PIN = 17
MOTOR_BACKWARD_PIN = 18
MOTOR_SPEED_PIN = 27

ENTRY_SENSOR_PIN = 22
CAPTURE_SENSOR_PIN = 23
FLIPBOARD_SENSOR_PIN = 24
EXIT_SENSOR_PIN = 25

LED_DATA_PIN = 12

FLIPBOARD_SERVO_PIN = 13

BUTTON_PIN = 26
STATUS_LED_PIN = 19
BUZZER_PIN = 6

# -----------------------------------------------
# LED CONFIGURATION
# -----------------------------------------------
LED_COUNT = 120          # Total LEDs across all strips
LED_BRIGHTNESS = 255     # 0 to 255
LED_COLOR_R = 255        # 6500K daylight white approximation
LED_COLOR_G = 250
LED_COLOR_B = 240

# -----------------------------------------------
# CONVEYOR CONFIGURATION
# -----------------------------------------------
BELT_DEFAULT_SPEED = 60      # Percent 0-100
BELT_CAPTURE_DELAY = 0.5     # Seconds to wait after belt stops
                             # before firing camera (motion settle)

# -----------------------------------------------
# CAMERA CONFIGURATION
# -----------------------------------------------
CAMERA_RESOLUTION = (4056, 3040)   # Full resolution capture
PREVIEW_RESOLUTION = (800, 600)    # Preview for trader interface

# -----------------------------------------------
# SESSION CONFIGURATION
# -----------------------------------------------
SESSION_BASE_PATH = "/snapbale/sessions"
DATABASE_PATH = "/snapbale/database/snapbale.db"
TEMP_PATH = "/snapbale/temp/previews"
LOG_PATH = "/snapbale/logs/snapbale.log"

# On laptop (simulation), use local paths
if SIMULATION_MODE:
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SESSION_BASE_PATH = os.path.join(BASE_DIR, "data/sessions")
    DATABASE_PATH = os.path.join(BASE_DIR, "data/snapbale.db")
    TEMP_PATH = os.path.join(BASE_DIR, "data/temp")
    LOG_PATH = os.path.join(BASE_DIR, "data/snapbale.log")

# -----------------------------------------------
# IMAGE PROCESSING
# -----------------------------------------------
BLUR_THRESHOLD = 100         # Laplacian variance threshold
                             # Below this = blurry, flag item
MIN_ITEM_COVERAGE = 0.20     # Item must cover 20% of frame
                             # Below this = misaligned, flag item

# -----------------------------------------------
# FLASK SERVER
# -----------------------------------------------
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = SIMULATION_MODE   # Debug only in simulation

# -----------------------------------------------
# WIFI HOTSPOT
# -----------------------------------------------
HOTSPOT_SSID_PREFIX = "SnapBale_"
HOTSPOT_IP = "192.168.4.1"

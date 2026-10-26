import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
FACES_DIR = os.path.join(DATA_DIR, 'faces')
DB_PATH = os.path.join(DATA_DIR, 'vision_guard.db')
HAAR_CASCADE_PATH = os.path.join(DATA_DIR, 'haarcascade_frontalface_default.xml')

# Ensure directories exist
for directory in [DATA_DIR, STATIC_DIR, UPLOADS_DIR, FACES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Camera Settings
DEFAULT_CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 30

# Vision Guard Default Settings
DEFAULT_SETTINGS = {
    "active_mode": "intrusion",  # Options: 'intrusion', 'face', 'drowsiness', 'tracking'
    "motion_sensitivity": 25,    # Threshold for pixel variance
    "min_contour_area": 800,     # Minimum area to consider as motion (px)
    "roi": {"x": 50, "y": 50, "w": 300, "h": 300, "enabled": True}, # ROI Bounding Box in percentage or px
    "ear_threshold": 0.22,       # Eye Aspect Ratio threshold for drowsiness
    "ear_consec_frames": 20,     # Consecutive frames eyes must be closed
    "face_confidence_threshold": 65.0, # Confidence for face match (LBPH lower is better)
    "alert_sound": True,
    "save_snapshots": True,
    "cooldown_seconds": 3        # Cooldown between consecutive alert logs
}

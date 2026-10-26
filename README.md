# 🛡️ VISION GUARD — Computer Vision Security & Safety Analytics System

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.13-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-00C7B7?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**Vision Guard** is an end-to-end, real-time Computer Vision surveillance and workplace safety analytics platform engineered for internship demonstration and industrial applications. Built with **OpenCV**, **MediaPipe**, **Python**, and a **Glassmorphism Web Dashboard**, Vision Guard integrates real-time optical stream processing, multi-zone ROI intrusion detection, AI facial recognition access control, operator fatigue/drowsiness monitoring, object tracking, event logging, and downloadable audit reporting.

---

## 🌟 Key Modules & Features

```
                                  ┌───────────────────────────┐
                                  │   LIVE OPTICAL CAMERA     │
                                  └─────────────┬─────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │   MULTITHREADED STREAM    │
                                  └─────────────┬─────────────┘
                                                │
             ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
             │                  │                               │                  │
    ┌────────┴────────┐┌────────┴────────┐             ┌────────┴────────┐┌────────┴────────┐
    │ PERIMETER GUARD ││  ACCESS GUARD   │             │  HEALTH GUARD   ││ ANALYTICS GUARD │
    │  (ROI Motion)   ││(Face Recognizer)│             │ (Drowsiness/EAR)││(Centroid Tracker)│
    └────────┬────────┘└────────┬────────┘             └────────┬────────┘└────────┬────────┘
             │                  │                               │                  │
             └──────────────────┴───────────────┬───────────────┴──────────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │  AUTOMATED AUDIT ENGINE   │
                                  │(SQLite DB / Snapshots/ Sound)│
                                  └─────────────┬─────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │   RESPONSIVE DASHBOARD    │
                                  │   (Flask / MJPEG / Web UI)│
                                  └───────────────────────────┘
```

### 1. 🛡️ Perimeter Guard (Intrusion & Motion Detection)
- **Background Subtraction**: Employs OpenCV `MOG2` algorithm with adaptive thresholding to distinguish moving subjects from static backgrounds.
- **ROI Restricted Zone**: Interactive Region of Interest bounding box with real-time breach detection, visual red alert border triggers, and timestamped snapshot recording.

### 2. 👤 Access Guard (AI Face Registration & Recognition)
- **Face Detection**: Fast facial localization using OpenCV Haar Cascade Classifier.
- **LBPH Recognition**: Local Binary Patterns Histograms (`LBPHFaceRecognizer`) algorithm for invariant local texture face recognition.
- **Face Studio Enrollment**: Interactive web-based face registration tool allowing instant webcam snapshot collection and real-time model re-training.

### 3. 😴 Health Guard (Drowsiness & Fatigue Monitor)
- **Facial Landmark Mesh**: Uses MediaPipe 468-point Face Mesh for precise 3D eye contour extraction.
- **Eye Aspect Ratio (EAR)**: Computes mathematical EAR scalar:
  $$\text{EAR} = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 \cdot ||p_1 - p_4||}$$
- **Fatigue Warning**: Triggers immediate audible siren and alert log when closed eye state exceeds configurable frame threshold (> 1.5 seconds).

### 4. 🎯 Analytics Guard (Centroid Object Tracker)
- **Euclidean Tracker**: Assigns persistent IDs to motion blobs across frames using Euclidean distance minimization.
- **Trajectory Trails**: Visualizes movement history lines, direction velocity vectors, and active/cumulative object statistics.

---

## 📁 Directory Structure

```
VISION GUARD/
├── app.py                      # Flask web server & streaming API routes
├── run_demo.py                 # Standalone native OpenCV window GUI script
├── config.py                   # System configuration & threshold defaults
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation & presentation guide
├── src/
│   ├── __init__.py
│   ├── database.py             # SQLite Manager for security events & face profiles
│   ├── utils.py                # OpenCV HUD overlay drawing & snapshot utilities
│   └── vision/
│       ├── __init__.py
│       ├── camera.py           # Threaded OpenCV Video Capture with automatic fallback
│       ├── motion_detector.py  # MOG2 Motion & ROI intrusion detector
│       ├── face_guard.py       # OpenCV Haar + LBPH Face Recognizer
│       ├── drowsiness_guard.py # Eye Aspect Ratio (EAR) & Fatigue Monitor
│       └── tracker.py          # Centroid Object Tracker & Path Renderer
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphism dark UI stylesheet
│   ├── js/
│   │   └── app.js              # Web Audio API, AJAX polling & mode controls
│   └── uploads/                # Saved security alert snapshots (.jpg)
├── templates/
│   └── index.html              # Modern single-page web dashboard
├── data/
│   ├── vision_guard.db         # SQLite Database (auto-generated)
│   ├── sample_video.mp4        # Pre-generated CCTV sample feed for offline demo
│   └── faces/                  # Registered face dataset folders
└── scripts/
    └── generate_sample_video.py # Synthetic security feed generator
```

---

## 🚀 Quick Start & Installation Guide

### Prerequisites
- **Python 3.8+** installed on system.
- Webcam (optional — if no webcam is connected, system automatically switches to sample CCTV feed).

### 1. Clone & Install Dependencies
```bash
# Navigate to project directory
cd "VISION GUARD"

# Install required Python packages
pip install -r requirements.txt
```

### 2. Run the Web Dashboard (Recommended)
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

### 3. Run Standalone Desktop OpenCV Window (For Offline Demos)
If you prefer running a native OpenCV desktop window without starting a web browser:
```bash
python run_demo.py
```
**Keyboard Shortcuts in Window:**
- `1`: Perimeter Intrusion Guard
- `2`: Access Face Recognition Guard
- `3`: Health & Drowsiness Guard
- `4`: Analytics Motion Tracker
- `q`: Quit Application

---

## 📊 Database & Reports

Vision Guard stores event logs in an embedded SQLite database (`data/vision_guard.db`).
- **Exporting Reports**: Click **"Download CSV Report"** in the web dashboard or fetch `/api/export_logs` to export timestamped event logs, alert types, severity levels, and snapshot file paths.

---

## 🎓 Internship Project Presentation Guide

When presenting this project to your evaluator or internship supervisor:

1. **Highlight the Modular Architecture**: Point out the decoupled `src/vision/` package separates video acquisition, feature extraction, AI decision logic, and rendering.
2. **Demonstrate Hardware Flexibility**: Mention that the system includes multi-threading and an automatic video fallback mechanism (`camera.py`) so it runs seamlessly on webcams, security RTSP feeds, or sample test files.
3. **Show Real-time Performance**: Showcase the live FPS meter, interactive mode switching, audio alarms (Web Audio API), and instant CSV report generation.
4. **Demonstrate Face Enrollment**: Register your face via the web dashboard modal, position your face in view, and show the instant authorized name tag overlay!

---

## 📄 License
This project is created for educational and internship demonstration purposes under the **MIT License**.

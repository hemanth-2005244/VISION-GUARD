from flask import Flask, render_template, Response, jsonify, request, send_file
import cv2
import time
import os
import csv
import io
import datetime

from config import DEFAULT_SETTINGS, DB_PATH, UPLOADS_DIR, FACES_DIR, FRAME_WIDTH, FRAME_HEIGHT
from src.database import DatabaseManager
from src.utils import draw_hud_header, draw_alert_banner, save_snapshot
from src.vision.camera import ThreadedCamera
from src.vision.motion_detector import MotionDetector
from src.vision.face_guard import FaceGuard
from src.vision.drowsiness_guard import DrowsinessGuard
from src.vision.tracker import CentroidTracker

app = Flask(__name__)
db = DatabaseManager(DB_PATH)

# Global State & CV Engine Instantiation
settings = DEFAULT_SETTINGS.copy()
camera = ThreadedCamera(source=0, width=FRAME_WIDTH, height=FRAME_HEIGHT)
motion_detector = MotionDetector(sensitivity=settings["motion_sensitivity"], min_area=settings["min_contour_area"])
face_guard = FaceGuard(faces_dir=FACES_DIR, confidence_threshold=settings["face_confidence_threshold"])
drowsiness_guard = DrowsinessGuard(ear_threshold=settings["ear_threshold"], consec_frames=settings["ear_consec_frames"])
tracker = CentroidTracker()

last_alert_time = 0

def generate_video_stream():
    """Generates continuous MJPEG video stream with dynamic OpenCV overlay processing."""
    global last_alert_time
    
    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.03)
            continue

        fps = camera.get_fps()
        mode = settings.get("active_mode", "intrusion")
        now = time.time()
        cooldown = settings.get("cooldown_seconds", 3)

        alert_triggered = False
        alert_title = ""
        alert_msg = ""
        alert_type = ""

        # --- MODE 1: Intrusion & Motion Detection ---
        if mode == "intrusion":
            frame, is_intrusion, breach_boxes = motion_detector.process_frame(frame, settings.get("roi"))
            if is_intrusion:
                alert_triggered = True
                alert_type = "Intrusion"
                alert_title = "RESTRICTED AREA BREACH"
                alert_msg = f"Motion detected inside security ROI zone!"

        # --- MODE 2: Face Recognition Access Guard ---
        elif mode == "face":
            frame, unknown_detected, faces_list = face_guard.process_frame(frame)
            if unknown_detected:
                alert_triggered = True
                alert_type = "Unknown Face"
                alert_title = "UNAUTHORIZED PERSON DETECTED"
                alert_msg = f"Unregistered facial pattern detected in view!"

        # --- MODE 3: Drowsiness & Health Guard ---
        elif mode == "drowsiness":
            frame, is_drowsy, stats = drowsiness_guard.process_frame(frame)
            if is_drowsy:
                alert_triggered = True
                alert_type = "Drowsiness"
                alert_title = "OPERATOR FATIGUE WARNING"
                alert_msg = f"Eye closure detected for > {settings.get('ear_consec_frames')} frames!"

        # --- MODE 4: Motion Tracking Analytics ---
        elif mode == "tracking":
            _, _, breach_boxes = motion_detector.process_frame(frame.copy(), None)
            frame, object_count = tracker.render_analytics(frame, breach_boxes)

        # Trigger Database Logging & Snapshot Capture on Cooldown
        if alert_triggered and (now - last_alert_time > cooldown):
            last_alert_time = now
            snapshot_url = None
            if settings.get("save_snapshots", True):
                snapshot_url = save_snapshot(frame.copy(), UPLOADS_DIR, prefix=alert_type.lower().replace(" ", "_"))
            
            db.log_alert(
                alert_type=alert_type,
                severity="HIGH",
                message=alert_msg,
                snapshot_path=snapshot_url
            )

        # Draw HUD overlays
        if alert_triggered:
            frame = draw_alert_banner(frame, alert_msg, alert_type=alert_title)
        
        frame = draw_hud_header(frame, title="VISION GUARD AI", mode=mode, fps=fps)

        # Encode frame to JPEG format
        ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')


@app.route('/')
def index():
    """Main Dashboard Web Page."""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """MJPEG Streaming Feed Route."""
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Get or update global configuration settings."""
    global settings
    if request.method == 'POST':
        data = request.json or {}
        for k, v in data.items():
            if k in settings:
                settings[k] = v
        
        # Update CV engine parameters
        motion_detector.update_settings(
            sensitivity=settings.get("motion_sensitivity"),
            min_area=settings.get("min_contour_area")
        )
        face_guard.confidence_threshold = settings.get("face_confidence_threshold", 65.0)
        drowsiness_guard.ear_threshold = settings.get("ear_threshold", 0.22)
        drowsiness_guard.consec_frames = settings.get("ear_consec_frames", 20)

        return jsonify({"status": "success", "settings": settings})
    return jsonify(settings)


@app.route('/api/roi', methods=['POST'])
def update_roi():
    """Update ROI bounding box coordinates."""
    data = request.json or {}
    settings["roi"] = {
        "x": float(data.get("x", 50)),
        "y": float(data.get("y", 50)),
        "w": float(data.get("w", 200)),
        "h": float(data.get("h", 200)),
        "enabled": bool(data.get("enabled", True))
    }
    return jsonify({"status": "success", "roi": settings["roi"]})


@app.route('/api/alerts', methods=['GET', 'DELETE'])
def handle_alerts():
    """Get recent alerts or clear alert logs."""
    if request.method == 'DELETE':
        db.clear_alerts()
        return jsonify({"status": "success", "message": "Alert logs cleared"})
    
    alerts = db.get_recent_alerts(limit=50)
    return jsonify(alerts)


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retrieve dynamic system analytics stats."""
    summary = db.get_summary_stats()
    summary["fps"] = round(camera.get_fps(), 1)
    summary["active_mode"] = settings.get("active_mode", "intrusion")
    summary["camera_fallback"] = camera.using_fallback
    return jsonify(summary)


@app.route('/api/register_face', methods=['POST'])
def register_face():
    """Register a new face profile by capturing current webcam frame samples."""
    data = request.json or {}
    person_name = data.get("name", "").strip()
    role = data.get("role", "Staff").strip()

    if not person_name:
        return jsonify({"status": "error", "message": "Person name is required"}), 400

    # Capture 5 frames to construct training samples
    captured_count = 0
    for idx in range(10):
        frame = camera.get_frame()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_guard.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        
        for (x, y, w, h) in faces:
            face_guard.save_face_sample(frame, (x, y, w, h), person_name, captured_count)
            captured_count += 1
            break
        time.sleep(0.1)

    if captured_count > 0:
        face_guard.train_model()
        db.register_person(person_name, role=role, samples_count=captured_count)
        return jsonify({"status": "success", "message": f"Registered '{person_name}' with {captured_count} face samples."})
    else:
        return jsonify({"status": "error", "message": "No clear face detected in camera view! Ensure face is visible."}), 400


@app.route('/api/persons', methods=['GET'])
def get_persons():
    """Get list of registered face profiles."""
    persons = db.get_registered_persons()
    return jsonify(persons)


@app.route('/api/export_logs', methods=['GET'])
def export_logs():
    """Export alert logs as downloadable CSV report."""
    alerts = db.get_recent_alerts(limit=500)
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Timestamp', 'Alert Type', 'Severity', 'Message', 'Snapshot Path'])
    
    for a in alerts:
        cw.writerow([a['id'], a['timestamp'], a['alert_type'], a['severity'], a['message'], a['snapshot_path']])
    
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    filename = f"vision_guard_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name=filename)


if __name__ == '__main__':
    print("\n=======================================================")
    print("  VISION GUARD COMPUTER VISION SYSTEM STARTING")
    print("=======================================================")
    print("-> Local Dashboard URL: http://127.0.0.1:5000")
    print("=======================================================\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

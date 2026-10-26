import cv2
import datetime
import os
import numpy as np

def draw_hud_header(frame, title="VISION GUARD", mode="MONITORING", fps=0.0):
    """Draw a futuristic high-tech HUD overlay header on the top of the video frame."""
    h, w, _ = frame.shape
    
    # Header overlay bar with gradient feel
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 45), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Title & Mode
    cv2.putText(frame, title, (15, 30), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 240, 255), 2, cv2.LINE_AA)
    
    mode_text = f"MODE: {mode.upper()}"
    cv2.putText(frame, mode_text, (200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    # Live FPS Badge
    fps_text = f"FPS: {fps:.1f}"
    cv2.putText(frame, fps_text, (w - 110, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 1, cv2.LINE_AA)

    # Timestamp footer line
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, now_str, (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

    # Status dot (green pulsing effect)
    cv2.circle(frame, (w - 130, 25), 5, (0, 255, 0), -1)

    return frame

def draw_alert_banner(frame, message, alert_type="INTRUSION DETECTED"):
    """Draw a bold red alert banner on top of the frame when security alert is triggered."""
    h, w, _ = frame.shape
    
    # Red glowing banner
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 45), (w, 90), (0, 0, 180), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    # Alert Text
    cv2.putText(frame, f"⚠️ ALERT: {alert_type}", (15, 72), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, message, (w - 300, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 255), 1, cv2.LINE_AA)

    # Red Border
    cv2.rectangle(frame, (0, 0), (w-1, h-1), (0, 0, 255), 4)

    return frame

def save_snapshot(frame, uploads_dir, prefix="alert"):
    """Save an alert snapshot frame to uploads folder and return relative URL path."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
    filename = f"{prefix}_{timestamp}.jpg"
    filepath = os.path.join(uploads_dir, filename)
    
    cv2.imwrite(filepath, frame)
    return f"/static/uploads/{filename}"

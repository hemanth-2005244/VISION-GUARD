import cv2
import time
import os
import sys

from config import DEFAULT_SETTINGS, FACES_DIR, UPLOADS_DIR, FRAME_WIDTH, FRAME_HEIGHT
from src.utils import draw_hud_header, draw_alert_banner
from src.vision.camera import ThreadedCamera
from src.vision.motion_detector import MotionDetector
from src.vision.face_guard import FaceGuard
from src.vision.drowsiness_guard import DrowsinessGuard
from src.vision.tracker import CentroidTracker

def main():
    print("=========================================================")
    print("  VISION GUARD - STANDALONE OPENCV NATIVE WINDOW DEMO")
    print("=========================================================")
    print("Keyboard Shortcuts:")
    print("  [1] Switch to Perimeter Intrusion Guard")
    print("  [2] Switch to Access Face Recognition Guard")
    print("  [3] Switch to Drowsiness & Fatigue Guard")
    print("  [4] Switch to Motion Analytics Tracker")
    print("  [q] Quit Application")
    print("=========================================================\n")

    settings = DEFAULT_SETTINGS.copy()
    camera = ThreadedCamera(source=0, width=FRAME_WIDTH, height=FRAME_HEIGHT)
    motion_detector = MotionDetector(sensitivity=settings["motion_sensitivity"], min_area=settings["min_contour_area"])
    face_guard = FaceGuard(faces_dir=FACES_DIR, confidence_threshold=settings["face_confidence_threshold"])
    drowsiness_guard = DrowsinessGuard(ear_threshold=settings["ear_threshold"], consec_frames=settings["ear_consec_frames"])
    tracker = CentroidTracker()

    mode = "intrusion"

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.03)
                continue

            fps = camera.get_fps()
            alert_triggered = False
            alert_title = ""
            alert_msg = ""
            alert_type = ""

            if mode == "intrusion":
                frame, is_intrusion, breach_boxes = motion_detector.process_frame(frame, settings.get("roi"))
                if is_intrusion:
                    alert_triggered = True
                    alert_type = "Intrusion"
                    alert_title = "RESTRICTED AREA BREACH"
                    alert_msg = "Motion detected in security ROI zone!"

            elif mode == "face":
                frame, unknown_detected, faces_list = face_guard.process_frame(frame)
                if unknown_detected:
                    alert_triggered = True
                    alert_type = "Unknown Face"
                    alert_title = "UNAUTHORIZED PERSON"
                    alert_msg = "Unregistered face detected!"

            elif mode == "drowsiness":
                frame, is_drowsy, stats = drowsiness_guard.process_frame(frame)
                if is_drowsy:
                    alert_triggered = True
                    alert_type = "Drowsiness"
                    alert_title = "FATIGUE ALARM"
                    alert_msg = "Eye closure detected!"

            elif mode == "tracking":
                _, _, breach_boxes = motion_detector.process_frame(frame.copy(), None)
                frame, object_count = tracker.render_analytics(frame, breach_boxes)

            if alert_triggered:
                frame = draw_alert_banner(frame, alert_msg, alert_type=alert_title)

            frame = draw_hud_header(frame, title="VISION GUARD AI", mode=mode, fps=fps)

            cv2.imshow("Vision Guard - OpenCV Interactive Window", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('1'):
                mode = "intrusion"
                print("Switched to Intrusion Mode")
            elif key == ord('2'):
                mode = "face"
                print("Switched to Face Recognition Mode")
            elif key == ord('3'):
                mode = "drowsiness"
                print("Switched to Drowsiness Mode")
            elif key == ord('4'):
                mode = "tracking"
                print("Switched to Tracking Mode")

    finally:
        camera.stop()
        cv2.destroyAllWindows()
        print("Vision Guard stopped clean.")

if __name__ == "__main__":
    main()

import cv2
import numpy as np

class MotionDetector:
    """Intrusion & Motion Detection Engine with Customizable ROI (Region of Interest) Guard Zones."""
    def __init__(self, sensitivity=25, min_area=800):
        self.sensitivity = sensitivity
        self.min_area = min_area
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=sensitivity, detectShadows=True)
        self.last_intruding_boxes = []

    def update_settings(self, sensitivity=None, min_area=None):
        if sensitivity is not None:
            self.sensitivity = sensitivity
            self.bg_subtractor.setVarThreshold(sensitivity)
        if min_area is not None:
            self.min_area = min_area

    def process_frame(self, frame, roi_config=None):
        """
        Process frame to detect motion contours and verify ROI breach.
        Returns: annotated_frame, is_intrusion, list_of_breach_boxes
        """
        h, w, _ = frame.shape
        fg_mask = self.bg_subtractor.apply(frame)

        # Morphological filtering to clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Parse ROI Box (Values expected in px or relative percentage)
        roi_box = None
        if roi_config and roi_config.get("enabled", True):
            rx = int(roi_config.get("x", 50) * w / 100) if roi_config.get("x", 50) <= 100 else int(roi_config.get("x", 50))
            ry = int(roi_config.get("y", 50) * h / 100) if roi_config.get("y", 50) <= 100 else int(roi_config.get("y", 50))
            rw = int(roi_config.get("w", 50) * w / 100) if roi_config.get("w", 50) <= 100 else int(roi_config.get("w", 50))
            rh = int(roi_config.get("h", 50) * h / 100) if roi_config.get("h", 50) <= 100 else int(roi_config.get("h", 50))
            
            # Clamp bounds
            rx = max(0, min(rx, w - 10))
            ry = max(0, min(ry, h - 10))
            rw = min(rw, w - rx)
            rh = min(rh, h - ry)
            roi_box = (rx, ry, rw, rh)

        is_intrusion = False
        breach_boxes = []

        # Analyze motion contours
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area:
                continue

            (x, y, bw, bh) = cv2.boundingRect(cnt)
            
            # Check overlap with ROI zone
            in_roi = False
            if roi_box:
                rx, ry, rw, rh = roi_box
                # Intersection check
                ix1 = max(x, rx)
                iy1 = max(y, ry)
                ix2 = min(x + bw, rx + rw)
                iy2 = min(y + bh, ry + rh)

                if ix1 < ix2 and iy1 < iy2:
                    in_roi = True

            color = (0, 0, 255) if in_roi else (255, 180, 0)
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), color, 2)
            cv2.putText(frame, f"MOTION ({int(area)}px)", (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

            if in_roi:
                is_intrusion = True
                breach_boxes.append((x, y, bw, bh))

        # Render ROI overlay zone on frame
        if roi_box:
            rx, ry, rw, rh = roi_box
            zone_color = (0, 0, 255) if is_intrusion else (0, 255, 100)
            
            # Semi-transparent fill for ROI box
            roi_overlay = frame.copy()
            cv2.rectangle(roi_overlay, (rx, ry), (rx + rw, ry + rh), zone_color, -1)
            cv2.addWeighted(roi_overlay, 0.15, frame, 0.85, 0, frame)

            # Draw dashed/corner bounding box for ROI
            cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), zone_color, 2)
            cv2.putText(frame, "🛡️ RESTRICTED ZONE", (rx + 8, ry + 22), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, zone_color, 1, cv2.LINE_AA)

        return frame, is_intrusion, breach_boxes

import cv2
import threading
import time
import os

class ThreadedCamera:
    """Threaded Camera reader that continuously captures frames in background to maintain low latency."""
    def __init__(self, source=0, width=640, height=480):
        self.source = source
        self.width = width
        self.height = height
        self.cap = None
        self.frame = None
        self.is_running = False
        self.thread = None
        self.fps = 0.0
        self._last_time = time.time()
        self._frame_count = 0
        self.using_fallback = False
        self._start_capture()

    def _start_capture(self):
        """Attempt to open camera source. If unavailable, open fallback video source or generate synthetic frame."""
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            print(f"[Camera Warning] Failed to open camera source '{self.source}'. Trying secondary index or synthetic fallback.")
            self.cap = cv2.VideoCapture(1)
            
        if not self.cap.isOpened():
            # Check if sample video exists in data folder
            sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample_video.mp4')
            if os.path.exists(sample_path):
                print(f"[Camera Info] Using sample video source: {sample_path}")
                self.cap = cv2.VideoCapture(sample_path)
                self.using_fallback = True
            else:
                self.using_fallback = True

        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.frame = cv2.resize(frame, (self.width, self.height))

        self.is_running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        """Background thread loop for capturing frames continuously."""
        while self.is_running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.frame = cv2.resize(frame, (self.width, self.height))
                    self._update_fps()
                else:
                    # If video file reached end, rewind
                    if self.using_fallback or isinstance(self.source, str):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    time.sleep(0.03)
            else:
                # Generate synthetic test pattern frame if camera fails completely
                self.frame = self._generate_synthetic_frame()
                self._update_fps()
                time.sleep(0.033)

    def _update_fps(self):
        self._frame_count += 1
        now = time.time()
        elapsed = now - self._last_time
        if elapsed >= 1.0:
            self.fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_time = now

    def _generate_synthetic_frame(self):
        """Generate synthetic frame with moving test target when no hardware camera is present."""
        import numpy as np
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Grid lines
        for x in range(0, self.width, 40):
            cv2.line(img, (x, 0), (x, self.height), (25, 35, 45), 1)
        for y in range(0, self.height, 40):
            cv2.line(img, (0, y), (self.width, y), (25, 35, 45), 1)

        t = time.time()
        # Moving synthetic target
        cx = int(self.width / 2 + np.sin(t * 2) * (self.width / 3))
        cy = int(self.height / 2 + np.cos(t * 2) * (self.height / 4))
        
        cv2.circle(img, (cx, cy), 35, (0, 200, 255), 2)
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
        
        # Simulated Face Shape for testing face/drowsiness when camera absent
        face_cx, face_cy = int(self.width / 2), int(self.height / 2)
        cv2.ellipse(img, (face_cx, face_cy), (70, 90), 0, 0, 360, (180, 180, 180), 2)
        cv2.circle(img, (face_cx - 25, face_cy - 20), 10, (255, 255, 255), -1)
        cv2.circle(img, (face_cx + 25, face_cy - 20), 10, (255, 255, 255), -1)
        cv2.circle(img, (face_cx - 25, face_cy - 20), 4, (0, 0, 0), -1)
        cv2.circle(img, (face_cx + 25, face_cy - 20), 4, (0, 0, 0), -1)
        
        # Smile
        cv2.ellipse(img, (face_cx, face_cy + 25), (30, 15), 0, 0, 180, (255, 255, 255), 2)

        cv2.putText(img, "SYNTHETIC DEMO STREAM (NO CAM ATTACHED)", (30, self.height - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 255, 100), 1)

        return img

    def get_frame(self):
        """Retrieve current processed frame."""
        if self.frame is None:
            return self._generate_synthetic_frame()
        return self.frame.copy()

    def get_fps(self):
        return self.fps

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

import cv2
import numpy as np

class DrowsinessGuard:
    """Eye Aspect Ratio (EAR) & Fatigue Monitor for Workplace Safety and Driver Eye Guard."""
    def __init__(self, ear_threshold=0.22, consec_frames=20):
        self.ear_threshold = ear_threshold
        self.consec_frames = consec_frames
        self.closed_frame_counter = 0
        self.total_blinks = 0
        self.is_eyes_closed = False

        # Attempt to load MediaPipe face mesh
        self.mp_face_mesh = None
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            print("[DrowsinessGuard] MediaPipe Face Mesh initialized.")
        except Exception as e:
            print(f"[DrowsinessGuard] MediaPipe not available ({e}), falling back to OpenCV Haar Eye cascade.")

        # OpenCV Haar Eye Cascade fallback
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    def _euclidean_dist(self, pt1, pt2):
        return np.linalg.norm(np.array(pt1) - np.array(pt2))

    def _calculate_ear_landmarks(self, eye_pts):
        # Vertical eye landmarks
        A = self._euclidean_dist(eye_pts[1], eye_pts[5])
        B = self._euclidean_dist(eye_pts[2], eye_pts[4])
        # Horizontal eye landmark
        C = self._euclidean_dist(eye_pts[0], eye_pts[3])
        if C == 0:
            return 0.3
        ear = (A + B) / (2.0 * C)
        return ear

    def process_frame(self, frame):
        """
        Compute Eye Aspect Ratio and assess drowsiness alert state.
        Returns: annotated_frame, is_drowsy_alert, stats_dict
        """
        h, w, _ = frame.shape
        ear = 0.3 # default open
        drowsy_alert = False

        if self.mp_face_mesh:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mp_face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                mesh_points = results.multi_face_landmarks[0].landmark
                
                # MediaPipe landmark indices for eyes
                # Left eye: [362, 385, 387, 263, 373, 380]
                # Right eye: [33, 160, 158, 133, 153, 144]
                left_indices = [362, 385, 387, 263, 373, 380]
                right_indices = [33, 160, 158, 133, 153, 144]

                left_eye = [(int(mesh_points[i].x * w), int(mesh_points[i].y * h)) for i in left_indices]
                right_eye = [(int(mesh_points[i].x * w), int(mesh_points[i].y * h)) for i in right_indices]

                left_ear = self._calculate_ear_landmarks(left_eye)
                right_ear = self._calculate_ear_landmarks(right_eye)
                ear = (left_ear + right_ear) / 2.0

                # Draw eye contours
                cv2.polylines(frame, [np.array(left_eye)], True, (0, 255, 255), 1)
                cv2.polylines(frame, [np.array(right_eye)], True, (0, 255, 255), 1)
        else:
            # Fallback OpenCV Haar Cascade
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30))
            if len(eyes) == 0:
                ear = 0.15 # Closed
            else:
                ear = 0.35 # Open
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(frame, (ex, ey), (ex+ew, ey+eh), (0, 255, 255), 1)

        # Evaluate Drowsiness Counter
        if ear < self.ear_threshold:
            self.closed_frame_counter += 1
            if not self.is_eyes_closed:
                self.is_eyes_closed = True

            if self.closed_frame_counter >= self.consec_frames:
                drowsy_alert = True
        else:
            if self.is_eyes_closed and self.closed_frame_counter > 2:
                self.total_blinks += 1
            self.closed_frame_counter = 0
            self.is_eyes_closed = False

        # Visual HUD Card for Drowsiness Status
        card_color = (0, 0, 255) if drowsy_alert else (0, 255, 128) if ear >= self.ear_threshold else (0, 165, 255)
        
        cv2.putText(frame, f"EAR: {ear:.2f}", (15, 70), cv2.FONT_HERSHEY_DUPLEX, 0.65, card_color, 2)
        cv2.putText(frame, f"BLINKS: {self.total_blinks}", (15, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"CLOSED FRAMES: {self.closed_frame_counter}", (15, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        if drowsy_alert:
            cv2.putText(frame, "😴 DROWSINESS ALARM - WAKE UP!", (15, 145), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255), 2)

        return frame, drowsy_alert, {"ear": ear, "blinks": self.total_blinks, "closed_frames": self.closed_frame_counter}

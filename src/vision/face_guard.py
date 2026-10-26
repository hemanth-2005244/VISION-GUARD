import cv2
import os
import numpy as np

class FaceGuard:
    """Access Guard: AI Face Detection, Registration & LBPH Recognition Engine."""
    def __init__(self, faces_dir, confidence_threshold=65.0):
        self.faces_dir = faces_dir
        self.confidence_threshold = confidence_threshold
        
        # Load Haar Cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # LBPH Recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.label_map = {} # id -> person_name
        self.is_trained = False
        
        # Load pre-saved dataset if available
        self.train_model()

    def train_model(self):
        """Train LBPH Face Recognizer from saved images in faces_dir."""
        faces = []
        labels = []
        label_id = 0
        self.label_map = {}

        if not os.path.exists(self.faces_dir):
            os.makedirs(self.faces_dir, exist_ok=True)

        person_folders = [f for f in os.listdir(self.faces_dir) if os.path.isdir(os.path.join(self.faces_dir, f))]
        
        for person_name in person_folders:
            person_path = os.path.join(self.faces_dir, person_name)
            self.label_map[label_id] = person_name
            
            for img_name in os.listdir(person_path):
                img_path = os.path.join(person_path, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    img_resized = cv2.resize(img, (150, 150))
                    faces.append(img_resized)
                    labels.append(label_id)
            
            label_id += 1

        if len(faces) > 0:
            self.recognizer.train(faces, np.array(labels))
            self.is_trained = True
            print(f"[FaceGuard] Trained on {len(faces)} samples across {len(self.label_map)} persons.")
        else:
            self.is_trained = False

    def save_face_sample(self, frame, face_box, person_name, sample_idx):
        """Crop and save face sample for enrollment dataset."""
        (x, y, w, h) = face_box
        person_dir = os.path.join(self.faces_dir, person_name)
        os.makedirs(person_dir, exist_ok=True)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size > 0:
            face_resized = cv2.resize(face_roi, (150, 150))
            filename = os.path.join(person_dir, f"sample_{sample_idx}_{int(os.path.basename(person_dir).__hash__())}.jpg")
            cv2.imwrite(filename, face_resized)

    def process_frame(self, frame):
        """
        Detect and recognize faces in the given video frame.
        Returns: annotated_frame, unknown_detected, detected_persons_list
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )

        unknown_detected = False
        detected_persons = []

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (150, 150))

            name = "UNKNOWN"
            confidence = 0.0

            if self.is_trained:
                label_id, dist = self.recognizer.predict(face_resized)
                # LBPH distance: lower is better match (typically < 70 is match)
                if dist < self.confidence_threshold and label_id in self.label_map:
                    name = self.label_map[label_id]
                    confidence = max(0.0, min(100.0, 100 - dist))

            if name == "UNKNOWN":
                unknown_detected = True
                color = (0, 0, 255) # Red for unknown
                label_str = "⚠️ UNKNOWN INTRUDER"
            else:
                color = (0, 255, 100) # Green for authorized
                label_str = f"✅ {name.upper()} ({confidence:.0f}%)"

            detected_persons.append({"name": name, "confidence": confidence, "box": (x, y, w, h)})

            # Draw bounding box & glowing target corners
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Corner accents
            length = 15
            cv2.line(frame, (x, y), (x + length, y), color, 3)
            cv2.line(frame, (x, y), (x, y + length), color, 3)
            cv2.line(frame, (x + w, y), (x + w - length, y), color, 3)
            cv2.line(frame, (x + w, y), (x + w, y + length), color, 3)

            # Label box
            cv2.rectangle(frame, (x, y - 25), (x + w, y), color, -1)
            cv2.putText(frame, label_str, (x + 5, y - 7), cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        return frame, unknown_detected, detected_persons

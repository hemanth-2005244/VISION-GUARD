import cv2
import numpy as np
import os
import math

def generate_sample_security_video(output_path, duration_sec=15, fps=30, width=640, height=480):
    """Generate a realistic security camera feed with animated moving objects, intruder box, and face simulation."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps

    for i in range(total_frames):
        # Create dark CCTV background grid
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (20, 25, 30)

        # Draw CCTV timestamp & static elements
        t_sec = i / fps
        cv2.putText(frame, f"CAM-01 [FRONT ENTRANCE] - RECV LIVE", (20, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Draw hallway floor/walls geometry
        cv2.line(frame, (0, 380), (640, 380), (60, 70, 80), 2) # floor line
        cv2.line(frame, (120, 0), (120, 380), (40, 50, 60), 1) # left door frame
        cv2.line(frame, (220, 0), (220, 380), (40, 50, 60), 1)

        # Animated Intruder / Person Silhouette moving across frame
        # Moves back and forth horizontally
        person_x = int(100 + (300 + 200 * math.sin(t_sec * 0.8)))
        person_y = 200 + int(20 * math.sin(t_sec * 3))

        # Person head
        cv2.circle(frame, (person_x, person_y - 40), 20, (180, 190, 200), -1)
        # Eyes
        cv2.circle(frame, (person_x - 7, person_y - 45), 3, (0, 0, 0), -1)
        cv2.circle(frame, (person_x + 7, person_y - 45), 3, (0, 0, 0), -1)
        # Person Body
        cv2.rectangle(frame, (person_x - 25, person_y - 20), (person_x + 25, person_y + 80), (80, 90, 110), -1)

        # Occasional moving box / object
        box_x = int(500 - (t_sec * 40) % 400)
        box_y = 330
        cv2.rectangle(frame, (box_x, box_y), (box_x + 40, box_y + 40), (0, 140, 220), -1)

        # Noise film grain for CCTV realism
        noise = np.random.randint(-10, 10, (height, width, 3), dtype=np.int16)
        frame_noisy = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        out.write(frame_noisy)

    out.release()
    print(f"[Sample Generator] Created sample security video at: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sample_video.mp4')
    generate_sample_security_video(out_file)

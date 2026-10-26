import cv2
import numpy as np
from collections import OrderedDict
from scipy.spatial import distance as dist

class CentroidTracker:
    """Centroid Object Tracker for object counting, path tracking, and movement analytics."""
    def __init__(self, max_disappeared=40):
        self.next_object_id = 0
        self.objects = OrderedDict() # id -> centroid (x, y)
        self.disappeared = OrderedDict() # id -> frames disappeared
        self.path_history = OrderedDict() # id -> list of (x, y)
        self.max_disappeared = max_disappeared

    def register(self, centroid):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.path_history[self.next_object_id] = [centroid]
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.path_history:
            del self.path_history[object_id]

    def update(self, rects):
        """
        Update tracker with bounding boxes [(x1, y1, x2, y2), ...]
        Returns: objects dict {id: centroid}
        """
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for i, (startX, startY, endX, endY) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            input_centroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i])
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            D = dist.cdist(np.array(object_centroids), input_centroids)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0

                # Append path history
                if object_id in self.path_history:
                    self.path_history[object_id].append(tuple(input_centroids[col]))
                    if len(self.path_history[object_id]) > 30:
                        self.path_history[object_id].pop(0)

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            for col in unused_cols:
                self.register(input_centroids[col])

        return self.objects

    def render_analytics(self, frame, rects):
        """Draw tracked objects, movement trails, and centroid IDs on frame."""
        objects = self.update(rects)

        for (object_id, centroid) in objects.items():
            # Draw centroid point
            cv2.circle(frame, (centroid[0], centroid[1]), 6, (0, 255, 255), -1)
            cv2.putText(frame, f"ID #{object_id}", (centroid[0] - 15, centroid[1] - 12),
                        cv2.FONT_HERSHEY_DUPLEX, 0.45, (0, 255, 255), 1)

            # Draw trajectory path line
            if object_id in self.path_history:
                pts = self.path_history[object_id]
                for i in range(1, len(pts)):
                    if pts[i - 1] is None or pts[i] is None:
                        continue
                    thickness = int(np.sqrt(30 / float(i + 1)) * 1.5)
                    cv2.line(frame, pts[i - 1], pts[i], (255, 100, 0), max(1, thickness))

        # Active object count HUD
        cv2.putText(frame, f"TRACKED OBJECTS: {len(objects)}", (15, 70),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 240, 255), 1)
        cv2.putText(frame, f"CUMULATIVE DETECTIONS: {self.next_object_id}", (15, 92),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        return frame, len(objects)

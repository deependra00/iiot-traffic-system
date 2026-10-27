import cv2
import numpy as np
from ultralytics import YOLO
import math

class TrafficAnalyzer:
    def __init__(self, model_path='yolov8n.pt', roi_polygon=None):
        self.model = YOLO(model_path)
        self.target_classes = [2, 3, 5, 7] # Car, Motorcycle, Bus, Truck
        self.class_names = {2: 'Car', 3: 'Bike', 5: 'Bus', 7: 'Truck'}
        self.roi_polygon = np.array(roi_polygon, np.int32) if roi_polygon is not None else None
        self.track_history = {}

    def is_inside_roi(self, point):
        if self.roi_polygon is None:
            return True
        result = cv2.pointPolygonTest(self.roi_polygon, point, False)
        return result >= 0

    def process_frame(self, frame):
        results = self.model.track(frame, persist=True, verbose=False)[0]
        
        vehicle_counts = {'Car': 0, 'Bike': 0, 'Bus': 0, 'Truck': 0}
        total_roi_vehicles = 0
        accident_risk_score = 0.0

        if self.roi_polygon is not None:
            cv2.polylines(frame, [self.roi_polygon], isClosed=True, color=(255, 255, 0), thickness=2)

        if results.boxes is not None and results.boxes.id is not None:
            boxes = results.boxes.xyxy.cpu().numpy()
            track_ids = results.boxes.id.int().cpu().numpy()
            class_ids = results.boxes.cls.int().cpu().numpy()

            for box, track_id, class_id in zip(boxes, track_ids, class_ids):
                if class_id in self.target_classes:
                    x1, y1, x2, y2 = map(int, box)
                    cx, cy = int((x1 + x2) / 2), int(y2)
                    
                    if self.is_inside_roi((cx, cy)):
                        v_type = self.class_names.get(class_id, 'Vehicle')
                        vehicle_counts[v_type] += 1
                        total_roi_vehicles += 1
                        
                        if track_id not in self.track_history:
                            self.track_history[track_id] = []
                        
                        self.track_history[track_id].append((cx, cy))
                        if len(self.track_history[track_id]) > 10:
                            self.track_history[track_id].pop(0)

                        history = self.track_history[track_id]
                        if len(history) >= 2:
                            dx = history[-1][0] - history[-2][0]
                            dy = history[-1][1] - history[-2][1]
                            displacement = math.sqrt(dx**2 + dy**2)
                            
                            if displacement < 2.0 and total_roi_vehicles > 2:
                                accident_risk_score += 0.15

                        color = (0, 255, 0)
                        label = f"ID:{track_id} {v_type}"
                    else:
                        color = (128, 128, 128)
                        label = f"ID:{track_id}"

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                    cv2.putText(frame, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        accident_risk_score = min(accident_risk_score + (0.05 * max(0, total_roi_vehicles - 5)), 1.0)

        if accident_risk_score > 0.7:
            risk_alert = "HIGH ACCIDENT RISK!"
            risk_color = (0, 0, 255)
        elif accident_risk_score > 0.4:
            risk_alert = "MODERATE RISK"
            risk_color = (0, 255, 255)
        else:
            risk_alert = "SAFE TRAFFIC FLOW"
            risk_color = (0, 255, 0)

        density_status = "HIGH CONGESTION" if total_roi_vehicles > 8 else ("MODERATE" if total_roi_vehicles > 3 else "FREE FLOW")

        cv2.rectangle(frame, (10, 10), (380, 180), (0, 0, 0), -1)
        cv2.putText(frame, f"Density: {density_status}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"ROI Vehicles: {total_roi_vehicles}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Risk Alert: {risk_alert}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, risk_color, 2)
        cv2.putText(frame, f"Risk Score: {accident_risk_score:.2f}", (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        return frame, {
            "total": total_roi_vehicles,
            "counts": vehicle_counts,
            "density": density_status,
            "risk_score": float(accident_risk_score),
            "alert": risk_alert
        }
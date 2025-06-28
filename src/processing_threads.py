# File: processing_threads.py
from PySide6.QtCore import QThread, Signal
import time
import numpy as np
import cv2

class SegmentationThread(QThread):
    segmentation_result = Signal(np.ndarray)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = False
        self.paused = False
        self.frame = None

    def set_frame(self, frame):
        self.frame = frame

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def run(self):
        self.running = True
        while self.running:
            if self.frame is not None and not self.paused:
                results = self.model.predict(source=self.frame, task='segment', imgsz=640, conf=0.4, verbose=False)
                masks = results[0].masks.data.cpu().numpy() if results[0].masks else []
                
                if len(masks) > 0:
                    mask = (masks[0] * 255).astype(np.uint8)
                    mask = cv2.resize(mask, (self.frame.shape[1], self.frame.shape[0]))
                    mask_colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)

                    # Calculate centroid
                    M = cv2.moments(mask)
                    if M["m00"] > 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])

                        # Draw line from bottom center to centroid
                        height, width = self.frame.shape[:2]
                        bottom_center = (width // 2, height - 1)
                        centroid_point = (cX, cY)
                        cv2.line(mask_colored, bottom_center, centroid_point, (255, 0, 0), 2)
                        cv2.circle(mask_colored, centroid_point, 5, (255, 0, 0), -1)
                        cv2.putText(mask_colored, f"Centroid: ({cX},{cY})", (cX + 10, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    # Blend and emit
                    blended = cv2.addWeighted(self.frame, 0.7, mask_colored, 0.3, 0)
                    self.segmentation_result.emit(blended)

            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()
        

class DetectionThread(QThread):
    detection_result = Signal(np.ndarray)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = False
        self.paused = False
        self.frame = None

    def set_frame(self, frame):
        self.frame = frame

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def run(self):
        self.running = True
        while self.running:
            if self.frame is not None and not self.paused:
                results = self.model.predict(source=self.frame, task='detect', imgsz=640, conf=0.4, verbose=False)
                boxes = results[0].boxes.data.cpu().numpy() if results[0].boxes else []
                display_frame = self.frame.copy()
                height, width = display_frame.shape[:2]
                bottom_center = (width // 2, height - 1)

                if len(boxes) > 0:
                    # Draw the first bounding box and line to its center
                    x1, y1, x2, y2 = boxes[0][:4].astype(int)
                    box_center = ((x1 + x2) // 2, (y1 + y2) // 2)

                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.line(display_frame, bottom_center, box_center, (255, 0, 0), 2)     # Blue line
                    cv2.circle(display_frame, box_center, 5, (255, 0, 0), -1)              # Blue dot
                    cv2.putText(display_frame, f"Pad Center: {box_center}", (box_center[0] + 10, box_center[1]), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

                self.detection_result.emit(display_frame)

            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()

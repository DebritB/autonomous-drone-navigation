# File: camera_thread.py
from PySide6.QtCore import QThread, Signal
import cv2
import time
import numpy as np

class CameraThread(QThread):
    frame_captured = Signal(np.ndarray)

    def __init__(self, drone):
        super().__init__()
        self.drone = drone
        self.running = True

    def run(self):
        frame_read = self.drone.get_frame_read()
        while self.running:
            frame = frame_read.frame
            if frame is not None:
                frame = cv2.resize(frame, (960, 720))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame_captured.emit(frame_rgb)
            time.sleep(1 / 30)

    def stop(self):
        self.running = False
        self.wait()

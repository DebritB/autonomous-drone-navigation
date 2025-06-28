"""
Autonomous Drone Navigation System

A Python package for autonomous drone navigation using computer vision and machine learning.
"""

__version__ = "1.0.0"
__author__ = "Autonomous Drone Navigation Team"
__email__ = "contact@example.com"

from .drone_worker import DroneWorker, DroneWorkerSignals
from .main_window_final import DroneGUI
from .processing_threads import SegmentationThread, DetectionThread
from .camera_thread import CameraThread

__all__ = [
    "DroneWorker",
    "DroneWorkerSignals", 
    "DroneGUI",
    "SegmentationThread",
    "DetectionThread",
    "CameraThread"
] 
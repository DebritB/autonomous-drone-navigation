# File: main_window.py
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QStatusBar, QFrame, QSpacerItem, QSizePolicy
from PySide6.QtGui import QImage, QPixmap, QFont, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QThread
import sys, cv2

from yolov5.recent_work_3.drone_worker import DroneWorker
from camera_thread import CameraThread
from processing_threads import SegmentationThread, DetectionThread

class VideoDisplay(QLabel):
    def __init__(self, title):
        super().__init__()
        self.setFixedSize(400, 300)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black; border: 2px solid #333; border-radius: 10px;")

        self.wrapper_widget = QFrame()
        self.wrapper_widget.setStyleSheet("background-color: #1e1e1e; border-radius: 12px; padding: 4px;")

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: white; font-weight: bold; padding: 6px;")
        self.title_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self.wrapper_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(self.title_label)
        layout.addWidget(self)

    def get_widget(self):
        return self.wrapper_widget

    def update_frame(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

class DroneGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autonomous Drone Navigation")
        self.setGeometry(100, 100, 1200, 750)

        layout = QVBoxLayout()

        # Top Status Layout
        status_header_layout = QHBoxLayout()

        self.status_badge = QLabel("🛸  DRONE GUI")
        self.status_badge.setFixedHeight(30)
        self.status_badge.setStyleSheet("""
            background-color: #2c2c2c;
            color: white;
            padding: 4px 12px;
            font-weight: bold;
            border-radius: 8px;
        """)
        status_header_layout.addWidget(self.status_badge)

        status_header_layout.addStretch()

        self.battery_label = QLabel("Battery: --%")
        self.battery_label.setFixedHeight(30)
        self.battery_label.setStyleSheet("""
            background-color: #2e7d32;
            color: white;
            padding: 4px 12px;
            font-weight: bold;
            border-radius: 8px;
        """)
        status_header_layout.addWidget(self.battery_label)

        layout.addLayout(status_header_layout)
        layout.addSpacerItem(QSpacerItem(0, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Video Feeds
        self.realtime_view = VideoDisplay("Real-time Drone Camera")
        self.segmentation_view = VideoDisplay("Segmentation Output")
        self.detection_view = VideoDisplay("Detection Output")

        video_layout = QHBoxLayout()
        video_layout.addWidget(self.realtime_view.get_widget())
        video_layout.addWidget(self.segmentation_view.get_widget())
        video_layout.addWidget(self.detection_view.get_widget())
        layout.addLayout(video_layout)

        layout.addSpacerItem(QSpacerItem(0, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Flight Controls
        control_layout = QVBoxLayout()
        control_label = QLabel("Flight Controls:")
        control_label.setStyleSheet("color: white; font-weight: bold; padding-top: 10px;")

        buttons_layout = QHBoxLayout()
        self.takeoff_btn = QPushButton("Takeoff")
        self.takeoff_btn.setFixedSize(200, 40)
        self.takeoff_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 100);
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 220);
            }
        """)


        self.land_btn = QPushButton("Land")
        self.land_btn.setFixedSize(200, 40)
        self.land_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 100);
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 220);
            }
        """)


        buttons_layout.addWidget(self.takeoff_btn)
        buttons_layout.addWidget(self.land_btn)
        control_layout.addWidget(control_label)
        control_layout.addLayout(buttons_layout)
        layout.addLayout(control_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.worker = DroneWorker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.signals.status_message.connect(lambda msg: self.statusBar().showMessage(msg))
        self.worker.signals.mission_started.connect(self.on_mission_started)
        self.worker.signals.mission_finished.connect(self.on_mission_finished)
        self.worker.signals.telemetry_updated.connect(self.update_telemetry)

        self.takeoff_btn.clicked.connect(self.worker.start_drone_mission)
        self.land_btn.clicked.connect(self.worker.land_drone)

        QShortcut(QKeySequence("Esc"), self, self.worker.emergency_land)

        self.camera_thread = None
        self.segmentation_thread = None
        self.detection_thread = None

        self.worker_thread.start()

        # Shared flag to control the active mode (segmentation or detection)
        self.active_mode = "none"  # "segmentation" or "detection"
        # self._start_processing_threads()

    def _start_processing_threads(self):
        drone = self.worker.get_drone()
        path_model = self.worker.get_path_model()
        pad_model = self.worker.get_pad_model()

        # Stop existing threads if they are running
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        if self.segmentation_thread:
            self.segmentation_thread.stop()
            self.segmentation_thread = None
        if self.detection_thread:
            self.detection_thread.stop()
            self.detection_thread = None

        # (Re)start threads
        self.camera_thread = CameraThread(drone)
        self.camera_thread.frame_captured.connect(self.on_new_frame)
        self.camera_thread.start()

        self.segmentation_thread = SegmentationThread(path_model)
        self.segmentation_thread.segmentation_result.connect(self.segmentation_view.update_frame)
        self.segmentation_thread.start()

        self.detection_thread = DetectionThread(pad_model)
        self.detection_thread.detection_result.connect(self.detection_view.update_frame)
        self.detection_thread.start()

    def update_telemetry(self, data):
        battery = data.get("battery", "--")
        status = data.get("status", "--")

        if isinstance(battery, int):
            if battery >= 40:
                color = "#2e7d32"
            elif battery >= 20:
                color = "#f9a825"
            else:
                color = "#c62828"
        else:
            color = "#616161"

        self.battery_label.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 4px 12px;
            font-weight: bold;
            border-radius: 8px;
        """)
        self.battery_label.setText(f"Battery: {battery}%")

    def on_mission_started(self):
        self._start_processing_threads()
        self.statusBar().showMessage("Mission started. Threads running.")

    def on_new_frame(self, frame):
        self.realtime_view.update_frame(frame)

        if self.worker.is_segmentation_active():
            self.segmentation_thread.resume()
            self.segmentation_thread.set_frame(frame)
            self.statusBar().showMessage("Segmentation mode active. Processing frame...")
        else:
            self.segmentation_thread.pause()
            self.segmentation_view.clear()

        if self.worker.is_pad_mode_active():
            self.detection_thread.resume()
            self.detection_thread.set_frame(frame)
            self.statusBar().showMessage("Pad detection mode active. Detecting landing pad...")
        else:
            self.detection_thread.pause()
            self.detection_view.clear()

    def on_mission_finished(self):
        self.statusBar().showMessage("Mission finished. Stopping threads...")
        # Stop camera thread gracefully
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None

        # Stop segmentation thread gracefully
        if self.segmentation_thread:
            self.segmentation_thread.stop()
            self.segmentation_thread = None

        # Stop detection thread gracefully
        if self.detection_thread:
            self.detection_thread.stop()
            self.detection_thread = None

        # Clear video displays
        self.realtime_view.clear()
        self.segmentation_view.clear()
        self.detection_view.clear()

        # Reset battery label and status bar
        self.battery_label.setStyleSheet(""" 
            background-color: #616161; 
            color: white; 
            padding: 4px 12px; 
            font-weight: bold; 
            border-radius: 8px; 
        """)
        self.battery_label.setText("Battery: --%")
        self.statusBar().showMessage("Ready for a new mission.")

        # Restart processing threads for new mission
        self._start_processing_threads()
        
        # Close the application
        QApplication.instance().quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    gui = DroneGUI()
    gui.show()
    app.setStyleSheet("""
        QMainWindow {
            background-color: #121212;
        }
        QLabel {
            color: white;
        }
        QPushButton {
            font-size: 12pt;
        }
    """)
    sys.exit(app.exec())

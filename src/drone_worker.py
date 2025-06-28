# File: drone_worker.py
from PySide6.QtCore import QObject, Signal, Slot, QThread, QTimer
from djitellopy import Tello
from ultralytics import YOLO
import os
import numpy as np
import time
import cv2

class DroneWorkerSignals(QObject):
    frame_ready = Signal(np.ndarray, str)
    telemetry_updated = Signal(dict)
    status_message = Signal(str)
    mission_finished = Signal()
    connection_status = Signal(bool)
    mission_started = Signal()

class DroneWorker(QObject):
    def __init__(self, path_model_path="epoch50.pt", pad_model_path="best_pad_new.pt", parent=None):
        super().__init__(parent)
        self.signals = DroneWorkerSignals()
        self.path_model_path = path_model_path
        self.pad_model_path = pad_model_path
        self.target_pad_id = 5

        self.path_model = None
        self.pad_model = None
        self.drone = None

        self._start_segmentation = False
        self._pad_mode = False
        self._is_running = True
        self._no_path_counter = 0
        self._pad_height_adjusted = False

        self.control_loop_timer = QTimer(self)
        self.control_loop_timer.setSingleShot(False)
        self.control_loop_timer.timeout.connect(self._mission_logic)

    def run(self):
        self.signals.status_message.emit("Starting DroneWorker...")
        try:
            self.path_model = YOLO(self.path_model_path)
            self.pad_model = YOLO(self.pad_model_path)
            self.drone = Tello()
            self.drone.connect()
            self.drone.set_speed(10)
            self.drone.streamon()
            self.signals.status_message.emit(f"Connected. Battery: {self.drone.get_battery()}%")
            self.signals.connection_status.emit(True)
        except Exception as e:
            self.signals.status_message.emit(f"Error: {e}")
            self.signals.connection_status.emit(False)
            self.signals.mission_finished.emit()
            return

        self.control_loop_timer.moveToThread(QThread.currentThread())
        self.signals.mission_started.emit()

    @Slot()
    def start_drone_mission(self):
        if self.drone:
            try:
                self.drone.takeoff()
                time.sleep(3)
                self.drone.move_down(30)
                time.sleep(3)
                self._start_segmentation = True
                self._pad_mode = False
                self._is_running = True
                self._no_path_counter = 0
                self._pad_height_adjusted = False
                self.signals.status_message.emit("Takeoff successful. Starting segmentation mode.")
                self.control_loop_timer.start(700)
            except Exception as e:
                self.signals.status_message.emit(f"Takeoff failed: {e}")
                self.signals.mission_finished.emit()

    def _mission_logic(self):
        if not self._is_running:
            return

        frame = self.drone.get_frame_read().frame
        if frame is None:
            return

        frame = cv2.resize(frame, (960, 720))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        telemetry = {
            "altitude": self.drone.get_height(),
            "battery": self.drone.get_battery(),
        }
        self.signals.telemetry_updated.emit(telemetry)

        # First check for pad detection
        if not self._pad_mode:
            results = self.pad_model.predict(source=rgb_frame, task='detect', imgsz=640, conf=0.4, verbose=False)
            boxes = results[0].boxes.data.cpu().numpy() if results[0].boxes else []
            
            if len(boxes) > 0:
                self.signals.status_message.emit("🎯 Pad detected → switching to pad mode")
                self._start_segmentation = False
                self._pad_mode = True
                self._pad_height_adjusted = False
            else:
                # If no pad detected, try segmentation
                if not self._start_segmentation:
                    self._start_segmentation = True
                    self._no_path_counter = 0

        # Pad mode handling
        if self._pad_mode:
            # === Pad Detection and Alignment ===
            if not self._pad_height_adjusted:
                try:
                    # First move up to ensure we have room to adjust
                    self.drone.move_up(40)
                    time.sleep(1)
                    
                    current_height = self.drone.get_height()
                    target_height = 25
                    adjustment = current_height - target_height

                    if adjustment > 0:
                        print(f"⏬ Lowering drone by ~{adjustment} cm to reach ~25 cm...")
                        self.drone.move_down(adjustment)
                        time.sleep(2)
                    else:
                        print("✅ Already near or below target height.")
                    self._pad_height_adjusted = True
                except Exception as e:
                    print(f"Error adjusting height for pad: {e}")
                    self.signals.status_message.emit(f"Error adjusting height: {e}")

            results = self.pad_model.predict(source=rgb_frame, task='detect', imgsz=640, conf=0.4, verbose=False)
            boxes = results[0].boxes.data.cpu().numpy() if results[0].boxes else []

            # Emit the frame with detection overlay
            self.signals.frame_ready.emit(frame, "detection")

            if len(boxes) > 0:
                x1, y1, x2, y2 = boxes[0][:4]
                pad_center_x = int((x1 + x2) / 2)
                frame_center_x = frame.shape[1] // 2
                offset = pad_center_x - frame_center_x

                if abs(offset) > 80:
                    if offset < 0:
                        print("↺ Slight ROTATE LEFT (1°) to align with pad...")
                        try:
                            self.drone.rotate_counter_clockwise(5)
                        except Exception as e:
                            print(f"Error during rotation: {e}")
                            self.signals.status_message.emit(f"Error during rotation: {e}")
                    else:
                        print("↻ Slight ROTATE RIGHT (1°) to align with pad...")
                        try:
                            self.drone.rotate_clockwise(5)
                        except Exception as e:
                            print(f"Error during rotation: {e}")
                            self.signals.status_message.emit(f"Error during rotation: {e}")
                else:
                    print("✅ Aligned. Moving forward toward pad...")
                    try:
                        self.drone.move_forward(20)
                        time.sleep(2)
                    except Exception as e:
                        print(f"Error during forward movement: {e}")
                        self.signals.status_message.emit(f"Error during forward movement: {e}")

            else:
                print("❌ Pad lost. Moving forward 40cm before recovery...")
                self.signals.status_message.emit("Pad lost. Moving forward before recovery.")
                try:
                    self.drone.move_forward(40)
                    time.sleep(2)
                    print("Triggering recovery maneuver after forward movement.")
                    self.trigger_pad_detection_recovery()
                except Exception as e:
                    print(f"Error during forward movement: {e}")
                    self.signals.status_message.emit(f"Error during forward movement: {e}")
                    # If forward movement fails, still try recovery
                    self.trigger_pad_detection_recovery()

        # Segmentation mode handling
        elif self._start_segmentation:
            results = self.path_model.predict(source=rgb_frame, task='segment', imgsz=640, conf=0.4, verbose=False)
            masks = results[0].masks.data.cpu().numpy() if results[0].masks else []
            if len(masks) > 0:
                self._no_path_counter = 0
                mask = (masks[0] * 255).astype(np.uint8)
                M = cv2.moments(mask)
                if M["m00"] > 0:
                    cX = int(M["m10"] / M["m00"])
                    center_x = mask.shape[1] // 2
                    if cX < center_x - 50:
                        self.signals.status_message.emit("⬅️ Path on LEFT → moving left")
                        self.drone.move_left(20)
                    elif cX > center_x + 50:
                        self.signals.status_message.emit("➡️ Path on RIGHT → moving right")
                        self.drone.move_right(20)
                    else:
                        self.signals.status_message.emit("⬆️ Path CENTERED → moving forward")
                        self.drone.move_forward(40)
                else:
                    self.signals.status_message.emit("🚫 No centroid found")
            else:
                self._no_path_counter += 1
                self.signals.status_message.emit("🔄 No path detected")
                if self._no_path_counter == 1:
                    self.drone.rotate_clockwise(90)
                elif self._no_path_counter == 2:
                    self.drone.rotate_counter_clockwise(180)
                elif self._no_path_counter > 2:
                    self.signals.status_message.emit("🛑 Path not found after recovery attempts. Switching to pad detection.")
                    # After segmentation fails, switch to pad detection mode
                    self._start_segmentation = False
                    self._pad_mode = True
                    self._pad_height_adjusted = False
                    # Trigger pad detection recovery
                    self.trigger_pad_detection_recovery()

    def trigger_pad_detection_recovery(self):
        """Trigger the pad detection recovery sequence"""
        try:
            # Move forward (e.g., 30 cm)
            # print("➡️ Moving forward for recovery...")
            # self.signals.status_message.emit("Moving forward for recovery.")
            # # self.drone.move_forward(30)
            # time.sleep(1.5)

            # Ascend to search altitude (e.g., 80 cm)
            print("⬆️ Ascending for Pad search...")
            self.signals.status_message.emit("Ascending for Pad search.")
            current_height = self.drone.get_height()
            target_search_height = 80
            if current_height < target_search_height:
                ascend_distance = target_search_height - current_height
                self.drone.move_up(ascend_distance)
                time.sleep(2)
                print(f"Reached approx height: {self.drone.get_height()} cm")
            else:
                print("Already above search height.")

            # After recovery maneuver, attempt built-in pad landing
            self.attempt_built_in_pad_landing(self.target_pad_id)

        except Exception as e:
            recovery_error_msg = f"❌ Error during recovery maneuver: {str(e)}"
            self.signals.status_message.emit(recovery_error_msg)
            print(recovery_error_msg)
            # Fallback to general landing if recovery fails
            self.land_drone()

    @Slot()
    def land_drone(self):
        if self.drone:
            try:
                self.drone.land()
                self.signals.status_message.emit("Landing successful.")
            except Exception as e:
                self.signals.status_message.emit(f"Landing failed: {e}")
        self._is_running = False
        self.control_loop_timer.stop()
        self.signals.mission_finished.emit()

    @Slot()
    def emergency_land(self):
        try:
            if self.drone:
                self.signals.status_message.emit("🚨 Emergency landing initiated")
                self.drone.send_rc_control(0, 0, 0, 0)
                time.sleep(0.1)
                try:
                    self.drone.emergency()
                except Exception:
                    self.drone.land()

            self._is_running = False
            self._start_segmentation = False
            self._pad_mode = False
            self.control_loop_timer.stop()
            self.signals.mission_finished.emit()

        except Exception as e:
            self.signals.status_message.emit(f"❌ Emergency landing error: {str(e)}")
            self._is_running = False
            self._start_segmentation = False
            self._pad_mode = False
            self.control_loop_timer.stop()
            self.signals.mission_finished.emit()

    def attempt_built_in_pad_landing(self, target_pad_id):
        """Attempts to use Tello's built-in pad landing feature."""
        print("Attempting built-in pad landing...")
        self.signals.status_message.emit("Attempting built-in pad landing...")

        try:
            if not self.drone:
                print("Drone not connected for built-in landing.")
                self.signals.status_message.emit("Built-in landing failed: Drone not connected.")
                self._is_running = False
                self.signals.mission_finished.emit()
                return

            # Ensure drone is at a suitable height for downward pad detection (e.g., ~80-120 cm)
            # Assuming the recovery maneuver (forward + ascend) brought it to roughly this height
            # If this method is called outside of the recovery maneuver, caller should ensure height
            # For now, we proceed assuming suitable height.
            current_height = self.drone.get_height()
            print(f"Starting built-in pad search from height: {current_height} cm")
            self.signals.status_message.emit(f"Starting built-in search from {current_height} cm.")

            self.drone.enable_mission_pads()
            self.drone.set_mission_pad_detection_direction(0)  # Downward camera
            print("下视视觉定位系统已启用（Mission Pad 检测：开启 | 检测方向：下视）")
            self.signals.status_message.emit("下视视觉定位系统已启用")

            pad_found = False
            search_attempts = 0
            max_search_attempts = 20 # Increased attempts
            rotation_angle = 30 # Degrees to rotate each attempt

            while not pad_found and search_attempts < max_search_attempts and self._is_running:
                pad_id = self.drone.get_mission_pad_id()
                print(f"Built-in search Attempt {search_attempts+1}: Detected ID: {pad_id}")

                if pad_id == target_pad_id:
                    print(f"🎯 Successfully identified target Pad ID: {target_pad_id}")
                    self.signals.status_message.emit(f"Target Pad ID {target_pad_id} identified.")
                    pad_found = True
                    break # Exit search loop
                elif pad_id != -1:
                     print(f"Identified non-target Pad ID: {pad_id}. Continuing search for {target_pad_id}.")
                     self.signals.status_message.emit(f"Non-target Pad ID {pad_id} detected. Searching for {target_pad_id}.")
                else:
                    print(f"🔍 No Pad detected. Rotating {rotation_angle}° clockwise and searching...")
                    self.signals.status_message.emit(f"No Pad detected. Rotating {rotation_angle}° and searching...")

                # Rotate and wait to search wider area
                try:
                    self.drone.rotate_clockwise(rotation_angle)
                    time.sleep(2) # Increased sleep to allow rotation and detection
                except Exception as rotate_e:
                    print(f"Error during built-in search rotation: {rotate_e}")
                    self.signals.status_message.emit(f"Error during built-in search rotation: {rotate_e}")
                    # If rotation fails, might as well stop the search and fallback
                    break 

                search_attempts += 1

            if pad_found:
                print("🛫 Moving to target Pad (offset height 50cm)...")
                self.signals.status_message.emit("Approaching target Pad.")
                # go_xyz_speed_mid is blocking, worker will wait here
                try:
                    # Move to 50cm above pad. Note: go_xyz_speed_mid is relative to the pad.
                    self.drone.go_xyz_speed_mid(0, 0, 50, 15, target_pad_id) 
                    print("✅ Reached position above Pad.")
                    self.signals.status_message.emit("Above Pad. Landing.")

                    print("🛬 Initiating built-in land...")
                    try:
                        self.drone.land()
                        print("✅ Built-in land command issued.")
                        self.signals.status_message.emit("Built-in landing complete.")
                    except Exception as land_e:
                         error_msg = f"❌ Built-in land command failed: {str(land_e)}"
                         self.signals.status_message.emit(error_msg)
                         print(error_msg)
                         # If land fails after reaching position, attempt simplified fallback land
                         print("Built-in land failed after positioning. Attempting simple fallback land.")
                         self.signals.status_message.emit("Built-in land failed. Fallback land.")
                         try:
                             if self.drone:
                                 self.drone.land()
                                 print("Simple fallback land command issued after built-in land failure.")
                         except Exception as ee:
                              final_error_msg = f"❌ Simple fallback land also failed after built-in land failure: {str(ee)}"
                              self.signals.status_message.emit(final_error_msg)
                              print(final_error_msg)

                except Exception as go_e:
                    error_msg = f"❌ go_xyz_speed_mid command failed: {str(go_e)}"
                    self.signals.status_message.emit(error_msg)
                    print(error_msg)
                    # If go_xyz_speed_mid fails, fallback to general land
                    print("go_xyz_speed_mid failed. Falling back to general landing.")
                    self.signals.status_message.emit("Positioning failed. Falling back.")
                    self.land_drone() # land_drone handles its own errors and stopping worker
                    return # Exit this built-in landing attempt method

                # Built-in landing or its fallback was attempted, stop the worker
                self._is_running = False
                self._start_segmentation = False
                self._pad_mode = False
                self.signals.mission_finished.emit()

            else:
                print("❌ Target Pad not identified after search attempts.")
                self.signals.status_message.emit("Target Pad not found after search. Falling back.")
                # If built-in detection failed after search attempts, perform a simple land as a fallback
                print("Attempting simple land after built-in search failure.")
                try:
                    if self.drone:
                        self.drone.land()
                        print("Simple fallback land command issued after built-in search failure.")
                except Exception as e:
                    final_error_msg = f"❌ Simple fallback land also failed after built-in search failure: {str(e)}"
                    self.signals.status_message.emit(final_error_msg)
                    print(final_error_msg)

                # Ensure worker stops regardless of final fallback success
                self._is_running = False
                self._start_segmentation = False
                self._pad_mode = False
                self.signals.mission_finished.emit()

        except Exception as e:
            # This catches unexpected errors during the built-in landing setup or initial search loop
            error_msg = f"❌ Unexpected error during built-in pad landing attempt: {str(e)}"
            self.signals.status_message.emit(error_msg)
            print(error_msg)
            
            # In case of an unexpected error during the procedure, attempt a simple land as a fallback
            print("Unexpected built-in landing error. Attempting simple land fallback.")
            self.signals.status_message.emit("Built-in attempt failed unexpectedly. Simple land fallback.")
            try:
                if self.drone:
                    self.drone.land()
                    print("Simple land fallback command issued after unexpected built-in failure.")
            except Exception as ee:
                 final_error_msg = f"❌ Simple land fallback also failed after unexpected built-in failure: {str(ee)}"
                 self.signals.status_message.emit(final_error_msg)
                 print(final_error_msg)

            # Ensure worker stops regardless of final fallback success
            self._is_running = False
            self._start_segmentation = False
            self._pad_mode = False
            self.signals.mission_finished.emit()

    def get_drone(self):
        return self.drone

    def get_path_model(self):
        return self.path_model

    def get_pad_model(self):
        return self.pad_model

    def is_segmentation_active(self):
        return self._start_segmentation

    def is_pad_mode_active(self):
        return self._pad_mode

    def switch_to_pad_mode(self):
        self._pad_mode = True
        self._start_segmentation = False

    def stop_worker(self):
        self._is_running = False
        self._start_segmentation = False
        self._pad_mode = False
        self.control_loop_timer.stop()
        self.signals.mission_finished.emit()

# Autonomous Drone Navigation System

An intelligent drone navigation system that combines computer vision and machine learning to enable autonomous flight with path following and landing pad detection capabilities.

![image](https://github.com/user-attachments/assets/faecf573-61a9-4141-bf9e-1469a87c731d)

![image](https://github.com/user-attachments/assets/270c8c8c-f989-483c-8784-2725de81657f)

![image](https://github.com/user-attachments/assets/f6f14706-5783-484a-aa21-bf3e5f2011df)


## Features

- **Real-time Path Segmentation**: Uses YOLO models to detect and follow paths in real-time
- **Landing Pad Detection**: Automatically detects and aligns with landing pads
- **Multi-threaded Processing**: Separate threads for camera feed, segmentation, and detection
- **Modern GUI**: Built with PySide6 for a professional user interface
- **Telemetry Monitoring**: Real-time battery and altitude monitoring
- **Emergency Controls**: Quick emergency landing with ESC key

## Requirements

- Python 3.8+
- DJI Tello Drone
- Webcam (for testing without drone)

## Dependencies

```
PySide6>=6.0.0
djitellopy>=2.5.0
ultralytics>=8.0.0
opencv-python>=4.5.0
numpy>=1.21.0
```

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd autonomous_drone_navigation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download the required YOLO models:
   - Path segmentation model: `epoch50.pt`
   - Landing pad detection model: `best_pad_new.pt`
   - Link: https://drive.google.com/drive/folders/1X5bv7n2080T2b7jmrMRxmG0J0X8nmPZk?usp=sharing 

## Usage

### Running the Application

```bash
python main_window_final.py
```

### Controls

- **Takeoff Button**: Initiates autonomous mission
- **Land Button**: Manual landing
- **ESC Key**: Emergency landing
- **GUI Displays**: Real-time camera feed, segmentation output, and detection overlay

### Mission Flow

1. **Takeoff**: Drone takes off and adjusts to optimal height
2. **Path Following**: Uses segmentation to follow detected paths
3. **Pad Detection**: Automatically switches to pad detection mode when landing pad is found
4. **Alignment**: Aligns with the landing pad using visual feedback
5. **Landing**: Performs autonomous landing on the detected pad

## Architecture

### Core Components

- **`drone_worker.py`**: Main drone control logic and mission management
- **`main_window_final.py`**: GUI application and user interface
- **`processing_threads.py`**: Multi-threaded image processing for segmentation and detection
- **`camera_thread.py`**: Camera feed handling and frame capture

### Threading Model

- **Main Thread**: GUI and user interaction
- **Drone Worker Thread**: Drone control and mission logic
- **Camera Thread**: Real-time frame capture
- **Segmentation Thread**: Path detection processing
- **Detection Thread**: Landing pad detection processing

## Configuration

### Model Paths

Update the model paths in `drone_worker.py`:

```python
def __init__(self, path_model_path="epoch50.pt", pad_model_path="best_pad_new.pt", parent=None):
```

### Drone Settings

Adjust drone parameters in `drone_worker.py`:

```python
self.drone.set_speed(10)  # Speed in cm/s
target_height = 25        # Target height in cm
```

## Performance

- **Frame Rate**: 30 FPS camera feed
- **Processing**: Real-time YOLO inference
- **Latency**: <100ms control loop
- **Accuracy**: Configurable confidence thresholds

## Safety Features

- **Emergency Landing**: Immediate landing with ESC key
- **Battery Monitoring**: Real-time battery level display
- **Connection Status**: Automatic connection verification
- **Error Handling**: Graceful error recovery

## Testing

### Without Drone

The system can be tested using a webcam by modifying the camera source in `camera_thread.py`.

### With Drone

1. Ensure DJI Tello is fully charged
2. Connect to drone's WiFi network
3. Run the application
4. Use Takeoff button to start autonomous mission

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- DJI Tello SDK for drone control
- Ultralytics for YOLO model implementation
- PySide6 for the modern GUI framework

## Support

For issues and questions, please open an issue on GitHub or send an email to debritb@gmail.com.

---

**Note**: This system is designed for educational and research purposes. Always ensure safe operation in controlled environments. 

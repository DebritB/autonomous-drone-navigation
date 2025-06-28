# User Guide

## Getting Started

### Prerequisites

Before using the Autonomous Drone Navigation System, ensure you have:

1. **Hardware Requirements**:
   - DJI Tello Drone (fully charged)
   - Computer with WiFi capability
   - Webcam (for testing without drone)

2. **Software Requirements**:
   - Python 3.8 or higher
   - All required dependencies (see requirements.txt)

### Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd autonomous_drone_navigation
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Models**:
   - Place your YOLO models in the project directory:
     - `epoch50.pt` (path segmentation model)
     - `best_pad_new.pt` (landing pad detection model)

## Running the Application

### Launch the GUI

```bash
python main.py
```

Or alternatively:

```bash
python src/main_window_final.py
```

### GUI Overview

The application window contains:

1. **Status Bar**: Shows current system status and battery level
2. **Video Displays**: Three video feeds showing:
   - Real-time drone camera
   - Segmentation output
   - Detection output
3. **Control Buttons**: Takeoff and Land buttons
4. **Status Messages**: Real-time feedback from the system

## Using the System

### Basic Operation

1. **Connect to Drone**:
   - Turn on your DJI Tello drone
   - Connect your computer to the drone's WiFi network
   - The application will automatically attempt to connect

2. **Start Mission**:
   - Click the "Takeoff" button to begin autonomous flight
   - The drone will take off and begin path following

3. **Monitor Progress**:
   - Watch the video feeds for real-time feedback
   - Monitor battery level and altitude in the status bar
   - Read status messages for current mission phase

4. **Emergency Controls**:
   - Press ESC key for emergency landing
   - Click "Land" button for controlled landing

### Mission Phases

#### 1. Takeoff Phase
- Drone takes off to safe altitude
- Adjusts to optimal height for navigation
- Initializes computer vision systems

#### 2. Path Following Phase
- Uses segmentation to detect navigation paths
- Automatically follows detected paths
- Maintains safe distance from obstacles

#### 3. Pad Detection Phase
- Automatically switches when landing pad is detected
- Aligns with the landing pad using visual feedback
- Adjusts height for optimal landing approach

#### 4. Landing Phase
- Performs autonomous landing on detected pad
- Uses built-in Tello landing capabilities
- Confirms successful landing

## Advanced Features

### Configuration

You can modify drone behavior by editing parameters in `src/drone_worker.py`:

```python
# Speed settings
self.drone.set_speed(10)  # cm/s

# Height settings
target_height = 25  # cm

# Detection confidence
conf=0.4  # YOLO confidence threshold
```

### Testing Without Drone

To test the system without a physical drone:

1. Modify `src/camera_thread.py` to use webcam:
   ```python
   # Replace drone camera with webcam
   self.cap = cv2.VideoCapture(0)  # Use webcam
   ```

2. Run the application normally
3. The system will process webcam feed instead of drone camera

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Ensure drone is powered on
   - Check WiFi connection to drone
   - Verify drone battery level

2. **Model Loading Errors**:
   - Check model file paths
   - Ensure model files are in correct format
   - Verify model compatibility

3. **Poor Detection Performance**:
   - Adjust confidence thresholds
   - Ensure adequate lighting
   - Check camera focus and positioning

### Performance Optimization

1. **Frame Rate Issues**:
   - Reduce processing resolution
   - Lower confidence thresholds
   - Close unnecessary applications

2. **Memory Usage**:
   - Restart application periodically
   - Monitor system resources
   - Optimize model inference settings

## Safety Guidelines

### Pre-flight Checklist

- [ ] Drone battery fully charged
- [ ] Propellers securely attached
- [ ] Flight area clear of obstacles
- [ ] Weather conditions suitable
- [ ] Emergency landing zone identified

### During Flight

- Always monitor battery level
- Keep emergency controls accessible
- Maintain visual line of sight
- Be prepared for manual intervention

### Post-flight

- Power off drone safely
- Check for any damage
- Review flight logs if available
- Charge battery for next use

## Support

For additional help:

1. Check the troubleshooting section
2. Review the main README.md
3. Open an issue on GitHub
4. Contact the development team

---

**Remember**: This system is for educational and research purposes. Always prioritize safety and follow local drone regulations. 
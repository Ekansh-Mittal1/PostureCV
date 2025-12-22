# Posture Corrector

Real-time posture monitoring application using computer vision. Uses MediaPipe pose detection to track shoulder alignment, calibrates baseline posture, and alerts when slouching. Built with Python, PySide6, and OpenCV.

## Features

- 🎯 **Real-time posture monitoring** using MediaPipe pose detection
- 📊 **Automatic calibration** - establishes your baseline posture in 3 seconds
- 🔔 **Prominent alerts** - native macOS notifications when slouching is detected
- 📷 **Live camera preview** - embedded preview with pose detection overlay
- 📈 **Posture scoring** - percentage-based posture score with color-coded feedback
- 🖥️ **Modern GUI** - clean PySide6 interface with status indicators

## Requirements

- **Python 3.12** (required for MediaPipe compatibility)
- **macOS 10.13 or later** (for camera access and notifications)
- **Camera access** (webcam required)
- **Virtual environment** (recommended)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd posture_corrector
```

### 2. Set Up Python Environment

If you don't have Python 3.12, install it using `pyenv`:

```bash
# Install pyenv if you don't have it
brew install pyenv

# Install Python 3.12
pyenv install 3.12.8

# Set local Python version
pyenv local 3.12.8
```

### 3. Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r config/requirements.txt
```

## Usage

### Running the Application

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the application
python posture_corrector.py
```

The application window will open with the following controls:

- **Start Monitoring** - Begin posture monitoring (calibrates for 3 seconds)
- **Stop Monitoring** - Stop posture monitoring
- **Show Camera Preview** - Display live camera feed with pose detection
- **Hide Camera Preview** - Hide the camera preview

### First Run

1. When you first run the application, macOS will request **Camera Access** permission
2. Grant permission in System Settings > Privacy & Security > Camera
3. Click **"Start Monitoring"** to begin
4. Sit up straight for 3 seconds while the app calibrates your baseline posture
5. The app will monitor your posture and alert you when slouching is detected

### Monitoring

- The app continuously monitors your posture using your webcam
- A **posture score** (percentage) is displayed in the camera preview
- **Green (≥100%)** - Excellent posture
- **Orange (85-99%)** - Fair posture
- **Red (<85%)** - Poor posture / Slouching
- After 3 seconds of sustained slouching, you'll receive a prominent alert

## Project Structure

```
posture_corrector/
├── src/                    # Source code
│   ├── __init__.py
│   ├── gui_app.py         # Main PySide6 GUI application
│   ├── posture_monitor.py # Core posture detection logic
│   ├── warning_popup.py   # Warning UI component
│   └── camera_preview.py  # Camera preview functionality
├── resources/             # GUI resources
│   ├── thumbnail.png     # App icon (PNG)
│   └── thumbnail.icns    # App icon (macOS)
├── posture_corrector.py   # Main entry point
├── setup.py              # Build configuration (for packaging)
├── config/              # Configuration files
│   ├── requirements.txt # Python dependencies
│   └── .python-version  # Python version (for pyenv)
└── README.md            # This file
```

## How It Works

1. **Pose Detection**: Uses MediaPipe to detect key body landmarks (nose, shoulders)
2. **Calibration**: Measures the ratio of neck height to shoulder width during initial 3-second period
3. **Monitoring**: Continuously compares current posture ratio to baseline
4. **Alerting**: Triggers native macOS alerts when posture drops below 85% of baseline for 3+ seconds

## Troubleshooting

### Camera Permission Issues

If the camera doesn't work:
- Check **System Settings > Privacy & Security > Camera**
- Ensure the Terminal (or Python) has camera access
- Restart the application after granting permissions

### Import Errors

If you see import errors:
- Ensure you're using Python 3.12: `python --version`
- Activate the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r config/requirements.txt`

### Camera Preview Not Showing

- Click **"Show Camera Preview"** button in the GUI
- Check that no other application is using the camera
- Try restarting the application

### Monitoring Stops Unexpectedly

- Check the Activity Log in the GUI for error messages
- Ensure camera permissions are granted
- Try stopping and restarting monitoring

## Development

### Running from Source

The application is designed to run directly from source:

```bash
source venv/bin/activate
python posture_corrector.py
```

### Code Organization

- All source code is in the `src/` directory
- The main entry point is `posture_corrector.py` in the root
- GUI resources (icons, images) are in `resources/`

### Dependencies

Key dependencies:
- **PySide6** - GUI framework
- **OpenCV** - Camera capture and image processing
- **MediaPipe** - Pose detection
- **NumPy** - Numerical computations

See `config/requirements.txt` for complete list.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

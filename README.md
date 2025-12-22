# Posture Corrector

A macOS menu bar application that monitors your posture using your webcam and alerts you when you're slouching.

## Features

- 🎯 Real-time posture monitoring using MediaPipe
- 📊 Automatic calibration
- 🔔 Prominent alerts when slouching is detected
- 📱 System tray menu for easy control
- 📷 Camera preview window
- 🚀 Standalone macOS application (no Python/terminal required)

## Installation

### Option 1: Run as Standalone App (Recommended)

1. Build the application:
   ```bash
   python setup.py py2app
   ```

2. The built app will be in `dist/Posture Corrector.app`

3. Double-click to run, or drag to Applications folder

### Option 2: Run from Source

1. Make sure you have Python 3.12 installed (use pyenv if needed)
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python posture_corrector.py
   ```

## Usage

1. Look for the **"P"** icon in your menu bar (top right of screen)
2. Right-click or click the icon to open the menu
3. Select **"Start Monitoring"**
4. Sit up straight for 3 seconds to calibrate
5. The app will monitor your posture and alert you when you slouch
6. Double-click the icon to toggle monitoring on/off

## Menu Options

- **Status** - Current monitoring status
- **Start Monitoring** - Begin posture monitoring
- **Stop Monitoring** - Stop monitoring
- **Show Camera** - Open camera preview window (shows pose detection)
- **Quit** - Exit the application

## Permissions

On first run, macOS will request:
- **Camera Access** - Required for posture monitoring
- **Accessibility** - Required for system notifications

Grant these permissions in System Settings if prompted.

## Building for Distribution

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Build the app:
   ```bash
   python setup.py py2app
   ```

3. The standalone `.app` bundle will be in the `dist` folder

4. You can distribute the entire `.app` file - users can drag it to Applications

## Project Structure

- `gui_app.py` - Main PySide6 GUI application
- `posture_monitor.py` - Core posture detection logic
- `warning_popup.py` - Warning UI component
- `camera_preview.py` - Camera preview window
- `posture_corrector.py` - Entry point
- `setup.py` - py2app build configuration

## Troubleshooting

### Menu bar icon doesn't appear
- Check if menu bar is crowded (hold ⌘ and drag icons to make space)
- Ensure System Settings > Privacy & Security > Accessibility has the app enabled

### Camera doesn't work
- Check System Settings > Privacy & Security > Camera permissions
- Ensure no other app is using the camera

### App won't build
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try: `python setup.py py2app --clean`
- Check that you're using Python 3.12

## Requirements

- macOS 10.13 or later
- Python 3.12 (for building)
- Camera access
- ~500MB disk space (for the built app)
# PostureCV

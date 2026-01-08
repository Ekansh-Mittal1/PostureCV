"""
Posture Corrector GUI Application using PySide6.
Main window application with embedded camera preview.
"""
import sys
import cv2
import numpy as np
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QMessageBox
)
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from .posture_monitor import PostureMonitor
from .warning_popup import WarningPopup


def check_camera_permission():
    """Check if camera permission is granted on macOS"""
    try:
        # Try to open camera briefly to trigger permission dialog if needed
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            return ret
        else:
            return False
    except Exception:
        return False


def request_camera_permission():
    """Request camera permission and show instructions if denied"""
    # Try to open camera - this will trigger macOS permission dialog
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        # Permission granted or already had access
        cap.release()
        return True
    else:
        # Permission denied or camera unavailable
        cap.release()
        return False


class CameraThread(QThread):
    """Thread for capturing and processing camera frames"""
    frame_ready = Signal(np.ndarray)  # Signal emitted when a new frame is ready
    
    def __init__(self, baseline_ratio=None, monitor=None):
        super().__init__()
        self.baseline_ratio = baseline_ratio
        self.monitor = monitor  # Reference to PostureMonitor to get status
        self.running = False
        self.cap = None
        self.pose = None
        self.mp_pose = None
        self.mp_drawing = None
        self.SENSITIVITY = 0.85
    
    def initialize_mediapipe(self):
        """Initialize MediaPipe"""
        if self.mp_pose is None:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
    
    def run(self):
        """Main camera loop"""
        try:
            self.running = True
            self.initialize_mediapipe()
            
            # Try to open camera with retry
            self.cap = None
            for attempt in range(5):  # More retries
                try:
                    self.cap = cv2.VideoCapture(0)
                    if self.cap.isOpened():
                        # Set camera properties for better compatibility
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        
                        # Test if we can actually read a frame
                        ret, test_frame = self.cap.read()
                        if ret and test_frame is not None:
                            break
                        else:
                            if self.cap:
                                self.cap.release()
                            self.cap = None
                    else:
                        if self.cap:
                            self.cap.release()
                        self.cap = None
                except Exception as e:
                    error_detail = f"Camera open attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}"
                    print(error_detail)
                    import traceback
                    traceback.print_exc()
                    if self.cap:
                        try:
                            self.cap.release()
                        except:
                            pass
                        self.cap = None
                
                self.msleep(500)  # Wait before retry
            
            if not self.cap or not self.cap.isOpened():
                error_msg = "Failed to open camera after 5 retries.\n\n"
                error_msg += "Possible causes:\n"
                error_msg += "1. Camera permission denied\n"
                error_msg += "2. Another app is using the camera\n"
                error_msg += "3. Camera hardware issue\n"
                error_msg += "4. Camera driver issue\n\n"
                error_msg += "Please check System Settings > Privacy & Security > Camera"
                print(error_msg)
                self.frame_ready.emit(None)
                return
            
            print("Camera opened successfully, starting frame capture...")
            frame_count = 0
            
            while self.running:
                try:
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        print(f"Failed to read frame (ret={ret}, frame is None={frame is None})")
                        self.msleep(100)
                        continue
                    
                    frame_count += 1
                    
                    # Process frame with MediaPipe
                    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.pose.process(image_rgb)
                    
                    # Draw pose detection
                    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                    h, w, _ = image_bgr.shape
                    
                    if results.pose_landmarks:
                        lm = results.pose_landmarks.landmark
                        
                        nose = [lm[0].x * w, lm[0].y * h]
                        l_shldr = [lm[11].x * w, lm[11].y * h]
                        r_shldr = [lm[12].x * w, lm[12].y * h]
                        
                        shldr_mid_x = (l_shldr[0] + r_shldr[0]) / 2
                        shldr_mid_y = (l_shldr[1] + r_shldr[1]) / 2
                        
                        neck_height = abs(shldr_mid_y - nose[1])
                        shldr_width = np.linalg.norm(np.array(l_shldr) - np.array(r_shldr))
                        
                        if shldr_width > 0:
                            current_ratio = neck_height / shldr_width
                            
                            # Draw pose lines
                            cv2.line(image_bgr, (int(shldr_mid_x), int(shldr_mid_y)),
                                    (int(nose[0]), int(nose[1])), (255, 255, 0), 2)
                            cv2.line(image_bgr, (int(l_shldr[0]), int(l_shldr[1])),
                                    (int(r_shldr[0]), int(r_shldr[1])), (255, 0, 255), 2)
                            
                            # Draw pose landmarks
                            self.mp_drawing.draw_landmarks(
                                image_bgr, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS
                            )
                            
                            # Show status - use monitor's status if available, otherwise calculate own
                            status = None
                            color = (255, 255, 255)
                            
                            # Prefer monitor's status if monitoring is running
                            if self.monitor and self.monitor.running and hasattr(self.monitor, 'current_status'):
                                monitor_status = self.monitor.current_status
                                if "SLOUCHING" in monitor_status or "SLOUCH" in monitor_status:
                                    status = "SLOUCHING"
                                    color = (0, 0, 255)  # Red
                                elif "Calibrating" in monitor_status:
                                    status = "CALIBRATING..."
                                    color = (0, 165, 255)  # Orange
                                elif "Good" in monitor_status:
                                    status = "GOOD POSTURE"
                                    color = (0, 255, 0)  # Green
                                elif "Error" in monitor_status:
                                    status = "ERROR"
                                    color = (0, 0, 255)  # Red
                            
                            # Fall back to own calculation if no monitor status
                            if status is None and self.baseline_ratio:
                                if current_ratio < (self.baseline_ratio * self.SENSITIVITY):
                                    status = "SLOUCHING"
                                    color = (0, 0, 255)  # Red
                                else:
                                    status = "GOOD POSTURE"
                                    color = (0, 255, 0)  # Green
                            
                            # Draw status if we have one
                            if status:
                                font = cv2.FONT_HERSHEY_DUPLEX
                                cv2.putText(image_bgr, status, (50, 50),
                                           font, 0.7, color, 2)
                                
                                # Show posture ratio as percentage score
                                if self.baseline_ratio and self.baseline_ratio > 0:
                                    # Calculate percentage: (current / baseline) * 100
                                    # 100% = baseline, >100% = better, <100% = worse
                                    percentage = (current_ratio / self.baseline_ratio) * 100
                                    percentage_text = f"Posture Score: {percentage:.0f}%"
                                    
                                    # Color code the percentage
                                    if percentage >= 100:
                                        score_color = (0, 255, 0)  # Green for good/excellent
                                    elif percentage >= 85:
                                        score_color = (0, 165, 255)  # Orange for fair
                                    else:
                                        score_color = (0, 0, 255)  # Red for poor
                                    
                                    cv2.putText(image_bgr, percentage_text, (50, 80),
                                               font, 0.5, score_color, 2)
                    
                    # Emit frame for display
                    self.frame_ready.emit(image_bgr)
                    
                    # Small delay to control frame rate
                    self.msleep(33)  # ~30 fps
                    
                except Exception as e:
                    print(f"Error processing frame: {e}")
                    import traceback
                    traceback.print_exc()
                    self.msleep(100)
                    continue
            
        except Exception as e:
            print(f"Camera thread error: {e}")
            import traceback
            traceback.print_exc()
            self.frame_ready.emit(None)
        finally:
            if self.cap:
                try:
                    self.cap.release()
                    print("Camera released")
                except:
                    pass
    
    def stop(self):
        """Stop the camera thread"""
        self.running = False
        if self.cap:
            self.cap.release()


class PostureCorrectorWindow(QMainWindow):
    """Main window for Posture Corrector"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Posture Corrector")
        self.setGeometry(100, 100, 800, 700)
        
        # Initialize components
        self.monitor = PostureMonitor(
            warning_callback=self.show_warning,
            status_callback=self.on_status_update
        )
        self.warning_popup = WarningPopup()
        self.camera_thread = None  # Camera preview thread
        
        # Create UI
        self.init_ui()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_display)
        self.status_timer.start(100)  # Update every 100ms
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title
        title = QLabel("Made with 💖 for LV")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Status Group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Idle")
        status_font = QFont()
        status_font.setPointSize(16)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px;")
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addSpacing(10)
        
        # Camera Preview Group
        camera_group = QGroupBox("Camera Preview")
        camera_layout = QVBoxLayout()
        
        # Camera display label
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 360)
        self.camera_label.setMaximumSize(640, 360)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: #000000;
            }
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setText("Camera preview will appear here")
        self.camera_label.setScaledContents(True)
        camera_layout.addWidget(self.camera_label)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        layout.addSpacing(10)
        
        # Control Buttons
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()
        
        # Start/Stop buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        controls_layout.addLayout(button_layout)
        
        # Toggle camera button
        self.camera_button = QPushButton("Show Camera Preview")
        self.camera_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.camera_button.clicked.connect(self.toggle_camera)
        controls_layout.addWidget(self.camera_button)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        layout.addSpacing(10)
        
        # Details log
        details_group = QGroupBox("Activity Log")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(100)
        self.details_text.setPlaceholderText("Activity log will appear here...")
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        layout.addStretch()
    
    def start_monitoring(self):
        """Start posture monitoring"""
        if not self.monitor.running:
            # Check camera permission first
            if not check_camera_permission():
                # Try to request permission
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Camera Permission Required")
                msg.setText("Camera access is required for posture monitoring.")
                msg.setInformativeText(
                    "Please grant camera permission when prompted.\n\n"
                    "If no prompt appears, go to:\n"
                    "System Settings > Privacy & Security > Camera\n"
                    "and enable 'Posture Corrector'"
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
                
                # Try to trigger permission dialog
                if not request_camera_permission():
                    QMessageBox.warning(
                        self,
                        "Camera Access Denied",
                        "Camera permission is required. Please enable it in System Settings > Privacy & Security > Camera"
                    )
                    self.details_text.append("Camera permission denied. Please enable in System Settings.")
                    return
            
            self.monitor.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.details_text.append("Monitoring started. Please sit up straight for calibration...")
        else:
            QMessageBox.information(self, "Already Running", "Posture monitoring is already active")
    
    def stop_monitoring(self):
        """Stop posture monitoring"""
        if self.monitor.running:
            self.monitor.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.details_text.append("Monitoring stopped.")
        else:
            QMessageBox.information(self, "Not Running", "Posture monitoring is not currently active")
    
    def toggle_camera(self):
        """Toggle camera preview on/off"""
        if self.camera_thread is None or not self.camera_thread.isRunning():
            # Update button text immediately
            self.camera_button.setText("Starting Camera...")
            
            # Ensure camera thread is fully cleaned up
            if self.camera_thread is not None:
                # Make sure it's really stopped
                if self.camera_thread.isRunning():
                    try:
                        self.camera_thread.frame_ready.disconnect()
                    except:
                        pass
                    self.camera_thread.stop()
                    self.camera_thread.wait(2000)
                self.camera_thread = None
            
            # Attempt to trigger permission dialog by opening camera briefly
            # This will show the macOS permission prompt if not already granted
            self.details_text.append("Requesting camera permission...")
            cap = None
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    # Try to read a frame to fully trigger permission dialog
                    ret, _ = cap.read()
                    if ret:
                        self.details_text.append("Camera permission granted or already authorized.")
                    else:
                        self.details_text.append("Camera opened but frame read failed. Will retry in thread...")
                # Always release immediately - don't hold the camera
                if cap:
                    cap.release()
                    cap = None
            except Exception as e:
                if cap:
                    try:
                        cap.release()
                    except:
                        pass
                    cap = None
                self.details_text.append(f"Permission check: {str(e)}. Will attempt to start camera...")
            
            # Use QTimer to delay starting the thread, ensuring camera is fully released
            # This prevents the camera from being opened twice simultaneously
            delay_ms = 800
            
            def start_camera_thread():
                baseline = None
                if hasattr(self.monitor, 'baseline_ratio') and self.monitor.baseline_ratio > 0:
                    baseline = self.monitor.baseline_ratio
                
                # Pass monitor reference so camera preview can use its status
                self.camera_thread = CameraThread(baseline_ratio=baseline, monitor=self.monitor)
                self.camera_thread.frame_ready.connect(self.update_camera_frame)
                self.camera_thread.start()
                self.camera_button.setText("Hide Camera Preview")
                self.details_text.append("Camera preview thread started. Waiting for frames...")
            
            # Wait before starting thread to ensure camera is fully released
            QTimer.singleShot(delay_ms, start_camera_thread)
        else:
            # Stop camera - disconnect signal first to prevent more frames
            if self.camera_thread:
                # Disconnect the signal immediately to stop frame updates
                try:
                    self.camera_thread.frame_ready.disconnect()
                except:
                    pass
                
                # Clear the preview immediately before stopping thread
                self.camera_label.clear()
                self.camera_label.setPixmap(QPixmap())
                self.camera_label.setText("Camera preview will appear here")
                self.camera_label.setAlignment(Qt.AlignCenter)
                self.camera_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #cccccc;
                        border-radius: 5px;
                        background-color: #000000;
                    }
                """)
                
                # Update button text immediately
                self.camera_button.setText("Show Camera Preview")
                
                # Stop the thread
                self.camera_thread.stop()
                # Wait up to 2 seconds for thread to finish (timeout in milliseconds as positional arg)
                if not self.camera_thread.wait(2000):  # Returns False if timeout
                    # Thread didn't finish in time, force termination
                    self.camera_thread.terminate()
                    self.camera_thread.wait()  # Wait for termination
                self.camera_thread = None
                self.details_text.append("Camera preview stopped.")
    
    def update_camera_frame(self, frame):
        """Update the camera display with a new frame"""
        if frame is None:
            self.camera_label.setText("Error: Could not open camera\n\nPlease check:\n1. Camera permissions in System Settings\n2. No other app is using the camera")
            self.camera_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #ff0000;
                    border-radius: 5px;
                    background-color: #ffebee;
                    color: #c62828;
                    padding: 20px;
                }
            """)
            # Stop the thread
            if self.camera_thread:
                self.camera_thread.stop()
                self.camera_thread.wait()
                self.camera_thread = None
                self.camera_button.setText("Show Camera Preview")
            self.details_text.append("Camera error: Could not open camera")
            return
        
        try:
            # Convert OpenCV BGR frame to QImage
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            
            # Make sure frame data is contiguous
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
            
            # Convert to QPixmap and display
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.camera_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error updating camera frame: {e}")
            import traceback
            traceback.print_exc()
    
    def show_warning(self):
        """Show prominent warning popup"""
        self.warning_popup.show_warning()
        self.details_text.append("⚠️ POSTURE ALERT: Slouching detected!")
    
    def on_status_update(self, status):
        """Handle status updates from monitor"""
        # Check if monitoring stopped unexpectedly
        if "Stopped" in status or "Error" in status:
            # Update button states if monitoring stopped
            if not self.monitor.running:
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                if "Error" in status:
                    self.details_text.append(f"Monitoring stopped due to error: {status}")
        
        # Update status label
        if "SLOUCHING" in status:
            self.status_label.setText("⚠️ SLOUCHING")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffebee; color: #c62828; border-radius: 5px;")
        elif "Calibrating" in status:
            self.status_label.setText("📐 Calibrating...")
            self.status_label.setStyleSheet("padding: 10px; background-color: #fff3e0; color: #e65100; border-radius: 5px;")
        elif "Good" in status:
            self.status_label.setText("✓ Good Posture")
            self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; color: #2e7d32; border-radius: 5px;")
        elif "Error" in status:
            self.status_label.setText("❌ Error")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffebee; color: #c62828; border-radius: 5px;")
        elif "Stopped" in status:
            self.status_label.setText("Idle")
            self.status_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; color: #424242; border-radius: 5px;")
        else:
            self.status_label.setText("Idle")
            self.status_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; color: #424242; border-radius: 5px;")
    
    def update_display(self):
        """Update display with current status"""
        if hasattr(self.monitor, 'current_status'):
            # Status is updated via callback, this is just for periodic refresh
            pass
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop monitoring
        self.monitor.stop()
        
        # Stop camera preview
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread.wait()
        
        # Close any OpenCV windows
        try:
            cv2.destroyAllWindows()
        except:
            pass
        
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Posture Corrector")
    app.setApplicationDisplayName("Posture Corrector")
    
    window = PostureCorrectorWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

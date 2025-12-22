"""
Core posture detection logic using MediaPipe.
Handles camera capture, pose detection, calibration, and slouch detection.
Runs headless (no GUI window) to avoid threading conflicts with GUI frameworks.
"""
import cv2
import numpy as np
import time
import threading


class PostureMonitor:
    """Monitors posture using MediaPipe - runs headless for menu bar compatibility"""
    
    def __init__(self, warning_callback=None, status_callback=None):
        """
        Initialize the posture monitor.
        
        Args:
            warning_callback: Called when slouching is detected
            status_callback: Called with status updates (for UI feedback)
        """
        self.warning_callback = warning_callback
        self.status_callback = status_callback
        self.running = False
        self.thread = None
        
        # MediaPipe setup - delay initialization until start() is called
        self.mp_pose = None
        self.pose = None
        self.mp_drawing = None
        
        # Calibration
        self.calibration_frames = 0
        self.avg_ratio = 0
        self.is_calibrated = False
        self.calibration_limit = 90  # ~3 seconds at 30fps
        self.baseline_ratio = 0
        
        # Monitoring
        self.SENSITIVITY = 0.85
        self.slouch_timer = 0
        self.slouch_trigger_time = 3  # seconds of slouching before alert
        
        self.cap = None
        self.current_status = "Idle"
    
    def _initialize_mediapipe(self):
        """Initialize MediaPipe components (called on first start)"""
        if self.mp_pose is None:
            # Import MediaPipe only when needed (not at module level)
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
    
    def _update_status(self, status):
        """Update current status and notify callback"""
        self.current_status = status
        if self.status_callback:
            self.status_callback(status)
        
    def start(self):
        """Start monitoring in a separate thread"""
        if self.running:
            return
        # Initialize MediaPipe on first start (not during app initialization)
        self._initialize_mediapipe()
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop monitoring and release camera"""
        self.running = False
        
        # Wait a moment for loop to check the flag
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        
        # Force release camera
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        
        # Ensure OpenCV windows are closed
        try:
            cv2.destroyAllWindows()
        except:
            pass
        
        self._update_status("Stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop - runs headless (no GUI window)"""
        # Try to open camera with retry (gives time for permission dialog)
        self.cap = None
        for attempt in range(3):
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                # Test if we can actually read a frame
                ret, _ = self.cap.read()
                if ret:
                    break
            else:
                self.cap.release()
                self.cap = None
            time.sleep(0.5)  # Wait before retry
        
        if not self.cap or not self.cap.isOpened():
            self._update_status("Error: Camera access denied")
            self.running = False
            return
        
        self._update_status("Calibrating...")
        print("Calibrating... Please sit up straight for 3 seconds")
        
        # Reset calibration
        self.calibration_frames = 0
        self.avg_ratio = 0
        self.is_calibrated = False
        
        consecutive_failures = 0
        max_consecutive_failures = 30  # ~1 second at 30fps
        
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    # Camera failed multiple times - update status and exit gracefully
                    self._update_status("Error: Camera read failed")
                    print(f"Camera read failed {consecutive_failures} times - stopping monitoring")
                    break
                # Wait a bit before retrying
                time.sleep(0.033)
                continue
            else:
                # Reset failure counter on successful read
                consecutive_failures = 0

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image)

            h, w, _ = frame.shape

            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark

                nose = [lm[0].x * w, lm[0].y * h]
                l_shldr = [lm[11].x * w, lm[11].y * h]
                r_shldr = [lm[12].x * w, lm[12].y * h]

                shldr_mid_y = (l_shldr[1] + r_shldr[1]) / 2

                # Vertical distance (Neck Height)
                neck_height = abs(shldr_mid_y - nose[1])
                
                # Horizontal distance (Shoulder Width)
                shldr_width = np.linalg.norm(np.array(l_shldr) - np.array(r_shldr))

                if shldr_width > 0:  # Avoid division by zero
                    current_ratio = neck_height / shldr_width

                    if not self.is_calibrated:
                        # Calibration phase
                        self.calibration_frames += 1
                        self.avg_ratio += current_ratio
                        
                        progress = int((self.calibration_frames / self.calibration_limit) * 100)
                        self._update_status(f"Calibrating: {progress}%")
                        
                        if self.calibration_frames >= self.calibration_limit:
                            self.baseline_ratio = self.avg_ratio / self.calibration_limit
                            self.is_calibrated = True
                            self._update_status("Monitoring")
                            print(f"Calibration complete! Baseline Ratio: {self.baseline_ratio:.2f}")

                    else:
                        # Monitoring phase - check for slouch
                        if current_ratio < (self.baseline_ratio * self.SENSITIVITY):
                            self.slouch_timer += 1
                            # Update status to show slouching
                            if self.slouch_timer > 15:  # ~0.5 seconds
                                self._update_status("SLOUCHING!")
                        else:
                            self.slouch_timer = 0
                            self._update_status("Good posture")
                        
                        # Trigger Warning after sustained slouching
                        if self.slouch_timer > (30 * self.slouch_trigger_time):
                            if self.warning_callback:
                                self.warning_callback()
                            self.slouch_timer = 0  # Reset to prevent spam
            
            # Sleep to prevent CPU hogging (no cv2.waitKey since we're headless)
            time.sleep(0.033)  # ~30 fps
            
            # Check if we should stop more frequently
            if not self.running:
                break
                
        # Cleanup: release camera
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        
        # Ensure camera is fully released
        import gc
        gc.collect()
        
        self.running = False
        self._update_status("Stopped")

"""
Menu bar application UI component.
Provides a macOS menu bar interface to control the posture monitor.
"""
import rumps
import subprocess
import sys
import os
from posture_monitor import PostureMonitor
from warning_popup import WarningPopup


class PostureCorrectorApp(rumps.App):
    """Menu bar application for posture corrector"""
    
    def __init__(self):
        """Initialize the menu bar application"""
        # Initialize with name and title - title shows in menu bar
        # quit_button=None to avoid duplicate since we have our own Quit
        super(PostureCorrectorApp, self).__init__(
            name="Posture Corrector",
            title="P",
            quit_button=None  # We handle quit ourselves
        )
        self.monitor = PostureMonitor(
            warning_callback=self.show_warning,
            status_callback=self.update_status
        )
        self.warning_popup = WarningPopup()
        self.camera_process = None
        # Menu items
        self.menu = ["Start Monitoring", "Stop Monitoring", None, "Show Camera", None, "Quit"]
        
    def update_status(self, status):
        """Update the menu bar title with current status"""
        if "SLOUCHING" in status:
            self.title = "P!"
        elif "Calibrating" in status:
            self.title = "P~"
        elif "Good" in status:
            self.title = "P"
        elif "Error" in status:
            self.title = "P?"
        else:
            self.title = "P"
        
    @rumps.clicked("Start Monitoring")
    def start_monitoring(self, _):
        """Start posture monitoring"""
        if not self.monitor.running:
            self.monitor.start()
            self.title = "P~"  # Calibrating
            rumps.notification(
                "Posture Corrector",
                "Calibrating...",
                "Please sit up straight for 3 seconds"
            )
        else:
            rumps.alert("Already Running", "Posture monitoring is already active")
    
    @rumps.clicked("Stop Monitoring")
    def stop_monitoring(self, _):
        """Stop posture monitoring"""
        if self.monitor.running:
            self.monitor.stop()
            self.title = "P"
            rumps.notification(
                "Posture Corrector",
                "Monitoring Stopped",
                "Posture monitoring has been stopped"
            )
        else:
            rumps.alert("Not Running", "Posture monitoring is not currently active")
    
    def show_warning(self):
        """Show prominent warning popup"""
        self.warning_popup.show_warning()
    
    @rumps.clicked("Show Camera")
    def show_camera(self, _):
        """Open camera preview window"""
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        camera_script = os.path.join(script_dir, "camera_preview.py")
        
        # Always pass baseline ratio if available (even if monitoring is stopped)
        args = [sys.executable, camera_script]
        if hasattr(self.monitor, 'baseline_ratio') and self.monitor.baseline_ratio > 0:
            args.append(str(self.monitor.baseline_ratio))
        
        # Launch camera preview as separate process
        try:
            # Close existing camera if open
            if self.camera_process and self.camera_process.poll() is None:
                self.camera_process.terminate()
            
            self.camera_process = subprocess.Popen(args)
        except Exception as e:
            rumps.alert("Error", f"Could not open camera: {e}")
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the application"""
        # Stop monitoring first (releases camera)
        self.monitor.stop()
        
        # Close camera preview if open
        if self.camera_process:
            try:
                self.camera_process.terminate()
                self.camera_process.wait(timeout=1)
            except:
                try:
                    self.camera_process.kill()
                except:
                    pass
        
        # Give a moment for cleanup
        import time
        time.sleep(0.2)
        
        rumps.quit_application()

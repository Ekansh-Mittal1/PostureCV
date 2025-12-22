"""
Warning popup UI component.
Creates prominent warnings using native macOS dialogs and notifications.
"""
import time
import threading
import subprocess


class WarningPopup:
    """Creates a prominent full-screen warning popup using native macOS"""
    
    def __init__(self):
        """Initialize the warning popup"""
        self.is_showing = False
        
    def show_warning(self, message="⚠️ POSTURE ALERT ⚠️", submessage="Sit tall! Your posture is slipping."):
        """
        Display a prominent warning using native macOS dialogs and notifications.
        
        Args:
            message: Main warning message
            submessage: Additional details message
        """
        if self.is_showing:
            return
            
        self.is_showing = True
        
        # Create a very prominent alert using osascript
        # This creates a modal dialog that appears on top of everything
        alert_script = f'''
        tell application "System Events"
            activate
            display dialog "{message}\\n\\n{submessage}" with title "⚠️ POSTURE ALERT ⚠️" buttons {{"OK"}} default button "OK" with icon caution giving up after 3
        end tell
        '''
        
        # Run the alert in background
        subprocess.Popen(['osascript', '-e', alert_script], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Also send a notification
        notification_script = f'''
        display notification "{submessage}" with title "{message}" sound name "Basso"
        '''
        subprocess.Popen(['osascript', '-e', notification_script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        
        # Reset flag after a delay
        def reset_flag():
            time.sleep(1)
            self.is_showing = False
        
        threading.Thread(target=reset_flag, daemon=True).start()



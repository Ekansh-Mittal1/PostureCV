"""
Camera preview window with pose detection overlay.
Small popup window that appears when clicking the menu bar icon.
"""
import cv2
import numpy as np
import sys
import os
import platform


def show_camera_preview(baseline_ratio=None):
    """
    Show camera preview with pose detection overlay in a small popup window.
    
    Args:
        baseline_ratio: If provided, shows slouch detection. Otherwise just shows pose.
    """
    # Import MediaPipe (delay import to avoid issues when bundled)
    try:
        import mediapipe as mp
    except ImportError:
        print("Error: MediaPipe not available")
        return
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Set window to small popup size (like a menu bar dropdown)
    window_width = 320
    window_height = 240
    
    # Create window
    cv2.namedWindow('Posture Preview', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Posture Preview', window_width, window_height)
    
    # Position window near top-right (where menu bar is)
    # Get screen dimensions for better positioning
    if platform.system() == 'Darwin':  # macOS
        try:
            # Try to get screen width using system_profiler or defaults
            import subprocess
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                  capture_output=True, text=True)
            # For simplicity, position at a reasonable offset from right edge
            # Most Mac screens are at least 1440px wide, so position at right edge minus window width
            screen_width = 1920  # Default, will be adjusted
            x_position = screen_width - window_width - 20  # 20px margin from right edge
            cv2.moveWindow('Posture Preview', x_position, 30)  # 30px from top (below menu bar)
        except:
            # Fallback: position at fixed location
            cv2.moveWindow('Posture Preview', 1600, 30)
    
    # Set window to stay on top (if possible)
    cv2.setWindowProperty('Posture Preview', cv2.WND_PROP_TOPMOST, 1)
    
    print("Camera preview opened. Press 'Q' to close.")
    
    SENSITIVITY = 0.85
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame to small preview size
        frame = cv2.resize(frame, (window_width, window_height))
        
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        h, w, _ = image.shape

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            nose = [lm[0].x * w, lm[0].y * h]
            l_shldr = [lm[11].x * w, lm[11].y * h]
            r_shldr = [lm[12].x * w, lm[12].y * h]

            shldr_mid_x = (l_shldr[0] + r_shldr[0]) / 2
            shldr_mid_y = (l_shldr[1] + r_shldr[1]) / 2

            # Vertical distance (Neck Height)
            neck_height = abs(shldr_mid_y - nose[1])
            
            # Horizontal distance (Shoulder Width)
            shldr_width = np.linalg.norm(np.array(l_shldr) - np.array(r_shldr))

            if shldr_width > 0:
                current_ratio = neck_height / shldr_width

                # Draw pose lines (thinner for small window)
                cv2.line(image, (int(shldr_mid_x), int(shldr_mid_y)), 
                        (int(nose[0]), int(nose[1])), (255, 255, 0), 1)
                cv2.line(image, (int(l_shldr[0]), int(l_shldr[1])), 
                        (int(r_shldr[0]), int(r_shldr[1])), (255, 0, 255), 1)

                # Draw pose landmarks (smaller for compact view)
                mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=1)
                )

                # Show status with professional font - always show if baseline exists
                if baseline_ratio:
                    if current_ratio < (baseline_ratio * SENSITIVITY):
                        status = "SLOUCHING"
                        color = (0, 0, 255)  # Red
                        bg_color = (0, 0, 0)
                    else:
                        status = "GOOD POSTURE"
                        color = (0, 255, 0)  # Green
                        bg_color = (0, 0, 0)
                    
                    # Use FONT_HERSHEY_DUPLEX for more professional look
                    font = cv2.FONT_HERSHEY_DUPLEX
                    font_scale = 0.5
                    thickness = 1
                    
                    # Get text size for background
                    (text_width, text_height), baseline = cv2.getTextSize(
                        status, font, font_scale, thickness
                    )
                    
                    # Draw background rectangle for better readability
                    cv2.rectangle(image, (5, 5), (text_width + 10, text_height + 10), 
                                 bg_color, -1)
                    
                    # Draw status text
                    cv2.putText(image, status, (10, text_height + 5), 
                               font, font_scale, color, thickness)
                    
                    # Show ratio in smaller font below
                    ratio_text = f"{current_ratio:.2f} / {baseline_ratio:.2f}"
                    (ratio_width, ratio_height), _ = cv2.getTextSize(
                        ratio_text, font, 0.35, 1
                    )
                    cv2.rectangle(image, (5, text_height + 15), 
                                 (ratio_width + 10, text_height + ratio_height + 15), 
                                 bg_color, -1)
                    cv2.putText(image, ratio_text, (10, text_height + ratio_height + 10), 
                               font, 0.35, (255, 255, 255), 1)
                else:
                    # No baseline - just show ratio
                    font = cv2.FONT_HERSHEY_DUPLEX
                    ratio_text = f"Ratio: {current_ratio:.2f}"
                    cv2.putText(image, ratio_text, (10, 25), 
                               font, 0.5, (255, 255, 255), 1)
        
        # Small close instruction at bottom
        cv2.putText(image, "Press Q to close", (5, h - 5), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.3, (150, 150, 150), 1)

        cv2.imshow('Posture Preview', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup: release camera properly
    try:
        cap.release()
    except:
        pass
    
    # Close all windows
    try:
        cv2.destroyAllWindows()
    except:
        pass
    
    # Force garbage collection to ensure camera is released
    import gc
    gc.collect()
    
    print("Camera preview closed.")


if __name__ == "__main__":
    # Can pass baseline_ratio as command line argument
    baseline = None
    if len(sys.argv) > 1:
        try:
            baseline = float(sys.argv[1])
        except ValueError:
            pass
    
    show_camera_preview(baseline)

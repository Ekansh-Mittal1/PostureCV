"""
Main entry point for the Posture Corrector application.
Launches the GUI application (PySide6-based).
"""
import sys
import signal
import traceback

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nShutting down Posture Corrector...")
    sys.exit(0)

def main():
    """Main entry point with error handling"""
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("=" * 60)
        print("Posture Corrector - Starting...")
        print("=" * 60)
        print("\nApplication window will open shortly")
        print("All controls are in the window")
        print("Press Ctrl+C to quit\n")
        
        # Import after print so we can see if it crashes
        print("Loading GUI...")
        from src.gui_app import main as gui_main
        
        print("Starting application window...")
        print("✓ Application window should open")
        print("\n" + "=" * 60)
        print("Application window is opening")
        print("All controls are in the window")
        print("=" * 60 + "\n")
        
        # Run the GUI
        exit_code = gui_main()
        return exit_code
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

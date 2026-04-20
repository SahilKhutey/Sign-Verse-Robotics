import cv2
import time
import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.perception.orchestrator import PerceptionOrchestrator
from src.perception.visualizer import PerceptionVisualizer

def main():
    parser = argparse.ArgumentParser(description="Sign-Verse Perception Demo v5.1")
    parser.add_argument("--source", type=str, default="0", help="Video source (index or path)")
    parser.add_argument("--gpu", action="store_true", default=True, help="Use GPU acceleration")
    args = parser.parse_args()

    print(f"[Launcher] Initializing Sign-Verse Perception Suite...")
    print(f"[Launcher] Source: {args.source}")
    
    # Initialize Core Engines
    try:
        orchestrator = PerceptionOrchestrator(use_gpu=args.gpu)
        visualizer = PerceptionVisualizer()
    except Exception as e:
        print(f"[Critical Error] Failed to initialize perception engines: {e}")
        return

    # Initialize Capture
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"[Error] Could not open video source: {args.source}")
        return

    print("[Launcher] Platform Sovereign. Running Perception Loop...")
    
    try:
        while True:
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                print("[Launcher] End of stream or capture lost.")
                break
            
            # Process Frame
            # Note: PerceptionOrchestrator handles YOLO discovery & MediaPipe sub-models
            frame_data = orchestrator.process(frame, timestamp=time.time())
            
            # Visualize
            display_frame = visualizer.render(frame, frame_data)
            
            # Show Result
            cv2.imshow("Sign-Verse Robotics | Perception Command Center", display_frame)
            
            # Exit conditions
            if cv2.waitKey(1) & 0xFF == ord('q') or cv2.waitKey(1) & 0xFF == 27:
                break
                
    except KeyboardInterrupt:
        print("\n[Launcher] Shutdown requested by user.")
    except Exception as e:
        print(f"[Runtime Error] {e}")
    finally:
        print("[Launcher] Releasing resources...")
        cap.release()
        orchestrator.release()
        cv2.destroyAllWindows()
        print("[Launcher] System Hibernated.")

if __name__ == "__main__":
    main()

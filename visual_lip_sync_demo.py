#!/usr/bin/env python3
"""
Visual-Only Lip Sync Demo for TV Display
No audio, just visual mouth animation
"""

import cv2
import numpy as np
import time

class VisualLipSyncDemo:
    def __init__(self):
        self.mouth_state = 0.0

    def draw_avatar(self, frame, is_speaking=False):
        """Draw avatar with animated mouth"""
        h, w = frame.shape[:2]
        cx, cy = w//2, h//2

        # Head
        cv2.circle(frame, (cx, cy-50), 250, (200, 180, 160), -1)
        cv2.circle(frame, (cx, cy-50), 250, (100, 80, 60), 3)

        # Eyes
        eye_y = cy - 100
        cv2.ellipse(frame, (cx-70, eye_y), (35, 30), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(frame, (cx+70, eye_y), (35, 30), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (cx-70, eye_y), 15, (50, 50, 200), -1)
        cv2.circle(frame, (cx+70, eye_y), 15, (50, 50, 200), -1)

        # Animated mouth
        mouth_y = cy + 40
        mouth_width = 60
        mouth_height = int(20 + self.mouth_state * 40)  # 20-60 pixels

        if is_speaking:
            cv2.ellipse(frame, (cx, mouth_y), (mouth_width, mouth_height), 0, 0, 180, (50, 50, 50), -1)
        else:
            cv2.ellipse(frame, (cx, mouth_y), (mouth_width, 20), 0, 0, 180, (50, 50, 50), 2)

        # Status text
        status = "🗣️ Speaking..." if is_speaking else "Idle - Visual Demo"
        cv2.putText(frame, status, (100, h-100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

        # Instructions
        cv2.putText(frame, "Lip Sync Avatar Demo", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 0), 4)
        cv2.putText(frame, "Watch the mouth move!", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)

        return frame

    def run_demo(self):
        """Run the visual lip sync demo"""
        print("🎭 Starting Visual Lip Sync Demo on TV...")

        # Set up display
        cv2.namedWindow('Lip Sync Avatar', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Lip Sync Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        print("✅ Display window created")
        print("🎬 Starting animation sequence...")

        try:
            frame_count = 0
            while frame_count < 600:  # Run for about 20 seconds at 30fps
                frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                frame[:] = (40, 40, 60)  # Dark blue background

                # Animate mouth based on frame count
                if frame_count < 150:  # First 5 seconds - speaking
                    self.mouth_state = 0.8
                    is_speaking = True
                elif frame_count < 300:  # Next 5 seconds - different mouth shape
                    self.mouth_state = 0.4
                    is_speaking = True
                elif frame_count < 450:  # Next 5 seconds - closed mouth
                    self.mouth_state = 0.0
                    is_speaking = False
                else:  # Final 5 seconds - speaking again
                    self.mouth_state = abs(np.sin(frame_count * 0.1)) * 0.6 + 0.2
                    is_speaking = True

                frame = self.draw_avatar(frame, is_speaking)
                cv2.imshow('Lip Sync Avatar', frame)

                # Check for quit key
                key = cv2.waitKey(33) & 0xFF  # ~30fps
                if key == ord('q') or key == 27:  # q or ESC
                    break

                frame_count += 1

            print("✅ Visual demo complete!")

        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted")
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            cv2.destroyAllWindows()
            print("🧹 Display cleanup complete")

if __name__ == "__main__":
    demo = VisualLipSyncDemo()
    demo.run_demo()

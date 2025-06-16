import numpy as np
import cv2  # This import was missing!
from picamera2 import Picamera2
import time
import os
from datetime import datetime
from adafruit_servokit import ServoKit

# Camera FOV (Arducam IMX519)
fov_horizontal = 72.9  # degrees
fov_vertical = 54.1    # degrees

# Servo setup
kit = ServoKit(channels=16)
pan, tilt = 90, 45
kit.servo[0].angle = pan
kit.servo[1].angle = tilt

print("Testing Servo 0")
kit.servo[0].angle = 45
time.sleep(1)
kit.servo[0].angle = 135
time.sleep(1)
kit.servo[0].angle = pan  # Return to center
time.sleep(1)

# Camera setup
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

dispW, dispH = 640, 480
width, height = dispW, dispH

# Video recording setup
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
video_filename = f"object_tracking_{timestamp}.mp4"
video_path = os.path.join(desktop_path, video_filename)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can also try 'XVID'
fps = 20.0  # Frames per second
out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

print(f"Starting object tracking and recording to: {video_path}")
print("Press 'q' to quit and save video.")

frame_count = 0
start_time = time.time()

while True:
    frame = picam2.capture_array()
    
    # Resize frame if needed
    frame = cv2.resize(frame, (width, height))
    
    # Convert RGB to BGR (picamera2 gives RGB by default)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.GaussianBlur(frame, (5, 5), 0)  # Reduce noise
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Color range for purple object detection
    # Purple/Violet HSV range
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([35, 255, 255])

    # Create mask for purple
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Alternative purple ranges (uncomment if the above doesn't work well)
    # For darker purple:
    # lower_purple = np.array([110, 50, 50])
    # upper_purple = np.array([140, 255, 255])
    
    # For lighter purple/magenta:
    # lower_purple = np.array([140, 50, 50])
    # upper_purple = np.array([170, 255, 255])
    
    # Morphological operations to clean up the mask
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create a clean frame for recording (without overlays)
    clean_frame = frame.copy()
    
    # Add overlays only to the display frame (not the recorded frame)
    display_frame = frame.copy()
    
    if contours:
        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        cnt = contours[0]
        area = cv2.contourArea(cnt)
        
        print(f"Largest contour area: {area}")  # Debug output
        
        if area > 100:  # Minimum area threshold
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(cnt)
            objX = x + w // 2
            objY = y + h // 2
            
            # Calculate error from center
            errorX = objX - width // 2
            errorY = objY - height // 2
            
            print(f"Object center: ({objX}, {objY}), Error: ({errorX}, {errorY})")
            
            # Convert pixel error to angle error
            angle_error_pan = (errorX / width) * fov_horizontal
            angle_error_tilt = (errorY / height) * fov_vertical
            
            # Apply servo control with damping
            damping = 8
            kp = 1.0  # Proportional gain
            
            # Calculate new servo positions
            pan_adjustment = (angle_error_pan * kp) / damping
            tilt_adjustment = (angle_error_tilt * kp) / damping
            
            # Update servo positions (try both directions to see which works)
            # If movement is opposite to what you expect, swap the + and - signs
            pan = max(0, min(180, pan - pan_adjustment))      # Try + first
            tilt = max(0, min(180, tilt - tilt_adjustment))   # Try - first
            
            # Alternative directions (uncomment if above moves opposite):
            # pan = max(0, min(180, pan - pan_adjustment))
            # tilt = max(0, min(180, tilt + tilt_adjustment))
            
            # Apply new servo angles
            kit.servo[0].angle = pan
            kit.servo[1].angle = tilt
            
            print(f"Servo angles - Pan: {pan:.1f}, Tilt: {tilt:.1f}")
            
            # Draw tracking visuals on display frame only (not on recorded video)
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.circle(display_frame, (int(objX), int(objY)), 5, (0, 255, 0), -1)
            cv2.putText(display_frame, f"Area: {int(area)}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    else:
        print("No objects detected")
    
    # Draw center crosshair on display only
    cv2.line(display_frame, (width//2 - 20, height//2), (width//2 + 20, height//2), (0, 255, 255), 1)
    cv2.line(display_frame, (width//2, height//2 - 20), (width//2, height//2 + 20), (0, 255, 255), 1)
    
    # Display current servo positions on display frame only
    cv2.putText(display_frame, f"Pan: {pan:.1f}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(display_frame, f"Tilt: {tilt:.1f}", (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Add recording indicator on display frame only
    cv2.circle(display_frame, (width - 30, 30), 10, (0, 0, 255), -1)  # Red recording dot
    cv2.putText(display_frame, "REC", (width - 60, 35), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    # Add frame counter and time on display frame only
    elapsed_time = time.time() - start_time
    cv2.putText(display_frame, f"Time: {elapsed_time:.1f}s", (10, height - 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(display_frame, f"Frame: {frame_count}", (10, height - 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Write clean frame to video file (no overlays)
    out.write(clean_frame)
    frame_count += 1
    
    # Display windows (use display_frame for camera view)
    cv2.imshow('Camera', display_frame)
    cv2.imshow('Mask', mask)
    
    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
picam2.stop()
cv2.destroyAllWindows()
out.release()  # Important: release the video writer

print(f"Tracking stopped. Video saved to: {video_path}")
print(f"Total frames recorded: {frame_count}")
print(f"Total recording time: {time.time() - start_time:.1f} seconds")

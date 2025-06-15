import numpy as np
import cv2  # This import was missing!
from picamera2 import Picamera2
import time
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

print("Starting object tracking. Press 'q' to quit.")

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
            
            # Draw tracking visuals
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.circle(frame, (int(objX), int(objY)), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"Area: {int(area)}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    else:
        print("No objects detected")
    
    # Draw center crosshair
    cv2.line(frame, (width//2 - 20, height//2), (width//2 + 20, height//2), (0, 255, 255), 1)
    cv2.line(frame, (width//2, height//2 - 20), (width//2, height//2 + 20), (0, 255, 255), 1)
    
    # Display current servo positions on frame
    cv2.putText(frame, f"Pan: {pan:.1f}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Tilt: {tilt:.1f}", (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Display windows
    cv2.imshow('Camera', frame)
    cv2.imshow('Mask', mask)
    
    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
picam2.stop()
cv2.destroyAllWindows()
print("Tracking stopped.")

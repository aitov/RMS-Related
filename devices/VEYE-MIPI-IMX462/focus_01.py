import cv2
import numpy as np
import time
import os

# --- Configuration ---
DEVICE_ID = 0
WIDTH, HEIGHT = 1920, 1080
FRAMES_TO_STACK = 40

cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw,format=UYVY, width=1920, height=1080,framerate=30/1 ! videoconvert ! appsink sync=1")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# Manual V4L2 settings
os.system(f"v4l2-ctl -d {DEVICE_ID} -c exposure_auto=1")
os.system(f"v4l2-ctl -d {DEVICE_ID} -c exposure_absolute=1000")
os.system(f"v4l2-ctl -d {DEVICE_ID} -c gain=200")

# Variables for locking
lock_x, lock_y = WIDTH // 2, HEIGHT // 2
locked = False

print("--- STAR FOCUS & CAPTURE TOOL (LOCKED MODE) ---")
print("Controls:")
print("  Tab - LOCK / RELOCK on the brightest star")
print("  's' - Start Long Exposure (Stacking)")
print("  'q' - Quit")

while True:
    ret, frame = cap.read()
    if not ret: break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 1. Update star position only if NOT locked or if Tab is pressed
    key = cv2.waitKey(1) & 0xFF

    if key == 9:  # TAB key
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)
        lock_x, lock_y = max_loc
        locked = True
        print(f"Locked on star at: {lock_x}, {lock_y}")

    # 2. Preparation for Preview
    small_frame = cv2.resize(frame, (640, 360))
    scale_x, scale_y = 640 / WIDTH, 360 / HEIGHT
    px, py = int(lock_x * scale_x), int(lock_y * scale_y)

    # Draw Marker and Box on Preview
    color = (0, 255, 0) if locked else (0, 0, 255)
    cv2.rectangle(small_frame, (px-20, py-20), (px+20, py+20), color, 1)
    if not locked:
        cv2.putText(small_frame, "PRESS TAB TO LOCK", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

    cv2.imshow("Full Preview", small_frame)

    # 3. Focus Analysis (Locked Area)
    d = 50
    if d < lock_x < WIDTH - d and d < lock_y < HEIGHT - d:
        crop = frame[lock_y-d:lock_y+d, lock_x-d:lock_x+d]
        gray_crop = blurred[lock_y-d:lock_y+d, lock_x-d:lock_x+d]

        # Calculate local brightness to handle flickering stars
        local_max = np.max(gray_crop)
        _, thresh = cv2.threshold(gray_crop, local_max * 0.75, 255, cv2.THRESH_BINARY)
        star_area = np.sum(thresh == 255)

        zoom = cv2.resize(crop, (400, 400), interpolation=cv2.INTER_NEAREST)
        status = "LOCKED" if locked else "AUTO-SCAN"
        cv2.putText(zoom, f"{status} | Area: {star_area}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.imshow("Focus Zoom", zoom)

    # 4. Long Exposure Mode
    if key == ord('s'):
        print(f"\nCapturing exposure... Stand by.")
        stacked = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        for i in range(FRAMES_TO_STACK):
            r, f = cap.read()
            if r: stacked += cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)

        stacked = cv2.normalize(stacked, None, 0, 255, cv2.NORM_MINMAX)
        fname = f"star_shot_{int(time.time())}.jpg"
        cv2.imwrite(fname, stacked.astype(np.uint8))
        print(f"Saved: {fname}")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

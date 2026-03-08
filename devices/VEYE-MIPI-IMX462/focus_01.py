import cv2
import numpy as np
import time
import os

# --- Configuration ---
DEVICE_ID = 0
WIDTH, HEIGHT = 1920, 1080
FRAMES_TO_STACK = 40 # Number of frames for "Long Exposure" simulation

cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw,format=UYVY, width=1920, height=1080,framerate=30/1 ! videoconvert ! appsink sync=1")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# Set manual exposure/gain for star visibility using V4L2
os.system(f"v4l2-ctl -d {DEVICE_ID} -c exposure_auto=1") # Manual
os.system(f"v4l2-ctl -d {DEVICE_ID} -c exposure_absolute=1000") # High exposure
os.system(f"v4l2-ctl -d {DEVICE_ID} -c gain=200") # High gain

print("--- STAR FOCUS & CAPTURE TOOL ---")
print("Controls:")
print("  'q' - Quit")
print("  's' - Start Long Exposure (Save Image)")
print("Goal: Minimize 'Star Area' using your 11cm lever.")

while True:
    ret, frame = cap.read()
    if not ret: break

    # --- MODE 1: LIVE FOCUS ANALYSIS ---
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)
    x, y = max_loc

    # High-precision crop for focusing
    d = 50
    if d < x < WIDTH - d and d < y < HEIGHT - d:
        crop = frame[y-d:y+d, x-d:x+d]
        gray_crop = blurred[y-d:y+d, x-d:x+d]
        _, thresh = cv2.threshold(gray_crop, max_val * 0.75, 255, cv2.THRESH_BINARY)
        star_area = np.sum(thresh == 255)

        zoom = cv2.resize(crop, (400, 400), interpolation=cv2.INTER_NEAREST)
        cv2.putText(zoom, f"Star Area: {star_area}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Focus Zoom (Live)", zoom)

    # Preview window
    small_frame = cv2.resize(frame, (640, 360))
    cv2.imshow("Full Preview", small_frame)

    key = cv2.waitKey(1) & 0xFF

    # --- MODE 2: LONG EXPOSURE (Press 's') ---
    if key == ord('s'):
        print(f"\nCapturing {FRAMES_TO_STACK} frames. DO NOT TOUCH THE CAMERA...")
        stacked = np.zeros((HEIGHT, WIDTH), dtype=np.float32)

        for i in range(FRAMES_TO_STACK):
            r, f = cap.read()
            if r:
                g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
                stacked += g
            print(f"Stacking: {int((i/FRAMES_TO_STACK)*100)}%", end='\r')

        # Normalize and save
        stacked = cv2.normalize(stacked, None, 0, 255, cv2.NORM_MINMAX)
        final_img = stacked.astype(np.uint8)
        fname = f"star_shot_{int(time.time())}.jpg"
        cv2.imwrite(fname, final_img)
        print(f"\nSaved: {fname}. Resuming live focus...")

        # Briefly show the result
        cv2.imshow("Last Capture", cv2.resize(final_img, (960, 540)))
        cv2.waitKey(2000) # Wait 2 seconds

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
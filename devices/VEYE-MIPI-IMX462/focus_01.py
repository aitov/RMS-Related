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

# Initial V4L2 setup
os.system(f"v4l2-ctl -d {DEVICE_ID} -c exposure_auto=1")
os.system(f"v4l2-ctl -d {DEVICE_ID} -c exposure_absolute=1000")
os.system(f"v4l2-ctl -d {DEVICE_ID} -c gain=200")

print("--- STAR FOCUS & CAPTURE TOOL ---")
print("Controls: 'q' - Quit | 's' - Save Long Exposure")

while True:
    ret, frame = cap.read()
    if not ret: break

    # 1. Background Analysis (Grayscale + Blur)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, max_val, _, max_loc = cv2.minMaxLoc(blurred)
    x, y = max_loc

    # 2. CREATE PREVIEW (RESIZED)
    small_frame = cv2.resize(frame, (640, 360))

    # 3. DRAW SELECTION BOX ON PREVIEW
    # We translate 1920x1080 coordinates to 640x360
    scale_x = 640 / WIDTH
    scale_y = 360 / HEIGHT
    px, py = int(x * scale_x), int(y * scale_y)
    p_box = int(50 * scale_x) # 50px crop radius scaled down

    # Draw Green Box and Red Crosshair on the Full View
    cv2.rectangle(small_frame, (px - p_box, py - p_box), (px + p_box, py + p_box), (0, 255, 0), 2)
    cv2.drawMarker(small_frame, (px, py), (0, 0, 255), cv2.MARKER_CROSS, 15, 2)

    cv2.imshow("Full Preview (Selection Visible)", small_frame)

    # 4. ZOOM WINDOW LOGIC
    d = 50
    if d < x < WIDTH - d and d < y < HEIGHT - d:
        crop = frame[y-d:y+d, x-d:x+d]
        gray_crop = blurred[y-d:y+d, x-d:x+d]

        # Calculate Star Area (FWHM metric)
        _, thresh = cv2.threshold(gray_crop, max_val * 0.75, 255, cv2.THRESH_BINARY)
        star_area = np.sum(thresh == 255)

        # Create zoomed window
        zoom = cv2.resize(crop, (400, 400), interpolation=cv2.INTER_NEAREST)
        cv2.putText(zoom, f"Area: {star_area}", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        cv2.imshow("Focus Zoom (High Res)", zoom)

    # 5. KEYBOARD COMMANDS
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        print(f"\nSTARTING LONG EXPOSURE... STACKING {FRAMES_TO_STACK} FRAMES")
        stacked = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
        for i in range(FRAMES_TO_STACK):
            r, f = cap.read()
            if r:
                stacked += cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
            print(f"Progress: {int((i/FRAMES_TO_STACK)*100)}%", end='\r')

        stacked = cv2.normalize(stacked, None, 0, 255, cv2.NORM_MINMAX)
        final_img = stacked.astype(np.uint8)
        fname = f"star_capture_{int(time.time())}.jpg"
        cv2.imwrite(fname, final_img)
        print(f"\nFILE SAVED: {fname}")

        # Flash the result
        cv2.imshow("Capture Result (2sec Preview)", cv2.resize(final_img, (960, 540)))
        cv2.waitKey(2000)

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
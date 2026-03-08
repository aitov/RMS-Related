import cv2
import numpy as np

# --- Configuration ---
# DEVICE_ID = 0  # Camera index (V4L2)
WIDTH, HEIGHT = 1920, 1080  # IMX662 sensor resolution
#
# cap = cv2.VideoCapture(DEVICE_ID)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw,format=UYVY, width=1920, height=1080,framerate=30/1 ! videoconvert ! appsink sync=1")
# Increase exposure/gain if possible via V4L2 for better star visibility
# cap.set(cv2.CAP_PROP_EXPOSURE, -5)

print("Focusing Tool Started.")
print("1. Point at a bright star.")
print("2. Move your 11cm lever by 1-2mm increments.")
print("3. Goal: MINIMIZE the 'Star Area' value.")
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Convert to grayscale and apply slight blur to reduce sensor noise
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # 2. Locate the brightest pixel (the target star)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)
    x, y = max_loc

    # 3. Define crop area (100x100 pixels) around the star
    d = 50
    if d < x < WIDTH - d and d < y < HEIGHT - d:
        crop = frame[y-d:y+d, x-d:x+d]
        gray_crop = blurred[y-d:y+d, x-d:x+d]

        # 4. Calculate star "tightness" using binary threshold
        # We only count pixels that are at least 70% of the peak brightness
        _, thresh = cv2.threshold(gray_crop, max_val * 0.7, 255, cv2.THRESH_BINARY)
        star_area = np.sum(thresh == 255)

        # 5. Create a high-magnification window (Digital Eyepiece)
        zoom = cv2.resize(crop, (400, 400), interpolation=cv2.INTER_NEAREST)

        # Display the numerical Star Area (FWHM-like metric)
        cv2.putText(zoom, f"Star Area: {star_area}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Visual crosshair for centering
        cv2.line(zoom, (200, 180), (200, 220), (0, 0, 255), 1)
        cv2.line(zoom, (180, 200), (220, 200), (0, 0, 255), 1)

        cv2.imshow("Focus Zoom (High Precision)", zoom)

    # 6. Orientation view (resized full frame)
    small_frame = cv2.resize(frame, (640, 360))
    cv2.circle(small_frame, (int(x * 640 / WIDTH), int(y * 360 / HEIGHT)), 10, (0, 255, 0), 2)
    cv2.imshow("Full Frame (Preview)", small_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
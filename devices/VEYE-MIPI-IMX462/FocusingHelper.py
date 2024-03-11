import cv2

# RPi5 config should be device id and without Gray8 convert
cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw,format=UYVY, width=1920, height=1080,framerate=30/1 ! videoconvert ! appsink sync=1")
#cap.set(3, 1920)
#cap.set(4, 1080)

while True:
    success, img = cap.read()
    imgLeftUpCorner = img[0:200, 0:200]
    imgLeftUpCorner = cv2.resize(imgLeftUpCorner, (imgLeftUpCorner.shape[1] * 2, imgLeftUpCorner.shape[0] * 2))

    imgRightUpCorner = img[0:200, 1720:1920]
    imgRightUpCorner = cv2.resize(imgRightUpCorner, (imgRightUpCorner.shape[1] * 2, imgRightUpCorner.shape[0] * 2))

    imgLeftDownCorner = img[880:1080, 0:200]
    imgLeftDownCorner = cv2.resize(imgLeftDownCorner, (imgLeftDownCorner.shape[1] * 2, imgLeftDownCorner.shape[0] * 2))

    imgRightDownCorner = img[880:1080, 1720:1920]
    imgRightDownCorner = cv2.resize(imgRightDownCorner,
                                    (imgRightDownCorner.shape[1] * 2, imgRightDownCorner.shape[0] * 2))

    imgCenter = img[440:640, 860:1060]
    imgCenter = cv2.resize(imgCenter, (imgCenter.shape[1] * 2, imgCenter.shape[0] * 2))

    OutImg = img
    OutImg[0:400, 0:400] = imgLeftUpCorner
    OutImg[0:400, 1520:1920] = imgRightUpCorner
    OutImg[680:1080, 0:400] = imgLeftDownCorner
    OutImg[680:1080, 1520:1920] = imgRightDownCorner
    OutImg[340:740, 760:1160] = imgCenter

    cv2.line(OutImg, (0, OutImg.shape[0] // 2), (OutImg.shape[1], OutImg.shape[0] // 2), (0, 255, 0), thickness=2)
    cv2.line(OutImg, (OutImg.shape[1] // 2, 0), (OutImg.shape[1] // 2, OutImg.shape[0]), (0, 255, 0), thickness=2)
    cv2.circle(OutImg, (OutImg.shape[1] // 2, OutImg.shape[0] // 2), 300, (0, 255, 0), thickness=2)
    cv2.imshow('FocusingHelper press "q" for quit', OutImg)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

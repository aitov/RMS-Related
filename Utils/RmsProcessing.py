from RMS.Formats.FTPdetectinfo import readFTPdetectinfo, findFTPdetectinfoFile
import RMS.Formats.FFfile as file
import cv2


def read_detected_meteors():
    folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0003_20231023_152622_865748"
    ftp_detect_file = findFTPdetectinfoFile(folder_path)
    meteor_list = readFTPdetectinfo(folder_path, ftp_detect_file)
    detected_meteors = get_detected_meteors(meteor_list)

    image_show = False
    try:
        for image in detected_meteors:
            img = file.read(folder_path, image).maxpixel
            cv2.imshow("Fit file", img)
            if not image_show:
                cv2.moveWindow("Fit file", 0, 0)
                image_show = True
            cv2.waitKey(0)
    except Exception as error:
        print("error:", error)


def get_detected_meteors(meteor_list):
    meteors = []
    for meteor in meteor_list:
        meteors.append(meteor[0])
    return meteors


read_detected_meteors()

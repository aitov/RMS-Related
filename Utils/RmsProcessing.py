from RMS.Formats.FTPdetectinfo import readFTPdetectinfo, findFTPdetectinfoFile
import RMS.Formats.FFfile as file
from RMS.Routines.CustomPyqtgraphClasses import *
import pyqtgraph as pg


class RmsProcessing(QtWidgets.QMainWindow):
    def __init__(self, input_path):
        super(RmsProcessing, self).__init__()
        self.input_path = input_path
        self.setupUI()

    def setupUI(self):
        self.central = QtWidgets.QWidget()


        layout = QtWidgets.QGridLayout()
        self.scroll = QtWidgets.QScrollArea()

        self.setCentralWidget(self.scroll)

        # Init the central image window



        # self.viewWidget.setCentralWidget(self.imgFrame)


        # layout.addWidget(self.scroll, 0, 1)

        # Add main image
        data = MeteorData()
        detectedMeteors = data.readDetectedMeteors()
        vbox = QtWidgets.QVBoxLayout()

        for image in detectedMeteors:
            viewWidget = pg.GraphicsView()
            imgFrame = ViewBox()
            viewWidget.setFixedHeight(720)
            viewWidget.setFixedWidth(1280)
            imgFrame.invertY()
            imgFrame.setAspectLocked()
            imgFrame.setMouseEnabled(False, False)
            imgFrame.setMenuEnabled(False)
            img = pg.ImageItem(self.loadImage(image))
            imgFrame.addItem(img, False)
            imgFrame.autoRange(padding=0)
            viewWidget.setCentralWidget(imgFrame)
            vbox.addWidget(viewWidget)
        self.central.setLayout(vbox)
        self.scroll.setWidget(self.central)


        self.setMinimumSize(1280, 720)
        self.showMaximized()

        self.show()

    def loadImage(self, imageName):


       # folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0003_20231023_152622_865748"
       folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20231109_145806_373961"

       return np.swapaxes(file.read(folder_path, imageName).maxpixel, 0, 1)

class MeteorData(object):
     def readDetectedMeteors(self):
        # folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0003_20231023_152622_865748"
        folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20231109_145806_373961"
        ftp_detect_file = findFTPdetectinfoFile(folder_path)
        meteor_list = readFTPdetectinfo(folder_path, ftp_detect_file)
        return self.getDetectedMeteors(meteor_list)


     def getDetectedMeteors(self, meteor_list):
        meteors = []
        for meteor in meteor_list:
            meteors.append(meteor[0])
        return meteors


# try:
#     for image in detected_meteors:
#         img = file.read(folder_path, image).maxpixel
#         cv2.imshow("Fit file", img)
#         if not image_show:
#             cv2.moveWindow("Fit file", 0, 0)
#             image_show = True
#         cv2.waitKey(0)
# except Exception as error:
#     print("error:", error)

if __name__ == '__main__':
    ### COMMAND LINE ARGUMENTS

    # Init the command line arguments parser
    # arg_parser = argparse.ArgumentParser(description="Tool for fitting astrometry plates and photometric calibration.")

    # arg_parser.add_argument('input_path', metavar='INPUT_PATH', type=str,
    #                         help='Path to the folder with FF or image files, path to a video file, or to a state file.'
    #                              ' If images or videos are given, their names must be in the format: YYYYMMDD_hhmmss.uuuuuu')


    # Parse the command line arguments
    # cml_args = arg_parser.parse_args()

    #########################

    app = QtWidgets.QApplication(sys.argv)

    # Init SkyFit
    input_path = ""
    plate_tool = RmsProcessing(input_path)


    # Run the GUI app
    sys.exit(app.exec_())

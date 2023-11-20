from RMS.Formats.FTPdetectinfo import readFTPdetectinfo, findFTPdetectinfoFile
import RMS.Formats.FFfile as file
from RMS.Routines.CustomPyqtgraphClasses import *
import pyqtgraph as pg
from PyQt5.QtCore import *
import os, datetime


class RmsProcessing(QtWidgets.QMainWindow):

    def __init__(self, input_path):
        super(RmsProcessing, self).__init__()
        self.input_path = input_path
        self.detectedCheckBoxes = {}
        self.toStackCheckBoxes = {}
        self.setupUI()

    def setupUI(self):
        vbox = QtWidgets.QVBoxLayout()
        central = QtWidgets.QWidget()
        central.setLayout(vbox)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

        data = MeteorData()
        detectedMeteors = data.readDetectedMeteors()

        # vbox.setAlignment(Qt.AlignRight)
        for meteorData in detectedMeteors:
            self.addImage(meteorData, vbox)

        self.setMinimumSize(1280, 720)
        self.showMaximized()
        self.show()

    def loadImage(self, imageName):
        folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0003_20231023_152622_865748"
        # folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20231109_145806_373961"

        return np.swapaxes(file.read(folder_path, imageName).maxpixel, 0, 1)

    def addImage(self, meteorData, layout):
        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.addStretch()
        horizontalLayout.addLayout(self.createCheckBoxesView(meteorData, True, True))
        viewWidget = pg.GraphicsView()
        viewWidget.setFixedHeight(720)
        viewWidget.setFixedWidth(1280)
        # create image view
        viewWidget.setCentralWidget(self.createImageView(meteorData.fileName))
        horizontalLayout.addWidget(viewWidget)
        horizontalLayout.addStretch()
        horizontalLayout.setAlignment(Qt.AlignCenter)

        layout.addLayout(horizontalLayout)

    def addTimestampToImage(self, imgFrame, imageName):
        label = pg.TextItem(color=(255, 255, 255))
        label.setFont(QtGui.QFont('monospace', 8))
        label.setTextWidth(200)
        label.setZValue(1000)
        label.setText(self.getTimestampTitle(imageName))
        label.setParentItem(imgFrame)
        label.setPos(0, 720 - label.boundingRect().height())

    def createImageView(self, imageName):
        imageView = ViewBox()
        imageView.invertY()
        imageView.setMouseEnabled(False, False)
        img = pg.ImageItem(self.loadImage(imageName))
        imageView.addItem(img, False)
        imageView.autoRange(padding=0)
        # add timestamp to image
        self.addTimestampToImage(imageView, imageName)
        return imageView

    def createCheckBoxesView(self, meteorData, detected, addToStack):
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.addStretch()
        detectedCheckBox = QtWidgets.QCheckBox("Detected")
        detectedCheckBox.setChecked(detected)
        detectedCheckBox.meteorId = meteorData.fileName + "_" + str(meteorData.meteorNumber)
        self.detectedCheckBoxes[detectedCheckBox.meteorId] = detectedCheckBox
        detectedCheckBox.toggled.connect(self.onDetectedClicked)
        verticalLayout.addWidget(detectedCheckBox)

        addToStackCheckBox = QtWidgets.QCheckBox("Add to stack")
        addToStackCheckBox.setChecked(addToStack)
        self.toStackCheckBoxes[detectedCheckBox.meteorId] = addToStackCheckBox
        verticalLayout.addWidget(addToStackCheckBox)
        verticalLayout.addStretch()
        return verticalLayout


    def getTimestampTitle(self, fr_path):
        _, fname = os.path.split(fr_path)
        splits = fname.split('_')
        dtstr = splits[2] + '_' + splits[3] + '.' + splits[4]
        imgdt = datetime.datetime.strptime(dtstr, '%Y%m%d_%H%M%S.%f')
        return splits[1] + ' ' + imgdt.strftime('%Y-%m-%d %H:%M:%S UTC')

    def onDetectedClicked(self):
        detectedCheckBox = self.sender()
        self.toStackCheckBoxes[detectedCheckBox.meteorId].setChecked(detectedCheckBox.isChecked())

class MeteorData(object):
    def __init__(self, fileName=None, meteorNumber=None):
        self.fileName = fileName
        self.meteorNumber = meteorNumber

    def readDetectedMeteors(self):
        folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0003_20231023_152622_865748"
        # folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20231109_145806_373961"
        ftp_detect_file = findFTPdetectinfoFile(folder_path)
        meteor_list = readFTPdetectinfo(folder_path, ftp_detect_file)
        return self.getDetectedMeteors(meteor_list)

    def getDetectedMeteors(self, meteor_list):
        meteors = []
        for meteor in meteor_list:
            meteors.append(MeteorData(meteor[0], meteor[2]))
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

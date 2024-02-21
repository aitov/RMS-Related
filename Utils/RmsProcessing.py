from RMS.Formats.FTPdetectinfo import readFTPdetectinfo, findFTPdetectinfoFile
import RMS.Formats.FFfile as file
from RMS.Routines.CustomPyqtgraphClasses import *
from RMS.Formats import FFfile
from Utils.ShowerAssociation import showerAssociation
import RMS.ConfigReader as cr
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
        self.initMenuAndStatusBar()
        vbox = QtWidgets.QVBoxLayout()
        central = QtWidgets.QWidget()
        central.setLayout(vbox)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

        data = MeteorData()
        detectedMeteors = data.readDetectedMeteors()
        self.detectedCount = len(detectedMeteors)
        self.detectedTotal = self.detectedCount
        # vbox.setAlignment(Qt.AlignRight)
        for meteorData in detectedMeteors:
            self.addImage(meteorData, vbox)
        self.updateStatus()
        self.setMinimumSize(1450, 800)
        self.showMaximized()
        self.show()

    def initMenuAndStatusBar(self):

        menuBar = self.menuBar()
        # menuBar.setNativeMenuBar(False)
        fileMenu = menuBar.addMenu("File")
        fileMenu.addAction("Open")
        fileMenu.addAction("Save")
        menuBar.show()
        self.statusBar = QtWidgets.QStatusBar()
        finishButton = QtWidgets.QPushButton("Finish Detection")
        finishButton.clicked.connect(self.onFinishDetectonClick)
        self.statusBar.addPermanentWidget(finishButton)
        self.setStatusBar(self.statusBar)


    def loadImage(self, imageName):
        folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20240108_145148_433498"
        # folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20231109_145806_373961"

        return np.swapaxes(file.read(folder_path, imageName).maxpixel, 0, 1)

    def addImage(self, meteorData, layout):
        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.addStretch()
        horizontalLayout.addLayout(self.createCheckBoxesView(meteorData, True))
        viewWidget = pg.GraphicsView()
        viewWidget.setFixedHeight(720)
        viewWidget.setFixedWidth(1280)
        # create image view
        viewWidget.setCentralWidget(self.createImageView(meteorData))
        horizontalLayout.addWidget(viewWidget)
        horizontalLayout.addStretch()
        horizontalLayout.setAlignment(Qt.AlignCenter)

        layout.addLayout(horizontalLayout)

    def addTimestampToImage(self, imgFrame, meteorData):
        label = pg.TextItem(color=(255, 255, 255))
        label.setFont(QtGui.QFont('monospace', 8))
        label.setTextWidth(200)
        label.setZValue(1000)
        label.setText("{:d} - {:s}".format(int(meteorData.meteorNumber), self.getTimestampTitle(meteorData.fileName)))
        label.setParentItem(imgFrame)
        label.setPos(0, 720 - label.boundingRect().height())

    def addShowerNameToImage(self, imgFrame, showerName):
        label = pg.TextItem(color=(255, 255, 255))
        label.setFont(QtGui.QFont('monospace', 8))
        label.setTextWidth(200)
        label.setZValue(1000)
        label.setText("Meteor shower : {:s}".format(showerName))
        label.setParentItem(imgFrame)
        label.setPos(165, 720 - label.boundingRect().height())

    def createImageView(self, meteorData):
        imageView = ViewBox()
        imageView.invertY()
        imageView.setMouseEnabled(False, False)
        img = pg.ImageItem(self.loadImage(meteorData.fileName))
        imageView.addItem(img, False)
        imageView.autoRange(padding=0)
        # add timestamp to image
        self.addTimestampToImage(imageView, meteorData)
        self.addShowerNameToImage(imageView, meteorData.showerName)
        return imageView

    def createCheckBoxesView(self, meteorData, addToStack):
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.addStretch()
        detectedCheckBox = QtWidgets.QCheckBox("Detected")
        detectedCheckBox.setChecked(meteorData.showerName != "Unknown")
        detectedCheckBox.meteorId = meteorData.fileName + "_" + str(meteorData.meteorNumber)
        self.detectedCheckBoxes[detectedCheckBox.meteorId] = detectedCheckBox
        detectedCheckBox.toggled.connect(self.onDetectedClick)
        verticalLayout.addWidget(detectedCheckBox)

        addToStackCheckBox = QtWidgets.QCheckBox("Add to stack")
        addToStackCheckBox.setChecked(addToStack)
        self.toStackCheckBoxes[detectedCheckBox.meteorId] = addToStackCheckBox
        verticalLayout.addWidget(addToStackCheckBox)
        verticalLayout.addStretch()
        return verticalLayout


    def getTimestampTitle(self, ff_path):
        fileName = os.path.basename(ff_path)
        stationName = fileName.split('_')[1]
        timestampt = FFfile.filenameToDatetime(fileName)
        return stationName + ' ' + timestampt.strftime('%Y-%m-%d %H:%M:%S UTC')

    def onDetectedClick(self):
        detectedCheckBox = self.sender()
        if detectedCheckBox.isChecked():
            self.detectedCount += 1
        else:
            self.detectedCount -= 1
        self.toStackCheckBoxes[detectedCheckBox.meteorId].setChecked(detectedCheckBox.isChecked())
        self.updateStatus()


    def onFinishDetectonClick(self):
        self.close()

    def updateStatus(self):
        self.statusBar.showMessage("Detected meteors: {}/{}".format(self.detectedCount, self.detectedTotal))

class MeteorData(object):
    def __init__(self, fileName=None, meteorNumber=None, showerName=None):
        self.fileName = fileName
        self.meteorNumber = meteorNumber
        self.showerName = showerName

    def readDetectedMeteors(self):
        folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20240108_145148_433498"
        # folder_path = "/Users/alexaitov/home/pi/RMS_data/ArchivedFiles/UA0004_20231109_145806_373961"
        config = cr.loadConfigFromDirectory([folder_path + "/.config"], 'notused')
        ftp_detect_file = findFTPdetectinfoFile(folder_path)
        meteor_list = readFTPdetectinfo(folder_path, ftp_detect_file)
        associations_per_dir, _ = showerAssociation(config, [ftp_detect_file],
                                                    shower_code=None, show_plot=False, save_plot=False, plot_activity=False)
        associations = {}
        associations.update(associations_per_dir)
        return self.getDetectedMeteors(meteor_list, associations)

    def getDetectedMeteors(self, meteor_list, associations):
        meteors = []
        for meteor in meteor_list:
            showerName = self.getMeteorShowerTitle(meteor[0], meteor[2], associations)
            meteors.append(MeteorData(meteor[0], meteor[2], showerName))
        return meteors

    def getMeteorShowerTitle(self, ffFile, meteorNumber, associations):
        title = "Unknown"
        # get all available meteors for current FF file

        # search first suitable by time range
        if (ffFile, meteorNumber) in associations:
            shower = associations[(ffFile, meteorNumber)][1]
            if shower is not None:
                title = "[{:s}] - {:s}".format(shower.name, shower.name_full)
            else:
                title = "Sporadic"

        return title


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

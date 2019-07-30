import sys
import os
SVFHOME = os.environ['SVFHOME']
CACHEDIR = SVFHOME + "Cache\\"
HTTPADDRESS = "http://127.0.0.1:8000/"
GSV_API_URL = "https://maps.googleapis.com/maps/api/streetview"
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication
# use the QtWebEngineWidgets
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import QProcess
from PyQt5.QtWebChannel import *
import time
import datetime

# Import Pillow:
from PIL import Image
from io import StringIO
from io import BytesIO
#import numpy as np
#from math import *
import requests
#import scipy
import argparse
import math
import time
#import cv2
#import caffe
import shapefile
import shutil
from shutil import copyfile
import json

class Config():
    apikey = ""
    lat = 40.721441
    lon = -73.994535
    cuda = True
    GoogleMapsHtmlContent = ""
    GoogleStreetViewHtmlContent = ""

    def __init__(self):
        configFile = SVFHOME + "Config.csv"
        if os.path.exists(configFile) == False:
           try:
             file = open(configFile,"w") 
             file.write("APIkey," + "\n")
             file.write("Lat,42.345573" + "\n")
             file.write("Lon,-71.098326" + "\n")
             file.write("CUDA,1" + "\n")
             file.close() 
           except Exception as err:
             print(str(err)) 
        else:
           try:
             file = open(configFile,"r") 
             lines = file.readlines()
             file.close()
             newPointSet = []
             for line in lines:
                 splits = line.split(",")
                 if len(splits) < 2:
                    continue
                 configName = splits[0].strip().lower()
                 self.cuda = True
                 if configName == "apikey":
                    self.apikey = splits[1].strip()
                 elif configName == "lat":
                    self.lat = splits[1].strip()
                 elif configName == "lon":
                    self.lon = splits[1].strip()
                 elif configName == "cuda" and int(splits[1].strip()) == 0:
                    self.cuda = False
           except Exception as err:
             print(str(err)) 

    def loadHtmls(self):
        with open(SVFHOME + "GoogleMaps.html", 'r') as content_file:
             self.GoogleMapsHtmlContent = content_file.read()
             self.GoogleMapsHtmlContent = self.GoogleMapsHtmlContent.replace("YOUR_API_KEY", self.apikey)

        with open(SVFHOME + "GoogleStreetView.html", 'r') as content_file:
             self.GoogleStreetViewHtmlContent = content_file.read()
             self.GoogleStreetViewHtmlContent = self.GoogleStreetViewHtmlContent.replace("YOUR_API_KEY", self.apikey)
        #print(self.APIKEY)

class LatLon():
    lat = 0.0
    lon = 0.0

MyConfig = Config()
CurLatLon =  LatLon()
EARTH_CIRCUMFERENCE = 6378137
PanoramaSamples = []
PanoramaJobs = []

class Panorama():
    def __init__(self):
        self.id = "0"
        self.panoid = ""
        self.lon = ""
        self.lat = ""
        self.date = ""
        self.svf = -1.0
        self.tvf = -1.0
        self.bvf = -1.0
        self.initialized = False

    def fromJSON(self,str):
        try:
            root = json.loads(str)
            if root['status'] != "OK":
                return False
            location = root['location']
            self.date = root['date']
            self.panoid = root['pano_id']
            self.lat = location['lat']
            self.lon = location['lng']
            self.initialized = True
            return True
        except ValueError:
            return False
        return False

    def fromPano(self,pano):
        self.id = pano.id
        self.panoid = pano.panoid
        self.lon = pano.lon
        self.lat = pano.lat
        self.date = pano.date
        self.svf = pano.svf
        self.tvf = pano.tvf
        self.bvf = pano.bvf
        self.initialized = pano.initialized

    def fromLocation(self,lat,lon):
        url= GSV_API_URL + "/metadata?location=" + str(lat) + "," + str(lon) +"&key="+ MyConfig.apikey
        #print(url)
        try:
            response = requests.get(url)
            if response.status_code == requests.codes.ok:
              return self.fromJSON(response.content)
        except ValueError:
            return False
        return False

    def write(self,filename):
        file = open(filename,"w") 
        file.write(str(self.id) + "," + self.panoid + "," + self.date  + "," + str(self.lat) + "," + str(self.lon) + "," + str(self.svf) + "," + str(self.tvf) + "," + str(self.bvf))
        file.close() 

    def read(self,filename):
        file = open(filename,"r") 
        splits = file.readline().split(",")
        self.id = splits[0]
        self.panoid = splits[1]
        self.date = splits[2]
        self.lat = float(splits[3])
        self.lon = float(splits[4])
        self.svf = float(splits[5])
        self.tvf = float(splits[6])
        self.bvf = float(splits[7])
        file.close() 
        self.initialized = True

    def fromline(self,line):
        splits = line.split(",")
        if len(splits) < 7:
            return False
        if splits[1] == "" or  splits[3] == "" or  splits[4] == "":
            return False
        self.id = splits[0]
        self.panoid = splits[1]
        self.date = splits[2]
        self.lat = float(splits[3])
        self.lon = float(splits[4])
        self.svf = float(splits[5])
        self.tvf = float(splits[6])
        self.bvf = float(splits[7])
        self.initialized = True
        return True
    def toString(self):
        return str(self.id) + "," + self.panoid + "," + self.date  + "," + str(self.lat) + "," + str(self.lon) + "," + str(self.svf) + "," + str(self.tvf) + "," + str(self.bvf)

class PanoramaJob():
    def __init__(self):
        self.jobid = ""
        self.panoramas = []

    def loadJob(self,dir):
        self.jobid = QDir(dir).dirName()
        alldirs = os.listdir(dir)
        for subdirname in alldirs:
            panofolder = dir + subdirname + "/"
            if os.path.exists(panofolder + "panoinfo.txt") == False:
               continue
            #print(panofolder + "panoinfo.txt")
            pano = Panorama()
            pano.read(panofolder + "panoinfo.txt")
            self.panoramas.append(pano)
            if subdirname != pano.panoid and os.path.exists(dir + pano.panoid + "/panoinfo.txt"):
               QDir.removeRecursively(QDir(dir + pano.panoid))
            if subdirname != pano.panoid:
               os.rename(dir + subdirname,dir + pano.panoid)

class BrowserChannel(QtCore.QObject):
    @QtCore.pyqtSlot(str)
    def loadCache(self, arg):
        self.Browser.loadCache(arg)

    @QtCore.pyqtSlot(str)
    def leftClick(self, arg):
        self.Browser.leftClick(arg)

    @QtCore.pyqtSlot(str)
    def rightClick(self, arg):
        self.Browser.rightClick(arg)
  
    @QtCore.pyqtSlot(str)
    def dblclick(self, arg):
        self.Browser.dblclick(arg)

class Browser(QMainWindow):
    EARTH_CIRCUMFERENCE = 6378137     # earth circumference in meters
    ICON_SIZE = 64
    LAST_DIRECTORY = '/'

    def checkDir(self, dir):
      if (dir.endswith('/') or dir.endswith('\\')) == False:
         dir = dir + '/'
      return dir

    def great_circle_distance(self, lat1, lon1,lat2, lon2): # doctest: +ELLIPSIS
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
                math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                math.sin(dLon / 2) * math.sin(dLon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = EARTH_CIRCUMFERENCE * c
        return d

    def createBTN(self, maxsize,name):
        btn = QPushButton()
        btn.setText(name)
        btn.setMaximumWidth(self.ICON_SIZE);
        btn.setMaximumHeight(self.ICON_SIZE);
        return btn

    def createLabel(self, maxsize,name):
        label = QLabel()
        label.setMaximumWidth(maxsize);
        label.setText(name)
        label.setMaximumHeight(self.ICON_SIZE);
        return label

    def loadUI(self):
        self.resize(1024,768)
        self.centralwidget = QWidget(self)

        self.mainLayout = QVBoxLayout(self.centralwidget)
        self.mainLayout.setSpacing(0)
       
        self.horizontalLayout = QGridLayout()

        self.horizontalLayout.setAlignment(Qt.AlignLeft);
        self.coords_line = QLineEdit()
        self.coords_line.setMaximumWidth(250);
        self.coords_line.setMaximumHeight(self.ICON_SIZE);
        self.coords_line.setToolTip("Update coordinates in the textbox by entering in the format of \"lat,lon\" or by right-click on the map.")

        self.bt_add = self.createBTN(32,"")
        self.bt_add.setToolTip('Add a sample point at the coordinates from the textbox')
        self.bt_add.clicked.connect(self.addPointFromTextBox)
        self.bt_add.setIcon(QIcon(SVFHOME + "Icons/Add.png"))

        self.bt_pick = self.createBTN(32,"")
        self.bt_pick.setCheckable(True);
        self.bt_pick.setChecked(False);
        self.bt_pick.setIcon(QIcon(SVFHOME + "Icons/pick.png"))
        QToolTip.setFont(QFont('SansSerif', 10))
        #self.setToolTip('Enter picking mode to interactively gather sample points')
        self.bt_pick.setToolTip('Enter picking mode to interactively gather sample points.')
      

        self.bt_interpolate = self.createBTN(32,"")
        self.bt_interpolate.setCheckable(True);
        self.bt_interpolate.setChecked(False)
        self.bt_interpolate.setToolTip('Interpolate between two sample points.')
        self.bt_interpolate.setIcon(QIcon(SVFHOME + "Icons/Interpolate.png"))

        self.bt_zoom = self.createBTN(32,"")
        self.bt_zoom.setToolTip('Zoom to the given coordinates.')
        self.bt_zoom.setIcon(QIcon(SVFHOME + "Icons/Zoom.png"))

        self.bt_remove = self.createBTN(32,"")
        self.bt_remove.setToolTip('Remove the last sample point.')
        self.bt_remove.setIcon(QIcon(SVFHOME + "Icons/Remove.png"))

        self.bt_removeAll = self.createBTN(32,"")
        self.bt_removeAll.setToolTip('Remove all sample points.')
        self.bt_removeAll.setIcon(QIcon(SVFHOME + "Icons/RemoveAll.png"))

        self.bt_searchradius =  QSpinBox();
        self.bt_searchradius.setMaximumWidth(75);
        self.bt_searchradius.setMaximumHeight(self.ICON_SIZE);
        self.bt_searchradius.setRange(5, 10000);
        self.bt_searchradius.setSingleStep(5);
        self.bt_searchradius.setValue(10);
        self.bt_searchradius.setToolTip('The radius parameter for GSV search query')

        self.bt_loadshapefile = self.createBTN(32,"")
        self.bt_loadshapefile.setToolTip('Load sample points from a ESRI Shapefile (needs to be in WGS84 geographic coordinates and will be treated as points).')
        self.bt_loadshapefile.setIcon(QIcon(SVFHOME + "Icons/LoadShapeFile.png"))

        self.bt_saveToNewFolder = QCheckBox("name folder?",self)
        self.bt_saveToNewFolder.setMaximumWidth(150);
        self.bt_saveToNewFolder.setMaximumHeight(self.ICON_SIZE);
        self.bt_saveToNewFolder.setToolTip('specify output folder name.')

        self.bt_compute = self.createBTN(32,"")
        self.bt_compute.setToolTip('Compute SVF for the collection of sample points.')
        self.bt_compute.setIcon(QIcon(SVFHOME + "Icons/Compute.png"))


        self.bt_rectSel = self.createBTN(32,"")
        self.bt_rectSel.setToolTip('Select sample points by dragging a rectangle.')
        self.bt_rectSel.setCheckable(True);
        self.bt_rectSel.setChecked(False)
        self.bt_rectSel.setIcon(QIcon(SVFHOME + "Icons/Select.png"))


        self.bt_export = self.createBTN(32,"")
        self.bt_export.setToolTip('Export the selected sample points.')
        self.bt_export.setIcon(QIcon(SVFHOME + "Icons/Export.png"))


        self.bt_sampledist =  QSpinBox();
        self.bt_sampledist.setMaximumWidth(75);
        self.bt_sampledist.setMaximumHeight(self.ICON_SIZE);
        self.bt_sampledist.setRange(5, 1000);
        self.bt_sampledist.setSingleStep(5);
        self.bt_sampledist.setValue(5);
        self.bt_sampledist.setToolTip('Set the sampling interval (in meters) for interpolating between two sample points')

        self.bt_loadshapefile.clicked.connect(self.loadShapeFile)
        self.bt_zoom.clicked.connect(self.zoom)
        self.bt_removeAll.clicked.connect(self.removeAllPoints)
        self.bt_remove.clicked.connect(self.removePoint)
        self.bt_compute.clicked.connect(self.compute)
        self.bt_rectSel.clicked.connect(self.select)
        self.bt_export.clicked.connect(self.export)

        pos = 0
        self.horizontalLayout.addWidget(self.coords_line,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_loadshapefile,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_add,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_pick,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_interpolate,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_sampledist,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_zoom,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_remove,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_removeAll,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_searchradius,0,pos)
        pos = pos + 1  
        self.horizontalLayout.addWidget(self.bt_compute,0,pos)
        pos = pos + 1  
        self.horizontalLayout.addWidget(self.bt_saveToNewFolder,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_rectSel,0,pos)
        pos = pos + 1
        self.horizontalLayout.addWidget(self.bt_export,0,pos)
        pos = pos + 1  
        self.mainLayout.addLayout(self.horizontalLayout)

        self.GoogleMapsView = QWebEngineView()
        self.GoogleMapsView.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True);
        self.GoogleMapsView.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls,True)
        self.GoogleStreetView = QWebEngineView()
        self.GoogleStreetView.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True);
        self.GoogleStreetView.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls,True)
        splitter1 = QSplitter()


        #self.horizontalLayoutLower = QGridLayout()
        #listWidget = QListWidget()
       # listWidget.setMinimumSize(1,1)
        #splitter1.addWidget(listWidget)

        splitter2 = QSplitter()
        splitter2.setOrientation(Qt.Vertical);
        splitter2.addWidget(self.GoogleMapsView)
        splitter2.addWidget(self.GoogleStreetView)
        splitter2.setStretchFactor(1, 20);
        splitter2.setStretchFactor(0, 80);
        #splitter1.addWidget(splitter2)
       # splitter1.setStretchFactor(0, 20);
        #splitter1.setStretchFactor(1, 80);
        #self.horizontalLayoutLower.addWidget(listWidget,0,0,1,1)
        #self.horizontalLayoutLower.addWidget(self.GoogleMapsView,0,1,1,6)

        self.mainLayout.addWidget(splitter2)

        self.setCentralWidget(self.centralwidget)
        extractAction = QAction("&GET TO THE CHOPPAH!!!", self)
        extractAction.setShortcut("Ctrl+Q")
        extractAction.setStatusTip('Leave The App')
        #extractAction.triggered.connect(self.close_application)
        #mainMenu = self.menuBar()
        #fileMenu = mainMenu.addMenu('&File')
        #fileMenu.addAction(extractAction)

        #self.default_url = "file:///" + SVFHOME + "GoogleMaps.html"
        #self.GoogleMapsView.load(QtCore.QUrl(self.default_url))
        #self.GoogleStreetView.load(QtCore.QUrl("file:///" + SVFHOME + "GoogleStreetView.html"))
        #self.GoogleMapsView.load(QtCore.QUrl("file:///" + SVFHOME + "test.html"))

        MyConfig.loadHtmls()
        self.GoogleMapsView.setHtml(MyConfig.GoogleMapsHtmlContent)
        self.GoogleStreetView.setHtml(MyConfig.GoogleStreetViewHtmlContent)
        #print(MyConfig.GoogleMapsHtmlContent)
        #print(MyConfig.GoogleStreetViewHtmlContent)

    def setupWebChannel(self):
        self.browserChannel = BrowserChannel()
        self.browserChannel.Browser = self
        self.webChannel = QWebChannel(self.GoogleMapsView.page());
        self.webChannel.registerObject('mainWin', self.browserChannel);
        self.GoogleMapsView.page().setWebChannel(self.webChannel);

    def enableUI(self, enabled):
        self.coords_line.setEnabled(enabled)
        self.bt_add.setEnabled(enabled)
        self.bt_compute.setEnabled(enabled)
        self.bt_interpolate.setEnabled(enabled)
        self.bt_pick.setEnabled(enabled)
        self.bt_export.setEnabled(enabled)
        self.bt_loadshapefile.setEnabled(enabled)
        self.bt_rectSel.setEnabled(enabled)
        self.bt_saveToNewFolder.setEnabled(enabled)
        self.bt_searchradius.setEnabled(enabled)
        self.bt_zoom.setEnabled(enabled)
        self.bt_remove.setEnabled(enabled)
        self.bt_removeAll.setEnabled(enabled)
        self.isEnabled = enabled

    def readClassiferOutput(self):
        output = str(self.classifier.readAllStandardOutput(), encoding = 'utf-8').strip()
        if output == "task.finished" or output == "task.failed":
            self.finishedTasks = self.finishedTasks + 1
        if self.finishedTasks >= self.pendingTasks:
            self.finishComputeTasks()
            self.enableUI(True)
            self.pendingTasks = 0
            self.finishedTasks = 0
        else:
          return

    def startClassifierProcess(self):
        self.pendingTasks = 0
        self.finishedTasks = 0
        self.taskdir = ""
        self.isEnabled = False
        command = SVFHOME + "RunSVFCore.bat"
        args =  {""}
        self.classifier = QProcess()
        self.classifier.readyRead.connect(self.readClassiferOutput)
        self.classifier.start(command, args, QIODevice.ReadWrite)
        self.classifier.setReadChannel(QProcess.StandardOutput)
        self.classifier.waitForReadyRead()
        self.classifier.waitForStarted()

    def startHttpServerProcess(self):
        command = SVFHOME + "StartHttpServer.bat"
        args =  {""}
        self.httpserver = QProcess()
        self.httpserver.start(command, args, QIODevice.ReadWrite)
        self.httpserver.waitForStarted()
        
    def initialize(self):
        self.setupWebChannel()
        self.startClassifierProcess()
        self.startHttpServerProcess()

    def __init__(self):
        QMainWindow.__init__(self)
        self.loadUI()

    def addPointFromTextBox(self):
        try:
          coorstr = self.coords_line.text();
          if coorstr == "":
             return
          splits = coorstr.split(",")
          if len(splits) < 2:
             return
          lat = float(str(splits[0]).strip())
          lon = float(str(splits[1]).strip())
          success = self.addPoint(lat,lon)
        except Exception as err:
          print(str(err) + "\n")

    def loadShapeFile(self):
        try:
          infile = QFileDialog.getOpenFileName(self, 'Open ESRI Shapefile', self.LAST_DIRECTORY,"ESRI Shapefile (*.shp)")
          #print(infile[0])
          if not infile:
             return
          sf = shapefile.Reader(infile[0])
          shapes = sf.shapes()
          numshapes = len(shapes)
          fid = 0
          newPointSet = []
          sumlon = 0.0
          sumlat = 0.0
          fileout = open(infile[0] +  ".csv","w") 
          fileout.write("id,panoid,date,lat,lon,svf\n") 
          for nshape in range(0,numshapes):
              numpoints = len(shapes[nshape].points)
              for npoint in range(0,numpoints):
                  point = shapes[nshape].points[npoint]
                  newSample = Panorama();
                  try:
                      newSample.fromLocation(point[1],point[0])
                      newSample.id = fid
                      newPointSet.append(newSample)
                      self.GoogleMapsView.page().runJavaScript("addMarker ({0},{1})".format(str(newSample.lat),str(newSample.lon)))
                      sumlat = sumlat + point[1]
                      sumlon = sumlon + point[0]
                      fileout.write(newSample.toString() + "\n") 
                      #print(str(fid) + ":" + newSample.panoid + "," + str(point[0]) + "," + str(point[1]))
                      fid = fid + 1
                  except: 
                      print("error")
          fileout.close() 
          PanoramaSamples.append(newPointSet)
          self.GoogleMapsView.page().runJavaScript("addPoint()")
          centerlon = sumlon / float(fid)
          centerlat = sumlat / float(fid)
          #print("Finished ({0},{1})".format(centerlat, centerlon))
          self.GoogleMapsView.page().runJavaScript("zoom({0},{1})".format(centerlat,centerlon))
        except Exception as err:
          print(str(err) + "\n")

    def loadCSVFile(self,infile):
        try:
          fs = open(infile,"r") 
          lines = fs.readlines()
          fs.close()
          firstLine = lines.pop(0) #removes the first line
          newPointSet = []
          for line in lines:
              pano = Panorama()
              pano.fromline(line)
              if pano.initialized == False:
                  continue
              newPointSet.append(pano)
          PanoramaSamples.append(newPointSet)
        except Exception as err:
          print(str(err) + "\n")

    def select(self):
        try:
          self.GoogleMapsView.page().runJavaScript("select()")
        except Exception as err:
          print(str(err) + "\n")

    def copyPanoDir(self,indir,outdir):
        try:
          if not os.path.exists(outdir):
             os.mkdir(outdir) 
          copyfile(indir+'mosaic.png',         outdir+'mosaic.png')
          copyfile(indir+'mosaic_classified.png',         outdir+'mosaic_classified.png')
          copyfile(indir+'fisheye.png',        outdir+'fisheye.png')
          copyfile(indir+'fisheye_classified.png', outdir+'fisheye_classified.png')
          copyfile(indir+'panoinfo.txt',       outdir+'panoinfo.txt')
        except Exception as err:
          print(str(err) + "\n")

    def export(self):
        try:
          self.GoogleMapsView.page().runJavaScript("getSelectionBound()", self.readyToExport)
        except Exception as err:
          print(str(err) + "\n")

    def readyToExport(self, selectionBound):
        try:
          if selectionBound == "":
              return
          splits = selectionBound.split(",")
          if len(splits) < 4:
              return
          outdir = QFileDialog.getExistingDirectory(self, 'Open Folder', self.LAST_DIRECTORY,QFileDialog.ShowDirsOnly)
          if not outdir:
              return
          foldername = QDir(outdir).dirName()
          self.LAST_DIRECTORY = outdir
          outdir = outdir + "\\"
          minLat = float(splits[0])
          minLon = float(splits[1])
          maxLat = float(splits[2])
          maxLon = float(splits[3])
          shp = shapefile.Writer(outdir + foldername, shapefile.POINT)
          shp.autoBalance = 1
          # create the field names and data type for each.
          shp.field("jobid", "C")
          shp.field("id", "N", decimal=15)
          shp.field("panoid", "C")
          shp.field("date", "C")
          shp.field("lat", 'N', decimal=15)
          shp.field("lon",  'N', decimal=15)
          shp.field("svf",  'N', decimal=10)
          fileout = open(outdir +  foldername + ".csv","w") 
          fileout.write("jobid,id,panoid,date,lat,lon,svf\n") 
          for i in range(0,len(PanoramaJobs)):
              newJob = PanoramaJob()
              job = PanoramaJobs[i] 
              newJob.jobid = job.jobid
              jobid = str(newJob.jobid)
              injobdir = CACHEDIR + jobid + "\\"
              outjobdir = outdir + jobid + "\\"
              #print(outjobdir)
              sel = []
              for n in range(0,len(job.panoramas)):
                  pano = job.panoramas[n]
                  #print(str(n) + "," + str(len(job.panoramas)))
                  if pano.lon > maxLon or pano.lat > maxLat or pano.lon < minLon or pano.lat < minLat:
                      continue
                  shp.point(pano.lon,pano.lat)
                  shp.record(jobid, int(pano.id), pano.panoid, pano.date, pano.lat, pano.lon, pano.svf)
                  fileout.write(jobid + "," + pano.toString() + "\n") 
                  if not os.path.exists(outjobdir):
                      os.makedirs(outjobdir) 
                  self.copyPanoDir(injobdir + str(pano.panoid) + "\\", outjobdir + str(pano.panoid) + "\\")       
          fileout.close() 
        except Exception as err:
          print(str(err) + "\n")

    def removePoint(self):
        try:
          if len(PanoramaSamples) == 0:
             return
          numpoints = len(PanoramaSamples[len(PanoramaSamples)-1])
          self.GoogleMapsView.page().runJavaScript("removeSamplePoints({0})".format(numpoints))
          PanoramaSamples.pop()
        except Exception as err:
          print(str(err) + "\n")

    def removeAllPoints(self):
        try:
          while len(PanoramaSamples) > 0:
                numpoints = len(PanoramaSamples[len(PanoramaSamples)-1])
                #self.GoogleMapsView.page().runJavaScript("removeSamplePoints({0})".format(numpoints))
                PanoramaSamples.pop()
          self.GoogleMapsView.page().runJavaScript("clear()")
        except Exception as err:
          print(str(err) + "\n")

    def zoom(self):
        try:
          coorstr = self.coords_line.text();
          if coorstr == "":
             return
          splits = coorstr.split(",")
          if len(splits) < 2:
             return
          lat = float(str(splits[0]).strip())
          lon = float(str(splits[1]).strip())
          self.GoogleMapsView.page().runJavaScript("zoom({0},{1})".format(lat,lon))
        except Exception as err:
          print(str(err) + "\n")

    @QtCore.pyqtSlot(str)
    def loadCache(self, arg):
        try:
          dirs = os.listdir(CACHEDIR)
          for foldername in dirs:
              outdir = CACHEDIR + foldername + "\\"
              print(outdir)
              job = PanoramaJob()
              job.loadJob(outdir)
              PanoramaJobs.append(job)
              for pano in job.panoramas:
                  httpdir = HTTPADDRESS + foldername + "/" + pano.panoid + "/"
                  fisheyefile = httpdir + "fisheye.png"
                  fisheyefile = fisheyefile.replace('\\','/')
                  classifiedfisheyefile = httpdir + "fisheye_classified.png"
                  classifiedfisheyefile = classifiedfisheyefile.replace('\\','/')

                  self.GoogleMapsView.page().runJavaScript("setMarker({0},{1},{2},\"{3}\",\"{4}\",{5},{6})".format(pano.svf,pano.tvf,pano.bvf,fisheyefile,classifiedfisheyefile, pano.lat,pano.lon))
        except Exception as err:
          print(str(err) + "\n")

    def startComputeTasks(self, outdir):
        try:
          outdir = self.checkDir(outdir)
          if not os.path.exists(outdir):
             os.makedirs(outdir)
          taskFile = outdir + "task.csv"
          tasks = []
          for i in range(0, len(PanoramaSamples)):
              sample = PanoramaSamples[i]
              for j in range(0, len(sample)):
                  pano = sample[j]
                  panoid = pano.panoid
                  if pano.initialized == False:
                      panoid = ''
                  tasks.append(panoid + "\n")

          file = open(taskFile,"w") 
          file.writelines(tasks)
          file.close() 
          self.pendingTasks = 1
          self.finishedTasks = 0
          self.taskdir = outdir
          arg = "batchgetbyid " + outdir + "\n"
          qcommand = QByteArray(arg.encode())
          self.classifier.write(qcommand)
          self.classifier.waitForBytesWritten()
        except Exception as err:
          print(str(err) + "\n")

    def finishPanoTask(self, outdir):
        try:
          resultFile = outdir + "result.txt"
          if not os.path.exists(resultFile):
             return []
          file = open(resultFile,"r")
          result = file.readline()
          splits = result.split(",")
          file.close() 
          if len(result) < 3:
             return []
          svf = float(splits[0])
          tvf = float(splits[1])
          bvf = float(splits[2])
          if svf * tvf * bvf < 0:
             return []
          return [svf,tvf,bvf]
        except Exception as err:
          print(str(err) + "\n")
          return []

    def finishComputeTasks(self):
        if not os.path.exists(self.taskdir):
           self.removeAllPoints()
           return

        foldername = QDir(self.taskdir).dirName()
        shp = shapefile.Writer(self.taskdir + foldername, shapetype=shapefile.POINT)
        shp.autoBalance = 1
        # create the field names and data type for each.
        shp.field("id", "C")
        shp.field("panoid", "C")
        shp.field("date", "C")
        shp.field("lat", 'N', decimal=15)
        shp.field("lon",  'N', decimal=15)
        shp.field("svf",  'N', decimal=10)
        shp.field("tvf",  'N', decimal=10)
        shp.field("bvf",  'N', decimal=10)
        fileout = open(self.taskDir + foldername +  ".csv","w") 
        fileout.write("id,panoid,date,lat,lon,svf,tvf,bvf\n") 
        job = PanoramaJob()
        job.jobid = foldername
        sampleid = -1
        for i in range(0, len(PanoramaSamples)):
            sample = PanoramaSamples[i]
            for j in range(0, len(sample)):
                pano = sample[j]
                sampleid = sampleid + 1
                if pano.initialized == False:
                    panoid = ''
                    continue
                panoid = pano.panoid
                outdir = self.taskDir + panoid + "\\"
                httpdir = HTTPADDRESS + foldername + "/" + panoid + "/"
                if not os.path.exists(self.taskdir):
                   continue
                pano.id  = sampleid
                panoinfo_file = outdir + "panoinfo.txt"
                result = self.finishPanoTask(outdir)
                if len(result) < 3:
                    continue
                pano.svf = result[0]
                pano.tvf = result[1]
                pano.bvf = result[2]
                pano.write(panoinfo_file)
                shp.point(pano.lon,pano.lat)
                shp.record(sampleid,pano.panoid, pano.date, pano.lat, pano.lon, pano.svf, pano.tvf, pano.bvf)
                fileout.write(pano.toString() + "\n") 
                fisheyefile = httpdir + "fisheye.png"
                fisheyefile = fisheyefile.replace('\\','/') 
                classifiedfisheyefile = httpdir + "fisheye_classified.png"
                classifiedfisheyefile = classifiedfisheyefile.replace('\\','/')
                self.GoogleMapsView.page().runJavaScript("setMarker({0},{1},{2},\"{3}\",\"{4}\",{5},{6})".format(pano.svf,pano.tvf,pano.bvf,fisheyefile,classifiedfisheyefile,pano.lat,pano.lon))
                job.panoramas.append(pano)

        PanoramaJobs.append(job)
        shp.close()
        fileout.close() 
        self.removeAllPoints()

    def createRandomFolderName(self, outdir):
        while 1:
           now = datetime.datetime.now()
           newdir = outdir + str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2) + "-" + str(now.hour).zfill(2) + "-" + str(now.minute).zfill(2) + "-" + str(now.second).zfill(2) + "-" + str(now.microsecond) + "\\"
           if not os.path.exists(newdir):
              os.makedirs(newdir)   
              return newdir

    def compute(self):
        outdir = ''
        if self.bt_saveToNewFolder.isChecked() == False:
          outdir = self.createRandomFolderName(CACHEDIR)
        else:
          foldername, ok = QInputDialog.getText(self, 'Job folder name', 'Specify the job folder name:')
          if ok == False:
             return
          foldername = str(foldername)
          outdir = CACHEDIR + foldername + "\\"
          if os.path.exists(outdir):
             choice = QMessageBox.question(self, 'A job folder with the same name already exists!',
                                              "Overwrite the folder?",
                                              QMessageBox.Yes | QMessageBox.No)
             if choice == QMessageBox.Yes:
                shutil.rmtree(outdir) 
             else:
                 return

        if not os.path.exists(outdir):
           os.makedirs(outdir) 
        try:
           self.taskDir = outdir
           self.startComputeTasks(outdir)
           self.enableUI(False)
        except Exception as err:
           print(str(err) + "\n")
           self.enableUI(True)

    def addPoint(self,lat,lon):
        newPointSet = []
        curPoint = Panorama();
        curPoint.fromLocation(lat,lon)
        if len(PanoramaSamples) == 0 or self.bt_interpolate.isChecked() == False:
           if curPoint.initialized:
              newPointSet.append(curPoint)
              PanoramaSamples.append(newPointSet)
           else:
              return 
        elif len(PanoramaSamples) > 0:
           lastPointSet = PanoramaSamples[len(PanoramaSamples)-1]
           lastPoint = lastPointSet[len(lastPointSet)-1]
           if curPoint.initialized == False:
              return
           interpDist = self.bt_sampledist.value()
           dist = self.great_circle_distance(lastPoint.lat, lastPoint.lon, curPoint.lat, curPoint.lon)
           numofpoints = int(dist / interpDist);
           if numofpoints < 1:
              return
           lonstep = (curPoint.lon - lastPoint.lon) / numofpoints;
           latstep = (curPoint.lat - lastPoint.lat) / numofpoints;
           if numofpoints > 100:
              return
           lastid = ""
           for i in range(0, numofpoints-1):
               newLon = lastPoint.lon + (i + 1) * lonstep;
               newLat = lastPoint.lat + (i + 1) * latstep;
               newSample = Panorama();
               newSample.fromLocation(newLat,newLon)
               #print(len(newPointSet))
               if lastid == newSample.panoid:
                  continue
               #print("({0},{1},{2},{3})".format(curPoint.lat, curPoint.lon,newSample.lat, newSample.lon))
               if self.great_circle_distance(lastPoint.lat, lastPoint.lon, curPoint.lat, curPoint.lon) < self.great_circle_distance(lastPoint.lat, lastPoint.lon, newSample.lat, newSample.lon):
                  continue
               lastid = newSample.panoid
               newPointSet.append(newSample)
           newPointSet.append(curPoint)
           PanoramaSamples.append(newPointSet)

        newPointSet = PanoramaSamples[len(PanoramaSamples)-1]
        if len(PanoramaSamples) > 1:
          lastPointSet = PanoramaSamples[len(PanoramaSamples)-2]
          lastPoint = lastPointSet[len(lastPointSet)-1]
          self.GoogleMapsView.page().runJavaScript("newPolyline ()")
          self.GoogleMapsView.page().runJavaScript("addLineVertex ({0},{1})".format(str(lastPoint.lat),str(lastPoint.lon)))
        for i in range(0, len(newPointSet)):
          samplePoint = newPointSet[i]
          self.GoogleMapsView.page().runJavaScript("addMarker ({0},{1})".format(str(samplePoint.lat),str(samplePoint.lon)))
          self.GoogleMapsView.page().runJavaScript("addLineVertex ({0},{1})".format(str(samplePoint.lat),str(samplePoint.lon)))

    @QtCore.pyqtSlot(str)
    def leftClick(self, arg):
        try:
          splits = arg.split(",")
          lat = float(str(splits[0]).strip())
          lon = float(str(splits[1]).strip())
          CurLatLon.lat = lat;
          CurLatLon.lon = lon;
          self.coords_line.setText("%05f,%05f" % (lat, lon))
          if self.isEnabled == False:
             return
          #print(arg)
          #setSamplingArgs = "setSampling ({0},{1})".format(str(self.bt_interpolate.isChecked()).lower(),self.bt_sampledist.value())
          #setSamplingArgs = "setSampling()"
          #print(setSamplingArgs)
          if self.bt_pick.isChecked() == False:
             return
          self.GoogleStreetView.page().runJavaScript("setPano ({0},{1})".format(lat, lon))
          self.addPoint(lat,lon)
        except Exception as err:
          print(str(err) + "\n")

    @QtCore.pyqtSlot(str)
    def rightClick(self, arg):
        try:
          splits = arg.split(",")
          lat = float(str(splits[0]).strip())
          lon = float(str(splits[1]).strip())
          #CurLatLon.lat = lat;
          #CurLatLon.lon = lon;
          #newSample = Panorama()
          #newSample.fromLocation(lat,lon)    
          #if newSample.initialized == True:
          #if self.isEnabled == True:
          #   return
          self.GoogleStreetView.page().runJavaScript("setPano ({0},{1})".format(lat, lon))
          self.coords_line.setText("%05f,%05f" % (lat, lon))
        except Exception as err:
          print(str(err) + "\n")

    @QtCore.pyqtSlot(str)
    def dblclick(self, arg):
        try:
          splits = arg.split(",")
          lat = float(str(splits[0]).strip())
          lon = float(str(splits[1]).strip())
          CurLatLon.lat = lat;
          CurLatLon.lon = lon;
          self.GoogleStreetView.page().runJavaScript("setPano ({0},{1})".format(lat, lon))
          mapInfo.GUI.coords_line.setText("%05f,%05f" % (lat, lon))
        except Exception as err:
          print(str(err) + "\n")
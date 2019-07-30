import sys
import os
SVFHOME = os.environ['SVFHOME']
GSV_API_URL = "https://maps.googleapis.com/maps/api/streetview"

# Import Pillow:
from PIL import Image
from io import StringIO
from io import BytesIO
import numpy as np
from math import *
import requests
import scipy
import argparse
import math
import cv2
import time
import caffe
import shapefile
import shutil
from shutil import copyfile
import json

class Config():
    apikey = ""
    lat = 42.345573
    lon = -71.098326
    cuda = True
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

MyConfig = Config()

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

class GSVCapture():
    #def getImage(self, outfile, panoid, xsize, ysize, fov, heading, pitch):
    #    url = GSV_API_URL + "?size=" + str(xsize) + "x" + str(ysize) + "&pano=" + panoid + "&fov=" + str(fov) + "&heading=" + str(heading) + "&pitch=" + str(pitch) + API_KEY;
    #    mp3file = urllib2.urlopen(url)
    #    with open(outfile,'wb') as output:
    #         output.write(mp3file.read())
    #    print url
    def checkDir(self, dir):
      if (dir.endswith('/') or dir.endswith('\\')) == False:
         dir = dir + '/'
      return dir

    def getImage(self, panoId, x, y, zoom,outdir):
        url = "https://" + "geo0.ggpht.com/cbk?cb_client=maps_sv.tactile&authuser=0&hl=en&panoid=" + panoId + "&output=tile&x=" + str(x) + "&y=" + str(y) + "&zoom=" + str(zoom) + "&nbt&fover=2"
        outfile = outdir + "/" + str(x) + "_" + str(y) + ".jpg"
        #http = urllib3.PoolManager()
        #response = http.request('GET', url)
        try:
            response = requests.get(url)
            if response.status_code == requests.codes.ok:
               file = BytesIO(response.content)
               return file
        except ValueError:
             return None
        return None
        #mp3file = urllib3.urlopen(url)
        #with open(outfile,'wb') as output:
        #     output.write(mp3file.read())

    def equirectangular2fisheye(self, infile, outfile,isClassified):
        img = Image.open(infile)
        width, height = img.size
        img = img.crop((0,0,width,height/2))
        width, height = img.size
        nparr = np.asarray(img.copy())
        red, green, blue = img.split()
        red = np.asarray(red)
        red.flags.writeable = True
        green = np.asarray(green)
        green.flags.writeable = True
        blue = np.asarray(blue)
        blue.flags.writeable = True
        #green[np.where(green == 128)] = 0
        #blue[np.where(blue == 128)] = 0
        fisheye = np.ndarray(shape=(512,512,3), dtype=np.uint8)
        fisheye.fill(0) # Transpose back needed
        fisheyesize = 512
        x = np.arange(0,512,dtype=float)
        x = x / 511.0;
        x = (x - 0.5) * 2;
        x = np.tile(x,(512,1))
        y = x.transpose();
        dist2ori = np.sqrt((y * y) + (x * x))

        zenithD = dist2ori * 90.0
        zenithD[np.where(zenithD <= 0.000000001)] = 0.000000001
        zenithR = zenithD * 3.1415926 / 180.0
        wproj = np.sin(zenithR) / (zenithD / 90.0);#weight for equal-areal projection
        x2 = np.ndarray(shape=(512,512),dtype=float)
        x2.fill(0.0)
        y2 = np.ndarray(shape=(512,512),dtype=float)
        y2.fill(1.0)
        cosa = (x*x2 + y*y2) / np.sqrt((x*x + y*y) * (x2*x2+ y2*y2));
        lon = np.arccos(cosa) * 180.0 / 3.1415926;
        indices = np.where(x > 0)
        lon[indices] = 360.0 - lon[indices]
        lon = 360.0 - lon
        lon = 1.0 -(lon / 360.0)
        outside = np.where(dist2ori > 1)
        lat = dist2ori
        srcx = (lon*(width-1)).astype(int)
        srcy = (lat*(height-1)).astype(int)
        srcy[np.where(srcy > 255)] = 0
        maxx = np.max(srcx)
        maxy = np.max(srcy)
        indices = (srcx + srcy*width).tolist();

        red = np.take(red,np.array(indices))
        green = np.take(green,np.array(indices))
        blue = np.take(blue,np.array(indices))
        red[outside] = 0
        green[outside] = 0
        blue[outside] = 0
        svf = -1  
        tvf = -1
        bvf = -1
        backgroundMask =  0                           #RGB[0,  0,  0]
        skyMask        =  65536*128+256*128+128       #RGB[128,128,128]
        treeMask       =  65536*128+256*128+192       #RGB[128,128,192]
        buildingMask   =  65536*0+256*0+128           #RGB[0,  0,  128]
        if isClassified:
            allPixels = 65536 * red + 256 * green + blue
            skyIndices = np.where(allPixels == skyMask)
            treeIndices = np.where(allPixels == treeMask)
            buildIndices = np.where(allPixels == buildingMask)

            backgroundIndices = np.where(allPixels != 0)
            svf = np.sum(wproj[skyIndices]) / np.sum(wproj[backgroundIndices])
            tvf = np.sum(wproj[treeIndices]) / np.sum(wproj[backgroundIndices])
            bvf = np.sum(wproj[buildIndices]) / np.sum(wproj[backgroundIndices])

            red[skyIndices] = 128
            green[skyIndices] = 128
            blue[skyIndices] = 128

            red[treeIndices] = 128
            green[treeIndices] = 128
            blue[treeIndices] = 192

            red[buildIndices] = 0
            green[buildIndices] = 0
            blue[buildIndices] = 128
        red[outside] = 255
        green[outside] = 255
        blue[outside] = 255
        fisheye = np.dstack((red, green, blue))
        Image.fromarray(fisheye).save(outfile)
        return [svf,tvf,bvf]

    def classify(self,infile,outfile):
        input_image = cv2.imread(infile)
        input_image = cv2.resize(input_image, (self.input_shape[3],self.input_shape[2]))
        input_image = input_image.transpose((2,0,1))
        input_image = np.asarray([input_image])
        out = self.segnet.forward_all(data=input_image)
        segmentation_ind = np.squeeze(self.segnet.blobs['argmax'].data)
        segmentation_ind_3ch = np.resize(segmentation_ind,(3,self.input_shape[2],self.input_shape[3]))
        segmentation_ind_3ch = segmentation_ind_3ch.transpose(1,2,0).astype(np.uint8)
        segmentation_rgb = np.zeros(segmentation_ind_3ch.shape, dtype=np.uint8)
        cv2.LUT(segmentation_ind_3ch,self.label_colours,segmentation_rgb)
        scipy.misc.toimage(segmentation_rgb, cmin=0.0, cmax=255).save(outfile)

    def initialize(self,useCUDA):
        segnetModel = SVFHOME + "SegNet-Tutorial-master/Example_Models/segnet_model_driving_webdemo.prototxt"
        segnetWeights = SVFHOME +"SegNet-Tutorial-master/Example_Models/segnet_weights_driving_webdemo.caffemodel"
        segnetColours = SVFHOME +"SegNet-Tutorial-master/Scripts/camvid11.png"
        if os.path.exists(segnetWeights) == False:
            f = open(segnetWeights, 'wb')
            f1 = open(SVFHOME +"SegNet-Tutorial-master/Example_Models/segnet_weights_driving_webdemo_1.caffemodel", 'rb')
            f.write(f1.read())
            f1.close()
            f2 = open(SVFHOME +"SegNet-Tutorial-master/Example_Models/segnet_weights_driving_webdemo_2.caffemodel", 'rb')
            f.write(f2.read())
            f2.close()
            f3 = open(SVFHOME +"SegNet-Tutorial-master/Example_Models/segnet_weights_driving_webdemo_3.caffemodel", 'rb')
            f.write(f3.read())
            f3.close()
            f.close()

        # Split into 3 parts as GitHub does not allow larger than 50MB files
        #f = open(segnetWeights, 'rb')
        #f.seek(0, os.SEEK_END)
        #fsize = f.tell()
        #f.seek(0)
        #partsize = fsize / 3
        #fdata = f.read(partsize)
        #f1 = open(SVFHOME +"SegNet-Tutorial-master/Example_Models/segnet_weights_driving_webdemo_1.caffemodel", 'wb')
        #f1.write(fdata)
        #f1.close()

        #fdata = f.read(partsize)
        #f2 = open(SVFHOME +"SegNet-Tutorial-master/Example_Models/segnet_weights_driving_webdemo_2.caffemodel", 'wb')
        #f2.write(fdata)
        #f2.close()

        #fdata = f.read(fsize-partsize)
        #f3 = open(SVFHOME +"SegNet-Tutorial-master/Example_Models/segnet_weights_driving_webdemo_3.caffemodel", 'wb')
        #f3.write(fdata)
        #f3.close()
        #f.close()


        self.segnet = caffe.Net(segnetModel,segnetWeights,caffe.TEST) 
        caffe.set_mode_cpu()   
        if MyConfig.cuda == True:
           caffe.set_mode_gpu()
        self.input_shape = self.segnet.blobs['data'].data.shape
        self.output_shape = self.segnet.blobs['argmax'].data.shape   
        self.label_colours = cv2.imread(segnetColours).astype(np.uint8) 

    def getByID(self, outdir, panoid):
        if panoid == '':
           return [-1,-1,-1] 
        outdir = self.checkDir(outdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir) 
        #self.getImage(outdir + "/POS_Y.jpg",panoid,600,600,90,0,0)
        #self.getImage(outdir + "/POS_X.jpg",panoid,600,600,90,90,0)
        #self.getImage(outdir + "/NEG_Y.jpg",panoid,600,600,90,180,0)
        #self.getImage(outdir + "/NEG_X.jpg",panoid,600,600,90,270,0)
        #self.getImage(outdir + "/NEG_Z.jpg",panoid,600,600,90,0,-90)
        #self.getImage(outdir + "/POS_Z.jpg",panoid,600,600,90,0,90)
        tilesize = 512
        numtilesx = 4
        numtilesy = 2
        mosaicxsize = tilesize*numtilesx
        mosaicysize = tilesize*numtilesy
        #start_time = time.time()
        mosaic = Image.new("RGB", (mosaicxsize, mosaicysize), "black")
        blkpixels = 0
        for x in range(0, numtilesx):
            for y in range(0, numtilesy):
                 imageTile = self.getImage(panoid, x, y, 2,outdir)
                 if imageTile == None:
                     os.rmdir(outdir)
                     return ""
                 img = Image.open(imageTile)
                 if y == 1:
                    pix_val = list(img.getdata())
                    blk1 = pix_val[tilesize*tilesize-1]
                    blk2 = pix_val[tilesize*(tilesize-1)]
                    blkpixels = blkpixels + sum(blk1) + sum(blk2) 
                    #print(blk1)
                    #print(blk2)
                 #img.save(outdir  + str(x) + "_" + str(y) + ".jpg")
                 mosaic.paste(img,(x*tilesize,y*tilesize,x*tilesize+tilesize,y*tilesize+tilesize))
        #elapsed_time = time.time() - start_time
        #print("(1) %s seconds ---" % elapsed_time)
        #start_time = time.time()
        xstart =  (512 - 128) / 2;
        xsize = mosaicxsize - xstart * 2;
        ysize = mosaicysize - (512 - 320);
        if blkpixels == 0:
           mosaic = mosaic.crop((xstart,0,xstart+xsize,ysize))
        mosaic = mosaic.resize((1024,512))
        mosaic.save(outdir + "mosaic.png")
        self.classify(outdir + "mosaic.png",outdir + "mosaic_classified.png")
        self.equirectangular2fisheye(outdir + "mosaic.png",outdir + "fisheye.png",False)
        return self.equirectangular2fisheye(outdir + "mosaic_classified.png",outdir + "fisheye_classified.png",True)
        #elapsed_time = time.time() - start_time
        #print("(5) %s seconds ---" % elapsed_time)
        #start_time = time.time()
        #os.remove(outdir + "mosaic_classified.png")

    def batchGetByID(self, outdir):
        outdir = self.checkDir(outdir)
        taskFile = outdir + "task.csv"
        if not os.path.exists(taskFile):
           return
        fs = open(taskFile,"r") 
        lines = fs.readlines()
        fs.close()
        for line in lines:
            panoid = line.strip()
            result = [-1,-1,-1]
            if len(panoid) > 3:
               panodir =  outdir + panoid + '/'
               result = self.getByID(panodir, panoid)
               if len(result) < 3:
                  result = [-1,-1,-1]
            fresult = open(panodir +  "result.txt","w") 
            fresult.write(str(result[0]) + "," + str(result[1]) + "," + str(result[2]) + "\n") 
            fresult.close()            

    def getByLatLong(self, outdir, lat,lon):
        pano = Panorama();
        pano.fromLocation(lat,lon)
        if pano.initialized == False:
            #print("Not available")
            return ""
        outdir = self.checkDir(outdir)
        outdir = outdir + pano.panoid + '/'
        result = self.getByID(outdir, pano.panoid)
        if len(result) == 3:
           pano.svf = result[0]
           pano.tvf = result[1]
           pano.bvf = result[2]
           panoinfo_file = outdir + "panoinfo.txt"
           pano.write(panoinfo_file)
        return pano.toString()

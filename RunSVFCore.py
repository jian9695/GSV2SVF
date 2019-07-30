import sys
import os
SVFHOME = os.environ['SVFHOME']
sys.path.insert(0, SVFHOME + 'PyCaffeCUDA/pycaffe')
import SVFCore
CacheDir = SVFHOME + "Cache\\Default\\"
import time
if __name__ == "__main__":
    GSVCapture = SVFCore.GSVCapture()
    GSVCapture.initialize(True)
    sys.stdout.flush()
    while 1:
        try:
            line = sys.stdin.readline().lower()
            splits = line.split()
            if len(splits) <= 0:
                continue
            if len(splits) > 0 and splits[0] == "exit":
                break
            if len(splits) > 0 and splits[0] == "setdir":
                cacheDir = GSVCapture.checkDir(splits[1])
                if not os.path.exists(cacheDir):
                   os.makedirs(cacheDir)
                if os.path.exists(cacheDir):
                   CacheDir = cacheDir
                   sys.stdout.write("set output directory successful: " + cacheDir +  "\n")
                   sys.stdout.flush()
                else:
                   sys.stdout.write("set output directory failed: " + cacheDir +  "\n")
                   sys.stdout.flush()
            if len(splits) > 2 and splits[0] == "getbylatlong":
                lat = float(splits[1])
                lon = float(splits[2])
                GSVCapture.getByLatLong(CacheDir,lat,lon)
            if len(splits) > 1 and splits[0] == "getbyid":
                id = splits[1]
                GSVCapture.getByID(CacheDir,lat,lon)
            if len(splits) > 1 and splits[0] == "batchgetbyid":
                dir = splits[1]
                GSVCapture.batchGetByID(dir)
            sys.stdout.write("task.finished\n")
            sys.stdout.flush()
        except Exception as err:
            sys.stdout.write(str(err) + "\n")
            sys.stdout.write("task.failed\n")
            sys.stdout.flush()
            continue
        time.sleep(0.01)
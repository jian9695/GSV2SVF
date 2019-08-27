
### 1.	Background
GSV2SVF is designed to interactively calculate sky/tree/building view factors from Google Street View GSV) panoramas in Google Maps. In GSV2SVF, a GSV panorama is first classified at the pixel level into multiple classes including sky, tree and building, and then transformed into a hemispherical (fisheye) image. The sky, tree and building view factor respectively represents the areal proportion (in the range of [0,1]) of a fisheye image that is occupied by sky, tree and building pixels. A video is available at https://github.com/jian9695/GSV2SVF/blob/master/Video.mp4 and https://youtu.be/k00wCnuzuvE
### 2.	Software infrastructure and system requirements
The Caffe-SegNet deep convolutional framework is used to classify street images (https://github.com/alexgkendall/caffe-segnet). Python and JavaScript were used to develop the interactive functionality that integrates Caffe-SegNet with Google Maps. The program currently runs only on Windows due to the restriction that the Caffe-SegNet module was compiled on Windows, although it could also be complied on Linux. A NVIDIA graphics card that supports CUDA 7.5 or newer versions is required. It has been tested only on Windows 10. Further efforts are needed to rebuild GSV2SVF for running on Linux.
### 3.	Google Maps API license
A Google Maps API is needed to explore Google Maps and perform GSV queries. The user may apply for a Google Maps API Key at https://developers.google.com/maps/documentation/javascript/get-api-key. 
### 4.	Configuration
Open the configuration table Config.csv in the root. The table consists of two columns: the variable names (APIKey, Lat, Lon, CUDA) are laid out in the first column with their respective values stored in the second column. Enter your Google Maps API Key and optionally the startup map location in the second column.
### 5.	Run GSV2SVF (Run.bat)
 
#### 5.1.	Add sample points
The user can add GSV sample points for view factor calculation in three different ways: (1) from the text box; (2) from mouse click; (3) from a shapefile (.shp).
*  (1)	Add a single GSV sample point from the coordinate text box. You can either manually type in coordinates in the format of “lat,lon” or by clicking on the map to update the coordinates in the text box, and then click   to add the point.
*  (2)	Add GSV sample points by interactively double-clicking on the map. First toggle on   to enter the interactive sampling mode. To densify the points between two mouse double-click positions, you may toggle on   and enter the desired sampling distance (in units of meters).
*  (3)	Add GSV sample points from a shapefile. Click   to browse for shapefiles and add GSV sample points from the selected shapefile. 
#### 5.2.	Compute and explore view factors
*  (1)	Compute and save the results to the default folder (./Cache/Default) by unchecking   and then clicking  .
*  (2)	Compute and save the results to a separate folder by checking   and then clicking  . You will be promoted to specify the folder path (relative to ./Cache) to which the results will be saved. 
When a computation task is done, the sample points will be shaded in colors of red (SVF=0) to green (SVF=1) by their sky view factor values. To view the tree and building view factors at a sample point, you can hover the mouse over the sample point and an information window will pop up displaying the sky, tree, and building view factors together with the unclassified and classified hemispherical street view.
The result set for each sample point is stored in a separate folder that contains the following items:
 
*  (1)	The GSV panorama (mosaic.png).
*  (2)	The fisheye image (fisheye.png).
*  (3)	The classified GSV panorama (mosaic_segnet.png).
*  (4)	The classified fisheye image (fisheye_segnet.png).
*  (5)	The sample point attributes (sequential number, GSV panorama ID, capture date, latitude, longitude, sky view factor, tree view factor, building view factor).
The attributes for each sample point are also written sequentially into a shapefile and a CSV file in the same folder. The shapefile and the CSV file can then be imported into GIS and other tools for further visualization and analysis.
#### 5.3.	Export results
Click   to interactively define the export extent and then click   to all results within the extent to the specified folder. 
### 6.	Contact
Jianming Liang 
jian9695@gmail.com

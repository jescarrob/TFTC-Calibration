### -----------------------------------------------------

# Use this script to calibrate data acquired with TFTC_Measurement.py

### -----------------------------------------------------

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import sqlite3
from sklearn.linear_model import LinearRegression
import os

import shutil

def copy_and_rename(src_path, dest_path, new_name):
	# Copy the file
    shutil.copy(src_path, dest_path)
    os.rename(f"{dest_path}/{os.path.basename(src_path)}",f"{dest_path}/{new_name}")

path_raw = "data/raw/"
path_calibrated = "data/"

filename = "____.db"
filename_calibrated = filename[:-3]+"_calibrated.db"



copy_and_rename(path_raw+filename, path_calibrated, filename_calibrated)
con = sqlite3.connect(path_calibrated+filename_calibrated)
cur = con.cursor()
cur.execute("SELECT * FROM measurement")
data = np.array(cur.fetchall())
con.close()

# data = data[4000:,:]  #truncate initial data points if needed


time=data[:,0]
emf=data[:,1]
HJ = data[:,2]
CJ = data[:,3]
DeltaT = HJ-CJ

avg_DeltaT_list = []
avg_emf_list = []
std_DeltaT_list = []
std_emf_list = []

#generate layout
app = pg.mkQApp("Calibration Tool")
win = pg.QtWidgets.QMainWindow()
win.setWindowTitle('Calibration Tool')
cw = QtWidgets.QWidget()
win.setCentralWidget(cw)
layout = QtWidgets.QGridLayout()
cw.setLayout(layout)

pw1 = pg.PlotWidget()
layout.addWidget(pw1,1,1,1,3)
pw2 = pg.PlotWidget()
layout.addWidget(pw2,2,1)
pw3 = pg.PlotWidget()
layout.addWidget(pw3,2,2)
pw4 = pg.PlotWidget()
layout.addWidget(pw4,2,3)
win.show()




# pi1 = pg.PlotItem()
# p1 = pw1.addItem(pi1,row=1, colspan=2)
# p1.avgPen = pg.mkPen('#FFFFFF')
# p1.avgShadowPen = pg.mkPen('#8080DD', width=10)
# p1.setMouseEnabled(x=False, y=False)  # Block this plot
# p2 = win.addPlot(row=2, col=0)
# p3 = win.addPlot(row=2,col=1)




# #pg.dbg()
# p1.setAutoVisible(y=True)



pw1.plot(time,emf)
pw1.setLabel("left","emf", units="mV")
pw1.setLabel("bottom","time", units="s")

pw2.plot(time,emf, pen="w")
pw2.setLabel("left","emf", units="mV")
pw2.setLabel("bottom","time", units="s")
pw2.enableAutoRange(axis=1)

l3 = pw3.plot(DeltaT,emf,pen=None,symbol="o",symbolSize=1)
pw3.enableAutoRange()
pw3.setLabel("left","emf", units="mV")
pw3.setLabel("bottom","DeltaT", units="°C")

avg_pen = pg.mkPen('y', width=1) 
std_pen = pg.mkPen('r', width=.5) 

avg_dt_line = pg.InfiniteLine(pos=0, angle=90, movable=False,pen=avg_pen)
avg_emf_line = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=avg_pen)
pw3.addItem(avg_dt_line, ignoreBounds=True)
pw3.addItem(avg_emf_line, ignoreBounds=True)
std_dt_line1 = pg.InfiniteLine(pos=0, angle=90, movable=False,pen=std_pen)
std_dt_line2 = pg.InfiniteLine(pos=0, angle=90, movable=False,pen=std_pen)
pw3.addItem(std_dt_line1, ignoreBounds=True)
pw3.addItem(std_dt_line2, ignoreBounds=True)
std_emf_line1 = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=std_pen)
std_emf_line2 = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=std_pen)
pw3.addItem(std_emf_line1, ignoreBounds=True)
pw3.addItem(std_emf_line2, ignoreBounds=True)
pw3.show()

l4 = pw4.plot(avg_DeltaT_list,avg_emf_list, pen=None,symbol="o")
pw4.setLabel("left","emf", units="mV")
pw4.setLabel("bottom","DeltaT", units="°C")
pw4.enableAutoRange(axis=1)
l5 = pw4.plot()
pw4.show()






# -------- ROI selector on lower plot ----------------
cal_range = pg.LinearRegionItem()
cal_range.setZValue(10)
pw2.addItem(cal_range)

def update3(self):
    global avg_emf,avg_DeltaT
    global std_dt,std_emf

    # region.setZValue(10)
    minX, maxX = cal_range.getRegion()
    DeltaT_roi = DeltaT[(minX<time) & (time<maxX)]
    emf_roi = emf[(minX<time) & (time<maxX)]
    l3.setData(DeltaT_roi, emf_roi)
    pw3.setAutoVisible(y=True)
    pw3.enableAutoRange()

    avg_DeltaT = DeltaT_roi.mean()
    avg_emf = emf_roi.mean()
    avg_dt_line.setValue(avg_DeltaT)
    avg_emf_line.setValue(avg_emf)

    std_dt = DeltaT_roi.std()
    std_emf = emf_roi.std()
    std_dt_line1.setValue(avg_DeltaT+std_dt)
    std_dt_line2.setValue(avg_DeltaT-std_dt)
    std_emf_line1.setValue(avg_emf+std_emf)
    std_emf_line2.setValue(avg_emf-std_emf)

    
    

cal_range.sigRegionChanged.connect(update3)

# # --------------------------------------------------





def savePointButtonClicked():
    global avg_emf,avg_DeltaT
    global avg_DeltaT_list, avg_emf_list
    global std_dt,std_emf
    global std_DeltaT_list, std_emf_list
    global xerr, yerr

    avg_emf_list += [avg_emf]
    std_emf_list += [std_emf]
    avg_DeltaT_list += [avg_DeltaT]
    std_DeltaT_list += [std_dt]
    l4.setData(avg_DeltaT_list, avg_emf_list)
    pw4.setAutoVisible(y=True)
    pw4.enableAutoRange()

    if len(avg_emf_list) > 2:
        reg = LinearRegression()
        reg.fit(np.array(avg_DeltaT_list).reshape(-1,1),np.array(avg_emf_list).reshape(-1,1))

        x_fit = np.linspace(min(avg_DeltaT_list),max(avg_DeltaT_list),100).reshape(-1,1)
        fit = reg.predict(x_fit)
        l5.setData(x_fit[:,0],fit[:,0])

        yerr = np.array(std_emf_list)
        xerr = np.array(std_DeltaT_list)+1
        err = pg.ErrorBarItem(x=np.array(avg_DeltaT_list), y=np.array(avg_emf_list), left=xerr,right=xerr, top=yerr,bottom=yerr, beam=0.1)
        pw4.addItem(err)
    
def savePlotButtonClicked():
    global avg_DeltaT_list, avg_emf_list
    global yerr, xerr

    print("Calibration Points for: ",filename)
    # print("DeltaT:")
    # print(avg_DeltaT_list)
    # print("emf:")
    # print(avg_emf_list)

    con = sqlite3.connect(path_calibrated+filename_calibrated)
    cur = con.cursor()
    try:
        cur.execute("DROP TABLE calibration")
    except: pass
    cur.execute("CREATE TABLE calibration(dt, emf, dt_err, emf_err)")
    for dt, emf, dt_err, emf_err in zip(avg_DeltaT_list,avg_emf_list,xerr,yerr):
        cur.execute(f"INSERT INTO calibration VALUES({dt},{emf},{dt_err},{emf_err})")
    con.commit()
    con.close()


    

lw = pg.LayoutWidget()
layout.addWidget(lw,3,1,1,3)
btn = QtWidgets.QPushButton("Save Data Point")
lw.addWidget(btn,1,1,1,2)
saveplot_btn = QtWidgets.QPushButton("Save Calibration Curve")
lw.addWidget(saveplot_btn,1,3,1,1)

btn.clicked.connect(savePointButtonClicked)
saveplot_btn.clicked.connect(savePlotButtonClicked)



# # w1 = pg.LayoutWidget()
# # btn = QtWidgets.QPushButton("Save Calibration Point")
# # # win.addWidget(btn,row=2,col=1)
# # button = win.addItem(btn, row=2,col=1)


if __name__ == '__main__':
    pg.exec()
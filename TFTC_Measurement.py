### -----------------------------------------------------

# Use this script to acquire data from a TFTC

### -----------------------------------------------------

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import nidaqmx
from nidaqmx.constants import AcquisitionType,VoltageUnits
from nidaqmx.constants import Edge
import csv
import sqlite3
import datetime as dt
import time

# ------- Saving File ------------------------------------------
start_timestamp = dt.datetime.now()
start_timestamp = start_timestamp.strftime('%Y%m%d-%H%M%S')
saving_file_comment = "K-type_1"
filename = "data/"+start_timestamp+"_"+saving_file_comment+".db"
print("Saving data to file ", filename)

con = sqlite3.connect(filename)
cur = con.cursor()
cur.execute("CREATE TABLE metadata(starting_time)")
cur.execute("CREATE TABLE measurement(time, TC1, TC_HJ, TC_CJ)")


start_time = dt.datetime.now()
start_time_formatted = start_time.strftime("%H:%M:%S.") + f"{start_time.microsecond:06d}"
print(start_time_formatted)
print(type(start_time_formatted))
cur.execute(f"INSERT INTO metadata VALUES('{start_time_formatted}')")

# ------PyQtGraph-----------------------------------------------------------------------------------
app = pg.mkQApp("Calibration Monitor")
win = pg.QtWidgets.QMainWindow()
win.setWindowTitle('Calibration Monitor')
cw = QtWidgets.QWidget()
win.setCentralWidget(cw)
layout = QtWidgets.QGridLayout()
cw.setLayout(layout)

avg_lb = pg.ValueLabel()
dev_lb = pg.ValueLabel()
layout.addWidget(avg_lb,1,3)
layout.addWidget(dev_lb,1,4)

readout_plot = pg.PlotWidget()
layout.addWidget(readout_plot,2,1,1,4)

DT_plot = pg.PlotWidget()
layout.addWidget(DT_plot,3,1,1,4)

HJ_plot = pg.PlotWidget()
layout.addWidget(HJ_plot,4,1,1,2)
CJ_plot = pg.PlotWidget()
layout.addWidget(CJ_plot,4,3,1,2)
win.show()


# p1 = win.addPlot(title="Readout")
# win.nextRow()
# p2 = win.addPlot(title="Control")

# pw.setCentralWidget(lineplot)

# p1.addLegend()
# p1.showGrid(x = True, y = True, alpha = 0.3)
# p2.addLegend()
# p2.showGrid(x = True, y = True, alpha = 0.3)

pch = np.array([])
lro = readout_plot.plot(pch,pch,pen={"color":"w","width":5})
readout_plot.setLabel("left","emf", units="mV")
readout_plot.setLabel("bottom","time", units="s")
readout_plot.enableAutoRange(axis=1)
readout_plot.setTitle("Readout")
readout_plot.showGrid(x=True, y=True, alpha=0.3)

lDT = DT_plot.plot([],[], pen={"color":"y","width":5})
DT_plot.setLabel("left","Temperature", units="C")
DT_plot.setLabel("bottom","time", units="s")
DT_plot.enableAutoRange(axis=1)
DT_plot.setTitle("DeltaT")
DT_plot.showGrid(x=True, y=True, alpha=0.3)

lHJ = HJ_plot.plot([],[],pen={"color":"r","width":5})
HJ_plot.setLabel("left","Temperature", units="C")
HJ_plot.setLabel("bottom","time", units="s")
HJ_plot.enableAutoRange(axis=1)
HJ_plot.setTitle("Hot Junction")
HJ_plot.showGrid(x=True, y=True, alpha=0.3)

lCJ = CJ_plot.plot([],[],pen={"color":"b","width":5})
CJ_plot.setLabel("left","Temperature", units="C")
CJ_plot.setLabel("bottom","time", units="s")
CJ_plot.enableAutoRange(axis=1)
CJ_plot.setTitle("Cold Junction")
CJ_plot.showGrid(x=True, y=True, alpha=0.3)

avg_pen = pg.mkPen('y', width=.5) 
std_pen = pg.mkPen('r', width=.5)
avg_dt_line = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=avg_pen)
avg_emf_line = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=avg_pen)
DT_plot.addItem(avg_dt_line, ignoreBounds=True)
readout_plot.addItem(avg_emf_line, ignoreBounds=True)
std_dt_line1 = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=std_pen)
std_dt_line2 = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=std_pen)
DT_plot.addItem(std_dt_line1, ignoreBounds=True)
DT_plot.addItem(std_dt_line2, ignoreBounds=True)
std_emf_line1 = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=std_pen)
std_emf_line2 = pg.InfiniteLine(pos=0, angle=0, movable=False,pen=std_pen)
readout_plot.addItem(std_emf_line1, ignoreBounds=True)
readout_plot.addItem(std_emf_line2, ignoreBounds=True)
# readout_plot.show()

# --------------------------------------------------------------------------------------------------

data = np.array([])
t_current = np.array([])
TC1_current = np.array([])
TC_HJ_current = np.array([])
TC_CJ_current = np.array([])
DT_current = np.array([])

sampling_rate = 60 #Hz
chans_to_read_V = [13]
chans_to_read_T = [0,1]
with nidaqmx.Task() as task:

	for cha in chans_to_read_V:
		task.ai_channels.add_ai_voltage_chan(f"cDAQ1Mod1/ai{cha:01}",
                                        #  thermocouple_type=nidaqmx.constants.ThermocoupleType.J
										min_val=-1e-3, max_val=1e-3, units=VoltageUnits.VOLTS
										)
	for cha in chans_to_read_T:
		task.ai_channels.add_ai_thrmcpl_chan(f"cDAQ1Mod1/ai{cha:01}",
                                         thermocouple_type=nidaqmx.constants.ThermocoupleType.J
										# min_val=-1e-3, max_val=1e-3, units=VoltageUnits.VOLTS
										)
		
	task.timing.cfg_samp_clk_timing(sampling_rate, sample_mode=AcquisitionType.CONTINUOUS, active_edge=Edge.RISING)


	def update():
		global TC1_current,t_current,TC_HJ_current,TC_CJ_current, DT_current
		t = (dt.datetime.now() - start_time).total_seconds()
		
		n_avg = 15
		data_read = task.read(number_of_samples_per_channel=n_avg)#number_of_samples_per_channel=1)

		TC1 = sum(data_read[0])/n_avg*1000
		TC_HJ = sum(data_read[1])/n_avg
		TC_CJ = sum(data_read[2])/n_avg
		DT = TC_HJ-TC_CJ

		n_current = 600

		TC1_current = np.append(TC1_current,TC1)[-n_current:]
		TC_HJ_current = np.append(TC_HJ_current,TC_HJ)[-n_current:]
		TC_CJ_current = np.append(TC_CJ_current,TC_CJ)[-n_current:]
		DT_current = np.append(DT_current,DT)[-n_current:]
		t_current = np.append(t_current,t)[-n_current:]

		cur.execute(f"INSERT INTO measurement VALUES ({t}, {TC1}, {TC_HJ}, {TC_CJ})")
		con.commit()
	
		lro.setData(t_current,TC1_current)
		lHJ.setData(t_current,TC_HJ_current)
		lCJ.setData(t_current,TC_CJ_current)
		lDT.setData(t_current,DT_current)
		n_dev = 1000

		DT_dev = np.std(DT_current[-n_dev:])
		DT_avg = np.mean(DT_current[-n_dev:])
		emf_avg = np.mean(TC1_current[-n_dev:])
		emf_dev = np.std(TC1_current[-n_dev:])
		avg_lb.setValue(DT_avg)
		dev_lb.setValue(DT_dev)

		std_dt_line1.setValue(DT_avg+DT_dev)
		std_dt_line2.setValue(DT_avg-DT_dev)
		std_emf_line1.setValue(emf_avg+emf_dev)
		std_emf_line2.setValue(emf_avg-emf_dev)
		avg_dt_line.setValue(DT_avg)
		avg_emf_line.setValue(emf_avg)
    


	timer = QtCore.QTimer()
	timer.timeout.connect(update)
	timer.start(200)



	if __name__ == "__main__":
		pg.exec()
		

	con.close()




# saving = 0
# saving_path = "saved_data/"
# start_timestamp = dt.datetime.now()
# start_timestamp = start_timestamp.strftime('%Y%m%d-%H%M')
# print(start_timestamp)

# app = pg.mkQApp("Board Test")
# pw = pg.GraphicsView()
# pw.show()


# lineplot = pg.PlotItem()

# pw.setCentralWidget(lineplot)

# lineplot.addLegend()
# lineplot.showGrid(x = True, y = True, alpha = 0.3)

# cjplot = lineplot.plot([],[],pen="w",name="Cold Juntion")

# #lineplot.setYRange(25,35)

# #legend=pg.PlotItem.addLegend(lineplot)
# #legend.setParentItem(lineplot)

# data = np.array([])
# frames = np.array([])

# data = [data,data,data,data,data,data,data,data,data,data,data,data,data,data,data,data]


# sampling_rate = 60 #Hz

# with nidaqmx.Task() as task:

	
# 	task.ai_channels.add_ai_temp_built_in_sensor_chan(f"cDAQ1Mod1/_cjtemp",
#                                         #  thermocouple_type=nidaqmx.constants.ThermocoupleType.J
# 										#min_val=-1e-3, max_val=1e-3, units=VoltageUnits.VOLTS
# 									)
		
# 	task.timing.cfg_samp_clk_timing(sampling_rate, sample_mode=AcquisitionType.CONTINUOUS, active_edge=Edge.RISING)


# 	def update():
# 		global data, frames

# 		data_read = task.read(number_of_samples_per_channel=15)#number_of_samples_per_channel=1)
# 		data = np.append(data,sum(data_read)/15)

# 		frames = np.append(frames,len(data))
# 		frames = frames.astype(np.float32)
# 		#data = data.astype(np.float32)
# 		cjplot.setData(frames,data)
		
# 		timer = QtCore.QTimer()
# 		#time.sleep(0.5)


# 		# if len(frames) > 100:
# 		# 	lineplot.setXRange(frames[-1]-100,frames[-1])

# 		if (saving) & (len(frames)%100 == 0):
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch00.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data)
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch01.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[1])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch02.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[2])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch03.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[3])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch04.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[4])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch05.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[5])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch06.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[6])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch07.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[7])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch08.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[8])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch09.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[9])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch10.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[10])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch11.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[11])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch12.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[12])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch13.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[13])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch14.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[14])
# 			with open(saving_path+start_timestamp+f"_{sampling_rate:03}a15_ch15.txt", 'w', newline='') as myfile:
# 				wr = csv.writer(myfile)
# 				wr.writerow(data[15])
# 			# with open(start_timestamp+f"_{sampling_rate:03}_HE.txt", 'w', newline='') as myfile:
# 			# 	wr = csv.writer(myfile)
# 			# 	wr.writerow(t2)



	# timer = QtCore.QTimer()
	# timer.timeout.connect(update)
	# timer.start(50)



	# if __name__ == "__main__":
	# 	pg.exec()
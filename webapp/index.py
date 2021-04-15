from flask import Flask, request, render_template, url_for, redirect
from datetime import datetime
import smbus
import math
import os, glob
from random import *
import time
import threading

app = Flask(__name__)

X0 = 1420
Y0 = 710
CAMERA_PATH = os.path.dirname(os.path.abspath(__file__)) + '/billiard_main.py'
RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__)) + '/resources/'
RESOURCE_EXTENSION = 'csv'
HW_SETUP = 'hw_setup.txt'
ADDR = [int(0x41), int(0x42), int(0x43)]

log = {'msg':'Page is loaded.'}
i2c = smbus.SMBus(1)
tx = []
coord = {
    'movex1':0, 'movey1':0,
    'movex2':0, 'movey2':0,
    'movex3':0, 'movey3':0,
    'offsetx1':10, 'offsety1':205,
    'offsetx2':78, 'offsety2':145,
    'offsetx3':10, 'offsety3':105,
    'laser1':19952,
    'laser2':19952,
    'laser3':19952,
}
error = 0

started = 0
recordBtnNameList = {
    str(0):'Game Start',
    str(1):'Stop Recording'
}
recordMsgList = {
    str(0):'Stopped.',
    str(1):'Recording..'
}
filepaths = glob.glob(RESOURCE_PATH+'*.csv')
filenames = []
records = {}
fileusing = []

def initialization():
    f = open(RESOURCE_PATH + HW_SETUP, 'r')
    lines = f.readlines()
    f.close()

    addrs = lines[0].split(',')
    initdatum = []
    initdatum.append(lines[1].split(','))
    initdatum.append(lines[2].split(','))
    initdatum.append(lines[3].split(','))

    for i in range(0, 3):
        tx.clear()
        tx.append(int(float(initdatum[i][0])*10)>>8 & 0xff)
        tx.append(int(float(initdatum[i][0])*10) & 0xff)
        tx.append(int(float(initdatum[i][1])*10)>>8 & 0xff)
        tx.append(int(float(initdatum[i][1])*10) & 0xff)
        tx.append(int(float(initdatum[i][2])*10)>>8 & 0xff)
        tx.append(int(float(initdatum[i][2])*10) & 0xff)
        try:
            time.sleep(0.1)
            i2c.write_i2c_block_data(ADDR[i], int(addrs[0].replace("0x",""),16), tx)
        except:
            Log('I2C Error')
    # Offset
    tx.clear()
    tx.append(int(coord['offsetx1'])>>8 & 0xff)
    tx.append(int(coord['offsetx1']) & 0xff)
    tx.append(int(coord['offsety1'])>>8 & 0xff)
    tx.append(int(coord['offsety1']) & 0xff)
    try:
        time.sleep(0.1)
        i2c.write_i2c_block_data(ADDR[0], 0x05, tx)
    except:
        Log('I2C Error')
    tx.clear()
    tx.append(int(coord['offsetx2'])>>8 & 0xff)
    tx.append(int(coord['offsetx2']) & 0xff)
    tx.append(int(coord['offsety2'])>>8 & 0xff)
    tx.append(int(coord['offsety2']) & 0xff)
    try:
        time.sleep(0.1)
        i2c.write_i2c_block_data(ADDR[1], 0x05, tx)
    except:
        Log('I2C Error')
    tx.clear()
    tx.append(int(coord['offsetx3'])>>8 & 0xff)
    tx.append(int(coord['offsetx3']) & 0xff)
    tx.append(int(coord['offsety3'])>>8 & 0xff)
    tx.append(int(coord['offsety3']) & 0xff)
    try:
        time.sleep(0.1)
        i2c.write_i2c_block_data(ADDR[2], 0x05, tx)
    except:
        Log('I2C Error')

@app.route('/')
def index():
    return render_template('index.html', \
        _log=log, \
        _coord=coord, \
        _error=error, \
        _recordBtnName=recordBtnNameList[str(started)], \
        _recordMsg=recordMsgList[str(started)], \
        _filenames=getFilenames(), \
        _records=records, \
        _fileusing=fileusing, \
        _image_update="image/image.jpg" \
        )

@app.route('/random')
def random():
    # coord['movex1'] = round(randint(-X0/10, X0/10),-1)
    # coord['movey1'] = round(randint(-Y0/10, Y0/10),-1)
    # coord['movex2'] = round(randint(-X0/10, X0/10),-1)
    # coord['movey2'] = round(randint(-Y0/10, Y0/10),-1)
    # coord['movex3'] = round(randint(-X0/10, X0/10),-1)
    # coord['movey3'] = round(randint(-Y0/10, Y0/10),-1)
    # coord['laser1'] = ((coord['movex1']*10 + X0) - (0.2 * X0 * (coord['movey1']*10 - Y0)))/10
    # coord['laser2'] = ((coord['movex2']*10 + X0) - (0.2 * X0 * (coord['movey2']*10 - Y0)))/10
    # coord['laser3'] = ((coord['movex3']*10 + X0) - (0.2 * X0 * (coord['movey3']*10 - Y0)))/10

    coord['laser1'] = round(randint(1, 39903), -1)
    coord['laser2'] = round(randint(1, 39903), -1)
    coord['laser3'] = round(randint(1, 39903), -1)
    coord['movex1'] = 10 * ((coord['laser1']-1) % (X0*2/10-1) + 1 - (X0/10))
    coord['movey1'] = (Y0 - 10) - 10*((coord['laser1']-1) // (X0*2/10-1))
    coord['movex2'] = 10 * ((coord['laser2']-1) % (X0*2/10-1) + 1 - (X0/10))
    coord['movey2'] = (Y0 - 10) - 10*((coord['laser2']-1) // (X0*2/10-1))
    coord['movex3'] = 10 * ((coord['laser3']-1) % (X0*2/10-1) + 1 - (X0/10))
    coord['movey3'] = (Y0 - 10) - 10*((coord['laser3']-1) // (X0*2/10-1))
    print(coord)

    return redirect(url_for('index'))

@app.route('/control/<int:data>')
def control(data):
    error = 0
    tx.clear()
    tx.append(data)
    try:
        time.sleep(0.3)
        i2c.write_i2c_block_data(ADDR[0], 0x00, tx)
    except:
        error = 1
    try:
        time.sleep(0.3)
        i2c.write_i2c_block_data(ADDR[1], 0x00, tx)
    except:
        error = 1
    try:
        time.sleep(0.3)
        i2c.write_i2c_block_data(ADDR[2], 0x00, tx)
    except:
        error = 1
    if data == 4:
        Log("HW Reset..")
        time.sleep(3)
        initialization()
        Log("HW Reset Complate")
    updateLog(0, data)
    return redirect(url_for('index'))

@app.route('/poweroff/<int:data>')
def poweroff(data):
    if data == 0:
        Log("Turning device power off..")
        os.system('shutdown -h now')
    elif data == 1:
        Log("Rebooting..")
        os.system('reboot')
    return redirect(url_for('index'))

@app.route('/move', methods = ['POST'])
def move():
    error = 0
    if request.method == 'POST':
        initialization()
        coord['laser1'] = int(request.form['laser1'])
        coord['movex1'] = 10 * ((coord['laser1']-1) % (X0*2/10-1) + 1 - (X0/10))
        coord['movey1'] = (Y0 - 10) - 10*((coord['laser1']-1) // (X0*2/10-1))
        # coord['movex1'] = float(request.form['moveX1'])*10
        # coord['movey1'] = float(request.form['moveY1'])*10
        tx.clear()
        x, y = transCoord1(int(coord['movex1']), int(coord['movey1']))
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        try:
            time.sleep(0.3)
            i2c.write_i2c_block_data(ADDR[0], 0x01, tx)
        except:
            error = 1

        coord['laser2'] = int(request.form['laser2'])
        coord['movex2'] = 10 * ((coord['laser2']-1) % (X0*2/10-1) + 1 - (X0/10))
        coord['movey2'] = (Y0 - 10) - 10*((coord['laser2']-1) // (X0*2/10-1))
        # coord['movex2'] = float(request.form['moveX2'])*10
        # coord['movey2'] = float(request.form['moveY2'])*10
        tx.clear()
        x, y = transCoord2(int(coord['movex2']), int(coord['movey2']))
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        try:
            time.sleep(0.3)
            i2c.write_i2c_block_data(ADDR[1], 0x01, tx)
        except:
            error = 1

        coord['laser3'] = int(request.form['laser3'])
        coord['movex3'] = 10 * ((coord['laser3']-1) % (X0*2/10-1) + 1 - (X0/10))
        coord['movey3'] = (Y0 - 10) - 10*((coord['laser3']-1) // (X0*2/10-1))
        # coord['movex3'] = float(request.form['moveX3'])*10
        # coord['movey3'] = float(request.form['moveY3'])*10
        tx.clear()
        x, y = transCoord3(int(coord['movex3']), int(coord['movey3']))
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        try:
            time.sleep(0.3)
            i2c.write_i2c_block_data(ADDR[2], 0x01, tx)
        except:
            error = 1

        updateLog(1, 0)
        return redirect(url_for('index'))

@app.route('/offset', methods = ['POST'])
def offset():
    error = 0
    if request.method == 'POST':
        coord['offsetx1'] = float(request.form['offsetX1'])*10
        coord['offsety1'] = float(request.form['offsetY1'])*10
        tx.clear()
        x, y = transCoord1(int(coord['offsetx1']), int(coord['offsety1']))
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        # tx.append(int(coord['offsetx1'])>>8 & 0xff)
        # tx.append(int(coord['offsetx1']) & 0xff)
        # tx.append(int(coord['offsety1'])>>8 & 0xff)
        # tx.append(int(coord['offsety1']) & 0xff)
        try:
            time.sleep(0.1)
            i2c.write_i2c_block_data(ADDR[0], 0x05, tx)
        except:
            error = 1

        coord['offsetx2'] = float(request.form['offsetX2'])*10
        coord['offsety2'] = float(request.form['offsetY2'])*10
        tx.clear()
        x, y = transCoord2(int(coord['offsetx2']), int(coord['offsety2']))
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        # tx.append(int(coord['offsetx2'])>>8 & 0xff)
        # tx.append(int(coord['offsetx2']) & 0xff)
        # tx.append(int(coord['offsety2'])>>8 & 0xff)
        # tx.append(int(coord['offsety2']) & 0xff)
        try:
            time.sleep(0.1)
            i2c.write_i2c_block_data(ADDR[1], 0x05, tx)
        except:
            error = 1

        coord['offsetx3'] = float(request.form['offsetX3'])*10
        coord['offsety3'] = float(request.form['offsetY3'])*10
        tx.clear()
        x, y = transCoord3(int(coord['offsetx3']), int(coord['offsety3']))
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        # tx.append(int(coord['offsetx3'])>>8 & 0xff)
        # tx.append(int(coord['offsetx3']) & 0xff)
        # tx.append(int(coord['offsety3'])>>8 & 0xff)
        # tx.append(int(coord['offsety3']) & 0xff)
        try:
            time.sleep(0.1)
            i2c.write_i2c_block_data(ADDR[2], 0x05, tx)
        except:
            error = 1

        updateLog(2, 0)
        return redirect(url_for('index'))

@app.route('/start')
def start():
    global started
    if os.path.isfile(RESOURCE_PATH+str(started)):
        os.remove(RESOURCE_PATH+str(started))

    if started is 0:
        
        t = threading.Thread(target=threadCamera)
        t.start()

        started = 1
        now = datetime.now().strftime("%y%m%d%H%M.csv")
        f = open(RESOURCE_PATH+now, 'w')
        f.close()

        f = open(RESOURCE_PATH+str(started), 'w')
        f.write(now)
        f.close()
    elif started is 1:

        started = 0

        f = open(RESOURCE_PATH+str(started), 'w')
        f.close()

    return redirect(url_for('index'))

@app.route('/readfile', methods = ['POST'])
def readfile():
    if request.method == 'POST':
        filename = request.form['filenames']
        filepath = RESOURCE_PATH+filename[2:4]+filename[5:7]+filename[8:10]+filename[11:13]+filename[14:16]+'.csv'
        f = open(filepath, 'r')
        lines = f.readlines()
        f.close()

        records.clear()
        for line in lines:
            key = line.split(',')[0]
            records[key] = line.split(',')[1:7]
            print(records[key])
            try:
                # x1 = int(float(records[key][0]))
                # y1 = int(float(records[key][1]))
                # x2 = int(float(records[key][2]))
                # y2 = int(float(records[key][3]))
                # x3 = int(float(records[key][4]))
                # y3 = int(float(records[key][5]))
                # print(x1, y1, x2, y2, x3, y3)
                # records[key].append(str(int(((x1*10 + X0) + ((0.2*X0-1) * ((Y0-10) - y1*10)))/10)))
                # records[key].append(str(int(((x2*10 + X0) + ((0.2*X0-1) * ((Y0-10) - y2*10)))/10)))
                # records[key].append(str(int(((x3*10 + X0) + ((0.2*X0-1) * ((Y0-10) - y3*10)))/10)))

                records[key].append(str(int(((int(float(records[key][0]))*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(float(records[key][1]))*10)))/10)))
                records[key].append(str(int(((int(float(records[key][2]))*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(float(records[key][3]))*10)))/10)))
                records[key].append(str(int(((int(float(records[key][4]))*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(float(records[key][5]))*10)))/10)))
            except:
                Log("nothing")

    fileusing.clear()
    fileusing.append(filename)
    return redirect(url_for('index'))

@app.route('/update/<key>')
def update(key):
    coord['movex1'] = int(float(records[str(key)][0])*10)
    coord['movey1'] = int(float(records[str(key)][1])*10)
    coord['movex2'] = int(float(records[str(key)][2])*10)
    coord['movey2'] = int(float(records[str(key)][3])*10)
    coord['movex3'] = int(float(records[str(key)][4])*10)
    coord['movey3'] = int(float(records[str(key)][5])*10)
    coord['laser1'] = int(((int(coord['movex1']/10)*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(coord['movey1']/10)*10))) / 10)
    coord['laser2'] = int(((int(coord['movex2']/10)*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(coord['movey2']/10)*10))) / 10)
    coord['laser3'] = int(((int(coord['movex3']/10)*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(coord['movey3']/10)*10))) / 10)
    # coord['laser1'] = int(((coord['movex1'] + X0) + ((0.2*X0-1) * ((Y0-10) - coord['movey1']))) / 10)
    # coord['laser2'] = int(((coord['movex2'] + X0) + ((0.2*X0-1) * ((Y0-10) - coord['movey2']))) / 10)
    # coord['laser3'] = int(((coord['movex3'] + X0) + ((0.2*X0-1) * ((Y0-10) - coord['movey3']))) / 10)
    print(coord)
    return redirect(url_for('index'))

def getFilenames():
    filepaths = glob.glob(RESOURCE_PATH+'*.csv')
    filenames.clear()
    for path in filepaths:
        name = os.path.basename(path)
        filenames.append('20'+name[0:2]+'-'+name[2:4]+'-'+name[4:6]+' '+name[6:8]+':'+name[8:10])
    filenames.sort(reverse=True)
    return filenames

def threadCamera():
    os.system('python3 ' + CAMERA_PATH)
    print('thread stop')

def transCoord1(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10
    
    if (x_camera < 0) and (y_camera >= 35):
        A = 1.140101
        B = -0.00691
        C = 1.728974
        D = 0.017554
        E = 1.241035
        F = -5.63158
        G = 5.96E-05
        H = 0.002065   
    elif (x_camera < 0) and (y_camera >= 0):
        A = 1.111888
        B = -0.02975
        C = 2.507486
        D = 0.013068
        E = 1.04584
        F = -0.18564
        G = -5.4E-05
        H = 0.00088
    elif (x_camera < 0) and (y_camera >= -35):
        A = 1.075855
        B = -0.00887
        C = 2.438181
        D = 0.012648
        E = 1.008831
        F = -0.179
        G = 0.000179
        H = 0.000282
    elif (x_camera < 0) and (y_camera < -35):
        A = 1.17951
        B = 0.006607
        C = 3.225702
        D = 0.029534
        E = 1.163647
        F = 4.000529
        G = -0.00023
        H = -0.00075
    elif (x_camera >= 0) and (y_camera >= 35):
        A = 0.963115
        B = -0.01053
        C = 1.627911
        D = 0.024687
        E = 1.2083
        F = -4.84488
        G = -0.00052
        H = 0.001739
    elif (x_camera >= 0) and (y_camera >= 0):
        A = 0.974365
        B = -0.02782
        C = 2.25975
        D = 0.034147
        E = 1.050563
        F = -0.14865
        G = -0.00025
        H = 0.001012
    elif (x_camera >= 0) and (y_camera >= -35):
        A = 0.942304
        B = -0.00777
        C = 2.198165
        D = 0.03297
        E = 1.010729
        F = -0.1428
        G = -0.00049
        H = 0.000264
    elif (x_camera >= 0) and (y_camera < -35):
        A = 1.028736
        B = 0.005894
        C = 2.877114
        D = 0.018522
        E = 1.123215
        F = 3.018373
        G = -5.5E-05
        H = -0.00039
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    print('1c) x=%d, y=%d' % (x_camera, y_camera))
    # x_laser = x_camera+4
    # y_laser = y_camera-2
    print('1l) x=%.1f, y=%.1f' % (x_laser, y_laser))
    return int(x_laser*10), int(y_laser*10)
def transCoord2(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10

    if (x_camera < 0) and (y_camera >= 35):
        A = 1.131718
        B = -0.00427
        C = 2.671414
        D = 0.001007
        E = 1.132847
        F = -0.63061
        G = -0.00018
        H = 0.001328
    elif (x_camera < 0) and (y_camera >= 0):
        A = 1.096317
        B = -0.00046
        C = 2.473596
        D = 0.00568
        E = 1.076298
        F = 0.79523
        G = -4.8E-05
        H = 0.000891
    elif (x_camera < 0) and (y_camera >= -35):
        A = 1.075727
        B = 0.004951
        C = 2.435269
        D = 0.005715
        E = 1.050589
        F = 0.800069
        G = 8.73E-05
        H = 0.000289
    elif (x_camera < 0) and (y_camera < -35):
        A = 1.20184
        B = 0.038975
        C = 3.91137
        D = 0.023885
        E = 1.15593
        F = 2.724086
        G = -0.00039
        H = -0.0011
    elif (x_camera >= 0) and (y_camera >= 35):
        A = 1.011127
        B = -0.00744
        C = 2.63679
        D = 0.024534
        E = 1.160128
        F = -1.23066
        G = -0.00041
        H = 0.001573
    elif (x_camera >= 0) and (y_camera >= 0):
        A = 0.992194
        B = 0.001166
        C = 2.286189
        D = 0.023543
        E = 1.082527
        F = 0.826821
        G = -0.00041
        H = 0.001048    
    elif (x_camera >= 0) and (y_camera >= -35):
        A = 0.972656
        B = 0.00583
        C = 2.250127
        D = 0.022889
        E = 1.055964
        F = 0.831033
        G = -0.00055
        H = 0.000177
    elif (x_camera >= 0) and (y_camera < -35):
        A = 1.096598
        B = 0.036646
        C = 3.60744
        D = -0.00447
        E = 1.06596
        F = 0.579299
        G = 0.000165
        H = -0.00028
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    print('2c) x=%d, y=%d' % (x_camera, y_camera))

    # x_laser = x_camera+8.5
    # y_laser = y_camera-2
    print('2l) x=%.1f, y=%.1f' % (x_laser, y_laser))
    return int(x_laser*10), int(y_laser*10)
def transCoord3(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10

    if (x_camera < 0) and (y_camera >= 35):
        A = 1.121155
        B = -0.00558
        C = 2.739254
        D = 0.011212
        E = 1.286472
        F = -6.39592
        G = 0.000203
        H = 0.002322
    elif (x_camera < 0) and (y_camera >= 0):
        A = 1.138942
        B = 0.01316
        C = 2.047464
        D = -0.0054
        E = 1.051834
        F = 0.280252
        G = -0.00025
        H = 0.001017
    elif (x_camera < 0) and (y_camera >= -35):
        A = 1.086927
        B = 0.018809
        C = 1.952707
        D = -0.00501
        E = 1.019028
        F = 0.287105
        G = 8.38E-05
        H = 1.08E-05
    elif (x_camera < 0) and (y_camera < -35):
        A = 1.136847
        B = 0.007144
        C = 1.626551
        D = 0.00269
        E = 1.080867
        F = 1.938441
        G = -0.00013
        H = -0.00042
    elif (x_camera >= 0) and (y_camera >= 35):
        A = 0.964499
        B = -0.0085
        C = 2.612055
        D = -0.00263
        E = 1.200844
        F = -4.37696
        G = -0.00067
        H = 0.001508
    elif (x_camera >= 0) and (y_camera >= 0):
        A = 0.996013
        B = 0.015143
        C = 1.789795
        D = 0.010207
        E = 1.050505
        F = 0.308658
        G = -0.00032
        H = 0.000985
    elif (x_camera >= 0) and (y_camera >= -35):
        A = 0.985014
        B = 0.01961
        C = 1.769103
        D = 0.009839
        E = 1.01701
        F = 0.31468
        G = -0.0004
        H = 9.28E-05
    elif (x_camera >= 0) and (y_camera < -35):
        A = 1.094286
        B = 0.00755
        C = 1.528613
        D = -0.00688
        E = 1.151273
        F = 3.597192
        G = 4.26E-05
        H = -0.00107
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    print('3c) x=%d, y=%d' % (x_camera, y_camera))
    # x_laser = x_camera+3
    # y_laser = y_camera-2.5
    print('3l) x=%.1f, y=%.1f' % (x_laser, y_laser))
    return int(x_laser*10), int(y_laser*10)

def Log(msg):
    log['msg'] = msg

def updateLog(reg, data):
    if reg is 0:
        if data is 0:
            Log('Laser Off')
        elif data is 1:
            Log('Laser On')
        elif data is 2:
            Log('Calibration Start')
    elif reg is 1:
        if data is 0:
            Log('Coordinates are updated.' \
                + ' (' + str(coord['movex1']/10) + ', ' + str(coord['movey1']/10) + ')' \
                + ' (' + str(coord['movex2']/10) + ', ' + str(coord['movey2']/10) + ')' \
                + ' (' + str(coord['movex3']/10) + ', ' + str(coord['movey3']/10) + ')' \
                    )
        elif data is 1:
            Log('An error has occurred during update coordinates.')
    elif reg is 2:
        if data is 0:
            Log('Offset data are applied.' \
                + ' (' + str(coord['offsetx1']/10) + ', ' + str(coord['offsety1']/10) + ')' \
                + ' (' + str(coord['offsetx2']/10) + ', ' + str(coord['offsety2']/10) + ')' \
                + ' (' + str(coord['offsetx3']/10) + ', ' + str(coord['offsety3']/10) + ')' \
                    )
        elif data is 1:
            Log('An error has occurred during setup offsets.')

if __name__ == '__main__':
    initialization()
    app.run(debug=True, port=80, host='0.0.0.0')

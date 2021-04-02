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
    'offsetx1':0, 'offsety1':310,
    'offsetx2':0, 'offsety2':250,
    'offsetx3':0, 'offsety3':200,
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
            # time.sleep(0.1)
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
        # time.sleep(0.1)
        i2c.write_i2c_block_data(ADDR[0], 0x05, tx)
    except:
        Log('I2C Error')
    tx.clear()
    tx.append(int(coord['offsetx2'])>>8 & 0xff)
    tx.append(int(coord['offsetx2']) & 0xff)
    tx.append(int(coord['offsety2'])>>8 & 0xff)
    tx.append(int(coord['offsety2']) & 0xff)
    try:
        # time.sleep(0.1)
        i2c.write_i2c_block_data(ADDR[1], 0x05, tx)
    except:
        Log('I2C Error')
    tx.clear()
    tx.append(int(coord['offsetx3'])>>8 & 0xff)
    tx.append(int(coord['offsetx3']) & 0xff)
    tx.append(int(coord['offsety3'])>>8 & 0xff)
    tx.append(int(coord['offsety3']) & 0xff)
    try:
        # time.sleep(0.1)
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
    print(tx)
    try:
        time.sleep(0.1)
        i2c.write_i2c_block_data(ADDR[0], 0x00, tx)
    except:
        error = 1
    try:
        time.sleep(0.1)
        i2c.write_i2c_block_data(ADDR[1], 0x00, tx)
    except:
        error = 1
    try:
        time.sleep(0.1)
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
            time.sleep(0.2)
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
            time.sleep(0.1)
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
            time.sleep(0.1)
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
    
    if (x_camera >= 0) and (y_camera >= 0):
        A =1.002836072911788
        B = -0.015728094503174
        C = 0
        D = 0.013644028202881
        E = 1.399800410782459
        F = 0
        G = -2.701844801195503e-04
        H = 0.001442380217459
    elif (x_camera < 0) and (y_camera >= 0):
        A =  1.113348002768265
        B = -0.015448588109139
        C =  0
        D = 0.014746331162494
        E = 1.374924341713333
        F = 3.971368159331492e-16
        G = -2.809669996865000e-04
        H = 0.001162873823424
    elif (x_camera < 0) and (y_camera < 0):
        A = 1.070528300681584
        B =  0
        C =  0
        D =  0.014179182790485
        E = 1.056850079430725
        F = 0
        G = 2.607186318007854e-06
        H = -1.916840626518055e-04
    elif (x_camera >= 0) and (y_camera < 0):
        A = 1.057951457566963
        B = 0
        C = 0
        D = 0.014393897381863
        E = 1.064904224070167
        F = 0
        G = 1.047501093714371e-04
        H = -3.020148111373127e-04
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    print('1c) x=%d, y=%d' % (x_camera, y_camera))

    # x_laser = x_camera-10
    # y_laser = y_camera-2
    print('1l) x=%d, y=%d' % (x_laser, y_laser))
    return int(x_laser*10), int(y_laser*10)
def transCoord2(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10

    if (x_camera >= 0) and (y_camera >= 0):
        A = 1.012697872340425
        B =  0
        C =  0
        D = 0.027370212765957
        E = 1.132251428571429
        F =  0
        G = -2.496453900709220e-04
        H = 0.001440000000000
    elif (x_camera < 0) and (y_camera >= 0):
        A = 1.157030782116832
        B = -1.301042606982605e-18
        C = 0
        D = -0.007416863987928
        E = 1.110173008399994
        F = 0
        G = -3.246654063681308e-04
        H = 0.001133355275397
    elif (x_camera < 0) and (y_camera < 0):
        A = 1.106657697224991
        B = -0.029131884503512
        C = 0
        D = -0.007093959597596
        E = 1.150709437888713
        F = 0
        G = -1.761016035811865e-06
        H = -2.802279660415735e-04
    elif (x_camera >= 0) and (y_camera < 0):
        A = 1.012049453002277
        B = -0.030369840851800
        C = 0
        D = 0.027352687918980
        E = 1.199608713646112
        F = 0
        G = -2.540266018151698e-04
        H = -8.992061401858611e-04
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    print('2c) x=%d, y=%d' % (x_camera, y_camera))

    # x_laser = x_camera-15
    # y_laser = y_camera+1
    print('2l) x=%d, y=%d' % (x_laser, y_laser))
    return int(x_laser*10), int(y_laser*10)
def transCoord3(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10

    if (x_camera >= 0) and (y_camera >= 0):
        A =  1.023089025574213
        B = -0.014285714285714
        C = 1
        D = -0.005844584142118
        E = 1.249106905836399
        F =  -6
        G = -1.782306342060986e-04
        H = 0.001226187315914
    elif (x_camera < 0) and (y_camera >= 0):
        A = 1.150804038893044
        B = -0.014285714285714
        C = 1
        D = -0.019830439695094
        E = 1.245894326316914
        F = -6
        G = -4.820520165290124e-04
        H = 0.001183352922321
    elif (x_camera < 0) and (y_camera < 0):
        A = 1.064499755154853
        B = 0.014285714285714
        C = 1
        D = -0.021545094338899
        E = 1.087738545932164
        F = -6
        G = 8.949953140602492e-05
        H = -3.824461098663388e-04
    elif (x_camera >= 0) and (y_camera < 0):
        A = 1.095847923961981
        B = 0.014285714285714
        C = 1
        D = -0.009262787422080
        E = 1.116715500607447
        F = -6
        G = 3.100841200742235e-04
        H = -7.446580433073684e-04
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    print('3c) x=%d, y=%d' % (x_camera, y_camera))

    # x_laser = x_camera-10
    # y_laser = y_camera-3
    print('3l) x=%d, y=%d' % (x_laser, y_laser))
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

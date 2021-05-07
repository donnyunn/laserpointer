from flask import Flask, request, render_template, url_for, redirect
from datetime import datetime
import smbus
import math
import os, glob
from random import *
import time
import threading
import projectivegeometry as pg

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
    coord['laser1'] = round(randint(1, 39903), -1)
    coord['laser2'] = round(randint(1, 39903), -1)
    coord['laser3'] = round(randint(1, 39903), -1)
    coord['movex1'] = 10 * ((coord['laser1']-1) % (X0*2/10-1) + 1 - (X0/10))
    coord['movey1'] = (Y0 - 10) - 10*((coord['laser1']-1) // (X0*2/10-1))
    coord['movex2'] = 10 * ((coord['laser2']-1) % (X0*2/10-1) + 1 - (X0/10))
    coord['movey2'] = (Y0 - 10) - 10*((coord['laser2']-1) // (X0*2/10-1))
    coord['movex3'] = 10 * ((coord['laser3']-1) % (X0*2/10-1) + 1 - (X0/10))
    coord['movey3'] = (Y0 - 10) - 10*((coord['laser3']-1) // (X0*2/10-1))
    # print(coord)

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
    control(0)
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
        # coord['movex1'] = 10 * ((coord['laser1']-1) % (X0*2/10-1) + 1 - (X0/10))
        # coord['movey1'] = (Y0 - 10) - 10*((coord['laser1']-1) // (X0*2/10-1))
        coord['movex1'] = float(request.form['moveX1'])*10
        coord['movey1'] = float(request.form['moveY1'])*10
        tx.clear()
        x, y = transCoord1(int(round(coord['movex1'])), int(round(coord['movey1'])))
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
        # coord['movex2'] = 10 * ((coord['laser2']-1) % (X0*2/10-1) + 1 - (X0/10))
        # coord['movey2'] = (Y0 - 10) - 10*((coord['laser2']-1) // (X0*2/10-1))
        coord['movex2'] = float(request.form['moveX2'])*10
        coord['movey2'] = float(request.form['moveY2'])*10
        tx.clear()
        x, y = transCoord2(int(round(coord['movex2'])), int(round(coord['movey2'])))
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
        # coord['movex3'] = 10 * ((coord['laser3']-1) % (X0*2/10-1) + 1 - (X0/10))
        # coord['movey3'] = (Y0 - 10) - 10*((coord['laser3']-1) // (X0*2/10-1))
        coord['movex3'] = float(request.form['moveX3'])*10
        coord['movey3'] = float(request.form['moveY3'])*10
        tx.clear()
        x, y = transCoord3(int(round(coord['movex3'])), int(round(coord['movey3'])))
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
        x, y = int(coord['offsetx1']), int(coord['offsety1'])
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        try:
            time.sleep(0.1)
            i2c.write_i2c_block_data(ADDR[0], 0x05, tx)
        except:
            error = 1

        coord['offsetx2'] = float(request.form['offsetX2'])*10
        coord['offsety2'] = float(request.form['offsetY2'])*10
        tx.clear()
        x, y = int(coord['offsetx2']), int(coord['offsety2'])
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
        try:
            time.sleep(0.1)
            i2c.write_i2c_block_data(ADDR[1], 0x05, tx)
        except:
            error = 1

        coord['offsetx3'] = float(request.form['offsetX3'])*10
        coord['offsety3'] = float(request.form['offsetY3'])*10
        tx.clear()
        x, y = int(coord['offsetx3']), int(coord['offsety3'])
        tx.append(x>>8 & 0xff)
        tx.append(x & 0xff)
        tx.append(y>>8 & 0xff)
        tx.append(y & 0xff)
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
                records[key].append(str(int(((int(round(float(records[key][0])))*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(round(float(records[key][1])))*10)))/10)))
                records[key].append(str(int(((int(round(float(records[key][2])))*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(round(float(records[key][3])))*10)))/10)))
                records[key].append(str(int(((int(round(float(records[key][4])))*10 + X0) + ((0.2*X0-1) * ((Y0-10) - int(round(float(records[key][5])))*10)))/10)))
            except:
                Log("nothing")

    fileusing.clear()
    fileusing.append(filename)
    return redirect(url_for('index'))

@app.route('/deletefile')
def deletefile():
    os.system('rm -f ' + RESOURCE_PATH + '*.csv')
    return redirect(url_for('index'))

@app.route('/update/<key>')
def update(key):
    try:
        coord['movex1'] = int(float(records[str(key)][0])*10)
        coord['movey1'] = int(float(records[str(key)][1])*10)
        coord['movex2'] = int(float(records[str(key)][2])*10)
        coord['movey2'] = int(float(records[str(key)][3])*10)
        coord['movex3'] = int(float(records[str(key)][4])*10)
        coord['movey3'] = int(float(records[str(key)][5])*10)
        coord['laser1'] = int(((round(coord['movex1']/10)*10 + X0) + ((0.2*X0-1) * ((Y0-10) - round(coord['movey1']/10)*10))) / 10)
        coord['laser2'] = int(((round(coord['movex2']/10)*10 + X0) + ((0.2*X0-1) * ((Y0-10) - round(coord['movey2']/10)*10))) / 10)
        coord['laser3'] = int(((round(coord['movex3']/10)*10 + X0) + ((0.2*X0-1) * ((Y0-10) - round(coord['movey3']/10)*10))) / 10)
    except:
        error = 1
    # print(coord)
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

INIT_SETUP = 0
def transCoord1(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10
    if INIT_SETUP is 0:
        x_laser, y_laser = white2laser1(x_camera, y_camera)
    else:
        x_laser = x_camera-12
        y_laser = y_camera+8
    print('1c) x=%.2f, y=%.2f' % (x_camera, y_camera))
    print('1l) x=%.2f, y=%.2f' % (x_laser, y_laser))
    return int(round(x_laser*10)), int(round(y_laser*10))
def transCoord2(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10
    if INIT_SETUP is 0:
        x_laser, y_laser = yellow2laser2(x_camera, y_camera)
    else:
        x_laser = x_camera+11
        y_laser = y_camera+4
    print('2c) x=%.2f, y=%.2f' % (x_camera, y_camera))
    print('2l) x=%.2f, y=%.2f' % (x_laser, y_laser))
    return int(round(x_laser*10)), int(round(y_laser*10))
def transCoord3(x_camera, y_camera):
    x_camera = x_camera / 10
    y_camera = y_camera / 10
    if INIT_SETUP is 0:
        x_laser, y_laser = red2laser3(x_camera, y_camera)
    else:
        x_laser = x_camera+1
        y_laser = y_camera-1
    print('3c) x=%.2f, y=%.2f' % (x_camera, y_camera))
    print('3l) x=%.2f, y=%.2f' % (x_laser, y_laser))
    return int(round(x_laser*10,-1)), int(round(y_laser*10,-1))

def white2laser1(x_camera, y_camera):
    if (y_camera >= 35):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 1)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 2)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 3)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 4)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 5)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 6)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 7)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 8)
    elif (y_camera >= 0):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 10)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 11)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 12)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 13)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 14)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 15)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 16)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 17)
    elif (y_camera >= -35):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 19)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 20)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 21)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 22)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 23)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 24)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 25)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 26)
    else:
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 28)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 29)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 30)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 31)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 32)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 33)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 34)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(0, 35)
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    print(x_laser, y_laser)
    return float(x_laser), float(y_laser)

def yellow2laser2(x_camera, y_camera):
    if (y_camera >= 35):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 1)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 2)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 3)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 4)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 5)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 6)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 7)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 8)
    elif (y_camera >= 0):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 10)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 11)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 12)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 13)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 14)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 15)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 16)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 17)
    elif (y_camera >= -35):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 19)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 20)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 21)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 22)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 23)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 24)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 25)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 26)
    else:
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 28)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 29)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 30)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 31)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 32)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 33)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 34)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(1, 35)
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    
    return float(x_laser), float(y_laser)

def red2laser3(x_camera, y_camera):
    if (y_camera >= 35):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 1)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 2)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 3)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 4)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 5)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 6)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 7)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 8)
    elif (y_camera >= 0):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 10)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 11)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 12)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 13)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 14)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 15)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 16)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 17)
    elif (y_camera >= -35):
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 19)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 20)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 21)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 22)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 23)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 24)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 25)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 26)
    else:
        if (x_camera < -105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 28)
        elif (x_camera < -70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 29)
        elif (x_camera < -35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 30)
        elif (x_camera < 0):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 31)
        elif (x_camera < 35):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 32)
        elif (x_camera < 70):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 33)
        elif (x_camera < 105):
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 34)
        else:
            A, B, C, D, E, F, G, H = pg.getMatrix(2, 35)
    x_laser = ((A*x_camera) + (B*y_camera) + C) / ((G*x_camera) + (H*y_camera) + 1)
    y_laser = ((D*x_camera) + (E*y_camera) + F) / ((G*x_camera) + (H*y_camera) + 1)
    
    return float(x_laser), float(y_laser)

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

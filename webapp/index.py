from flask import Flask, request, render_template, url_for, redirect
from datetime import datetime
import smbus
import os, glob
from random import *

app = Flask(__name__)

RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__)) + '/resources/'
RESOURCE_EXTENSION = 'csv'
ADDR = [int(0x41), int(0x42), int(0x43)]

log = {'msg':'Page is loaded.'}
i2c = smbus.SMBus(1)
tx = []
coord = {
    'movex1':0, 'movey1':0,
    'movex2':0, 'movey2':0,
    'movex3':0, 'movey3':0,
    'offsetx1':0, 'offsety1':0,
    'offsetx2':0, 'offsety2':0,
    'offsetx3':0, 'offsety3':0
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
        _fileusing=fileusing \
        )

@app.route('/random')
def random():
    coord['movex1'] = randint(-3000, 3000)
    coord['movey1'] = randint(-3000, 3000)
    coord['movex2'] = randint(-3000, 3000)
    coord['movey2'] = randint(-3000, 3000)
    coord['movex3'] = randint(-3000, 3000)
    coord['movey3'] = randint(-3000, 3000)
    return redirect(url_for('index'))

@app.route('/control/<int:data>')
def control(data):
    error = 0
    tx.clear()
    tx.append(data)
    try:
        i2c.write_i2c_block_data(ADDR[0], 0x00, tx)
    except:
        error = 1
    try:
        i2c.write_i2c_block_data(ADDR[1], 0x00, tx)
    except:
        error = 1
    try:
        i2c.write_i2c_block_data(ADDR[2], 0x00, tx)
    except:
        error = 1
    
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
        coord['movex1'] = float(request.form['moveX1'])*10
        coord['movey1'] = float(request.form['moveY1'])*10
        tx.clear()
        tx.append(int(coord['movex1'])>>8 & 0xff)
        tx.append(int(coord['movex1']) & 0xff)
        tx.append(int(coord['movey1'])>>8 & 0xff)
        tx.append(int(coord['movey1']) & 0xff)
        try:
            i2c.write_i2c_block_data(ADDR[0], 0x01, tx)
        except:
            error = 1

        coord['movex2'] = float(request.form['moveX2'])*10
        coord['movey2'] = float(request.form['moveY2'])*10
        tx.clear()
        tx.append(int(coord['movex2'])>>8 & 0xff)
        tx.append(int(coord['movex2']) & 0xff)
        tx.append(int(coord['movey2'])>>8 & 0xff)
        tx.append(int(coord['movey2']) & 0xff)
        try:
            i2c.write_i2c_block_data(ADDR[1], 0x01, tx)
        except:
            error = 1

        coord['movex3'] = float(request.form['moveX3'])*10
        coord['movey3'] = float(request.form['moveY3'])*10
        tx.clear()
        tx.append(int(coord['movex3'])>>8 & 0xff)
        tx.append(int(coord['movex3']) & 0xff)
        tx.append(int(coord['movey3'])>>8 & 0xff)
        tx.append(int(coord['movey3']) & 0xff)
        try:
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
        tx.append(int(coord['offsetx1'])>>8 & 0xff)
        tx.append(int(coord['offsetx1']) & 0xff)
        tx.append(int(coord['offsety1'])>>8 & 0xff)
        tx.append(int(coord['offsety1']) & 0xff)
        try:
            i2c.write_i2c_block_data(ADDR[0], 0x05, tx)
        except:
            error = 1

        coord['offsetx2'] = float(request.form['offsetX2'])*10
        coord['offsety2'] = float(request.form['offsetY2'])*10
        tx.clear()
        tx.append(int(coord['offsetx2'])>>8 & 0xff)
        tx.append(int(coord['offsetx2']) & 0xff)
        tx.append(int(coord['offsety2'])>>8 & 0xff)
        tx.append(int(coord['offsety2']) & 0xff)
        try:
            i2c.write_i2c_block_data(ADDR[1], 0x05, tx)
        except:
            error = 1

        coord['offsetx3'] = float(request.form['offsetX3'])*10
        coord['offsety3'] = float(request.form['offsetY3'])*10
        tx.clear()
        tx.append(int(coord['offsetx3'])>>8 & 0xff)
        tx.append(int(coord['offsetx3']) & 0xff)
        tx.append(int(coord['offsety3'])>>8 & 0xff)
        tx.append(int(coord['offsety3']) & 0xff)
        try:
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
            records[key] = []
            records[key].append(line.split(',')[1:7])

    fileusing.clear()
    fileusing.append(filename)
    return redirect(url_for('index'))

@app.route('/update/<key>')
def update(key):
    coord['movex1'] = int(float(records[str(key)][0][0])*10)
    coord['movey1'] = int(float(records[str(key)][0][1])*10)
    coord['movex2'] = int(float(records[str(key)][0][2])*10)
    coord['movey2'] = int(float(records[str(key)][0][3])*10)
    coord['movex3'] = int(float(records[str(key)][0][4])*10)
    coord['movey3'] = int(float(records[str(key)][0][5])*10)
    return redirect(url_for('index'))

def getFilenames():
    filepaths = glob.glob(RESOURCE_PATH+'*.csv')
    filenames.clear()
    for path in filepaths:
        name = os.path.basename(path)
        filenames.append('20'+name[0:2]+'-'+name[2:4]+'-'+name[4:6]+' '+name[6:8]+':'+name[8:10])
    return filenames

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
    app.run(debug=True, port=80, host='0.0.0.0')

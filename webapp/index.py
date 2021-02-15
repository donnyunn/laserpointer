from flask import Flask, flash, request, render_template, url_for, redirect, Markup
from flask.helpers import send_from_directory
import smbus
import os
from random import *

app = Flask(__name__)

RESOURCE_PATH = '/resources/'
ADDR = [int(0x41), int(0x42), int(0x43)]

log = {'msg':''}
i2c = smbus.SMBus(1)
tx = []
coord = {
    'x1':0, 'y1':0,
    'x2':0, 'y2':0,
    'x3':0, 'y3':0
}
error = 0

filenames = []

@app.route('/')
def index():
    return render_template('index.html', \
        _log=log, \
        _coord=coord, \
        _error=error, \
        _filename=getFilenames() \
        )

@app.route('/random')
def random():
    coord['x1'] = randint(1, 350)
    coord['y1'] = randint(1, 350)
    coord['x2'] = randint(1, 350)
    coord['y2'] = randint(1, 350)
    coord['x3'] = randint(1, 350)
    coord['y3'] = randint(1, 350)
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

@app.route('/move', methods = ['POST'])
def move():
    error = 0
    if request.method == 'POST':
        coord['x1'] = request.form['numberBoxX1']
        coord['y1'] = request.form['numberBoxY1']
        tx.clear()
        tx.append(int(coord['x1'])>>8 & 0xff)
        tx.append(int(coord['x1']) & 0xff)
        tx.append(int(coord['y1'])>>8 & 0xff)
        tx.append(int(coord['y1']) & 0xff)
        try:
            i2c.write_i2c_block_data(ADDR[0], 0x01, tx)
        except:
            error = 1

        coord['x2'] = request.form['numberBoxX2']
        coord['y2'] = request.form['numberBoxY2']
        tx.clear()
        tx.append(int(coord['x1'])>>8 & 0xff)
        tx.append(int(coord['x1']) & 0xff)
        tx.append(int(coord['y1'])>>8 & 0xff)
        tx.append(int(coord['y1']) & 0xff)
        try:
            i2c.write_i2c_block_data(ADDR[1], 0x01, tx)
        except:
            error = 1

        coord['x3'] = request.form['numberBoxX3']
        coord['y3'] = request.form['numberBoxY3']
        tx.clear()
        tx.append(int(coord['x1'])>>8 & 0xff)
        tx.append(int(coord['x1']) & 0xff)
        tx.append(int(coord['y1'])>>8 & 0xff)
        tx.append(int(coord['y1']) & 0xff)
        try:
            i2c.write_i2c_block_data(ADDR[2], 0x01, tx)
        except:
            error = 1

        updateLog(1, 0)
        return redirect(url_for('index'))

def getFilenames():
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
                + ' (' + coord['x1'] + ', ' + coord['y1'] + ')' \
                + ' (' + coord['x2'] + ', ' + coord['y2'] + ')' \
                + ' (' + coord['x2'] + ', ' + coord['y3'] + ')' \
                    )
        elif data is 1:
            Log('An error has occurred during update coordinates.')

if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')
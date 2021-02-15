from flask import Flask, flash, request, render_template, url_for, redirect
from flask.helpers import send_from_directory
import smbus
import os

app = Flask(__name__)

i2c = smbus.SMBus(1)
tx = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control/<int:data>')
def control(data):
    tx.clear()
    tx.append(data)
    try:
        i2c.write_i2c_block_data(0x41, 0x00, tx)
        i2c.write_i2c_block_data(0x42, 0x00, tx)
        i2c.write_i2c_block_data(0x43, 0x00, tx)
    finally:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')
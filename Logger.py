import serial, serial.tools.list_ports, time
from datetime import datetime
from threading import Thread
from flask import Flask, send_file, request

app = Flask(__name__)

ports = serial.tools.list_ports.comports(True)

serialPort = ""

for port, desc, hwid in sorted(ports):
    if "ACM" in port:
        serialPort = port
        continue

ser = serial.Serial(serialPort, 9600, timeout=30)
ser.flushInput()


@app.route("/")
def log():
    return send_file("log.txt")

@app.route("/RPI")
def RPI_Only():
    return send_file("RPI_only.txt")

@app.route("/clear")
def clear_log():
    open('log.txt', 'w').close()
    open('RPI_only.txt', 'w').close()
    return "Cleared"

@app.route("/add", methods=["POST"])
def add_to_log():
    data = request.get_json()
    print(f"[From: {data['from']}] {data['data']}")
    with open("log.txt", "a") as fi: fi.write(f"[{datetime.now().strftime('%H:%M:%S')}] [From: {data['from']}] {data['data']}\n")
    with open("RPI_only.txt", "a") as fi: fi.write(f"[{datetime.now().strftime('%H:%M:%S')}] {data['data']}\n")
    return send_file("log.txt")

@app.route("/start")
def force_start():
    ser.write(b"Force the system to start")
    return "Forcing startup..."

def serial_thread():
    while True:
        try:
            try:
                ser_bytes = ser.readline()
                # decoded_bytes = ser_bytes.decode('ascii')
                # decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8")
                # if decoded_bytes == "": decoded_bytes = "[No data]"
                print(ser_bytes)
                with open("log.txt", "a") as fi: fi.write(f"[{datetime.now().strftime('%H:%M:%S')}] {ser_bytes}\n")
            except Exception as e: 
                with open("log.txt", "a") as fi: fi.write(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {e}\n")
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            return True

if __name__ == '__main__': 
   ser_thread = Thread(target=serial_thread, name="serial_thread")
   ser_thread.setDaemon(True)
   ser_thread.start()

   app.run(host="0.0.0.0", port=1337)
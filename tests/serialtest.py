import serial

ser = serial.Serial("/dev/tty.usbmodem1201", 9600)

ser.write(b"Hello i beleave you exist maybe?")

print(ser.readline())
import serial
import time

port = '/dev/serial0'
baud = 9600

try:
    ser = serial.Serial(port, baud, timeout=1)
except Exception as e:
    print("Failed to open serial port:", e)
    exit(1)

time.sleep(2)  # Allow time for the port to initialize

# Replace with a valid command for your device
command = b'Y'
ser.flush()
ser.write(command.encode())
time.sleep(0.5)


response = ser.read(64)  # Adjust the number of bytes based on your expected response
print("Received:", response.decode())

ser.close()
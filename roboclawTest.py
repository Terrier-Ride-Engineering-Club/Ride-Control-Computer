"""
GPIO14 - UART_TX
GPIO15 - UART_RX

RaspiConfig Serial Tutorial: https://resources.basicmicro.com/configuring-the-raspberry-pi-3-serial-port/
RoboClaw tutorial: https://resources.basicmicro.com/packet-serial-with-the-raspberry-pi-3/
"""


from roboclaw import RoboClaw
from time import sleep

if __name__ == "__main__":
    
    address = 0x80
    roboclaw = RoboClaw(port='/dev/ttyAMA0',address=0x80)
    
    while True:
        
        print(f"STATUS: {roboclaw.read_status()}")
        print(f"VOLTAGE: {roboclaw.read_batt_voltage('main')}")
        sleep(2)
        
        # roboclaw.drive_motor(1,0)
        # sleep(2)
        
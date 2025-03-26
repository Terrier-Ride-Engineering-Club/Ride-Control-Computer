import logging
import time
from threading import Lock

import serial
import struct
from PyCRC.CRCCCITT import CRCCCITT

from roboclaw_cmd import Cmd

logger = logging.getLogger('pyroboclaw')
logger.setLevel(logging.WARNING)


class RoboClaw:
    def __init__(self, port, address, auto_recover=False, **kwargs):
        self.port = serial.Serial(baudrate=9600, timeout=0.1, interCharTimeout=0.01)
        self.port.port = port
        self.address = address
        self.serial_lock = Lock()
        self.auto_recover = auto_recover
        try:
            self.port.close()
            self.port.open()
        except serial.serialutil.SerialException:
            logger.exception('roboclaw serial')
            if auto_recover:
                self.recover_serial()
            else:
                raise

    def _read(self, cmd, fmt):
        cmd_bytes = struct.pack('>BB', self.address, cmd)
        expected_length = struct.calcsize(fmt)
        try:
            with self.serial_lock:
                self.port.write(cmd_bytes)
                response = bytearray()
                start_time = time.time()
                # Read until we have the expected number of data bytes plus 2 CRC bytes
                while len(response) < expected_length + 2:
                    byte = self.port.read(1)
                    if not byte:
                        # Check for timeout
                        if time.time() - start_time > self.port.timeout:
                            break
                        continue
                    response.extend(byte)
                if len(response) < expected_length + 2:
                    logger.error(f"Incomplete read: expected {expected_length + 2} bytes, got {len(response)} bytes")
                    raise Exception("Incomplete read")
            
            print(f"[_read] cmd_bytes: {cmd_bytes.hex()} response: {response.hex()}")
            
            crc_actual = CRCCCITT().calculate(cmd_bytes + response[:-2])
            crc_expect = struct.unpack('>H', response[-2:])[0]
            print(f"[_read] CRC computed: {crc_actual:04x}, expected: {crc_expect:04x}")
            
            if crc_actual != crc_expect:
                logger.error('read crc failed')
                raise CRCException('CRC failed')
            return struct.unpack(fmt, response[:-2])
        except serial.serialutil.SerialException:
            if self.auto_recover:
                self.recover_serial()
            else:
                logger.exception('roboclaw serial')
                raise

    def _write(self, cmd, fmt, *data):
        cmd_bytes = struct.pack('>BB', self.address, cmd)
        data_bytes = struct.pack(fmt, *data)
        message = cmd_bytes + data_bytes
        write_crc = CRCCCITT().calculate(message)
        crc_bytes = struct.pack('>H', write_crc)
        
        print(f"[_write] message: {message.hex()} CRC: {crc_bytes.hex()}")
        
        try:
            with self.serial_lock:
                self.port.write(message + crc_bytes)
                self.port.flush()
                start_time = time.time()
                verification = None
                # Wait for the verification byte
                while True:
                    verification = self.port.read(1)
                    if verification:
                        break
                    if time.time() - start_time > self.port.timeout:
                        break
                if not verification:
                    logger.error("No verification byte received")
                    raise Exception("No verification byte received")
            
            print(f"[_write] verification byte: {verification.hex()}")
            
            if 0xff != struct.unpack('>B', verification)[0]:
                logger.error('write crc failed')
                raise CRCException('CRC failed')
        except serial.serialutil.SerialException:
            if self.auto_recover:
                self.recover_serial()
            else:
                logger.exception('roboclaw serial')
                raise

    def set_speed(self, motor, speed):
        if motor == 1:
            cmd = Cmd.M1SPEED
        else:
            cmd = Cmd.M2SPEED
        self._write(cmd, '>i', speed)

    def recover_serial(self):
        self.port.close()
        while not self.port.isOpen():
            try:
                self.port.close()
                self.port.open()
            except serial.serialutil.SerialException as e:
                time.sleep(0.2)
                logger.warning('failed to recover serial. retrying.')

    def drive_to_position_raw(self, motor, accel, speed, deccel, position, buffer):
        # drive to a position expressed as a percentage of the full range of the motor
        if motor == 1:
            cmd = Cmd.M1SPEEDACCELDECCELPOS
        else:
            cmd = Cmd.M2SPEEDACCELDECCELPOS
        self._write(cmd, '>IiIiB', accel, speed, deccel, position, buffer)

    def drive_to_position(self, motor, accel, speed, deccel, position, buffer):
        range = self.read_range(motor)
        max_speed = self.read_max_speed(motor)
        set_speed = (speed / 100.) * max_speed
        set_position = (position / 100.) * (range[1] - range[0]) + range[0]
        self.drive_to_position_raw(motor,
                                   accel,
                                   round(set_speed),
                                   deccel,
                                   round(set_position),
                                   buffer)

    def drive_motor(self, motor, speed):
        # assert -64 <= speed <= 63
        write_speed = speed + 64
        if motor == 1:
            cmd = Cmd.M17BIT
        else:
            cmd = Cmd.M27BIT
        self._write(cmd, '>B', write_speed)

    def stop_motor(self, motor):
        if motor == 1:
            self._write(Cmd.M1FORWARD, '>B', 0)
        else:
            self._write(Cmd.M2FORWARD, '>B', 0)

    def stop_all(self):
        self._write(Cmd.M1FORWARD, '>B', 0)
        self._write(Cmd.M2FORWARD, '>B', 0)

    def read_encoder(self, motor):
        # Currently, this function doesn't check over/underflow, which is fine since we're using pots.
        if motor == 1:
            cmd = Cmd.GETM1ENC
        else:
            cmd = Cmd.GETM2ENC
        return self._read(cmd, '>IB')[0]

    def reset_quad_encoders(self):
        self._write(Cmd.SETM1ENCCOUNT, '>I', 0)
        self._write(Cmd.SETM2ENCCOUNT, '>I', 0)

    def read_range(self, motor):
        if motor == 1:
            cmd = Cmd.READM1POSPID
        else:
            cmd = Cmd.READM2POSPID
        pid_vals = self._read(cmd, '>IIIIIii')
        return pid_vals[5], pid_vals[6]

    def read_position(self, motor):
        # returns position as a percentage across the full set range of the motor
        encoder = self.read_encoder(motor)
        range = self.read_range(motor)
        return ((encoder - range[0]) / float(range[1] - range[0])) * 100.

    def read_status(self):
        cmd = Cmd.GETERROR
        status = self._read(cmd, '>B')[0]
        return {
            0x0000: 'Normal',
            0x0001: 'Warning: High Current - Motor 1',
            0x0002: 'Warning: High Current - Motor 2',
            0x0004: 'Emergency Stop Triggered',
            0x0008: 'Error: High Temperature - Sensor 1',
            0x0010: 'Error: High Temperature - Sensor 2',
            0x0020: 'Error: High Voltage - Main Battery',
            0x0040: 'Error: High Voltage - Logic Battery',
            0x0080: 'Error: Low Voltage - Logic Battery',
            0x0100: 'Driver Fault - Motor 1 Driver',
            0x0200: 'Driver Fault - Motor 2 Driver',
            0x0400: 'Warning: High Voltage - Main Battery',
            0x0800: 'Warning: Low Voltage - Main Battery',
            0x1000: 'Warning: High Temperature - Sensor 1',
            0x2000: 'Warning: High Temperature - Sensor 2',
            0x4000: 'Home - Motor 1',
            0x8000: 'Home - Motor 2'
        }.get(status, 'Unknown Error')

    def read_temp_sensor(self, sensor):
        if sensor == 1:
            cmd = Cmd.GETTEMP
        else:
            cmd = Cmd.GETTEMP2
        return self._read(cmd, '>H')[0] / 10

    def read_batt_voltage(self, battery):
        if battery in ['logic', 'Logic', 'L', 'l']:
            cmd = Cmd.GETLBATT
        else:
            cmd = Cmd.GETMBATT
        return self._read(cmd, '>H')[0] / 10

    def read_voltages(self):
        mainbatt = self._read(Cmd.GETMBATT, '>H')[0] / 10.
        logicbatt = self._read(Cmd.GETLBATT, '>H')[0] / 10.
        return mainbatt, logicbatt

    def read_currents(self):
        currents = self._read(Cmd.GETCURRENTS, '>hh')
        return tuple([c / 100. for c in currents])

    def read_motor_current(self, motor):
        if motor == 1:
            return self.read_currents()[0]
        else:
            return self.read_currents()[1]
        
    def read_version(self):
        """
        Read RoboClaw firmware version.
        Returns up to 48 bytes (depending on the RoboClaw model) terminated by a line feed (10) and null (0) character.
        Example response: b'RoboClaw 10.2A v4.1.11\n\x00' followed by 2 CRC bytes.
        """
        cmd = 21
        cmd_bytes = struct.pack('>BB', self.address, cmd)
        try:
            with self.serial_lock:
                # Send the command
                self.port.write(cmd_bytes)
                # Read response until termination sequence (LF and null) is encountered
                response = bytearray()
                start_time = time.time()
                while True:
                    byte = self.port.read(1)
                    if not byte:
                        # Check for timeout
                        if time.time() - start_time > self.port.timeout:
                            break
                        continue
                    response.extend(byte)
                    # Termination: last two bytes are LF (10) and NULL (0)
                    if len(response) >= 2 and response[-2:] == b'\x0a\x00':
                        break
                # Read the following 2 bytes for CRC
                crc_bytes = self.port.read(2)
            
            print(f"[read_version] cmd_bytes: {cmd_bytes.hex()} response: {response.hex()} crc_bytes: {crc_bytes.hex()}")
            
            # Verify CRC: Calculate over the command and response (excluding CRC bytes)
            crc_actual = CRCCCITT().calculate(cmd_bytes + response)
            crc_expected = struct.unpack('>H', crc_bytes)[0]
            print(f"[read_version] CRC computed: {crc_actual:04x}, expected: {crc_expected:04x}")
            
            if crc_actual != crc_expected:
                logger.error('read version CRC failed')
                raise CRCException('CRC failed')
            # Decode the version string and strip termination characters
            version_str = response.decode('utf-8', errors='ignore').rstrip('\n\x00')
            print(f"[read_version] Firmware version: {version_str}")
            return version_str
        except serial.serialutil.SerialException:
            if self.auto_recover:
                self.recover_serial()
            else:
                logger.exception('roboclaw serial')
                raise

    def read_motor_pwms(self):
        pwms = self._read(Cmd.GETPWMS, '>hh')
        return tuple([c / 327.67 for c in pwms])

    def read_motor_pwm(self, motor):
        if motor == 1:
            return self.read_motor_pwms()[0]
        else:
            return self.read_motor_pwms()[1]

    def read_input_pin_modes(self):
        modes = self._read(Cmd.GETPINFUNCTIONS, '>BBB')
        s3_mode = {
            0: 'Default',
            1: 'Emergency Stop (require restart)',
            2: 'Emergency Stop',
            3: 'Voltage Clamp'
        }.get(modes[0], 'Unknown Mode')
        s4_mode = {
            0: 'Disabled',
            1: 'Emergency Stop (require restart)',
            2: 'Emergency Stop',
            3: 'Voltage Clamp',
            4: 'Home Motor 1'
        }.get(modes[0], 'Unknown Mode')
        s5_mode = {
            0: 'Disabled',
            1: 'Emergency Stop (require restart)',
            2: 'Emergency Stop',
            3: 'Voltage Clamp',
            4: 'Home Motor 2'
        }.get(modes[0], 'Unknown Mode')
        return s3_mode, s4_mode, s5_mode

    def read_max_speed(self, motor):
        if motor == 1:
            cmd = Cmd.READM1PID
        else:
            cmd = Cmd.READM2PID
        return self._read(cmd, '>IIII')[3]

    def read_speed(self, motor):
        # returns velocity as a percentage of max speed
        if motor == 1:
            cmd = Cmd.GETM1SPEED
        else:
            cmd = Cmd.GETM2SPEED
        max_speed = self.read_max_speed(motor)
        speed_vals = self._read(cmd, '>IB')
        speed = (speed_vals[0] / max_speed) * 100.
        if speed_vals[1]:
            speed *= -1
        return speed


class CRCException(Exception):
    pass

import logging
import time
from threading import Lock

import serial
import struct
from PyCRC.CRCCCITT import CRCCCITT

from Backend.roboclaw_cmd import Cmd

logger = logging.getLogger('pyroboclaw')
logger.setLevel(logging.WARNING)


class RoboClaw:
    def __init__(self, port, address, auto_recover=False, **kwargs):
        self.port = serial.Serial(baudrate=38400, timeout=0.1, interCharTimeout=0.01)
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
                self.port.reset_input_buffer()
                # self.port.reset_input_buffer()
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
            
            # print(f"[_read] cmd_bytes: {cmd_bytes.hex()} response: {response.hex()}")
            
            crc_actual = CRCCCITT().calculate(cmd_bytes + response[:-2])
            crc_expect = struct.unpack('>H', response[-2:])[0]
            # print(f"[_read] CRC computed: {crc_actual:04x}, expected: {crc_expect:04x}")
            
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
        
        try:
            with self.serial_lock:
                # print(f"[_write] message: {message.hex()} CRC: {crc_bytes.hex()} ==> {(message + crc_bytes).hex()}")
                self.port.write(message + crc_bytes)
                self.port.flush()
                start_time = time.time()
                verification = None
                # Wait for the verification byte
                while True:
                    verification = self.port.read(1)
                    # print(verification)
                    if verification:
                        break
                    if time.time() - start_time > self.port.timeout:
                        break
                if not verification:
                    logger.error("No verification byte received")
                    raise Exception("No verification byte received")
            
            # print(f"[_write] verification byte: {verification.hex()}")
            
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

    def set_speed_with_acceleration(self, motor: int, speed: int, acceleration: int):
        """
        Params:
            motor (int): 1 or 2 to select which motor gets this command.
            speed (int): the signed speed in QPPS (quad pulses per second)
            acceleration (int): the unsigned acceleration in QPPS (quad pulses per second)


        ## Detailed Desc:
            Drive M1 with a signed speed and acceleration value. The sign indicates which direction the
            motor will run. The acceleration values are not signed. This command is used to drive the motor
            by quad pulses per second and using an acceleration value for ramping. Different quadrature
            encoders will have different rates at which they generate the incoming pulses. The values used
            will differ from one encoder to another. Once a value is sent the motor will begin to accelerate
            incrementally until the rate defined is reached.

            The acceleration is measured in speed increase per second. An acceleration value of 12,000
            QPPS with a speed of 12,000 QPPS would accelerate a motor from 0 to 12,000 QPPS in 1
            second. Another example would be an acceleration value of 24,000 QPPS and a speed value of
            12,000 QPPS would accelerate the motor to 12,000 QPPS in 0.5 seconds.

        Serial:
            Send: [Address, 38, Accel(4 Bytes), Speed(4 Bytes), CRC(2 bytes)]
            Receive: [0xFF]
        """
        if (motor == 1):
            cmd = Cmd.M1SPEEDACCEL
        elif motor == 2:
            cmd = Cmd.M2SPEEDACCEL
        else:
            raise ValueError(f"Motor #{motor} is not valid!")
        
        # The format string '>Ii' means:
        #   - 'I' for a 4-byte unsigned acceleration value
        #   - 'i' for a 4-byte signed speed value
        self._write(cmd, '>Ii', acceleration, speed)
    
    def set_motor1_default_speed(self, default_speed: int):
        """
        Set Motor1 Default Speed for use with M1 position command and RC or analog modes when position
        control is enabled.
        This sets the percentage of the maximum speed set by QPSS as the default speed.
        The range is 0 to 32767.
        
        Serial:
            Send: [Address, 70, Value(2 bytes), CRC(2 bytes)]
            Receive: [0xFF]
        """
        if not (0 <= default_speed <= 32767):
            raise ValueError("Default speed must be between 0 and 32767.")
        self._write(70, '>H', default_speed)
    
    def read_default_speeds(self):
        """
        Read current default speeds for M1 and M2.
        
        Serial:
            Send: [Address, 72]
            Receive: [M1Speed(2 bytes), M2Speed(2 bytes), CRC(2 bytes)]
        
        Returns:
            A tuple (M1Speed, M2Speed) where each speed is a 2-byte unsigned value.
        """
        speeds = self._read(72, '>HH')
        return speeds


    def drive_to_position_with_speed_acceleration_deceleration(self, motor: int, position: int, speed: int, acceleration: int, deceleration: int, buffer: int = 5):
        """
        Params:
            motor (int): 1 or 2 to select which motor gets this command.
            position (int): Signed target position in encoder counts.
            speed (int): Signed cruising speed in QPPS (quad pulses per second) that the motor will run at
                after accelerating and before decelerating.
            acceleration (int): Unsigned acceleration value in QPPS (quad pulses per second).
            deceleration (int): Unsigned deceleration value in QPPS.
            buffer (int, optional): Buffer index for command queuing. Typically use 0 for immediate execution.
        

        ##Detailed Desc:
            Move M1 or M2 positions from their current positions to the specified new positions and hold the
            new positions. Accel sets the acceleration value and deccel the decceleration value. QSpeed sets
            the speed in quadrature pulses the motor will run at after acceleration and before decceleration.
        
        Serial:
            Send: [Address, 65, Accel(4 bytes), Speed(4 Bytes), Deccel(4 bytes), Position(4 Bytes), Buffer, CRC(2 bytes)]
            Receive: [0xFF]
        """
        # Select the appropriate command for each motor.
        if motor == 1:
            cmd = Cmd.M1SPEEDACCELDECCELPOS
        elif motor == 2:
            cmd = Cmd.M2SPEEDACCELDECCELPOS
        else:
            raise ValueError(f"Motor #{motor} is not valid!")
        
        # Send the command.
        # The format '>IiIiB' corresponds to:
        #   'I' : unsigned 4-byte acceleration
        #   'i' : signed 4-byte QSpeed (cruising speed)
        #   'I' : unsigned 4-byte deceleration
        #   'i' : signed 4-byte target position
        #   'B' : 1-byte buffer indicator
        self._write(cmd, '>IiIiB', acceleration, speed, deceleration, position, buffer)

    def recover_serial(self):
        self.port.close()
        while not self.port.is_open:
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

    def drive_to_position_buffered(self, motor: int, position: int, buffer: int = 0):
        """
        Buffered Drive to Position using default acceleration, deceleration, and speed.
        
        Params:
            motor (int): 1 for M1 only (command 119 only supports M1).
            position (int): Signed target position in encoder counts.
            buffer (int): Buffer index for command queuing.
        
        Command 119:
            Send: [Address, 119, Position (4 bytes), Buffer, CRC (2 bytes)]
            Receive: [0xFF]
        """
        if motor != 1:
            raise ValueError("Buffered drive with command 119 only supports motor 1.")
        
        cmd = 119
        self._write(cmd, '>iB', position, buffer)

    def buffered_drive_m1_speed_position(self, speed: int, position: int, buffer: int = 0):
        """
        Buffered Drive M1 with Speed and Position.
        Move M1 from the current position to the specified new position at a given speed and hold the new position.
        Default acceleration and deceleration values are used.
        
        Command 122:
            Send: [Address, 122, Speed (4 bytes), Position (4 bytes), Buffer, CRC (2 bytes)]
            Receive: [0xFF]
        """
        cmd = 122
        self._write(cmd, '>iiB', speed, position, buffer)


    def set_position_pid_constants(self, d=0, p=0, i=0, maxi=0, deadzone=0, min_pos=0, max_pos=0):
        """
        Set the Position PID constants used for the position control commands.

        The Position PID system consists of seven constants:
            - D: Derivative constant (4 bytes, unsigned)
            - P: Proportional constant (4 bytes, unsigned)
            - I: Integral constant (4 bytes, unsigned)
            - MaxI: Maximum integral windup (4 bytes, unsigned)
            - Deadzone: Deadzone in encoder counts (4 bytes, unsigned)
            - MinPos: Minimum Position (4 bytes, signed)
            - MaxPos: Maximum Position (4 bytes, signed)

        Default values for all constants are 0.

        Serial format:
            Send: [Address, 61, D(4 bytes), P(4 bytes), I(4 bytes), MaxI(4 bytes),
                   Deadzone(4 bytes), MinPos(4 bytes), MaxPos(4 bytes), CRC(2 bytes)]
            Receive: [0xFF]
        """
        cmd = 61
        # Format string: 5 unsigned ints followed by 2 signed ints.
        self._write(cmd, '>IIIIIii', d, p, i, maxi, deadzone, min_pos, max_pos)
    
    def read_position_pid_constants(self):
        """
        Read Motor 1 Position PID Constants.
    
        Serial:
            Send: [Address, 63]
            Receive: [P(4 bytes), I(4 bytes), D(4 bytes), MaxI(4 bytes), Deadzone(4 bytes),
                      MinPos(4 bytes), MaxPos(4 bytes), CRC(2 bytes)]
    
        Returns:
            A dictionary containing the Position PID constants:
                - "P": Proportional constant (4 bytes, unsigned)
                - "I": Integral constant (4 bytes, unsigned)
                - "D": Derivative constant (4 bytes, unsigned)
                - "MaxI": Maximum Integral windup (4 bytes, unsigned)
                - "Deadzone": Deadzone in encoder counts (4 bytes, unsigned)
                - "MinPos": Minimum Position (4 bytes, signed)
                - "MaxPos": Maximum Position (4 bytes, signed)
        """
        cmd = 63
        pid_vals = self._read(cmd, '>IIIIIii')
        return {
            "P": pid_vals[0],
            "I": pid_vals[1],
            "D": pid_vals[2],
            "MaxI": pid_vals[3],
            "Deadzone": pid_vals[4],
            "MinPos": pid_vals[5],
            "MaxPos": pid_vals[6]
        }

    def read_encoder(self, motor):
        # Currently, this function doesn't check over/underflow, which is fine since we're using pots.
        if motor == 1:
            cmd = Cmd.GETM1ENC
        else:
            cmd = Cmd.GETM2ENC
        # Discards status byte
        encoder, _ = self._read(cmd, '>iB')
        return encoder
    
    def read_encoder_m1(self):
        """
        Read Encoder Count/Value M1.
        
        Sends: [Address, 16]
        Receives: [Enc1 (4 bytes), Status, CRC (2 bytes)]
        
        The status byte:
            Bit0 - Counter Underflow (1 = Underflow Occurred, Clear After Reading)
            Bit1 - Direction (0 = Forward, 1 = Backwards)
            Bit2 - Counter Overflow (1 = Overflow Occurred, Clear After Reading)
            Bits3-7 - Reserved
        
        Returns:
            A dictionary with the encoder count and interpreted status flags.
        """
        cmd = 16
        encoder, status = self._read(cmd, '>iB')
        underflow = bool(status & 0x01)
        direction = "Backward" if (status & 0x02) else "Forward"
        overflow = bool(status & 0x04)
        return {"encoder": encoder, "underflow": underflow, "direction": direction, "overflow": overflow}

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
        raw = self._read(cmd, '>BBBB')
        status = (raw[0] << 24) | (raw[1] << 16) | (raw[2] << 8) | raw[3]
        # print(f"RETURNED: {raw}")
        return {
            0x00000000: 'Normal',
            0x00000001: 'E-Stop',
            0x00000002: 'Temperature Error',
            0x00000004: 'Temperature 2 Error',
            0x00000008: 'Main Voltage High Error',
            0x00000010: 'Logic Voltage High Error',
            0x00000020: 'Logic Voltage Low Error',
            0x00000040: 'M1 Driver Fault Error',
            0x00000080: 'M2 Driver Fault Error',
            0x00000100: 'M1 Speed Error',
            0x00000200: 'M2 Speed Error',
            0x00000400: 'M1 Position Error',
            0x00000800: 'M2 Position Error',
            0x00001000: 'M1 Current Error',
            0x00002000: 'M2 Current Error',
            0x00010000: 'M1 Over Current Warning',
            0x00020000: 'M2 Over Current Warning',
            0x00040000: 'Main Voltage High Warning',
            0x00080000: 'Main Voltage Low Warning',
            0x00100000: 'Temperature Warning',
            0x00200000: 'Temperature 2 Warning',
            0x00400000: 'S4 Signal Triggered',
            0x00800000: 'S5 Signal Triggered',
            0x01000000: 'Speed Error Limit Warning',
            0x02000000: 'Position Error Limit Warning'
        }.get(status, f'Unknown Error: {status}')

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

    def set_m2_max_current_limit(self, max_current):
        """
        Set Motor 2 Maximum Current Limit.
        :param max_current: Maximum current in 10mA units (e.g. 1000 = 10A).
        """
        cmd = 134
        # The protocol requires padding with 4 zero bytes after the 4-byte current value
        self._write(cmd, '>IBBBB', max_current, 0, 0, 0, 0)

    def read_m2_max_current_limit(self):
        """
        Read Motor 2 Maximum Current Limit.
        :return: Maximum current in 10mA units (e.g. 1000 = 10A).
        """
        cmd = 136
        max_current, _ = self._read(cmd, '>II')
        return max_current
        
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
            
            # print(f"[read_version] cmd_bytes: {cmd_bytes.hex()} response: {response.hex()} crc_bytes: {crc_bytes.hex()}")
            
            # Verify CRC: Calculate over the command and response (excluding CRC bytes)
            crc_actual = CRCCCITT().calculate(cmd_bytes + response)
            crc_expected = struct.unpack('>H', crc_bytes)[0]
            # print(f"[read_version] CRC computed: {crc_actual:04x}, expected: {crc_expected:04x}")
            
            if crc_actual != crc_expected:
                logger.error('read version CRC failed')
                raise CRCException('CRC failed')
            # Decode the version string and strip termination characters
            version_str = response.decode('utf-8', errors='ignore').rstrip('\n\x00')
            # print(f"[read_version] Firmware version: {version_str}")
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

    def write_settings_to_eeprom(self):
        """
        Writes all current settings to non-volatile EEPROM.
        """
        cmd = 94
        self._write(cmd, '', *[])

    def read_settings_from_eeprom(self):
        """
        Reads all settings from non-volatile EEPROM.
        Returns: (Enc1Mode, Enc2Mode)
        """
        cmd = 95
        return self._read(cmd, '>BB')
    
    def read_standard_config(self):
        """
        Reads standard configuration bitmask from the controller.
        Returns: Config bitmask as an integer.
        """
        cmd = 99
        config, = self._read(cmd, '>H')
        return self.decode_standard_config(config)
    
    def decode_standard_config(self, config):
        """
        Decodes a 16-bit standard config value into a dict of boolean settings.
        
        :param config: The 16-bit configuration bitmask.
        :return: A dict with keys for each option and boolean values.
        """
        result = {}
        # Group 1: Serial Mode (bits 0-1)
        serial_mode = config & 0x0003
        result["RC Mode"] = (serial_mode == 0x0000)
        result["Analog Mode"] = (serial_mode == 0x0001)
        result["Simple Serial Mode"] = (serial_mode == 0x0002)
        result["Packet Serial Mode"] = (serial_mode == 0x0003)

        # Group 2: Battery Mode (bits 2-4)
        battery_mode = config & 0x001C
        result["Battery Mode Off"] = (battery_mode == 0x0000)
        result["Battery Mode Auto"] = (battery_mode == 0x0004)
        result["Battery Mode 2 Cell"] = (battery_mode == 0x0008)
        result["Battery Mode 3 Cell"] = (battery_mode == 0x000C)
        result["Battery Mode 4 Cell"] = (battery_mode == 0x0010)
        result["Battery Mode 5 Cell"] = (battery_mode == 0x0014)
        result["Battery Mode 6 Cell"] = (battery_mode == 0x0018)
        result["Battery Mode 7 Cell"] = (battery_mode == 0x001C)

        # Group 3: BaudRate (bits 5-7)
        baud_rate = config & 0x00E0
        result["BaudRate 2400"] = (baud_rate == 0x0000)
        result["BaudRate 9600"] = (baud_rate == 0x0020)
        result["BaudRate 19200"] = (baud_rate == 0x0040)
        result["BaudRate 38400"] = (baud_rate == 0x0060)
        result["BaudRate 57600"] = (baud_rate == 0x0080)
        result["BaudRate 115200"] = (baud_rate == 0x00A0)
        result["BaudRate 230400"] = (baud_rate == 0x00C0)
        result["BaudRate 460800"] = (baud_rate == 0x00E0)

        # Group 4: FlipSwitch (bit 8)
        result["FlipSwitch"] = bool(config & 0x0100)

        # Group 5: Packet Address (bits 8-10)
        # Extract the field (shift right by 8 bits and mask with 0x07)
        packet_address_field = (config & 0x0700) >> 8
        for i in range(8):
            key = f"Packet Address 0x{0x80 + i:02X}"
            result[key] = (packet_address_field == i)

        # Remaining flags (each a single bit)
        result["Slave Mode"] = bool(config & 0x0800)
        result["Relay Mode"] = bool(config & 0x1000)
        result["Swap Encoders"] = bool(config & 0x2000)
        result["Swap Buttons"] = bool(config & 0x4000)
        result["Multi-Unit Mode"] = bool(config & 0x8000)

        return result
    
    def set_s_pin_modes(self, s3_mode, s4_mode, s5_mode):
        """
        Sets the modes for S3, S4 and S5.
        
        Parameters:
            s3_mode, s4_mode, s5_mode: mode values (as integer) to be set.
            
        Command 74 - Set S3, S4 and S5 Modes:
            Send: [Address, 74, S3mode, S4mode, S5mode, CRC(2 bytes)]
            Receive: [0xFF]
        """
        cmd = 74
        self._write(cmd, '>BBB', s3_mode, s4_mode, s5_mode)


    def read_s_pin_modes(self):
        """
        Gets the modes for S3, S4 and S5.
        
        Command 75 - Get S3, S4 and S5 Modes:
            Send: [Address, 75]
            Receive: [S3mode, S4mode, S5mode, CRC(2 bytes)]
        
        Returns:
            A dict with keys 'S3', 'S4', and 'S5' containing the mode descriptions.
        """
        cmd = 75
        raw_modes = self._read(cmd, '>BBBBB')
        s3_mode, s4_mode, s5_mode, bad1, bad2 = raw_modes

        # Mapping dictionaries based on your provided table.
        # Note: Some mode values are only valid for S3; S4 and S5 have fewer options.
        s3_mapping = {
            0x00: "Default",
            0x01: "E-Stop",
            0x81: "E-Stop(Latching)",
            0x14: "Voltage Clamp",
            0x24: "RS485 Direction",
            0x84: "Encoder toggle",
            0x04: "Brake",
            0xE2: "Home(Auto)",
            0x62: "Home(User)",
            0xF2: "Home(Auto)/Limit(Fwd)",
            0x72: "Home(User)/Limit(Fwd)",
            0x12: "Limit(Fwd)",
            0x22: "Limit(Rev)",
            0x32: "Limit(Both)"
        }
        s4_mapping = {
            0x00: "Disabled",
            0x01: "E-Stop",
            0x81: "E-Stop(Latching)",
            0x14: "Voltage Clamp",
            0x04: "Brake",
            0x62: "Home(User)",
            0xF2: "Home(Auto)/Limit(Fwd)",
            0x72: "Home(User)/Limit(Fwd)",
            0x12: "Limit(Fwd)",
            0x22: "Limit(Rev)",
            0x32: "Limit(Both)"
        }
        s5_mapping = {
            0x00: "Disabled",
            0x01: "E-Stop",
            0x81: "E-Stop(Latching)",
            0x14: "Voltage Clamp",
            0x62: "Home(User)",
            0xF2: "Home(Auto)/Limit(Fwd)",
            0x72: "Home(User)/Limit(Fwd)"
        }

        return {
            "S3": s3_mapping.get(s3_mode, f"Unknown (0x{s3_mode:02X})"),
            "S4": s4_mapping.get(s4_mode, f"Unknown (0x{s4_mode:02X})"),
            "S5": s5_mapping.get(s5_mode, f"Unknown (0x{s5_mode:02X})")
        }

    # def read_duty_acceleration_settings(self):
    #     """
    #     Read M1 and M2 Duty Cycle Acceleration Settings.
        
    #     Command 81:
    #         Send: [Address, 81]
    #         Receive: [M1Accel(4 bytes), M2Accel(4 bytes), CRC(2 bytes)]
        
    #     Returns:
    #         A tuple (M1Accel, M2Accel) of acceleration settings as unsigned 4-byte integers.
    #     """
    #     cmd = 81
    #     return self._read(cmd, '>II')


class CRCException(Exception):
    pass

# Fault Framework for TREC's REC Ride Control Computer
    # Made by Aryan Kumar 

from enum import Enum
import logging
from typing import List
from Backend.iocontroller import IOController

MOTOR_MAX_SPEED = 3000

class FaultSeverity(Enum):
    LOW = 1      # Warning, does not stop ride
    MEDIUM = 2   # Requires operator intervention
    HIGH = 3     # Stops ride immediately (ESTOP)

class Fault:
    def __init__(self, code, message, severity: FaultSeverity):
        self.code = code
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity.name}] Fault {self.code}: {self.message}"
    

# Predefined faults
PREDEFINED_FAULTS = {
    101: Fault(101, "Emergency Stop Activated", FaultSeverity.HIGH),
    102: Fault(102, "Motor Controller Failure", FaultSeverity.HIGH),
    103: Fault(103, "Sensor Failure", FaultSeverity.MEDIUM),
    104: Fault(104, "Motor Overspeed", FaultSeverity.HIGH),
    105: Fault(105, "Sensor Mismatch", FaultSeverity.MEDIUM),
    106: Fault(106, "Motor Overheating", FaultSeverity.MEDIUM),
    107: Fault(107, "Unexpected Data Type", FaultSeverity.HIGH),
    108: Fault(108, "MC Communication Failure", FaultSeverity.HIGH),
    109: Fault(109, "MC Estop Triggered", FaultSeverity.HIGH)
}

class FaultManager:

    active_faults: List[Fault]

    def __init__(self):
        '''
        FaultManager is used to handle multiple faults for the RCC.

        Raise a fault by calling `raise_fault()`.
        '''
        self.log = logging.getLogger('FaultManager')
        self.active_faults = []
        self.faultRequiresEStop = False
        

    def raise_fault(self, fault: Fault):
        '''
        Used by other classes to raise a fault.

        Params:
            fault (Fault): The fault to be raised
        '''

        if fault not in self.active_faults:
            self.active_faults.append(fault)
            self.log_fault(fault)

            if fault.severity == FaultSeverity.HIGH:
                self.faultRequiresEStop = True


    def check_faults(self, io: IOController, rmc):
        """
        Checks for various fault conditions by executing one IO check per call in a round-robin manner.
        Must check in round robin because of how long io calls take
        """
        # Initialize round-robin mechanism if not already set up
        if not hasattr(self, 'current_check'):
            self.current_check = 0
            self.io_checks = [
                self.check_estop,
                self.check_motor_controller_status,
                self.check_sensor_failure,
                self.check_motor_speed,
                self.check_motor_overheat
            ]
        
        # Determine which check to run based on the current round-robin index
        check_to_run = self.io_checks[self.current_check]
        
        try:
            if check_to_run == self.check_estop:
                check_to_run(io)
            elif check_to_run == self.check_motor_controller_status:
                status = io.read_status()
                check_to_run(status)
            elif check_to_run == self.check_sensor_failure:
                actual_sensor_data = io.read_encoder()
                check_to_run(actual_sensor_data)
            elif check_to_run == self.check_motor_speed:
                actual_speed = io.read_speed()
                check_to_run(actual_speed, MOTOR_MAX_SPEED)
            elif check_to_run == self.check_motor_overheat:
                actual_temp1 = io.read_temp_sensor(1)
                actual_temp2 = io.read_temp_sensor(2)
                check_to_run(actual_temp1, actual_temp2)
        except Exception as e:
            self.raise_fault(PREDEFINED_FAULTS[108])
            return
        else:
            self.clear_fault(PREDEFINED_FAULTS[108].code)
        
        # Update round-robin index for the next call
        self.current_check = (self.current_check + 1) % len(self.io_checks)

    def check_estop(self, io: IOController):
        if io.read_estop():
            self.raise_fault(PREDEFINED_FAULTS[101])
        else:
            self.clear_fault(PREDEFINED_FAULTS[101].code)

    def check_motor_controller_status(self, status):
        if isinstance(status, str):
            if not status:
                self.raise_fault(PREDEFINED_FAULTS[108])
                return
            else:
                self.clear_fault(PREDEFINED_FAULTS[108].code)
            if "fault" in status.lower() or "error" in status.lower():
                self.raise_fault(PREDEFINED_FAULTS[102])
                self.log.warning(f"Motor controller status indicates fault: {status}")
            else:
                self.clear_fault(PREDEFINED_FAULTS[102].code)
            if "e-stop" in status.lower():
                self.raise_fault(PREDEFINED_FAULTS[109])
            else:
                self.clear_fault(PREDEFINED_FAULTS[109].code)

    def check_sensor_failure(self, actual_sensor_data):
        if actual_sensor_data == "None":
            self.raise_fault(PREDEFINED_FAULTS[103])
            self.log.warning("There is a sensor failure")
        else:
            self.clear_fault(PREDEFINED_FAULTS[103].code)

    def check_motor_speed(self, actual_speed, max_speed):
        if isinstance(actual_speed, int):
            speed_deviation = abs(actual_speed) - max_speed
            if speed_deviation > 5:
                self.raise_fault(PREDEFINED_FAULTS[104])
                self.log.warning(f"Speed deviation: Expected at or below {max_speed}. Got {actual_speed}.")
            else:
                self.clear_fault(PREDEFINED_FAULTS[104].code)
        else:
            self.raise_fault(PREDEFINED_FAULTS[107])

    def check_motor_overheat(self, actual_temp1, actual_temp2):
        if actual_temp1 and isinstance(actual_temp1, (float, int)):
            temp1_dev = actual_temp1 - 80
            if actual_temp1 > 80:
                self.raise_fault(PREDEFINED_FAULTS[106])
                self.log.warning(f"Motor 1 is Overheating by {temp1_dev}. Should be below 80.")
            else:
                self.clear_fault(PREDEFINED_FAULTS[106].code)
        if actual_temp2 and isinstance(actual_temp2, (float, int)):
            temp2_dev = actual_temp2 - 80
            if actual_temp2 > 80:
                self.raise_fault(PREDEFINED_FAULTS[106])
                self.log.warning(f"Motor 2 is Overheating by {temp2_dev}. Should be below 80.")
            else:
                self.clear_fault(PREDEFINED_FAULTS[106].code)

    def log_fault(self, fault: Fault):
        if fault.severity == FaultSeverity.LOW:
            self.log.warning(f"{fault}")
        elif fault.severity == FaultSeverity.MEDIUM:
            self.log.error(f"{fault}")
        elif fault.severity == FaultSeverity.HIGH:
            self.log.critical(f"{fault}")

    def clear_all_faults(self):
        self.active_faults.clear()


    def clear_fault(self, faultCodeToClear: int) -> bool:
        '''
        Clears a fault from the active list based on its fault code

        Returns:
            bool: Whether the fault was successfully cleared.
        '''
        # self.log.debug(f'Attempting to clear Fault #{faultCodeToClear}')

        for activeFault in self.active_faults[:]:  # Iterate over a copy
            if activeFault.code == faultCodeToClear:
                self.active_faults.remove(activeFault)
                self.log.info(f'Fault #{faultCodeToClear} Cleared')
                if activeFault.severity == FaultSeverity.HIGH:
                    # Check if any other HIGH severity faults remain
                    if not any(f.severity == FaultSeverity.HIGH for f in self.active_faults):
                        self.faultRequiresEStop = False

                return True
        return False
    
    def get_faults(self) -> dict:
        """Returns a dict of the active faults by fault code, including fault message and severity."""
        faults_dict = {}
        for fault in self.active_faults:
            faults_dict[fault.code] = {
                "message": fault.message,
                "severity": fault.severity.name
            }
        return faults_dict

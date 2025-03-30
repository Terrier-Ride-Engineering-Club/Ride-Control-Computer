# Fault Framework for TREC's REC Ride Control Computer
    # Made by Aryan Kumar 


from enum import Enum
import logging
from typing import List
from Backend.iocontroller import IOController

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
    104: Fault(104, "Speed Deviation Detected", FaultSeverity.MEDIUM),
    105: Fault(105, "Sensor Mismatch", FaultSeverity.MEDIUM),
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
        Checks for various fault conditions by comparing actual sensor and motor encoder data.
        """
        # Read actual values using the provided methods
        current_position = io.read_position()
        actual_sensor_data = io.read_encoder()  # Returns int {encoder1 pos}
        actual_speed = io.read_speed()
        max_speed = io.read_max_speed()

        # Fault Detection Logic
        
        # Emergency stop detection
        if io.read_estop():
            self.raise_fault(PREDEFINED_FAULTS[101])
        else:
            self.clear_fault(PREDEFINED_FAULTS[101].code)

        # Motor controller status check
        status = io.read_status()
        if not status or "fault" in status.lower() or "error" in status.lower():
            self.raise_fault(PREDEFINED_FAULTS[102])
            # self.log.error(f"Motor controller status indicates fault: {status}")
        else:
            self.clear_fault(PREDEFINED_FAULTS[102].code)
         

        # Sensor failure detection (Assumes None means failure)
        if actual_sensor_data is None:
            self.raise_fault(PREDEFINED_FAULTS[103])
        else:
            self.clear_fault(PREDEFINED_FAULTS[103].code)


        # Motor speed deviation detection   
        if actual_speed:         
            speed_deviation = abs(actual_speed) - max_speed
            if speed_deviation > 5:
                self.raise_fault(PREDEFINED_FAULTS[104])
                self.log.warning(f"Speed deviation: Expected -63 to 64, Got {actual_speed}")


        # Position mismatch detection
        if current_position:
            if isinstance(current_position, dict):
                deviation = 0 - abs(current_position.get('encoder'))
            else:
                deviation = current_position
            if deviation > 5:
                self.raise_fault(PREDEFINED_FAULTS[105])
                self.log.warning(f"Position mismatch detected! Expected: 0, Actual: {current_position}, Deviation: {deviation}")


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
# Fault Framework for TREC's REC Ride Control Computer
    # Made by Aryan Kumar 


from enum import Enum
import logging
from typing import List

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

    def log_fault(self, fault: Fault):
        if (fault.severity == FaultSeverity.LOW):
            self.log.warning(fault)
        elif (fault.severity == FaultSeverity.MEDIUM):
            self.log.error(fault)
        elif (fault.severity == FaultSeverity.HIGH):
            self.log.critical(fault)
        

    def raise_fault(self, fault: Fault):
        '''
        Used by other classes to raise a fault.

        Params:
            fault (Fault): The fault to be raised
        '''

        self.active_faults.append(fault)
        self.log_fault(fault)


        if fault.severity == FaultSeverity.HIGH:
            self.faultRequiresEStop = True

    def clear_all_faults(self):
        self.active_faults.clear()


    def clear_fault(self, faultCodeToClear: int) -> bool:
        '''
        Clears a fault from the active list based on its fault code

        Returns:
            bool: Whether the fault was successfully cleared.
        '''

        for activeFault in self.active_faults[:]:  # Iterate over a copy
            if activeFault.code == faultCodeToClear:
                self.active_faults.remove(activeFault)
                self.log.info(f'Fault #{faultCodeToClear} Cleared')
                return True
        return False

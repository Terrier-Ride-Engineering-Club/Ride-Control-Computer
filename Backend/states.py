from Backend.state import State
from Backend.event import *

class OffState(State):
    """
    Ride OFF State
    """

    def on_event(self, event):
        if type(event) is RideOnOffPressed:
            return self._transition(IdleState())
        return self

class IdleState(State):
    """
    Description of state
    """
    def on_event(self, event):
        if type(event) is RideOnOffPressed:
            return self._transition(OffState())
        if type(event) is EStopPressed:
            return self._transition(EstoppedState())
        if type(event) is DispatchedPressed:
            return self._transition(RunningState())
        return self
    
class EstoppedState(State):
    """
    EStopped State
    """
    def on_event(self, event):
        if type(event) is ResetPressed:
            return self._transition(ResettingState())
        return self

class ResettingState(State):
    """
    Description of state
    """
    def on_event(self, event):
        if type(event) is EStopPressed:
            return self._transition(EstoppedState())
        return self

class RunningState(State):
    """
    Description of state
    """
    def on_event(self, event):
        if type(event) is StopPressed:
            return self._transition(IdleState())
        if type(event) is EStopPressed:
            return self._transition(EstoppedState())
        return self

    

if __name__ == "__main__":
    originalState = OffState()
    newState = originalState.on_event(RideOnOffPressed())
    print(f"{originalState} -> {newState}")
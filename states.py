from state import State
from event import *

class OffState(State):
    """
    Ride OFF State
    """

    def on_event(self, event):
        if event is RideOnOffPressed:
            return IdleState()
        return self

class IdleState(State):
    """
    Description of state
    """
    def on_event(self, event):
        if event is RideOnOffPressed:
            return OffState()
        if event is EStopPressed:
            return EstoppedState()
        if event is DispatchedPressed:
            return RunningState()
        return self
    
class EstoppedState(State):
    """
    EStopped State
    """
    def on_event(self, event):
        if event is ResetPressed:
            return ResettingState()
        return self

class ResettingState(State):
    """
    Description of state
    """
    def on_event(self, event):
        if event is EStopPressed:
            return EstoppedState()
        return self

class RunningState(State):
    """
    Description of state
    """
    def on_event(self, event):
        if event is StopPressed:
            return IdleState()
        if event is EStopPressed:
            return EstoppedState()
        return self

    
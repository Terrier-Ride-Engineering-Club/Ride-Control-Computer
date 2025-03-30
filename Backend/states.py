from Backend.state import State
from Backend.event import *
import time
import threading

class OffState(State):
    """
    Ride OFF State

    Includes a timer b/c there is only one event to enter/exit this state.
    If the timer hasn't reached the threshold, the RideOnOffPressed event will
    do nothing.
    
    The `disable_timer` flag can be used to disable this timer.
    """

    def __init__(self,disable_timer = False):
        super().__init__()
        self.enter_time = time.time()
        self.min_off_duration = 2.0  # seconds
        self.disable_timer = disable_timer

    def on_event(self, event):
        if isinstance(event, RideOnOffPressed):
            if time.time() - self.enter_time >= self.min_off_duration or self.disable_timer:
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

    done_resetting = False

    def _on_enter(self):
        
        def reset_exit_timer_thread():
            enter_time = time.time()
            reset_time = 2
            while True:
                if time.time() - enter_time >= reset_time:
                    self.done_resetting = True
                else:
                    time.sleep(0.1)
        threading.Thread(target=reset_exit_timer_thread, daemon=True).start()
        
    def on_event(self, event):
        if type(event) is EStopPressed:
            return self._transition(EstoppedState())
        elif self.done_resetting:
            return self._transition(IdleState())
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
from __future__ import annotations  # Ensures forward references work in Python 3.9+

class State(object):
    """
    We define a state object which provides some utility functions for the
    individual states within the state machine.
    """

    def __init__(self):
        print(f'Processing current state: {str(self)}')

    def on_event(self, event) -> State:
        """
        Handle events that are delegated to this State.

        Returns:
            State - The state that we are entering.
        """
        raise NotImplementedError('Must Implement on_event in state subclass')

    def __repr__(self):
        """
        Leverages the __str__ method to describe the State.
        """
        return self.__str__()

    def __str__(self):
        """
        Returns the name of the State.
        """
        return self.__class__.__name__


#mystates.py
class OffState(State):
    """
    Description of state
    """

    def on_event(self, event):
        if event == 'estop_pressed':
            return EstoppedState()
        return self

class EstoppedState(State):
    """
    Description of state
    """
    def on_event(self, event):
        pass

class IdleState(State):
    """
    Description of state
    """
    def on_event(self, event):
        pass
    

class ResettingState(State):
    """
    Description of state
    """
    def on_event(self, event):
        pass

class RunningState(State):
    """
    Description of state
    """
    def on_event(self, event):
        pass

    
# simple_device.py

class RideControlComputerMachine(object):
    """ 
    A Ride Control Computer State Machine
    """

    def __init__(self):
        """ Initialize the components. """

        # Start with a default state.
        self.state = OffState()

    def on_event(self, event):
        """
        This is the bread and butter of the state machine. Incoming events are
        delegated to the given states which then handle the event. The result is
        then assigned as the new state.
        """

        # The next state will be the result of the on_event function.
        self.state = self.state.on_event(event)

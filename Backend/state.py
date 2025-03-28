# State Machine class for TREC's REC Ride Control Computer
    # Jackson Justus (jackjust@bu.edu)

from __future__ import annotations  # Ensures forward references work in Python 3.9+
from Backend.event import Event

class State():
    """
    We define a state object which provides some utility functions for the
    individual states within the state machine.
    """

    def __init__(self):
        print(f'Processing current state: {str(self)}')

    def on_event(self, event: Event) -> State:
        """
        Handle events that are delegated to this State.
        Should be called by the state machine when an event occurs (EX: an IO action).
        
        If a state transition is required by the event passed in, 
        this method will call _on_exit() for this state, _on_enter() for the new state,
        and then return the new state.

        Returns:
            State - The new state that we are entering. Self if no transition is required
        """
        raise NotImplementedError('Must Implement on_event in state subclass')
    
    def run(self):
        """
        Logic to run while the RCC is in this state.
        """
        pass

    def _transition(self, new_state: 'State') -> 'State':
        """
        If transitioning to a new state, run the exit logic on the current
        state and the enter logic on the new state.
        """
        if new_state is not self:
            self._on_exit()
            new_state._on_enter()
        return new_state

    def _on_enter(self):
        """
        Logic to execute when entering this state.
        """
        pass

    def _on_exit(self):
        """
        Logic to execute when exiting this state.
        """
        pass

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



# class RideControlComputerMachine(object):
#     """ 
#     A Ride Control Computer State Machine
#     """

#     def __init__(self):
#         """ Initialize the components. """

#         # Start with a default state.
#         self.state = OffState()

#     def on_event(self, event):
#         """
#         This is the bread and butter of the state machine. Incoming events are
#         delegated to the given states which then handle the event. The result is
#         then assigned as the new state.
#         """

#         # The next state will be the result of the on_event function.
#         self.state = self.state.on_event(event)

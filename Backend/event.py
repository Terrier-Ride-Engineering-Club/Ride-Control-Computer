# Event class for TREC's REC Ride Control Computer
    # Jackson Justus (jackjust@bu.edu)

class Event:
    """
    Events are simple object which happen when an IO Action takes place.
    The states use events to determine which state to transition to.
    """
    pass

    def __str__(self):
        """
        Returns the name of the Event.
        """
        return self.__class__.__name__
    
    def __eq__(self, other):
        return isinstance(other, self.__class__)

class RideOn(Event):
    """Happens when the ride on/off is switched to on positon."""
    pass

class RideOff(Event):
    """Happens when the ride on/off is switched to off positon."""
    pass

class DispatchedPressed(Event):
    """Happens when both of the ride dispatch buttons are pressed."""
    pass

class StopPressed(Event):
    """Happens when the stop button is pressed."""
    pass

class EStopPressed(Event):
    """Happens when the E-Stop button is pressed."""
    pass

class ResetPressed(Event):
    """Happens when the Reset button is pressed."""
    pass
import unittest
from unittest.mock import patch, call, MagicMock

# Import states and events
from Backend.states import OffState, IdleState, EstoppedState, ResettingState, RunningState
from event import RideOnOffPressed, EStopPressed, DispatchedPressed, ResetPressed, StopPressed

class TestStateTransitions(unittest.TestCase):

    def test_on_exit_called(self):
        originalState = OffState()
        originalState._on_exit = MagicMock()
        newState = originalState.on_event(RideOnOffPressed())
        originalState._on_exit.assert_called_once()

    def test_on_enter_called(self):
        originalState = OffState()
        IdleState._on_enter = MagicMock()
        originalState.on_event(RideOnOffPressed())
        IdleState._on_enter.assert_called_once()

    def test_off_state_transitions(self):
        originalState = OffState()
        self.assertIsInstance(originalState.on_event(RideOnOffPressed()), IdleState)
        originalState = OffState()
        self.assertIsInstance(originalState.on_event(DispatchedPressed()), OffState)
        originalState = OffState()
        self.assertIsInstance(originalState.on_event(EStopPressed()), OffState)
        originalState = OffState()
        self.assertIsInstance(originalState.on_event(StopPressed()), OffState)
        originalState = OffState()
        self.assertIsInstance(originalState.on_event(ResetPressed()), OffState)

    def test_idle_state_transitions(self):
        originalState = IdleState()
        self.assertIsInstance(originalState.on_event(RideOnOffPressed()), OffState)
        originalState = IdleState()
        self.assertIsInstance(originalState.on_event(DispatchedPressed()), RunningState)
        originalState = IdleState()
        self.assertIsInstance(originalState.on_event(EStopPressed()), EstoppedState)
        originalState = IdleState()
        self.assertIsInstance(originalState.on_event(StopPressed()), IdleState)
        originalState = IdleState()
        self.assertIsInstance(originalState.on_event(ResetPressed()), IdleState)

    def test_running_state_transitions(self):
        originalState = RunningState()
        self.assertIsInstance(originalState.on_event(RideOnOffPressed()), RunningState)
        originalState = RunningState()
        self.assertIsInstance(originalState.on_event(DispatchedPressed()), RunningState)
        originalState = RunningState()
        self.assertIsInstance(originalState.on_event(EStopPressed()), EstoppedState)
        originalState = RunningState()
        self.assertIsInstance(originalState.on_event(StopPressed()), IdleState)
        originalState = RunningState()
        self.assertIsInstance(originalState.on_event(ResetPressed()), RunningState)

    def test_estop_state_transitions(self):
        originalState = EstoppedState()
        self.assertIsInstance(originalState.on_event(RideOnOffPressed()), EstoppedState)
        originalState = EstoppedState()
        self.assertIsInstance(originalState.on_event(DispatchedPressed()), EstoppedState)
        originalState = EstoppedState()
        self.assertIsInstance(originalState.on_event(EStopPressed()), EstoppedState)
        originalState = EstoppedState()
        self.assertIsInstance(originalState.on_event(StopPressed()), EstoppedState)
        originalState = EstoppedState()
        self.assertIsInstance(originalState.on_event(ResetPressed()), ResettingState)

    def test_resetting_state_transitions(self):
        originalState = ResettingState()
        self.assertIsInstance(originalState.on_event(RideOnOffPressed()), ResettingState)
        originalState = ResettingState()
        self.assertIsInstance(originalState.on_event(DispatchedPressed()), ResettingState)
        originalState = ResettingState()
        self.assertIsInstance(originalState.on_event(EStopPressed()), EstoppedState)
        originalState = ResettingState()
        self.assertIsInstance(originalState.on_event(StopPressed()), ResettingState)
        originalState = ResettingState()
        self.assertIsInstance(originalState.on_event(ResetPressed()), ResettingState)


if __name__ == '__main__':
    unittest.main()
import unittest
import time
import threading

# Attempt to import IdleState from your Backend.states module.
# If unavailable (e.g. for testing), we create a dummy IdleState.
try:
    from Backend.states import IdleState
except ImportError:
    class IdleState:
        pass

# A dummy non-idle state for testing the rejection behavior.
class FakeNonIdleState:
    pass

# Fake IO controller to capture motor move calls.
class FakeIO:
    def __init__(self):
        self.move_calls = []

    def move_motor(self, direction):
        self.move_calls.append(direction)

    # Add this method to capture commands from send_motor_command
    def send_motor_command(self, command):
        self.move_calls.append(command)

# Fake RCC (Ride Control Computer) with a state and an IO controller.
class FakeRCC:
    def __init__(self, state):
        self.state = state
        self.io = FakeIO()

# Import the RideWebServer from your project.
# Adjust the import path as necessary to reflect your project structure.
from web.backend.webserver import RideWebServer

class TestCreepMotor(unittest.TestCase):
    def setUp(self):
        # Initialize FakeRCC in Idle state.
        self.fake_rcc = FakeRCC(IdleState())
        self.server = RideWebServer(self.fake_rcc)

    def test_creep_motor_idle_state(self):
        # Call creep_motor when RCC state is Idle.
        response, status = self.server.creep_motor(forward=True)
        self.assertEqual(status, 200)
        self.assertEqual(response.get("message"), "Motor creeping")
        self.assertTrue(self.server.creep_active)
        
        # Wait long enough for the creep loop to timeout (0.5s + extra buffer)
        time.sleep(0.7)
        self.assertFalse(self.server.creep_active)
        # Ensure that move_motor was called at least once with True (forward)
        self.assertTrue(len(self.fake_rcc.io.move_calls) > 0)
        self.assertTrue(all(call.get('direction') == 'fwd' for call in self.fake_rcc.io.move_calls if isinstance(call, dict)))

    def test_creep_motor_non_idle_state(self):
        # Set RCC state to a non-idle state.
        self.fake_rcc.state = FakeNonIdleState()
        response, status = self.server.creep_motor(forward=True)
        self.assertEqual(status, 403)
        self.assertEqual(response.get("message"), "Action forbidden: Ride not in Idle.")

if __name__ == '__main__':
    unittest.main()
# Testing file for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import unittest
from unittest.mock import MagicMock, patch
import time
import threading
from ridecontrolcomputer import RideControlComputer, State

class TestRideControlComputer(unittest.TestCase):

    def setUp(self):
        """Initialize a new Ride Control Computer instance before each test."""
        self.rcc = RideControlComputer()
        self.rcc.initialize()
        # Default sensor mocks
        self.rcc.io.read_estop = MagicMock(return_value=False)
        self.rcc.io.read_on_switch = MagicMock(return_value=False)
        self.rcc.io.read_reset_switch = MagicMock(return_value=False)

    # Existing Tests

    def test_initial_state(self):
        """Verify the initial state is IDLE."""
        self.assertEqual(self.rcc.state, State.IDLE)

    def test_state_transition_to_running(self):
        """Simulate turning on the ride and ensure it transitions to RUNNING."""
        self.rcc.io.read_on_switch.return_value = True  # Simulate switch press
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.RUNNING)

    def test_emergency_stop(self):
        """Simulate an emergency stop and ensure state changes to ESTOPPED."""
        self.rcc.io.read_estop.return_value = True  # Simulate ESTOP activation
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.ESTOPPED)

    def test_reset_after_estop(self):
        """Simulate resetting after an emergency stop."""
        self.rcc.io.read_estop.return_value = True  # Trigger ESTOP
        self.rcc.update()
        # Now simulate releasing the estop and activating the reset switch
        self.rcc.io.read_estop.return_value = False  
        self.rcc.io.read_reset_switch.return_value = True  
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.RESETTING)
        # Release the reset switch
        self.rcc.io.read_reset_switch.return_value = False  
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.IDLE)

    def test_state_change_logging(self):
        """Verify state change logging output."""
        with self.assertLogs() as captured_logs:
            # Transition from IDLE -> RUNNING -> ESTOPPED
            self.rcc.io.read_on_switch.return_value = True
            self.rcc.update()  # should go to RUNNING
            self.rcc.io.read_estop.return_value = True
            self.rcc.update()  # should go to ESTOPPED
        # Check for expected log substrings
        self.assertTrue(any("IDLE" in log and "RUNNING" in log for log in captured_logs.output))
        self.assertTrue(any("RUNNING" in log and "ESTOPPED" in log for log in captured_logs.output))

    def test_update_loop_timing(self):
        """
        Measure update loop timing to ensure it's able to run at least 60 times per second.
        """
        start_time = time.time()
        for _ in range(80):
            self.rcc.update()
        elapsed_time = time.time() - start_time
        expected_time = 1  # 80 updates should take less than 1 second under normal conditions.
        self.assertLess(elapsed_time, expected_time)

    # Additional Tests

    def test_multiple_sequential_state_transitions(self):
        """Simulate a full cycle: IDLE -> RUNNING -> ESTOPPED -> RESETTING -> IDLE."""
        # IDLE to RUNNING
        self.rcc.io.read_on_switch.return_value = True
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.RUNNING)
        # RUNNING to ESTOPPED
        self.rcc.io.read_on_switch.return_value = False
        self.rcc.io.read_estop.return_value = True
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.ESTOPPED)
        # ESTOPPED to RESETTING
        self.rcc.io.read_estop.return_value = False
        self.rcc.io.read_reset_switch.return_value = True
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.RESETTING)
        # RESETTING back to IDLE
        self.rcc.io.read_reset_switch.return_value = False
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.IDLE)

    def test_simultaneous_sensor_activation(self):
        """If both on switch and estop are active, ESTOP should take precedence."""
        self.rcc.io.read_on_switch.return_value = True
        self.rcc.io.read_estop.return_value = True
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.ESTOPPED)

    def test_debounce_noise_handling(self):
        """Simulate rapid toggling (bounce) of the on switch and ensure only a stable signal transitions state."""
        # Rapidly change on switch values several times
        for value in [False, True, False, True, True]:
            self.rcc.io.read_on_switch.return_value = value
            self.rcc.update()
        # If the final stable state is True, we should be in RUNNING.
        self.assertEqual(self.rcc.state, State.RUNNING)

    def test_boundary_timing_for_sensor_inputs(self):
        """Simulate a very short on switch pulse that may be below the debounce threshold."""
        self.rcc.io.read_on_switch.return_value = True
        self.rcc.update()
        # Immediately set back to false
        self.rcc.io.read_on_switch.return_value = False
        self.rcc.update()
        # Depending on the debounce implementation, the state may either remain RUNNING or revert; check for a safe state.
        self.assertIn(self.rcc.state, [State.RUNNING, State.IDLE])

    def test_stress_update_cycles(self):
        """Run the update method for a large number of cycles to check for resource issues or state corruption."""
        for _ in range(10000):
            self.rcc.update()
        # At the end, ensure the system is still in a valid state (one of the defined states).
        self.assertIn(self.rcc.state, [State.IDLE, State.RUNNING, State.ESTOPPED, State.RESETTING])

    def test_concurrent_sensor_input_simulation(self):
        """Simulate concurrent sensor updates using threads to test for race conditions."""
        def update_sensor(sensor_name, values, delay=0.001):
            for val in values:
                getattr(self.rcc.io, sensor_name).return_value = val
                self.rcc.update()
                time.sleep(delay)

        thread1 = threading.Thread(target=update_sensor, args=("read_on_switch", [False, True, False, True]))
        thread2 = threading.Thread(target=update_sensor, args=("read_estop", [False, False, True, False]))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        # Check that the final state is one of the defined states.
        self.assertIn(self.rcc.state, [State.IDLE, State.RUNNING, State.ESTOPPED, State.RESETTING])


    def test_multiple_updates_in_rapid_succession(self):
        """Call update() multiple times in rapid succession and check that state transitions remain valid."""
        for _ in range(10):
            self.rcc.update()
        self.assertIn(self.rcc.state, [State.IDLE, State.RUNNING, State.ESTOPPED, State.RESETTING])

    def test_state_persistence_after_full_cycle(self):
        """After a complete cycle, verify that any state-dependent properties are reset appropriately."""
        # Run through a full cycle
        self.rcc.io.read_on_switch.return_value = True
        self.rcc.update()  # IDLE -> RUNNING
        self.rcc.io.read_on_switch.return_value = False
        self.rcc.io.read_estop.return_value = True
        self.rcc.update()  # RUNNING -> ESTOPPED
        self.rcc.io.read_estop.return_value = False
        self.rcc.io.read_reset_switch.return_value = True
        self.rcc.update()  # ESTOPPED -> RESETTING
        self.rcc.io.read_reset_switch.return_value = False
        self.rcc.update()  # RESETTING -> IDLE
        # Here we assume the system resets its state-dependent properties (if any)
        self.assertEqual(self.rcc.state, State.IDLE)

    def test_sensor_recovery_timing(self):
        """Simulate a sensor error that recovers and check that the system correctly resumes operation."""
        # Activate estop, then deactivate quickly
        self.rcc.io.read_estop.return_value = True
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.ESTOPPED)
        # Sensor recovers
        self.rcc.io.read_estop.return_value = False
        self.rcc.io.read_reset_switch.return_value = True
        self.rcc.update()
        # Depending on your design, this may transition to RUNNING or another state.
        self.assertEqual(self.rcc.state, State.RESETTING)

        self.rcc.io.read_reset_switch.return_value = False
        self.rcc.update()
        self.assertEqual(self.rcc.state, State.IDLE)

    def test_update_without_initialization(self):
        """Ensure that calling update before initialize() is handled gracefully."""
        new_rcc = RideControlComputer()
        # Do not call initialize() on purpose.
        # new_rcc.io = type("DummyIO", (), {})()  # Create a dummy IO object
        # new_rcc.io.read_estop = MagicMock(return_value=False)
        # new_rcc.io.read_on_switch = MagicMock(return_value=False)
        # new_rcc.io.read_reset_switch = MagicMock(return_value=False)
        try:
            new_rcc.update()
        except Exception as e:
            return
        self.fail(f"update() didn't raise an exception when called without initialization: {e}")

    def test_repeated_emergency_stop_and_reset(self):
        """Cycle emergency stop and reset several times to check for consistency."""
        for _ in range(5):
            self.rcc.io.read_estop.return_value = True
            self.rcc.update()
            self.assertEqual(self.rcc.state, State.ESTOPPED)
            self.rcc.io.read_estop.return_value = False
            self.rcc.io.read_reset_switch.return_value = True
            self.rcc.update()
            self.assertEqual(self.rcc.state, State.RESETTING)
            self.rcc.io.read_reset_switch.return_value = False
            self.rcc.update()
            self.assertEqual(self.rcc.state, State.IDLE)

    def test_long_term_resource_utilization(self):
        """Run update cycles for an extended period and check for stability (this test is lightweight)."""
        for _ in range(1000):
            self.rcc.update()
        # Verify state is one of the valid states.
        self.assertIn(self.rcc.state, [State.IDLE, State.RUNNING, State.ESTOPPED, State.RESETTING])

    def test_reset_switch_boundary_condition(self):
        """Simulate a reset switch press that is too short to trigger a full RESETTING state."""
        # Trigger ESTOP first
        self.rcc.io.read_estop.return_value = True
        self.rcc.update()
        # Release estop and simulate a very brief reset switch press
        self.rcc.io.read_estop.return_value = False
        self.rcc.io.read_reset_switch.return_value = True
        self.rcc.update()
        # Immediately release the reset switch (simulate too short a press)
        self.rcc.io.read_reset_switch.return_value = False
        self.rcc.update()
        # Depending on your implementation, the state might either remain in RESETTING or revert safely.
        self.assertIn(self.rcc.state, [State.RESETTING, State.IDLE])


if __name__ == '__main__':
    unittest.main()
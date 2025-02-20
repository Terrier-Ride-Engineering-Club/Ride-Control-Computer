# Testing file for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

#TODO: IMPLEMENT

    # def test_unexpected_sensor_values(self):
    #     """Simulate sensor methods returning unexpected values (like None) and ensure safe behavior."""
    #     self.rcc.io.read_estop.return_value = None
    #     self.rcc.io.read_on_switch.return_value = "unexpected"
    #     try:
    #         self.rcc.update()
    #     except Exception as e:
    #         self.fail(f"update() raised an exception on unexpected sensor values: {e}")
    #     # Assuming safe default behavior, state should remain IDLE.
    #     self.assertEqual(self.rcc.state, State.IDLE)

    # def test_error_handling_in_external_function_calls(self):
    #     """Simulate an exception in an external function called during state transition."""
    #     # Assume that during the transition to RUNNING an external function is called.
    #     # Patch a hypothetical external function used in update().
    #     with patch('ridecontrolcomputer.read_on_switch', side_effect=Exception("Simulated error")):
    #         self.rcc.io.read_on_switch.return_value = True
    #         try:
    #             self.rcc.update()
    #         except Exception as e:
    #             self.fail(f"update() did not handle external function exception gracefully: {e}")
    #         # After exception handling, the state should remain safe.
    #         self.assertIn(self.rcc.state, [State.IDLE, State.RUNNING])
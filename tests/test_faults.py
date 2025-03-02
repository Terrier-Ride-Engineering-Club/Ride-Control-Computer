# Testing file for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import unittest
from Backend.faults import Fault, FaultManager, FaultSeverity
from unittest.mock import MagicMock

class TestFaultSeverity(unittest.TestCase):
    def test_fault_severity_values(self):
        # Ensure the enum values are set as expected.
        self.assertEqual(FaultSeverity.LOW.value, 1)
        self.assertEqual(FaultSeverity.MEDIUM.value, 2)
        self.assertEqual(FaultSeverity.HIGH.value, 3)

class TestFault(unittest.TestCase):
    def test_fault_str(self):
        # Test the string representation of a Fault instance.
        fault = Fault(code=101, message="Test fault", severity=FaultSeverity.LOW)
        expected_str = "[LOW] Fault 101: Test fault"
        self.assertEqual(str(fault), expected_str)

    def test_fault_attributes(self):
        # Test that the Fault attributes are correctly assigned.
        fault = Fault(code=202, message="Warning", severity=FaultSeverity.MEDIUM)
        self.assertEqual(fault.code, 202)
        self.assertEqual(fault.message, "Warning")
        self.assertEqual(fault.severity, FaultSeverity.MEDIUM)

class TestFaultManager(unittest.TestCase):

    def setUp(self):
        # Instantiate a FaultManager and override its logger with a MagicMock
        self.fm = FaultManager()
        self.fm.log = MagicMock()

    def test_raise_fault_low(self):
        # Test that a LOW severity fault is added and logged correctly.
        fault = Fault(code=1, message="Low severity", severity=FaultSeverity.LOW)
        self.fm.raise_fault(fault)
        self.assertIn(fault, self.fm.active_faults)
        self.fm.log.warning.assert_called_once_with(fault)
        self.assertFalse(self.fm.faultRequiresEStop)

    def test_raise_fault_medium(self):
        # Test that a MEDIUM severity fault is added and logged correctly.
        fault = Fault(code=2, message="Medium severity", severity=FaultSeverity.MEDIUM)
        self.fm.raise_fault(fault)
        self.assertIn(fault, self.fm.active_faults)
        self.fm.log.error.assert_called_once_with(fault)
        self.assertFalse(self.fm.faultRequiresEStop)

    def test_raise_fault_high(self):
        # Test that a HIGH severity fault is added, logged, and sets the ESTOP flag.
        fault = Fault(code=3, message="High severity", severity=FaultSeverity.HIGH)
        self.fm.raise_fault(fault)
        self.assertIn(fault, self.fm.active_faults)
        self.fm.log.critical.assert_called_once_with(fault)
        self.assertTrue(self.fm.faultRequiresEStop)

    def test_clear_fault_success(self):
        # Test that clear_fault successfully removes a fault that exists.
        fault = Fault(code=4, message="Test fault", severity=FaultSeverity.LOW)
        self.fm.raise_fault(fault)
        result = self.fm.clear_fault(4)
        self.assertTrue(result)
        self.assertNotIn(fault, self.fm.active_faults)
        # Check that the info log was called with the appropriate message.
        self.fm.log.info.assert_called_with("Fault #4 Cleared")

    def test_clear_fault_failure(self):
        # Test that clear_fault returns False when the fault is not found.
        fault = Fault(code=5, message="Test fault", severity=FaultSeverity.LOW)
        self.fm.raise_fault(fault)
        result = self.fm.clear_fault(999)  # A non-existent fault code.
        self.assertFalse(result)
        self.assertIn(fault, self.fm.active_faults)

    def test_clear_all_faults(self):
        # Test that clear_all_faults properly empties the active faults list.
        fault1 = Fault(code=6, message="Fault one", severity=FaultSeverity.LOW)
        fault2 = Fault(code=7, message="Fault two", severity=FaultSeverity.MEDIUM)
        self.fm.raise_fault(fault1)
        self.fm.raise_fault(fault2)
        self.fm.clear_all_faults()
        self.assertEqual(len(self.fm.active_faults), 0)

if __name__ == '__main__':
    unittest.main()
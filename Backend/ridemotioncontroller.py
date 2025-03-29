# Ride Motion Controller for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import json
import time

RIDE_CONFIG_FILE_PATH = "rideconfig.json"


class RideMotionController:
    def __init__(self):
        self.config = self.load_config()
        self.current_phase_index = None
        self.current_instruction = None
        self.cycle_start_time = 0


    def load_config(self) -> dict:
        with open(RIDE_CONFIG_FILE_PATH, "r") as file:
            config: dict = json.load(file).get('ride_cycles')
            # Iterate over each cycle and its instructions
            for cycle_name, instructions in config.items():
                for instr in instructions:
                    self.validate_instruction(instr)
            return config
        
        
    def validate_instruction(self, instr):
        """
        Validate that the instruction dictionary contains valid parameters.
        Raises a ValueError if not valid.
        """
        if not isinstance(instr, dict):
            print("Invalid instruction: not a dictionary.")
            print(f'{instr}')
            return False

        name = instr.get("name")
        if name == "Move":
            required_keys = {"duration": int, "speed": str, "direction": str, "accel": str}
            # Validate each required key
            for key, expected_type in required_keys.items():
                if key not in instr:
                    raise ValueError(f"Invalid Move instruction: Missing key '{key}'.")
                # Check if duration can also be a float
                if key == "duration":
                    if not isinstance(instr[key], (int, float)):
                        raise ValueError(f"Invalid Move instruction: '{key}' should be a number.")
                elif not isinstance(instr[key], expected_type):
                    raise ValueError(f"Invalid Move instruction: '{key}' should be of type {expected_type.__name__}.")
            return True

        elif name == "Position":
            required_keys = {"duration": int, "pos": str}
            for key, expected_type in required_keys.items():
                if key not in instr:
                    raise ValueError(f"Invalid Position instruction: Missing key '{key}'.")
                if key == "duration":
                    if not isinstance(instr[key], (int, float)):
                        raise ValueError(f"Invalid Position instruction: '{key}' should be a number.")
                elif not isinstance(instr[key], expected_type):
                    raise ValueError(f"Invalid Position instruction: '{key}' should be of type {expected_type.__name__}.")
            return True

        else:
            print(f"Unknown instruction type: {name}")
            return False

    def start_cycle(self):
        cycle = self.get_cycle(1)
        if cycle is None or len(cycle) == 0:
            print("No instructions found for cycle 1")
            return None
        self.current_phase_index = 0
        self.current_instruction = cycle[self.current_phase_index]
        self.cycle_start_time = time.time()
        return self.current_instruction

    def update(self):
        """
        Updates the Ride Motion Controller. If a cycle is currently active,
        this function will return an instruction for the motor when a new one
        is needed, according to the duration set by the current instruction.
        """
        if self.current_instruction is None:
            return self.start_cycle()

        # Check if the duration for the current instruction has passed
        elapsed_time = time.time() - self.cycle_start_time
        if elapsed_time >= self.current_instruction.get("duration", 0):
            # Move to the next instruction in cycle 1
            cycle = self.get_cycle(1)
            self.current_phase_index += 1
            if self.current_phase_index >= len(cycle):
                # End of cycle: finish the cycle and return None
                self.finish()
                return None
            else:
                self.current_instruction = cycle[self.current_phase_index]
                self.cycle_start_time = time.time()
                return self.current_instruction

        # Not yet time for a new instruction, return None.
        return None

    def finish(self):
        # End of ride cycle actions
        self.current_phase_index = None
        self.current_instruction = None

    def get_cycle(self, cycle_number: int):
        return self.config.get(f'cycle_{cycle_number}')


if __name__ == '__main__':

    r = RideMotionController()

    # print(r.config)
    while True:
        time.sleep(1)
        print(r.update())
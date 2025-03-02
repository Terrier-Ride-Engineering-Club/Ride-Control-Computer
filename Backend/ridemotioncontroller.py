# Ride Motion Controller for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import json

RIDE_CONFIG_FILE_PATH = "rideconfig.json"

class RidePhase:
    def __init__(self, config):
        self.config = config  # Configuration for the phase

    def enter(self):
        # Initialization when the phase starts
        print(f"Entering phase: {self.config.get('name', 'Unnamed Phase')}")

    def execute(self, dt):
        # Instead of directly commanding the IO controller,
        # generate and return an instruction.
        # For example, use the config to generate a speed and duration.
        instruction = {
            "phase": self.config.get("name", "Unnamed Phase"),
            "motor_speed": self.config.get("motor_speed", 0),
            "duration": self.config.get("duration", 0),
            "dt": dt  # Pass along the delta time if needed
        }
        return instruction

    def is_complete(self):
        # Return True when this phase is done.
        # This could be based on elapsed time or some sensor feedback.
        return False

    def exit(self):
        # Cleanup when phase finishes
        print(f"Exiting phase: {self.config.get('name', 'Unnamed Phase')}")

class RideMotionController:
    def __init__(self):
        self.config = self.load_config()
        self.phases = self.load_phases()
        self.current_phase_index = None
        self.current_instruction = None


    def load_config(self):
        with open(RIDE_CONFIG_FILE_PATH, "r") as file:
            return json.load(file)

    def load_phases(self):
        phases = []
        for phase_config in self.config.get("ride_phases", []):
            phases.append(RidePhase(phase_config))
        return phases

    def start(self):
        if self.phases:
            self.current_phase_index = 0
            self.phases[0].enter()

    def update(self, dt):
        if self.current_phase_index is None:
            return None  # Ride not started or already finished

        current_phase = self.phases[self.current_phase_index]
        # Generate an instruction rather than executing motor commands directly
        instruction = current_phase.execute(dt)
        self.current_instruction = instruction

        if current_phase.is_complete():
            current_phase.exit()
            self.current_phase_index += 1
            if self.current_phase_index < len(self.phases):
                self.phases[self.current_phase_index].enter()
            else:
                self.finish()

        return instruction

    def finish(self):
        # End of ride cycle actions
        self.current_phase_index = None
        self.current_instruction = None
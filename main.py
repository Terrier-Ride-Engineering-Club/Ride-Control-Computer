# Main file for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

r'''
Notes for members:
    INITIAL SETUP:
    1. Make sure you have the most recent version of python installed
        python3 --version => make sure it says 3.13.2
    2. Naviate to your project directory:
        cd path\to\your\project
    3. Make sure you have created a virtual environment by running:
        python3 -m venv venv
    4. Activate the virtual environment by running:
        [MacOS/Linux]: source venv/bin/activate
        [Windows]: venv\Scripts\activate
    5. Install required dependicies by running:
        pip install -r requirements.txt

    TO RUN PROJECT:
    3. Activate the virtual environment by running:
        [MacOS/Linux]: source venv/bin/activate
        [Windows]: venv\Scripts\activate
    4. To run a specific file:
        python -m main
'''

# Native modules
import threading
import logging
from roboclaw import RoboClaw
# Custom modules
from ridecontrolcomputer import RideControlComputer


# Initialize Ride Control Computer
RCC = RideControlComputer()
RCC.initialize()
RCC.start()


# Start the RCC Thread
# rccThread = threading.Thread(target=RCC.start, daemon=True) #daemon=quit once main program stops
# rccThread.start()


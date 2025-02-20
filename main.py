# Main file for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

r'''
Notes for members:
    INITIAL SETUP:
    1. Naviate to your project directory:
        cd path\to\your\project
    2. Make sure you have created a virtual environment by running:
        python -m venv venv
    3. Install required dependicies by running:
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
# Custom modules
from ridecontrolcomputer import RideControlComputer


# Initialize Ride Control Computer
RCC = RideControlComputer()
RCC.initialize()
RCC.start()


# Start the RCC Thread
# rccThread = threading.Thread(target=RCC.start, daemon=True) #daemon=quit once main program stops
# rccThread.start()


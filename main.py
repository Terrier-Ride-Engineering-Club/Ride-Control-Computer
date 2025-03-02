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
import logging
# from roboclaw import RoboClaw
# Custom modules
from ridecontrolcomputer import RideControlComputer
from web.backend.webserver import RideWebServer

# --- Configure Logging ---
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
LOG_FILE = "ride_control.log"

logging.basicConfig(
    level=logging.WARNING,  # Change to DEBUG for more details
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),  # Log to a file
        logging.StreamHandler()  # Log to the console
    ]
)

# Initialize RCC
rcc = RideControlComputer()
rcc.initialize()

# Start Web Server
web_server = RideWebServer(rcc)
web_server.run()

# Start RCC Main Loop
rcc.start()  # This will keep running while the web server runs in parallel


# Start the RCC Thread
# rccThread = threading.Thread(target=RCC.start, daemon=True) #daemon=quit once main program stops
# rccThread.start()


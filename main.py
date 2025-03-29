# Main file for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

r'''
Notes for members:
    INITIAL SETUP:
    1. Make sure you have the correct version of python installed
        python3 --version => make sure it says 3.11.2 
        https://www.python.org/downloads/release/python-3112/
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

# --- Configure Logging ---
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"
LOG_FILE = "ride_control.log"
logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
    handlers=[logging.FileHandler(LOG_FILE)])  # Log to a file
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
console_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console_handler)  # Log to the console (INFO or higher)


# --- Import Custom Modules ---
from ridecontrolcomputer import RideControlComputer
from web.backend.webserver import RideWebServer



# Initialize RCC
rcc = RideControlComputer()
rcc.initialize()

# Start Web Server
web_server = RideWebServer(rcc)
web_server.run()

# Start RCC Main Loop
rcc.start()  # This will keep running while the web server runs in parallel


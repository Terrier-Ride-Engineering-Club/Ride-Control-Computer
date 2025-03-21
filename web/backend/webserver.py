# RCC Webserver for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import threading
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS  # Import the extension
from ridecontrolcomputer import RideControlComputer, State
from Backend.iocontroller import IOController

class RideWebServer:
    def __init__(self, rcc: RideControlComputer, host="0.0.0.0", port=23843):
        """
        Initialize the web server with a reference to the Ride Control Computer (RCC).
        """
        self.rcc = rcc
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "http://127.0.0.1:23843"}})
        self.host = host
        self.port = port
        self.web_thread = None

        # Define routes
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/status', 'status', self.status, methods=['GET'])
        self.app.add_url_rule('/start', 'start_ride', self.start_ride, methods=['POST'])
        self.app.add_url_rule('/estop', 'trigger_estop', self.trigger_estop, methods=['POST'])
        self.app.add_url_rule('/stop', 'stop_ride', self.stop_ride, methods=['POST'])
        self.app.add_url_rule('/dispatch', 'dispatch_ride', self.dispatch_ride, methods=['POST'])
        self.app.add_url_rule('/ride_off', 'ride_off', self.ride_off, methods=['POST'])
        self.app.add_url_rule('/restart', 'restart_ride', self.restart_ride, methods=['POST'])

    def index(self):
        """Serve the HTML dashboard."""
        return render_template('main.html')

    def status(self):
        """Return the current status of the ride system, including all button states."""
        return jsonify({
            'state': self.rcc.state.name,
            'ESTOP': self.rcc.io.read_estop(),
            'STOP': self.rcc.io.read_stop(),
            'DISPATCH': self.rcc.io.read_dispatch(),
            'RIDE_OFF': self.rcc.io.read_ride_off(),
            'RESTART': self.rcc.io.read_restart(),
        })

    def start_ride(self):
        """Attempt to start the ride."""
        if self.rcc.state == State.IDLE:
            self.rcc.state = State.RUNNING
            return jsonify({'message': 'Ride started'}), 200
        return jsonify({'error': 'Ride must be idle to start'}), 400

    def trigger_estop(self):
        """Manually trigger an emergency stop via the web API."""
        self.rcc.io.toggle_estop()  # Call the method in IOController
        return jsonify({'message': 'ESTOP triggered'}), 200

    def stop_ride(self):
        """Stop ride safely while prioritizing rider comfort."""
        self.rcc.io.toggle_stop()  # Call the method in IOController
        return jsonify({'message': 'Ride stopping safely'}), 200

    def dispatch_ride(self):
        """Start the ride when dispatch conditions are met."""
        self.rcc.io.trigger_dispatch()  # Call the method in IOController
        return jsonify({'message': 'Ride dispatched'}), 200

    def ride_off(self):
        """Power down the ride safely."""
        self.rcc.io.trigger_ride_off()  # Call the method in IOController
        return jsonify({'message': 'Ride powered off'}), 200

    def restart_ride(self):
        """Return ride to operation mode after ESTOP or stop."""
        self.rcc.io.trigger_restart()  # Call the method in IOController
        return jsonify({'message': 'Ride restarted and ready'}), 200

    def run(self):
        """Run the Flask app in a separate thread."""
        self.web_thread = threading.Thread(target=self._run_server, daemon=True)
        self.web_thread.start()

    def _run_server(self):
        """Internal method to start the Flask server."""
        self.app.run(host=self.host, port=self.port)

    def stop(self):
        """Gracefully stop the web server."""
        print("Stopping web server (not implemented yet).")
import threading
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS  # Import the extension
from ridecontrolcomputer import RideControlComputer, State

class RideWebServer:
    def __init__(self, rcc, host="0.0.0.0", port=23843):
        """
        Initialize the web server with a reference to the Ride Control Computer (RCC).
        """
        self.rcc = rcc
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.host = host
        self.port = port
        self.web_thread = None

        # Define routes
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/status', 'status', self.status, methods=['GET'])
        self.app.add_url_rule('/start', 'start_ride', self.start_ride, methods=['POST'])
        self.app.add_url_rule('/estop', 'trigger_estop', self.trigger_estop, methods=['POST'])

    def index(self):
        """Serve the HTML dashboard."""
        return render_template('main.html')

    def status(self):
        """Return the current status of the ride system."""
        return jsonify({
            'state': self.rcc.state.name,
            'ESTOP': self.rcc.ESTOP,
            'OnSwitchActive': self.rcc.OnSwitchActive,
            'ResetSwitchActive': self.rcc.ResetSwitchActive
        })

    def start_ride(self):
        """Attempt to start the ride."""
        if self.rcc.state == State.IDLE:
            self.rcc.state = State.RUNNING
            return jsonify({'message': 'Ride started'}), 200
        return jsonify({'error': 'Ride must be idle to start'}), 400

    def trigger_estop(self):
        """Manually trigger an emergency stop."""
        self.rcc.state = State.ESTOPPED
        self.rcc.io.terminate_power()
        return jsonify({'message': 'ESTOP triggered'}), 200

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
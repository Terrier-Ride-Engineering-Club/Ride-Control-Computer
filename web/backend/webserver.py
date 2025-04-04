# RCC Webserver for TREC's REC Ride Control Computer
    # Made by Jackson Justus (jackjust@bu.edu)

import threading
import logging
import sys
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS  # Import the extension
from ridecontrolcomputer import RideControlComputer, State
from Backend.iocontroller import HardwareIOController

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s]: %(message)s"

# Used to suppress webserver logs to the debug level
class DowngradeToDebugFilter(logging.Filter):
    def filter(self, record):
        record.levelno = logging.DEBUG
        record.levelname = 'DEBUG'
        return True

# Used to send logs to the client
class InMemoryLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logs = []

    def emit(self, record):
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        self.logs.append(msg)


class RideWebServer:
    def __init__(self, rcc: RideControlComputer, host="0.0.0.0", port=23843):
        """
        Initialize the web server with a reference to the Ride Control Computer (RCC).
        """
        self.rcc = rcc
        self.app = Flask(__name__)
        self.app.name = "RCCWebserver"
        # Configure flask logging to just be debug level using a filter
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.DEBUG)
        werkzeug_logger.addFilter(DowngradeToDebugFilter())

        CORS(self.app, resources={r"/*": {"origins": "http://127.0.0.1:23843"}})
        
        self.log_handler = InMemoryLogHandler()
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(self.log_handler)

        self.host = host
        self.port = port
        self.web_thread = None

        # Define routes
        self.app.add_url_rule('/', 'index', self.index, methods=['GET']) # Redirect to control
        self.app.add_url_rule('/control', 'control', self.control, methods=['GET'])
        self.app.add_url_rule('/maintenance', 'maintenance', self.maintenance, methods=['GET'])
        self.app.add_url_rule('/api/status', 'status', self.status, methods=['GET'])
        self.app.add_url_rule('/api/start', 'start_ride', self.start_ride, methods=['POST'])
        self.app.add_url_rule('/api/estop', 'trigger_estop', self.trigger_estop, methods=['POST'])
        self.app.add_url_rule('/api/stop', 'stop_ride', self.stop_ride, methods=['POST'])
        self.app.add_url_rule('/api/dispatch', 'dispatch_ride', self.dispatch_ride, methods=['POST'])
        self.app.add_url_rule('/api/ride_off', 'ride_off', self.ride_off, methods=['POST'])
        self.app.add_url_rule('/api/restart', 'restart_ride', self.restart_ride, methods=['POST'])
        self.app.add_url_rule('/api/toggle_webcontrols','toggle_web_controls', self.toggle_webserver_control, methods=['POST'])
        self.app.add_url_rule('/api/logs', 'logs', self.get_logs, methods=['GET'])
        self.app.add_url_rule('/api/faults','faults', self.get_faults, methods=['GET'])
        self.app.add_url_rule('/api/motor/status', 'motor_status', self.get_motor_status, methods=['GET'])

    # --- Run Methods ---
    def run(self):
        """Run the Flask app in a separate thread."""
        self.web_thread = threading.Thread(target=self._run_server, daemon=True)
        self.web_thread.start()

    def _run_server(self):
        """Internal method to start the Flask server."""
        self.app.run(host=self.host, port=self.port)

    # --- Webserver Routes ---
    def index(self):
        """Serve the HTML dashboard."""
        return redirect(url_for('control'))
    
    def control(self):
        return render_template('control.html')
    
    def maintenance(self):
        return render_template('maintenance.html')

    def status(self):
        """Return the current status of the ride system, including all button states."""
        return jsonify({
            'controlType': self.rcc.ioControllerType,
            'state': self.rcc.state.__str__(),
            'ESTOP': self.rcc.io.read_estop(),
            'STOP': self.rcc.io.read_stop(),
            'DISPATCH': self.rcc.io.read_dispatch(),
            'RIDE_OFF': self.rcc.io.read_ride_on_off(),
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
        self.rcc.io.simulate_estop_toggle()  # Call the method in IOController
        return jsonify({'message': 'ESTOP triggered'}), 200

    def stop_ride(self):
        """Stop ride safely while prioritizing rider comfort."""
        self.rcc.io.simulate_stop_toggle()  # Call the method in IOController
        return jsonify({'message': 'Ride stopping safely'}), 200

    def dispatch_ride(self):
        """Start the ride when dispatch conditions are met."""
        self.rcc.io.simulate_dispatch()  # Call the method in IOController
        return jsonify({'message': 'Ride dispatched'}), 200

    def ride_off(self):
        """Power down the ride safely."""
        self.rcc.io.simulate_ride_off()  # Call the method in IOController
        return jsonify({'message': 'Ride powered off'}), 200

    def restart_ride(self):
        """Return ride to operation mode after ESTOP or stop."""
        self.rcc.io.simulate_reset()  # Call the method in IOController
        return jsonify({'message': 'Ride restarted and ready'}), 200
    
    def toggle_webserver_control(self):
        """Toggles the IO Controller from webserver control to hardware control."""
        new_type = self.rcc.toggle_io_controller()
        return jsonify({'message': f'Webserver control switched to: {new_type}'}), 200

    def get_logs(self):
        return jsonify({'logs': self.log_handler.logs[-100:]})
    
    def get_faults(self):
        return jsonify(self.rcc.fault_manager.get_faults())

    def get_motor_status(self):
        """Returns motor status values as a JSON object."""
        try:
            motor_status = {
                "encoderPosition": self.rcc.io.read_encoder(),
                "encoderHomePosition": "NOT IMPL", # TODO: IMPLEMENT
                "motorSpeed": self.rcc.io.read_max_speed(),
                "motorCurrent": self.rcc.io.read_motor_current(),
                "powerSupplyVoltage": "NOT IMPL", # TODO: IMPLEMENT
                "motorControllerStatus": self.rcc.io.read_status()
            }
        except Exception as e:
            return {"message": "Error fetching data"}, 500
        return jsonify(motor_status)

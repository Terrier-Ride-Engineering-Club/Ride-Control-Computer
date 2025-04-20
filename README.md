# Ride Control Computer (RCC) 2024-2025
This repo hosts all of the code and files related to Terrier Ride Engineering Club's (TREC) Ride Control Computer (RCC) project. This was made as a control system and Human Machine Interface (HMI) for TREC's Ride Engineering Competition (REC) entry, Poseidon's Wrath. This repository is no longer maintained, as the 2024-2025 REC season has concluded. It exists for archive purposes. 

## About the Project
The Ride Control Computer (RCC) is a control and operator interface meant for controlling TREC's Poseidon's Wrath ride. This project uses a state machine for control logic, as well as a Flask webserver to serve as a Human Machine Interface. This project complies with all of ASTM F2291-24 Standards, minus operator access control. This code is open source, and other entities are encouraged to use it in any way they please. Attribution is required. 

## Key Features
- **State Machine Architecture**: Utilizes a state machine for rigid and predictable system behavior.
- **Web Server HMI**: A operator interface meant for a ride operator to carry out maintenance actions & monitor the state of the ride.
- **Fault Monitoring**: A package which constantly monitors all parameters of the system, and makes sure the system stays in a safe state.

## Credits
__Project Credits:__ <br>
Jackson Justus - Electrical Lead -- jackjust@bu.edu <br>
Aryan Kumar - Electrical Team Member <br>

__Club Leadership:__ <br>
Ride Engineering Coordinator: Jackson Justus (jackjust@bu.edu) <br>
Electrical Lead: Jackson Justus (jackjust@bu.edu) <br>
Mechanical Lead: Daniel Ulrich (dculrich@bu.edu) <br>
Design Lead: Zachary Walton <br>

## System Requirements <br>
Python 3.11.2
Raspberry Pi 5 (or compatible system). <br>
Dependencies listed in requirements.txt

# EchoNav

## Bluetooth Beacon-Based Indoor Navigation System for the Visually Impaired

EchoNav is an innovative indoor navigation solution designed specifically for visually impaired users. By leveraging strategically placed Bluetooth beacons, the system provides real-time auditory feedback that guides users through indoor environments with precision and confidence.

## Features

- **Proximity-Based Guidance**: Delivers real-time audio cues based on user's proximity to Bluetooth beacons
- **Spatial Awareness**: Provides directional guidance and obstacle warnings
- **Accessible Interface**: Fully voice-controlled with intuitive audio feedback
- **Offline Navigation**: Functions without requiring constant internet connectivity
- **Privacy-Focused**: All data processing happens locally on the device

## How It Works

EchoNav uses a network of Bluetooth Low Energy (BLE) beacons installed throughout an indoor environment. These beacons transmit signals that are detected by the user's smartphone. The app calculates the user's position relative to these beacons and provides audio guidance through:

1. Directional instructions ("Turn left," "Continue straight ahead")
2. Proximity alerts ("Approaching elevator," "Door 10 feet ahead")
3. Contextual information about the surrounding environment

The system relies on RSSI (Received Signal Strength Indicator) measurements to determine proximity to Bluetooth devices, enabling real-time tracking and navigation.

## Requirements

### Hardware
- Smartphone with Bluetooth 4.0 or later capability acting as a beacon

### Software Dependencies
- Python 3.8+
- pyobjc-core (for macOS Objective-C bridge)
- pyobjc-framework-Foundation (for Foundation framework access)
- pyobjc-framework-CoreBluetooth (for Bluetooth functionality)
- pyobjc-framework-libdispatch (for Grand Central Dispatch)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/echonav.git
   cd echonav
   ```

2. Create and activate a virtual environment:
   ```
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the bluetooth based navigation app
   ```
   python3 bluetooth_nav.py
   ```

## Usage Guide

### Bluetooth Beacon Tracking

1. Launch the application:
   ```
   python3 bluetooth_nav.py
   ```

2. The system will scan for nearby Bluetooth devices and display them with their signal strength (RSSI).

3. After 10 seconds, you'll be prompted to select a device to track by entering its corresponding number.

4. Once connected, the application continuously monitors the signal strength (RSSI) of the selected device, providing feedback on proximity.

5. Press Ctrl+C to stop tracking and exit the application.

### WiFi Scanning (Alternative Method)

The system can also use WiFi signals for positioning:
```
python3 wifi_scan.py
```
This will continuously scan for available WiFi networks and display their signal strengths.

## Contributing

Contributions to EchoNav are welcome!  

## License

This project is licensed under the MIT License - see the LICENSE file for details.
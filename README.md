# EchoNav
## Bluetooth Beacon-Based Indoor Navigation System with Proximity Sound Feedback

EchoNav is an innovative indoor navigation solution designed specifically for visually impaired users. The system provides real-time auditory feedback based on proximity to Bluetooth devices, creating an intuitive sonic interface that helps users navigate indoor environments.

## Features

- **Proximity Sound Feedback**: Generates continuous tones that change frequency based on distance to a Bluetooth device
- **Responsive Tracking**: High-performance RSSI scanning provides immediate feedback as you move
- **Wide Frequency Range**: Uses a 4-octave sound range (110Hz-1760Hz) for precise distance perception
- **Automatic Reconnection**: Seamlessly reconnects if the Bluetooth connection is lost
- **Audible Connection Status**: Distinct sound patterns indicate connection and disconnection events
- **Real-time Metrics**: Displays RSSI values and update rates in the terminal

## How It Works

EchoNav uses the Bluetooth Low Energy (BLE) protocol to track the signal strength (RSSI) of a selected Bluetooth device. As you move closer to or further from the device, the system generates a continuous tone that changes in frequency:

- **Higher frequency** = Closer proximity (stronger signal)
- **Lower frequency** = Greater distance (weaker signal)

The system creates an intuitive audio landscape that allows you to "hear" your position relative to the Bluetooth target, making it especially useful for visually impaired users.

## Requirements

### Hardware
- macOS computer with Bluetooth capability
- Bluetooth device to track (smartphone, Bluetooth beacon, etc.)

### Software Dependencies
- Python 3.8+
- PyObjC (for macOS Objective-C bridge)
- NumPy (for audio signal processing)
- SoundDevice (for audio output)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/echonav.git
   cd echonav
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv env_nav
   source env_nav/bin/activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Detailed Usage Guide

### Running the Bluetooth Navigation System

1. Activate the virtual environment if not already active:
   ```
   source env_nav/bin/activate
   ```

2. Launch the application:
   ```
   python3 bluetooth_nav.py
   ```

3. The system will scan for nearby Bluetooth devices for 10 seconds and display them with their signal strength (RSSI):
   ```
   Scanning for Bluetooth devices...
   
   [1] iPhone (RSSI: -65)
   [2] Bluetooth Speaker (RSSI: -78)
   [3] Unnamed (RSSI: -92)
   ```

4. When prompted, select a device to track by entering its corresponding number:
   ```
   Enter device number to track: 1
   ```

5. After connecting, the system will:
   - Start playing a continuous tone
   - Begin high-performance RSSI scanning
   - Display real-time RSSI values, smoothed RSSI, and the corresponding tone frequency

6. Move around with your Mac to experience how the tone changes:
   - Move closer to the device: tone frequency increases (higher pitch)
   - Move away from the device: tone frequency decreases (lower pitch)

7. The terminal will display information like:
   ```
   RSSI: -65, Smoothed RSSI: -65.3, Frequency: 594.0Hz
   RSSI updates per second: 10
   ```

8. If the connection is lost, the system will:
   - Play a distinct low-frequency alternating tone
   - Automatically attempt to reconnect
   - Display reconnection progress in the terminal

9. Press `Ctrl+C` at any time to stop tracking and exit the application.

### Performance Tuning

The bluetooth_nav.py script includes several parameters you can adjust to fine-tune its performance:

- **Frequency Range**: Modify `min_freq` and `max_freq` values to change the sound range
- **RSSI Thresholds**: Adjust `min_rssi` and `max_rssi` to calibrate distance sensitivity
- **Frequency Curve**: Change `frequency_curve` to 'linear', 'logarithmic', or 'exponential' for different response curves
- **Smoothing**: Increase `max_history_size` for smoother frequency transitions (may reduce responsiveness)

### Troubleshooting

- **Low Update Rate**: If you experience a low RSSI update rate (displayed in the terminal), try:
  - Reconnecting several times, as update rates tend to improve after multiple connections
  - Ensuring Bluetooth is properly enabled on both devices
  - Moving to an area with less Bluetooth interference

- **Disconnection Issues**: If the device keeps disconnecting:
  - Check that the Bluetooth device battery is not low
  - Ensure you're within reasonable range (typically up to 10 meters)
  - Restart the Bluetooth on both devices

- **Audio Problems**: If you don't hear the tone:
  - Verify your Mac's volume is turned up
  - Check that no other application is using audio exclusively
  - Try restarting the application

## Technical Details

The bluetooth_nav.py script uses PyObjC to interface with macOS's CoreBluetooth framework. It implements a high-performance scanning system that maximizes RSSI update rates for responsive audio feedback.

Key technical features:

- **Multi-threaded Scanning**: Uses multiple threads to achieve high RSSI scanning rates
- **RSSI Smoothing**: Averages readings to prevent abrupt frequency jumps
- **Logarithmic Frequency Mapping**: Maps signal strength to frequency using musical intervals
- **Continuous Audio Generation**: Implements real-time audio synthesis with smooth phase transitions

## WiFi Scanning (Alternative Method)

The system also supports WiFi signal-based positioning through the wifi_scan.py script:
```
python3 wifi_scan.py
```

This will continuously scan for available WiFi networks and display their signal strengths.

## Future Development

Planned features for future releases:
- Multiple device tracking for triangulation
- Custom sound profiles for different environments
- Machine learning for improved distance estimation
- iOS/Android companion apps

## Contributing

Contributions to EchoNav are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
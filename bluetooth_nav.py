import objc
from CoreBluetooth import CBCentralManager, CBPeripheral
from Foundation import NSObject, NSLog, NSNumber, NSRunLoop, NSDefaultRunLoopMode, NSDate
import dispatch
from PyObjCTools import AppHelper
import threading
import time
import os
import math
import numpy as np
import sounddevice as sd
from queue import Queue

# Load CoreBluetooth framework
objc.loadBundle('CoreBluetooth', globals(), '/System/Library/Frameworks/CoreBluetooth.framework')

class ContinuousToneGenerator:
    """Generates a continuous tone with frequency that can be updated in real-time"""
    def __init__(self, initial_freq=440.0, sample_rate=44100):
        self.sample_rate = sample_rate
        self.frequency = initial_freq
        self.amplitude = 0.3
        self.phase = 0.0
        self.running = False
        self.freq_queue = Queue()
        self.stream = None
    
    def audio_callback(self, outdata, frames, time, status):
        """Callback for the sounddevice stream"""
        # Check if there's a new frequency to apply
        while not self.freq_queue.empty():
            self.frequency = self.freq_queue.get()
        
        # Generate audio samples
        t = np.arange(frames) / self.sample_rate
        phase_increment = 2 * np.pi * self.frequency / self.sample_rate
        
        # Generate continuous sine wave with current phase
        samples = self.amplitude * np.sin(self.phase + 2 * np.pi * self.frequency * t)
        
        # Update phase for next callback
        self.phase = (self.phase + frames * phase_increment) % (2 * np.pi)
        
        # Write to output buffer
        outdata[:, 0] = samples

    def start(self):
        """Start the continuous tone"""
        if not self.running:
            self.running = True
            self.stream = sd.OutputStream(
                channels=1,
                samplerate=self.sample_rate,
                callback=self.audio_callback
            )
            self.stream.start()
    
    def set_frequency(self, freq):
        """Update the frequency of the tone"""
        # Put the new frequency in the queue
        if self.running:
            # Clear queue to avoid backlog
            while not self.freq_queue.empty():
                self.freq_queue.get()
            self.freq_queue.put(freq)
    
    def stop(self):
        """Stop the continuous tone"""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

class BluetoothDelegate(NSObject):
    def init(self):
        self = objc.super(BluetoothDelegate, self).init()
        if self is None:
            return None
        self.devices = {}          # Mapping: serial number -> peripheral
        self.device_counter = 0    # To assign serial numbers
        self.selected_peripheral = None
        self.running = True
        self.manager = None        # Will hold the CBCentralManager instance
        
        # Sound and RSSI related attributes
        self.min_rssi = -100       # Weak signal (far away)
        self.max_rssi = -40        # Strong signal (close)
        
        # Expanded frequency range for more granular sound feedback
        self.min_freq = 110        # Lowest frequency in Hz (A2)
        self.max_freq = 1760       # Highest frequency in Hz (A6) - much wider range
        
        # RSSI smoothing for more natural frequency changes
        self.rssi_history = []
        self.max_history_size = 3  # Number of readings to average
        self.last_rssi = None
        
        # Fine-tuning parameters
        self.frequency_curve = 'logarithmic'  # 'linear', 'logarithmic', or 'exponential'
        self.frequency_curve_factor = 2.0     # Curve steepness factor
        
        # High-performance scanning
        self.scan_threads = []
        self.scan_threads_count = 10  # Increased from 5 to 10 threads
        self.scan_thread_delay = 0.0001  # Extremely minimal delay between reads
        self.last_successful_read_time = time.time()
        self.rssi_updates_per_second = 0
        self.rssi_updates_count = 0
        self.rssi_update_times = []
        self.last_stats_time = time.time()
        
        # Connection state
        self.is_connected = False
        self.connection_monitor_active = False
        self.disconnection_time = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 50  # Maximum number of reconnection attempts
        
        # Initialize the continuous tone generator
        self.tone_generator = ContinuousToneGenerator(initial_freq=self.min_freq)
        
        return self

    def centralManagerDidUpdateState_(self, central):
        self.manager = central  # Save reference to the central manager
        if central.state() == 5:  # CBManagerStatePoweredOn
            NSLog("Bluetooth is powered on, scanning for devices...")
            
            # Use scan options to improve device discovery
            scan_options = {
                'CBCentralManagerScanOptionAllowDuplicatesKey': True
            }
            central.scanForPeripheralsWithServices_options_(None, scan_options)
        else:
            NSLog("Bluetooth state: %d" % central.state())

    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, central, peripheral, data, rssi):
        # Only add new peripherals
        if peripheral in self.devices.values():
            return

        self.device_counter += 1
        self.devices[self.device_counter] = peripheral
        peripheral_name = peripheral.name() or "Unnamed"
        print(f"[{self.device_counter}] {peripheral_name} (RSSI: {rssi})")

    def prompt_for_device_selection(self):
        # Wait for 10 seconds before prompting so that some devices are discovered.
        time.sleep(10)
        self.manager.stopScan()
        if not self.devices:
            print("No devices found.")
            return
        print("\nDiscovered devices:")
        for num, periph in self.devices.items():
            print(f"[{num}] {periph.name() or 'Unnamed'}")
        while True:
            try:
                choice = int(input("Enter device number to track: "))
                if choice in self.devices:
                    self.selected_peripheral = self.devices[choice]
                    break
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        print(f"Connecting to {self.selected_peripheral.name()}...")
        self.manager.connectPeripheral_options_(self.selected_peripheral, None)

    def centralManager_didConnectPeripheral_(self, central, peripheral):
        if peripheral == self.selected_peripheral:
            NSLog("Connected to %s" % (peripheral.name() or "Unnamed"))
            peripheral.setDelegate_(self)
            print("Starting continuous tone proximity tracking...")
            print("Closer = higher frequency tone, Further = lower frequency tone")
            
            # Update connection state
            self.is_connected = True
            self.disconnection_time = None
            self.reconnect_attempts = 0
            
            # Start the continuous tone
            self.tone_generator.start()
            
            # Apply high-performance settings to the peripheral
            try:
                # Try to optimize peripheral settings
                peripheral.setValue_forKey_(NSNumber.numberWithFloat_(0.01), "notifyOnNotificationTimeout")
            except:
                pass
                
            # Warmup the BLE stack with an initial burst of RSSI requests
            # This helps establish a higher scan rate from the beginning
            print("Warming up BLE scanning for maximum responsiveness...")
            self.warmup_rssi_scanning(peripheral)
            
            # Start high-performance scanning for RSSI values
            if not self.scan_threads:
                self.start_high_performance_scanning(peripheral)
            
            # Start stats reporting thread
            if not hasattr(self, 'stats_thread') or not self.stats_thread.is_alive():
                self.start_stats_reporting()
            
            # Start connection monitoring
            if not self.connection_monitor_active:
                self.start_connection_monitor()

    def warmup_rssi_scanning(self, peripheral):
        """Perform initial burst of RSSI readings to maximize scan rate from the start"""
        def warmup():
            # Create a dedicated runloop for the warmup
            warmup_loop = NSRunLoop.currentRunLoop()
            
            # Send 100 RSSI requests in rapid succession to "warm up" the BLE stack
            for _ in range(100):
                try:
                    peripheral.readRSSI()
                    # Process events immediately
                    warmup_loop.runMode_beforeDate_(
                        NSDefaultRunLoopMode,
                        NSDate.dateWithTimeIntervalSinceNow_(0.001)
                    )
                    time.sleep(0.001)
                except:
                    pass
                    
        # Run warmup in a separate thread
        warmup_thread = threading.Thread(target=warmup, daemon=True)
        warmup_thread.start()
        
        # Give the warmup a moment to get started
        time.sleep(0.5)

    def start_high_performance_scanning(self, peripheral):
        """Start multiple threads for high-performance RSSI scanning"""
        def scan_loop():
            """Thread function for continuous RSSI scanning"""
            run_loop = NSRunLoop.currentRunLoop()
            
            # Pre-allocate date object to minimize overhead
            next_date = NSDate.dateWithTimeIntervalSinceNow_(0.001)
            
            while self.running:
                try:
                    # Request RSSI reading
                    peripheral.readRSSI()
                    
                    # Process the runloop immediately to handle callbacks
                    run_loop.runMode_beforeDate_(
                        NSDefaultRunLoopMode,
                        next_date
                    )
                    
                    # Minimize delay between scans for faster updates
                    time.sleep(0.00005)  # Reduced delay to 50 microseconds
                except Exception as e:
                    # Shorter sleep on error for faster recovery
                    time.sleep(0.01)
        
        # Start multiple threads for better throughput
        if not self.scan_threads:
            for i in range(self.scan_threads_count):
                thread = threading.Thread(target=scan_loop, daemon=True)
                thread.start()
                self.scan_threads.append(thread)
                
            print(f"Started {self.scan_threads_count} high-performance scanning threads")

    def start_stats_reporting(self):
        """Start a thread to periodically report scanning performance stats"""
        def stats_loop():
            while self.running:
                time.sleep(1.0)  # Update stats every second
                
                # Calculate updates per second
                current_time = time.time()
                elapsed = current_time - self.last_stats_time
                
                if elapsed >= 1.0:
                    # Clean old timestamps
                    while self.rssi_update_times and self.rssi_update_times[0] < current_time - 1.0:
                        self.rssi_update_times.pop(0)
                        
                    # Calculate rate
                    self.rssi_updates_per_second = len(self.rssi_update_times)
                    
                    # Only print every 5 seconds to reduce console spam
                    if int(current_time) % 5 == 0:
                        print(f"RSSI updates per second: {self.rssi_updates_per_second}")
                        
                    self.last_stats_time = current_time
        
        stats_thread = threading.Thread(target=stats_loop, daemon=True)
        stats_thread.start()

    def peripheral_didReadRSSI_error_(self, peripheral, rssi, error):
        """Called when RSSI is read from the peripheral"""
        if peripheral != self.selected_peripheral:
            return
            
        # Update last successful read time for monitoring
        self.last_successful_read_time = time.time()
        
        if error:
            # Silently ignore errors to prevent console spam
            return
            
        # Get the RSSI value
        rssi_val = rssi.intValue()
        
        # Add to history and maintain maximum size
        self.rssi_history.append(rssi_val)
        if len(self.rssi_history) > self.max_history_size:
            self.rssi_history.pop(0)
        
        # Get smoothed RSSI value (average of recent readings)
        smoothed_rssi = sum(self.rssi_history) / len(self.rssi_history)
        self.last_rssi = smoothed_rssi
        
        # Track update rate
        current_time = time.time()
        self.rssi_update_times.append(current_time)
        self.rssi_updates_count += 1
        
        # Update tone frequency based on the smoothed RSSI value
        frequency = self.calculate_frequency(smoothed_rssi)
        self.tone_generator.set_frequency(frequency)
        
        # Dynamically adjust scan thread delay based on update rate
        # If we're getting fewer than 5 updates per second, decrease delay
        if len(self.rssi_update_times) < 5 and self.scan_thread_delay > 0.0001:
            self.scan_thread_delay = max(0.0001, self.scan_thread_delay * 0.9)
        
        # Print RSSI value and frequency to the terminal
        print(f"RSSI: {rssi_val}, Smoothed RSSI: {smoothed_rssi:.1f}, Frequency: {frequency:.1f}Hz")
        
        # Print occasionally (every 5 seconds) to avoid console spam
        if int(current_time) % 5 == 0 and int(current_time * 10) % 10 == 0:
            print(f"RSSI updates per second: {self.rssi_updates_per_second}")

    def calculate_frequency(self, rssi):
        """Calculate tone frequency based on RSSI value with more granular mapping"""
        # Ensure RSSI is within our defined range
        clamped_rssi = max(min(rssi, self.max_rssi), self.min_rssi)
        
        # Normalize RSSI to [0, 1] range where 1 is closest
        normalized = (clamped_rssi - self.min_rssi) / (self.max_rssi - self.min_rssi)
        
        # Apply chosen frequency curve for more natural sound progression
        if self.frequency_curve == 'logarithmic':
            # Logarithmic curve - more granular changes when further away
            # This gives finer distinctions at lower signal strengths
            adjusted = math.log(normalized * (self.frequency_curve_factor - 1) + 1) / math.log(self.frequency_curve_factor)
        elif self.frequency_curve == 'exponential':
            # Exponential curve - more granular changes when closer
            # This gives finer distinctions at higher signal strengths
            adjusted = math.pow(normalized, self.frequency_curve_factor)
        else:  # 'linear'
            adjusted = normalized
        
        # Apply frequency mapping using musical intervals for more pleasing sounds
        # Using a logarithmic frequency scale like musical octaves
        freq_ratio = self.max_freq / self.min_freq
        frequency = self.min_freq * math.pow(freq_ratio, adjusted)
        
        return frequency

    def centralManager_didDisconnectPeripheral_error_(self, central, peripheral, error):
        if peripheral == self.selected_peripheral:
            self.is_connected = False
            self.disconnection_time = time.time()
            print(f"Disconnected from {peripheral.name() or 'Unnamed'}")
            
            # Play a distinct "disconnected" sound pattern
            self.play_disconnected_sound_pattern()
            
            # Try to reconnect immediately
            print("Attempting to reconnect...")
            central.connectPeripheral_options_(peripheral, None)
            self.reconnect_attempts += 1

    def play_disconnected_sound_pattern(self):
        """Play a distinct sound pattern to indicate disconnection"""
        # Use a low frequency oscillation pattern
        base_freq = 150
        self.tone_generator.set_frequency(base_freq)

    def start_connection_monitor(self):
        """Start a thread to monitor connection status and handle reconnection"""
        def connection_monitor_loop():
            self.connection_monitor_active = True
            disconnect_sound_alternator = 0
            
            while self.running:
                time.sleep(0.5)  # Check every half second
                
                current_time = time.time()
                
                # Check if we're not connected
                if not self.is_connected:
                    # Play alternating tones when disconnected to make it obvious
                    disconnect_sound_alternator = (disconnect_sound_alternator + 1) % 4
                    
                    if disconnect_sound_alternator == 0:
                        self.tone_generator.set_frequency(150)  # Low tone
                    elif disconnect_sound_alternator == 2:
                        self.tone_generator.set_frequency(100)  # Even lower tone
                    
                    # Try to reconnect if we've been disconnected
                    if self.disconnection_time and self.reconnect_attempts < self.max_reconnect_attempts:
                        # Retry connection every 2 seconds
                        if current_time - self.disconnection_time > 2.0:
                            if self.selected_peripheral:
                                print(f"Reconnection attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts}...")
                                self.manager.connectPeripheral_options_(self.selected_peripheral, None)
                                self.reconnect_attempts += 1
                                self.disconnection_time = current_time  # Reset timer
                
                # Check for silent disconnection (no RSSI updates for a while)
                elif current_time - self.last_successful_read_time > 5.0:
                    print("No RSSI updates for 5 seconds - device may be silently disconnected")
                    # Mark as disconnected
                    self.is_connected = False
                    self.disconnection_time = current_time
                    self.reconnect_attempts = 0
                    
                    # Try to disconnect and reconnect
                    if self.selected_peripheral:
                        try:
                            self.manager.cancelPeripheralConnection_(self.selected_peripheral)
                            time.sleep(1.0)
                            self.manager.connectPeripheral_options_(self.selected_peripheral, None)
                        except Exception as e:
                            print(f"Error during reconnection: {str(e)}")
            
            self.connection_monitor_active = False
        
        monitor_thread = threading.Thread(target=connection_monitor_loop, daemon=True)
        monitor_thread.start()
        print("Connection monitoring started")

    def stop(self):
        print("Stopping Bluetooth tracking...")
        self.running = False
        
        # Stop the tone generator
        if hasattr(self, 'tone_generator'):
            self.tone_generator.stop()
            
        print("Tracking stopped")


if __name__ == '__main__':
    # Create delegate and central manager instances.
    delegate = BluetoothDelegate.alloc().init()
    manager = CBCentralManager.alloc().initWithDelegate_queue_(delegate, None)

    print("Scanning for Bluetooth devices...\n")

    # Start a background thread to prompt for device selection after a delay.
    selection_thread = threading.Thread(target=delegate.prompt_for_device_selection, daemon=True)
    selection_thread.start()

    try:
        AppHelper.runConsoleEventLoop()
    except KeyboardInterrupt:
        delegate.stop()
        print("Stopped by user")


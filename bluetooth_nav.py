import objc
from CoreBluetooth import CBCentralManager, CBPeripheral
from Foundation import NSObject, NSLog
import dispatch
from PyObjCTools import AppHelper
import threading
import time

# Load CoreBluetooth framework
objc.loadBundle('CoreBluetooth', globals(), '/System/Library/Frameworks/CoreBluetooth.framework')

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
        return self

    def centralManagerDidUpdateState_(self, central):
        self.manager = central  # Save reference to the central manager
        if central.state() == 5:  # CBManagerStatePoweredOn
            NSLog("Bluetooth is powered on, scanning for devices...")
            central.scanForPeripheralsWithServices_options_(None, None)
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
            self.read_rssi(peripheral)

    def peripheral_didReadRSSI_error_(self, peripheral, rssi, error):
        if peripheral != self.selected_peripheral:
            return
        if error:
            NSLog("Error reading RSSI for %s: %s" % ((peripheral.name() or "Unnamed"), str(error)))
        else:
            print(f"{peripheral.name() or 'Unnamed'} RSSI: {rssi}")
        if self.running:
            self.schedule_next_read(peripheral)

    def read_rssi(self, peripheral):
        if peripheral:
            peripheral.readRSSI()

    def schedule_next_read(self, peripheral):
        # Immediately schedule the next RSSI read with no delay
        dispatch.dispatch_after(
            dispatch.dispatch_time(0, 0),
            dispatch.dispatch_get_main_queue(),
            lambda: self.read_rssi(peripheral)
        )

    def stop(self):
        self.running = False

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


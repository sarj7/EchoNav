import objc
import time

# Load the CoreWLAN framework
bundle_path = '/System/Library/Frameworks/CoreWLAN.framework'
objc.loadBundle('CoreWLAN', bundle_path=bundle_path, module_globals=globals())

# Access CoreWLAN classes
try:
    CWInterface = objc.lookUpClass('CWInterface')
    CWNetwork = objc.lookUpClass('CWNetwork')
except objc.nosuchclass_error:
    print("Error: Unable to load CoreWLAN classes. Ensure macOS permissions are set correctly.")
    exit(1)

def scan_wifi_networks():
    """
    Scans for available WiFi networks and returns a list of network details.

    Returns:
        list: A list of dictionaries with network info (SSID, BSSID, RSSI, channel, security).
    """
    # Get the default WiFi interface
    interface = CWInterface.interface()
    if not interface:
        print("No WiFi interface found. Ensure WiFi is enabled.")
        return []

    # Perform the scan
    try:
        networks, error = interface.scanForNetworksWithName_error_(None, None)
        if error:
            print(f"Error scanning for networks: {error}")
            return []
    except Exception as e:
        print(f"Exception during scan: {e}")
        return []

    # Extract network information
    network_list = []
    for network in networks:
        ssid = network.ssid()  # Network name
        bssid = network.bssid()  # MAC address of the access point
        rssi = network.rssiValue()  # Signal strength in dBm
        channel = network.wlanChannel().channelNumber()  # WiFi channel
        security = network.securityMode()  # Security type

        # Warn if SSID or BSSID is None
        if ssid is None or bssid is None:
            print("Warning: SSID or BSSID is None. Enable Location Services for this application in System Preferences > Privacy & Security.")

        network_list.append({
            'ssid': ssid if ssid else "Unknown",
            'bssid': bssid if bssid else "Unknown",
            'rssi': rssi,
            'channel': channel,
            'security': security
        })

    return network_list

def continuously_track_rssi(interval=5):
    """
    Continuously scans for WiFi networks and tracks their RSSI every 'interval' seconds.

    Args:
        interval (int): Time in seconds between scans.
    """
    print(f"Starting continuous WiFi scan every {interval} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            networks = scan_wifi_networks()
            if networks:
                print("\n" + "=" * 80)
                print(f"Scan at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'SSID':<32} {'BSSID':<20} {'RSSI':<10} {'Channel':<10} {'Security':<10}")
                print("-" * 80)
                for net in networks:
                    print(f"{net['ssid']:<32} {net['bssid']:<20} {net['rssi']:<10} {net['channel']:<10} {net['security']:<10}")
            else:
                print("No networks found or unable to scan.")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping WiFi scan.")

if __name__ == "__main__":
    continuously_track_rssi(interval=5)

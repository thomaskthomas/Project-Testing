"""Standalone script to check whether the device is connected to WiFi.

Run directly:
    python check_wifi.py
"""

import subprocess


def check_wifi(interface="wlan0"):
    try:
        # Runs 'iwgetid' to grab the connected SSID name
        ssid = subprocess.check_output(["iwgetid", "-r", interface], text=True).strip()
        if ssid:
            print(f"Wi-Fi Status: CONNECTED (Network: {ssid})")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # iwgetid exits with an error code if there is no connection
        pass

    print("Wi-Fi Status: DISCONNECTED")
    return False


if __name__ == "__main__":
    check_wifi()
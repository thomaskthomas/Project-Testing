import subprocess
import time
import requests


class PiPairingClient:
    """Encapsulates all operations needed to drive and verify the
    Raspberry Pi SoftAP -> home WiFi pairing flow."""

    def __init__(self, pi_web_url, home_ssid, wlan_interface,
                 pairing_timeout=30, pairing_poll_interval=2):
        self.pi_web_url = pi_web_url
        self.home_ssid = home_ssid
        self.wlan_interface = wlan_interface
        self.pairing_timeout = pairing_timeout
        self.pairing_poll_interval = pairing_poll_interval

    def get_current_ssid(self):
        """Return the SSID the test machine's WiFi interface is currently
        connected to, or '' if not connected / command unavailable."""
        try:
            result = subprocess.check_output(
                ["iwgetid", self.wlan_interface, "-r"], text=True
            )
            return result.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def has_internet(self):
        """Check external internet connectivity by pinging Google DNS."""
        try:
            subprocess.check_call(
                ["ping", "-c", "1", "-W", "2", "8.8.8.8"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_connected_clients(self):
        """Return the number of stations connected to the Pi's AP
        (only meaningful while the Pi is still in AP mode)."""
        try:
            result = subprocess.check_output(
                ["iw", "dev", self.wlan_interface, "station", "dump"], text=True
            )
            return result.count("Station ")
        except (subprocess.CalledProcessError, FileNotFoundError):
            return 0

    def submit_pairing_form(self, ssid, password, claim_code, timeout=5):
        """Submit home WiFi credentials and claim code to the Pi's
        onboarding endpoint. Returns the requests.Response object."""
        payload = {
            "ssid": ssid,
            "password": password,
            "claim_code": claim_code,
        }
        return requests.post(f"{self.pi_web_url}/submit", data=payload, timeout=timeout)

    def wait_for_pairing(self):
        """Poll until the test machine's current SSID matches the home
        network, or until pairing_timeout elapses. Returns True if paired."""
        attempts = self.pairing_timeout // self.pairing_poll_interval
        for _ in range(attempts):
            time.sleep(self.pairing_poll_interval)
            if self.get_current_ssid() == self.home_ssid:
                return True
        return False
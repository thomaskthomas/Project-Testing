import subprocess
import pytest


def run_cmd(args):
    try:
        return subprocess.check_output(args, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_wifi_mode_and_ssid(interface):
    """Check the active connection's mode and SSID for the given interface."""
    conn_name = run_cmd(
        ["nmcli", "-t", "-f", "GENERAL.CONNECTION", "device", "show", interface]
    ).split(":")[-1]

    if not conn_name or conn_name == "--":
        return "unknown", ""

    output = run_cmd(
        ["nmcli", "-t", "-f",
         "802-11-wireless.mode,802-11-wireless.ssid",
         "connection", "show", conn_name]
    )

    mode, ssid = "unknown", ""
    for line in output.splitlines():
        if line.startswith("802-11-wireless.mode:"):
            mode = line.split(":", 1)[1].strip().lower()
        elif line.startswith("802-11-wireless.ssid:"):
            ssid = line.split(":", 1)[1].strip()
    return mode, ssid


def get_connected_clients_count(interface):
    output = run_cmd(["iw", "dev", interface, "station", "dump"])
    return output.count("Station ")


@pytest.mark.incremental
class TestSoftApLifecycle:
    """Tests the progressive stages of the SoftAP connection sequence."""

    def test_softap_appears_and_active(self, wlan_interface, softap_ssid):
        """Stage 1 & 2: SoftAP appears & SoftAP is active."""
        mode, ssid = get_wifi_mode_and_ssid(wlan_interface)
        assert mode == "ap", f"Expected 'ap' mode, but interface is in '{mode}' mode."
        assert ssid == softap_ssid, (
            f"SoftAP broadcasted SSID is '{ssid}', expected '{softap_ssid}'."
        )

    def test_user_connects_to_softap(self, wlan_interface):
        """Stage 3 & 4: Connection establishment & user connects to SoftAP."""
        client_count = get_connected_clients_count(wlan_interface)
        assert client_count > 0, "No external users have connected to the SoftAP yet."
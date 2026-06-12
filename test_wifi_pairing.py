import pytest
from pi_pairing import PiPairingClient


@pytest.fixture(scope="session")
def pairing_client(pi_web_url, home_wifi_ssid, wlan_interface):
    return PiPairingClient(
        pi_web_url=pi_web_url,
        home_ssid=home_wifi_ssid,
        wlan_interface=wlan_interface,
    )


@pytest.mark.incremental
class TestWiFiPairingLifecycle:
    """Tests the onboarding submission, pairing transition, and disconnection states."""

    def test_submit_wifi_details_and_code(
        self, pairing_client, home_wifi_ssid, home_wifi_password, claim_code
    ):
        """Stage 5: Enter home WiFi + claim code at :18091 and Submit."""
        try:
            response = pairing_client.submit_pairing_form(
                ssid=home_wifi_ssid,
                password=home_wifi_password,
                claim_code=claim_code,
            )
            assert response.status_code == 200, (
                f"Form submission failed with status: {response.status_code}"
            )
        except Exception as e:
            pytest.fail(f"Could not connect to the Pi web server at {pairing_client.pi_web_url}: {e}")

    def test_pi_paired_with_wifi(self, pairing_client):
        """Stage 6: Pi paired with WiFi."""
        print("Waiting for Pi to switch networks and pair...")
        paired = pairing_client.wait_for_pairing()
        assert paired, (
            f"Pi failed to switch and pair with home Wi-Fi network: {pairing_client.home_ssid}"
        )

    def test_no_connection_with_user_and_has_internet(self, pairing_client):
        """Stage 7: No connection with user as well as Internet validation."""
        active_clients = pairing_client.get_connected_clients()
        assert active_clients == 0, (
            f"Expected 0 connected users, but found {active_clients} still attached."
        )
        assert pairing_client.has_internet(), "Pi is connected to the router but has NO internet access."
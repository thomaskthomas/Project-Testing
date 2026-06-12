import pytest


# --- Incremental test marker support ---

def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail(f"previous test failed ({previousfailed.name})")


# --- CLI options ---

def pytest_addoption(parser):
    parser.addoption("--claim-code", action="store", default=None,
                      help="Claim code to submit during the Pi onboarding step")
    parser.addoption("--home-wifi-ssid", action="store", default=None,
                      help="SSID of the home WiFi network to pair the Pi with")
    parser.addoption("--home-wifi-password", action="store", default=None,
                      help="Password for the home WiFi network used during pairing")
    parser.addoption("--pi-web-url", action="store", default=None,
                      help="Base URL of the Pi's SoftAP onboarding web server")
    parser.addoption("--wlan-interface", action="store", default=None,
                      help="WiFi interface name on the test machine (e.g. wlan0)")
    parser.addoption("--softap-ssid", action="store", default=None,
                      help="Expected SSID broadcast by the Pi's SoftAP")


def _get_value(request, opt_name, prompt, default=None):
    value = request.config.getoption(opt_name)
    if value:
        return value
    suffix = f" [{default}]" if default else ""
    entered = input(f"{prompt}{suffix}: ").strip()
    if not entered and default:
        return default
    if not entered:
        pytest.fail(f"A value for {opt_name} is required to run this test suite.")
    return entered


# --- Shared fixtures ---

@pytest.fixture(scope="session")
def claim_code(request):
    return _get_value(request, "--claim-code", "Enter claim code for Pi pairing")


@pytest.fixture(scope="session")
def home_wifi_ssid(request):
    return _get_value(request, "--home-wifi-ssid", "Enter home WiFi SSID")


@pytest.fixture(scope="session")
def home_wifi_password(request):
    return _get_value(request, "--home-wifi-password", "Enter home WiFi password")


@pytest.fixture(scope="session")
def pi_web_url(request):
    return _get_value(
        request, "--pi-web-url", "Enter Pi SoftAP web URL",
        default="http://192.168.4.1:18091"
    )


@pytest.fixture(scope="session")
def wlan_interface(request):
    return _get_value(
        request, "--wlan-interface", "Enter WiFi interface name",
        default="wlan0"
    )


@pytest.fixture(scope="session")
def softap_ssid(request):
    return _get_value(
        request, "--softap-ssid", "Enter expected SoftAP SSID",
        default="Pi_Setup_Network"
    )
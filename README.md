# Raspberry Pi WiFi / SoftAP Pairing Test Suite

This project contains a set of `pytest` tests and helper scripts to verify the
end-to-end WiFi onboarding flow of a Raspberry Pi 4 — from the moment its
SoftAP (Soft Access Point) becomes visible, through a user connecting to it,
submitting home WiFi credentials, and the Pi successfully pairing with the
home network and getting internet access.

## How it works

The onboarding flow is broken into two stages, each tested by its own file:

### Stage A — SoftAP Lifecycle (`test_softap_lifecycle.py`)

Verifies that the Pi's SoftAP is up and a client has joined it:

1. **SoftAP appears / is active** — checks that the test machine's WiFi
   interface is operating in `ap` mode and broadcasting the expected SSID
   (via `nmcli`).
2. **User connects to SoftAP** — checks that at least one client device has
   associated with the access point (via `iw dev <iface> station dump`).

### Stage B — WiFi Pairing Lifecycle (`test_wifi_pairing.py`)

Verifies that the onboarding form works and the Pi successfully switches
networks:

1. **Submit WiFi details + claim code** — POSTs the home WiFi SSID,
   password, and claim code to the Pi's onboarding web server
   (`http://192.168.4.1:18091/submit` by default).
2. **Pi paired with WiFi** — polls until the test machine's current SSID
   matches the home network, confirming the Pi dropped AP mode and the
   client followed it / re-joined the home network.
3. **No connection with user + internet check** — confirms no clients remain
   attached to the old SoftAP and that the Pi now has working internet
   access (pings `8.8.8.8`).

Both test classes use `@pytest.mark.incremental` (defined in `conftest.py`),
so if an earlier stage fails, later stages in the same class are
automatically marked `xfail` instead of running and failing for unrelated
reasons.

### Standalone script (`check_wifi.py`)

A simple, non-pytest script that just checks whether the current device is
connected to WiFi and prints the SSID. Useful for a quick manual sanity
check independent of the test suite.

## File structure

```
project/
├── conftest.py              # pytest hooks, CLI options, shared fixtures
├── check_wifi.py             # standalone WiFi connectivity check
├── pi_pairing.py              # PiPairingClient helper class
├── test_softap_lifecycle.py   # Stage A tests
└── test_wifi_pairing.py        # Stage B tests
```

## Requirements

- Python 3.8+
- `pytest`
- `requests`
- Linux command-line tools available on the test machine: `iwgetid`, `iw`,
  `nmcli`, `ping`

Install Python dependencies:

```bash
pip install pytest requests
```

## Configuration

None of the key values (claim code, SSIDs, password, interface, Pi URL) are
hardcoded. They are supplied either as **command-line arguments** or, if
omitted, the test suite will **prompt you interactively** at the start of the
run.

| Option | Description | Default (if left blank) |
|---|---|---|
| `--claim-code` | Claim code submitted during onboarding | *(required, no default)* |
| `--home-wifi-ssid` | SSID of the home WiFi network to pair with | *(required, no default)* |
| `--home-wifi-password` | Password for the home WiFi network | *(required, no default)* |
| `--pi-web-url` | Base URL of the Pi's SoftAP onboarding web server | `http://192.168.4.1:18091` |
| `--wlan-interface` | WiFi interface name on the test machine | `wlan0` |
| `--softap-ssid` | Expected SSID broadcast by the Pi's SoftAP | `Pi_Setup_Network` |

## Running the tests

### Run everything with all options specified

```bash
pytest -v -s test_softap_lifecycle.py test_wifi_pairing.py \
    --claim-code=CLAIM123XYZ \
    --home-wifi-ssid=MyHomeNetwork \
    --home-wifi-password=mypassword \
    --softap-ssid=Pi_Setup_Network \
    --pi-web-url=http://192.168.4.1:18091 \
    --wlan-interface=wlan0
```

### Run everything interactively (prompted for missing values)

```bash
pytest -v -s
```

> **Note:** The `-s` flag is required so that pytest does not capture
> stdin/stdout — without it, the interactive prompts won't appear and the run
> may hang or fail.

### Run only one stage

```bash
# Just the SoftAP checks
pytest -v -s test_softap_lifecycle.py --softap-ssid=Pi_Setup_Network --wlan-interface=wlan0

# Just the pairing checks
pytest -v -s test_wifi_pairing.py \
    --claim-code=CLAIM123XYZ \
    --home-wifi-ssid=MyHomeNetwork \
    --home-wifi-password=mypassword
```

### Run the standalone WiFi check

```bash
python check_wifi.py
```

## Expected manual setup before running

1. The Raspberry Pi should be powered on and broadcasting its SoftAP
   (matching `--softap-ssid`).
2. The test machine (the device running pytest) should be **connected to the
   Pi's SoftAP** before running `test_softap_lifecycle.py`.
3. After Stage A passes, run `test_wifi_pairing.py` — this will submit the
   home WiFi credentials to the Pi and then wait for the Pi (and the test
   machine, if applicable) to switch onto the home network.

## Important notes / caveats

- **Single interface assumption**: both stages assume the same WiFi
  interface (`--wlan-interface`) is used throughout — first connected to the
  Pi's SoftAP, then later connected to (or observing) the home network. If
  your physical setup uses two separate WiFi adapters (one for AP
  interaction, one for scanning), the fixtures will need to be adjusted to
  accept two interface names.
- **Form submission response**: `test_submit_wifi_details_and_code` checks
  for an HTTP `200` response from `/submit`. If your Pi's onboarding server
  responds with a redirect (`302`) on success instead, you may need to add
  `allow_redirects=False` to the request and check for `302`, or follow the
  redirect and check the resulting page content.
- **Timing**: `wait_for_pairing()` polls for up to `pairing_timeout` seconds
  (default 30s) at `pairing_poll_interval` second intervals (default 2s).
  Adjust these in `PiPairingClient.__init__` if your Pi takes longer to
  switch networks.
- **Test order**: pytest runs files alphabetically by default, so
  `test_softap_lifecycle.py` runs before `test_wifi_pairing.py`, matching the
  expected onboarding sequence (SoftAP active → user connects → submit
  credentials → pairing → internet check).

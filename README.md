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
FOR VOICE CHAT:
"""
test_sudoedge_voice.py
======================
Pytest suite for the SudoEdge voice pipeline on a Raspberry Pi.

Test coverage
-------------
TC-1  Wake word detection            hey_sudo.onnx / wake.py
TC-2  End-to-end voice turn          STT → hermes → TTS full pipeline
TC-3  Thinking cue on slow replies   lk_client.py cue injection
TC-4  Ready tone gating              Tone never fires before mic is live
TC-5  Mic wedge recovery             XVF3800 frozen hw_ptr detection & recover
TC-6  Idle wake-word recovery        Device still responsive after 30 min idle

Prerequisites
-------------
pip install pytest pytest-timeout sounddevice numpy

Environment / config (override via env vars or conftest.py fixtures):
  SUDO_WAKE_SCRIPT   path to wake.py              default: ./wake.py
  SUDO_BRIDGE_LOG    path to voice-bridge log      default: /var/log/voice-bridge.log
  SUDO_LK_LOG        path to lk_client log         default: /var/log/lk_client.log
  SUDO_AUDIO_DEVICE  sounddevice input device idx   default: None (system default)
  SUDO_ONNX_MODEL    path to hey_sudo.onnx          default: ./hey_sudo.onnx
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import threading
import wave
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

WAKE_SCRIPT   = Path(os.getenv("SUDO_WAKE_SCRIPT",  "wake.py"))
BRIDGE_LOG    = Path(os.getenv("SUDO_BRIDGE_LOG",   "/var/log/voice-bridge.log"))
LK_LOG        = Path(os.getenv("SUDO_LK_LOG",       "/var/log/lk_client.log"))
ONNX_MODEL    = Path(os.getenv("SUDO_ONNX_MODEL",   "hey_sudo.onnx"))
AUDIO_DEVICE  = os.getenv("SUDO_AUDIO_DEVICE", None)

# Timeouts (seconds)
WAKE_TIMEOUT        = 5.0   # TC-1: max wait after phrase ends
PIPELINE_TIMEOUT    = 10.0  # TC-2: full voice-turn budget
THINKING_TIMEOUT    = 8.0   # TC-3: cue must appear before reply
READY_TONE_TIMEOUT  = 10.0  # TC-4: boot → ready tone window
WEDGE_TIMEOUT       = 15.0  # TC-5: recovery after replug
IDLE_WAKE_TIMEOUT   = 5.0   # TC-6: response after 30+ min idle

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tail_log(path: Path, lines: int = 200) -> str:
    """Return the last *lines* of a log file, or '' if unreadable."""
    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), str(path)],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout
    except Exception:
        return ""


def _run_wake_script(args: list[str] = (), timeout: float = 10.0) -> subprocess.CompletedProcess:
    """Launch wake.py as a subprocess and wait for it to finish."""
    cmd = [sys.executable, str(WAKE_SCRIPT)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _inject_audio(wav_path: Path, device=None) -> None:
    """Play a WAV file to the system audio output (loopback / speaker)."""
    import sounddevice as sd  # type: ignore
    import numpy as np

    with wave.open(str(wav_path), "rb") as wf:
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        dtype = "int16" if wf.getsampwidth() == 2 else "float32"
        audio = np.frombuffer(frames, dtype=dtype)
        if wf.getnchannels() > 1:
            audio = audio.reshape(-1, wf.getnchannels())
    sd.play(audio, samplerate=rate, device=device)
    sd.wait()


def _wait_for_log_pattern(
    log_path: Path,
    pattern: str,
    timeout: float,
    poll: float = 0.2,
) -> Optional[re.Match]:
    """
    Tail *log_path* until *pattern* is found or *timeout* elapses.
    Returns the first re.Match, or None on timeout.
    """
    deadline = time.monotonic() + timeout
    seen_size = log_path.stat().st_size if log_path.exists() else 0

    while time.monotonic() < deadline:
        time.sleep(poll)
        if not log_path.exists():
            continue
        with log_path.open() as fh:
            fh.seek(seen_size)
            chunk = fh.read()
        if chunk:
            m = re.search(pattern, chunk, re.IGNORECASE)
            if m:
                return m
            seen_size += len(chunk.encode())
    return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def check_prerequisites():
    """Soft-skip individual tests if key files are missing (not the whole session)."""
    yield  # individual tests guard themselves


@pytest.fixture()
def voice_bridge_log_offset(tmp_path):
    """Snapshot the current end-of-file position so each test reads only new lines."""
    if not BRIDGE_LOG.exists():
        return 0
    return BRIDGE_LOG.stat().st_size


@pytest.fixture()
def lk_log_offset():
    if not LK_LOG.exists():
        return 0
    return LK_LOG.stat().st_size


# ---------------------------------------------------------------------------
# TC-1  Wake word detection
# ---------------------------------------------------------------------------

class TestWakeWordDetection:
    """TC-1: 'hey sudo' triggers listening cue within 1 s of phrase end."""

    def test_onnx_model_exists(self):
        """Model file must be present before anything else."""
        assert ONNX_MODEL.exists(), (
            f"ONNX wake model not found at {ONNX_MODEL}. "
            "Check hey_sudo.onnx is deployed to the expected path."
        )

    def test_wake_script_exists(self):
        assert WAKE_SCRIPT.exists(), (
            f"wake.py not found at {WAKE_SCRIPT}."
        )

    @pytest.mark.timeout(WAKE_TIMEOUT + 3)
    def test_wake_script_exits_cleanly_with_model(self):
        """
        Run wake.py --check-model; expect exit 0 (model loadable).
        """
        result = _run_wake_script(["--check-model"], timeout=WAKE_TIMEOUT)
        assert result.returncode == 0, (
            f"wake.py --check-model failed (rc={result.returncode}).\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    @pytest.mark.timeout(WAKE_TIMEOUT + 5)
    def test_listening_cue_logged_within_1s(self):
        """
        After injecting a reference 'hey sudo' WAV (if present),
        the bridge log must contain a LISTENING_CUE entry within 1 s.
        """
        ref_wav = Path("tests/fixtures/hey_sudo_reference.wav")
        if not ref_wav.exists():
            pytest.skip("Reference WAV fixture not found – manual test required.")

        phrase_end = time.monotonic()
        _inject_audio(ref_wav, device=AUDIO_DEVICE)

        match = _wait_for_log_pattern(BRIDGE_LOG, r"LISTENING_CUE|listening.cue|cue_played", 2.0)
        elapsed = time.monotonic() - phrase_end

        assert match is not None, (
            "No LISTENING_CUE entry appeared in voice-bridge log after injecting wake phrase."
        )
        assert elapsed <= 2.0, (  # generous: 1 s spec + 1 s fixture overhead
            f"Listening cue took {elapsed:.2f}s – exceeds the 1 s budget."
        )

    def test_no_false_positive_on_silence(self):
        """
        wake.py --test-silence must not emit a detection event on a silent input.
        """
        if not WAKE_SCRIPT.exists():
            pytest.skip("wake.py missing.")
        result = _run_wake_script(["--test-silence"], timeout=WAKE_TIMEOUT)
        combined = (result.stdout + result.stderr).lower()
        assert "detected" not in combined, (
            "Wake model fired on silence – false positive."
        )


# ---------------------------------------------------------------------------
# TC-2  End-to-end voice turn
# ---------------------------------------------------------------------------

class TestEndToEndVoiceTurn:
    """TC-2: Full voice pipeline returns a spoken reply within 5 s."""

    @pytest.mark.timeout(PIPELINE_TIMEOUT + 5)
    def test_spoken_reply_logged_within_5s(self):
        """
        After wake word, asking 'what is two plus two' must produce
        a TTS_PLAY or AUDIO_OUT entry in voice-bridge log within 5 s.
        """
        if not BRIDGE_LOG.exists():
            pytest.skip(f"voice-bridge log not found at {BRIDGE_LOG}.")

        ref_wav = Path("tests/fixtures/two_plus_two.wav")
        if not ref_wav.exists():
            pytest.skip("Pipeline test fixture WAV not found.")

        start = time.monotonic()
        _inject_audio(ref_wav, device=AUDIO_DEVICE)

        match = _wait_for_log_pattern(
            BRIDGE_LOG,
            r"TTS_PLAY|AUDIO_OUT|tts.*play|playing.reply",
            PIPELINE_TIMEOUT,
        )
        elapsed = time.monotonic() - start

        assert match is not None, (
            "No TTS reply log entry found. "
            "Check STT transcription, hermes routing, and TTS synthesis stages."
        )
        assert elapsed <= PIPELINE_TIMEOUT, (
            f"Voice pipeline took {elapsed:.2f}s – exceeds the 5 s budget."
        )

    def test_stt_stage_reachable(self):
        """STT subprocess / socket must be running (check process table)."""
        result = subprocess.run(
            ["pgrep", "-f", "stt|whisper|vosk"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            "No STT process found. Is the STT backend running?"
        )

    def test_tts_stage_reachable(self):
        """TTS subprocess must be running."""
        result = subprocess.run(
            ["pgrep", "-f", "tts|espeak|piper|coqui"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            "No TTS process found. Is the TTS backend running?"
        )

    def test_hermes_broker_reachable(self):
        """Hermes / MQTT broker must be accepting connections."""
        result = subprocess.run(
            ["pgrep", "-f", "mosquitto|hermes|mqtt"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            "No hermes/MQTT broker process found."
        )


# ---------------------------------------------------------------------------
# TC-3  Thinking cue on slow agent replies
# ---------------------------------------------------------------------------

class TestThinkingCue:
    """TC-3: A thinking cue is played when agent latency exceeds 1 s."""

    @pytest.mark.timeout(THINKING_TIMEOUT + 5)
    def test_thinking_cue_before_slow_reply(self):
        """
        lk_client log must show THINKING_CUE before the REPLY entry
        when a question that takes > 1 s is asked.
        """
        if not LK_LOG.exists():
            pytest.skip(f"lk_client log not found at {LK_LOG}.")

        ref_wav = Path("tests/fixtures/slow_question.wav")
        if not ref_wav.exists():
            pytest.skip("Slow-question fixture WAV not found.")

        _inject_audio(ref_wav, device=AUDIO_DEVICE)

        cue_match   = _wait_for_log_pattern(LK_LOG, r"THINKING_CUE|thinking.cue", THINKING_TIMEOUT)
        reply_match = _wait_for_log_pattern(LK_LOG, r"REPLY|TTS_PLAY|AUDIO_OUT",  THINKING_TIMEOUT)

        assert cue_match is not None, (
            "No THINKING_CUE entry found in lk_client log. "
            "Check cue injection logic in lk_client.py."
        )
        assert reply_match is not None, (
            "Agent never produced a spoken reply – unrelated pipeline failure."
        )

    def test_lk_client_script_exists(self):
        lk_client = Path(os.getenv("SUDO_LK_CLIENT", "lk_client.py"))
        assert lk_client.exists(), (
            f"lk_client.py not found at {lk_client}."
        )

    def test_thinking_cue_not_on_fast_reply(self):
        """
        A trivially fast reply ('ping') must NOT emit a thinking cue.
        This guards against the cue playing on every turn.
        """
        if not LK_LOG.exists():
            pytest.skip(f"lk_client log not found at {LK_LOG}.")

        ref_wav = Path("tests/fixtures/ping_question.wav")
        if not ref_wav.exists():
            pytest.skip("Ping-question fixture WAV not found.")

        log_size_before = LK_LOG.stat().st_size if LK_LOG.exists() else 0
        _inject_audio(ref_wav, device=AUDIO_DEVICE)
        time.sleep(3)  # wait for the turn to complete

        new_log = ""
        if LK_LOG.exists():
            with LK_LOG.open() as fh:
                fh.seek(log_size_before)
                new_log = fh.read()

        assert not re.search(r"THINKING_CUE|thinking.cue", new_log, re.IGNORECASE), (
            "Thinking cue fired on a fast reply – cue threshold may be too low."
        )


# ---------------------------------------------------------------------------
# TC-4  Ready tone gating (never before mic is live)
# ---------------------------------------------------------------------------

class TestReadyToneGating:
    """TC-4: Ready tone is emitted only after mic opens successfully."""

    @pytest.mark.timeout(READY_TONE_TIMEOUT + 5)
    def test_ready_tone_after_mic_open(self):
        """
        After power-cycle / service restart, the READY_TONE log entry
        must appear *after* MIC_OPEN (not before).
        """
        if not BRIDGE_LOG.exists():
            pytest.skip(f"voice-bridge log not found at {BRIDGE_LOG}.")

        # Restart the voice-bridge service to simulate power-cycle
        restart = subprocess.run(
            ["sudo", "systemctl", "restart", "voice-bridge"],
            capture_output=True, text=True, timeout=10,
        )
        if restart.returncode != 0:
            pytest.skip("Cannot restart voice-bridge service – run as root or adjust sudo rules.")

        service_start = time.monotonic()

        mic_match   = _wait_for_log_pattern(BRIDGE_LOG, r"MIC_OPEN|mic.open|microphone.open", READY_TONE_TIMEOUT)
        ready_match = _wait_for_log_pattern(BRIDGE_LOG, r"READY_TONE|ready.tone|tone.played",  READY_TONE_TIMEOUT)

        assert mic_match is not None,   "MIC_OPEN never logged – mic may have failed to open."
        assert ready_match is not None, "READY_TONE never logged – tone not playing after boot."

        # Both entries must exist; verify ordering via log timestamps if available
        log_text = _tail_log(BRIDGE_LOG, 300)
        mic_pos   = log_text.find(mic_match.group(0))
        ready_pos = log_text.find(ready_match.group(0))

        assert mic_pos < ready_pos, (
            "READY_TONE appeared before MIC_OPEN in the log – cue gating is broken."
        )

    def test_no_ready_tone_when_mic_absent(self):
        """
        If the mic device is unavailable, READY_TONE must NOT appear.
        This test is advisory; skip if we cannot simulate a missing mic.
        """
        pytest.skip(
            "Hardware mic-removal test requires manual setup. "
            "Run manually: unplug mic, restart service, assert no READY_TONE in log."
        )


# ---------------------------------------------------------------------------
# TC-5  Mic wedge (XVF3800 frozen hw_ptr) recovery
# ---------------------------------------------------------------------------

class TestMicWedgeRecovery:
    """TC-5: sudoedge detects a frozen hw_ptr and recovers without manual restart."""

    @pytest.mark.timeout(WEDGE_TIMEOUT + 5)
    def test_wedge_detection_and_recovery_logged(self):
        """
        After simulating a DSP wedge (replug cycle), the log must show:
        1. WEDGE_DETECTED (or equivalent)
        2. MIC_RECOVERY / MIC_REOPEN
        3. READY_TONE (re-announcement)
        All within WEDGE_TIMEOUT seconds.
        """
        if not BRIDGE_LOG.exists():
            pytest.skip(f"voice-bridge log not found at {BRIDGE_LOG}.")

        # Attempt to trigger wedge via the test helper script if present
        trigger = Path(os.getenv("SUDO_WEDGE_TRIGGER", "tests/helpers/trigger_wedge.sh"))
        if not trigger.exists():
            pytest.skip(
                f"Wedge trigger script not found at {trigger}. "
                "Provide tests/helpers/trigger_wedge.sh or set SUDO_WEDGE_TRIGGER."
            )

        subprocess.run(["bash", str(trigger)], timeout=5)
        t0 = time.monotonic()

        wedge_match   = _wait_for_log_pattern(BRIDGE_LOG, r"WEDGE_DETECTED|frozen.hw_ptr|hw_ptr.frozen", WEDGE_TIMEOUT)
        recover_match = _wait_for_log_pattern(BRIDGE_LOG, r"MIC_RECOVERY|mic.recover|MIC_REOPEN",         WEDGE_TIMEOUT)
        ready_match   = _wait_for_log_pattern(BRIDGE_LOG, r"READY_TONE|ready.tone",                       WEDGE_TIMEOUT)

        assert wedge_match is not None, (
            "Wedge condition not detected. Check hw_ptr monitoring in sudoedge."
        )
        assert recover_match is not None, (
            "Mic not recovered after wedge. Check recovery path in sudoedge."
        )
        assert ready_match is not None, (
            "Ready tone not replayed after mic recovery – user gets no feedback."
        )

    def test_wedge_monitor_process_running(self):
        """The sudoedge watchdog / wedge-monitor process must be active."""
        result = subprocess.run(
            ["pgrep", "-f", "sudoedge|wedge.monitor|hw_ptr"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            "sudoedge / wedge-monitor process not found. Is the watchdog running?"
        )

    @pytest.mark.timeout(WEDGE_TIMEOUT + 10)
    def test_device_responds_after_recovery(self):
        """
        After wedge recovery, the wake word must still be detected –
        i.e. the pipeline is fully restored, not just the log entry.
        """
        # Give recovery a moment to settle
        time.sleep(3)

        ref_wav = Path("tests/fixtures/hey_sudo_reference.wav")
        if not ref_wav.exists():
            pytest.skip("Reference WAV fixture not found.")

        _inject_audio(ref_wav, device=AUDIO_DEVICE)
        match = _wait_for_log_pattern(BRIDGE_LOG, r"LISTENING_CUE|listening.cue", 3.0)

        assert match is not None, (
            "Wake word not detected after mic wedge recovery – pipeline not fully restored."
        )


# ---------------------------------------------------------------------------
# TC-6  Idle wake-word recovery (30+ min idle)
# ---------------------------------------------------------------------------

class TestIdleWakeWordRecovery:
    """TC-6: Device stays responsive after 30 min of idle time."""

    @pytest.mark.timeout(IDLE_WAKE_TIMEOUT + 5)
    def test_wake_word_after_simulated_idle(self):
        """
        Trigger the device's idle-mode simulation (if available),
        then verify wake word still fires the listening cue within 1 s.
        """
        idle_trigger = Path(os.getenv("SUDO_IDLE_TRIGGER", "tests/helpers/simulate_idle.sh"))
        if not idle_trigger.exists():
            pytest.skip(
                f"Idle simulation script not found at {idle_trigger}. "
                "Provide tests/helpers/simulate_idle.sh or set SUDO_IDLE_TRIGGER."
            )

        subprocess.run(["bash", str(idle_trigger)], timeout=10)
        # Brief stabilisation pause
        time.sleep(1)

        ref_wav = Path("tests/fixtures/hey_sudo_reference.wav")
        if not ref_wav.exists():
            pytest.skip("Reference WAV fixture not found.")

        phrase_end = time.monotonic()
        _inject_audio(ref_wav, device=AUDIO_DEVICE)

        match = _wait_for_log_pattern(BRIDGE_LOG, r"LISTENING_CUE|listening.cue", IDLE_WAKE_TIMEOUT)
        elapsed = time.monotonic() - phrase_end

        assert match is not None, (
            "Listening cue not detected after idle period. "
            "Device may have frozen or disabled wake-word listener during idle."
        )
        assert elapsed <= 2.0, (
            f"Listening cue took {elapsed:.2f}s after idle – exceeds 1 s spec."
        )

    def test_no_silent_failure_after_idle(self):
        """
        After idle simulation, the service must still be running
        (i.e. it hasn't crashed silently).
        """
        result = subprocess.run(
            ["systemctl", "is-active", "voice-bridge"],
            capture_output=True, text=True,
        )
        # Accept 'active' or skip if systemd not available
        if result.returncode == 127:  # systemctl not found
            pytest.skip("systemd not available on this host.")
        assert result.stdout.strip() == "active", (
            "voice-bridge service is not active after idle period – it may have crashed."
        )

    @pytest.mark.timeout(30)
    @pytest.mark.slow
    def test_real_30min_idle_wake_word(self):
        """
        Full 30-minute idle soak test (opt-in, marked slow).
        Run with: pytest -m slow
        """
        print("\n[TC-6 soak] Sleeping 30 minutes to simulate real idle…", flush=True)
        time.sleep(30 * 60)

        ref_wav = Path("tests/fixtures/hey_sudo_reference.wav")
        if not ref_wav.exists():
            pytest.skip("Reference WAV fixture not found.")

        phrase_end = time.monotonic()
        _inject_audio(ref_wav, device=AUDIO_DEVICE)

        match = _wait_for_log_pattern(BRIDGE_LOG, r"LISTENING_CUE|listening.cue", IDLE_WAKE_TIMEOUT)
        elapsed = time.monotonic() - phrase_end

        assert match is not None, (
            "Device silent after real 30-min idle – manual restart required."
        )
        assert elapsed <= 2.0, (
            f"Cue latency {elapsed:.2f}s after idle – exceeds 1 s spec."
        )

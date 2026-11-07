"""Serial link with the Arduino Uno security prototype.

The sketch in the board communicates at 9600 baud and prints one message per
line.  This module turns those messages into small dictionaries that the UI
can consume, and keeps the serial port open in a background thread so the
window never blocks while waiting for the physical buttons.

Recognised lines (from the sketch):
    INTENTO REGISTRADO: 3
    NIVEL VERDE: ACTIVIDAD NORMAL
    NIVEL AMARILLO: ADVERTENCIA
    NIVEL ROJO: ALERTA DE SEGURIDAD
    ALARMA SONORA ACTIVADA
    !!! SISTEMA REINICIADO !!!
    Contador de intentos: 0
"""

from __future__ import annotations

import re
import threading

from PyQt6.QtCore import QThread, pyqtSignal

from .config import (
    ALERT_LEVEL_HIGH,
    ALERT_LEVEL_LOW,
    ALERT_LEVEL_MEDIUM,
    ARDUINO_AUTO_PORT,
    ARDUINO_BAUD_RATE,
    ARDUINO_READ_TIMEOUT_S,
    ARDUINO_RECONNECT_MS,
)

try:  # pyserial is optional at import time so the UI can still explain the error.
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - depends on the environment
    serial = None
    list_ports = None


# --- Protocol -----------------------------------------------------------------

ATTEMPT_PATTERN = re.compile(r"INTENTO\s+REGISTRADO\s*:\s*(\d+)", re.IGNORECASE)
RESET_PATTERN = re.compile(r"SISTEMA\s+REINICIADO", re.IGNORECASE)
LEVEL_PATTERN = re.compile(r"NIVEL\s+(VERDE|AMARILLO|ROJO)", re.IGNORECASE)
ALARM_PATTERN = re.compile(r"ALARMA\s+SONORA\s+ACTIVADA", re.IGNORECASE)

LEVEL_BY_COLOR = {
    "VERDE": ALERT_LEVEL_LOW,
    "AMARILLO": ALERT_LEVEL_MEDIUM,
    "ROJO": ALERT_LEVEL_HIGH,
}


def level_for_attempts(attempts: int) -> str:
    """Map the Arduino counter to the alert level shown by the monitor."""
    if attempts >= 7:
        return ALERT_LEVEL_HIGH
    if attempts >= 4:
        return ALERT_LEVEL_MEDIUM
    return ALERT_LEVEL_LOW


def parse_arduino_line(line: str) -> dict:
    """Convert one serial line into an event dictionary.

    The returned ``kind`` is one of: ``attempt``, ``level``, ``reset``,
    ``alarm``, ``empty`` or ``raw``.
    """
    clean = (line or "").strip()

    if not clean:
        return {"kind": "empty", "raw": clean}

    match = ATTEMPT_PATTERN.search(clean)
    if match:
        attempts = int(match.group(1))
        return {
            "kind": "attempt",
            "attempts": attempts,
            "level": level_for_attempts(attempts),
            "raw": clean,
        }

    if RESET_PATTERN.search(clean):
        return {"kind": "reset", "attempts": 0, "raw": clean}

    match = LEVEL_PATTERN.search(clean)
    if match:
        return {
            "kind": "level",
            "level": LEVEL_BY_COLOR[match.group(1).upper()],
            "raw": clean,
        }

    if ALARM_PATTERN.search(clean):
        return {"kind": "alarm", "level": ALERT_LEVEL_HIGH, "raw": clean}

    return {"kind": "raw", "raw": clean}


# --- Port discovery -----------------------------------------------------------

# USB chips commonly used by Arduino-compatible boards.
_ARDUINO_HINTS = (
    "arduino",
    "genuino",
    "ch340",
    "ch341",
    "wch",
    "ft232",
    "ftdi",
    "cp210",
    "usb serial",
    "usb-serial",
)


def list_serial_ports() -> list[tuple[str, str]]:
    """Return ``(device, description)`` pairs for the available ports."""
    if list_ports is None:
        return []

    ports = []
    for port in sorted(list_ports.comports(), key=lambda item: item.device):
        description = port.description or ""
        if description and description != "n/a":
            ports.append((port.device, description))
        else:
            ports.append((port.device, "Serial port"))
    return ports


def _looks_like_arduino(port) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            port.description,
            port.manufacturer,
            port.product,
            port.hwid,
        )
    ).lower()
    return any(hint in haystack for hint in _ARDUINO_HINTS)


def find_arduino_port() -> str | None:
    """Auto-detect a USB Arduino board, ignoring built-in serial ports."""
    if list_ports is None:
        return None

    ports = list(list_ports.comports())
    candidates = [port for port in ports if _looks_like_arduino(port)]

    if not candidates:
        # Fallback: real USB devices normally expose a VID.  This keeps
        # motherboards' ACPI COM1 from being selected by mistake.
        candidates = [port for port in ports if getattr(port, "vid", None) is not None]

    if not candidates:
        return None

    candidates.sort(key=lambda port: port.device)
    return candidates[0].device


# --- Background reader --------------------------------------------------------


class ArduinoReader(QThread):
    """Reads the Arduino serial port continuously and emits parsed lines."""

    line_received = pyqtSignal(str)
    connection_changed = pyqtSignal(bool, str)  # connected, port
    status_message = pyqtSignal(str)

    def __init__(self, port: str = ARDUINO_AUTO_PORT, parent=None):
        super().__init__(parent)
        self._port_setting = port or ARDUINO_AUTO_PORT
        self._wake = threading.Event()
        self._stopping = False
        self._active_port = ""
        self._last_message = ""

    # -- Public API --------------------------------------------------------

    @property
    def active_port(self) -> str:
        return self._active_port

    def set_port(self, port: str):
        """Select a port (or ``ARDUINO_AUTO_PORT``) and reopen immediately."""
        port = port or ARDUINO_AUTO_PORT
        if port == self._port_setting:
            return
        self._port_setting = port
        self._wake.set()

    def stop(self):
        """Ask the thread to finish and wait for the serial port to close."""
        self._stopping = True
        self._wake.set()
        self.wait(3000)

    # -- Thread ------------------------------------------------------------

    def run(self):
        if serial is None:
            self._emit_status(
                "pyserial no está instalado. Ejecuta: pip install pyserial"
            )
            return

        while not self._stopping:
            port_name = self._resolve_port()

            if not port_name:
                self._emit_status(
                    "Arduino no detectado. Conecta la placa por USB o elige el puerto."
                )
                self.connection_changed.emit(False, "")
                self._wait_or_wake()
                continue

            try:
                self._read_port(port_name)
            except (serial.SerialException, OSError) as error:
                self._emit_status(f"No se pudo abrir {port_name}: {error}")
                self.connection_changed.emit(False, port_name)

            if not self._stopping:
                self._wait_or_wake()

    def _resolve_port(self) -> str | None:
        if self._port_setting != ARDUINO_AUTO_PORT:
            return self._port_setting
        return find_arduino_port()

    def _read_port(self, port_name: str):
        self._wake.clear()
        self._active_port = port_name

        with serial.Serial(
            port_name,
            ARDUINO_BAUD_RATE,
            timeout=ARDUINO_READ_TIMEOUT_S,
        ) as connection:
            self._emit_status(f"Arduino conectado en {port_name}")
            self.connection_changed.emit(True, port_name)

            while not self._stopping:
                # If the user changed the port, reopen it right away.
                if self._wake.is_set():
                    break

                raw = connection.readline()

                if raw:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line:
                        self.line_received.emit(line)

        self._active_port = ""
        self.connection_changed.emit(False, "")

    def _wait_or_wake(self):
        self._wake.wait(ARDUINO_RECONNECT_MS / 1000)
        self._wake.clear()

    def _emit_status(self, message: str):
        if message != self._last_message:
            self._last_message = message
            self.status_message.emit(message)

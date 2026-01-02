"""
Dieses Modul stellt gemeinsame Hilfsfunktionen, globale Variablen und
Konstanten bereit, die von mehreren Modulen des Beast-Clients verwendet
werden.

Es enthält:
- Eine globale Liste aller Beasts (`GLOBAL_BEAST_LIST`)
- Eine Utility-Funktion zur konsistenten Konsolenausgabe (`print_and_flush`)
- Eine strukturierte Sammlung aller vom Server verwendeten Kommandos (`cmd`)
- Eine Shutdown-Routine, die das Programm kontrolliert beendet
"""

from collections import namedtuple
import os
import signal
import sys

GLOBAL_BEAST_LIST = []


def print_and_flush(message: str):
    """
    Zusammenfassung der Funktion: Gibt eine Nachricht aus und erzwingt das
    sofortige Flushen des Ausgabestreams.

    Dies stellt sicher, dass Nachrichten auch in Umgebungen mit asynchroner
    Protokollierung oder Puffern sofort sichtbar sind (z. B. Logging über
    Pipes oder WebSocket-Ausgaben).

    Args:
        message (str): Die auszugebende Zeichenkette.

    Returns:
        None
    """

    print(message)
    sys.stdout.flush()


Command = namedtuple(
    "Command",
    [
        "BEAST_COMMAND_REQUEST",
        "BEAST_GONE_INFO",
        "NO_BEASTS_LEFT_INFO",
        "SHUTDOWN_INFO",
        "MOVE",
        "SPLIT",
    ],
)

cmd = Command(
    BEAST_COMMAND_REQUEST="BEAST_COMMAND_REQUEST",
    BEAST_GONE_INFO="BEAST_GONE_INFO",
    NO_BEASTS_LEFT_INFO="NO_BEASTS_LEFT_INFO",
    SHUTDOWN_INFO="SHUTDOWN_INFO",
    MOVE="MOVE",
    SPLIT="SPLIT",
)


async def handle_shutdown():
    """
    Zusammenfassung der Funktion: Führt einen kontrollierten Programm-Shutdown aus.

    Die Funktion dient als zentraler Punkt für das Beenden des Clients.
    Sie gibt zunächst eine Abschiedsnachricht aus und sendet anschließend
    ein SIGTERM-Signal an den aktuellen Prozess, um das Programm sauber
    zu beenden.

    Args:
        None

    Returns:
        None
    """

    print_and_flush("bye")
    sys.stdout.flush()
    os.kill(os.getpid(), signal.SIGTERM)

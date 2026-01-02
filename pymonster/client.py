"""
Dieses Modul stellt den Client für das Beast-Spiel bereit und übernimmt die
Verbindung zum Server.

Der Client baut eine gesicherte WebSocket-Verbindung zum Spielserver auf,
authentifiziert sich mit Benutzername und Passwortdatei, startet die
asynchrone Client-Schleife und leitet eingehende Servernachrichten an die
Steuerungslogik weiter. Außerdem stellt das Modul einen CLI-Einstiegspunkt
bereit, um den Client über die Kommandozeile zu starten.
"""

import argparse
import asyncio
import ssl
import websockets
from . import utils
from websockets.exceptions import ConnectionClosed
from .utils import print_and_flush, handle_shutdown
from .controller import control_cmd
from .beast import Beast
from .logger import log_server

# accept self-signed certificate
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

################################################################################
# No need to change functionality below this line
# You should remove most of the debug print statements to save disk space.
################################################################################


async def client_loop(
    username: str, password_file_name: str, hostname: str, port: int
):
    """
    Zusammenfassung der Funktion: Baut eine gesicherte WebSocket-Verbindung
    zum Server auf und führt die asynchrone Client-Schleife aus.

    Die Funktion liest zunächst das Passwort aus einer Datei, stellt dann
    eine TLS-gesicherte WebSocket-Verbindung zum Spielserver her und
    führt einen einfachen Login-Handshake aus. Anschließend wird in einer
    Endlosschleife auf Nachrichten vom Server gewartet und jede Nachricht
    zur weiteren Verarbeitung an control_cmd() übergeben. Wenn der Server
    einen Shutdown signalisiert oder die Verbindung schließt, wird die
    Schleife beendet und ein geordneter Shutdown ausgelöst.

    Args:
        username (str): Benutzername für die Authentifizierung am Server.
        password_file_name (str): Pfad zur Datei, die das Passwort für die
            Authentifizierung enthält (abschließende Leerzeichen werden entfernt).
        hostname (str): Hostname oder IP-Adresse des WebSocket-Servers.
        port (int): TCP-Portnummer des WebSocket-Servers.

    Returns:
        None

    Raises:
        FileNotFoundError: Wenn die Passwortdatei nicht gefunden wird.
        PermissionError: Wenn auf die Passwortdatei nicht zugegriffen werden kann.
        IsADirectoryError: Wenn password_file_name auf ein Verzeichnis zeigt.
        ConnectionClosedError: Wenn die WebSocket-Verbindung unerwartet
            während des Empfangens von Nachrichten geschlossen wird.
    """

    try:
        with open(password_file_name, "r", encoding="utf-8") as password_file:
            password = password_file.read().rstrip("\n")
            password = password.strip()
            log_server("SUCCESS", "Read password_file successfully")
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        log_server("ERROR", "Error reading Password file")
        raise type(e)("Error reading Password file") from e

    async with websockets.connect(
        f"wss://{hostname}:{port}/login",
        ssl=ssl_context,
    ) as websocket:
        await websocket.send(f"{username}:{password}")
        server_str = await websocket.recv()
        log_server("SMSG", f"{server_str!r}")
        print_and_flush(f"Reply from server: {server_str!r}")
        # Biest hier intitalisieren
        my_beast = Beast()
        utils.GLOBAL_BEAST_LIST.append(my_beast)
        while True:
            try:
                server_str = await websocket.recv()
                # log_server("SMSG", f"{server_str!r}") #logt den Serverstring in unseren Logs
                # print_and_flush(f"{server_str = }")
                # warten auf control_cmd() weil es async ist
                keep_running = await control_cmd(
                    server_str, websocket, my_beast
                )
                if not keep_running:
                    break
            except websockets.ConnectionClosedError:
                print_and_flush("Connection closed by server")
                log_server("ERROR", "Connection closed by server")
                break
        await handle_shutdown()


def client_main():
    """
    Zusammenfassung der Funktion: Parst die Kommandozeilenargumente und
    startet die asynchrone Client-Schleife.

    Die Funktion legt einen ArgumentParser an, liest Benutzername,
    Passwortdatei, Hostname und Port aus der Kommandozeile und ruft
    anschließend client_loop() mit diesen Parametern über asyncio.run()
    auf. Wird die Verbindung vom Server geschlossen, wird die Ausnahme
    abgefangen und eine entsprechende Meldung ausgegeben und geloggt.

    Args:
        None

    Returns:
        None
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="User name for authentification")
    parser.add_argument(
        "password_file_name",
        help="Name of File containing Password for authentification.",
    )
    parser.add_argument(
        "-n", "--hostname", type=str, help="Host name", default="localhost"
    )
    parser.add_argument(
        "-p", "--port", type=int, help="Port number", default=9721
    )
    args = parser.parse_args()
    try:
        asyncio.run(
            client_loop(
                args.username,
                args.password_file_name,
                args.hostname,
                args.port,
            )
        )
    except ConnectionClosed:
        print_and_flush("Connection closed by server")
        log_server("ERROR", "Connection closed by server")


if __name__ == "__main__":
    client_main()

"""
Dieses Modul steuert die Verarbeitung aller Serverbefehle für den Beast-Client.

Es enthält die Logik zur Rollenzuteilung (z. B. Farmer, Hunter, Backbag),
wertet empfangene Serverkommandos aus, aktualisiert die Zustände der Beasts
und erstellt neue Beasts bei einem erfolgreichen Split. Außerdem stellt es
das zentrale Steuerelement `control_cmd()` bereit, welches alle eingehenden
Nachrichten des Servers interpretiert und passende Aktionen ausführt.
"""

import random
from . import utils
from .utils import print_and_flush, cmd
from .logic import (
    handle_beast_gone,
    handle_no_beasts_left,
    decide_action,
)
from .beast import Beast
from .logger import log_server


# Rollen-Presets: hier kannst du später einfach Zahlen anpassen oder Rollen hinzufügen
ROLE_CONFIGS = {
    "farmer": {
        "food": 40,
        "hunt": 7,
        "kill": 35,
        "escape": 85,
        "energy": 3.0,
    },
    "hunter": {
        "food": 30,
        "hunt": 5,
        "kill": 40,
        "escape": 120,
        "energy": 3.0,
    },
    "backbag": {
        "food": 35,
        "hunt": 25,
        "kill": 11,
        "escape": 80,
        "energy": 1.8,
    },
}


def choose_role_by_score(score):
    """
    Zusammenfassung der Funktion: Wählt eine Rolle für ein Beast basierend auf
    einem Leistungswert (Score).

    Je nach Score wird eine defensive, ausgewogene oder offensive Rolle
    probabilistisch ausgewählt. Dies erlaubt es neuen Beasts, in ihrer
    Spielweise variabel zu sein und sich der Spielsituation anzupassen.

    Args:
        score (float): Leistungswert des Beasts (z. B. Energie / Rundenanzahl).

    Returns:
        str: Name der gewählten Rolle ("farmer", "hunter" oder "backbag").
    """

    if score < 1.25:
        # wir stehen schlecht -> defensiv / sparen
        weights = {
            "farmer": 0.2,
            "hunter": 0.1,
            "backbag": 0.7,  # Backbag dominiert im Low-Score
        }
    elif score < 2.5:
        # mittel -> Mix
        weights = {
            "farmer": 0.40,
            "hunter": 0.30,
            "backbag": 0.30,
        }
    else:
        # wir stehen sehr gut -> mehr Hunter/Offensiv
        weights = {
            "farmer": 0.4,
            "hunter": 0.5,
            "backbag": 0.1,
        }

    roles = list(weights.keys())
    probs = list(weights.values())
    return random.choices(roles, weights=probs, k=1)[0]


def apply_role_to_beast(beast: Beast, role_name: str) -> None:
    """
    Zusammenfassung der Funktion: Überträgt eine Rollen-Konfiguration
    auf ein Beast.

    Jede Rolle legt fest, wie stark das Beast Futter priorisiert, wie weit
    es Gegner jagt, wann es fliehen soll oder welche max. Move-Energie es
    besitzt. Diese Werte werden als Prioritäten in das Beast geschrieben.

    Args:
        beast (Beast): Das zu konfigurierende Beast.
        role_name (str): Rollenname entsprechend ROLE_CONFIGS.

    Returns:
        None
    """

    cfg = ROLE_CONFIGS[role_name]
    beast.set_priority_food(cfg["food"])
    beast.set_priority_hunt(cfg["hunt"])
    beast.set_priority_kill(cfg["kill"])
    beast.set_priority_escape(cfg["escape"])
    beast.set_priority_energy(cfg["energy"])


async def control_cmd(server_str, websocket, my_beast):
    """
    Zusammenfassung der Funktion: Hauptsteuerung zur Verarbeitung von
    Servernachrichten und zum Ausführen der passenden Aktionen.

    Diese Funktion wird für jedes eingehende Serverkommando aufgerufen.
    Je nach Nachricht werden Energie und Environment aktualisiert, eine
    Aktion berechnet, neue Beasts erstellt, tote Beasts entfernt oder der
    Client ordnungsgemäß beendet.

    Args:
        server_str (str): Das vom Server empfangene Kommando.
        websocket (WebSocketClientProtocol): Aktive WebSocket-Verbindung.
        my_beast (Beast): Das Haupt-Beast des Clients. Bei Splits können
            weitere Beasts hinzukommen.

    Returns:
        bool:
            True  – Client soll weiterlaufen.
            False – Server signalisiert Shutdown → Client beendet sich.

    Raises:
        ValueError: Falls das empfangene Format unerwartet ist.
    """

    match server_str:
        case cmd.BEAST_COMMAND_REQUEST:
            id_energy_env = await websocket.recv()
            # print_and_flush(f"{id_energy_env = }")
            (
                beast_id_str,
                energy_str,
                environment_str,
            ) = id_energy_env.split("#")
            beast_id = int(beast_id_str)
            energy = float(energy_str)
            environment_str = str(environment_str)
            # initalisierungen damit sie existieren bevor sie genutzt werden
            found = False
            server_command = None
            new_abs_x = None
            new_abs_y = None
            abs_round = None

            for beast in utils.GLOBAL_BEAST_LIST:
                beast_id_list = beast.get_id()
                if beast_id == beast_id_list:
                    beast.set_energy(energy)
                    beast.set_environment(environment_str)
                    server_command, (new_abs_x, new_abs_y), abs_round = (
                        decide_action(beast)
                    )
                    found = True
                    break

            if not found:  # Wird nur bei dem ersten Biest ausgeführt
                my_beast.set_id(beast_id)
                my_beast.set_energy(energy)
                my_beast.set_environment(environment_str)
                server_command, (new_abs_x, new_abs_y), abs_round = (
                    decide_action(my_beast)
                )

            # Biest hier mit Setter überschreiben
            # print_and_flush(f'sending "{server_command}"')
            await websocket.send(server_command)
            server_str = await websocket.recv()
            if "ERROR" in server_str:
                print_and_flush(server_str)
                success_str = "False"
                new_beast_id_str = "None"
            else:
                new_beast_id_str, success_str = server_str.split("#")
            # erfolgreicher split
            if success_str == "True" and new_beast_id_str != "None":
                new_beast_id = int(new_beast_id_str)
                # Erstellt ein neues Biest
                split_energy = energy / 2
                score = split_energy / abs_round
                new_beast = Beast()
                new_beast.set_id(new_beast_id)
                new_beast.set_abs_x(new_abs_x)
                new_beast.set_abs_y(new_abs_y)
                new_beast.set_round_abs(abs_round)

                # neue Bestie bekommt eine zufällige Rolle
                role_name = choose_role_by_score(score)
                apply_role_to_beast(new_beast, role_name)

                utils.GLOBAL_BEAST_LIST.append(new_beast)
                log_server("S_R", server_str)

            return True

        case cmd.BEAST_GONE_INFO:
            id_energy_env = await websocket.recv()
            print_and_flush(f"{id_energy_env = }")
            (
                beast_id_str,
                energy_str,
                environment_str,
            ) = id_energy_env.split("#")
            beast_id = int(beast_id_str)
            energy = float(energy_str)
            environment_str = str(environment_str)
            await handle_beast_gone(beast_id, energy, environment_str)
            return True
        case cmd.NO_BEASTS_LEFT_INFO:
            await handle_no_beasts_left()
            return True
        case cmd.SHUTDOWN_INFO:
            return False
        # default, damit unser Client nicht stoppt
        case _:
            print_and_flush(f"Unknown server message: {server_str!r}")
            return True

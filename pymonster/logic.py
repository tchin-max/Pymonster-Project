"""
Dieses Modul enthält die zentrale Spiel-Logik für die Beasts.

Es stellt Hilfsfunktionen für Koordinaten-Wrapping, Kollisionsprüfungen,
Energie- und Move-Berechnung bereit und bündelt in `decide_action()` die
Entscheidung, ob ein Beast sich bewegt oder splittet. Zusätzlich werden
Ereignisse wie das Verschwinden eines Beasts oder das Ende aller Beasts
behandelt.
"""

import math
from . import utils
import numpy as np
from .utils import print_and_flush, cmd, handle_shutdown
from .logger import log_beast

HIGH_ENERGY_THRESHOLD = 100  # für high_energy boolean in flee_advanced()
FIELD_WIDTH = 71
FIELD_HEIGHT = 34

MIN_ABS_X = -(FIELD_WIDTH // 2)  # -35
MAX_ABS_X = MIN_ABS_X + FIELD_WIDTH - 1  # 35  -> [-35..35]

MIN_ABS_Y = -(FIELD_HEIGHT // 2)  # -17
MAX_ABS_Y = MIN_ABS_Y + FIELD_HEIGHT - 1  # 16  -> [-17..16]


def filter_valid_moves(arr, limit=3):
    """
    Zusammenfassung der Funktion: Filtert ein Array von Moves auf einen
    erlaubten Wertebereich.

    Es werden nur diejenigen Tupel (dx, dy) beibehalten, deren Betrag in
    beiden Komponenten im Intervall [-limit, limit] liegt. Leere Arrays
    werden als leeres (0, 2)-Array zurückgegeben.

    Args:
        arr (numpy.ndarray): 2D-Array mit Moves der Form [[dx, dy], ...].
        limit (int): Maximal zulässiger Betrag pro Koordinate.

    Returns:
        numpy.ndarray: Gefiltertes 2D-Array mit gültigen Moves.
    """

    if arr.size == 0:
        # Gibt das leere Array sofort zurück, wenn es leer ist.
        # print(arr)
        return np.zeros((0, 2), dtype=int)
    else:
        mask = np.all(
            np.abs(arr) < limit, axis=1
        )  # Die Maske filtert nach allen Betragstupeln die kleiner als N = 3 sind
        return arr[mask]


def array_to_dict(arr, priority):
    """
    Zusammenfassung der Funktion: Wandelt ein Move-Array in ein
    Prioritäten-Dictionary um.

    Jedes Move (dx, dy) aus dem Array wird als Schlüssel in ein Dictionary
    übernommen. Die Priorität startet beim übergebenen Wert und wird für
    jeden folgenden Eintrag um 1 dekrementiert.

    Args:
        arr (numpy.ndarray): 2D-Array mit Moves der Form [[dx, dy], ...].
        priority (int): Startwert für die Priorisierung des ersten Moves.

    Returns:
        dict[tuple[int, int], int]: Dictionary von Move-Tupeln auf Prioritätswerte.
    """

    move_dict = {}

    current_priority = priority

    for move in arr:
        move_tuple = tuple(move)

        move_dict[move_tuple] = current_priority

        current_priority -= 1

    return move_dict


def merge_dict(*dicts):
    """
    Zusammenfassung der Funktion: Führt mehrere Move-Prioritäten-Dictionaries
    zusammen und addiert die Prioritäten gleicher Moves.

    Wenn ein Move in mehreren Dictionaries vorkommt, werden seine Werte
    summiert. Nicht doppelt vorkommende Moves werden einfach übernommen.

    Args:
        *dicts (dict[tuple[int, int], int]): Beliebig viele Dictionaries
            mit Move-Prioritäten.

    Returns:
        dict[tuple[int, int], int]: Zusammengeführtes Dictionary mit
        aufsummierten Prioritäten.
    """

    merge_dict = {}

    for d in dicts:
        for move, priority in d.items():
            if move in merge_dict:
                merge_dict[move] += priority
            else:
                merge_dict[move] = priority

    return merge_dict


def calc_move_energy(move_tuple):
    """
    Zusammenfassung der Funktion: Berechnet die Energie (Distanz) eines Moves.

    Die Energie eines Moves wird als euklidische Distanz vom Ursprung zum
    Punkt (dx, dy) interpretiert und mit math.hypot() berechnet.

    Args:
        move_tuple (tuple[int, int]): Move als Tupel (dx, dy).

    Returns:
        float: Euklidische Distanz des Moves.
    """

    x = move_tuple[0]
    y = move_tuple[1]

    # berechnet die Hypothenuse für die energy
    energy = math.hypot(x, y)

    return energy


def wrap_centered(value: int, min_v: int, max_v: int) -> int:
    """
    Zusammenfassung der Funktion: Wrappt einen Zahlenwert toroidal in
    einen vorgegebenen Bereich.

    Der Wert wird so umgerechnet, dass er immer im Intervall [min_v, max_v]
    liegt. Dabei wird modulo über die Spannweite gerechnet, sodass auch
    negative Werte korrekt in den Bereich zurückgeführt werden.

    Args:
        value (int): Ursprünglicher Wert (z. B. Koordinate).
        min_v (int): Untere Grenze des erlaubten Bereichs.
        max_v (int): Obere Grenze des erlaubten Bereichs.

    Returns:
        int: In den Bereich [min_v, max_v] gewrappter Wert.
    """

    span = max_v - min_v + 1
    return ((value - min_v) % span) + min_v


def wrap_abs_coords(x: int, y: int) -> tuple[int, int]:
    """
    Zusammenfassung der Funktion: Wrappt absolute Spielfeldkoordinaten
    in den erlaubten Spielfeldbereich.

    Die Funktion nimmt an, dass (0, 0) im Zentrum des Spielfelds liegt und
    nutzt wrap_centered(), um x- und y-Koordinaten getrennt in den Bereich
    [MIN_ABS_X, MAX_ABS_X] bzw. [MIN_ABS_Y, MAX_ABS_Y] zu bringen.

    Args:
        x (int): Absolute X-Koordinate.
        y (int): Absolute Y-Koordinate.

    Returns:
        tuple[int, int]: Gewrappte Koordinate (x, y) im Spielfeld.
    """

    wrapped_x = wrap_centered(x, MIN_ABS_X, MAX_ABS_X)
    wrapped_y = wrap_centered(y, MIN_ABS_Y, MAX_ABS_Y)
    return wrapped_x, wrapped_y


def check_beast_collision(move, abs_x, abs_y):
    """
    Zusammenfassung der Funktion: Prüft, ob ein geplanter Move zu einer
    Kollision mit einem anderen eigenen Beast führt.

    Der Move wird auf die aktuelle absolute Position (abs_x, abs_y)
    angewendet, anschließend über wrap_abs_coords() gewrapped und dann
    gegen alle Einträge in utils.GLOBAL_BEAST_LIST verglichen. Falls
    irgendein Beast bereits auf der Zielposition steht, liegt eine
    Kollision vor.

    Args:
        move (tuple[int, int]): Geplanter Move (dx, dy) relativ zur aktuellen Position.
        abs_x (int): Aktuelle absolute X-Position des Beasts.
        abs_y (int): Aktuelle absolute Y-Position des Beasts.

    Returns:
        bool: True, wenn keine Kollision mit einem eigenen Beast entsteht,
        sonst False.
    """

    dx = move[0]
    dy = move[1]
    new_abs_x = abs_x + dx
    new_abs_y = abs_y + dy

    # Check Wrap
    new_abs_x, new_abs_y = wrap_abs_coords(new_abs_x, new_abs_y)

    # Prüft das das Biest nicht kollidiert
    for beast in utils.GLOBAL_BEAST_LIST:
        ally_abs_x = beast.get_abs_x()
        ally_abs_y = beast.get_abs_y()
        if ally_abs_x == new_abs_x and ally_abs_y == new_abs_y:
            return False

    return True


def valid_first_move(sorted_moves, current_energy, abs_x, abs_y):
    """
    Zusammenfassung der Funktion: Wählt den ersten gültigen Move aus einer
    priorisierten Liste von Moves aus.

    Die Moves werden in absteigender Priorität geprüft. Ein Move ist gültig,
    wenn
      - keine Kollision mit einem eigenen Beast entsteht,
      - der Move nicht (0, 0) ist und
      - die benötigte Energie kleiner oder gleich current_energy ist.
    Wird kein gültiger Move gefunden, wird (0, 0) mit Energie 0.0 und
    Priorität 0 zurückgegeben.

    Args:
        sorted_moves (list[tuple[tuple[int, int], int]]): Liste von
            (Move, Priorität)-Tupeln, absteigend sortiert.
        current_energy (float): Aktuell verfügbare Energie des Beasts.
        abs_x (int): Aktuelle absolute X-Position des Beasts.
        abs_y (int): Aktuelle absolute Y-Position des Beasts.

    Returns:
        tuple[tuple[int, int], float, int]:
            - Gültiger Move (dx, dy) oder (0, 0), wenn keiner passt.
            - Energiebedarf des Moves als float.
            - Prioritätswert des Moves.
    """

    for (dx, dy), prio in sorted_moves:
        move = (int(dx), int(dy))
        no_collision = check_beast_collision(move, abs_x, abs_y)
        if not no_collision:
            continue

        if move == (0, 0):
            continue

        move_energy = calc_move_energy(move)
        if move_energy <= current_energy:
            return move, move_energy, prio
        else:
            continue
    return (0, 0), 0.0, 0  # "Der Energieverbauch für diesen Move ist zu Hoch"


def decide_action(curr_beast):
    """
    Zusammenfassung der Funktion: Entscheidet die nächste Aktion eines Beasts
    (MOVE oder SPLIT) und berechnet den entsprechenden Serverbefehl.

    Die Funktion aktualisiert ggf. die Energie-Priorität, ruft die
    Bewegungs- und Entscheidungslogik des Beasts auf (chase_food, hunt,
    compute_kill_list, escape, split) und entscheidet dann:
      - SPLIT: wenn split() dies erlaubt, inklusive Berechnung der
        neuen absoluten Position.
      - MOVE: basierend auf den kombinierten Listen von Food-, Hunt-,
        Kill- und Escape-Moves werden Prioritäten gemischt, gültige
        Moves gefiltert und der beste Move gewählt.

    Am Ende werden die Runden-Counter des Beasts erhöht und relevante
    Informationen stehen für Logging bereit.

    Args:
        curr_beast: Instanz der Beast-Klasse, für die die Aktion
            berechnet wird.

    Returns:
        tuple[str, tuple[int, int], int]:
            - server_command (str): Protokollkonformer Befehlsstring
              (z. B. "1 MOVE 1 0" oder "1 SPLIT 0 -1").
            - (new_abs_x, new_abs_y): Neue absolute Position des Beasts.
            - abs_r (int): Neue absolute Rundenzahl nach der Aktion.
    """

    abs_r = curr_beast.get_round_abs()
    if abs_r > 100:
        curr_beast.set_priority_energy(1.9)
    # Holt sich wichtig Atribute des Beasts
    bid = curr_beast.get_id()
    abs_x = curr_beast.get_abs_x()
    abs_y = curr_beast.get_abs_y()

    # Ruft die Module auf
    curr_beast.chase_food()
    curr_beast.hunt()
    curr_beast.compute_kill_list()
    curr_beast.escape()
    split_pos, do_split = curr_beast.split()

    # Überprüft ob ein Split statt finden soll
    if do_split:
        chosen_cmd = "SPLIT"

        d_x = split_pos[0]
        d_y = split_pos[1]

        new_abs_x, new_abs_y = wrap_abs_coords(abs_x + d_x, abs_y + d_y)

        move = (d_x, d_y)
        server_command = f"{bid} {cmd.SPLIT} {d_x} {d_y}"

    # führt einen Move durch
    else:
        chosen_cmd = "MOVE"

        # holt sich die Listen
        food_list = curr_beast.get_food_list()
        hunt_list = curr_beast.get_hunt_list()
        kill_list = curr_beast.get_kill_list()
        escape_list = curr_beast.get_escape_list()

        # wandelt die Listen in np.arrays um
        food_arr_temp = np.array(food_list)
        hunt_arr_temp = np.array(hunt_list)
        kill_arr_temp = np.array(kill_list)
        escape_arr_temp = np.array(escape_list)

        # validiert die moves
        food_arr = filter_valid_moves(food_arr_temp)
        hunt_arr = filter_valid_moves(hunt_arr_temp)
        kill_arr = filter_valid_moves(kill_arr_temp)
        escape_arr = filter_valid_moves(escape_arr_temp)

        # macht mehrere Dictionary mit den arrays und die prioritäten
        food_dict = array_to_dict(food_arr, curr_beast.get_priority_food())
        hunt_dict = array_to_dict(hunt_arr, curr_beast.get_priority_hunt())
        kill_dict = array_to_dict(kill_arr, curr_beast.get_priority_kill())
        escape_dict = array_to_dict(
            escape_arr, curr_beast.get_priority_escape()
        )

        # verknüpft alle Dictonarys
        merged_dict = merge_dict(food_dict, hunt_dict, kill_dict, escape_dict)

        clean_dict = {
            tuple(int(k_val) for k_val in move): int(priority)
            for move, priority in merged_dict.items()
        }

        sorted_dict = sorted(
            clean_dict.items(), key=lambda item: item[1], reverse=True
        )

        current_energy = curr_beast.get_energy()

        move, energy, priority = valid_first_move(
            sorted_dict, current_energy, abs_x, abs_y
        )

        # print(f"\nBest Move: {move} mit Priorität {priority} kosten Energy {energy}")
        d_x = move[0]
        d_y = move[1]

        new_abs_x, new_abs_y = wrap_abs_coords(abs_x + d_x, abs_y + d_y)

        curr_beast.set_abs_x(new_abs_x)
        curr_beast.set_abs_y(new_abs_y)
        server_command = f"{bid} {cmd.MOVE} {d_x} {d_y}"

    # Runden Erhöhen um 1
    curr_beast.set_round_abs(1)
    curr_beast.set_round_rel(1)

    # Log Aufruf
    abs_r = curr_beast.get_round_abs()
    rel_r = curr_beast.get_round_rel()
    energy = curr_beast.get_energy()
    environment = curr_beast.get_environment()
    # move
    # position
    abs_x = curr_beast.get_abs_x()
    abs_y = curr_beast.get_abs_y()
    # listen und prios
    food_list = curr_beast.get_food_list()
    priority_food = curr_beast.get_priority_food()
    hunt_list = curr_beast.get_hunt_list()
    priority_hunt = curr_beast.get_priority_hunt()
    kill_list = curr_beast.get_kill_list()
    priority_kill = curr_beast.get_priority_kill()
    escape_list = curr_beast.get_escape_list()
    priority_escape = curr_beast.get_priority_escape()
    priority_energy = curr_beast.get_priority_energy()

    log_beast(
        abs_r=abs_r,
        rel_r=rel_r,
        bid=bid,
        cmd=chosen_cmd,
        e=energy,
        env=environment,
        move=move,
        abs_x=abs_x,
        abs_y=abs_y,
        fl=food_list,
        pf=priority_food,
        hl=hunt_list,
        ph=priority_hunt,
        kl=kill_list,
        pk=priority_kill,
        el=escape_list,
        pe=priority_escape,
        pen=priority_energy,
    )

    return server_command, (new_abs_x, new_abs_y), abs_r


async def handle_beast_gone(
    beast_id: int,
    energy: float,
    environment: str,
) -> None:
    """
    Zusammenfassung der Funktion: Behandelt den Fall, dass ein Beast stirbt
    (verhungert oder gefressen wird).

    Das entsprechende Beast wird aus der GLOBAL_BEAST_LIST entfernt und
    eine kurze Textmeldung mit ID, Energie und Umgebung wird ausgegeben.

    Args:
        beast_id (int): ID des verstorbenen Beasts.
        energy (float): Restenergie des Beasts zum Zeitpunkt des Todes.
        environment (str): Umgebung als 1D-String aus Sicht des Beasts.

    Returns:
        None
    """

    for beast in utils.GLOBAL_BEAST_LIST:
        beast_id_list = beast.get_id()
        if beast_id == beast_id_list:
            utils.GLOBAL_BEAST_LIST.remove(beast)

    print_and_flush(f"beast {beast_id} with energy {energy} gone")
    print_and_flush(f"  environment: {environment}")


async def handle_no_beasts_left() -> None:
    """
    Zusammenfassung der Funktion: Reagiert auf die Situation, dass keine
    Beasts mehr im Spiel sind.

    Es wird eine einfache Meldung ausgegeben und anschließend ein geordneter
    Shutdown über handle_shutdown() ausgelöst.

    Args:
        None

    Returns:
        None
    """

    print_and_flush("No beasts left")
    await handle_shutdown()

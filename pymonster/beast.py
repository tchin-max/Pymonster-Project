"""
Dieses Modul definiert die Beast-Klasse, die das Verhalten eines einzelnen
Beasts in einem 7x7-Sichtfeld innerhalb eines größeren Spielfelds steuert.

Das Beast kann Futter suchen, Gegner jagen, gefährliche Felder meiden,
Kill-Moves berechnen und sich bei passenden Bedingungen aufteilen.
"""

import random
import numpy as np
import math
from collections import OrderedDict
from . import utils
from .logic import wrap_abs_coords


class Beast:
    """
    Zusammenfassung der Klasse: Repräsentiert ein einzelnes Beast im Spielfeld
    und verwaltet dessen Status, Position und Entscheidungen.

    Die Beast-Klasse speichert ID, Energie, Position und Prioritäten für
    verschiedene Aktionen (Futter, Jagd, Flucht, Kill). Sie analysiert das
    aktuelle Sichtfeld, bewertet mögliche Moves und entscheidet anhand von
    Energie- und Spielsituation, ob sie sich bewegt, Gegner jagt, flieht oder
    sich in ein weiteres Beast aufteilt.
    """

    def __init__(self):
        """
        Zusammenfassung der Funktion: Initialisiert ein neues Beast mit
        Standardwerten für ID, Energie, Position und Prioritäten.

        Das Beast startet in der Mitte des lokalen 7x7-Sichtfeldes (3, 3),
        mit leerer Umweltbeschreibung und voreingestellten Prioritäten für
        Futter, Jagd, Flucht, Kill und Energieverbrauch. Listen für Food,
        Escape, Hunt und Kill werden ebenfalls leer initialisiert.
        """

        self._id = 0
        self._energy = 0.0
        self._environment = ""

        self._priority_food = 35
        self._priority_hunt = 10
        self._priority_kill = 40
        self._priority_escape = 90
        self._priority_energy = 3.0

        self.x = 3
        self.y = 3

        self._food_list = []
        self._escape_list = []
        self._hunt_list = []
        self._kill_list = []

        self._round_abs = 0
        self._round_rel = 0
        self._abs_x = 0
        self._abs_y = 0

    # Getter

    def get_id(self):
        return self._id

    def get_environment(self):
        return self._environment

    def get_energy(self):
        return self._energy

    def get_food_list(self):
        return self._food_list

    def get_escape_list(self):
        return self._escape_list

    def get_hunt_list(self):
        return self._hunt_list

    def get_priority_food(self):
        return self._priority_food

    def get_kill_list(self):
        return self._kill_list

    def get_priority_escape(self):
        return self._priority_escape

    def get_priority_hunt(self):
        return self._priority_hunt

    def get_priority_kill(self):
        return self._priority_kill

    def get_priority_energy(self):
        return self._priority_energy

    def get_round_abs(self):
        return self._round_abs

    def get_round_rel(self):
        return self._round_rel

    def get_abs_x(self):
        return self._abs_x

    def get_abs_y(self):
        return self._abs_y

    # Setter

    def set_id(self, updated_id):
        self._id = updated_id

    def set_energy(self, updated_energy: float):
        self._energy = updated_energy

    def set_environment(self, updated_environment):
        self._environment = updated_environment

    def set_priority_food(self, updated_priority_food):
        self._priority_food = updated_priority_food

    def set_priority_escape(self, updated_priority_escape):
        self._priority_escape = updated_priority_escape

    def set_priority_hunt(self, updated_priority_hunt):
        self._priority_hunt = updated_priority_hunt

    def set_priority_kill(self, updated_priority_kill):
        self._priority_kill = updated_priority_kill

    def set_priority_energy(self, updated_priority_energy: float):
        self._priority_energy = updated_priority_energy

    def set_kill_list(self, updated_kill_list):
        self._kill_list = updated_kill_list

    def set_food_list(self, updated_food_list):
        self._food_list = updated_food_list

    def set_escape_list(self, updated_escape_list):
        self._escape_list = updated_escape_list

    def set_hunt_list(self, updated_hunt_list):
        self._hunt_list = updated_hunt_list

    def set_round_abs(self, round_increment):
        self._round_abs += round_increment

    def set_round_rel(self, round_increment):
        self._round_rel += round_increment

    def set_abs_x(self, updated_abs_x):
        self._abs_x = updated_abs_x

    def set_abs_y(self, updated_abs_y):
        self._abs_y = updated_abs_y

    def parse_environment(self, env: str):
        """
        Zusammenfassung der Funktion: Wandelt einen linearen Environment-String
        in ein 7x7-Array um und setzt das Beast in die Mitte.

        Der Environment-String wird zeilenweise in eine Liste von Listen
        aufgeteilt, entsprechend der Spielfeldgröße (7x7). Anschließend wird
        an der zentralen Position das Zeichen 'B' gesetzt, um die Position
        des Beasts im Sichtfeld zu markieren.

        Args:
            env (str): Lineare Darstellung des 7x7-Sichtfeldes als String.

        Returns:
            numpy.ndarray: 2D-Array (7x7) mit den Zeichen des Environments,
            inklusive 'B' in der Mitte.
        """

        # Bestimmt die Länge einer Array Zeile bevor die nächste startet.
        N: int = 3
        size_game: int = 2 * N + 1

        # Macht aus dem String Environment eine Liste
        result = [
            list(env[element : element + size_game])
            for element in range(0, len(env), size_game)
        ]
        result[N][N] = "B"  # Biest steht in der Mitte bei 3,3

        numpy_env = np.array(result)
        return numpy_env

    #####################
    #  Chase-Food-Algo  #
    #####################

    def _is_safe_move(self, move: tuple[int, int]) -> bool:
        """
        Zusammenfassung der Funktion: Prüft, ob ein relativer Move kein
        Feld belegt, das bereits von einem eigenen Beast besetzt ist.

        Der relative Move (dx, dy) wird auf absolute Koordinaten umgerechnet,
        inklusive Spielfeld-Wrapping. Anschließend wird geprüft, ob auf diesem
        Ziel-Feld ein anderes Beast aus der GLOBAL_BEAST_LIST steht.

        Args:
            move (tuple[int, int]): Geplanter Move relativ zur aktuellen
                Position (dx, dy).

        Returns:
            bool: True, wenn das Zielfeld frei von eigenen Beasts ist,
            sonst False.
        """

        dx, dy = move

        # Berechnet die neuen Absolut Coords
        new_abs_x, new_abs_y = wrap_abs_coords(
            self._abs_x + dx, self._abs_y + dy
        )

        for beast in utils.GLOBAL_BEAST_LIST:
            # eigenes Beast überspringen für den Fall das wir stehen bleiben
            if beast.get_id() == self._id:
                continue

            if (
                beast.get_abs_x() == new_abs_x
                and beast.get_abs_y() == new_abs_y
            ):
                return (
                    False  # Auf diesen neuen Feld steht eins unserer Biester
                )

        return True  # Dieses Feld ist frei von unseren Biestern

    def random_move(self):
        """
        Zusammenfassung der Funktion: Erzeugt einen zufälligen Move in eine der
        vier Hauptachsen.

        Es wird zufällig eine der Bewegungen nach oben, unten, links oder rechts
        gewählt. Der Move ist jeweils genau ein Schritt in die entsprechende
        Richtung.

        Returns:
            tuple[int, int]: Einer der Moves (1, 0), (-1, 0), (0, 1) oder (0, -1).
        """

        d_x, d_y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        return d_x, d_y

    def _move_energy(self, move: tuple[int, int]) -> float:
        """
        Zusammenfassung der Funktion: Berechnet die "Energie" eines Moves als
        euklidische Distanz.

        Die Energie des Moves entspricht der euklidischen Distanz zwischen
        Start- und Zielpunkt und wird über die Hypotenusenfunktion berechnet.

        Args:
            move (tuple[int, int]): Relativer Move (dx, dy).

        Returns:
            float: Euklidische Distanz des Moves.
        """

        dx, dy = move
        return math.hypot(dx, dy)

    def _is_move_within_energy_limit(self, move: tuple[int, int]) -> bool:
        """
        Zusammenfassung der Funktion: Prüft, ob ein Move innerhalb des
        erlaubten Energie-Limits liegt.

        Das Energie-Limit wird durch den Wert _priority_energy festgelegt.
        Nur Moves, deren Distanz kleiner oder gleich diesem Wert ist,
        gelten als zulässig.

        Args:
            move (tuple[int, int]): Relativer Move (dx, dy), der geprüft wird.

        Returns:
            bool: True, wenn die Move-Energie im erlaubten Bereich liegt,
            sonst False.
        """

        return self._move_energy(move) <= self._priority_energy

    def _clamp_move(
        self, dx: int, dy: int, max_step: int = 2
    ) -> tuple[int, int]:
        """
        Begrenzung eines Moves auf den erlaubten Bereich [-2, +2].

        Moves, die zu groß sind, werden auf gültige Werte gestutzt,
        bleiben aber in dieselbe Richtung orientiert.

        Args:
            dx (int): Delta-X des Moves.
            dy (int): Delta-Y des Moves.

        Returns:
            tuple[int, int]: Gekürzter, gültiger Move.
        """
        max_step = max(1, int(max_step))
        dx = max(-max_step, min(max_step, dx))
        dy = max(-max_step, min(max_step, dy))
        return dx, dy

    def _simulate_future_environment(self, first_move: tuple[int, int]):
        """
        Zusammenfassung der Funktion: Simuliert das zukünftige 7x7-Sichtfeld
        nach Ausführung eines ersten Moves.

        Das aktuelle Environment wird so verschoben, als hätte sich das Beast
        bereits um (dx, dy) bewegt. Bereiche außerhalb des ursprünglichen
        Sichtfeldes werden mit '.' aufgefüllt. Anschließend wird das Beast
        wieder in die Mitte des Arrays gesetzt.

        Args:
            first_move (tuple[int, int]): Simulierter erster Move (dx, dy).

        Returns:
            numpy.ndarray: Simuliertes zukünftiges 7x7-Sichtfeld.
        """

        dx, dy = first_move

        # ursprüngliches 7x7-Feld holen
        field = self.parse_environment(self._environment).copy()

        # 'B' im alten Feld entfernen, wir interessieren uns nur für Futter / Gegner
        field[field == "B"] = "."

        size = field.shape[0]  # 7
        new_field = np.full((size, size), ".", dtype=str)

        # Sichtfeld so verschieben, als ob das Beast um (dx, dy) gegangen wäre
        for new_y in range(size):
            for new_x in range(size):
                src_x = new_x + dx
                src_y = new_y + dy
                if 0 <= src_x < size and 0 <= src_y < size:
                    new_field[new_y][new_x] = field[src_y][src_x]

        # Beast sitzt in der Zukunft wieder in der Mitte
        center = size // 2
        new_field[center][center] = "B"
        return new_field

    def _food_moves_in_field(self, field) -> list[tuple[int, int]]:
        """
        Zusammenfassung der Funktion: Simuliert das zukünftige 7x7-Sichtfeld
        nach Ausführung eines ersten Moves.

        Das aktuelle Environment wird so verschoben, als hätte sich das Beast
        bereits um (dx, dy) bewegt. Bereiche außerhalb des ursprünglichen
        Sichtfeldes werden mit '.' aufgefüllt. Anschließend wird das Beast
        wieder in die Mitte des Arrays gesetzt.

        Args:
            first_move (tuple[int, int]): Simulierter erster Move (dx, dy).

        Returns:
            numpy.ndarray: Simuliertes zukünftiges 7x7-Sichtfeld.
        """

        size = field.shape[0]
        center = size // 2
        moves: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()

        max_step = 1 if self._priority_energy < 2.0 else 2

        for y in range(size):
            for x in range(size):
                if field[y][x] == "*":
                    diff_x = x - center
                    diff_y = y - center
                    dx, dy = self._clamp_move(diff_x, diff_y, max_step)
                    move = (dx, dy)
                    if move not in seen:
                        seen.add(move)
                        moves.append(move)
        return moves

    def _score_two_step_food(
        self,
        m1: tuple[int, int],
        future_moves: list[tuple[int, int]],
        is_direct_hit: bool,
    ) -> float:
        """
        Zusammenfassung der Funktion: Bewertet einen Start-Move anhand eines
        Zwei-Schritt-Lookaheads auf Futter.

        Der erste Move m1 wird mit möglichen Folge-Moves kombiniert, um zu
        bestimmen, wie viel Futter erreichbar ist und wie groß die benötigte
        Distanz ist. Direkte Treffer können einen zusätzlichen Basis-Bonus
        erhalten.

        Args:
            m1 (tuple[int, int]): Erster Move (dx, dy), der bewertet wird.
            future_moves (list[tuple[int, int]]): Liste möglicher Folge-Moves
                im simulierten Environment.
            is_direct_hit (bool): True, wenn m1 direkt auf ein Futterfeld zeigt.

        Returns:
            float: Score-Wert für den Move, höher ist besser.
        """

        BONUS_PER_FOOD = 10.0

        dist1 = math.hypot(*m1)

        if future_moves:
            # bester zweiter Schritt (kürzeste Distanz)
            dist2 = min(math.hypot(dx, dy) for dx, dy in future_moves)
            extra_foods = len(future_moves)
        else:
            dist2 = 0.0
            extra_foods = 0

        # Nur Basis-Food-Bonus (10.0) addieren, wenn der Move direkt auf das Food führt (is_direct_hit = True)
        base_food_bonus = 1 if is_direct_hit else 0

        total_foods = base_food_bonus + extra_foods
        score = total_foods * BONUS_PER_FOOD - (dist1 + dist2)
        return score

    def _score_food_moves_with_lookahead(
        self,
        moves: list[tuple[int, int]],
        is_direct_hit_path: bool,
    ) -> list[tuple[int, int]]:
        """
        Zusammenfassung der Funktion: Bewertet mehrere Food-Moves mithilfe
        eines Zwei-Schritt-Lookaheads.

        Für jeden Move m1 wird optional ein zukünftiges Environment simuliert
        und mögliche Folge-Moves bestimmt. Aus diesen Informationen wird ein
        Score berechnet, der Futtermenge und Distanz kombiniert. Die Moves
        werden anschließend nach Score absteigend sortiert zurückgegeben.

        Args:
            moves (list[tuple[int, int]]): Kandidaten-Moves (dx, dy) in Richtung Futter.
            is_direct_hit_path (bool): True, wenn mindestens ein direkter Treffer
                im Pfad möglich ist und entsprechend höher belohnt werden soll.

        Returns:
            list[tuple[int, int]]: Moves sortiert nach absteigendem Score.
        """

        scores: dict[tuple[int, int], float] = {}
        MAX_LOOKAHEAD = 6

        for idx, m1 in enumerate(moves):
            dist1 = math.hypot(*m1)

            # Basis-Score, wenn wir keinen Lookahead machen.
            # Der Basis-Score ist hier nicht entscheidend, da er nur für idx >= 6 benutzt wird.
            base_score = (10.0 if is_direct_hit_path else 0.0) - dist1

            if idx < MAX_LOOKAHEAD:
                # Zukunftsfeld simulieren & erneut Futter-Suche
                future_field = self._simulate_future_environment(m1)
                future_moves = self._food_moves_in_field(future_field)
                # Übergabe des Flags an die Scoring-Funktion
                score = self._score_two_step_food(
                    m1, future_moves, is_direct_hit_path
                )
            else:
                # nur Ein-Schritt-Bewertung (fällt selten an)
                score = base_score

            scores[m1] = score

        # Moves nach Score absteigend sortieren
        sorted_moves = sorted(moves, key=lambda mv: scores[mv], reverse=True)

        return sorted_moves

    def chase_food(self) -> list[tuple[int, int]]:
        """
        Zusammenfassung der Funktion: Sucht Futter mit Hilfe eines
        Zwei-Schritt-Lookaheads und liefert priorisierte Moves zurück.

        Zunächst werden alle relativen Futterpositionen bestimmt. Je nach
        eingestellter Energie-Priorität wird entweder im normalen Modus
        (1er- und 2er-Moves) oder im 1er-Move-Modus gearbeitet. Dabei werden
        erreichbare Futterziele bevorzugt, clamped Moves gebildet und die
        bestbewerteten Moves nach Score zurückgegeben. Falls kein Futter
        gefunden wird, wird ein zufälliger Move gewählt.

        Returns:
            list[tuple[int, int]]: Liste sortierter Moves (dx, dy) in Richtung Futter.
        """

        # 0. Rohdaten (relative Positionen)
        raw = self.locate_food_list()

        # 0a. Kein Food im Sichtfeld -> Random-Fallback
        if not raw:
            rx, ry = self.random_move()
            moves = [(rx, ry)]
            self.set_food_list(moves)
            return moves

        # 0b. 1er-Move-Modus? -> 1er-Move-Funktion benutzen
        if self._priority_energy < 2.0:
            return self._chase_food_one_step(raw)

        # 1. Nur Moves betrachten, die im erlaubten 5x5 liegen (|dx|,|dy| <= 2)
        in_range = [
            (dx, dy) for (dx, dy) in raw if -2 <= dx <= 2 and -2 <= dy <= 2
        ]

        if in_range:
            # Prüft direkter Hit möglich (is_direct_hit_path = True)
            # nach Distanz (und leichtem Tie-Break) sortieren und duplizierte Moves entfernen
            uniq: list[tuple[int, int]] = []
            seen: set[tuple[int, int]] = set()
            for mv in sorted(
                in_range, key=lambda m: (math.hypot(*m), abs(m[0]) + abs(m[1]))
            ):
                if mv not in seen:
                    seen.add(mv)
                    uniq.append(mv)

            # Aufruf mit is_direct_hit_path = True
            best = (
                self._score_food_moves_with_lookahead(uniq, True)
                if len(uniq) <= 7
                else uniq
            )

            # Prüft ob die Moves im Energybereich ist
            best = [mv for mv in best if self._is_move_within_energy_limit(mv)]

            # Mach Random Move
            if not best:
                rx, ry = self.random_move()
                moves = [(rx, ry)]
                self.set_food_list(moves)
                return moves

            self.set_food_list(best)
            return best

        # 2. Kein erreichbares Food -> clamped Richtungen bilden
        clamped: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()
        for dx, dy in raw:
            mv = self._clamp_move(dx, dy)
            if mv not in seen:
                seen.add(mv)
                clamped.append(mv)

        clamped.sort(key=lambda m: (math.hypot(*m), abs(m[0]) + abs(m[1])))

        # CLAMPED PFAD: Direkter Hit nicht möglich (is_direct_hit_path = False)
        # Aufruf mit is_direct_hit_path = False
        best = (
            self._score_food_moves_with_lookahead(clamped, False)
            if len(clamped) <= 7
            else clamped
        )

        best = [mv for mv in best if self._is_move_within_energy_limit(mv)]

        if not best:
            rx, ry = self.random_move()
            moves = [(rx, ry)]
            self.set_food_list(moves)
            return moves

        self.set_food_list(best)
        return best

    def locate_food_list(self) -> list:
        """
        Zusammenfassung der Funktion: Ermittelt alle Futterpositionen relativ
        zum Beast im aktuellen Sichtfeld.

        Das Environment wird als 7x7-Feld interpretiert. Für jede Zelle mit '*'
        wird die relative Position zur Feldmitte (Position des Beasts) berechnet
        und als (dx, dy) in einer Liste gesammelt.

        Returns:
            list[tuple[int, int]]: Liste relativer Futterpositionen (dx, dy).
        """

        field = self.parse_environment(self._environment)
        food_list = []

        cx, cy = 3, 3  # Beast in der Mitte

        for y in range(7):
            for x in range(7):
                if field[y][x] == "*":
                    dx = x - cx
                    dy = y - cy
                    food_list.append((dx, dy))

        return food_list

    def _chase_food_one_step(
        self, raw: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """
        Zusammenfassung der Funktion: Sucht Futter im 1er-Move-Modus und
        priorisiert sichere, energiearme Schritte.

        Das Futter wird in drei Ringe (Nachbarn, 5x5, äußerer 7x7-Ring)
        unterteilt. Zunächst werden direkte Nachbarn bevorzugt, danach
        clamped Moves in Richtung Futter im 5x5- und 7x7-Bereich. Die
        gefundenen Moves können anschließend mit einem Lookahead bewertet
        und nach Energie gefiltert werden.

        Args:
            raw (list[tuple[int, int]]): Liste relativer Futterpositionen
                (dx, dy) aus dem Sichtfeld.

        Returns:
            list[tuple[int, int]]: Sortierte Liste von 1er-Moves in Richtung Futter.
        """

        # Ring-Einteilung anhand der Chebyshev-Distanz
        neighbours: list[tuple[int, int]] = []
        ring5: list[tuple[int, int]] = []
        ring7: list[tuple[int, int]] = []

        for dx, dy in raw:
            cheby = max(abs(dx), abs(dy))
            if cheby == 1:
                neighbours.append((dx, dy))
            elif cheby <= 2:
                ring5.append((dx, dy))
            else:
                ring7.append((dx, dy))

        def unique_sorted(
            moves: list[tuple[int, int]],
        ) -> list[tuple[int, int]]:
            """Entfernt Duplikate und sortiert nach Distanz + kleinem Tie-Break."""
            uniq: list[tuple[int, int]] = []
            seen: set[tuple[int, int]] = set()
            for mv in sorted(
                moves, key=lambda m: (math.hypot(*m), abs(m[0]) + abs(m[1]))
            ):
                if mv not in seen:
                    seen.add(mv)
                    uniq.append(mv)
            return uniq

        candidate_moves: list[tuple[int, int]] = []
        is_direct_hit_path = False

        if neighbours:
            # 1. Direkte Nachbarn: tatsächlich erreichbares Futter
            candidate_moves = unique_sorted(neighbours)
            is_direct_hit_path = (
                True  # direkter Hit -> extra Food-Bonus im Scoring
            )
        elif ring5:
            # 2. Food im 5x5, aber nicht direkt an uns dran -> clampen auf 1er-Moves
            clamped: list[tuple[int, int]] = []
            seen: set[tuple[int, int]] = set()
            for dx, dy in ring5:
                mv = self._clamp_move(dx, dy, max_step=1)  # Annäherung
                if mv != (0, 0) and mv not in seen:
                    seen.add(mv)
                    clamped.append(mv)
            candidate_moves = unique_sorted(clamped)
            # is_direct_hit_path bleibt False -> keine Base-Food-Belohnung
        elif ring7:
            # 3. Food im äußeren Ring des 7x7 -> ebenfalls clampen
            clamped = []
            seen = set()
            for dx, dy in ring7:
                mv = self._clamp_move(dx, dy, max_step=1)
                if mv != (0, 0) and mv not in seen:
                    seen.add(mv)
                    clamped.append(mv)
            candidate_moves = unique_sorted(clamped)

        # Kein sinnvoller Kandidat -> wie bei "kein Food": Random-Fallback
        if not candidate_moves:
            rx, ry = self.random_move()
            moves = [(rx, ry)]
            self.set_food_list(moves)
            return moves

        # Lookahead + Scoring wie bisher, nur mit ggf. anderem is_direct_hit_path
        best = (
            self._score_food_moves_with_lookahead(
                candidate_moves, is_direct_hit_path
            )
            if len(candidate_moves) <= 7
            else candidate_moves
        )

        # Sicherheitshalber trotzdem Energie-Filter
        best = [mv for mv in best if self._is_move_within_energy_limit(mv)]

        if not best:
            rx, ry = self.random_move()
            moves = [(rx, ry)]
            self.set_food_list(moves)
            return moves

        self.set_food_list(best)
        return best

    ########################
    #   Hunt & Kill Algo   #
    ########################

    def hunt(self) -> list:
        """
        Zusammenfassung der Funktion: Sucht Futter im 1er-Move-Modus und
        priorisiert sichere, energiearme Schritte.

        Das Futter wird in drei Ringe (Nachbarn, 5x5, äußerer 7x7-Ring)
        unterteilt. Zunächst werden direkte Nachbarn bevorzugt, danach
        clamped Moves in Richtung Futter im 5x5- und 7x7-Bereich. Die
        gefundenen Moves können anschließend mit einem Lookahead bewertet
        und nach Energie gefiltert werden.

        Args:
            raw (list[tuple[int, int]]): Liste relativer Futterpositionen
                (dx, dy) aus dem Sichtfeld.

        Returns:
            list[tuple[int, int]]: Sortierte Liste von 1er-Moves in Richtung Futter.
        """

        unsorted_hunting_list = self.locate_hunting_list()

        x_beast, y_beast = 3, 3
        enemy_data = []

        max_step = 1 if self._priority_energy < 2.0 else 2

        # Berechnet die Jagd auf Gegner  und sortiert sie ggf. wird geclamped
        for x_e, y_e in unsorted_hunting_list:
            diff_x = x_e - x_beast
            diff_y = y_e - y_beast

            c_diff_x, c_diff_y = self._clamp_move(diff_x, diff_y, max_step)
            total_distance = math.hypot(diff_x, diff_y)
            move_key = (c_diff_x, c_diff_y)

            enemy_data.append((total_distance, move_key))

        enemy_data.sort(key=lambda item: item[0])

        sorted_hunt_list = []
        seen_moves = set()
        for total_dist, move in enemy_data:
            if move not in seen_moves:
                seen_moves.add(move)
                sorted_hunt_list.append(move)

        if not sorted_hunt_list:
            self.set_hunt_list([])
            return []

        # Prüft ob der nächste move auf ein anderes unsere Biester steppt
        # wenn die liste true zurückliefert wird es in die liste gefügt
        safe_hunt_list = [
            move
            for move in sorted_hunt_list
            if self._is_safe_move(move)
            and self._is_move_within_energy_limit(move)
        ]

        self.set_hunt_list(safe_hunt_list)
        return safe_hunt_list

    def locate_hunting_list(self) -> list:
        """
        Zusammenfassung der Funktion: Sucht Gegner ('<') im aktuellen
        7x7-Sichtfeld und gibt deren absolute Feldkoordinaten zurück.

        Das Environment wird geparst und Zeile für Zeile durchsucht. Jede
        Zelle mit einem Gegner-Symbol '<' wird als Koordinate (x, y) im
        7x7-Feld gespeichert.

        Returns:
            list[tuple[int, int]]: Liste absoluter Gegnerkoordinaten (x, y)
            im 7x7-Feld.
        """

        field = self.parse_environment(self._environment)
        hunting_list = list()
        opponent_symbols = {"<"}

        for r_idx, row in enumerate(field):
            for c_idx, col in enumerate(row):
                if col in opponent_symbols:
                    coordinate = (c_idx, r_idx)
                    hunting_list.append(coordinate)
        return hunting_list

    def locate_unique_enemy_moves(self) -> list:
        """
        Zusammenfassung der Funktion: Bestimmt alle einzigartigen Moves in
        die Umgebung von stärkeren Gegnern.

        Es werden alle Gegner mit den Symbolen '>' und '=' im 7x7-Feld
        gesucht. Für jede gefundene Position wird über locate_enemy_list()
        das jeweilige 5x5-Umfeld berechnet. Anschließend werden alle
        Koordinaten zu einer Menge zusammengeführt und als Liste von
        eindeutigen Koordinaten zurückgegeben.

        Returns:
            list[tuple[int, int]]: Liste einzigartiger Koordinaten (dx, dy),
            die zum 5x5-Umfeld aller stärkeren Gegner gehören.
        """

        field = self.parse_environment(self._environment)
        enemy_list = []

        opponent_symbols = {">", "="}
        for r_idx, row in enumerate(field):
            for c_idx, col in enumerate(row):
                if col in opponent_symbols:
                    coordinate = (c_idx, r_idx)
                    enemy_list.append(self.locate_enemy_list(coordinate))

        unique_set = set()
        for enemy in enemy_list:
            unique_set.update(enemy)
        return list(unique_set)

    def get_enemy_positions(self) -> list:
        """
        Zusammenfassung der Funktion: Ermittelt die relativen Positionen
        echter Gegner im Sichtfeld.

        Es werden alle Zellen mit den Symbolen '>' oder '=' gesucht, in
        relative Koordinaten zur Beast-Position umgerechnet und anschließend
        mittels wrap_abs_coords in absolute Spielfeldkoordinaten übersetzt.
        Felder, auf denen eigene Beasts stehen, werden ausgeschlossen, so
        dass nur echte Gegner zurückgegeben werden.

        Returns:
            list[tuple[int, int]]: Liste relativer Gegnerpositionen (dx, dy),
            bezogen auf die aktuelle Beast-Position.
        """

        field = self.parse_environment(self._environment)

        enemy_list = []
        opponent_symbols = {">", "="}

        for r_idx, row in enumerate(field):
            for c_idx, col in enumerate(row):
                if col in opponent_symbols:
                    relative_x = c_idx - 3
                    relative_y = r_idx - 3

                    abs_x, abs_y = wrap_abs_coords(
                        self._abs_x + relative_x, self._abs_y + relative_y
                    )

                    # prüft das die neue Abs coordiante nicht keins unserer bieaster ist.
                    is_ally = False
                    for beast in utils.GLOBAL_BEAST_LIST:
                        # eigenes Beast überspringen ist nur zur Sicherheit
                        if beast.get_id() == self._id:
                            continue

                        if (
                            beast.get_abs_x() == abs_x
                            and beast.get_abs_y() == abs_y
                        ):
                            is_ally = True
                            break

                    # nur echte Gegner hinzufügen
                    if not is_ally:
                        enemy_list.append((relative_x, relative_y))

        return enemy_list

    def score_safe_moves(
        self, safe_moves: list, enemy_list: list
    ) -> tuple[list, dict]:
        """
        Zusammenfassung der Funktion: Bewertet sichere Moves danach, wie weit
        sie das Beast von Gegnern weg bewegen.

        Für jeden sicheren Move wird die Distanz zu allen Gegnerpositionen
        berechnet und aufsummiert. Moves, die im Durchschnitt weiter von
        Gegnern entfernt liegen, erhalten höhere Scores und werden in
        absteigender Reihenfolge zurückgegeben.

        Args:
            safe_moves (list[tuple[int, int]]): Liste sicherer Moves (dx, dy).
            enemy_list (list[tuple[int, int]]): Liste relativer Gegnerpositionen
                (dx, dy).

        Returns:
            tuple[list[tuple[int, int]], dict[tuple[int, int], float]]:
                - Liste der Moves sortiert nach absteigendem Score.
                - Dictionary mit Move als Key und Score als Value.
        """

        score_by_move = {}

        for mx, my in safe_moves:
            score = 0.0
            for ex, ey in enemy_list:
                dx = mx - ex
                dy = my - ey
                score += math.hypot(dx, dy)
            score_by_move[(mx, my)] = score

        sorted_scores = OrderedDict(
            sorted(
                score_by_move.items(), key=lambda item: item[1], reverse=True
            )
        )
        sorted_moves = list(sorted_scores.keys())
        return sorted_moves, sorted_scores

    def compute_kill_list(self) -> list:
        """
        Zusammenfassung der Funktion: Berechnet alle möglichen Kill-Moves
        auf kleinere Gegner im 5x5-Bereich.

        Das 7x7-Sichtfeld wird durchsucht und alle Gegnerpositionen ('<')
        werden auf die Beast-Position bezogen. Es werden nur Gegner in einem
        5x5-Bereich (Koordinaten -2 bis +2 relativ) berücksichtigt. Die
        resultierenden Moves werden nach Distanz sortiert und anschließend
        über _is_safe_move gefiltert, sodass nur sichere Kill-Moves übrig
        bleiben.

        Returns:
            list[tuple[int, int]]: Liste sicherer Kill-Moves (dx, dy) im 5x5-Bereich.
        """

        enemy_list = self.locate_hunting_list()
        kill_moves = []
        for x_e, y_e in enemy_list:
            # Beast sitzt in der Mitte (Index 3,3)
            dx = x_e - 3
            dy = y_e - 3

            # Nur Gegner im 5x5 Bereich zulassen
            if -2 <= dx <= 2 and -2 <= dy <= 2:
                kill_moves.append((dx, dy))

        # Sortieren nach Distanz (nächste Ziele zuerst)
        kill_moves.sort(key=lambda move: math.hypot(move[0], move[1]))

        # Prüft ob der nächste move auf ein anderes unsere Biester steppt
        # wenn die liste true zurückliefert wird es in die liste gefügt
        safe_kill_moves = [
            move for move in kill_moves if self._is_safe_move(move)
        ]

        self.set_kill_list(safe_kill_moves)
        return safe_kill_moves

    ################
    #  Split-Algo  #
    ################

    def split(self):
        """
        Zusammenfassung der Funktion: Entscheidet, ob sich das Beast in zwei
        Beasts aufteilt, und liefert ggf. den Start-Move für das neue Beast.

        Zunächst wird eine durchschnittliche Energie pro Runde berechnet.
        Ein regulärer Split ist nur erlaubt, wenn genügend Energie vorhanden
        ist, keine Jagd- oder Fluchtsituation besteht und ausreichend Futter
        in Reichweite ist. Zusätzlich existiert ein Notfall-Split, der
        greift, wenn nur noch ein Beast lebt, bestimmte Mindestenergie und
        -rundenzahlen erreicht sind, keine Gegner im 5x5-Bereich sichtbar
        sind und mindestens ein Futterfeld vorhanden ist. Im Erfolgsfall
        wird ein Move in eine der vier Hauptachsen geliefert, auf dem das
        neue Beast spawnen soll.

        Returns:
            tuple[tuple[int, int] | None, bool]:
                - Move (dx, dy) für das neue Beast, oder None, wenn kein Split
                  durchgeführt wird.
                - True, wenn ein Split stattfinden soll, sonst False.
        """

        # GENERAL_ENERGY_AVG wurde nach näherer Analysen der Futter-Runde
        # Verhältnis aus der beast logs vom 14.11.25 ermittelt und gezeigt
        # dass sich dieser Wert oder größer etwa eine Wahrscheinlichkeit von
        # 20% hat um vorzukommen.
        GENERAL_ENERGY_AVG: float = 2.5
        MINIMUM_SPLIT_ENERGY: float = 80.0

        # Drehschrauben für den Notfall-Split
        EMERGENCY_MIN_ENERGY: float = 50.0
        EMERGENCY_MIN_ROUND: float = 100

        # Schutz Div durch 0
        if self._round_abs <= 0:
            cur_energy_avg = 0.0
        else:
            cur_energy_avg: float = self._energy / self._round_abs

        food_list: list = self._food_list
        hunt_list: list = self._hunt_list
        escape_list: list = self._escape_list

        ######### Normaler Split #########
        # Wir müssen hier die Anforderungen für den Split erfüllen
        if (
            self._energy > MINIMUM_SPLIT_ENERGY
            and cur_energy_avg >= GENERAL_ENERGY_AVG
            and len(hunt_list) == 0
            and len(escape_list) == 0
            and len(food_list) >= 4
        ):
            legal_moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]

            move = None

            # 1. Suche: Ist einer der legalen Moves ein Food-Feld?
            for option in legal_moves:
                if option in food_list:
                    move = option
                    break  # Den ersten Treffer nehmen und Schleife beenden

            # 2. Fallback: Wenn kein Food da ist, nimm einen zufälligen legalen Move
            if move is None:
                move = random.choice(legal_moves)

            # Bedingungen == True -> Split erlaubt (True)
            # -> Bester Food-MOVE -> neuer beast spawnt auf dem Food.
            return move, True

        ######### Notfall-Split #########
        # lebt nur noch 1 eigenes Beast?
        only_one_beast_left = len(utils.GLOBAL_BEAST_LIST) == 1

        # Mindestenergie + Mindest-Runde erreicht?
        has_min_energy_and_round = (
            self._energy >= EMERGENCY_MIN_ENERGY
            and self._round_abs >= EMERGENCY_MIN_ROUND
        )

        # Sichtfeld analysieren (direkt der String, weil z.B. Foodliste auch bei keinem Food im Sichtfeld NICHT leer ist, wegen random-Move)
        env_str = self._environment or ""

        # mindestens ein Futter im Sichtfeld?
        has_food_in_view = "*" in env_str

        # irgendein anderes Biest im 5x5-Bereich (Chebyshev <=2)?
        enemy_symbols = (">", "=", "<")
        field = self.parse_environment(env_str)

        size = field.shape[0]  # sollte 7 sein
        center = size // 2  # 3 -> unser Beast sitzt in der Mitte
        has_enemy_in_view = False

        for y in range(size):
            for x in range(size):
                if field[y][x] in enemy_symbols:
                    dx = x - center
                    dy = y - center
                    # Chebyshev-Distanz
                    if max(abs(dx), abs(dy)) <= 2:  # <=2 für 5x5-Bereich
                        has_enemy_in_view = True

        if (
            only_one_beast_left
            and has_min_energy_and_round
            and has_food_in_view
            and not has_enemy_in_view
        ):
            legal_moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            move = None

            # 1. Suche: Wie beim normalen Split zuerst versuchen, direkt auf Food zu splitten
            for option in legal_moves:
                if option in food_list:
                    move = option
                    break  # Den ersten Treffer nehmen und Schleife beenden

            if move is None:
                # Fallback: zufälliger legaler Move, möglichst "sicher"
                move = random.choice(legal_moves)

            # Bedingungen == True -> Split erlaubt (True)
            # -> Bester Food-MOVE -> neuer beast spawnt auf dem Food.
            return move, True

        ######### Kein Split #########
        # Bedingungen != True -> Kein MOVE (None) und Kein Split erlaubt (False)
        return None, False

    def locate_enemy_list(self, enemy: tuple) -> list:
        """
        Zusammenfassung der Funktion: Liefert das 5x5-Umfeld um eine gegnerische
        Position als relative Koordinaten.

        Ausgehend von einer gegnerischen Position im 7x7-Feld werden alle
        Koordinaten mit Abstand bis 2 in x- und y-Richtung gesammelt, solange
        sie innerhalb des Bereiches [-2, 2] bleiben. Das Ergebnis ist die
        Menge aller relativen Koordinaten im 5x5-Umfeld des Gegners.

        Args:
            enemy (tuple[int, int]): Gegnerkoordinate (x, y) im 7x7-Feld.

        Returns:
            list[tuple[int, int]]: Liste relativer Koordinaten im 5x5-Umfeld.
        """

        my_list = list()
        for r_idx in range(-2, 2 + 1):  # r_idx ist y
            for c_idx in range(-2, 2 + 1):  # c_idx ist x
                coordinate = (c_idx + enemy[0], r_idx + enemy[1])
                if (
                    coordinate[0] <= 2
                    and coordinate[0] >= -2
                    and coordinate[1] <= 2
                    and coordinate[1] >= -2
                ):
                    my_list.append(coordinate)
        return my_list

    #################
    #  Escape-Algo  #
    #################

    def escape(self) -> list:
        """
        Zusammenfassung der Funktion: Berechnet sichere Escape-Moves im 5x5-
        Bereich, um Abstand zu Gegnern zu gewinnen.

        Die Funktion ermittelt zunächst alle Gegnerpositionen. Dann werden
        alle möglichen Moves im Bereich [-2..2] × [-2..2] betrachtet, das
        eigene Feld (0, 0) ausgeschlossen. Felder, die im 5x5-Umfeld eines
        Gegners liegen, gelten als gefährlich. Sichere Moves sind alle
        übrigen, die zusätzlich über _is_safe_move geprüft werden. Diese
        sicheren Moves werden in 1er-Moves und längere Moves aufgeteilt
        und jeweils nach Distanz zu den Gegnern mit score_safe_moves sortiert.

        Returns:
            list[tuple[int, int]]: Liste sicherer Escape-Moves (dx, dy),
            sortiert nach ihrer Eignung.
        """

        # 1. Alle Gegnerpositionen (relativ zu uns) holen
        enemy_list = self.get_enemy_positions()

        # Sofortregel: wenn kein Enemy vorhanden -> leere Liste zurückgeben
        if not enemy_list:
            self.set_escape_list([])
            return []

        # 2. Alle möglichen Moves im 5x5 (ohne (0,0))
        our_moves = [
            (x, y)
            for x in range(-2, 3)
            for y in range(-2, 3)
            if not (x == 0 and y == 0)
        ]

        # 3. Gefährliche Felder bestimmen (5x5 um jeden Gegner, geschnitten mit unserem 5x5)
        danger_moves_set = set()
        our_area_set = set((x, y) for x in range(-2, 3) for y in range(-2, 3))

        for ex, ey in enemy_list:
            for gx in range(ex - 2, ex + 3):
                for gy in range(ey - 2, ey + 3):
                    if (gx, gy) in our_area_set:
                        danger_moves_set.add((gx, gy))

        danger_moves_set.discard((0, 0))

        # 4. Sichere Moves = our_moves - danger_moves, zusätzlich globale Kollisionsprüfung
        safe_moves = [
            move for move in our_moves if move not in danger_moves_set
        ]
        safe_moves = [move for move in safe_moves if self._is_safe_move(move)]

        # WENN GAR KEIN sicherer Move -> raus
        if not safe_moves:
            self.set_escape_list([])
            return []

        # 5. Safe Moves nach Schrittweite in zwei Gruppen aufteilen
        one_step_moves = []
        longer_moves = []

        for mx, my in safe_moves:
            cheby = max(abs(mx), abs(my))  # Chebyshev-Distanz
            if cheby == 1:
                one_step_moves.append((mx, my))
            else:
                longer_moves.append((mx, my))

        result_moves: list[tuple[int, int]] = []

        # 6. ZUERST: 1er-Moves sortieren (weiter weg vom Gegner = besser)
        if one_step_moves:
            sorted_one_step, _ = self.score_safe_moves(
                one_step_moves, enemy_list
            )
            result_moves.extend(sorted_one_step)

        # 7. DANN: längere Moves sortieren und hinten anhängen
        if longer_moves:
            sorted_longer, _ = self.score_safe_moves(longer_moves, enemy_list)
            result_moves.extend(sorted_longer)

        # leere liste wenn es nichts ist
        if not result_moves:
            self.set_escape_list([])
            return []

        self.set_escape_list(result_moves)
        return result_moves

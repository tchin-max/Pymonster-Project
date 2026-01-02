import os
from datetime import datetime
import json
import gzip
import shutil  # für "alte Datei in Ordner schieben"

game_round = 0

LOG_FOLDER = "logs"
ARCHIVE_FOLDER = os.path.join(LOG_FOLDER, "archive")
CHUNK_SIZE = 20000  # nach 20k Runden neue Datei

"""
Dieses Modul kümmert sich um das Logging für Server- und Beast-Ereignisse.

Es bietet Funktionen, um Servermeldungen sowie Zustände der Beasts in komprimierte
.ndjson.gz-Dateien zu schreiben. Beast-Logs werden in Chunks aufgeteilt und bei
Bedarf automatisch in ein Archiv verschoben, um die Log-Dateien übersichtlich und
handhabbar zu halten.
"""


def ensure_dir(path):
    """
    Zusammenfassung der Funktion: Stellt sicher, dass ein Verzeichnis existiert.

    Falls das angegebene Verzeichnis noch nicht existiert, wird es inklusive
    aller notwendigen Unterverzeichnisse erstellt. Existiert es bereits,
    passiert nichts.

    Args:
        path (str): Pfad zu dem Verzeichnis, das überprüft bzw. erstellt
            werden soll.

    Returns:
        None
    """

    if not os.path.isdir(path):
        os.makedirs(path)


def get_beast_log_file(bid, abs_r):
    """
    Zusammenfassung der Funktion: Bestimmt die Log-Datei (mit Chunking) für
    ein Beast in einer bestimmten absoluten Runde.

    Die Runden werden in Blöcke der Länge CHUNK_SIZE aufgeteilt. Für jede
    Kombination aus Beast-ID und Chunk-Index wird eine eigene komprimierte
    .ndjson.gz-Datei im LOG_FOLDER angelegt bzw. verwendet.

    Args:
        bid: Kennung des Beasts (z.B. int oder str), die im Dateinamen
            verwendet wird.
        abs_r (int): Absolute Rundenanzahl des Spiels, anhand derer der
            Chunk-Index berechnet wird.

    Returns:
        tuple[str, int]:
            - str: Vollständiger Dateipfad zur Log-Datei des aktuellen Chunks.
            - int: Berechneter Chunk-Index (0, 1, 2, ...).
    """

    ensure_dir(LOG_FOLDER)

    chunk_index = abs_r // CHUNK_SIZE  # 0,1,2,...
    filename = f"beast-{bid}_c{chunk_index:04d}.ndjson.gz"
    file_path = os.path.join(LOG_FOLDER, filename)
    return file_path, chunk_index


def archive_previous_chunk_if_exists(bid, chunk_index):
    """
    Zusammenfassung der Funktion: Verschiebt die vorherige Chunk-Datei eines
    Beasts (falls vorhanden) ins Archiv.

    Für den aktuellen Chunk-Index wird geprüft, ob es eine Datei für den
    vorherigen Index (chunk_index - 1) im LOG_FOLDER gibt. Wenn ja, wird sie
    in den ARCHIVE_FOLDER verschoben, sofern sie dort noch nicht existiert.

    Args:
        bid: Kennung des Beasts, um den Dateinamen der vorherigen Log-Datei
            zu bestimmen.
        chunk_index (int): Aktueller Chunk-Index. Nur wenn dieser größer
            als 0 ist, wird nach einem vorherigen Chunk gesucht.

    Returns:
        None
    """

    if chunk_index <= 0:
        return  # kein vorheriger Chunk

    prev_filename = f"beast-{bid}_c{chunk_index - 1:04d}.ndjson.gz"
    prev_path = os.path.join(LOG_FOLDER, prev_filename)

    if os.path.exists(prev_path):
        ensure_dir(ARCHIVE_FOLDER)
        target_path = os.path.join(ARCHIVE_FOLDER, prev_filename)
        # nur verschieben, wenn sie nicht schon im Archiv liegt
        if not os.path.exists(target_path):
            shutil.move(prev_path, target_path)


def log_server(servermsg: str, exceptions: str, searchstring="server"):
    """
    Zusammenfassung der Funktion: Schreibt einen Server-Logeintrag in eine
    komprimierte .ndjson.gz-Datei.

    Für Servermeldungen wird pro Tag eine Log-Datei im LOG_FOLDER geführt.
    Jeder Eintrag wird als JSON-Objekt in eine gzip-komprimierte NDJSON-Datei
    geschrieben. Zusätzlich wird die aktuelle Spielrunde (game_round) als
    Feld abgelegt.

    Args:
        servermsg (str): Inhalt bzw. Text der Servernachricht.
        exceptions (str): Zusatzinformationen oder Fehlermeldungen, die zur
            Servernachricht gehören (kann auch leer sein).
        searchstring (str): Prefix im Dateinamen der Log-Datei, standardmäßig
            "server". Kann angepasst werden, um unterschiedliche Log-Typen
            zu trennen.

    Returns:
        None
    """

    ensure_dir(LOG_FOLDER)

    # Eine Datei pro Tag
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{searchstring}_{timestamp}.ndjson.gz"
    file_path = os.path.join(LOG_FOLDER, filename)

    eintrag = {
        "r": game_round,
        "smsg": servermsg,
        "ex": exceptions,
    }

    line = (json.dumps(eintrag, ensure_ascii=False) + "\n").encode("utf-8")
    with gzip.open(file_path, "ab", compresslevel=1) as f:
        f.write(line)


def log_beast(**fields):
    """
    Zusammenfassung der Funktion: Schreibt einen Beast-Logeintrag mit
    automatischem Chunking und Archivierung.

    Die Funktion erwartet Log-Daten als Keyword-Argumente (z.B. bid, abs_r,
    Energie, Position usw.). Anhand der absoluten Runde (abs_r) wird die
    passende Log-Datei bestimmt und ein gzip-komprimierter NDJSON-Eintrag
    geschrieben. Wenn mit dem aktuellen Eintrag ein neuer Chunk beginnt,
    wird die vorherige Chunk-Datei (falls vorhanden) automatisch in den
    ARCHIVE_FOLDER verschoben.

    Erwartete Felder (optional, aber üblich):
        - bid: ID des Beasts.
        - abs_r: Absolute Rundenanzahl, in der der Eintrag erstellt wird.

    Args:
        **fields: Beliebige Log-Felder als Keyword-Argumente, die direkt
            als JSON-Objekt in die Log-Datei geschrieben werden.

    Returns:
        None
    """

    global game_round
    game_round = fields.get("abs_r", 0)
    bid = fields.get("bid", "unknown")
    abs_r = fields.get("abs_r", 0)

    # richtige Datei für diese Runde bestimmen
    file_path, chunk_index = get_beast_log_file(bid, abs_r)

    # vorherigen Chunk (falls vorhanden) ins Archiv verschieben
    archive_previous_chunk_if_exists(bid, chunk_index)

    # Eintrag schreiben
    line = (json.dumps(fields, ensure_ascii=False) + "\n").encode("utf-8")
    with gzip.open(file_path, "ab", compresslevel=1) as f:
        f.write(line)

#  PyMonster -- Strategie-Client (Prog3 Semesterprojekt)

**Programmierung 3 -- Wintersemester 25/26**

## 📌 Projektübersicht

Dieses Semesterprojekt implementiert einen Strategie-Client für das
rundenbasierte Spiel **PyMonster (Biester)**.

In jeder Spielrunde erhält ein Beast ein **7×7 großes Sichtfeld** als
Zeichenkette (49 Zeichen), das seine unmittelbare Umgebung beschreibt.\
Mögliche Symbole:

-   `B` -- eigenes Beast (immer im Zentrum)
-   `*` -- Nahrung
-   `.` -- freies Feld
-   `>` -- gegnerisches Beast
-   `<` -- schwaches Beast

Auf Basis dieses Sichtfeldes entscheidet der Client, welche Bewegungen
ausgeführt werden sollen.\
Die Bewegungen werden als relative Vektoren `(dx, dy)` zurückgegeben.

Der Client tritt gegen andere Teams auf einem zentralen Server an. Die
Performance bestimmt die Rangliste.

------------------------------------------------------------------------

## 🏗 Architektur

Der ursprüngliche Beispiel-Client wurde in eine modulare Architektur
überführt, um bessere Struktur, Wartbarkeit und Testbarkeit zu
gewährleisten.

### Zentrale Module

-   **client.py** -- Kommunikation mit dem Server
-   **controller.py** -- Verarbeitung der Serverdaten
-   **logic.py** -- Zentrale Entscheidungslogik
-   **beast.py** -- Zustands- und Strategielogik des Beasts
-   **logger.py** -- Logging für Analyse und GUI
-   **utils.py** -- Hilfsfunktionen und Konstanten

Diese Struktur sorgt für klare Trennung von Verantwortlichkeiten
(Separation of Concerns).

------------------------------------------------------------------------

## 🧠 Strategiekonzept

Die Entscheidungslogik basiert auf priorisierten Strategiemodulen:

-   Food (Nahrungssuche)
-   Hunt (Jagd)
-   Kill (Angriff)
-   Escape (Flucht)
-   Split (Aufteilen bei ausreichend Energie)

Die Hauptlogik bewertet situativ die Umgebung und wählt die passendste
Strategie aus.

------------------------------------------------------------------------

# 👨‍💻 Mein Beitrag

Mein Schwerpunkt im Projekt lag auf der **Implementierung der
Beast-Logik sowie der Entwicklung einer umfassenden Test-Suite**.

------------------------------------------------------------------------

## 1️⃣ Parsing des Sichtfeldes

### `parse_environment()`

-   Wandelt die 49-Zeichen-Zeichenkette in ein **7×7 Grid**
-   Stellt sicher, dass sich das Beast im Zentrum befindet
-   Nutzung von NumPy zur effizienten Verarbeitung

Diese Methode bildet die Grundlage für alle weiteren Strategien.

------------------------------------------------------------------------

## 2️⃣ Nahrungserkennung & Basisstrategie

### `locate_food_list()`

-   Identifiziert alle Nahrungspositionen (`*`)
-   Wandelt sie in relative Koordinaten `(dx, dy)` um

### Erste Version von `chase_food()`

Vorgehen:

1.  Umgebung parsen\
2.  Nahrung lokalisieren\
3.  Nächstgelegene Nahrung mittels **Manhattan-Distanz** bestimmen\
4.  Bewegung auf maximal einen Schritt begrenzen (`[-1, 0, 1]`)\
5.  Falls keine Nahrung vorhanden → zufällige Bewegung

Diese Version stellte eine funktionierende Basisstrategie dar.

------------------------------------------------------------------------

## 3️⃣ Erweiterung: Two-Step Lookahead

Zur Optimierung der Entscheidungsfindung wurde eine **Two-Step Lookahead
Strategie** implementiert.

Statt nur das nächstgelegene Ziel zu betrachten, werden mögliche
Bewegungen simuliert und bewertet:

-   Nutzung der **Chebyshev-Distanz**
-   Bewertung potenzieller Folgepositionen
-   Vermeidung riskanter Bewegungen

Diese Erweiterung erhöhte die strategische Tiefe deutlich.

------------------------------------------------------------------------

## 🧪 Test-Suite

Es wurde eine umfangreiche Test-Suite mit **pytest** entwickelt:

-   Testen der Parsing-Funktion
-   Validierung der Koordinatenberechnung
-   Tests für Bewegungsentscheidungen
-   Sicherstellung robuster Strategielogik

Dies verbesserte Stabilität und Wartbarkeit des Projekts erheblich.

------------------------------------------------------------------------

## ⚙️ Technologien

-   Python
-   NumPy
-   pytest
-   Client-Server-Kommunikation
-   Modulare Softwarearchitektur

------------------------------------------------------------------------

## 🎯 Lernziele

Dieses Projekt demonstriert:

-   Strategische Entscheidungsalgorithmen
-   Zustandsbasierte Logik
-   Modulare Architektur
-   Testgetriebene Entwicklung
-   Analyse und Optimierung von Spielstrategien
-   Arbeiten in einem wettbewerbsbasierten Client-Server-Umfeld

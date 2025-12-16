---
Projektname: SpotRec
Sprache(n): Python, Bash
Build: Keine zentralisierte Build-Tooling (Optionale standalone-Build via `build-standalone.sh` / Nuitka)
Startbefehl: `python3 spotrec.py --client ncspot -o ~/Music/SpotRec` (siehe README für Varianten)
Tests: FEHLT (empfohlen: `pytest` hinzufügen)
CI vorhanden: nein (keine `.github/workflows` gefunden)
---

# Copilot-Anweisungen — SpotRec (DE)

Kurze Erklärung
- SpotRec ist ein kleines, betriebssystemabhängiges Tool zum Aufzeichnen der Audio-Ausgabe von Spotify-Clients (`spotify` Desktop, `ncspot`) mithilfe von `ffmpeg`.
- Unterstützte OS: macOS (BlackHole) und Linux (PulseAudio/Pulse sink remapping).

Dateien, die ich für diese Anleitung geprüft habe (Autoritätsquellen):
- `README.md` — Setup & Usage
- `spotrec.py` — Hauptprogramm, CLI, Provider, FFmpeg-Management
- `ncspot_hook.py` — Hook-Skript für `ncspot`
- `configure-ncspot.sh` — macOS-Setup-Skript
- `build-standalone.sh` — Beispiel-Build-Skript (Nuitka)
- `requirements.txt` — Python-Pakete
- `img/` — Dokumentations-Assets

Wichtige Erkenntnisse (repo-spezifisch)
- Der Code ist monolithisch in `spotrec.py`. Provider (`DBusProvider`, `NcspotHookProvider`), `FFmpeg`, `PulseAudio`, und `Shell` Klassen sind darin enthalten.
- macOS-Workflow nutzt `ncspot` Hook (`ncspot_hook.py`) + `BlackHole` und optional einen `Multi-Output Device`-Workaround. `configure-ncspot.sh` automatisiert das Setup.
- Linux-Workflow nutzt PulseAudio sink remapping (`pactl`), sowie `pavucontrol` zu Debugzwecken.
- Es gibt keine Tests, keine CI, und keine Formate/Checks (z. B. `pre-commit` oder Linting).

Hauptprinzipien für Copilot
1) Repo zuerst lesen (Autorität: oben genannte Dateien). Allgemeine Vorschläge nur als genau gekennzeichnete Empfehlungen hinzufügen.
2) Keine Änderungen an globalen Konstanten ohne Begründung und tests (z. B. `_blackhole_device_name`, `_pa_recording_sink_name`).
3) Platform-spezifische Änderungen mit Tests/Checks versehen (macOS vs Linux unterscheiden).
4) Vermeidung von Problemen mit Shell Injection: `Shell.run`/`Shell.Popen` sollten sicherere Interfaces oder robustes Quoting verwenden.

Lokale Analyse-Prioritäten (in Reihenfolge)
1. `spotrec.py`: Prüfe CLI-Flags & Platform-Paths (`_is_macos`, FFmpeg args).
2. `PulseAudio` class: Prüfe sink load/unload & `pactl` command strings auf robustes quoting.
3. `FFmpeg.record`: Aufruf-Parameter, temporäres Dateinamen-Präfix, Zeitverhalten.
4. `NcspotHookProvider`: Format/Vorbedingungen des JSON-Temporärfiles überprüfen (`/tmp/spotrec_metadata.json`).
5. `configure-ncspot.sh`: macOS-Install/venv/vendoring-Skripte prüfen.

Aufbau & Ordnerstruktur (erkannt)
- Root: `README.md`, `spotrec.py`, `ncspot_hook.py`, `configure-ncspot.sh`, `build-standalone.sh`, `requirements.txt`, `img/`
- `.github/` — enthält `copilot-instructions.md` (diese Datei)
- `venv/` — lokale virtuelle Umgebung (lokal erzeugt, nicht im VCS empfohlen)

Sprachen & Tooling
- Python 3 (Code in `spotrec.py`, `ncspot_hook.py`)
- Bash (Setup- & Build-Skripte)
- Shell tools: `ffmpeg`, `pactl`, `dbus-send` (für D-Bus interaction on Linux), `SwitchAudioSource` or GUI audio setup on macOS

Entwicklungs-Konventionen
- Stil/Format: PEP8/Black nicht durchgesetzt. Vorschlag: `black` + `ruff` + `pylint` optional (als Empfehlung).
- Namespaces: Verwende Module/Packages anstelle eines monolithischen `spotrec.py` für bessere Testbarkeit (optional, aber empfohlen).
- Fehlerbehandlung: Logging wird verwendet; vermeide `os._exit()` ohne Kommentar; `sys.exit` bevorzugt.

Abhängigkeiten & Paketmanager
- Python-Pakete: `requests` (in `requirements.txt`).
- Systempakete: `ffmpeg`, `pulseaudio` (Linux), `BlackHole` (macOS), `ncspot` (client option), `dbus-python`/`pygobject`.

Build/Run/Test Befehle (repo-spezifisch)
- macOS setup (script):
```bash
chmod +x ./configure-ncspot.sh
./configure-ncspot.sh
```
- Virtualenv & run (macOS example):
```bash
source venv/bin/activate
python3 spotrec.py --client ncspot -o ~/Music/SpotRec
```
- Linux run:
```bash
pip3 install -r requirements.txt
python3 spotrec.py --client spotify -o ~/Music/SpotRec
```
- Build (optional, Nuitka fallback):
```bash
./build-standalone.sh
```
Tests: FEHLT — Vorschlag: `pytest` + mocks für shell, DBus, FFmpeg.

Debugging & Logs
- CLI: `--debug` aktiviert ausführliche logs.
- Multi-Output Device & `pavucontrol` empfohlen auf Linux.
- Für ffmpeg output: Look for `Lavf`/ffmpeg logs in pavucontrol and in stdout (if debug turned on).

Security & Secrets
- Keine Secrets oder `.env`-Dateien in diesem Repo. Praktische Empfehlung: Geheimnisse (falls hinzugefügt) müssen in CI als Secrets und nicht im VCS gespeichert werden; für Deploy: GitHub Secrets / Vault.

Deployment & Umgebungen
- Kein Deployment-Mechanismus im Repo vorhanden — Tool ist CLI/desktop based. Standalone packaging uses Nuitka (see `build-standalone.sh`).

Checklisten für typische Aufgaben
- Neuer CLI Flag (Feature):
  1) Änderungen in `handle_command_line` in `spotrec.py` hinzufügen
  2) Helfer testen (`--help` CLI; Start script with `--debug`)
  3) README aktualisieren
  4) Wenn notwendig, `app_version` erhöhen

- Bugfix: `ffmpeg` not finishing
  1) Test manually reproducing with `--debug`
  2) Add unit test if possible (mock FFmpeg process)
  3) Add logging around process termination and file rename

Beispiele für häufige Tasks (Kurzanleitung für Copilot)
1) Feature: Add `--dry-run` option
   - Prüfe `spotrec.py::handle_command_line`.
   - Implementiere `args.dry_run` toggling `FFmpeg.record` so it prints command instead of running.
   - Update `README.md`.
   - Tests: Add `pytest` that checks `FFmpeg.record` not started.

2) Bugfix: Avoid file-path traversal
   - Prüfe `BaseProvider.get_track()` (filename building).
   - Sanitize all filename parts (remove `..`, control chars) and validate with `Path.resolve().is_relative_to(output_dir)`.
   - Add unit tests for suspicious track strings (e.g., artist: `../etc/passwd`).

3) CI: Add basic GitHub Action
   - Create `.github/workflows/python.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with: python-version: '3.11'
      - name: Install deps
        run: pip3 install -r requirements.txt
      - name: Lint
        run: pip3 install ruff && ruff check .
      - name: Run tests
        run: pytest -q
```
Note: `pytest` is FEHLT and must be introduced.

Nützliche Befehle & Snippets
- Run with debug:
```bash
python3 spotrec.py --client ncspot -o ./out --debug
```
- Convert output to MP3 in 320kbps:
```bash
python3 spotrec.py --client ncspot -f mp3 -q 320
```

Praktische Empfehlungen (General / nicht bereits im Repo)
- Tests: Add `pytest` and `pytest-mock`; extract small parts from `spotrec.py` into functions to make them testable.
- CI: Add GitHub Actions as shown.
- Linting: Add `requirements-dev.txt` with `black`, `ruff`, and add a workflow step.

Kurz-Beispiel für Copilot-ToDos (Schritt-für-Schritt)
1) Öffne `spotrec.py` und suche `handle_command_line`.
2) Implementiere `--dry-run` in `handle_command_line`, speichere flag in global (or better pass config object).
3) Verändere `FFmpeg.record()` behavior: wenn dry-run, just log the ffmpeg command instead of launching `Popen`.
4) Ergänze `README.md` mit `--dry-run` usage example.
5) Erstelle unit test verifying `FFmpeg.record()` does not spawn a process in dry-run mode.

---

Kontakt / Notes
- Ich habe die Dateien oben gelesen und verwendet; falls du möchtest, kann ich jetzt ein PR mit einer kleineren Änderung (z. B. `--dry-run` Feature und ein erster Unit Test) erstellen.

Vielen Dank — Bei Bedarf erstelle ich CI / Test-Skeleton oder refactoriere `spotrec.py` in Module.

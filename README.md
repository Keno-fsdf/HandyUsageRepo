# handyUsage — Projektübersicht

Dieses Repository enthält Skripte und ein Android-Beispielprojekt zur Erstellung, Auswertung und Nutzung von Batterie/Vorhersagemodellen (TensorFlow/TFLite). Diese README beschreibt die komplette Ordnerstruktur, den Zweck wichtiger Dateien und Nutzungsbeispiele, so dass auch eine andere KI das Projekt verstehen und verarbeiten kann.

**Kurz:** Python-Skripte erzeugen Trainings- und Evaluierungsdaten, trainieren Modelle und konvertieren sie zu TFLite. Das `android/`-Projekt bindet das Modell in eine Android-App ein.

**Projektstruktur (vollständig)**

- `convert_tflite.py` — Skript zur Konvertierung/Kalibrierung von Keras/TensorFlow-Modellen nach TFLite.
- `generate_data.py` — Erzeugt synthetische oder verarbeitete Datensätze zur Modell-Trainingsvorbereitung.
- `run_pipeline.py` — Wrapper/Orchestrator, der Datenvorbereitung, Training und Evaluation in Reihenfolge ausführt.
- `train_model.py` — Trainingsskript für das Batterie-Vorhersagemodell (Keras/TensorFlow).
- `train_real_data.py` — Variante des Trainings, die reale Messdaten verwendet.

- `android/` — Android-App-Quellcode (Gradle/Kotlin)
  - `build.gradle.kts`, `gradle.properties`, `settings.gradle.kts`, `gradlew.bat`, `local.properties` — Build- und Konfigurationsdateien.
  - `app/` — Android-App-Modul
    - `build.gradle.kts` — Modul-Build-Skript
    - `build/` — automatisch erzeugte Build-Artefakte (nicht versionieren)
    - `src/` — Quellcode der App (Activitys, Layouts, Ressourcen)

- `data/` — Eingabedaten und vorbereitete Datensätze
  - `battery_data.csv` — (synthetische) oder Rohdaten
  - `real_battery_data.csv` — Messdaten aus realer Aufnahme
  - `X_sequences.npy`, `y_sequences.npy` — vorberechnete Sequenzen für Training/Evaluation

- `model/` — Trainierte Modelle und zugehörige Artefakte
  - `battery_model.keras` / `battery_model_real.keras` — Keras-Modelldateien
  - `battery_model.tflite` / `battery_model_real.tflite` — TFLite-Modelle
  - `battery_model_float16.tflite`, `battery_model_int8.tflite`, `battery_model_dynamic.tflite` — weitere TFLite-Varianten
  - `scaler.joblib`, `scaler_real.joblib` — Feature-Scaler für Vor-/Nachverarbeitung
  - `metrics.json`, `metrics_real.json` — Evaluationsmetriken
  - `tflite_results.json` — Ergebnisse der TFLite-Evaluation

- `plots/` — Generierte Visualisierungen (Loss, Metriken, Vorhersagen)
- `ERKENNTNISSE.md` — Erkenntnisse und Notizen zum Projekt


Beschreibung wichtiger Skripte

- `generate_data.py`:
  - Liest Rohdaten (`data/*.csv`), erstellt Sequenzen oder Fenster und speichert `X_sequences.npy` / `y_sequences.npy`.
  - Parameter: Fenstergröße, Schrittweite, Normalisierung (ggf. als CLI-Argumente implementiert).

- `train_model.py` / `train_real_data.py`:
  - Laden der Sequenzen, Train/Test-Split, Erstellung eines Keras-Modells (z.B. LSTM/GRU/Dense), Training mit Checkpoints.
  - Am Ende Speichern des Modells unter `model/*.keras` und Erzeugen eines TFLite-Modells via `convert_tflite.py`.

- `convert_tflite.py`:
  - Nimmt ein Keras-Modell oder gespeicherte Gewichtedatei und konvertiert sie in verschiedene TFLite-Formate (float32, float16, int8/quantized).
  - Bei Quantisierung werden `scaler.joblib` oder Kalibrierdaten verwendet.

- `run_pipeline.py`:
  - Kombiniert `generate_data.py`, `train_model.py`, ggf. Evaluation-Skripte und erzeugt `model/`-Artefakte automatisiert.

Android-spezifische Hinweise

- Die Android-App im Verzeichnis `android/app` nutzt TFLite-Modelle aus `model/` (kopieren/Einbinden erforderlich).
- Auf Windows wird die App mit `gradlew.bat assembleDebug` gebaut, alternativ mit Android Studio öffnen und `Run`.
- `local.properties` enthält den SDK-Pfad; zum Bauen sicherstellen, dass Android SDK installiert und `local.properties` korrekt ist.

Umgebung & Abhängigkeiten (Python)

- Empfohlene Python-Version: 3.8–3.11
- Typische Abhängigkeiten (nicht abschließend):
  - `tensorflow` oder `tensorflow-cpu` (zum Trainieren)
  - `numpy`
  - `scikit-learn` (für Scaler und Metriken)
  - `joblib` (zum Speichern von Scaler)
  - `matplotlib` (zum Erzeugen von Plots)
  - `tflite-runtime` (optional, für TFLite-Inferenz außerhalb von TensorFlow)

Beispiel: virtuelle Umgebung und Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install tensorflow numpy scikit-learn joblib matplotlib
# optional: pip install tflite-runtime
```

Wichtige Befehle (Beispielablauf)

```powershell
# Daten erzeugen
python generate_data.py

# Training (synthetisch)
python train_model.py

# Training mit realen Daten
python train_real_data.py

# Pipeline komplett
python run_pipeline.py

# Modell konvertieren
python convert_tflite.py

# Android Debug-APK bauen (Windows)
cd android
gradlew.bat assembleDebug
```

Hinweise für eine andere KI/Automatisierung

- Dateipfade: Verwende projektrelative Pfade, z. B. `data/`, `model/`, `android/app/`.
- Determinismus: Verwende feste Zufalls-Seeds (falls vorhanden) und dokumentiere alle Hyperparameter in Config-Dateien oder Kopfzeilen der Skripte.
- Schnittstellen: Die Skripte sollten klar definierte Ein-/Ausgaben haben (Input-Dateien, Output-Pfade). Falls CLI-Argumente fehlen, erweitere die Skripte mit `argparse`.
- Tests: Eine KI kann einfache Prüfschritte implementieren: Existenz der Eingabedateien, Formate (`.npy`, `.csv`), und erfolgreiche Erzeugung von `model/*.tflite`.

Dateibeschreibungen (Kurzreferenz)

- `X_sequences.npy`, `y_sequences.npy` — NumPy-Arrays: Inputs (3D: samples, timesteps, features), Targets (labels/values pro Sample).
- `scaler.joblib` — scikit-learn Objekt zur Normalisierung; bei Inferenz vor dem Modell anwenden und nachher invertieren falls nötig.
- `metrics.json` — JSON mit Schlüsseln wie `loss`, `val_loss`, `mae`, `rmse` etc.

Entwicklungsempfehlungen

- Git: Ignoriere große Dateien wie `android/build/` und `model/*.tflite` im Repo (oder verwende ein Releases-Asset/Storage), stattdessen nur Quellcode und kleine Checkpoints versionieren.
- Konfiguration: Ergänze ein `requirements.txt` oder `pyproject.toml` für reproduzierbare Abhängigkeiten.
- Automatisierung: Füge ein `Makefile` oder PowerShell-Skripte hinzu, die häufige Abläufe kapseln.

Abschluss

Diese README wurde automatisch erstellt, ohne andere Dateien zu verändern. Wenn du möchtest, kann ich optional ein `requirements.txt` generieren oder die Skripte um einheitliche CLI-Argumente erweitern.

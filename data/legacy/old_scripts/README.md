# Evaluation

Dieser Ordner fasst Evaluationsdaten und -skripte zusammen.

Zweck:
- Ablage von Test-/Validierungsdaten, Kalibrierdaten für Quantisierung und Evaluationsskripten.

Empfohlenes Layout:
- `calibration/` — Daten für INT8-Quantisierung (z. B. kleine .npy-Samples)
- `test_sets/` — getrennte Testsets (z. B. `real/`, `synthetic/`)
- `reports/` — gespeicherte Auswertungen (JSON, CSV, Plots)

Aktuelle Hinweise:
- Trainings- und Evaluationsskripte liegen aktuell im Projektstamm (`train_model.py`). Diese erzeugen bereits `model/metrics.json`.
- Zum Ausführen der Evaluation verwende:

```powershell
# Beispiel: Evaluation läuft als Teil von train_model.py
python ..\train_model.py
```

Wenn du möchtest, kann ich Unterordner `calibration/`, `test_sets/` und `reports/` anlegen und vorhandene Dateien dorthin kopieren.
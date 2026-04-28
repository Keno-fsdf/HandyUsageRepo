# Training

Dieser Ordner dient zur Organisation von Trainingsskripten und -artefakten.

Aktuelle Skripte befinden sich im Projektstamm (z. B. `train_model.py`, `train_real_data.py`).

Empfohlenes Vorgehen:

- Kopiere oder verschiebe die konkreten Trainingsskripte hierher, wenn du die Struktur physisch anpassen möchtest.
- Alternativ kannst du die im Projektstamm verbleibenden Skripte per relativen Pfad aufrufen.

Beispiel: Aus diesem Ordner das Training ausführen (Windows PowerShell):

```powershell
# Aus dem Projektstamm (empfohlen)
python train_model.py

# Oder aus diesem Ordner heraus (relativer Aufruf)
python ..\train_model.py
```

Ablageempfehlungen:
- Modellartefakte: `../model/`
- Plots: `../plots/`
- Scaler: `../model/scaler.joblib`

Wenn du willst, kann ich die Skripte automatisch in diesen Ordner kopieren und Pfade anpassen (sag Bescheid).
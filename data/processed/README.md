# Processed Data

Hier liegen verarbeitete/transformierte Datensätze, die von den Skripten verwendet werden.

Beispiele:
- `X_sequences.npy`, `y_sequences.npy` — Sequenz-Datasets für Training/Evaluation
- Normalisierte oder aggregierte CSV/NPY-Dateien

Empfehlung:
- Lege transformierte Dateien hier ab, rohdaten bleiben in `data/`.

Beispiel-Pfade:
- Rohdaten: `data/battery_data.csv`, `data/real_battery_data.csv`
- Verarbeitet: `data/processed/X_sequences.npy`, `data/processed/y_sequences.npy`

Hinweis: Aktuell liegen `X_sequences.npy` und `y_sequences.npy` im Projektstamm-`data/` Ordner. Wenn du willst, verschiebe ich sie automatisch in `data/processed/` und passe Pfade in den Skripten an.
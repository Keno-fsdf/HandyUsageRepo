# handyUsage — TinyML für Akkulaufzeit-Vorhersage auf Android

**6-Wege-Vergleich auf Multi-Device-Daten** (4 Geräte, 2 Hersteller, 66.001 Messungen).
Geräte: Xiaomi 2107113SG, Google Pixel 7 Pro, 8 Pro, 9 Pro XL.

Sechs Methoden zur Akku-Restzeit-Vorhersage im Vergleich:

| Methode | Wer berechnet | Datenzugang | Rolle |
|---|---|---|---|
| **TinyML Conv1D** | App, TFLite | 10 öffentliche Sensor-/System-Features | Hauptmodell |
| **Random Forest** | Pipeline | gleiche Features (flach) | Sanity (anderes Paradigma) |
| **Mean Predictor** | Pipeline | — | Floor (zeigt: was ohne Features?) |
| **Linear Baseline** | App / Pipeline | `BatteryManager` (charge / current_avg) | Baseline 1 |
| **Exponential Fit** | Pipeline | `b(t) = a + c·exp(-k·t)` aus letzten 10 Punkten | Baseline 2 |
| **Google API** | System | `PowerManager.getBatteryDischargePrediction()` | State of the Art |

Forschungsfrage und vollständiger Befund: siehe [ERKENNTNISSE.md](ERKENNTNISSE.md).
Auto-generierter Ergebnis-Report: [reports/REPORT.md](reports/REPORT.md).
Lit-Review für die Paper-Einleitung: [reports/RELATED_WORK.md](reports/RELATED_WORK.md).

---

## Projektstruktur (forschungsorientiert)

```
handyUsage/
├── configs/                 # default.yaml — eine Wahrheit für alle Hyperparameter
├── data/
│   ├── raw/                 # real_battery_data.csv (read-only)
│   ├── processed/           # train.npz / val.npz / test.npz / predictions_*.npz
│   └── legacy/              # alte Skripte/Daten/ERKENNTNISSE_v1
├── methods/                 # Die SECHS Vergleichsmethoden
│   ├── tinyml/              # Conv1D + TFLite + Predict + Scaler-Export für Android
│   ├── random_forest/       # Sanity-Modell, gleiche Features, anderes Paradigma
│   ├── mean_predictor/      # gibt train mean zurück (Floor-Baseline)
│   ├── linear_baseline/     # battery / drain_rate aus letzten N Punkten
│   ├── exponential_fit/     # b(t) = a + c·exp(-k·t), per Segment
│   └── google_api/          # extrahiert system_estimate_min aus CSV
├── evaluation/
│   ├── accuracy.py          # MAE, RMSE, ME, Acc±t, C-Index + Bootstrap-CI
│   ├── significance.py      # Permutationstests zwischen Methodenpaaren
│   ├── data_diagnostics.py  # Pearson, Spearman, Mutual Information (modell-unabhängig)
│   ├── feature_importance.py# Permutation Importance auf RF
│   ├── per_segment_analysis.py  # Per-Bucket-MAE/C-Idx (Battery-Level, Segmentlänge)
│   ├── three_way_compare.py # 6-Wege-Vergleich + Plots + accuracy.json
│   ├── efficiency.py        # TFLite-Latenz, Modellgröße (MLPerf-Tiny-Stil)
│   └── report_generator.py  # erzeugt reports/REPORT.md aus allen JSON-Artefakten
├── models/                  # *.keras, *_dynamic_range.tflite, *_float16.tflite, *_int8_full.tflite, scaler.joblib, random_forest.joblib
├── reports/
│   ├── REPORT.md            # auto-generiert, paper-ready
│   ├── RELATED_WORK.md      # Lit-Review, BibTeX-Stubs, Story-Struktur
│   ├── accuracy.json
│   ├── significance.json
│   ├── data_diagnostics.json
│   ├── feature_importance.json
│   ├── per_segment_analysis.json
│   ├── efficiency.json
│   ├── main_table.csv       # Hauptergebnisse zum LaTeX/Word-Import
│   └── figures/             # Cumulative Error, Scatter, Histogramme, Trainings-Kurven
├── android/                 # Kotlin: Datensammlung + On-Device-Inferenz
├── run_pipeline.py          # Orchestrator
├── ERKENNTNISSE.md          # methodische Notizen + Hauptergebnisse
├── architektur_gesamt.puml  # Pipeline-Diagramm (für Paper)
├── requirements.txt
└── README.md
```

---

## Pipeline ausführen

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Komplette Pipeline (merge → data → train → tflite → train_rf → predict → evaluate → report)
python run_pipeline.py

# Einzelne Stages:
python run_pipeline.py --stage merge       # 4 CSVs zu data/raw/combined.csv konsolidieren
python run_pipeline.py --stage data        # Segmente, Sliding-Window, Train/Val/Test
python run_pipeline.py --stage train       # Conv1D
python run_pipeline.py --stage tflite      # 3 TFLite-Varianten + Latenz-Benchmark
python run_pipeline.py --stage train_rf    # Random Forest Sanity-Modell
python run_pipeline.py --stage predict     # alle 6 Methoden
python run_pipeline.py --stage evaluate    # Accuracy, Significance, Per-Device, Diagnostics
python run_pipeline.py --stage report      # reports/REPORT.md zusammenstellen
```

Ergebnis nach vollem Lauf:
- [reports/REPORT.md](reports/REPORT.md) — alle Tabellen + Bootstrap-CI + Permutationstests
- [reports/main_table.csv](reports/main_table.csv) — kompakter CSV-Import für Paper-Tabellen
- [reports/figures/](reports/figures/) — alle Plots fürs Paper

---

## Methodische Hinweise (paper-relevant)

1. **Kein Sequenz-Level-Leakage.** Train/Val/Test wird auf **Segment-Ebene** gesplittet. Sliding-Window-Sequenzen aus demselben Entladesegment landen nie in Train UND Test. Auf identischer Datenbasis: MAE 0.53 h (Random-Split, geleakt) → 9.96 h (Segment-Split, sauber). Diese Größenordnung-Differenz ist im Paper als methodischer Beitrag wert (Hidden Leaks in Time Series Forecasting, Polonis 2025).
2. **Zwei Targets pro Sample.** `y_extrap` (Trainings-Target mit Drain-Rate-Extrapolation) und `y_real` (gemessene Restzeit ohne Extrapolation). Endergebnisse werden gegen `y_extrap` auf Common-Subset berichtet (das gemeinsame Approximations-Target aller 6 Methoden).
3. **Common-Subset-Tabelle.** Der faire Vergleich nur dort, wo alle 6 Methoden gültige Werte haben (Google API undefiniert wenn ladend, Exp-Fit undefiniert am Segment-Anfang etc.).
4. **Concordance-Index (Harrell 1982)** zusätzlich zu MAE — Bias-robust und auch bei zensierten Targets aussagekräftig (Li et al. 2018).
5. **Bootstrap 95%-CI** für MAE/RMSE/C-Index (1.000 Resamples) und **Permutationstests** für paarweise Methoden-Vergleiche.
6. **Modell-unabhängige Daten-Diagnose** (Pearson, Spearman, Mutual Information) ergänzt die Random-Forest-Permutation-Importance — beide Sichten zusammen erlauben die Aussage, dass das Daten-Limit modell-unabhängig ist.
7. **MLPerf-Tiny-konform**. TFLite-Effizienz wird in Größe + Latenz (avg, p50, p95) für alle Quantisierungen gemessen.

## Android-App

```powershell
cd android
./gradlew.bat assembleDebug
```

Wichtige Code-Stellen:
- `DataCollectorService.kt` — alle 30 s ein Datenpunkt (10 Features + Google-Schätzung + Personalized-Flag + eigene Vorhersage + lineare Baseline) wird in `filesDir/battery_data.csv` geschrieben.
- `BatteryPredictor.kt` — TFLite-Interpreter mit StandardScaler. Nach jedem Re-Training die Scaler-Werte neu setzen via:
  ```powershell
  python -m methods.tinyml.export_scaler_for_android
  ```
- Wenn das CSV-Schema sich ändert (neue Spalte in `BatteryDataPoint.CSV_HEADER`), parkt der Logger die alte CSV automatisch unter `battery_data_legacy_<timestamp>.csv`.

## Daten exportieren vom Phone

CSV via Share-Intent (Mail / Drive / USB) ans Notebook holen, nach `data/raw/real_battery_data.csv` legen, dann `python run_pipeline.py`.

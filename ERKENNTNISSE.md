# Erkenntnisse — TinyML für Akkulaufzeit-Vorhersage auf Android

> Stand der aktuellen Pipeline (Multi-Device, Segment-Level-Split, 6-Wege-Vergleich).
> Die historische Single-Device-Version liegt unter
> [data/legacy/ERKENNTNISSE_v1_pre_segment_split.md](data/legacy/ERKENNTNISSE_v1_pre_segment_split.md).
> Alle aktuellen Zahlen kommen aus [reports/REPORT.md](reports/REPORT.md).

## 1. Forschungsfrage und Setup

> *„Wie gut kann TinyML die Akkulaufzeit auf Android vorhersagen im Vergleich
> zu exponentiellem Fitting und der nativen Google-API, bezogen auf
> Genauigkeit sowie Effizienz?"*

**Datenbasis (Multi-Device)**
- **4 Geräte**, 2 Hersteller (Xiaomi und Google)
- **66.001 Datenpunkte** über 45 Tage (25.03.--10.05.2026, je Gerät 21--34 Tage), **180 Sessions**
- Nach Segmentierung: **553 Discharge-Segmente** mit ≥15 Punkten
- Sliding-Window (Länge 10): **20.842 Sequenzen**, gesplittet auf Segment-Ebene
  in 13.901 Train / 3.056 Val / 3.885 Test

**Geräte-Verteilung im Test-Set**
| Gerät | Test-Sequenzen | y_extrap mean (h) |
|---|---|---|
| Pixel 7 Pro | 1.825 | 5.79 |
| Pixel 9 Pro XL | 614 | 7.93 |
| Pixel 8 Pro | 98 | 7.68 |
| Xiaomi 2107113SG | 1.348 | 10.14 |

**Verglichene Methoden (6-Wege)**
1. **TinyML Conv1D** — 5.697 Parameter, 14.4 KB als INT8 TFLite
2. **Random Forest** — Sanity-Modell, gleiche Features, anderes Paradigma
3. **Mean Predictor** — gibt immer den Trainings-Mittelwert zurück (Floor)
4. **Linear Baseline** — `battery / drain_rate` aus letzten 10 Punkten
5. **Exponential Fit** — `b(t) = a + c·exp(-k·t)` per Segment, mit 72h-Cap gegen Divergenz
6. **Google API** — `PowerManager.getBatteryDischargePrediction()` (Android 12+)

## 2. Methodische Entscheidungen

### Segment-Level-Split (Leakage-Vermeidung)

Sliding-Window-Sequenzen aus demselben Discharge-Segment werden nie gleichzeitig
in Train UND Test geführt. Begründung: Hidden Leaks in Time Series Forecasting
(Albelali und Ahmed 2025) — Random-Shuffle-Split auf Sequenzen ist Data Leakage.

**Direkter Beleg dieser Wirkung** (Single-Device-Subset, identisches Conv1D):

| Split-Strategie | Test MAE (h) | Aussagekraft |
|---|---|---|
| Random Shuffle (alt) | 0.53 | Leakage-Artefakt |
| Segment-Level (neu) | **9.96** | sauber |

→ Eine Größenordnung Differenz, allein durch den Split. Eigener methodischer
Beitrag fürs Paper.

### Zwei Targets pro Datenpunkt

- **`y_extrap`** = Zeit bis Segment-Ende + Drain-Rate-Extrapolation auf 0%
  (Multi-Device-Test-Mittelwert ~7.7h, das gemeinsame Target aller Methoden).
- **`y_real`** = nur die gemessene Zeit bis Segment-Ende, ohne Extrapolation
  (Multi-Device: max 6.37h, mean 1.11h — datenbedingt right-censored).

Endergebnisse berichten wir gegen `y_extrap` auf der Common-Subset-Tabelle.

### Bias-robuste Metrik: Concordance-Index

Smartphone-Akku-Restzeit ist **right-censored** (User entladen selten auf 0%).
Wir folgen Li et al. (2018) und nutzen den C-Index (Harrell 1982) als primäre
Metrik. MAE/RMSE als sekundäre Metrik gegen `y_extrap`.

### Statistische Härte

- **Bootstrap 95%-CI** für MAE, RMSE und C-Index (1.000 Resamples).
- **Permutationstests** (1.000 Perms) für paarweise Methoden-Vergleiche.
- Alle Konfigurationen seed-gesteuert in `configs/default.yaml` festgehalten.

## 3. Hauptergebnisse (Multi-Device)

### Common Subset, vs. y_extrap (n=2.827, alle Methoden gültig)

| Methode | C-Index 95%-CI | MAE 95%-CI |
|---|---|---|
| Mean Predictor | 0.500 [0.500, 0.500] | 6.51 [6.28, 6.75] |
| **TinyML Conv1D** | **0.666 [0.656, 0.675]** | **4.28 [4.04, 4.53]** |
| **Random Forest** | **0.686 [0.673, 0.696]** | 4.01 [3.79, 4.25] |
| Linear | 0.776 [0.767, 0.784] | **3.21 [2.93, 3.49]** |
| Exponential | 0.773 [0.764, 0.781] | 3.49 [3.20, 3.76] |
| Google API | 0.777 [0.767, 0.785] | 3.24 [2.97, 3.52] |

→ **Headline 1:** Beide ML-Modelle schlagen den Mean-Predictor signifikant
(p≤0.005). Anders als auf dem Single-Device-Setup ist TinyML jetzt klar
**über** dem Floor.

→ **Headline 2:** Linear, Exponential und Google sind statistisch nicht zu
unterscheiden (Linear vs Google p=0.83, Linear vs Exp p=0.30). Die Google-API
ist **nicht** klar überlegen — die simple `charge/drain_rate`-Baseline ist
auf Augenhöhe.

### Per-Device-Performance (vs. y_extrap)

| Gerät | n | TinyML C | RF C | Linear C | Google C |
|---|---|---|---|---|---|
| Pixel 7 Pro | 1.825 | 0.79 | 0.80 | 0.79 | **0.85** |
| Pixel 8 Pro | 98 | 0.71 | 0.80 | 0.70 | **0.92** |
| Pixel 9 Pro XL | 614 | 0.60 | 0.76 | **0.73** | 0.68 |
| Xiaomi | 1.348 | 0.59 | 0.63 | **0.72** | 0.66 |

→ **Headline 3:** Hardware-Effekt ist groß. TinyML schwankt zwischen
C=0.79 (Pixel 7 Pro) und C=0.59 (Xiaomi). Das ist **die zentrale neue
Erkenntnis** des Multi-Device-Settings.

### Bemerkenswerte Einzelbeobachtungen
- **Pixel 9 Pro XL**: Linear (0.73) schlägt Google (0.68). Klare Gegenevidenz
  zu „ML wins always".
- **Pixel 8 Pro**: Google C=0.92 (sehr gut beim Ranking) aber MAE=9.92h
  (sehr schlecht beim absoluten Wert) — das motiviert die Wahl von C-Index
  als primäre Metrik.

### Effizienz-Benchmark

| Variante | Größe | Avg Latenz |
|---|---|---|
| Keras Float32 | 109.18 KB | 47.1 ms |
| TFLite Dynamic Range | 15.99 KB | 3.9 µs |
| TFLite Float16 | 17.80 KB | 3.7 µs |
| **TFLite INT8 (deploy)** | **14.35 KB** | **4.5 µs** |

→ Die TinyML-Quantisierung funktioniert technisch einwandfrei: 7.6× kleineres
Modell, ~10.000× schnellere Inferenz. Der Tiny-Aspekt der Arbeit ist
**unangefochten**.

## 4. Was das fürs Paper heißt — Antwort auf den Dreiklang

**Genauigkeit:** TinyML lernt erkennbares Signal (C=0.67), bleibt aber
hinter den analytischen Baselines und Google API (alle bei C≈0.77).
Die analytische Baseline ist auf Augenhöhe mit Google.

**Effizienz:** Die Quantisierungs-Pipeline funktioniert. 14 KB INT8,
~5 µs Inferenz. Auf der Effizienz-Achse ist TinyML uneingeschränkt
empfehlenswert.

**Vergleich vs. Google:** Auf Pixel-Hardware liegt Google klar vorne
(C=0.85 auf Pixel 7 Pro). Auf Xiaomi und Pixel 9 Pro XL ist die
einfache lineare Drain-Rate-Baseline überraschend konkurrenzfähig.
Der Mehrwert der Google-API ist **hardware-abhängig**.

## 5. Bekannte Limitationen (im Paper ehrlich nennen)

1. **Right-Censoring intrinsisch**: Akku wird im Alltag nie auf 0%
   entladen → echte Restzeit nicht direkt beobachtbar. Mitigation
   via C-Index (Standard in der Literatur).
2. **Common-Subset-Selection-Bias**: Der gemeinsame Subset hat
   y_extrap mean ~6.7h vs Test gesamt ~7.7h. Google-API ist häufiger
   bei kürzeren Restzeiten verfügbar. Affektiert MAE-Werte symmetrisch
   (Ranking unbeeinflusst).
3. **Multi-Device, aber nicht Cross-Device-Generalisierung**: Train
   sieht alle 4 Geräte. Eine Leave-One-Device-Out-Studie ist offene
   Folgearbeit.
4. **n=98 für Pixel 8 Pro**: zu klein für stabile CIs.
5. **TinyML auf Pixel 9 Pro XL anomal schlecht** (C=0.60), während
   RF auf demselben Gerät C=0.76 erreicht. Keine kausale Erklärung
   im aktuellen Datensatz.
6. **3 Features konstant**: `wifi_on`=0, `mobile_data_on`=1,
   `charging`=0 nach Discharge-Filter (auf manchen Geräten).
   Multi-Device-Variation würde das teilweise heilen.

## 6. Was eine wirklich saubere Folgestudie bräuchte

- Leave-One-Device-Out-Cross-Validation für echte
  Cross-Device-Generalisierung
- Pro-Device-Trainings vs. global trainiertes Modell — vermutlich
  würden gerätespezifische Modelle weiter besser performen
- 3-5 vollständige Entladezyklen pro Gerät → Ground Truth ohne
  Censoring
- Längerer Zeitraum (~3 Monate) mit Variation der Ladegewohnheiten
- Hyperparameter-Sweep für Conv1D speziell auf Pixel-9-Pro-XL-Daten
  (warum versagt TinyML dort?)

# Related Work — Notizen für die Paper-Einleitung

Strukturierte Zusammenfassung der recherchierten Literatur. Vier Themenblöcke:
(1) Battery Prediction auf Smartphones, (2) TinyML allgemein,
(3) Evaluations-Methodik / Data Leakage, (4) Battery-Modellierung physikalisch.

Zitiervorschläge sind Beispiele — Stil an die Konferenz/Journal-Vorgaben anpassen.

---

## 1. Battery Prediction auf Smartphones

### Li et al. (2018) — *Predicting Smartphone Battery Life based on Comprehensive and Real-time Usage Data*

- **arXiv**: <https://arxiv.org/abs/1801.04069>
- **Datensatz**: 51 Nutzer, 21 Monate, fein-granulare Smartphone-Nutzung (System-Status, Sensor-Indikatoren, System-Events, App-Status).
- **Methodik**: Erste Arbeit, die das Missing-Data-Problem (User entladen selten auf 0%) explizit adressiert. Verwenden den **Concordance-Index (Harrell 1982)** als primäre Metrik, weil dieser invariant gegen Bias und unter zensierten Bedingungen valide bleibt.
- **Ergebnis**: ML-Modelle können Restlaufzeit aus Nutzungsverhalten + Sensor-Daten vorhersagen, Identifizieren prädiktive Features.
- **Wichtig für unser Paper**: Begründet die Wahl des C-Index als zusätzliche Metrik. Liefert die methodische Vorlage, dass MAE allein bei zensierten Daten täuschen kann.

> *Beispiel-Zitation*: „Wie Li et al. (2018) auf einem deutlich größeren Datensatz von 51 Nutzern über 21 Monaten zeigten, ist die echte Restlaufzeit von Smartphones systematisch zensiert — wir folgen ihrem Ansatz und nutzen den Concordance-Index als Bias-robuste Bewertungsmetrik."

### Flores-Martin et al. (2024) — *Enhancing Smartphone Battery Life: A Deep Learning Model Based on User-Specific Application and Network Behavior*

- **MDPI Electronics 13(24), 4897, Dezember 2024**: <https://www.mdpi.com/2079-9292/13/24/4897>
- **Methodik**: Android-App zur passiven Datensammlung. LSTM auf User-spezifischen Sequenzen. Vergleichsbasis: Battery Historian Framework.
- **Features**: Application Usage, Screen Time, Network Type, Network Usage, Battery Temperature.
- **Wichtig für unser Paper**: Direkter Methodik-Verwandter — bestätigt App-basierte Datensammlung als Standardansatz. Wir gehen einen Schritt weiter: zusätzlich Vergleich gegen native Google-API und einfache Baselines.

> *Beispiel-Zitation*: „Flores-Martin et al. (2024) implementieren einen LSTM-Ansatz mit App-spezifischer Datensammlung. Unsere Arbeit erweitert dieses Setup um (i) ein TinyML-quantisiertes On-Device-Modell, (ii) einen 6-Wege-Vergleich gegen native und analytische Baselines, und (iii) eine modell-unabhängige Feature-Diagnose."

---

## 2. TinyML — Frameworks und Benchmarks

### Banbury et al. (2021) — *MLPerf Tiny Benchmark*

- **arXiv**: <https://arxiv.org/abs/2106.07597>
- **NeurIPS 2021 Datasets and Benchmarks Track**
- **Inhalt**: Erster industrieller Standard-Benchmark für TinyML-Inferenz auf ultra-low-power Systemen. Drei Pflicht-Metriken: **Accuracy, Latency, Energy**. Zwei Divisionen: Closed (gleiches Modell) und Open (eigene Modelle).
- **Wichtig für unser Paper**: Begründet, warum wir Latenz + Modellgröße + Accuracy gemeinsam berichten. Wir replizieren die methodische Trias (außer Energie, da auf Smartphone nicht zugänglich).

> *Beispiel-Zitation*: „Wir folgen der MLPerf-Tiny-Methodik (Banbury et al. 2021) und berichten Accuracy, Inferenzlatenz und Modellgröße gemeinsam. Energie wird als Proxy über Latenz + CPU-Auslastung geschätzt, da direkter Strommessung auf App-Ebene nicht möglich ist."

### Asutkar et al. (2023) — *TinyML: Enabling of Inference Deep Learning Models on Ultra-Low-Power IoT Edge Devices*

- **PMC**: <https://pmc.ncbi.nlm.nih.gov/articles/PMC9227753/>
- **Inhalt**: Survey über TinyML-Anwendungen auf Mikrocontrollern. Identifiziert vier Standard-Metriken: Modell-Accuracy, Inferenz-Latenz (0.18-300 ms typisch), Speicher, Power (25-300 mW vs. 50-1000 W Cloud).
- **Befund**: „evaluation metrics extracted from TinyML experiments were not standardized across experiments" — Lücke, die MLPerf zu schließen versucht.

### Bouguettaya et al. (2025) — *Tiny Machine Learning and On-Device Inference: A Survey of Applications, Challenges, and Future Directions*

- **PMC**: <https://pmc.ncbi.nlm.nih.gov/articles/PMC12115890/>
- **Inhalt**: Aktuelles Survey, fokussiert auf Mikrocontroller (Arduino, Raspberry Pi). **Keine Smartphone-spezifischen Anwendungen** — eine Lücke, die unsere Arbeit explizit anspricht.

> *Beispiel-Zitation*: „Aktuelle TinyML-Surveys (Bouguettaya et al. 2025) fokussieren auf Mikrocontroller-Hardware. Smartphone-Anwendungen sind unterrepräsentiert, obwohl sich die Frage nach dem methodischen Mehrwert von TinyML auf einer Hardware mit GB-RAM legitim stellt — was unsere Arbeit untersucht."

---

## 3. Evaluations-Methodik

### Albelali & Ahmed (2025) — *Hidden Leaks in Time Series Forecasting: How Data Leakage Affects LSTM Evaluation*

- **arXiv**: <https://arxiv.org/html/2512.06932v1>
- **Inhalt**: Demonstriert, dass Data Leakage in Zeitreihen-Settings die Performance um Größenordnungen überschätzt. Spezifisch: Sequenzen aus Sliding-Windows mit Random-Split lassen Future-Information in den Train-Set lecken.
- **Wichtig für unser Paper**: Zentrale Begründung für unseren Segment-Level-Split. Wir können beobachtet zeigen: dieselbe Datenbasis ergibt MAE 0.5h (Random-Split, geleakt) vs. MAE 9-10h (Segment-Split, sauber).

> *Beispiel-Zitation*: „Random-Sequenz-Splits in Time-Series-Settings führen zu Data Leakage (Albelali & Ahmed 2025). Wir splitten daher auf Segment-Ebene: Sliding-Window-Sequenzen aus demselben Discharge-Segment landen niemals in Train UND Test. Auf einem identischen Datensatz reduziert dies den scheinbaren MAE des Conv1D-Modells von 0.53 h (geleakt) auf 9.96 h (sauber) — eine Größenordnung."

### Harrell (1982) — *Evaluating the yield of medical tests* (Konkordanz-Index)

- **JAMA, klassische Survival-Analysis-Referenz**
- **Inhalt**: C-Index als Anteil korrekt geordneter Paare. Robust gegen zensierte Daten. Standard in Survival Analysis seit 40+ Jahren.
- **Wichtig für unser Paper**: Methodische Verankerung des C-Index. Smartphone-Akku-Restzeit ist konzeptuell **right-censored survival data**.

---

## 4. Battery-Modellierung physikalisch (Kontext, nicht direkt vergleichbar)

### Hu et al. (2024) — *A Review of Degradation Models and Remaining Useful Life Prediction*

- **PMC**: <https://pmc.ncbi.nlm.nih.gov/articles/PMC11174798/>
- **Kontext**: Beschreibt klassische Degradationsmodelle (single/double exponential decay) für Lithium-Ion-Zellen über **Cycles** (langzeitige Alterung). **Nicht direkt anwendbar** auf unser Problem (Restzeit innerhalb eines Entladezyklus), aber liefert die Begründung für die Form unseres exponentiellen Fits: `b(t) = a + c · exp(-k·t)`.

### NREL Technical Report (2021) — *Challenging Practices of Algebraic Battery Life Models*

- **NREL/TP-5400-78256**: <https://docs.nrel.gov/docs/fy21osti/78256.pdf>
- **Inhalt**: Argumentiert gegen alle einfachen algebraischen Modelle für Battery-Aging — relevant für die Diskussion, dass auch einfache Fits (linear, exponential) per se limitiert sind.

---

## 5. Android API — Primär-Quelle

### `PowerManager.getBatteryDischargePrediction()`

- **Android Developer Docs**: <https://developer.android.com/reference/android/os/PowerManager#getBatteryDischargePrediction()>
- **Verfügbar**: API 31 (Android 12), Oktober 2021.
- **Verwandt**: `PowerManager.isBatteryDischargePredictionPersonalized()` zeigt an, ob die Schätzung gerätspezifisch eingelernt ist.
- **Wichtig für unser Paper**: Die einzige offizielle ML-basierte Smartphone-Akkuvorhersage-API. Wir loggen sowohl den Wert als auch das Personalisierungs-Flag, um faire Vergleiche zu ermöglichen.

---

## 6. Empfohlene Story-Struktur fürs Paper

1. **Einleitung**: Akkulaufzeit-Vorhersage als Problem (Flores-Martin et al. 2024, Li 2018). Native Lösung seit Android 12 — wie gut ist sie *wirklich*, und kann eine Drittanbieter-App da mithalten?
2. **Related Work**: Drei Stränge — Battery Prediction (Li 2018, Flores-Martin et al. 2024), TinyML (MLPerf Tiny, TinyML Surveys), Evaluation Methodology (Albelali & Ahmed 2025, Harrell 1982).
3. **Methodik**:
   - Datensammlung-App (10 Features, 30s, 38k Datenpunkte über 10 Tage)
   - Vier Methoden im Vergleich (TinyML / RF / Linear / Exp / Google) plus Mean-Predictor als Floor
   - **Segment-Level-Split** (kein Leakage)
   - Bias-robuste Metriken (C-Index)
   - Bootstrap-CI + Permutationstests für statistische Signifikanz
4. **Ergebnisse**:
   - Random Forest und TinyML konvergieren beide auf C-Index ≈ 0.5 (Mean-Predictor-Niveau)
   - Google führt klar (C-Index 0.79 [bootstrap CI])
   - Datendiagnose: 9/10 Features liefern keine messbare Information
   - Effizienz-Benchmark: TFLite-Quantisierung funktioniert technisch (14 KB, 5 µs)
5. **Diskussion**:
   - Limitierender Faktor ist **nicht** Modell-Architektur, sondern **App-Level-Sensorzugang**
   - TinyML-Idee technisch valide, aber bei Smartphones inhaltlich überflüssig
   - Notwendigkeit eines prospektiven Live-Tests für definitive Aussagen
6. **Fazit**: Negative Ergebnis + Methodik-Beitrag (Leakage-Sensitivität, faire Multi-Methoden-Evaluation).

---

## BibTeX-Vorschläge

```bibtex
@article{li2018predicting,
  title={Predicting Smartphone Battery Life based on Comprehensive and Real-time Usage Data},
  author={Li, Huoran and Lu, Xuan and Liu, Xuanzhe and others},
  journal={arXiv preprint arXiv:1801.04069},
  year={2018}
}

@article{floresmartin2024enhancing,
  title={Enhancing Smartphone Battery Life: A Deep Learning Model Based on User-Specific Application and Network Behavior},
  journal={Electronics},
  volume={13},
  number={24},
  pages={4897},
  year={2024},
  publisher={MDPI}
}

@inproceedings{banbury2021mlperf,
  title={MLPerf Tiny Benchmark},
  author={Banbury, Colby and Reddi, Vijay Janapa and Torelli, Peter and others},
  booktitle={NeurIPS Datasets and Benchmarks Track},
  year={2021}
}

@article{harrell1982evaluating,
  title={Evaluating the yield of medical tests},
  author={Harrell, Frank E. and Califf, Robert M. and Pryor, David B. and Lee, Kerry L. and Rosati, Robert A.},
  journal={JAMA},
  volume={247},
  number={18},
  pages={2543--2546},
  year={1982}
}
```

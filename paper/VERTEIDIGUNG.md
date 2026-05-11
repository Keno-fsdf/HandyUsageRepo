# Verteidigungs-Spickzettel (Multi-Device-Stand)

> Version 2 — nach Hinzunahme der drei Pixel-Geräte (Pixel 7 Pro,
> Pixel 8 Pro, Pixel 9 Pro XL) zusätzlich zum Xiaomi.
> Aktuelle Zahlen aus `reports/REPORT.md` und `reports/per_device_analysis.json`.

---

## 1. Der Drei-Sätze-Pitch (auswendig)

> *„Ich habe sechs konkurrierende Methoden zur Akkulaufzeit-Vorhersage auf Android verglichen — TinyML Conv1D, Random Forest, Mean-Predictor als Floor, lineare Drain-Rate, exponentielles Fitting und die native Google-API — auf einem Multi-Device-Datensatz von vier Geräten (Xiaomi und drei Pixel) mit insgesamt 66.000 Messungen über 45 Tage (je Gerät 21–34 Tage aktiv). Mit einem leakage-freien Segment-Level-Split: beide ML-Modelle schlagen den Mean-Predictor signifikant (TinyML C-Index 0.67, RF 0.69, p≤0.005), aber die analytischen Baselines und die Google-API sind in einer gemeinsamen Spitzengruppe bei C≈0.77 — und die Google-API ist statistisch nicht von der einfachen linearen Drain-Rate-Baseline zu unterscheiden. Mein Hauptbefund ist die starke Hardware-Abhängigkeit: dasselbe TinyML-Modell erreicht auf Pixel 7 Pro C=0.79, auf Xiaomi nur C=0.59."*

Diesen Absatz solltest du **flüssig sprechen können**.

---

## 2. Schlüsselzahlen (sollten präsent sein)

| Was | Zahl |
|---|---|
| Datenmenge | **66.001** Messungen, **553** Discharge-Segmente, **180** Sessions |
| Geräte | **4** (Xiaomi 2107113SG, Pixel 7/8/9 Pro) |
| TinyML Modell | **5.697 Parameter**, **14.7 KB** INT8 TFLite |
| Inferenzlatenz | **~5 µs** TFLite vs. ~43 ms Keras Float32 |
| Common Subset | **n=2.827** für 6-Wege-Vergleich |
| TinyML C-Index | **0.666** [0.656, 0.675] |
| Random Forest C-Index | **0.686** [0.673, 0.696] |
| Mean Predictor (Floor) | 0.500 |
| Linear C-Index | **0.776** |
| Google C-Index | **0.777** |
| Linear vs. Google C | $\Delta$=−0.001, p=**0.83** (n.s.) |
| TinyML vs. Mean p | **0.005** (signifikant über Floor) |
| TinyML auf Pixel 7 Pro | C=**0.79** |
| TinyML auf Xiaomi | C=**0.59** |

---

## 3. Wenn jemand sagt: „Ihre ML-Modelle sind ja schlechter als die simplen Baselines"

**Standard-Antwort:**

> *„Stimmt — und das ist eine wissenschaftlich interessante Beobachtung. Die linearen Drain-Rate-Baseline und das exponentielle Fitting nutzen direkt das, was die ML-Modelle erst aus zehn schwach korrelierten Features rekonstruieren müssen — nämlich die Drain-Rate selbst. Mit einem reicheren Feature-Set, insbesondere mit Zugriff auf die instantane Stromstärke aus dem Kernel-Fuel-Gauge, würde sich das Bild vermutlich umkehren. Aber auf öffentlich zugänglichen Sensoren ist der Mehrwert eines gelernten Modells gegenüber `b/dot{b}`-Extrapolation gering. Genau das ist eine messbare Aussage über die Limits von App-Level-TinyML."*

---

## 4. Wenn jemand sagt: „Aber Google sollte doch viel besser sein als Linear"

**Das ist die spannendste Beobachtung deiner Arbeit.** Antwort:

> *„Das überrascht mich auch, ist aber genau der Befund: auf der gemeinsamen Schnittmenge von 2.827 Test-Punkten ist der Permutationstest-p-Wert für den C-Index-Unterschied zwischen Linear und Google bei 0.83 — sie sind statistisch ununterscheidbar. Auf MAE genauso (p=0.55). Google hat als Systemprozess Zugriff auf zusätzliche Signale — etwa per-App-Stromverbrauch über PowerStats HAL und Integration ins Adaptive-Battery-System — die für Drittanbieter-Apps nicht verfügbar sind. Aber für die spezifische Frage 'wie viele Stunden bis 0%' liefert die einfache `charge_counter / current_average`-Berechnung im Wesentlichen dasselbe Signal. Für die Praxis heißt das: ein App-Entwickler kann mit der `BatteryManager`-API allein eine prinzipiell konkurrenzfähige Schätzung implementieren — er braucht nur den C-Index nicht."*

Auf Pixel 9 Pro XL ist Linear sogar **besser** als Google (C=0.73 vs 0.68) — falls jemand danach fragt.

---

## 5. Wenn jemand sagt: „Die Performance schwankt ja extrem zwischen den Geräten"

**Das ist genau der Punkt — als Erkenntnis verkaufen, nicht als Schwäche:**

> *„Ja, das ist der praktisch relevanteste Befund. Auf Pixel 7 Pro erreicht TinyML C=0.79, auf Xiaomi nur C=0.59 — eine Differenz von 0.20 in einer Metrik, die zwischen 0.5 (Zufall) und 0.85 (bestes Ergebnis im Datensatz) liegt. Das heißt: für einen real deployten App-Level-Battery-Predictor müsste man pro Geräteklasse eine eigene Konfidenz-Schätzung mitliefern. Eine globale Modell-Konfidenz ist irreführend. Diese Beobachtung ist aus meiner Sicht der eigentliche praktische Beitrag der Arbeit, weil sie für jeden Entwickler relevant ist, der ähnliche Modelle deployen will."*

---

## 6. Wenn jemand sagt: „Aber das Phone wird nie ganz entladen"

**Standard-Antwort (gleich wie Version 1):**

> *„Smartphone-Akku-Daten sind in der Survival-Analysis-Sprache 'right-censored' — eine intrinsische Eigenschaft der Domäne, kein Defizit der Studie. Li et al. 2018 hatten dasselbe Problem auf 51 Geräten mit 21 Monaten und haben deshalb den Concordance-Index als primäre Metrik eingeführt. Ich folge derselben Konvention. Eine Studie ohne Censoring würde einen kontrollierten Discharge-Protokoll erfordern, der nur auf dieses Protokoll generalisiert."*

---

## 7. Wenn jemand sagt: „Was hätten Sie anders gemacht?"

**Antwort:**

> *„Drei Sachen. Erstens würde ich von Anfang an mit Segment-Level-Split arbeiten — die initiale Random-Shuffle-Variante hat MAE 0.53h gezeigt, was sich als Leakage-Artefakt entpuppte (echter Wert: 9.96h). Zweitens würde ich gezielt eine Pixel- und Xiaomi-Variante separat trainieren, statt ein gemeinsames Modell — der Hardware-Effekt ist groß genug, dass per-Geräteklasse-Modelle vermutlich besser performen. Drittens würde ich ein paar kontrollierte Vollentlade-Zyklen mit einem Zweitgerät durchführen, um Ground-Truth-Validierung zu haben."*

---

## 7b. Wenn jemand sagt: „Generalisiert das auf neue Geräte?"

**Standard-Antwort:**

> *„Das ist eine offen gelassene Frage. Mein Train/Val/Test-Split ist segment-level über alle vier Geräte hinweg, also hat das Modell jedes der vier Geräte im Training gesehen. Eine Leave-One-Device-Out-Studie wäre der saubere Test für Cross-Device-Generalisierung — ich habe sie als zentrale Folgearbeit in Section VII benannt. Der gefundene starke Hardware-Effekt deutet aber darauf hin, dass die Generalisierung problematisch wäre und gerätespezifisches Training notwendig sein dürfte."*

## 7c. Wenn jemand sagt: „Auf Pixel 9 Pro XL funktioniert Ihr TinyML nicht — warum?"

**Ehrliche Antwort:**

> *„Das ist eine offene Beobachtung. TinyML erreicht dort C=0.60, der Random Forest auf den gleichen Daten C=0.76 — also dreimal die Distanz zum Mean-Predictor-Floor. Ich habe keine kausale Erklärung. Drei Hypothesen: erstens unterscheidet sich der Pixel-9-Pro-XL-Sensor-Stack möglicherweise von den älteren Pixels in einer Weise, die meine zehn Features nicht abbilden. Zweitens könnte der StandardScaler, den ich auf den Trainingsdaten fit, schlechter zur gerätespezifischen Feature-Verteilung passen. Drittens ist Pixel 9 Pro XL der jüngste der vier Geräte — vielleicht ein generelles Distribution-Shift-Phänomen. Ohne kontrollierte Tests kann ich keine davon beweisen."*

Das offen zuzugeben ist STÄRKER als eine erfundene Erklärung.

## 7d. Wenn jemand sagt: „Linear-Baseline ist besser als Google? Das kann nicht sein"

**Standard-Antwort:**

> *„Das hat mich auch überrascht, ist aber statistisch belastbar. Auf der gemeinsamen Schnittmenge von 2.827 Test-Punkten ist der Permutationstest-p-Wert für den C-Index-Unterschied zwischen Linear und Google bei 0.83 — sie sind ununterscheidbar. Auf Pixel 9 Pro XL führt Linear sogar (C=0.73 vs Google 0.68). Die Erklärung ist plausibel: für die spezifische Frage 'wie viele Stunden bis 0%' ist die aktuelle Drain-Rate das dominante Signal. Google's zusätzlicher Hardware-Zugang bringt für diese Frage offenbar keinen Mehrwert über `charge/current_avg`. Praktisch heißt das: ein App-Entwickler kann mit der `BatteryManager`-API allein eine konkurrenzfähige Schätzung implementieren."*

---

## 8. Stärke-Themen, die du AKTIV einbringen solltest

- **Multi-Device-Studie** mit 4 Geräten von 2 Herstellern — der Dreisatz wurde eingelöst
- **Bootstrap 95%-Konfidenzintervalle** für alle Hauptmetriken
- **Permutationstests** für statistische Signifikanz aller paarweisen Vergleiche
- **Modell-unabhängige Daten-Diagnose** (Pearson, Spearman, MI)
- **Reproduzierbarkeit**: ein-Befehl-Pipeline (`python run_pipeline.py`)
- **Per-Device-Analyse** als zentrale neue Erkenntnis
- **Leakage-Beobachtung als methodischer Beitrag** (eigenständig publizierbar)

---

## 9. Aussagen die du VERMEIDEN solltest

| ❌ Nicht sagen | ✓ Stattdessen |
|---|---|
| „TinyML schlägt nichts" | „TinyML schlägt den Mean-Predictor signifikant (p≤0.005), bleibt aber hinter den analytischen Baselines" |
| „Mein Modell ist schlecht" | „Mein Modell ist hardware-abhängig: 0.79 auf Pixel 7 Pro, 0.59 auf Xiaomi" |
| „Google ist besser als alles" | „Google ist im Spitzenfeld, aber statistisch nicht besser als die lineare Baseline" |
| „Tut mir leid, dass kein klares Bild rauskommt" | „Das gemischte Bild ist ein wissenschaftlich gehaltvolles Ergebnis: zwei klare Gruppen statistisch trennbar, plus Hardware-Effekt" |

---

## 10. Wenn der Prüfer technisch in die Tiefe geht

**„Was macht der Concordance-Index genau?"**
> *„Anteil der korrekt geordneten Paare: für alle Test-Punkte i,j mit y_i < y_j wird gezählt, ob auch y_pred_i < y_pred_j gilt. Wertebereich [0,1], 0.5 = Münzwurf. Robust gegen Bias und Skalierung — wichtig bei zensierten Targets, weil die absolute Höhe nicht zählt, nur die Reihenfolge."*

**„Warum schwankt die TinyML-Performance so stark zwischen den Geräten?"**
> *„Drei plausible Erklärungen, ich kann keine davon mit den vorhandenen Daten beweisen: erstens unterschiedliche Sensorgenauigkeit (Pixel-Geräte haben oft präzisere Hardware-Schätzer); zweitens unterschiedliche Datenmenge pro Gerät (Pixel 7 Pro hat 1825 Test-Samples, Pixel 8 Pro nur 98); drittens unterschiedliche Nutzungsprofile pro Person (jedes Gerät = anderer User). Eine kontrollierte Studie mit identischer Nutzung auf verschiedenen Geräten würde das auflösen."*

**„Linear ist genauso gut wie Google — gibt es eine Erklärung?"**
> *„Die linearen Baseline-Berechnung `b / dot b` aus den letzten N Punkten greift exakt das Signal ab, das auch die Google-API primär nutzt — die aktuelle Drain-Rate. Googles ML-Modell hat zwar zusätzlichen Zugriff auf hardware-interne Metriken, aber die zusätzliche Information scheint für den Zeithorizont 'Stunden bis 0%' kaum Mehrwert zu bringen. Für längere Horizonte (Tage) oder Vorhersagen unter Lastwechseln würde das Bild vermutlich anders aussehen — aber das ist mit unserem censored Test-Set nicht messbar."*

**„Was sagt Mutual Information aus?"**
> *„Pearson misst nur lineare Zusammenhänge. Mutual Information misst beliebige Abhängigkeit, auch nicht-monotone. In meinen Daten zeigt sich z.B. bei `temperature` Pearson r ≈ 0.02, aber MI ≈ 1.24 nat — Temperatur trägt Information, aber nicht als linearer Trend, sondern komplexer."*

---

## 11. Mentaler Anker

Du hast eine **Multi-Device-Studie** mit:

- 66.001 Messungen über 4 Geräte
- 6 Methoden im sauberen Vergleich, mit Konfidenzintervallen und Signifikanz-Tests
- Methodischem Eigenbeitrag (Leakage-Quantifizierung)
- Per-Device-Befund mit klarer praktischer Implikation
- Reproduzierbarer Pipeline (ein Befehl, jede Zahl im Paper)
- Vier konkreten Anwendungsszenarien für App-Level-TinyML jenseits des Negativbefunds

Das ist eine **vollwertige empirische Studie** und keine reine Negativ-Beobachtung mehr. Geh entspannt rein.

---

## 12. Vor der Verteidigung mitnehmen

- [ ] `paper/main.pdf` ausgedruckt
- [ ] `reports/REPORT.md` (oder Tablet)
- [ ] Diese Datei
- [ ] `reports/main_table.csv` für Zahlen-Lookups
- [ ] `reports/per_device_analysis.json` (auf dem Phone als Notfall-Lookup)
- [ ] Optional: `reports/figures/cumulative_error.png` und `data_distribution.png` als Bilder

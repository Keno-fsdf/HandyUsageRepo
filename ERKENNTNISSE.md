# TinyML Battery Prediction — Erkenntnisse & Zusammenfassung

## 1. Projektübersicht

### Was wurde gebaut
- **Android-App** (Kotlin): Sammelt alle 30 Sekunden 10 Features vom Smartphone
- **ML-Pipeline** (Python/TensorFlow): Training eines Conv1D-Modells auf realen Gerätedaten
- **TFLite-Modell** (14.6 KB, INT8-quantisiert): On-Device-Inference direkt in der App
- **Live-Vorhersage**: App zeigt "Noch Xh Ymin" basierend auf dem eigenen Modell

### Technischer Stack
- **Gerät**: Xiaomi 2107113SG, Android 12+
- **Modellarchitektur**: Conv1D → Conv1D → GlobalAveragePooling → Dense → Dense
- **Parameter**: 5.697 (ca. 14.6 KB als INT8 TFLite)
- **Input**: Sliding Window von 10 Zeitschritten × 10 Features
- **Output**: Verbleibende Akkulaufzeit in Stunden

### Die 10 Features
1. `battery_level` (0-100%)
2. `screen_on` (0/1)
3. `brightness` (0-100%)
4. `active_app_category` (0=idle, 1=social, 2=video, 3=gaming, 4=browser, 5=productivity)
5. `wifi_on` (0/1)
6. `mobile_data_on` (0/1)
7. `charging` (0/1)
8. `cpu_usage` (0-100%, basierend auf CPU-Frequenz)
9. `temperature` (°C, Batterietemperatur)
10. `hotspot_on` (0/1)

---

## 2. Trainingsergebnisse

### Datengrundlage
- 11.026 Datenpunkte über ca. 10 Tage
- 9 Sessions
- **Problem**: 74.5% der Daten bei Batterie 100% (häufig am Ladekabel)
- Nur 3.3% der Daten unter 50% Batterie
- 135 Entladesegmente erkannt, davon viele ohne echten Drain (100%→100%)
- 2.627 verwendbare Sequenzen

### Modell-Performance (Test-Daten)
| Metrik | Wert |
|--------|------|
| MAE | 4.20 Stunden |
| RMSE | 6.82 Stunden |
| R² | 0.838 |
| Accuracy ±1h | 19.5% |
| Accuracy ±2h | 41.3% |

### Vergleich mit Android-Schätzung (auf 244 gemeinsamen Datenpunkten)
| Metrik | Eigenes Modell | Android API |
|--------|---------------|-------------|
| MAE | 2.67h | 7.15h |
| Accuracy ±1h | 24.2% | 9.8% |

**⚠️ ACHTUNG — ARTEFAKT**: Dieser Vergleich ist **irreführend** (siehe Abschnitt 8). Unser Modell wurde auf unsere selbst-berechneten Targets trainiert und ist natürlich besser darin, diese zu treffen. Die Google-API versucht die *echte* verbleibende Laufzeit vorherzusagen, nicht unsere Approximation. **Dieser Vergleich beweist NICHT, dass unser Modell besser ist als Googles API.** In der subjektiven Live-Nutzung schneidet die Google-API deutlich besser ab.

---

## 3. Die Google Battery Discharge Prediction API

### Was ist das?
- **API**: `PowerManager.getBatteryDischargePrediction()` — verfügbar seit Android 12 (Oktober 2021)
- **Lokale Inference**: Läuft komplett auf dem Gerät, kein Internet nötig
- **Internes Modell**: Teil des "Adaptive Battery" Systems, intern "TURBO" / "Battery Prediction Framework"
- Der Quellcode des Modells ist nicht öffentlich — nur die API-Schnittstelle

### Warum ist Googles Modell besser?
1. **Datenzugang**: Google hat als Systemprozess (Root) Zugriff auf ~50+ interne Metriken:
   - Exakte Stromstärke (mA) und Spannung (mV)
   - Batterie-Impedanz und Ladezyklen-Zähler
   - Wakelocks und CPU-Temperaturen pro Kern
   - Battery Health Zustand (Kapazitätsverlust)
   - PowerStats HAL — exakter Stromverbrauch jeder App
   - Kernel-Level Fuel Gauge (misst tatsächliche Coulombs)
2. **Trainingsumfang**: Trainiert auf Daten von Millionen von Geräten über Jahre
3. **Modellgröße**: Keine TinyML-Beschränkung nötig, Smartphone hat genug Ressourcen (8 GB RAM)
4. **Historische Daten**: Zugriff auf Wochen/Monate an historischen Daten

### Was unsere App **nicht** lesen kann (aber Google schon)
- Exakte mA/mV Werte (nur über Root oder versteckte APIs)
- Battery Health / Degradation
- App-spezifischer Stromverbrauch
- Kernel-Level Fuel Gauge Daten
- Precise Wakelocks und Doze-State

### Unsere App: 10 Features mit eingeschränktem Zugang
Wir lesen als normale App nur öffentlich zugängliche Daten — das ist ein fundamentaler Nachteil gegenüber einem Systemprozess.

---

## 4. Batterie-Anzeige in den Einstellungen vs. Google API

Es gibt **zwei verschiedene Systeme** auf Android:

### Settings-Anzeige ("Noch ca. X Stunden" in Einstellungen → Batterie)
- **Simpel**: Nimmt den durchschnittlichen Verbrauch der letzten Tage und rechnet linear hoch
- **Beispiel**: "Du hast im Schnitt 10%/Stunde verbraucht, du hast 80%, also noch 8 Stunden"
- **Ignoriert** was gerade aktiv genutzt wird
- Wird vom **Hersteller** (Xiaomi/MIUI) angepasst — oft schlechter als Stock-Android
- **Legacy**: Existiert seit Android 5 (2014), wurde bei vielen Herstellern nie aktualisiert

### Google ML-API (`getBatteryDischargePrediction()`)
- **ML-basiert**: Berücksichtigt aktuelle Nutzung, Sensordaten, Muster
- **Deutlich genauer** als die Settings-Anzeige
- **Erst seit Android 12** (2021) verfügbar
- **Wird NICHT in den Settings angezeigt** bei den meisten Herstellern (Xiaomi, Samsung, etc.)
- **Nur auf Pixel-Handys** wird der ML-Wert direkt in den Einstellungen genutzt

### Warum zeigen Hersteller nicht die bessere API an?
- MIUI/OneUI etc. haben ihre eigene Settings-App seit Jahren
- Die Integration der neuen API erfordert aktive Code-Änderungen
- Wenig Business-Incentive — User beschweren sich selten über ungenaue Akkuanzeigen
- Legacy-Code der nie aktualisiert wurde

### Relevanz für unser Projekt
Unsere App macht den ML-Wert von Google **erstmals sichtbar** für Nutzer auf Nicht-Pixel-Geräten. Gleichzeitig bieten wir einen eigenen Vergleichswert aus dem TinyML-Modell.

---

## 5. TinyML auf Smartphones — Einordnung

### Ist TinyML auf Smartphones sinnvoll?
**Grundsätzlich nein** — TinyML ist für Mikrocontroller mit wenigen KB RAM gedacht (Arduino, ESP32, etc.). Ein Smartphone ist ein vollwertiger Computer mit GB an RAM. Es gibt keinen technischen Grund, ein Modell auf 14 KB zu beschränken.

### Wo TinyML bei Battery Prediction Sinn machen würde
- **Auf einem Wearable** (Smartwatch mit limitiertem Prozessor)
- **Auf einem IoT-Gerät** (Sensor-Node mit ESP32)
- **Auf Smartphones ohne Android 12** (pre-2021 Geräte, wo die Google-API nicht existiert)
- **Auf Plattformen ohne native Prediction-API** (z.B. ältere Custom-ROMs)

### Wo es keinen Sinn macht
- Auf modernen Android 12+ Geräten, wo `getBatteryDischargePrediction()` verfügbar ist
- Der System-Level-Zugang von Google ist ein uneinholbarer Vorteil

---

## 6. Wissenschaftliche Einordnung

### Mögliche Forschungsfrage
"Kann ein personalisiertes TinyML-Modell mit eingeschränktem Sensorzugang die Akkulaufzeit eines Smartphones vorhersagen, und wie schneidet es gegen die native Android-ML-API ab?"

### Realistische Paper-Struktur (was wir tatsächlich belegen können)

**Typ**: Erfahrungsbericht / Empirische Systemstudie (kein Benchmarking-Paper)

**Forschungsfrage**: "Ist ein personalisiertes TinyML-Modell auf App-Ebene ein praktikabler Ansatz zur Akkulaufzeit-Vorhersage auf Android-Smartphones?"

**Antwort**: Technisch ja, praktisch nein — und zwar aus Gründen die *vor dem Experiment* nicht offensichtlich waren.

1. **Einleitung**: Akkulaufzeit-Vorhersage als Problem, TinyML als leichtgewichtiger Ansatz, Motivation: geht das auch ohne System-Level-Zugang?
2. **Related Work**: Google's native API, bestehende Battery-Prediction-Papers, TinyML-Einsatzgebiete
3. **Methodik**:
   - Datensammlung-App (10 Features, 30s Intervall)
   - Feature Engineering (Sliding Window, StandardScaler)
   - Modellarchitektur (Conv1D, INT8-Quantisierung, 14.6 KB)
   - On-Device Deployment (TFLite auf Android)
4. **Ergebnisse**:
   - Modell-interne Metriken (MAE 4.20h, R²=0.838) — zeigt dass das Modell grundsätzlich *funktioniert*
   - **Kein belastbarer Vergleich** mit anderen Systemen (ehrlich erklären warum, siehe Abschnitt 8)
   - Qualitative Live-Beobachtung: Google-API erscheint genauer
5. **Analyse — Warum der Ansatz fundamental limitiert ist**:
   - **Informationsasymmetrie**: 10 öffentliche Features vs. 50+ System-Features bei Google
   - **Kein Zugang zu Hardware-Daten**: Strom (mA), Spannung (mV), Fuel Gauge, Battery Health
   - **Android 12+ hat das Problem bereits gelöst**: `getBatteryDischargePrediction()` existiert seit 2021
   - **TinyML ist die falsche Abstraktion**: Smartphones haben GB an RAM, kein Bedarf für 14-KB-Modelle
6. **Fazit**:
   - TinyML-basierte Akkulaufzeit-Vorhersage auf App-Ebene ist **technisch machbar, aber praktisch überflüssig**
   - Der limitierende Faktor ist **nicht die Modellarchitektur oder -größe**, sondern der **Datenzugang**
   - Auf Android 12+ Geräten existiert bereits eine native Lösung mit privilegiertem Systemzugang
   - **Potenzieller Nutzen**: Pre-Android-12-Geräte, andere Plattformen ohne native API, Forschungskontext

### Warum das trotzdem ein valides Paper ist
- **Man wusste das vorher nicht**: Dass eine Drittanbieter-App fundamental nicht mithalten kann, ist eine Erkenntnis die erst durch das Experiment klar wurde
- **Vollständige Pipeline gebaut und dokumentiert**: Reproduzierbar, End-to-End
- **Negative Ergebnisse sind unterrepräsentiert**: In der Literatur werden hauptsächlich positive Ergebnisse publiziert — ein ehrlicher Bericht "das funktioniert nicht und hier ist warum" hat Wert
- **Konkrete technische Begründung**: Nicht einfach "hat nicht geklappt" sondern eine klare Analyse der Ursache (Informationsasymmetrie, API-Beschränkungen)

### Was man NICHT behaupten darf
- ❌ "Unser Modell ist besser als die Android-API" (Artefakt, siehe Abschnitt 8)
- ❌ "Unser Modell ist besser als naive lineare Extrapolation" (nicht getestet)
- ❌ "TinyML funktioniert nicht für Battery Prediction" (es funktioniert — nur nicht besser als was es schon gibt)

---

## 7. Technische Details

### Android-App Architektur
- **DataCollectorService**: Foreground Service, `START_STICKY`, überlebt App-Schließen
- **BatteryPredictor**: TFLite Interpreter, Sliding Window Buffer, StandardScaler-Normalisierung
- **BatteryDataLogger**: CSV-Schreiber mit Session-IDs
- **MainActivity**: UI mit Live-Prediction-Anzeige via BroadcastReceiver
- **BootReceiver**: Auto-Restart nach Geräte-Neustart
- **onTaskRemoved()**: Auto-Restart nach Wegwischen der App (AlarmManager)

### Modelldetails
- **Architektur**: Input(10,10) → Conv1D(32,k=3) → Conv1D(32,k=3) → GAP → Dense(32) → Dropout(0.2) → Dense(16) → Dense(1)
- **Training**: 150 Epochs, LR=5e-4 mit ReduceLROnPlateau, Patience=20
- **Quantisierung**: INT8 mit Float32 I/O (wichtig für TFLite-Kompatibilität)
- **StandardScaler**: Mean und Scale hardcoded in der Android-App

### Scaler-Werte (aus dem Training)
```
MEAN:  [84.694, 0.810, 9.339, 1.779, 0.0, 1.0, 0.0, 53.982, 31.925, 0.0]
SCALE: [17.481, 0.392, 11.558, 1.254, 1.0, 1.0, 1.0, 13.401, 4.773, 1.0]
```

### Datei-Übersicht
```
handyUsage/
├── data/real_battery_data.csv          # 11.026 Datenpunkte
├── train_real_data.py                  # Training-Pipeline für echte Daten
├── generate_data.py                    # Synthetische Daten (initial)
├── train_model.py                      # Training für synthetische Daten
├── convert_tflite.py                   # TFLite-Konvertierung
├── run_pipeline.py                     # Pipeline-Runner
├── model/
│   ├── battery_model_real.keras        # Trainiertes Keras-Modell
│   ├── battery_model_real.tflite       # INT8 TFLite (14.2 KB, INT8 I/O)
│   ├── battery_model_real_float.tflite # INT8 TFLite mit Float I/O (14.6 KB)
│   ├── scaler_real.joblib              # StandardScaler
│   └── metrics_real.json               # Evaluationsmetriken
├── plots/
│   └── real_training_results.png       # Training-Visualisierung
└── android/                            # Komplette Android-App
    └── app/src/main/
        ├── assets/battery_model.tflite # Modell in der App
        ├── java/.../
        │   ├── MainActivity.kt
        │   ├── DataCollectorService.kt
        │   ├── BatteryPredictor.kt     # TFLite Inference
        │   ├── BatteryDataPoint.kt
        │   ├── BatteryDataLogger.kt
        │   └── BootReceiver.kt
        └── res/layout/activity_main.xml
```

---

## 8. Warum der Trainings-Vergleich ein Artefakt ist

### Das Problem
Der Vergleich "Eigenes Modell MAE 2.67h vs Android API MAE 7.15h" ist **kein fairer Vergleich**, sondern ein statistisches Artefakt:

1. **Unser Target ist selbst-berechnet**: Wir berechnen die "Ground Truth" (verbleibende Akkulaufzeit) aus der beobachteten Drain-Rate im CSV. Das ist eine Extrapolation, kein gemessener Wert.
2. **Unser Modell wurde auf dieses Target trainiert**: Natürlich kann unser Modell die eigenen berechneten Targets besser vorhersagen — es wurde genau darauf optimiert.
3. **Die Google-API hat ein anderes Ziel**: Sie versucht die *echte* verbleibende Laufzeit vorherzusagen, nicht unsere berechnete Approximation. Wenn sie von unserem Target abweicht, kann das daran liegen, dass sie *besser* ist als unser Target.
4. **Zirkelschluss**: "Unser Modell ist besser als Google" → gemessen an einem Target, das unser Modell gelernt hat → das beweist gar nichts.

### Was man stattdessen bräuchte
Ein fairer Vergleich würde erfordern:
- **Echte Ground Truth**: Das Handy tatsächlich von X% bis 0% laufen lassen und die reale Zeit messen
- **Beide Modelle zum gleichen Zeitpunkt befragen**: "Wie lange noch?" → 3h später nachschauen wer Recht hatte
- **Mehrere vollständige Entladezyklen**: Nicht nur Segmente aus dem Alltag

### Konsequenz für das Paper
Man kann die Trainings-Metriken (MAE, R², etc.) als **Modell-interne Evaluation** berichten, aber man darf **nicht behaupten**, dass das eigene Modell besser ist als die Google-API. Der einzig ehrliche Vergleich wäre ein prospektiver Live-Test.

---

## 9. Kann man die Settings-Batterie-Anzeige loggen?

### Kurze Antwort: Nicht direkt, aber man kann sie nachbauen

Die "Noch X Stunden"-Anzeige in den Einstellungen (besonders bei MIUI/Xiaomi) ist **keine öffentliche API**. Es gibt kein `getSettingsBatteryEstimate()`. Aber:

### Was wir lesen KÖNNEN (BatteryManager API, seit Android 5/API 21):
- `BATTERY_PROPERTY_CURRENT_NOW` — Momentanstrom in Mikroampere (µA)
- `BATTERY_PROPERTY_CURRENT_AVERAGE` — Durchschnittsstrom in µA
- `BATTERY_PROPERTY_CHARGE_COUNTER` — Restkapazität in Mikroamperestunden (µAh)

### Daraus selbst die "naive lineare Baseline" berechnen:
```
verbleibende_stunden = charge_counter_µAh / abs(current_average_µA)
```

Das ist **im Wesentlichen die gleiche Berechnung** die die Settings-App macht (linearer Durchschnitt). Wir können diese "Naive Linear Baseline" in unserer App loggen und als dritten Vergleichswert mitführen.

### Einschränkungen:
- **Geräteabhängig**: Manche Hersteller (besonders Xiaomi) liefern 0 oder Long.MIN_VALUE zurück
- **Kein 1:1 Match**: Die MIUI-Settings-Anzeige kann noch weitere interne Heuristiken verwenden
- **Aber konzeptuell identisch**: Beide basieren auf linearer Extrapolation vom Durchschnittsverbrauch

### Was das fürs Paper bedeutet:
**Stand jetzt haben wir die naive lineare Baseline NICHT implementiert und NICHT geloggt.** Wir können also auch nicht behaupten, dass unser Modell besser ist als die naive Extrapolation — das ist genauso unbewiesen wie der Vergleich mit Googles API.

Um einen echten 3-Wege-Vergleich zu machen, müssten wir:
1. Die naive lineare Baseline in die App einbauen und mitloggen
2. Die eigene Modell-Vorhersage ebenfalls in die CSV loggen (aktuell wird sie nur in der UI angezeigt)
3. Mehrere Tage neue Daten sammeln
4. Retrospektiv auswerten: "Was hat jedes System um 14:00 bei 75% vorhergesagt, und wann war der Akku tatsächlich bei 0%?"

| System | Methode | Datenquelle | Status |
|--------|---------|-------------|--------|
| **Naive Linear Baseline** | `charge / avg_current` | BatteryManager API | ❌ Nicht implementiert |
| **Eigenes TinyML-Modell** | Conv1D auf 10 Features | Öffentliche Sensor-APIs | ⚠️ Nur in UI, nicht in CSV geloggt |
| **Google ML-API** | `getBatteryDischargePrediction()` | System-internes ML-Modell | ✅ Geloggt als `system_estimate_min` |

**Ohne diesen Vergleich ist die einzig belegbare Aussage des Papers:**
- Wir haben ein funktionierendes End-to-End TinyML-System gebaut (Datensammlung → Training → On-Device-Inference)
- Das Modell erreicht R²=0.838 auf den eigenen Testdaten (interne Evaluation)
- Ein System-Level-ML-Modell (Google API) ist subjektiv besser, weil es privilegierten Datenzugang hat
- **Kein quantitativer Vergleich ist belastbar** — weder gegen Google API noch gegen naive Baseline

---

## 10. Bekannte Limitierungen

1. **Datenverteilung**: 74.5% der Daten bei 100% Batterie — Modell schwach im mittleren/unteren Bereich
2. **Nur 10 Tage Daten**: Zu wenig für robustes Modell
3. **Eingeschränkter Sensorzugang**: Nur 10 Features vs. 50+ bei Google
4. **WiFi immer 0, Mobile immer 1**: Keine Varianz in diesen Features
5. **Xiaomi-spezifisch**: App-Kategorie-Zuordnung und CPU-Frequenz-Zugang variieren je nach Gerät
6. **Drain-Rate-Extrapolation**: Target-Variable wird aus beobachteter Drain-Rate hochgerechnet, nicht gemessen
7. **Trainings-Vergleich ist Artefakt**: Der MAE 2.67h vs 7.15h Vergleich beweist nicht, dass unser Modell besser ist als Googles API — unser Modell ist nur besser darin, unsere eigenen berechneten Targets zu treffen (siehe Abschnitt 8)
8. **Kein prospektiver Live-Vergleich**: Es fehlt ein unabhängiger Test mit echter Ground Truth (Handy bis 0% laufen lassen)

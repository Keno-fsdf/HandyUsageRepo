# Vortragsskript — Paper-Präsentation

> **Vortragstermin:** 24.6. oder 1.7. — Slot: 15 Min (10 Min Vortrag + 2–3 Min Fragen)
> **15 Folien** — Ziel-Tempo ~40 Sek pro Folie

Das hier ist ein Sprech-Gerüst, nicht ein Skript zum Vorlesen. Üben → frei reden, das hier nur als Anker.

---

## Folie 1 — Titel (10 Sek)

*Folie zeigen, kurz stehen lassen.*

> *"Guten Tag. Mein Name ist Keno Schürger. Ich präsentiere heute meine Arbeit App-Level TinyML für Akkulaufzeit-Vorhersage auf Android — ein Multi-Device-Vergleich von sechs Methoden."*

→ Schnell weiter zur nächsten Folie.

---

## Folie 2 — Motivation (60 Sek)

*Reihenfolge auf Wunsch von Prof. John: erst motivieren, dann die Forschungsfrage.*

> *"Smartphone-Akkuanzeigen rechnen klassisch einen statischen Durchschnitt linear hoch — sie ignorieren, welche App gerade läuft, ob das Display hell ist, ob Mobilfunk schwach ist. Daher: 30 % Akku und 'noch 4 Stunden' steht plötzlich nach einem YouTube-Video bei '1 Stunde'.*"

→ Auf die rechte Spalte:

> *"Erst seit Android 12, also Oktober 2021, hat Google ein eigenes ML-Modell ins System eingebaut. Das läuft aber im Systemprozess mit privilegiertem Hardware-Zugriff — eine normale App kann das nicht so machen."*

→ Auf die orange Highlight-Box:

> *"Im Kern fragen wir also: Wie gut schneidet ein TinyML-Modell auf öffentlich verfügbaren Sensoren gegenüber etablierten Vorhersage-Methoden ab?"*

---

## Folie 3 — Forschungsfrage (40 Sek)

*Quote-Box laut vorlesen, langsam.*

> *"Daraus ergibt sich die Forschungsfrage: Wie gut kann TinyML die Akkulaufzeit auf Android vorhersagen im Vergleich zu exponentiellem Fitting und der nativen Google-API — bezogen auf Genauigkeit sowie Effizienz?"*

**Tonspur: warum das eine gute Forschungsfrage ist** (von Prof. John gewünscht):

> *"Die Frage ist deshalb lohnend, weil die System-API zwar seit 2021 ausgeliefert wird, ihre Genauigkeit aber nie unabhängig gegen App-Level-Alternativen auf echten Nutzungsdaten vermessen wurde — und die TinyML-Literatur das Smartphone als Zielplattform weitgehend auslässt. Diese doppelte Lücke schließt die Arbeit."*

Dann auf die drei Kacheln zeigen:

> *"Wir vergleichen also TinyML gegen fünf andere Methoden auf zwei Achsen — Genauigkeit, gemessen mit C-Index und MAE, und Effizienz, gemessen über Latenz und Modellgröße."*

---

## Folie 4 — Verwandte Arbeiten (45 Sek)

*Nicht jedes Werk einzeln durchgehen — nur die Highlights.*

> *"Vier relevante Vorarbeiten. Li et al. 2018 — die Smartphone-Battery-Standardreferenz mit 51 Nutzern über 21 Monate — hat den Concordance-Index als Standard-Metrik für diese Domäne eingeführt, weil Akku-Daten ein 'severe data missing problem' haben: Nutzer entladen selten auf 0 %.*"

→ Kurz auf die anderen:

> *"Flores-Martin 2024 ist der direkteste Methodik-Verwandter mit LSTM. MLPerf Tiny ist der Industriestandard-Benchmark für TinyML — wobei Smartphone-Anwendungen in der Literatur weitgehend fehlen. Und Albelali & Ahmed 2025 haben gezeigt, dass Random-Shuffle bei Zeitreihen-Splits Future-Information leckt — das ist methodisch relevant für meinen Ansatz."*

---

## Folie 5 — Datensammlung (45 Sek)

> *"Die Datenbasis: 66.001 Messungen über 45 Tage auf vier Geräten — eigener Xiaomi plus drei Pixel-Geräte bei Familienmitgliedern."*

→ Auf die Tabelle:

> *"Das Xiaomi war mit 38.000 Messungen der Schwerpunkt, die drei Pixel-Geräte tragen zusammen rund 28.000 Messungen bei."*

→ Auf die Features-Box rechts:

> *"Jede Messung erfasst zehn Features — Akkustand, Bildschirm, Helligkeit, App-Kategorie, Netzwerk-Zustand, CPU-Proxy, Temperatur. Alles aus öffentlich verfügbaren Android-APIs — ohne Root, ohne Sonderrechte."*

---

## Folie 6 — Sechs Methoden (60 Sek)

> *"Sechs Methoden im Vergleich, in drei Gruppen:*

→ Zeile 1 zeigen:

> *"Zwei ML-Modelle — TinyML Conv1D als Hauptmodell mit 14 KB INT8, und Random Forest als zweites Paradigma zur Validierung. Plus den Mean Predictor als Floor — wenn das eigene Modell nicht über diesen Floor kommt, hat es nichts gelernt.*"

→ Zeile 2:

> *"Zwei analytische Baselines — Linear-Berechnung aus der Drain-Rate und exponentielles Fitting pro Discharge-Segment. Plus die native Google-API als State of the Art."*

---

## Folie 7 — Segment-Level-Split (60 Sek)

> *"Methodisch zentraler Punkt: Wie teilt man Train und Test? Bei zufälliger Aufteilung sieht das Modell unbemerkt zukünftige Daten — Data Leakage."*

→ Auf die Tabelle zeigen:

> *"Auf den Single-Device-Daten wirkt der Test-MAE dadurch um den Faktor ~1,7 zu gut — 6,5 statt ehrlicher 11,1 Stunden."*

→ Zweite Zeile:

> *"Auf Multi-Device-Daten schrumpft die Verzerrung auf 1,24-fach. Die Datenvielfalt schwächt das Lecken ab — vergleichbar mit Albelali & Ahmed 2025 bei zeitreihen-typischer Cross-Validation."*

---

## Folie 8 — Ergebnis 1: Common Subset (90 Sek — **Kernfolie, Zeit nehmen**)

→ Auf die Erklär-Box oben zeigen:

> *"Kurz zur Metrik: C-Index ist der Anteil korrekt geordneter Vorhersage-Paare — 0,5 Münzwurf, 1,0 perfekt. Klammerwerte sind 95 %-Konfidenzintervalle. MAE in Stunden für die absolute Genauigkeit."*

→ Tabelle Zeile für Zeile:

> *"Mean-Predictor als Floor bei 0,500. TinyML erreicht 0,656, Random Forest 0,685 — beide klar über dem Floor. Die analytischen Baselines und Google liegen alle drei bei C-Index 0,77 — also deutlich besser als die ML-Modelle."*

→ Auf die grüne Take-away-Box:

> *"Beide ML-Modelle schlagen Mean signifikant. Linear, Exponential und Google bilden eine gemeinsame Spitzengruppe bei C circa 0,77."*

---

## Folie 9 — Statistische Signifikanz (60 Sek)

→ Auf die Erklär-Box oben:

> *"p < 0,05 heißt signifikant — der Unterschied ist nicht durch Zufall erklärbar. n.s. heißt nicht signifikant — die beiden Methoden sind statistisch ununterscheidbar."*

→ Tabelle:

> *"TinyML und Random Forest schlagen Mean signifikant. Aber jetzt der überraschende Befund: Linear gegen Google ergibt einen BH-korrigierten p-Wert von 0,11 — statistisch nicht unterscheidbar, Linear liegt numerisch sogar minimal vorn."*

→ Auf die rote Box:

> *"Die simple Linear-Berechnung aus dem BatteryManager ist auf Aggregat-Ebene praktisch identisch zu Googles System-ML. Der zusätzliche Hardware-Zugang zahlt sich erst bei sehr langen Restzeiten aus — ab etwa 30 Stunden zieht Google klar davon."*

---

## Folie 10 — Per-Device (75 Sek — **wichtigster praktischer Befund**)

> *"Wenn man dasselbe TinyML-Modell pro Gerät auswertet, kommt der praktisch relevanteste Befund."*

→ Auf das Chart:

> *"TinyML erreicht auf Pixel 7 Pro einen C-Index von 0,75 — auf dem Xiaomi nur 0,59. Eine Differenz von 0,16 in einer Metrik, die zwischen 0,5 und 0,85 läuft."*

→ Auf die Beobachtungs-Bullets:

> *"Die analytischen Baselines sind stabiler über die Geräte. Auf Pixel 9 Pro XL ist Linear sogar besser als Google."*

→ Auf die Confounder-Box:

> *"Wichtig zur Einordnung: Auf dem Xiaomi war der Akku zu 88 % der Zeit über 75 % geladen — Sensor-Qualität und mangelnder Entlade-Verlauf vermischen sich also als Erklärung für den schwachen Xiaomi-Wert."*

---

## Folie 11 — Effizienz (30 Sek)

*Schnell durch — die Zahlen sprechen für sich.*

> *"Auf der Effizienz-Achse hat TinyML klare Vorteile. 14,4 KB INT8-Modell, 3,3 Mikrosekunden Inferenz-Latenz — 7,6-fach kleiner und rund 12.000-fach schneller als das ursprüngliche Keras-Float32-Modell."*

→ Auf die grüne Take-away-Box:

> *"Die TinyML-Quantisierungs-Pipeline funktioniert wie beworben. Effizienz ist die klare Stärke von TinyML."*

---

## Folie 12 — Diskussion (60 Sek)

> *"Zwei Schlüssel-Befunde zusammen:"*

→ Linke Spalte:

> *"Erstens: ML lernt Signal — aber target-abhängig. Gegen das Trainings-Target erreicht TinyML C-Index 0,66 und Random Forest 0,68, beide signifikant über dem Floor. Gegen die tatsächlich gemessene Restzeit verschwindet dieser Vorsprung — dort ist TinyML nicht mehr vom Mean-Predictor unterscheidbar. Und in beiden Fällen bleiben die analytischen Baselines und Google vorn."*

→ Rechte Spalte:

> *"Zweitens: Google ist statistisch nicht von der Linear-Baseline unterscheidbar. Linear 0,770, Google 0,762, BH-korrigierter p-Wert 0,11. Der zusätzliche Hardware-Zugang zahlt sich erst bei sehr langen Restzeiten aus."*

---

## Folie 13 — Limitations (45 Sek)

*Schnell durchgehen, nur Headlines.*

> *"Drei wichtige Limitationen:*

> *Erstens: Akku-Daten sind 'right-censored' — wird im Alltag nie auf 0 % gefahren. Deshalb C-Index als Hauptmaß statt MAE.*

> *Zweitens: Training hat alle vier Geräte gesehen — wie das Modell auf einem komplett neuen Gerät funktionieren würde, ist offene Folgearbeit.*

> *Drittens: Auf Pixel 9 Pro XL fällt TinyML auf 0,57, während Random Forest auf denselben Daten 0,77 erreicht. Dafür habe ich im aktuellen Datensatz keine kausale Erklärung — offen für Folgearbeiten."*

---

## Folie 14 — Conclusion (60 Sek)

> *"Antwort auf die Forschungsfrage in drei Achsen:*

→ Genauigkeit-Box:

> *"Genauigkeit: TinyML schlägt Mean, bleibt aber hinter Linear, Exponential und Google bei C circa 0,77. Google ist statistisch nicht besser als Linear.*"

→ Effizienz-Box:

> *"Effizienz: TFLite-Quantisierung funktioniert wie beworben — 14,4 KB, 3,3 Mikrosekunden. Auf dieser Achse hat TinyML uneingeschränkt seinen Wert.*"

→ Hardware-&-Datenvielfalt-Box:

> *"Hardware und Datenvielfalt: TinyML schwankt von 0,75 auf Pixel 7 Pro bis 0,59 auf Xiaomi. Engpass nicht am Modell, sondern an Sensor-Qualität und fehlendem Entlade-Verlauf."*

→ Abschluss:

> *"Damit zeigt sich App-Level-TinyML auf öffentlichen Android-Sensoren als methodisch ehrlicher Negativbefund auf der Genauigkeits-Achse — bei klarer Stärke auf der Effizienz-Achse."*

---

## Folie 15 — Vielen Dank (5 Sek)

> *"Vielen Dank für Ihre Aufmerksamkeit. Ich freue mich auf Ihre Fragen."*

---

# Q&A — Vorbereitete Antworten

## "Warum hat TinyML nicht gewonnen?"

> *"Linear-Baseline nutzt direkt aus dem BatteryManager die aktuelle Drain-Rate — das eine Signal, das die Frage 'Stunden bis 0 %' wirklich beantwortet. TinyML muss aus zehn schwach korrelierten Features dieses Signal erst rekonstruieren. Mit Zugriff auf den Kernel-Fuel-Gauge wäre TinyML vermutlich auf Augenhöhe — aber Apps haben diesen Zugriff nicht. Das ist eine messbare Aussage über die Limits von App-Level-TinyML."*

## "Warum ist Google nicht besser als Linear?"

> *"Auf der gemeinsamen Schnittmenge von 2.883 Test-Punkten ist der BH-korrigierte p-Wert (paired Bootstrap auf Delta-C) bei 0,11 — die zwei sind statistisch ununterscheidbar, Linear liegt numerisch sogar minimal vorn. Beide nutzen intern die aktuelle Drain-Rate — Googles ML-Anteil bringt für genau diese Frage auf typischen Horizonten keinen Mehrwert. Auf Pixel 9 Pro XL ist Linear sogar deutlich besser als Google."*

## "Warum war TinyML auf Pixel 9 Pro XL so schlecht?"

> *"Offene Beobachtung. TinyML erreicht dort 0,57, Random Forest auf denselben Daten 0,77. Drei Hypothesen: erstens unterschiedlicher Sensor-Stack der neuesten Pixel-Generation, zweitens schlechter passender StandardScaler, drittens ein generelles Distribution-Shift-Phänomen. Ich kann keine davon mit den aktuellen Daten beweisen — bewusst offen gelassen statt eine erfundene Erklärung."*

## "Was hätten Sie anders gemacht?"

> *"Drei Sachen: Erstens von Anfang an Segment-Level-Split statt Random-Shuffle — die Random-Shuffle-Variante wies den Test-MAE um Faktor ~1,7 zu optimistisch aus (6,5 statt 11,1 Stunden), ein Leakage-Artefakt. Zweitens hätte ich pro Geräteklasse trainiert statt ein gemeinsames Modell — der Hardware-Effekt ist groß genug, dass das Sinn ergeben würde. Drittens kontrollierte Vollentlade-Zyklen mit einem Zweitgerät zur Ground-Truth-Validierung."*

## "Generalisiert das auf neue Geräte?"

> *"Offen gelassene Frage. Mein Train/Test-Split ist segment-level über alle vier Geräte hinweg — das Modell hat alle vier Geräte im Training gesehen. Eine Leave-One-Device-Out-Studie wäre der saubere Test für Cross-Device-Generalisierung. Der gefundene Hardware-Effekt deutet aber darauf hin, dass die Generalisierung problematisch wäre."*

## "Warum nutzt eine App TinyML, wenn Linear gleich gut ist?"

> *"Linear ist eine fixe Formel — TinyML ist anpassbar. Das mitgelieferte Modell kann mit den eigenen gesammelten Daten nachtrainiert werden. Außerdem zeigt die App alle drei Methoden live im Vergleich — der Nutzer sieht selbst, welche auf seinem Gerät vorn liegt. Das ist Transparenz, die keine Standard-Battery-Anzeige liefert."*

## "Was ist Concordance-Index überhaupt?"

> *"Anteil korrekt geordneter Paare. Für alle Test-Punkte i, j mit wahrer Restzeit y_i kleiner als y_j wird gezählt, ob auch die Vorhersage y_pred_i kleiner als y_pred_j ist. Wertebereich 0 bis 1, 0,5 ist Münzwurf. Originalquelle Harrell 1982 aus der Survival-Analysis — robust gegen Bias und Skalierung, wichtig bei zensierten Daten."*

---

# Tipps fürs Üben

1. **Zeitmanagement**: Stoppuhr nutzen. Folien 8 und 10 sind die längsten, hier nicht hetzen.
2. **Forschungsfrage** auf Folie 3 langsam vorlesen — der ganze Vortrag baut darauf auf. Davor (Folie 2) die Motivation, danach kurz begründen, warum die Frage lohnend ist.
3. **Frei sprechen, nicht ablesen.** Dieses Skript ist Anker, nicht Manuskript.
4. **Auf die Folie zeigen** wenn du Zahlen erwähnst — hilft dem Publikum, mitzukommen.
5. **Bei "überraschender Befund" (Folie 9 + 12 Google ≈ Linear) eine Pause machen** — das ist der spannendste Moment des Vortrags.
6. **Fragen aktiv einladen** am Ende: *"Ich freue mich auf Ihre Fragen"* — keine zaghafte Pause.

---

# Mentaler Anker

Du hast eine **Multi-Device-Studie** mit 66.001 Messungen, 6 Methoden, Konfidenzintervallen, Signifikanztests und einem **methodisch ehrlichen Negativbefund**. Das ist eine vollwertige empirische Studie — du brauchst nichts schönzureden und nichts zu verstecken. Geh entspannt rein.

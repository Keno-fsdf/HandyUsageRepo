// Verteidigungs-Präsentation für das Paper:
// "App-Level TinyML for Smartphone Battery-Life Prediction"
// Output: Paper_Verteidigung.pptx
//
// Aufruf: node build_pptx.js

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "Keno Schürger";
pres.title = "TinyML für Akkulaufzeit-Vorhersage auf Android - Verteidigung";

// ============================================================
// Farbpalette
// ============================================================
const COL = {
  primary: "0F3460",       // deep navy - Titel, Akzente
  secondary: "16213E",     // darker navy
  bg: "FFFFFF",            // white
  bgDark: "0F1B2D",        // very dark navy (Title/Conclusion)
  text: "1A1A1A",
  muted: "64748B",
  border: "E2E8F0",
  // Methode-Farben (konsistent mit Plots)
  tinyml: "2196F3",        // blue
  rf: "9C27B0",            // purple
  mean: "9E9E9E",          // gray
  linear: "455A64",        // slate
  exp: "4CAF50",           // green
  google: "FF9800",        // orange
  // Highlights
  good: "27AE60",
  bad: "E94560",
};

// ============================================================
// Helpers
// ============================================================

function addPageNumber(slide, n, total) {
  slide.addText(`${n} / ${total}`, {
    x: 9.0, y: 5.3, w: 0.9, h: 0.25,
    fontSize: 9, color: COL.muted, align: "right", fontFace: "Calibri",
  });
}

function addFooter(slide) {
  slide.addText("K. Schürger - TinyML für Akkulaufzeit-Vorhersage", {
    x: 0.5, y: 5.3, w: 7, h: 0.25,
    fontSize: 9, color: COL.muted, fontFace: "Calibri",
  });
}

function slideTitle(slide, title) {
  slide.addText(title, {
    x: 0.5, y: 0.30, w: 9, h: 0.65,
    fontSize: 28, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });
}

const TOTAL = 15;

// ============================================================
// SLIDE 1 - Titelseite (dunkler Hintergrund)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  s.addText("App-Level TinyML für", {
    x: 0.6, y: 1.5, w: 8.8, h: 0.7,
    fontSize: 36, bold: true, color: "FFFFFF", fontFace: "Calibri", align: "left",
  });
  s.addText("Akkulaufzeit-Vorhersage auf Android", {
    x: 0.6, y: 2.2, w: 8.8, h: 0.7,
    fontSize: 36, bold: true, color: "FFFFFF", fontFace: "Calibri", align: "left",
  });

  // Akzent-Linie
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 3.05, w: 1.4, h: 0.06, fill: { color: COL.bad }, line: { type: "none" },
  });

  s.addText("Multi-Device-Vergleich von sechs Methoden", {
    x: 0.6, y: 3.2, w: 8.8, h: 0.45,
    fontSize: 16, italic: true, color: "CADCFC", fontFace: "Calibri",
  });

  s.addText([
    { text: "Keno Schürger", options: { bold: true, breakLine: true } },
    { text: "Matrikelnr.: 5023033", options: { color: "9CB4DE", breakLine: true } },
    { text: "Technische Hochschule Würzburg-Schweinfurt (THWS)", options: { color: "9CB4DE", breakLine: true } },
    { text: "Vertiefungsseminar - Sommersemester 2026", options: { color: "9CB4DE" } },
  ], {
    x: 0.6, y: 4.05, w: 8.8, h: 1.25,
    fontSize: 14, color: "FFFFFF", fontFace: "Calibri",
  });

  // Seitenzahl auch auf der Titelfolie (heller Schrift, weil dunkler Hintergrund)
  s.addText("1 / " + TOTAL, {
    x: 9.0, y: 5.3, w: 0.9, h: 0.25,
    fontSize: 9, color: "9CB4DE", align: "right", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 2 - Forschungsfrage (der Dreisatz)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Forschungsfrage");

  // Quote-Box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 0.08, h: 2.0, fill: { color: COL.primary }, line: { type: "none" },
  });
  s.addText('"Wie gut kann TinyML die Akkulaufzeit auf Android vorhersagen im Vergleich zu exponentiellem Fitting und der nativen Google-API, bezogen auf Genauigkeit sowie Effizienz?"', {
    x: 0.85, y: 1.3, w: 8.6, h: 2.0,
    fontSize: 20, italic: true, color: COL.secondary, fontFace: "Calibri",
    valign: "top",
  });

  // Drei-Achsen-Aufgliederung
  const xs = [0.5, 3.7, 6.9];
  const labels = [
    { head: "Methode", body: "TinyML\nvs.\n5 andere Methoden", col: COL.tinyml },
    { head: "Achse 1", body: "Genauigkeit\n(C-Index, MAE)", col: COL.exp },
    { head: "Achse 2", body: "Effizienz\n(Latenz, Modellgröße)", col: COL.google },
  ];
  labels.forEach((l, i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: xs[i], y: 3.7, w: 2.6, h: 1.3,
      fill: { color: "F5F7FA" }, line: { color: COL.border, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: xs[i], y: 3.7, w: 2.6, h: 0.08,
      fill: { color: l.col }, line: { type: "none" },
    });
    s.addText(l.head, {
      x: xs[i] + 0.1, y: 3.82, w: 2.4, h: 0.3,
      fontSize: 11, bold: true, color: l.col, fontFace: "Calibri", margin: 0,
    });
    s.addText(l.body, {
      x: xs[i] + 0.1, y: 4.15, w: 2.4, h: 0.8,
      fontSize: 14, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
    });
  });

  addFooter(s);
  addPageNumber(s, 2, TOTAL);
}

// ============================================================
// SLIDE 3 - Motivation
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Motivation: Akkuvorhersage auf Android");

  // Zwei-Spalten-Layout
  s.addText("Problem", {
    x: 0.5, y: 1.15, w: 4.3, h: 0.4,
    fontSize: 17, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "Klassisch: Settings-App rechnet linear hoch", options: { bullet: true, breakLine: true } },
    { text: "Ignoriert aktuelle Nutzung, App-Kontext", options: { bullet: true } },
  ], {
    x: 0.5, y: 1.55, w: 4.3, h: 1.8,
    fontSize: 13, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 6,
  });

  s.addText("Was sich seit Android 12 (2021) ändert", {
    x: 5.2, y: 1.15, w: 4.3, h: 0.4,
    fontSize: 17, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "PowerManager.getBatteryDischargePrediction()", options: { bullet: true, breakLine: true } },
    { text: "Erstes ML-Modell direkt im Android-System", options: { bullet: true, breakLine: true } },
    { text: "Läuft im Systemprozess - privilegierter Zugriff", options: { bullet: true } },
  ], {
    x: 5.2, y: 1.55, w: 4.3, h: 1.8,
    fontSize: 13, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 6,
  });

  // Highlight: plain-language framing (Erläuterung der Forschungsfrage)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.7, w: 9, h: 1.0,
    fill: { color: "FFF6E5" }, line: { color: COL.google, width: 1 },
  });
  s.addText("Worum es im Kern geht", {
    x: 0.7, y: 3.78, w: 8.6, h: 0.3,
    fontSize: 11, bold: true, color: COL.google, fontFace: "Calibri", margin: 0,
  });
  s.addText("Wie gut schneidet ein TinyML-Modell auf öffentlich verfügbaren Sensoren gegenüber etablierten Vorhersage-Methoden ab?", {
    x: 0.7, y: 4.05, w: 8.6, h: 0.6,
    fontSize: 14, italic: true, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
  });

  addFooter(s);
  addPageNumber(s, 3, TOTAL);
}

// ============================================================
// SLIDE 4 - Verwandte Arbeiten
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Verwandte Arbeiten");

  const works = [
    {
      head: "Li et al. (2018)",
      sub: "Smartphone Battery Prediction at Scale",
      body: "51 Nutzer, 21 Monate. Führt den Concordance-Index als Standard-Metrik ein, weil das 'severe data missing problem' (User entladen selten auf 0%) MAE unzuverlässig macht.",
      col: COL.primary,
    },
    {
      head: "Flores-Martin et al. (2024)",
      sub: "Deep Learning auf Android, DNN vs. LSTM",
      body: "Direkter Methodik-Verwandter. LSTM auf user-spezifischen App-, Sensor-, Screen-Time-Features.",
      col: COL.exp,
    },
    {
      head: "Banbury et al. (2021) - MLPerf Tiny",
      sub: "Industriestandard-Benchmark für TinyML",
      body: "Misst Accuracy, Latency, Energy gemeinsam. Smartphone-Anwendungen fehlen in der Literatur (siehe Heydari & Mahmoud 2025, Alajlan & Ibrahim 2022).",
      col: COL.google,
    },
    {
      head: "Albelali & Ahmed (2025)",
      sub: "Hidden Leaks in Time Series Forecasting",
      body: "Random-Shuffle-Splits über Sliding-Window-Sequenzen lecken Future-Information. RMSE Gain bis 20.5% bei 10-fold CV (LSTM).",
      col: COL.bad,
    },
  ];

  const colW = 4.4;
  works.forEach((w, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * (colW + 0.2);
    const y = 1.15 + row * 2.05;

    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: colW, h: 1.85,
      fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 0.08, h: 1.85, fill: { color: w.col }, line: { type: "none" },
    });
    s.addText(w.head, {
      x: x + 0.2, y: y + 0.10, w: colW - 0.3, h: 0.35,
      fontSize: 14, bold: true, color: w.col, fontFace: "Calibri", margin: 0,
    });
    s.addText(w.sub, {
      x: x + 0.2, y: y + 0.42, w: colW - 0.3, h: 0.3,
      fontSize: 11, italic: true, color: COL.muted, fontFace: "Calibri", margin: 0,
    });
    s.addText(w.body, {
      x: x + 0.2, y: y + 0.75, w: colW - 0.3, h: 1.0,
      fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
    });
  });

  addFooter(s);
  addPageNumber(s, 4, TOTAL);
}

// ============================================================
// SLIDE 5 - Datensammlung
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Datensammlung: 4 Geräte, 45 Tage");

  // Big stat row
  const stats = [
    { val: "66.001", lbl: "Messungen" },
    { val: "4", lbl: "Geräte" },
    { val: "45 Tage", lbl: "Zeitraum" },
    { val: "180", lbl: "Sessions" },
  ];
  stats.forEach((st, i) => {
    const x = 0.5 + i * 2.3;
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.15, w: 2.05, h: 1.1,
      fill: { color: COL.primary }, line: { type: "none" },
    });
    s.addText(st.val, {
      x: x, y: 1.2, w: 2.05, h: 0.6,
      fontSize: 26, bold: true, color: "FFFFFF", fontFace: "Calibri", align: "center", margin: 0,
    });
    s.addText(st.lbl, {
      x: x, y: 1.78, w: 2.05, h: 0.4,
      fontSize: 12, color: "CADCFC", fontFace: "Calibri", align: "center", margin: 0,
    });
  });

  // Per-Device Tabelle
  const tableData = [
    [
      { text: "Gerät", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Messungen", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Sessions", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Aktive Tage", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    ["Xiaomi 2107113SG", "38.087", "69", "34"],
    ["Pixel 7 Pro", "16.919", "72", "28"],
    ["Pixel 9 Pro XL", "7.641", "21", "21"],
    ["Pixel 8 Pro", "3.354", "18", "21"],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 2.55, w: 6.5,
    colW: [2.3, 1.5, 1.2, 1.5],
    fontSize: 12, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  // Features panel
  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.3, y: 2.55, w: 2.2, h: 2.45,
    fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
  });
  s.addText("10 Features", {
    x: 7.4, y: 2.65, w: 2.0, h: 0.35,
    fontSize: 13, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "battery_level", options: { breakLine: true } },
    { text: "screen_on", options: { breakLine: true } },
    { text: "brightness", options: { breakLine: true } },
    { text: "active_app_category", options: { breakLine: true } },
    { text: "wifi_on / mobile_data", options: { breakLine: true } },
    { text: "charging", options: { breakLine: true } },
    { text: "cpu_usage (proxy)", options: { breakLine: true } },
    { text: "temperature", options: { breakLine: true } },
    { text: "hotspot_on" },
  ], {
    x: 7.4, y: 2.97, w: 2.0, h: 2.0,
    fontSize: 9.5, color: COL.text, fontFace: "Consolas", margin: 0, valign: "top",
  });

  addFooter(s);
  addPageNumber(s, 5, TOTAL);
}

// ============================================================
// SLIDE 6 - Sechs Methoden im Vergleich
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Sechs Methoden im Vergleich");

  const methods = [
    { name: "TinyML Conv1D", desc: "Eigenes Modell, 5.697 Param., 14 KB INT8", role: "Hauptmodell", col: COL.tinyml },
    { name: "Random Forest", desc: "200 Trees auf gleichen Features", role: "Sanity (anderes Paradigma)", col: COL.rf },
    { name: "Mean Predictor", desc: "Konstante = Trainings-Mittelwert", role: "Floor (kein Feature-Lernen)", col: COL.mean },
    { name: "Linear Baseline", desc: "battery / drain_rate (BatteryManager)", role: "Analytische Baseline 1", col: COL.linear },
    { name: "Exponential Fit", desc: "b(t) = a + c*exp(-k*t) per Segment", role: "Analytische Baseline 2", col: COL.exp },
    { name: "Google API", desc: "getBatteryDischargePrediction() (Android 12+)", role: "State of the Art", col: COL.google },
  ];

  methods.forEach((m, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 3.05;
    const y = 1.2 + row * 1.85;

    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 2.9, h: 1.6,
      fill: { color: "FFFFFF" }, line: { color: COL.border, width: 1 },
      shadow: { type: "outer", color: "000000", blur: 6, offset: 1, angle: 135, opacity: 0.06 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 2.9, h: 0.08, fill: { color: m.col }, line: { type: "none" },
    });

    s.addText(m.name, {
      x: x + 0.15, y: y + 0.15, w: 2.6, h: 0.35,
      fontSize: 14, bold: true, color: m.col, fontFace: "Calibri", margin: 0,
    });
    s.addText(m.desc, {
      x: x + 0.15, y: y + 0.5, w: 2.6, h: 0.6,
      fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
    });
    s.addText(m.role, {
      x: x + 0.15, y: y + 1.18, w: 2.6, h: 0.3,
      fontSize: 10, italic: true, color: COL.muted, fontFace: "Calibri", margin: 0,
    });
  });

  addFooter(s);
  addPageNumber(s, 6, TOTAL);
}

// ============================================================
// SLIDE 7 - Methodik-Kernpunkt: Segment-Level-Split
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Methodik-Kernpunkt: Segment-Level-Split");

  s.addText("Problem: Bei zufälliger Aufteilung sieht das Modell unbemerkt Daten aus der Zukunft", {
    x: 0.5, y: 1.05, w: 9, h: 0.4,
    fontSize: 14, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  // Leakage Tabelle (Tabelle I aus Paper)
  const tableData = [
    [
      { text: "Setup", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Sequenzen", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "MAE Random-Split (leaky)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "MAE Segment-Level (clean)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Inflation", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    ["Single Device (Xiaomi)", "9.024", "6.53 h", { text: "11.06 h", options: { bold: true, color: COL.bad } }, { text: "~1.69x", options: { bold: true, color: COL.bad } }],
    ["Multi-Device (4 Geräte)", "20.842", "4.00 h", { text: "4.97 h", options: { bold: true, color: COL.exp } }, { text: "~1.24x", options: { bold: true, color: COL.exp } }],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 1.55, w: 9,
    colW: [2.5, 1.4, 2.1, 2.1, 0.9],
    fontSize: 12, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  // Take-aways (direkt unter der Tabelle anschließen)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.85, w: 9, h: 2.2,
    fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
  });
  s.addText("Was das bedeutet", {
    x: 0.7, y: 2.95, w: 8.6, h: 0.35,
    fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Bei zufälliger Aufteilung 'sieht' das Modell unbemerkt zukünftige Daten — der Test-MAE wirkt dadurch um Faktor ~1,7 besser (Single-Device: 6,5 statt 11,1 h).", options: { bullet: true, breakLine: true } },
    { text: "Mit 4 Geräten (Multi-Device) schrumpft die Verzerrung auf 1,24x — die Datenvielfalt schwächt das Lecken ab. Vergleichbar mit Albelali & Ahmed (2025).", options: { bullet: true } },
  ], {
    x: 0.7, y: 3.35, w: 8.6, h: 1.6,
    fontSize: 13, color: COL.text, fontFace: "Calibri", margin: 0, paraSpaceAfter: 8,
  });

  addFooter(s);
  addPageNumber(s, 7, TOTAL);
}

// ============================================================
// SLIDE 8 - Hauptergebnis 1: 6-Wege-Vergleich
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Ergebnis 1: Common Subset (n=2.883)");

  s.addText("Vergleich gegen extrapolierte echte Restzeit · Klammerwerte = 95%-Konfidenzintervall", {
    x: 0.5, y: 1.05, w: 9, h: 0.3,
    fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  // Mini-Erklär-Strip: C-Index in einem Satz für Nicht-ML-Hörer
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.4, w: 9, h: 0.32,
    fill: { color: "F0F4F8" }, line: { color: COL.border, width: 0.5 },
  });
  s.addText("C-Index: Anteil korrekt geordneter Vorhersage-Paare. 0,5 = Münzwurf, 1,0 = perfekt. MAE: durchschnittliche Abweichung in Stunden.", {
    x: 0.7, y: 1.42, w: 8.6, h: 0.28,
    fontSize: 10, italic: true, color: COL.secondary, fontFace: "Calibri", margin: 0, valign: "middle",
  });

  const tableData = [
    [
      { text: "Methode", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "MAE (h)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "RMSE (h)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "C-Index 95%-CI", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Acc +/- 2h", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    [{ text: "Mean Predictor (floor)", options: { color: COL.mean } }, "6.52", "9.25", { text: "0.500 [0.500, 0.500]", options: { color: COL.mean } }, "21.5%"],
    [{ text: "TinyML Conv1D", options: { color: COL.tinyml, bold: true } }, "4.60", "8.47", { text: "0.656 [0.647, 0.664]", options: { bold: true } }, "43.7%"],
    [{ text: "Random Forest", options: { color: COL.rf, bold: true } }, "4.06", "7.56", { text: "0.685 [0.673, 0.695]", options: { bold: true } }, "46.4%"],
    [{ text: "Linear (drain rate)", options: { color: COL.linear } }, { text: "3.30", options: { bold: true } }, "8.57", { text: "0.770 [0.761, 0.780]", options: { bold: true, color: COL.good } }, "57.3%"],
    [{ text: "Exponential fit", options: { color: COL.exp } }, "3.63", "9.04", "0.767 [0.758, 0.776]", "59.0%"],
    [{ text: "Google API", options: { color: COL.google, bold: true } }, "3.37", "8.65", { text: "0.762 [0.751, 0.772]", options: { bold: true } }, "59.0%"],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 1.85, w: 9,
    colW: [2.6, 1.2, 1.2, 2.6, 1.4],
    fontSize: 12, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.55, w: 9, h: 0.6,
    fill: { color: "EDF7EE" }, line: { color: COL.good, width: 1 },
  });
  s.addText("Beide ML-Modelle schlagen Mean-Predictor signifikant. Linear, Exp und Google bilden eine gemeinsame Spitzengruppe bei C ~ 0.77.", {
    x: 0.7, y: 4.58, w: 8.6, h: 0.55,
    fontSize: 12, italic: true, color: COL.text, fontFace: "Calibri", margin: 0, valign: "middle",
  });

  addFooter(s);
  addPageNumber(s, 8, TOTAL);
}

// ============================================================
// SLIDE 9 - Statistische Signifikanz
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Ergebnis 2: Statistische Signifikanz");

  s.addText("Paarweise Tests auf C-Index (paired Bootstrap, BH-korrigiert; Common Subset n=2.883)", {
    x: 0.5, y: 1.05, w: 9, h: 0.3,
    fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  // Mini-Erklär-Strip: p-Wert in einem Satz für Nicht-Statistik-Hörer
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.4, w: 9, h: 0.32,
    fill: { color: "F0F4F8" }, line: { color: COL.border, width: 0.5 },
  });
  s.addText("p < 0,05 = signifikant (Unterschied nicht durch Zufall erklärbar). n.s. = nicht signifikant (beide Methoden statistisch ununterscheidbar).", {
    x: 0.7, y: 1.42, w: 8.6, h: 0.28,
    fontSize: 10, italic: true, color: COL.secondary, fontFace: "Calibri", margin: 0, valign: "middle",
  });

  const tableData = [
    [
      { text: "Vergleich", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "C(A)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "C(B)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Delta C", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "p", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Befund", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    ["TinyML vs. Mean", "0.656", "0.500", "+0.156", "<0.001", { text: "** signifikant über Floor", options: { color: COL.good } }],
    ["RF vs. Mean", "0.685", "0.500", "+0.184", "<0.001", { text: "** signifikant über Floor", options: { color: COL.good } }],
    ["Linear vs. Exponential", "0.770", "0.767", "+0.004", "0.27", { text: "n.s.", options: { color: COL.muted } }],
    ["Linear vs. Google", "0.770", "0.762", "+0.009", { text: "0.11", options: { bold: true, color: COL.bad } }, { text: "n.s. - überraschend!", options: { color: COL.bad, italic: true } }],
    ["TinyML vs. Google", "0.656", "0.762", "-0.105", "<0.001", { text: "** Google klar besser", options: { color: COL.good } }],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 1.8, w: 9,
    colW: [2.6, 0.8, 0.8, 1.0, 0.8, 3.0],
    fontSize: 11.5, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.85, w: 9, h: 1.3,
    fill: { color: "FFF5F5" }, line: { color: COL.bad, width: 1 },
  });
  s.addText("Überraschender Befund", {
    x: 0.7, y: 3.9, w: 8.6, h: 0.3,
    fontSize: 13, bold: true, color: COL.bad, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Linear-Drain-Rate-Baseline ist statistisch nicht von Google-API unterscheidbar (p=0.11 für C, p=0.16 für MAE) — Linear liegt numerisch sogar minimal vorn.", options: { bullet: true, breakLine: true } },
    { text: "Beide ML-Modelle (TinyML, RF) signifikant über Mean, aber unter der Spitzengruppe.", options: { bullet: true, breakLine: true } },
    { text: "Implikation: 'einfach BatteryManager-Counter lesen' ist auf Aggregat-Ebene konkurrenzfähig mit dem System-ML-Estimator.", options: { bullet: true } },
  ], {
    x: 0.7, y: 4.2, w: 8.6, h: 0.95,
    fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, paraSpaceAfter: 2,
  });

  addFooter(s);
  addPageNumber(s, 9, TOTAL);
}

// ============================================================
// SLIDE 10 - Hauptergebnis 3: Per-Device (Hardware-Effekt)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Ergebnis 3: Per-Device (Hardware-Effekt)");

  s.addText("Derselbe TinyML-Conv1D, evaluiert pro Gerät - der praktisch relevanteste Befund", {
    x: 0.5, y: 1.05, w: 9, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  // Per-Device C-Index als Chart
  s.addChart(pres.charts.BAR, [
    {
      name: "TinyML",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.754, 0.742, 0.571, 0.593],
    },
    {
      name: "Random Forest",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.807, 0.815, 0.767, 0.628],
    },
    {
      name: "Linear",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.792, 0.696, 0.730, 0.724],
    },
    {
      name: "Google API",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.853, 0.921, 0.677, 0.473],
    },
  ], {
    x: 0.5, y: 1.5, w: 5.8, h: 3.5,
    barDir: "col",
    chartColors: [COL.tinyml, COL.rf, COL.linear, COL.google],
    catAxisLabelFontSize: 10,
    valAxisLabelFontSize: 10,
    showLegend: true, legendPos: "b", legendFontSize: 10,
    valAxisMinVal: 0.4, valAxisMaxVal: 1.0,
    showValue: false,
    valGridLine: { color: COL.border, size: 0.5 },
    catGridLine: { style: "none" },
    chartArea: { fill: { color: "FFFFFF" } },
    title: "C-Index nach Gerät",
    showTitle: true, titleFontSize: 12, titleColor: COL.primary,
  });

  // Right side: Key observations
  s.addText("Beobachtungen", {
    x: 6.5, y: 1.55, w: 3, h: 0.35,
    fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "TinyML: 0.75 (Pixel 7 Pro) bis 0.59 (Xiaomi)", options: { bullet: true, breakLine: true } },
    { text: "Analytische Baselines stabiler über Geräte", options: { bullet: true, breakLine: true } },
    { text: "Pixel 9 Pro XL: Linear (0.73) > Google (0.68)", options: { bullet: true, breakLine: true, bold: true } },
    { text: "Pixel 8 Pro: nur n=98 (breite CIs)", options: { bullet: true } },
  ], {
    x: 6.5, y: 1.9, w: 3, h: 2.0,
    fontSize: 11, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 3,
  });

  // Confounder Caveat
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.5, y: 3.85, w: 3, h: 1.15,
    fill: { color: "FFF6E5" }, line: { color: COL.google, width: 1 },
  });
  s.addText("Aber Achtung", {
    x: 6.6, y: 3.92, w: 2.8, h: 0.28,
    fontSize: 11, bold: true, color: COL.google, fontFace: "Calibri", margin: 0,
  });
  s.addText("Auf dem Xiaomi war der Akku meist voll (88,8 % der Zeit über 75 %). Damit fehlt dem Modell Entlade-Verlauf zum Lernen — der schwache Xiaomi-Wert kann genauso gut an mangelnder Datenvielfalt liegen wie an der Hardware.", {
    x: 6.6, y: 4.2, w: 2.8, h: 0.8,
    fontSize: 9.5, italic: true, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
  });

  addFooter(s);
  addPageNumber(s, 10, TOTAL);
}

// ============================================================
// SLIDE 11 - Effizienz
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Ergebnis 4: Effizienz (TFLite funktioniert)");

  // Stat callouts
  const stats = [
    { val: "14.4", unit: "KB", lbl: "INT8 Modell", col: COL.tinyml },
    { val: "3.3", unit: "us", lbl: "Inferenz-Latenz", col: COL.exp },
    { val: "7.6x", unit: "", lbl: "kleiner als Keras", col: COL.google },
    { val: "~12.000x", unit: "", lbl: "schneller als Keras Float32", col: COL.rf },
  ];
  stats.forEach((st, i) => {
    const x = 0.5 + i * 2.3;
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.15, w: 2.05, h: 1.4,
      fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.15, w: 2.05, h: 0.08, fill: { color: st.col }, line: { type: "none" },
    });
    s.addText([
      { text: st.val, options: { fontSize: 30, bold: true, color: st.col } },
      { text: " " + st.unit, options: { fontSize: 16, color: st.col } },
    ], {
      x: x, y: 1.3, w: 2.05, h: 0.65,
      align: "center", fontFace: "Calibri", margin: 0, valign: "middle",
    });
    s.addText(st.lbl, {
      x: x + 0.05, y: 2.0, w: 1.95, h: 0.5,
      fontSize: 11, color: COL.text, fontFace: "Calibri", align: "center", margin: 0, valign: "top",
    });
  });

  // Tabelle mit allen Varianten
  const tableData = [
    [
      { text: "Variante", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Größe (KB)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Avg Latenz", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    ["Keras Float32", "109.19", "39.0 ms"],
    ["TFLite dynamic-range", "15.99", "3.1 us"],
    ["TFLite float16", "17.80", "2.9 us"],
    [{ text: "TFLite INT8 (Deploy)", options: { bold: true, color: COL.tinyml } }, { text: "14.35", options: { bold: true } }, { text: "3.3 us", options: { bold: true } }],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 2.85, w: 5.5,
    colW: [2.5, 1.5, 1.5],
    fontSize: 11, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  // Take-away
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.3, y: 2.85, w: 3.2, h: 2.0,
    fill: { color: "EDF7EE" }, line: { color: COL.good, width: 1 },
  });
  s.addText("Take-away", {
    x: 6.45, y: 2.95, w: 3.0, h: 0.3,
    fontSize: 12, bold: true, color: COL.good, fontFace: "Calibri", margin: 0,
  });
  s.addText("Die TinyML-Quantisierungs-Pipeline funktioniert wie beworben. Effizienz ist die klare Stärke von TinyML.", {
    x: 6.45, y: 3.3, w: 3.0, h: 1.5,
    fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
  });

  addFooter(s);
  addPageNumber(s, 11, TOTAL);
}

// ============================================================
// SLIDE 12 - Diskussion: zwei Schlüssel-Befunde (konsolidiert)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Diskussion: Zwei Schlüssel-Befunde");

  // ===== LINKE SPALTE: TinyML lernt Signal =====
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.15, w: 4.3, h: 3.8,
    fill: { color: "F8FAFC" }, line: { color: COL.good, width: 1 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.15, w: 0.08, h: 3.8, fill: { color: COL.good }, line: { type: "none" },
  });
  s.addText("Befund 1: TinyML lernt Signal", {
    x: 0.75, y: 1.25, w: 4.0, h: 0.4,
    fontSize: 14, bold: true, color: COL.good, fontFace: "Calibri", margin: 0,
  });
  s.addText("Signal vorhanden — aber target-abhängig:", {
    x: 0.75, y: 1.65, w: 4.0, h: 0.35,
    fontSize: 11, italic: true, color: COL.muted, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "vs. Trainings-Target (y_extrap): ", options: { bold: true } },
    { text: "TinyML C=0.66, RF C=0.69", options: { color: COL.good, bold: true, breakLine: true } },
    { text: "  beide signifikant über Floor (p < 0.001)", options: { color: COL.good, breakLine: true } },
    { text: "  ", options: { breakLine: true } },
    { text: "vs. gemessene Restzeit (y_real): ", options: { bold: true } },
    { text: "kein signifikanter Vorsprung mehr", options: { color: COL.bad, bold: true, breakLine: true } },
    { text: "  TinyML p=0.82; RF sogar unter Floor", options: { color: COL.muted } },
  ], {
    x: 0.75, y: 2.0, w: 4.0, h: 2.4,
    fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top", paraSpaceAfter: 2,
  });
  s.addText("Aber: ML bleibt hinter analytischen Baselines + Google (C ~ 0.77).", {
    x: 0.75, y: 4.5, w: 4.0, h: 0.4,
    fontSize: 11, italic: true, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });

  // ===== RECHTE SPALTE: Google ~ Linear =====
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.15, w: 4.3, h: 3.8,
    fill: { color: "F8FAFC" }, line: { color: COL.bad, width: 1 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.15, w: 0.08, h: 3.8, fill: { color: COL.bad }, line: { type: "none" },
  });
  s.addText("Befund 2: Google = Linear-Baseline", {
    x: 5.45, y: 1.25, w: 4.0, h: 0.4,
    fontSize: 14, bold: true, color: COL.bad, fontFace: "Calibri", margin: 0,
  });
  s.addText("Statistisch ununterscheidbar (p=0.11):", {
    x: 5.45, y: 1.65, w: 4.0, h: 0.35,
    fontSize: 11, italic: true, color: COL.muted, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Linear ", options: { bold: true, color: COL.linear } },
    { text: "(battery / drain_rate)", options: { color: COL.muted, breakLine: true } },
    { text: "  MAE 3.30 h, C-Index 0.770", options: { breakLine: true } },
    { text: "  ", options: { breakLine: true } },
    { text: "Google API ", options: { bold: true, color: COL.google } },
    { text: "(privilegierter Systemzugang)", options: { color: COL.muted, breakLine: true } },
    { text: "  MAE 3.37 h, C-Index 0.762", options: { breakLine: true } },
  ], {
    x: 5.45, y: 2.0, w: 4.0, h: 2.4,
    fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top", paraSpaceAfter: 2,
  });
  s.addText("Hardware-Vorteil zahlt sich erst bei sehr langen Restzeiten aus (>=30 h: C 0.98 vs. 0.64).", {
    x: 5.45, y: 4.5, w: 4.0, h: 0.4,
    fontSize: 11, italic: true, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });

  addFooter(s);
  addPageNumber(s, 12, TOTAL);
}

// ============================================================
// SLIDE 13 - Limitations (3 wichtigste)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Limitations (ehrlich)");

  const lims = [
    {
      head: "Akku wird selten ganz leer gefahren",
      body: "Akku wird im Alltag nie auf 0 % entladen — Grundeigenschaft der Daten, gleiche Beobachtung bei Li et al. (2018) mit 51 Nutzern. Deshalb C-Index als Hauptmaß statt MAE.",
    },
    {
      head: "Multi-Device, aber nicht Cross-Device",
      body: "Training sieht alle vier Geräte. Wie das Modell auf einem komplett neuen Gerät funktionieren würde, ist offene Folgearbeit.",
    },
    {
      head: "TinyML auf Pixel 9 Pro XL überraschend schlecht",
      body: "TinyML schafft dort nur C-Index 0,57, während Random Forest auf denselben Daten 0,77 erreicht. Warum genau, ist mit den aktuellen Daten nicht erklärbar — offen für Folgearbeiten.",
    },
  ];

  lims.forEach((l, i) => {
    const y = 1.3 + i * 1.25;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 9, h: 1.05,
      fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 0.08, h: 1.05, fill: { color: COL.primary }, line: { type: "none" },
    });
    s.addText(l.head, {
      x: 0.75, y: y + 0.12, w: 8.6, h: 0.35,
      fontSize: 15, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
    });
    s.addText(l.body, {
      x: 0.75, y: y + 0.5, w: 8.6, h: 0.55,
      fontSize: 12, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
    });
  });

  addFooter(s);
  addPageNumber(s, 13, TOTAL);
}

// ============================================================
// SLIDE 14 - Conclusion (drei Achsen)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  s.addText("Conclusion: Antwort auf die Forschungsfrage", {
    x: 0.5, y: 0.4, w: 9, h: 0.7,
    fontSize: 26, bold: true, color: "FFFFFF", fontFace: "Calibri",
  });

  const concl = [
    {
      head: "Genauigkeit",
      body: "TinyML schlägt Mean (C 0.66), bleibt aber hinter Linear/Exp/Google (C ~ 0.77). Google nicht signifikant besser als Linear.",
      col: COL.tinyml,
    },
    {
      head: "Effizienz",
      body: "TFLite-Quantisierung funktioniert. 14.4 KB, 3.3 us. Auf dieser Achse hat TinyML uneingeschränkt seinen Wert.",
      col: COL.exp,
    },
    {
      head: "Hardware & Datenvielfalt",
      body: "TinyML 0,75 auf Pixel 7 Pro, 0,59 auf Xiaomi. Engpass nicht am Modell, sondern an Sensor-Qualität und fehlendem Entlade-Verlauf (Xiaomi-Akku 88,8 % der Zeit voll).",
      col: COL.google,
    },
  ];

  concl.forEach((c, i) => {
    const x = 0.5 + i * 3.1;
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.5, w: 2.95, h: 2.8,
      fill: { color: "FFFFFF", transparency: 92 }, line: { color: c.col, width: 2 },
    });
    s.addText(c.head, {
      x: x + 0.15, y: 1.65, w: 2.65, h: 0.4,
      fontSize: 17, bold: true, color: c.col, fontFace: "Calibri", margin: 0,
    });
    s.addText(c.body, {
      x: x + 0.15, y: 2.1, w: 2.65, h: 2.1,
      fontSize: 12, color: "FFFFFF", fontFace: "Calibri", margin: 0, valign: "top",
    });
  });

  // Footer + Seitenzahl in hellem Schriftton (dunkler Hintergrund)
  s.addText("K. Schürger - TinyML für Akkulaufzeit-Vorhersage", {
    x: 0.5, y: 5.3, w: 7, h: 0.25,
    fontSize: 9, color: "9CB4DE", fontFace: "Calibri",
  });
  s.addText("14 / " + TOTAL, {
    x: 9.0, y: 5.3, w: 0.9, h: 0.25,
    fontSize: 9, color: "9CB4DE", align: "right", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 15 - Q&A (schlicht)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  // Großer Dank-Block, mittig
  s.addText("Vielen Dank", {
    x: 0.6, y: 1.6, w: 8.8, h: 0.9,
    fontSize: 54, bold: true, color: "FFFFFF", fontFace: "Calibri", align: "center",
  });

  // Akzent-Linie unter dem Dank
  s.addShape(pres.shapes.RECTANGLE, {
    x: 4.3, y: 2.55, w: 1.4, h: 0.06,
    fill: { color: COL.bad }, line: { type: "none" },
  });

  s.addText("Fragen?", {
    x: 0.6, y: 2.85, w: 8.8, h: 0.7,
    fontSize: 32, italic: true, color: "CADCFC", fontFace: "Calibri", align: "center",
  });

  // Subtle attribution unten
  s.addText([
    { text: "Keno Schürger", options: { bold: true, breakLine: true } },
    { text: "TinyML für Akkulaufzeit-Vorhersage auf Android", options: { color: "9CB4DE" } },
  ], {
    x: 0.6, y: 4.15, w: 8.8, h: 0.9,
    fontSize: 13, color: "FFFFFF", fontFace: "Calibri", align: "center",
  });

  // Footer + Seitenzahl in hellem Schriftton (dunkler Hintergrund)
  s.addText("K. Schürger - TinyML für Akkulaufzeit-Vorhersage", {
    x: 0.5, y: 5.3, w: 7, h: 0.25,
    fontSize: 9, color: "9CB4DE", fontFace: "Calibri",
  });
  s.addText("15 / " + TOTAL, {
    x: 9.0, y: 5.3, w: 0.9, h: 0.25,
    fontSize: 9, color: "9CB4DE", align: "right", fontFace: "Calibri",
  });
}

// ============================================================
// Write
// ============================================================
pres.writeFile({ fileName: "Paper_Verteidigung.pptx" }).then((file) => {
  console.log("Wrote: " + file);
});

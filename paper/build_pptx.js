// Verteidigungs-Praesentation fuer das Paper:
// "App-Level TinyML for Smartphone Battery-Life Prediction"
// Output: Paper_Verteidigung.pptx
//
// Aufruf: node build_pptx.js

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "Keno Schuerger";
pres.title = "TinyML fuer Akkulaufzeit-Vorhersage auf Android - Verteidigung";

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
  slide.addText("K. Schuerger - TinyML fuer Akkulaufzeit-Vorhersage", {
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

const TOTAL = 16;

// ============================================================
// SLIDE 1 - Titelseite (dunkler Hintergrund)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  s.addText("App-Level TinyML fuer", {
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

  s.addText("Ein methodisch ehrlicher Erfahrungsbericht aus dem Multi-Device-Vergleich", {
    x: 0.6, y: 3.2, w: 8.8, h: 0.45,
    fontSize: 16, italic: true, color: "CADCFC", fontFace: "Calibri",
  });

  s.addText([
    { text: "Keno Schuerger", options: { bold: true, breakLine: true } },
    { text: "Technische Hochschule Wuerzburg-Schweinfurt (THWS)", options: { color: "9CB4DE", breakLine: true } },
    { text: "Vertiefungsseminar - Mai 2026", options: { color: "9CB4DE" } },
  ], {
    x: 0.6, y: 4.2, w: 8.8, h: 1.1,
    fontSize: 14, color: "FFFFFF", fontFace: "Calibri",
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
    { head: "Achse 2", body: "Effizienz\n(Latenz, Modellgroesse)", col: COL.google },
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
    { text: "Ignoriert aktuelle Nutzung, App-Kontext", options: { bullet: true, breakLine: true } },
    { text: "MIUI/OneUI: oft Legacy-Code seit Android 5", options: { bullet: true } },
  ], {
    x: 0.5, y: 1.55, w: 4.3, h: 1.8,
    fontSize: 13, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 6,
  });

  s.addText("Was sich seit Android 12 (2021) aendert", {
    x: 5.2, y: 1.15, w: 4.3, h: 0.4,
    fontSize: 17, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "PowerManager.getBatteryDischargePrediction()", options: { bullet: true, breakLine: true } },
    { text: "Erstes ML-Modell direkt im Android-System", options: { bullet: true, breakLine: true } },
    { text: "Laeuft im Systemprozess - privilegierter Zugriff", options: { bullet: true } },
  ], {
    x: 5.2, y: 1.55, w: 4.3, h: 1.8,
    fontSize: 13, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 6,
  });

  // Highlight: research question
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.7, w: 9, h: 1.0,
    fill: { color: "FFF6E5" }, line: { color: COL.google, width: 1 },
  });
  s.addText("Forschungsfrage", {
    x: 0.7, y: 3.78, w: 8.6, h: 0.3,
    fontSize: 11, bold: true, color: COL.google, fontFace: "Calibri", margin: 0,
  });
  s.addText("Kann eine Drittanbieter-App, die nur oeffentliche Sensor-APIs nutzt, mit der System-API mithalten - oder ueberhaupt etwas Sinnvolles lernen?", {
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
      body: "51 Nutzer, 21 Monate. Fuehrt den Concordance-Index als Standard-Metrik ein, weil das 'severe data missing problem' (User entladen selten auf 0%) MAE unzuverlaessig macht.",
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
      sub: "Industriestandard-Benchmark fuer TinyML",
      body: "Misst Accuracy, Latency, Energy gemeinsam. Smartphone-Anwendungen fehlen in der Literatur (siehe Heydari & Mahmoud 2025, Alajlan & Ibrahim 2022).",
      col: COL.google,
    },
    {
      head: "Albelali & Ahmed (2025)",
      sub: "Hidden Leaks in Time Series Forecasting",
      body: "Random-Shuffle-Splits ueber Sliding-Window-Sequenzen lecken Future-Information. RMSE Gain bis 20.5% bei 10-fold CV (LSTM).",
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
  slideTitle(s, "Datensammlung: 4 Geraete, 45 Tage");

  // Big stat row
  const stats = [
    { val: "66.001", lbl: "Messungen" },
    { val: "4", lbl: "Geraete" },
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
      { text: "Geraet", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
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

  s.addText("Problem: Random-Shuffle ueber Sliding-Window-Sequenzen leckt Future-Information", {
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
    ["Single Device (Xiaomi)", "9.024", "0.53 h", { text: "9.96 h", options: { bold: true, color: COL.bad } }, { text: "~19x", options: { bold: true, color: COL.bad } }],
    ["Multi-Device (4 Geraete)", "20.842", "4.00 h", { text: "4.97 h", options: { bold: true, color: COL.exp } }, { text: "~1.24x", options: { bold: true, color: COL.exp } }],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 1.55, w: 9,
    colW: [2.5, 1.4, 2.1, 2.1, 0.9],
    fontSize: 12, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  // Take-aways (direkt unter der Tabelle anschliessen)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.85, w: 9, h: 2.2,
    fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
  });
  s.addText("Was das bedeutet", {
    x: 0.7, y: 2.95, w: 8.6, h: 0.35,
    fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Single-Device: random-shuffle taeuscht eine 19x bessere Performance vor - reines Leakage-Artefakt.", options: { bullet: true, breakLine: true } },
    { text: "Multi-Device: nur noch 1.24x Inflation, im Bereich von Albelali & Ahmed (2025) mit 10-fold CV.", options: { bullet: true, breakLine: true } },
    { text: "Eigener methodischer Beitrag: Inflation ist data-diversity-dependent. Empfehlung fuer Folgearbeiten in dieser Domaene: Splitting-Strategie explizit nennen.", options: { bullet: true } },
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
  slideTitle(s, "Ergebnis 1: Common Subset (n=2.827)");

  s.addText("vs. y_extrap, 95% Bootstrap-CI, leakage-freier Multi-Device-Split", {
    x: 0.5, y: 1.05, w: 9, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  const tableData = [
    [
      { text: "Methode", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "MAE (h)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "RMSE (h)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "C-Index 95%-CI", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Acc +/- 2h", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    [{ text: "Mean Predictor (floor)", options: { color: COL.mean } }, "6.51", "9.28", { text: "0.500 [0.500, 0.500]", options: { color: COL.mean } }, "21.7%"],
    [{ text: "TinyML Conv1D", options: { color: COL.tinyml, bold: true } }, "4.28", "8.38", { text: "0.666 [0.656, 0.675]", options: { bold: true } }, "51.1%"],
    [{ text: "Random Forest", options: { color: COL.rf, bold: true } }, "4.01", "7.54", { text: "0.686 [0.673, 0.696]", options: { bold: true } }, "45.2%"],
    [{ text: "Linear (drain rate)", options: { color: COL.linear } }, { text: "3.21", options: { bold: true } }, "8.55", "0.776 [0.767, 0.784]", "58.3%"],
    [{ text: "Exponential fit", options: { color: COL.exp } }, "3.49", "8.88", "0.773 [0.764, 0.781]", "59.8%"],
    [{ text: "Google API", options: { color: COL.google, bold: true } }, "3.24", "8.55", { text: "0.777 [0.767, 0.785]", options: { bold: true, color: COL.good } }, "60.1%"],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 1.45, w: 9,
    colW: [2.6, 1.2, 1.2, 2.6, 1.4],
    fontSize: 12, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.4, w: 9, h: 0.7,
    fill: { color: "EDF7EE" }, line: { color: COL.good, width: 1 },
  });
  s.addText("Beide ML-Modelle schlagen Mean-Predictor signifikant. Linear, Exp und Google bilden eine gemeinsame Spitzengruppe bei C ~ 0.77.", {
    x: 0.7, y: 4.45, w: 8.6, h: 0.6,
    fontSize: 13, italic: true, color: COL.text, fontFace: "Calibri", margin: 0, valign: "middle",
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

  s.addText("Paarweise Permutationstests auf C-Index (Common Subset n=2.827)", {
    x: 0.5, y: 1.05, w: 9, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri",
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
    ["TinyML vs. Mean", "0.666", "0.500", "+0.166", "0.005", { text: "** signifikant ueber Floor", options: { color: COL.good } }],
    ["RF vs. Mean", "0.686", "0.500", "+0.186", "0.005", { text: "** signifikant ueber Floor", options: { color: COL.good } }],
    ["Linear vs. Exponential", "0.776", "0.773", "+0.003", "0.30", { text: "n.s.", options: { color: COL.muted } }],
    ["Linear vs. Google", "0.776", "0.777", "-0.001", { text: "0.83", options: { bold: true, color: COL.bad } }, { text: "n.s. - ueberraschend!", options: { color: COL.bad, italic: true } }],
    ["TinyML vs. Google", "0.666", "0.777", "-0.111", "0.005", { text: "** Google klar besser", options: { color: COL.good } }],
  ];
  s.addTable(tableData, {
    x: 0.5, y: 1.45, w: 9,
    colW: [2.6, 0.8, 0.8, 1.0, 0.8, 3.0],
    fontSize: 11.5, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border },
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.55, w: 9, h: 1.65,
    fill: { color: "FFF5F5" }, line: { color: COL.bad, width: 1 },
  });
  s.addText("Ueberraschender Befund", {
    x: 0.7, y: 3.62, w: 8.6, h: 0.32,
    fontSize: 14, bold: true, color: COL.bad, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Linear-Drain-Rate-Baseline ist statistisch nicht von Google-API unterscheidbar (p=0.83 fuer C, p=0.55 fuer MAE).", options: { bullet: true, breakLine: true } },
    { text: "Beide ML-Modelle (TinyML, Random Forest) signifikant ueber Mean-Predictor, aber signifikant unter der Spitzengruppe.", options: { bullet: true, breakLine: true } },
    { text: "Implikation: 'einfach BatteryManager-Counter lesen' ist auf Aggregat-Ebene konkurrenzfaehig mit dem System-ML-Estimator.", options: { bullet: true } },
  ], {
    x: 0.7, y: 3.97, w: 8.6, h: 0.95,
    fontSize: 12, color: COL.text, fontFace: "Calibri", margin: 0, paraSpaceAfter: 3,
  });

  // Caveat-Zeile in muted Italic
  s.addText("Nuance: Aggregat-Befund. Im Bucket >=30h (n=58) gewinnt Google klar (C 0.98 vs 0.64). Auf kurzen/mittleren Restzeiten (~97% der Daten) wirklich praktisch identisch.", {
    x: 0.7, y: 4.93, w: 8.6, h: 0.25,
    fontSize: 10, italic: true, color: COL.muted, fontFace: "Calibri", margin: 0,
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

  s.addText("Derselbe TinyML-Conv1D, evaluiert pro Geraet - der praktisch relevanteste Befund", {
    x: 0.5, y: 1.05, w: 9, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  // Per-Device C-Index als Chart
  s.addChart(pres.charts.BAR, [
    {
      name: "TinyML",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.786, 0.714, 0.599, 0.593],
    },
    {
      name: "Random Forest",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.804, 0.801, 0.759, 0.631],
    },
    {
      name: "Linear",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.792, 0.696, 0.730, 0.724],
    },
    {
      name: "Google API",
      labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"],
      values: [0.853, 0.921, 0.677, 0.664],
    },
  ], {
    x: 0.5, y: 1.5, w: 5.8, h: 3.5,
    barDir: "col",
    chartColors: [COL.tinyml, COL.rf, COL.linear, COL.google],
    catAxisLabelFontSize: 10,
    valAxisLabelFontSize: 10,
    showLegend: true, legendPos: "b", legendFontSize: 10,
    valAxisMinVal: 0.5, valAxisMaxVal: 1.0,
    showValue: false,
    valGridLine: { color: COL.border, size: 0.5 },
    catGridLine: { style: "none" },
    chartArea: { fill: { color: "FFFFFF" } },
    title: "C-Index nach Geraet (vs. y_extrap)",
    showTitle: true, titleFontSize: 12, titleColor: COL.primary,
  });

  // Right side: Key observations
  s.addText("Beobachtungen", {
    x: 6.5, y: 1.55, w: 3, h: 0.35,
    fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "TinyML: 0.79 (Pixel 7 Pro) bis 0.59 (Xiaomi)", options: { bullet: true, breakLine: true } },
    { text: "Analytische Baselines stabiler ueber Geraete", options: { bullet: true, breakLine: true } },
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
  s.addText("Confounder", {
    x: 6.6, y: 3.92, w: 2.8, h: 0.28,
    fontSize: 11, bold: true, color: COL.google, fontFace: "Calibri", margin: 0,
  });
  s.addText("Xiaomi-Daten: Akku 88.8% der Zeit ueber 75% (mean 94%). Wenig Discharge-Dynamik zum Lernen. Sensor-Qualitaet UND Datenverteilung gemischt.", {
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
    { val: "4.5", unit: "us", lbl: "Inferenz-Latenz", col: COL.exp },
    { val: "7.6x", unit: "", lbl: "kleiner als Keras", col: COL.google },
    { val: "10.000x", unit: "", lbl: "schneller als Keras Float32", col: COL.rf },
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
      { text: "Groesse (KB)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Avg Latenz", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    ["Keras Float32", "109.18", "47.1 ms"],
    ["TFLite dynamic-range", "15.99", "3.9 us"],
    ["TFLite float16", "17.80", "3.7 us"],
    [{ text: "TFLite INT8 (Deploy)", options: { bold: true, color: COL.tinyml } }, { text: "14.35", options: { bold: true } }, { text: "4.5 us", options: { bold: true } }],
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
  s.addText("Die TinyML-Quantisierungs-Pipeline funktioniert wie beworben. Auf der Effizienz-Achse hat TinyML keinen Wettbewerbsnachteil - der Engpass liegt allein auf der Accuracy-Achse.", {
    x: 6.45, y: 3.3, w: 3.0, h: 1.5,
    fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
  });

  addFooter(s);
  addPageNumber(s, 11, TOTAL);
}

// ============================================================
// SLIDE 12 - Diskussion: TinyML lernt Signal aber...
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Diskussion 1: TinyML lernt Signal");

  s.addText("Anders als auf Single-Device-Setup ist TinyML hier kein Mean-Predictor mehr", {
    x: 0.5, y: 1.05, w: 9, h: 0.35,
    fontSize: 13, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  // Vergleich Single vs Multi-Device
  const rows = [
    { title: "Single Device (frueher Stand)", col: COL.bad, text: "TinyML C-Index 0.50 = Mean-Predictor. Random Forest 0.51. Beide statistisch nicht von 'kein Modell' unterscheidbar." },
    { title: "Multi-Device (jetzt)", col: COL.good, text: "TinyML C-Index 0.67, RF 0.69. Beide signifikant ueber Floor (p<=0.005). ML lernt erkennbares Signal." },
  ];

  rows.forEach((r, i) => {
    const y = 1.55 + i * 1.5;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 9, h: 1.3,
      fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 0.08, h: 1.3, fill: { color: r.col }, line: { type: "none" },
    });
    s.addText(r.title, {
      x: 0.75, y: y + 0.15, w: 8.6, h: 0.4,
      fontSize: 14, bold: true, color: r.col, fontFace: "Calibri", margin: 0,
    });
    s.addText(r.text, {
      x: 0.75, y: y + 0.55, w: 8.6, h: 0.7,
      fontSize: 12, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
    });
  });

  s.addText('Aber: ML bleibt hinter analytischen Baselines + Google bei C ~ 0.77.', {
    x: 0.5, y: 4.65, w: 9, h: 0.4,
    fontSize: 13, italic: true, color: COL.primary, fontFace: "Calibri", align: "center", bold: true,
  });

  addFooter(s);
  addPageNumber(s, 12, TOTAL);
}

// ============================================================
// SLIDE 13 - Diskussion: Google ≈ Linear
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Diskussion 2: Google = Linear-Baseline");

  s.addText("Auf der gemeinsamen Schnittmenge sind die System-API und die einfache lineare Drain-Rate-Baseline statistisch ununterscheidbar.", {
    x: 0.5, y: 1.05, w: 9, h: 0.6,
    fontSize: 13, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  // Zwei boxes nebeneinander
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.85, w: 4.3, h: 2.6,
    fill: { color: "F8FAFC" }, line: { color: COL.linear, width: 1 },
  });
  s.addText("Linear (battery / drain_rate)", {
    x: 0.7, y: 2.0, w: 4.0, h: 0.4,
    fontSize: 14, bold: true, color: COL.linear, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Liest BatteryManager.CHARGE_COUNTER", options: { breakLine: true } },
    { text: "Liest BatteryManager.CURRENT_AVERAGE", options: { breakLine: true } },
    { text: "  ", options: { breakLine: true } },
    { text: "MAE: 3.21 h", options: { bold: true, breakLine: true } },
    { text: "C-Index: 0.776", options: { bold: true } },
  ], {
    x: 0.7, y: 2.4, w: 4.0, h: 2.0,
    fontSize: 12, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.85, w: 4.3, h: 2.6,
    fill: { color: "F8FAFC" }, line: { color: COL.google, width: 1 },
  });
  s.addText("Google API (Systemprozess)", {
    x: 5.4, y: 2.0, w: 4.0, h: 0.4,
    fontSize: 14, bold: true, color: COL.google, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Zusaetzliche privilegierte Signale:", options: { breakLine: true } },
    { text: "PowerStats HAL (per-App-Strom)", options: { breakLine: true, bullet: true, indentLevel: 0 } },
    { text: "Adaptive-Battery-Integration", options: { breakLine: true, bullet: true } },
    { text: "MAE: 3.24 h", options: { bold: true, breakLine: true } },
    { text: "C-Index: 0.777", options: { bold: true } },
  ], {
    x: 5.4, y: 2.4, w: 4.0, h: 2.0,
    fontSize: 12, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
  });

  // Conclusion
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.55, w: 9, h: 0.55,
    fill: { color: "FFF6E5" }, line: { color: COL.google, width: 1 },
  });
  s.addText("Der zusaetzliche Hardware-Zugang von Google traegt nichts Messbares fuer 'Stunden bis 0%' bei (Permutationstest p=0.83 fuer C, p=0.55 fuer MAE).", {
    x: 0.7, y: 4.6, w: 8.6, h: 0.45,
    fontSize: 12, italic: true, color: COL.text, fontFace: "Calibri", margin: 0, valign: "middle",
  });

  addFooter(s);
  addPageNumber(s, 13, TOTAL);
}

// ============================================================
// SLIDE 14 - Limitations
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Limitations (ehrlich)");

  const lims = [
    {
      head: "Right-censored Daten",
      body: "Akku wird im Alltag nie auf 0% entladen. Strukturelle Eigenschaft der Domaene, nicht der Studie - gleiche Beobachtung bei Li et al. (2018) mit 51 Nutzern.",
      col: COL.muted,
    },
    {
      head: "Common-Subset-Selection-Bias",
      body: "Wo Google-API definiert ist, sind die Restzeiten kuerzer (mean 6.7 h vs. 7.7 h im gesamten Test). Affektiert MAE symmetrisch, Ranking unaffected.",
      col: COL.muted,
    },
    {
      head: "Multi-Device, aber nicht Cross-Device",
      body: "Train sieht alle 4 Geraete. Eine Leave-One-Device-Out-Studie ist offene Folgearbeit.",
      col: COL.muted,
    },
    {
      head: "n=98 fuer Pixel 8 Pro",
      body: "Breite Konfidenzintervalle. C-Index 0.92 ist Punktwert mit wenig statistischer Sicherheit.",
      col: COL.muted,
    },
    {
      head: "TinyML auf Pixel 9 Pro XL anomal schlecht",
      body: "C=0.60 waehrend RF auf demselben Geraet C=0.76 erreicht. Keine kausale Erklaerung im aktuellen Datensatz.",
      col: COL.muted,
    },
  ];

  lims.forEach((l, i) => {
    const y = 1.15 + i * 0.78;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 0.08, h: 0.7, fill: { color: COL.primary }, line: { type: "none" },
    });
    s.addText(l.head, {
      x: 0.75, y: y, w: 8.6, h: 0.3,
      fontSize: 13, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
    });
    s.addText(l.body, {
      x: 0.75, y: y + 0.27, w: 8.6, h: 0.45,
      fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
    });
  });

  addFooter(s);
  addPageNumber(s, 14, TOTAL);
}

// ============================================================
// SLIDE 15 - Conclusion (drei Achsen)
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
      body: "TinyML schlaegt Mean (C 0.67), bleibt aber hinter Linear/Exp/Google (C ~ 0.77). Google nicht signifikant besser als Linear.",
      col: COL.tinyml,
    },
    {
      head: "Effizienz",
      body: "TFLite-Quantisierung funktioniert. 14.4 KB, 4.5 us. Auf dieser Achse hat TinyML uneingeschraenkt seinen Wert.",
      col: COL.exp,
    },
    {
      head: "Hardware & Daten-Coverage",
      body: "TinyML 0.79 auf Pixel 7 Pro, 0.59 auf Xiaomi. Engpass: Sensor-Qualitaet UND Discharge-Dynamik-Coverage (Xiaomi-Akku 88.8% der Zeit voll). Nicht die Modellarchitektur.",
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

  s.addText("Methodischer Beitrag: Segment-Level-Split als Standard fuer Sliding-Window-Time-Series in Mobile-Sensing.", {
    x: 0.5, y: 4.55, w: 9, h: 0.5,
    fontSize: 14, italic: true, color: "CADCFC", fontFace: "Calibri", align: "center",
  });
}

// ============================================================
// SLIDE 16 - Q&A / Backup
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Vielen Dank - Fragen?");

  s.addText("Vorbereitete Antworten auf erwartete Fragen", {
    x: 0.5, y: 1.05, w: 9, h: 0.4,
    fontSize: 14, italic: true, color: COL.muted, fontFace: "Calibri",
  });

  const qa = [
    { q: "Warum kein positives Ergebnis?", a: "Das positive Ergebnis (MAE 0.5h Single-Device) war Leakage-Artefakt. Die saubere Methodik enthuellt das. Beitrag der Arbeit ist genau diese Korrektur." },
    { q: "Warum nur 4 Geraete, kein Cross-Device-Test?", a: "Methodisch ehrliche Limitation. Aber: Hauptbefund (Informations-Asymmetrie) ist nicht geraet-spezifisch und auf 4 Geraeten bestaetigt." },
    { q: "Wieso Linear ~ Google?", a: "p=0.83 fuer C, p=0.55 fuer MAE. Drain-Rate ist das dominante Signal. Googles Hardware-Zugang bringt fuer 'Stunden bis 0%' keinen Mehrwert." },
    { q: "Was tun fuer Folgestudien?", a: "Leave-One-Device-Out, kontrollierte Vollentlade-Zyklen, Multi-Device-Sweep ueber N>=5 Geraete." },
  ];
  qa.forEach((p, i) => {
    const y = 1.5 + i * 0.85;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y, w: 0.08, h: 0.75, fill: { color: COL.primary }, line: { type: "none" },
    });
    s.addText("F: " + p.q, {
      x: 0.75, y: y, w: 8.6, h: 0.3,
      fontSize: 12, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
    });
    s.addText("A: " + p.a, {
      x: 0.75, y: y + 0.3, w: 8.6, h: 0.45,
      fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top",
    });
  });

  addFooter(s);
  addPageNumber(s, 16, TOTAL);
}

// ============================================================
// Write
// ============================================================
pres.writeFile({ fileName: "Paper_Verteidigung.pptx" }).then((file) => {
  console.log("Wrote: " + file);
});

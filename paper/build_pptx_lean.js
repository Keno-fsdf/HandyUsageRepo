// Lean-Version der Verteidigungs-Praesentation (Ziel: ~10 Folien, 10 Minuten frei sprechbar)
// Output: Paper_Verteidigung_Kurz.pptx   (das ausfuehrliche build_pptx.js bleibt als Backup)
// Aufruf: node build_pptx_lean.js

const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Keno Schürger";
pres.title = "TinyML für Akkulaufzeit-Vorhersage - Kurzfassung";

const COL = {
  primary: "0F3460", secondary: "16213E", bg: "FFFFFF", bgDark: "0F1B2D",
  text: "1A1A1A", muted: "64748B", border: "E2E8F0",
  tinyml: "2196F3", rf: "9C27B0", mean: "9E9E9E", linear: "455A64",
  exp: "4CAF50", google: "FF9800", good: "27AE60", bad: "E94560",
};

const TOTAL = 10;

function addPageNumber(s, n) {
  s.addText(`${n} / ${TOTAL}`, { x: 9.0, y: 5.3, w: 0.9, h: 0.25,
    fontSize: 9, color: COL.muted, align: "right", fontFace: "Calibri" });
}
function addFooter(s) {
  s.addText("K. Schürger - TinyML für Akkulaufzeit-Vorhersage", { x: 0.5, y: 5.3, w: 7, h: 0.25,
    fontSize: 9, color: COL.muted, fontFace: "Calibri" });
}
function slideTitle(s, t) {
  s.addText(t, { x: 0.5, y: 0.30, w: 9, h: 0.65, fontSize: 28, bold: true,
    color: COL.primary, fontFace: "Calibri", margin: 0 });
}

// ============================================================
// SLIDE 1 - Titel + Haken
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };
  s.addText("App-Level TinyML für", { x: 0.6, y: 1.5, w: 8.8, h: 0.7,
    fontSize: 36, bold: true, color: "FFFFFF", fontFace: "Calibri" });
  s.addText("Akkulaufzeit-Vorhersage auf Android", { x: 0.6, y: 2.2, w: 8.8, h: 0.7,
    fontSize: 36, bold: true, color: "FFFFFF", fontFace: "Calibri" });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 3.05, w: 1.4, h: 0.06, fill: { color: COL.bad }, line: { type: "none" } });
  s.addText("Multi-Device-Vergleich von sechs Methoden", { x: 0.6, y: 3.2, w: 8.8, h: 0.45,
    fontSize: 16, italic: true, color: "CADCFC", fontFace: "Calibri" });
  s.addText([
    { text: "Keno Schürger", options: { bold: true, breakLine: true } },
    { text: "Matrikelnr.: 5023033", options: { color: "9CB4DE", breakLine: true } },
    { text: "Technische Hochschule Würzburg-Schweinfurt (THWS)", options: { color: "9CB4DE", breakLine: true } },
    { text: "Vertiefungsseminar - Sommersemester 2026", options: { color: "9CB4DE" } },
  ], { x: 0.6, y: 4.05, w: 8.8, h: 1.25, fontSize: 14, color: "FFFFFF", fontFace: "Calibri" });
  s.addText("1 / " + TOTAL, { x: 9.0, y: 5.3, w: 0.9, h: 0.25, fontSize: 9, color: "9CB4DE", align: "right", fontFace: "Calibri" });
}

// ============================================================
// SLIDE 2 - Motivation + Forschungsfrage (zusammengelegt)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Motivation und Forschungsfrage");

  s.addText([
    { text: "Die Akku-Restzeit-Anzeige im System ist oft unzuverlässig (rechnet grob den Schnitt hoch).", options: { bullet: true, breakLine: true } },
    { text: "Seit Android 12 gibt es ein eigenes ML-Modell im System, aber nur mit privilegiertem Zugriff. Normale Apps kommen da nicht ran.", options: { bullet: true } },
  ], { x: 0.5, y: 1.15, w: 9, h: 1.1, fontSize: 14, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 6 });

  // Forschungsfrage-Box
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 2.6, w: 0.08, h: 1.5, fill: { color: COL.primary }, line: { type: "none" } });
  s.addText('"Wie gut kann ein TinyML-Modell die Akkulaufzeit auf Android vorhersagen, im Vergleich zu linearem und exponentiellem Fitting sowie der nativen Google-API, bezogen auf Genauigkeit und Effizienz?"',
    { x: 0.85, y: 2.6, w: 8.6, h: 1.5, fontSize: 19, italic: true, color: COL.secondary, fontFace: "Calibri", valign: "top" });

  s.addText("Gemessen an zwei Achsen:  Genauigkeit (C-Index, MAE)  und  Effizienz (Modellgröße, Latenz).",
    { x: 0.85, y: 4.25, w: 8.6, h: 0.4, fontSize: 13, color: COL.muted, fontFace: "Calibri" });

  addFooter(s); addPageNumber(s, 2);
}

// ============================================================
// SLIDE 3 - Verwandte Arbeiten (zwei prominent, zwei klein)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Verwandte Arbeiten");

  const main = [
    { x: 0.5, head: "Li et al. (2018)", sub: "Smartphone Battery Prediction at Scale",
      body: "51 Nutzer, 21 Monate. Führt den Concordance-Index als Metrik ein, weil Nutzer fast nie auf 0% entladen und MAE dann unzuverlässig wird. Der C-Index stammt aus der Medizin.",
      col: COL.primary },
    { x: 5.1, head: "Albelali & Ahmed (2025)", sub: "Hidden Leaks in Time Series Forecasting",
      body: "Zufälliges Mischen von Sliding-Window-Sequenzen leckt Zukunfts-Information ins Training und schönt die Ergebnisse.",
      col: COL.bad },
  ];
  main.forEach((w) => {
    s.addShape(pres.shapes.RECTANGLE, { x: w.x, y: 1.4, w: 4.4, h: 3.2, fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 },
      shadow: { type: "outer", color: "000000", blur: 6, offset: 1, angle: 135, opacity: 0.07 } });
    s.addShape(pres.shapes.RECTANGLE, { x: w.x, y: 1.4, w: 0.1, h: 3.2, fill: { color: w.col }, line: { type: "none" } });
    s.addText(w.head, { x: w.x + 0.25, y: 1.65, w: 4.0, h: 0.4, fontSize: 18, bold: true, color: w.col, fontFace: "Calibri", margin: 0 });
    s.addText(w.sub, { x: w.x + 0.25, y: 2.12, w: 4.0, h: 0.3, fontSize: 12.5, italic: true, color: COL.muted, fontFace: "Calibri", margin: 0 });
    s.addText(w.body, { x: w.x + 0.25, y: 2.6, w: 4.0, h: 1.85, fontSize: 13.5, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top" });
  });

  addFooter(s); addPageNumber(s, 3);
}

// ============================================================
// SLIDE 4 - Datensammlung (schlank: Stat-Kacheln + Features)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Datensammlung: 4 Geräte, 45 Tage");

  const stats = [
    { val: "66.001", lbl: "Messungen" }, { val: "4", lbl: "Geräte" },
    { val: "45 Tage", lbl: "Zeitraum" }, { val: "180", lbl: "Sessions" },
  ];
  stats.forEach((st, i) => {
    const x = 0.5 + i * 2.3;
    s.addShape(pres.shapes.RECTANGLE, { x: x, y: 1.2, w: 2.05, h: 1.1, fill: { color: COL.primary }, line: { type: "none" } });
    s.addText(st.val, { x: x, y: 1.25, w: 2.05, h: 0.6, fontSize: 26, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(st.lbl, { x: x, y: 1.83, w: 2.05, h: 0.4, fontSize: 12, color: "CADCFC", align: "center", fontFace: "Calibri", margin: 0 });
  });

  s.addText([
    { text: "Eigener Xiaomi plus drei Pixel-Geräte (7, 8, 9 Pro), bei Familienmitgliedern.", options: { bullet: true, breakLine: true } },
    { text: "Alle 30 Sekunden ein Messpunkt, im Hintergrund über einen Foreground-Service.", options: { bullet: true } },
  ], { x: 0.5, y: 2.7, w: 5.6, h: 1.2, fontSize: 13, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 6 });

  s.addShape(pres.shapes.RECTANGLE, { x: 6.4, y: 2.7, w: 3.1, h: 2.3, fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 } });
  s.addText("10 Features (nur öffentliche Sensoren)", { x: 6.55, y: 2.8, w: 2.8, h: 0.5, fontSize: 12, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0, valign: "top" });
  s.addText([
    { text: "battery_level, screen_on,", options: { breakLine: true } },
    { text: "brightness, active_app_category,", options: { breakLine: true } },
    { text: "wifi_on, mobile_data_on,", options: { breakLine: true } },
    { text: "charging, cpu_usage (proxy),", options: { breakLine: true } },
    { text: "temperature, hotspot_on", options: {} },
  ], { x: 6.55, y: 3.35, w: 2.85, h: 1.55, fontSize: 10, color: COL.text, fontFace: "Consolas", margin: 0, valign: "top" });

  addFooter(s); addPageNumber(s, 4);
}

// ============================================================
// SLIDE 5 - Sechs Methoden
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Sechs Methoden im Vergleich");

  const methods = [
    { name: "TinyML Conv1D", desc: "Eigenes Modell, 14 KB INT8", role: "Hauptmodell", col: COL.tinyml },
    { name: "Random Forest", desc: "200 Trees, gleiche Features", role: "Sanity-Check", col: COL.rf },
    { name: "Mean Predictor", desc: "Konstanter Mittelwert", role: "Floor (kein Lernen)", col: COL.mean },
    { name: "Linear Baseline", desc: "Akku / aktuelle Drain-Rate", role: "Analytisch 1", col: COL.linear },
    { name: "Exponential Fit", desc: "Kurvenfit pro Segment", role: "Analytisch 2", col: COL.exp },
    { name: "Google API", desc: "getBatteryDischargePrediction", role: "State of the Art", col: COL.google },
  ];
  methods.forEach((m, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.5 + col * 3.05, y = 1.25 + row * 1.85;
    s.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: 2.9, h: 1.6, fill: { color: "FFFFFF" }, line: { color: COL.border, width: 1 },
      shadow: { type: "outer", color: "000000", blur: 6, offset: 1, angle: 135, opacity: 0.06 } });
    s.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: 2.9, h: 0.08, fill: { color: m.col }, line: { type: "none" } });
    s.addText(m.name, { x: x + 0.15, y: y + 0.15, w: 2.6, h: 0.35, fontSize: 14, bold: true, color: m.col, fontFace: "Calibri", margin: 0 });
    s.addText(m.desc, { x: x + 0.15, y: y + 0.52, w: 2.6, h: 0.5, fontSize: 11, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top" });
    s.addText(m.role, { x: x + 0.15, y: y + 1.18, w: 2.6, h: 0.3, fontSize: 10, italic: true, color: COL.muted, fontFace: "Calibri", margin: 0 });
  });

  addFooter(s); addPageNumber(s, 5);
}

// ============================================================
// SLIDE 7 - Ergebnis: 6-Wege-Vergleich + Signifikanz
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Ergebnis: 6-Wege-Vergleich");

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.05, w: 9, h: 0.32, fill: { color: "F0F4F8" }, line: { color: COL.border, width: 0.5 } });
  s.addText("C-Index: bewertet nur ob die Reihenfolge stimmt (0,5 = Münzwurf, 1,0 = perfekt). MAE: durchschnittliche Abweichung in Stunden.",
    { x: 0.7, y: 1.07, w: 8.6, h: 0.28, fontSize: 10, italic: true, color: COL.secondary, fontFace: "Calibri", margin: 0, valign: "middle" });

  const tableData = [
    [
      { text: "Methode", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "MAE (h)", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "C-Index 95%-CI", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
      { text: "Acc +/- 2h", options: { bold: true, color: "FFFFFF", fill: { color: COL.primary } } },
    ],
    [{ text: "Mean Predictor (floor)", options: { color: COL.mean } }, "6.52", { text: "0.500 [0.500, 0.500]", options: { color: COL.mean } }, "21.5%"],
    [{ text: "TinyML Conv1D", options: { color: COL.tinyml, bold: true } }, "4.60", { text: "0.656 [0.647, 0.664]", options: { bold: true } }, "43.7%"],
    [{ text: "Random Forest", options: { color: COL.rf, bold: true } }, "4.06", { text: "0.685 [0.673, 0.695]", options: { bold: true } }, "46.4%"],
    [{ text: "Linear (drain rate)", options: { color: COL.linear } }, { text: "3.30", options: { bold: true } }, { text: "0.770 [0.761, 0.780]", options: { bold: true, color: COL.good } }, "57.3%"],
    [{ text: "Exponential fit", options: { color: COL.exp } }, "3.63", "0.767 [0.758, 0.776]", "59.0%"],
    [{ text: "Google API", options: { color: COL.google, bold: true } }, "3.37", "0.762 [0.751, 0.772]", "59.0%"],
  ];
  s.addTable(tableData, { x: 0.5, y: 1.5, w: 9, colW: [3.0, 1.5, 3.0, 1.5], fontSize: 12, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: COL.border } });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.35, w: 9, h: 0.8, fill: { color: "FFF5F5" }, line: { color: COL.bad, width: 1 } });
  s.addText([
    { text: "Beide ML-Modelle signifikant über dem Floor (p < 0,001), aber unter der Spitzengruppe. ", options: {} },
    { text: "Überraschend: Google ist statistisch nicht besser als die simple Linear-Baseline (p = 0,11).", options: { bold: true, color: COL.bad } },
  ], { x: 0.7, y: 4.42, w: 8.6, h: 0.66, fontSize: 12.5, color: COL.text, fontFace: "Calibri", margin: 0, valign: "middle" });

  addFooter(s); addPageNumber(s, 6);
}

// ============================================================
// SLIDE 8 - Per-Device (Hardware-Effekt)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Per-Device: starker Hardware-Effekt");

  s.addChart(pres.charts.BAR, [
    { name: "TinyML", labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"], values: [0.754, 0.742, 0.571, 0.593] },
    { name: "Random Forest", labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"], values: [0.807, 0.815, 0.767, 0.628] },
    { name: "Linear", labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"], values: [0.792, 0.696, 0.730, 0.724] },
    { name: "Google API", labels: ["Pixel 7 Pro", "Pixel 8 Pro", "Pixel 9 Pro XL", "Xiaomi"], values: [0.853, 0.921, 0.677, 0.473] },
  ], {
    x: 0.5, y: 1.5, w: 5.8, h: 3.5, barDir: "col",
    chartColors: [COL.tinyml, COL.rf, COL.linear, COL.google],
    catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
    showLegend: true, legendPos: "b", legendFontSize: 10,
    valAxisMinVal: 0.4, valAxisMaxVal: 1.0, showValue: false,
    valGridLine: { color: COL.border, size: 0.5 }, catGridLine: { style: "none" },
    chartArea: { fill: { color: "FFFFFF" } },
    title: "C-Index nach Gerät", showTitle: true, titleFontSize: 12, titleColor: COL.primary,
  });

  s.addText("Beobachtungen", { x: 6.5, y: 1.55, w: 3, h: 0.35, fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri" });
  s.addText([
    { text: "Dasselbe TinyML: 0.75 (Pixel 7 Pro) bis 0.59 (Xiaomi)", options: { bullet: true, breakLine: true } },
    { text: "Analytische Baselines stabiler über Geräte", options: { bullet: true, breakLine: true } },
    { text: "Praktisch: Konfidenz sollte gerätespezifisch sein", options: { bullet: true } },
  ], { x: 6.5, y: 1.95, w: 3, h: 3.0, fontSize: 11.5, color: COL.text, fontFace: "Calibri", paraSpaceAfter: 6 });

  addFooter(s); addPageNumber(s, 7);
}

// ============================================================
// SLIDE 9 - Effizienz
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Effizienz: TinyML funktioniert");

  const stats = [
    { val: "14.4", unit: "KB", lbl: "INT8 Modell", col: COL.tinyml },
    { val: "3.3", unit: "µs", lbl: "Inferenz-Latenz", col: COL.exp },
    { val: "7.6x", unit: "", lbl: "kleiner als das Original-Modell", col: COL.google },
    { val: "~12.000x", unit: "", lbl: "schneller als das Original", col: COL.rf },
  ];
  stats.forEach((st, i) => {
    const x = 0.5 + i * 2.3;
    s.addShape(pres.shapes.RECTANGLE, { x: x, y: 1.25, w: 2.05, h: 1.4, fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x: x, y: 1.25, w: 2.05, h: 0.08, fill: { color: st.col }, line: { type: "none" } });
    s.addText([{ text: st.val, options: { fontSize: 28, bold: true, color: st.col } }, { text: " " + st.unit, options: { fontSize: 15, color: st.col } }],
      { x: x, y: 1.42, w: 2.05, h: 0.65, align: "center", fontFace: "Calibri", margin: 0, valign: "middle" });
    s.addText(st.lbl, { x: x + 0.05, y: 2.1, w: 1.95, h: 0.5, fontSize: 11, color: COL.text, align: "center", fontFace: "Calibri", margin: 0, valign: "top" });
  });

  s.addText("Original-Modell = unquantisierte Float32-Version (109 KB, 39 ms).",
    { x: 0.5, y: 2.75, w: 9, h: 0.3, fontSize: 11, italic: true, color: COL.muted, fontFace: "Calibri", align: "center" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.1, w: 9, h: 1.1, fill: { color: "EDF7EE" }, line: { color: COL.good, width: 1 } });
  s.addText("Take-away", { x: 0.7, y: 3.2, w: 8.6, h: 0.3, fontSize: 13, bold: true, color: COL.good, fontFace: "Calibri", margin: 0 });
  s.addText("Die Quantisierung funktioniert wie beworben. Effizienz ist die klare Stärke von TinyML. Der Engpass liegt allein bei der Genauigkeit.",
    { x: 0.7, y: 3.55, w: 8.6, h: 0.6, fontSize: 13, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top" });

  addFooter(s); addPageNumber(s, 8);
}

// ============================================================
// SLIDE 9 - Kernbefunde (drei Verdikt-Zeilen)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Kernbefunde");

  const rows = [
    { y: 1.35, col: COL.bad, axis: "Genauigkeit", verdict: "TinyML unterlegen",
      detail: "Bleibt unter Linear, Exponential und Google (C ~ 0,77). Google ist nicht besser als die simple Linear-Baseline." },
    { y: 2.45, col: COL.good, axis: "Effizienz", verdict: "TinyML überlegen",
      detail: "14,4 KB, 3,3 Mikrosekunden, läuft offline. Hier hat TinyML klar seinen Wert." },
    { y: 3.55, col: COL.google, axis: "Hardware", verdict: "stark geräteabhängig",
      detail: "C-Index 0,75 auf Pixel 7 Pro gegen 0,59 auf Xiaomi (gleiches Modell, anderes Gerät)." },
  ];
  rows.forEach((r) => {
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: r.y, w: 9, h: 0.9, fill: { color: "F8FAFC" }, line: { color: COL.border, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: r.y, w: 0.1, h: 0.9, fill: { color: r.col }, line: { type: "none" } });
    s.addText([
      { text: r.axis + "    ", options: { bold: true, color: COL.primary } },
      { text: r.verdict, options: { bold: true, color: r.col } },
    ], { x: 0.78, y: r.y + 0.13, w: 8.5, h: 0.35, fontSize: 16, fontFace: "Calibri", margin: 0 });
    s.addText(r.detail, { x: 0.78, y: r.y + 0.49, w: 8.5, h: 0.4, fontSize: 12.5, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top" });
  });

  s.addText("Grenzen: Handy nie ganz leer, nur 4 Geräte.",
    { x: 0.5, y: 4.7, w: 9, h: 0.4, fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri", align: "center" });

  addFooter(s); addPageNumber(s, 9);
}

// ============================================================
// SLIDE 11 - Antwort auf die Forschungsfrage + Dank
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bg };
  slideTitle(s, "Antwort auf die Forschungsfrage");

  s.addText("Wie gut sagt ein App-Level-TinyML-Modell die Akkulaufzeit vorher, verglichen mit etablierten Methoden und der Google-API?",
    { x: 0.5, y: 1.05, w: 9, h: 0.5, fontSize: 13, italic: true, color: COL.muted, fontFace: "Calibri" });

  // Genauigkeit
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.65, w: 9, h: 1.25, fill: { color: "FFF5F5" }, line: { color: COL.bad, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.65, w: 0.1, h: 1.25, fill: { color: COL.bad }, line: { type: "none" } });
  s.addText("Genauigkeit: erreicht die etablierten Methoden nicht", { x: 0.75, y: 1.75, w: 8.5, h: 0.35, fontSize: 15, bold: true, color: COL.bad, fontFace: "Calibri", margin: 0 });
  s.addText("TinyML lernt Signal über dem Floor, bleibt aber hinter Linear, Exponential und Google (C ~ 0.77). Und Google ist nicht besser als die simple Linear-Baseline.",
    { x: 0.75, y: 2.15, w: 8.5, h: 0.7, fontSize: 13, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top" });

  // Effizienz
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.05, w: 9, h: 1.0, fill: { color: "EDF7EE" }, line: { color: COL.good, width: 1 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.05, w: 0.1, h: 1.0, fill: { color: COL.good }, line: { type: "none" } });
  s.addText("Effizienz: hier ist TinyML klar überlegen", { x: 0.75, y: 3.15, w: 8.5, h: 0.35, fontSize: 15, bold: true, color: COL.good, fontFace: "Calibri", margin: 0 });
  s.addText("14,4 KB, 3,3 Mikrosekunden Inferenz, läuft komplett offline auf jedem Android-Gerät.",
    { x: 0.75, y: 3.55, w: 8.5, h: 0.45, fontSize: 13, color: COL.text, fontFace: "Calibri", margin: 0, valign: "top" });

  s.addText("Vielen Dank. Fragen?", { x: 0.5, y: 4.55, w: 9, h: 0.4, fontSize: 18, bold: true, color: COL.primary, fontFace: "Calibri", align: "center" });

  addFooter(s); addPageNumber(s, 10);
}

pres.writeFile({ fileName: "Paper_Verteidigung_Kurz.pptx" }).then((f) => console.log("Wrote: " + f));

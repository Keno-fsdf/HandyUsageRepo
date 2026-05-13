// Kurzreferat-Praesentation fuer Vertiefung I (Portfolio):
// "TinyML fuer Akkulaufzeit-Vorhersage auf Android"
//
// Zielgruppe: BWI / E-Commerce Mitstudierende mit leichtem Info-Hintergrund
// Output: portfolio/Portfolio_Kurzreferat.pptx
//
// Aufruf: node build_kurzreferat.js

const pptxgen = require("../paper/node_modules/pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "Keno Schuerger";
pres.title = "Akkuvorhersage mit TinyML - Kurzreferat Vertiefung I";

// ============================================================
// Farbpalette (THWS-naehe, etwas freundlicher als Paper-Defense)
// ============================================================
const COL = {
  primary: "0F3460",       // deep navy
  thws: "F6821E",          // THWS-Orange
  bg: "FFFFFF",
  bgDark: "0F1B2D",
  bgSoft: "F8FAFC",
  text: "1A1A1A",
  muted: "64748B",
  border: "E2E8F0",
  // Methode-Farben
  tinyml: "2196F3",
  rf: "9C27B0",
  mean: "9E9E9E",
  linear: "455A64",
  exp: "4CAF50",
  google: "FF9800",
  good: "27AE60",
  bad: "E94560",
};

const IMG_LOGO  = path.join(__dirname, "Thws-logo_English.png");
const IMG_START = path.join(__dirname, "screenshot_app_start.jpg");
const IMG_PRED  = path.join(__dirname, "screenshot_app_prediction.jpg");
const IMG_TRAIN = path.join(__dirname, "..", "reports", "figures", "training_curves.png");
const IMG_CUM   = path.join(__dirname, "..", "reports", "figures", "cumulative_error.png");

const TOTAL = 22;

// ============================================================
// Helpers
// ============================================================
function addPageNumber(slide, n) {
  slide.addText(`${n} / ${TOTAL}`, {
    x: 9.0, y: 5.3, w: 0.9, h: 0.25,
    fontSize: 9, color: COL.muted, align: "right", fontFace: "Calibri",
  });
}
function addFooter(slide) {
  slide.addText("Keno Schuerger - Vertiefung I - Akkuvorhersage mit TinyML", {
    x: 0.5, y: 5.3, w: 7, h: 0.25,
    fontSize: 9, color: COL.muted, fontFace: "Calibri",
  });
}
function slideTitle(slide, title, sub) {
  slide.addText(title, {
    x: 0.5, y: 0.30, w: 9, h: 0.55,
    fontSize: 28, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });
  // Orange Akzentlinie unter dem Titel
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.92, w: 0.6, h: 0.05,
    fill: { color: COL.thws }, line: { type: "none" },
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.5, y: 1.0, w: 9, h: 0.35,
      fontSize: 13, italic: true, color: COL.muted, fontFace: "Calibri",
    });
  }
}
function chrome(slide, n) {
  slide.background = { color: COL.bg };
  addFooter(slide);
  addPageNumber(slide, n);
}

// ============================================================
// SLIDE 1 - Titelseite
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  // THWS-Logo unten links
  s.addImage({ path: IMG_LOGO, x: 0.5, y: 4.7, w: 1.4, h: 0.7 });

  s.addText("Wie lange haelt mein Akku noch?", {
    x: 0.6, y: 1.2, w: 8.8, h: 0.7,
    fontSize: 34, bold: true, color: "FFFFFF", fontFace: "Calibri",
  });
  s.addText("Ein eigenes TinyML-Modell auf dem Smartphone", {
    x: 0.6, y: 1.95, w: 8.8, h: 0.55,
    fontSize: 22, color: "CADCFC", fontFace: "Calibri",
  });

  // Akzent
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 2.65, w: 1.4, h: 0.06,
    fill: { color: COL.thws }, line: { type: "none" },
  });

  s.addText([
    { text: "Vertiefung I: Mobile und Ubiquitaere Anwendungen", options: { color: "9CB4DE", breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Keno Schuerger", options: { bold: true, fontSize: 18, breakLine: true } },
    { text: "Matrikelnummer 5023033 - BWI", options: { color: "9CB4DE", breakLine: true } },
    { text: "SoSe 2026 - Prof. Dr. Huffstadt / Prof. Dr. John", options: { color: "9CB4DE" } },
  ], {
    x: 0.6, y: 2.9, w: 8.8, h: 2.0,
    fontSize: 14, color: "FFFFFF", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 2 - Das Problem im Alltag (Hook)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 2);
  slideTitle(s, "Kennt ihr das?", "Akku-Anzeige zwischen Wunsch und Wirklichkeit");

  // Zwei Phasen-Boxen
  const phases = [
    { x: 0.6, t: "30%", sub: '"noch 4 Stunden"',  color: COL.good },
    { x: 5.1, t: "15%", sub: '"noch 1 Stunde"',   color: COL.bad },
  ];
  phases.forEach((p) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: p.x, y: 1.7, w: 4.3, h: 2.4,
      fill: { color: COL.bgSoft },
      line: { color: COL.border, width: 1 },
      rectRadius: 0.1,
    });
    s.addText(p.t, {
      x: p.x, y: 1.85, w: 4.3, h: 0.9,
      fontSize: 48, bold: true, color: p.color, align: "center", fontFace: "Calibri",
    });
    s.addText(p.sub, {
      x: p.x, y: 2.8, w: 4.3, h: 0.5,
      fontSize: 18, italic: true, color: COL.text, align: "center", fontFace: "Calibri",
    });
  });
  // Pfeil zwischen den Phasen
  s.addText(">", {
    x: 4.5, y: 2.5, w: 0.6, h: 0.8,
    fontSize: 36, bold: true, color: COL.thws, align: "center", fontFace: "Calibri",
  });
  s.addText("ein YouTube-Video spaeter ...", {
    x: 0.6, y: 3.7, w: 8.8, h: 0.4,
    fontSize: 13, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });

  s.addText("Die einfache Hochrechnung 'Verbrauch der letzten Stunden -> Zukunft' funktioniert nicht, sobald sich das Nutzungsverhalten aendert.", {
    x: 0.6, y: 4.3, w: 8.8, h: 0.6,
    fontSize: 14, color: COL.text, fontFace: "Calibri", align: "center",
  });
}

// ============================================================
// SLIDE 3 - Warum ist das ueberhaupt schwer?
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 3);
  slideTitle(s, "Warum ist das schwer?", "Vom Akku-Verbrauch haengen viele Dinge gleichzeitig ab");

  const factors = [
    { icon: "App",        text: "Welche App laeuft? Spotify zieht weniger als TikTok." },
    { icon: "Bildschirm", text: "Helligkeit + an/aus ist der groesste Einzel-Verbraucher." },
    { icon: "CPU",        text: "Im Spiel laeuft die CPU heiss - 5x mehr Verbrauch." },
    { icon: "Netz",       text: "Mobilfunk vs WLAN, schwacher Empfang kostet Energie." },
    { icon: "Temperatur", text: "Bei Kaelte sinkt die nutzbare Akku-Kapazitaet." },
    { icon: "Hotspot",    text: "Tethering verdoppelt schnell den Verbrauch." },
  ];
  const gridX = [0.6, 5.2];
  factors.forEach((f, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = gridX[col], y = 1.6 + row * 1.15;
    // Icon-Pill
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 1.4, h: 0.55, fill: { color: COL.thws },
      line: { type: "none" }, rectRadius: 0.08,
    });
    s.addText(f.icon, {
      x, y, w: 1.4, h: 0.55, fontSize: 14, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", fontFace: "Calibri",
    });
    s.addText(f.text, {
      x: x + 1.55, y: y + 0.04, w: 2.7, h: 0.5,
      fontSize: 12, color: COL.text, fontFace: "Calibri", valign: "middle",
    });
  });

  s.addText("Das ist genau die Art von Problem, fuer das sich Machine Learning eignet.", {
    x: 0.6, y: 4.8, w: 8.8, h: 0.4,
    fontSize: 14, italic: true, bold: true, color: COL.primary,
    align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 4 - Forschungsfrage
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 4);
  slideTitle(s, "Meine Forschungsfrage");

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.4, w: 0.08, h: 1.9, fill: { color: COL.thws }, line: { type: "none" },
  });
  s.addText('"Wie gut kann TinyML die Akkulaufzeit auf Android vorhersagen im Vergleich zu klassischen Berechnungs-Methoden und der nativen Google-API - bezogen auf Genauigkeit und Effizienz?"', {
    x: 0.85, y: 1.35, w: 8.6, h: 2.0,
    fontSize: 19, italic: true, color: COL.text, fontFace: "Calibri", valign: "top",
  });

  // Drei Aspekte
  const aspects = [
    { t: "Eigenes Modell", s: "Conv1D-Netz, on-device" },
    { t: "Vergleich",      s: "5 weitere Methoden + Google API" },
    { t: "Multi-Device",   s: "4 Geraete, 45 Tage" },
  ];
  aspects.forEach((a, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 3.8, w: 2.9, h: 1.1, fill: { color: COL.bgSoft },
      line: { color: COL.border, width: 1 }, rectRadius: 0.08,
    });
    s.addText(a.t, {
      x, y: 3.85, w: 2.9, h: 0.45,
      fontSize: 15, bold: true, color: COL.primary, align: "center", fontFace: "Calibri",
    });
    s.addText(a.s, {
      x, y: 4.3, w: 2.9, h: 0.5,
      fontSize: 12, color: COL.muted, align: "center", fontFace: "Calibri",
    });
  });
}

// ============================================================
// SLIDE 5 - Was Smartphones heute haben
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 5);
  slideTitle(s, "Was Android heute schon kann", "Google hat seit 2021 ein eigenes ML-Modell im System");

  // Code-aehnliche Box
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 1.6, w: 8.8, h: 1.0,
    fill: { color: "0F1B2D" }, line: { type: "none" }, rectRadius: 0.08,
  });
  s.addText("PowerManager.getBatteryDischargePrediction()", {
    x: 0.8, y: 1.7, w: 8.6, h: 0.45,
    fontSize: 16, color: "92DCE5", fontFace: "Consolas", bold: true,
  });
  s.addText("// gibt die geschaetzte Restzeit zurueck - seit Android 12 (API 31)", {
    x: 0.8, y: 2.15, w: 8.6, h: 0.35,
    fontSize: 12, color: "9CB4DE", fontFace: "Consolas",
  });

  // Aber-Box
  s.addText("Aber:", {
    x: 0.6, y: 2.95, w: 1.2, h: 0.4,
    fontSize: 18, bold: true, color: COL.bad, fontFace: "Calibri",
  });
  const buts = [
    "Auf Pixel-Geraeten nutzt der Einstellungs-Screen den Wert. Sonst meist gar nicht sichtbar.",
    "Bei Xiaomi, Samsung, OnePlus etc. ist die API zwar verfuegbar - aber wenig erforscht.",
    "Niemand weiss oeffentlich, wie GUT diese Google-Vorhersage eigentlich ist.",
  ];
  buts.forEach((b, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.6, y: 3.45 + i * 0.5, w: 0.2, h: 0.35,
      fill: { color: COL.thws }, line: { type: "none" }, rectRadius: 0.04,
    });
    s.addText(b, {
      x: 0.95, y: 3.4 + i * 0.5, w: 8.5, h: 0.45,
      fontSize: 13, color: COL.text, fontFace: "Calibri", valign: "middle",
    });
  });
}

// ============================================================
// SLIDE 6 - Mein Plan
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 6);
  slideTitle(s, "Mein Plan", "Drei Bausteine, klare Schnittstellen");

  const steps = [
    { n: "1", t: "Eigene App", body: "Sammelt alle 30s Akku-Daten im Hintergrund. Laeuft auf Xiaomi + 3 Pixel-Geraeten." },
    { n: "2", t: "Eigenes ML-Modell", body: "Conv1D-Netz, am Laptop trainiert, dann ins Handy zurueck deployed. Klein genug fuer Smartphones." },
    { n: "3", t: "Fairer Vergleich", body: "Auf dem gleichen Test-Set messen, wer wirklich besser vorhersagt - mein Modell, einfache Berechnungen oder Google." },
  ];
  steps.forEach((step, i) => {
    const y = 1.4 + i * 1.25;
    // Nummer-Kreis
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y, w: 0.9, h: 0.9,
      fill: { color: COL.thws }, line: { type: "none" },
    });
    s.addText(step.n, {
      x: 0.6, y, w: 0.9, h: 0.9,
      fontSize: 32, bold: true, color: "FFFFFF",
      align: "center", valign: "middle", fontFace: "Calibri",
    });
    s.addText(step.t, {
      x: 1.7, y: y - 0.05, w: 7.7, h: 0.45,
      fontSize: 18, bold: true, color: COL.primary, fontFace: "Calibri",
    });
    s.addText(step.body, {
      x: 1.7, y: y + 0.35, w: 7.7, h: 0.6,
      fontSize: 13, color: COL.text, fontFace: "Calibri",
    });
  });
}

// ============================================================
// SLIDE 7 - Die App (Screenshots)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 7);
  slideTitle(s, "So sieht die App aus", "Zwei Zustaende: Aufwaermphase und aktive Vorhersage");

  // Linker Screenshot
  s.addImage({ path: IMG_START, x: 1.1, y: 1.4, w: 1.85, h: 3.7 });
  s.addText('"Sammle Daten ... (0/10)"', {
    x: 0.6, y: 5.1, w: 2.85, h: 0.25,
    fontSize: 11, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });

  // Rechter Screenshot
  s.addImage({ path: IMG_PRED, x: 4.5, y: 1.4, w: 1.85, h: 3.7 });
  s.addText('"Noch 13h 57min" bei 100% Akku', {
    x: 4.0, y: 5.1, w: 2.85, h: 0.25,
    fontSize: 11, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });

  // Erklaerungs-Block rechts
  s.addText("Was passiert hier?", {
    x: 7.0, y: 1.5, w: 2.7, h: 0.4,
    fontSize: 16, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "- Service laeuft im Hintergrund", options: { breakLine: true } },
    { text: "  (auch wenn App geschlossen)", options: { breakLine: true, color: COL.muted, fontSize: 10 } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "- Modell braucht erst 10 Datenpunkte", options: { breakLine: true } },
    { text: "  bevor es eine Vorhersage gibt", options: { breakLine: true, color: COL.muted, fontSize: 10 } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "- Danach alle 30s ein neuer Wert", options: { breakLine: true } },
    { text: "  (bzw. auf Knopfdruck)", options: { color: COL.muted, fontSize: 10 } },
  ], {
    x: 7.0, y: 2.0, w: 2.7, h: 3.2,
    fontSize: 12, color: COL.text, fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 8 - Architektur
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 8);
  slideTitle(s, "Wie haengt alles zusammen?", "Daten-Sammlung am Phone, Training am PC, Deployment zurueck aufs Phone");

  // Drei Bloecke
  const blocks = [
    { x: 0.5, t: "Android-App",  sub: "Daten sammeln", col: COL.tinyml,
      detail: ["10 Features", "alle 30s", "CSV-Export"] },
    { x: 3.7, t: "Python-Pipeline", sub: "Training & Auswertung", col: COL.thws,
      detail: ["Conv1D-Netz", "Quantisierung", "Eval-Stats"] },
    { x: 6.9, t: "Android-App",  sub: "Vorhersagen", col: COL.tinyml,
      detail: [".tflite-Modell", "on-device", "Notification"] },
  ];
  blocks.forEach((b) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: b.x, y: 1.7, w: 2.6, h: 2.3,
      fill: { color: COL.bgSoft },
      line: { color: b.col, width: 2 }, rectRadius: 0.1,
    });
    s.addText(b.t, {
      x: b.x, y: 1.85, w: 2.6, h: 0.4,
      fontSize: 16, bold: true, color: b.col, align: "center", fontFace: "Calibri",
    });
    s.addText(b.sub, {
      x: b.x, y: 2.25, w: 2.6, h: 0.35,
      fontSize: 12, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
    });
    s.addText(b.detail.map(d => "- " + d).join("\n"), {
      x: b.x + 0.3, y: 2.7, w: 2.0, h: 1.1,
      fontSize: 11, color: COL.text, fontFace: "Calibri",
    });
  });

  // Pfeile mit Beschriftung
  s.addShape(pres.shapes.RIGHT_ARROW, {
    x: 3.15, y: 2.65, w: 0.5, h: 0.4, fill: { color: COL.muted }, line: { type: "none" },
  });
  s.addText("CSV", { x: 3.0, y: 3.05, w: 0.8, h: 0.25, fontSize: 10, color: COL.muted, align: "center", fontFace: "Calibri" });
  s.addShape(pres.shapes.RIGHT_ARROW, {
    x: 6.35, y: 2.65, w: 0.5, h: 0.4, fill: { color: COL.muted }, line: { type: "none" },
  });
  s.addText(".tflite", { x: 6.2, y: 3.05, w: 0.8, h: 0.25, fontSize: 10, color: COL.muted, align: "center", fontFace: "Calibri" });

  s.addText("Klare Trennung: was am Handy passiert, bleibt am Handy. Trainingsdaten landen nur ueber expliziten Share-Intent am PC.", {
    x: 0.5, y: 4.5, w: 9, h: 0.6,
    fontSize: 13, italic: true, color: COL.text, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 9 - Daten-Sammlung: Was und Wie
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 9);
  slideTitle(s, "Was sammelt die App?", "10 Features alle 30 Sekunden - was eine normale App lesen darf");

  const features = [
    { g: "Akku",          items: ["Level (%)", "Temperatur (°C)", "Laedt ja/nein"] },
    { g: "Bildschirm",    items: ["An/aus", "Helligkeit"] },
    { g: "Verhalten",     items: ["Aktive App-Kategorie", "CPU-Auslastung"] },
    { g: "Konnektivitaet", items: ["WLAN ja/nein", "Mobilfunk ja/nein", "Hotspot ja/nein"] },
  ];
  features.forEach((f, i) => {
    const x = 0.6 + (i % 2) * 4.45;
    const y = 1.6 + Math.floor(i / 2) * 1.8;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 4.25, h: 1.6,
      fill: { color: COL.bgSoft }, line: { color: COL.border, width: 1 }, rectRadius: 0.08,
    });
    s.addText(f.g, {
      x: x + 0.15, y: y + 0.1, w: 4, h: 0.35,
      fontSize: 14, bold: true, color: COL.thws, fontFace: "Calibri",
    });
    s.addText(f.items.map(it => "- " + it).join("\n"), {
      x: x + 0.25, y: y + 0.5, w: 4, h: 1.0,
      fontSize: 12, color: COL.text, fontFace: "Calibri",
    });
  });

  s.addText("Bewusste Beschraenkung: nur Daten, die eine normale Drittanbieter-App ohne Spezial-Rechte sehen kann.", {
    x: 0.6, y: 5.05, w: 8.8, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 10 - MIUI killt deinen Service (Story)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 10);
  slideTitle(s, "Herausforderung Nr. 1", "Xiaomi-Phones killen Hintergrund-Apps - und das Modell konnte nicht messen");

  // Zeitlinie
  const events = [
    { t: "Tag 1", text: "App gestartet, Daten fliessen rein - perfekt." },
    { t: "Tag 2", text: "App aus der Uebersicht weggewischt - Service tot." },
    { t: "Tag 3", text: "Phone-Restart - Service kommt nicht mehr zurueck." },
    { t: "Loesung", text: "Foreground-Service + Alarm-Manager + Boot-Listener.", isFix: true },
  ];
  events.forEach((e, i) => {
    const y = 1.6 + i * 0.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.6, y, w: 1.4, h: 0.55,
      fill: { color: e.isFix ? COL.good : COL.muted },
      line: { type: "none" }, rectRadius: 0.06,
    });
    s.addText(e.t, {
      x: 0.6, y, w: 1.4, h: 0.55,
      fontSize: 13, bold: true, color: "FFFFFF",
      align: "center", valign: "middle", fontFace: "Calibri",
    });
    s.addText(e.text, {
      x: 2.15, y: y + 0.05, w: 7.3, h: 0.5,
      fontSize: 14, color: e.isFix ? COL.good : COL.text, bold: e.isFix,
      fontFace: "Calibri", valign: "middle",
    });
  });

  s.addText("Im Paper schoen, in der Praxis 18 Stunden Geraete-Tuning, bis es robust lief.", {
    x: 0.6, y: 5.0, w: 8.8, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 11 - Datensatz
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 11);
  slineTitleSafe(pres, s, "Der finale Datensatz", "Drei Pixel-Geraete von Mitstudis + mein Xiaomi");

  // Vier Geraete-Karten
  const phones = [
    { t: "Xiaomi 2107113SG", n: "38.087",  badge: "eigenes Geraet" },
    { t: "Pixel 7 Pro",       n: "16.919", badge: "Mitstudi" },
    { t: "Pixel 8 Pro",       n: "3.354",  badge: "Mitstudi" },
    { t: "Pixel 9 Pro XL",    n: "7.641",  badge: "Mitstudi" },
  ];
  phones.forEach((p, i) => {
    const x = 0.6 + i * 2.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.7, w: 2.05, h: 1.9,
      fill: { color: COL.bgSoft }, line: { color: COL.border, width: 1 }, rectRadius: 0.08,
    });
    s.addText(p.t, {
      x, y: 1.8, w: 2.05, h: 0.4,
      fontSize: 12, bold: true, color: COL.primary, align: "center", fontFace: "Calibri",
    });
    s.addText(p.n, {
      x, y: 2.2, w: 2.05, h: 0.65,
      fontSize: 26, bold: true, color: COL.thws, align: "center", fontFace: "Calibri",
    });
    s.addText("Messpunkte", {
      x, y: 2.9, w: 2.05, h: 0.3,
      fontSize: 10, color: COL.muted, align: "center", fontFace: "Calibri",
    });
    s.addText(p.badge, {
      x, y: 3.2, w: 2.05, h: 0.3,
      fontSize: 10, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
    });
  });

  // Summe
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 2.5, y: 4.0, w: 5.0, h: 1.0,
    fill: { color: COL.primary }, line: { type: "none" }, rectRadius: 0.08,
  });
  s.addText("66.001", {
    x: 2.5, y: 4.05, w: 5.0, h: 0.55,
    fontSize: 28, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri",
  });
  s.addText("Messpunkte ueber 45 Tage und 180 Sessions", {
    x: 2.5, y: 4.55, w: 5.0, h: 0.4,
    fontSize: 13, color: "CADCFC", align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 12 - Was ist TinyML?
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 12);
  slideTitle(s, "Was ist TinyML eigentlich?", "Machine Learning, das direkt auf kleinen Geraeten laeuft - ohne Cloud");

  // Vergleichs-Karten
  const compare = [
    { t: "Normales ML",  col: COL.muted,
      items: ["Modell ist mehrere 100 MB gross", "Laeuft auf GPU-Servern", "Cloud-Anfragen pro Vorhersage", "Latenz: 100-1000 ms"] },
    { t: "TinyML",       col: COL.thws,
      items: ["Modell unter 100 KB", "Laeuft auf CPU/MCU", "Direkt auf dem Geraet (offline)", "Latenz: Mikrosekunden"] },
  ];
  compare.forEach((c, i) => {
    const x = 0.6 + i * 4.45;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.6, w: 4.25, h: 2.9,
      fill: { color: COL.bgSoft }, line: { color: c.col, width: 2 }, rectRadius: 0.1,
    });
    s.addText(c.t, {
      x, y: 1.75, w: 4.25, h: 0.5,
      fontSize: 20, bold: true, color: c.col, align: "center", fontFace: "Calibri",
    });
    s.addText(c.items.map(it => "- " + it).join("\n\n"), {
      x: x + 0.25, y: 2.4, w: 4.0, h: 2.1,
      fontSize: 12, color: COL.text, fontFace: "Calibri",
    });
  });

  s.addText("Vorteile: kein Datenleak, keine Server-Kosten, funktioniert ohne Netz.", {
    x: 0.6, y: 4.75, w: 8.8, h: 0.35,
    fontSize: 13, italic: true, color: COL.primary, bold: true, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 13 - Quantisierung
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 13);
  slideTitle(s, "Wie wird das Modell so klein?", "Quantisierung: weniger Genauigkeit pro Gewicht, viel weniger Speicher");

  // Visualisierung Float32 -> INT8
  const variants = [
    { t: "Float32",  sub: "Original-Training", size: "109 KB",  bar: 8.0, col: COL.muted },
    { t: "Dynamic Range", sub: "Naive Kompression", size: "16 KB", bar: 1.2, col: COL.linear },
    { t: "Float16",  sub: "Halbe Genauigkeit", size: "17.8 KB", bar: 1.3, col: COL.exp },
    { t: "INT8",     sub: "Ganzzahlen, deployed", size: "14.4 KB", bar: 1.05, col: COL.thws },
  ];
  variants.forEach((v, i) => {
    const y = 1.5 + i * 0.85;
    s.addText(v.t, {
      x: 0.6, y, w: 1.6, h: 0.4,
      fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri", valign: "middle",
    });
    s.addText(v.sub, {
      x: 0.6, y: y + 0.35, w: 1.6, h: 0.3,
      fontSize: 10, color: COL.muted, fontFace: "Calibri",
    });
    // Bar
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 2.4, y: y + 0.1, w: v.bar, h: 0.45,
      fill: { color: v.col }, line: { type: "none" }, rectRadius: 0.04,
    });
    s.addText(v.size, {
      x: 2.5 + v.bar, y: y + 0.1, w: 1.3, h: 0.45,
      fontSize: 13, bold: true, color: COL.text, fontFace: "Calibri", valign: "middle",
    });
  });

  s.addText("Faktor 7-8x kleiner und 10.000x schneller als die Float32-Variante - bei vergleichbarer Genauigkeit.", {
    x: 0.6, y: 5.0, w: 8.8, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 14 - Training Curves
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 14);
  slideTitle(s, "Wie wurde trainiert?", "Standard-Pipeline am Laptop, ca. 20 Epochen mit Early Stopping");

  s.addImage({ path: IMG_TRAIN, x: 0.8, y: 1.5, w: 5.5, h: 3.4 });

  s.addText("Was hier passiert:", {
    x: 6.5, y: 1.5, w: 3.0, h: 0.4,
    fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "- Blau: Training-Fehler", options: { breakLine: true, color: "2196F3", bold: true } },
    { text: "- Orange: Validation-Fehler", options: { breakLine: true, color: "FF9800", bold: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Beide sinken, Validation-Fehler stoppt nach ~21 Epochen.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Hyperparameter wurden mit einer Konfig-Datei festgeschrieben - alles reproduzierbar.", options: { italic: true, color: COL.muted } },
  ], {
    x: 6.5, y: 2.0, w: 3.0, h: 3.0,
    fontSize: 11, color: COL.text, fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 15 - Methodischer Aha-Moment: Split-Strategie
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 15);
  slideTitle(s, "Der wichtigste Aha-Moment", "Wie man Daten teilt, entscheidet, ob das Ergebnis ehrlich ist");

  // Zwei Schemata nebeneinander
  const drawSplit = (x, title, label, color, sequences, badge, badgeColor) => {
    s.addText(title, {
      x, y: 1.4, w: 4.2, h: 0.4,
      fontSize: 16, bold: true, color: COL.primary, align: "center", fontFace: "Calibri",
    });
    s.addText(label, {
      x, y: 1.75, w: 4.2, h: 0.3,
      fontSize: 11, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
    });
    // 12 kleine Blocks
    for (let i = 0; i < 12; i++) {
      const col = sequences[i];
      const cx = x + 0.15 + (i % 6) * 0.66;
      const cy = 2.2 + Math.floor(i / 6) * 0.55;
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: 0.6, h: 0.45,
        fill: { color: col === "T" ? color : "CFD8DC" },
        line: { color: COL.border, width: 0.5 },
      });
    }
    // Badge
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x + 0.6, y: 3.6, w: 3.0, h: 0.55,
      fill: { color: badgeColor }, line: { type: "none" }, rectRadius: 0.06,
    });
    s.addText(badge, {
      x: x + 0.6, y: 3.6, w: 3.0, h: 0.55,
      fontSize: 13, bold: true, color: "FFFFFF",
      align: "center", valign: "middle", fontFace: "Calibri",
    });
  };

  // Random: Train/Test gemixt (T = Train, '_' = Test)
  drawSplit(0.5, "Random-Split (naiv)", "Sequenzen wild gemischt",
    COL.bad, ["T","T","_","T","_","T","T","_","T","T","_","T"],
    "Test-Fehler: 6.53h",  COL.bad);

  // Segment-Level: ganze Bloecke
  drawSplit(5.3, "Segment-Level-Split (sauber)", "Ganze Sitzungen getrennt",
    COL.good, ["T","T","T","T","T","T","T","T","_","_","_","_"],
    "Test-Fehler: 11.06h", COL.good);

  s.addText("Im naiven Fall sieht das Modell wegen Sliding-Windows Teile der Test-Daten schon im Training -> 'Cheating'.", {
    x: 0.5, y: 4.5, w: 9, h: 0.35,
    fontSize: 12, color: COL.text, align: "center", fontFace: "Calibri",
  });
  s.addText("Erst sauberer Split zeigt den ehrlichen Fehler - Faktor 1.69x hoeher. Das war der Wendepunkt der Arbeit.", {
    x: 0.5, y: 4.85, w: 9, h: 0.35,
    fontSize: 12, italic: true, bold: true, color: COL.primary, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 16 - Ergebnis-Tabelle
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 16);
  slideTitle(s, "Wer gewinnt nun?", "6 Methoden auf demselben Test-Set verglichen");

  const rows = [
    { m: "Mean Predictor (Floor)",      mae: "11.21h", cidx: "0.50", verdict: "Zufall", col: COL.mean },
    { m: "Linear-Baseline",              mae: "3.30h",  cidx: "0.77", verdict: "Solide", col: COL.linear },
    { m: "TinyML (mein Modell)",         mae: "4.60h",  cidx: "0.77", verdict: "Solide", col: COL.tinyml },
    { m: "Random Forest",                mae: "4.06h",  cidx: "0.77", verdict: "Solide", col: COL.rf },
    { m: "Exponential Fit",              mae: "3.63h",  cidx: "0.76", verdict: "Solide", col: COL.exp },
    { m: "Google API",                   mae: "3.37h",  cidx: "0.77", verdict: "Solide", col: COL.google },
  ];

  // Header
  s.addText("Methode",        { x: 0.6, y: 1.5, w: 3.7, h: 0.35, fontSize: 13, bold: true, color: COL.muted, fontFace: "Calibri" });
  s.addText("MAE (Fehler)",  { x: 4.3, y: 1.5, w: 1.7, h: 0.35, fontSize: 13, bold: true, color: COL.muted, fontFace: "Calibri", align: "center" });
  s.addText("Ranking-Score", { x: 6.0, y: 1.5, w: 1.8, h: 0.35, fontSize: 13, bold: true, color: COL.muted, fontFace: "Calibri", align: "center" });
  s.addText("Bewertung",      { x: 7.8, y: 1.5, w: 1.7, h: 0.35, fontSize: 13, bold: true, color: COL.muted, fontFace: "Calibri", align: "center" });
  s.addShape(pres.shapes.LINE, { x: 0.6, y: 1.88, w: 8.9, h: 0, line: { color: COL.border, width: 1 } });

  rows.forEach((r, i) => {
    const y = 2.0 + i * 0.43;
    // Method-Bullet
    s.addShape(pres.shapes.OVAL, { x: 0.62, y: y + 0.07, w: 0.18, h: 0.18, fill: { color: r.col }, line: { type: "none" } });
    s.addText(r.m, { x: 0.9, y, w: 3.4, h: 0.32, fontSize: 12, color: COL.text, fontFace: "Calibri", valign: "middle" });
    s.addText(r.mae, { x: 4.3, y, w: 1.7, h: 0.32, fontSize: 12, color: COL.text, fontFace: "Calibri", align: "center", valign: "middle" });
    s.addText(r.cidx, { x: 6.0, y, w: 1.8, h: 0.32, fontSize: 12, color: COL.text, fontFace: "Calibri", align: "center", valign: "middle" });
    s.addText(r.verdict, { x: 7.8, y, w: 1.7, h: 0.32, fontSize: 12, bold: true,
      color: r.verdict === "Zufall" ? COL.muted : COL.good,
      fontFace: "Calibri", align: "center", valign: "middle" });
  });

  s.addText("Ueberraschung: alle ernsthaften Methoden landen praktisch gleichauf. Auch die simple Linear-Berechnung schlaegt sich gegen Google API.", {
    x: 0.6, y: 4.7, w: 8.8, h: 0.55,
    fontSize: 12, italic: true, color: COL.primary, bold: true, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 17 - Per-Device-Effekt
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 17);
  slideTitle(s, "Pro Geraet betrachtet", "Die Hardware macht mehr Unterschied als das Modell");

  // Bar Chart (manuell)
  const devices = [
    { name: "Pixel 7 Pro",       c: 0.75, label: "0.75" },
    { name: "Pixel 8 Pro",       c: 0.74, label: "0.74" },
    { name: "Pixel 9 Pro XL",   c: 0.77, label: "0.77" },
    { name: "Xiaomi 2107113SG", c: 0.59, label: "0.59" },
  ];
  const baseY = 4.4, maxBar = 2.6;
  devices.forEach((d, i) => {
    const x = 1.0 + i * 2.0;
    const h = d.c * maxBar / 0.8;
    const col = d.c < 0.65 ? COL.bad : COL.good;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: baseY - h, w: 1.5, h,
      fill: { color: col }, line: { type: "none" },
    });
    s.addText(d.label, {
      x: x - 0.1, y: baseY - h - 0.35, w: 1.7, h: 0.3,
      fontSize: 14, bold: true, color: COL.text, align: "center", fontFace: "Calibri",
    });
    s.addText(d.name, {
      x: x - 0.25, y: baseY + 0.05, w: 2.0, h: 0.5,
      fontSize: 11, color: COL.text, align: "center", fontFace: "Calibri",
    });
  });

  // Erklaerung rechts
  s.addText("Warum?", {
    x: 0.6, y: 1.45, w: 8.8, h: 0.4,
    fontSize: 15, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText("Auf Xiaomi war der Akku 88.8% der Zeit ueber 75% - kaum Entlade-Dynamik zum Lernen. Auf Pixel wurde der Akku regelmaessig leergespielt.", {
    x: 0.6, y: 1.8, w: 8.8, h: 0.7,
    fontSize: 12, color: COL.text, fontFace: "Calibri",
  });
  s.addText("Das Modell ist nicht 'schlechter' auf Xiaomi - es hatte weniger zu lernen.", {
    x: 0.6, y: 2.55, w: 8.8, h: 0.4,
    fontSize: 12, italic: true, color: COL.muted, fontFace: "Calibri",
  });
  s.addText("Concordance Index (Ranking-Score, 0.5 = Zufall, 1.0 = perfekt)", {
    x: 0.6, y: 5.0, w: 8.8, h: 0.3,
    fontSize: 10, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 18 - Effizienz
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 18);
  slideTitle(s, "Was kostet das Modell?", "Klein, schnell und stromsparend genug fuer Dauerbetrieb");

  const stats = [
    { v: "14.4", u: "KB",  l: "Modell-Groesse", sub: "passt in einen E-Mail-Anhang" },
    { v: "5",    u: "µs",  l: "Inferenz-Zeit",  sub: "pro Vorhersage auf CPU" },
    { v: "10",   u: "k×",  l: "Speedup",         sub: "vs. Float32-Variante" },
    { v: "30",   u: "s",   l: "Update-Rate",    sub: "fuer Live-Anzeige" },
  ];
  stats.forEach((st, i) => {
    const x = 0.6 + i * 2.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.6, w: 2.05, h: 2.6,
      fill: { color: COL.bgSoft }, line: { color: COL.border, width: 1 }, rectRadius: 0.1,
    });
    s.addText(st.v, {
      x, y: 1.75, w: 2.05, h: 1.0,
      fontSize: 44, bold: true, color: COL.thws, align: "center", fontFace: "Calibri",
    });
    s.addText(st.u, {
      x, y: 2.7, w: 2.05, h: 0.4,
      fontSize: 16, color: COL.muted, align: "center", fontFace: "Calibri",
    });
    s.addText(st.l, {
      x, y: 3.15, w: 2.05, h: 0.35,
      fontSize: 13, bold: true, color: COL.primary, align: "center", fontFace: "Calibri",
    });
    s.addText(st.sub, {
      x, y: 3.5, w: 2.05, h: 0.55,
      fontSize: 10, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
    });
  });

  s.addText("Bei dieser Effizienz koennte die Vorhersage problemlos in jeder Akku-Anzeige laufen - quasi gratis.", {
    x: 0.6, y: 4.7, w: 8.8, h: 0.4,
    fontSize: 13, italic: true, color: COL.text, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 19 - Fehler-Verteilung
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 19);
  slideTitle(s, "Wie sicher sind die Vorhersagen?", "Kumulative Fehler-Verteilung der drei Hauptmethoden");

  s.addImage({ path: IMG_CUM, x: 0.7, y: 1.4, w: 5.6, h: 3.6 });

  s.addText("Wie liest man das?", {
    x: 6.5, y: 1.5, w: 3.0, h: 0.4,
    fontSize: 14, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "Je weiter links die Kurve,\nje besser die Methode.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Beispiel: 50% der TinyML-Vorhersagen liegen unter 2 Stunden Fehler.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Bei sehr langen Horizonten (> 30h) gewinnt die Google API.", options: { italic: true, color: COL.muted } },
  ], {
    x: 6.5, y: 1.95, w: 3.0, h: 3.0,
    fontSize: 11, color: COL.text, fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 20 - Lessons Learned
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 20);
  slideTitle(s, "Was ich mitnehme", "Drei Erkenntnisse, die ueber das Projekt hinausgehen");

  const lessons = [
    { title: "Android im Hintergrund ist hart.",
      body: "Foreground-Services sind theoretisch Standard - praktisch killt jeder Hersteller anders. Multi-Device-Test war Pflicht." },
    { title: "Methodische Disziplin > Modell-Komplexitaet.",
      body: "Der Wechsel vom naiven zum sauberen Train/Test-Split hatte mehr Wirkung als jedes Hyperparameter-Tuning." },
    { title: "Ehrliche Negativ-Ergebnisse sind wertvoll.",
      body: "Anfangs sah alles nach 'mein Modell gewinnt!' aus. Erst saubere Methodik zeigte: TinyML ist gleichauf mit einfacher Berechnung. Das ehrlich zu reporten ist wissenschaftlich richtig." },
  ];
  lessons.forEach((l, i) => {
    const y = 1.5 + i * 1.2;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: y + 0.05, w: 0.12, h: 1.0,
      fill: { color: COL.thws }, line: { type: "none" },
    });
    s.addText(l.title, {
      x: 0.9, y, w: 8.5, h: 0.45,
      fontSize: 16, bold: true, color: COL.primary, fontFace: "Calibri",
    });
    s.addText(l.body, {
      x: 0.9, y: y + 0.45, w: 8.5, h: 0.7,
      fontSize: 12, color: COL.text, fontFace: "Calibri",
    });
  });
}

// ============================================================
// SLIDE 21 - Repository / Demo
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 21);
  slideTitle(s, "Alles offen", "Code, Daten, Pipeline auf GitHub");

  // Repo-URL Box
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 1.0, y: 1.7, w: 8.0, h: 0.9,
    fill: { color: "0F1B2D" }, line: { type: "none" }, rectRadius: 0.08,
  });
  s.addText("github.com/Keno-fsdf/HandyUsageRepo", {
    x: 1.0, y: 1.7, w: 8.0, h: 0.9,
    fontSize: 22, bold: true, color: "92DCE5", fontFace: "Consolas",
    align: "center", valign: "middle",
  });

  const what = [
    { t: "Android-App", d: "Kotlin-Source + APK fuer Demo" },
    { t: "Python-Pipeline", d: "python run_pipeline.py reproduziert alles" },
    { t: "Datensatz",      d: "66.001 Messpunkte als CSV im Repo" },
    { t: "Paper + Portfolio", d: "Beide als PDF + LaTeX-Source" },
  ];
  what.forEach((w, i) => {
    const x = 0.6 + (i % 2) * 4.45;
    const y = 3.0 + Math.floor(i / 2) * 1.0;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 4.25, h: 0.85,
      fill: { color: COL.bgSoft }, line: { color: COL.border, width: 1 }, rectRadius: 0.06,
    });
    s.addText(w.t, {
      x: x + 0.2, y: y + 0.08, w: 4.0, h: 0.35,
      fontSize: 14, bold: true, color: COL.thws, fontFace: "Calibri",
    });
    s.addText(w.d, {
      x: x + 0.2, y: y + 0.43, w: 4.0, h: 0.35,
      fontSize: 11, color: COL.text, fontFace: "Calibri",
    });
  });

  s.addText("Auf dem Handy: APK installierbar, Datensammlung sofort startbar.", {
    x: 0.6, y: 5.0, w: 8.8, h: 0.35,
    fontSize: 12, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 22 - Danke / Fragen
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  s.addText("Danke fuer eure Aufmerksamkeit", {
    x: 0.6, y: 1.6, w: 8.8, h: 0.8,
    fontSize: 38, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri",
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 4.3, y: 2.55, w: 1.4, h: 0.06,
    fill: { color: COL.thws }, line: { type: "none" },
  });

  s.addText("Fragen?", {
    x: 0.6, y: 2.8, w: 8.8, h: 0.7,
    fontSize: 28, italic: true, color: "CADCFC", align: "center", fontFace: "Calibri",
  });

  s.addText([
    { text: "Keno Schuerger", options: { bold: true, breakLine: true } },
    { text: "keno.schuerger@study.thws.de", options: { color: "9CB4DE", fontFace: "Consolas", breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "github.com/Keno-fsdf/HandyUsageRepo", options: { color: "9CB4DE", fontFace: "Consolas" } },
  ], {
    x: 0.6, y: 4.0, w: 8.8, h: 1.2,
    fontSize: 14, color: "FFFFFF", align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// Helper that was forward-declared (typo-safe)
// ============================================================
function slineTitleSafe(presRef, slideRef, title, sub) {
  slideRef.addText(title, {
    x: 0.5, y: 0.30, w: 9, h: 0.55,
    fontSize: 28, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });
  slideRef.addShape(presRef.shapes.RECTANGLE, {
    x: 0.5, y: 0.92, w: 0.6, h: 0.05,
    fill: { color: COL.thws }, line: { type: "none" },
  });
  if (sub) {
    slideRef.addText(sub, {
      x: 0.5, y: 1.0, w: 9, h: 0.35,
      fontSize: 13, italic: true, color: COL.muted, fontFace: "Calibri",
    });
  }
}

// ============================================================
// Speichern
// ============================================================
pres.writeFile({ fileName: path.join(__dirname, "Portfolio_Kurzreferat.pptx") })
  .then(file => console.log("Erstellt: " + file))
  .catch(err => { console.error("Fehler: ", err); process.exit(1); });

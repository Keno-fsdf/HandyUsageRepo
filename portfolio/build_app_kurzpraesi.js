// App-Kurzpraesentation fuer den Portfolio-Teil (Vertiefung I):
// "Battery Data Collector - Eine Android-App mit On-Device-Akkuvorhersage"
//
// HINWEIS: Diese Praesentation ist STRIKT GETRENNT vom Paper.
//   - Paper-Defense:    paper/Paper_Verteidigung.pptx (16 Folien, ~10-15 Min)
//   - Lange Portfolio-Praesi (Forschung): portfolio/Portfolio_Kurzreferat.pptx (22 Folien)
//   - Diese App-Kurzpraesi (heute, 5 Min): portfolio/App_Kurzpraesi.pptx
//
// Inhalt: ausschliesslich die APP selbst und ihr Hauptfeature (On-Device-Inferenz).
//         KEINE Methoden-Vergleichszahlen, KEIN C-Index, KEIN per-Device-Ranking -
//         das gehoert in die Paper-Praesi.
//
// Dauer: ~5 Minuten - 8 Folien.
//
// Aufruf: node build_app_kurzpraesi.js

const pptxgen = require("../paper/node_modules/pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "Keno Schuerger";
pres.title = "Battery Data Collector - App-Kurzpraesi";

// ============================================================
// Farbpalette (THWS-naehe)
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
  accent: "2196F3",
  good: "27AE60",
  bad: "E94560",
};

const IMG_LOGO  = path.join(__dirname, "Thws-logo_English.png");
const IMG_START = path.join(__dirname, "screenshot_app_start.jpg");
const IMG_PRED  = path.join(__dirname, "screenshot_app_prediction.jpg");

const TOTAL = 8;

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
  slide.addText("Keno Schuerger - Vertiefung I - Battery Data Collector App", {
    x: 0.5, y: 5.3, w: 7, h: 0.25,
    fontSize: 9, color: COL.muted, fontFace: "Calibri",
  });
}
function slideTitle(slide, title, sub) {
  slide.addText(title, {
    x: 0.5, y: 0.30, w: 9, h: 0.55,
    fontSize: 28, bold: true, color: COL.primary, fontFace: "Calibri", margin: 0,
  });
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
// SLIDE 1 - Titelseite (~10s)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  s.addImage({ path: IMG_LOGO, x: 0.5, y: 4.7, w: 1.4, h: 0.7 });

  s.addText("Battery Data Collector", {
    x: 0.6, y: 1.1, w: 8.8, h: 0.8,
    fontSize: 40, bold: true, color: "FFFFFF", fontFace: "Calibri",
  });
  s.addText("Eine Android-App mit On-Device-Akkuvorhersage", {
    x: 0.6, y: 1.95, w: 8.8, h: 0.55,
    fontSize: 22, color: "CADCFC", fontFace: "Calibri",
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 2.65, w: 1.4, h: 0.06,
    fill: { color: COL.thws }, line: { type: "none" },
  });

  s.addText([
    { text: "Vertiefung I: Mobile und Ubiquitaere Anwendungen", options: { color: "9CB4DE", breakLine: true } },
    { text: "App-Kurzpraesentation - 5 Minuten", options: { color: COL.thws, italic: true, breakLine: true } },
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
// SLIDE 2 - Was die App ist und wofuer (~45s)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 2);
  slideTitle(s, "Was macht die App?",
    "Akku-Daten sammeln und direkt am Handy eine eigene Restzeit berechnen");

  const cards = [
    { t: "Sammeln",  body: "Alle 30 Sekunden ein Datenpunkt mit 10 Features (Akku, Bildschirm, App, CPU, Temperatur, Netz)." },
    { t: "Rechnen",  body: "Eigenes ML-Modell laeuft direkt auf dem Geraet und gibt eine Restzeit-Vorhersage aus." },
    { t: "Anzeigen", body: "Aktuelle Vorhersage in der App und in einer dauerhaften Notification - ohne dass die App offen sein muss." },
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 3.0;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.7, w: 2.8, h: 3.0,
      fill: { color: COL.bgSoft }, line: { color: COL.border, width: 1 }, rectRadius: 0.1,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.15, y: 1.85, w: 0.45, h: 0.45,
      fill: { color: COL.thws }, line: { type: "none" },
    });
    s.addText((i + 1).toString(), {
      x: x + 0.15, y: 1.85, w: 0.45, h: 0.45,
      fontSize: 18, bold: true, color: "FFFFFF",
      align: "center", valign: "middle", fontFace: "Calibri",
    });
    s.addText(c.t, {
      x: x + 0.7, y: 1.85, w: 2.0, h: 0.45,
      fontSize: 18, bold: true, color: COL.primary, fontFace: "Calibri", valign: "middle",
    });
    s.addText(c.body, {
      x: x + 0.2, y: 2.5, w: 2.45, h: 2.1,
      fontSize: 12, color: COL.text, fontFace: "Calibri",
    });
  });

  s.addText("Heute geht es um die App selbst - der wissenschaftliche Methoden-Vergleich ist Thema der separaten Paper-Praesentation.", {
    x: 0.6, y: 4.85, w: 8.8, h: 0.4,
    fontSize: 11, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 3 - Die App in Aktion (~45s)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 3);
  slideTitle(s, "Die App in Aktion",
    "Zwei Zustaende auf dem Xiaomi 2107113SG - Aufwaermphase und aktive Vorhersage");

  s.addImage({ path: IMG_START, x: 1.1, y: 1.4, w: 1.85, h: 3.7 });
  s.addText('"Sammle Daten ... (0/10)"', {
    x: 0.6, y: 5.1, w: 2.85, h: 0.25,
    fontSize: 11, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });

  s.addImage({ path: IMG_PRED, x: 4.5, y: 1.4, w: 1.85, h: 3.7 });
  s.addText('"Noch 13h 57min" bei 100% Akku', {
    x: 4.0, y: 5.1, w: 2.85, h: 0.25,
    fontSize: 11, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });

  s.addText("Was passiert da?", {
    x: 7.0, y: 1.5, w: 2.7, h: 0.4,
    fontSize: 16, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "Service laeuft im Hintergrund", options: { bold: true, breakLine: true } },
    { text: "auch bei geschlossener App", options: { breakLine: true, color: COL.muted, fontSize: 10 } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Modell braucht 10 Datenpunkte", options: { bold: true, breakLine: true } },
    { text: "= 5 Minuten Aufwaermphase", options: { breakLine: true, color: COL.muted, fontSize: 10 } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Danach alle 30s neuer Wert", options: { bold: true, breakLine: true } },
    { text: "live in App und Notification", options: { color: COL.muted, fontSize: 10 } },
  ], {
    x: 7.0, y: 2.0, w: 2.7, h: 3.2,
    fontSize: 12, color: COL.text, fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 4 - HAUPTFEATURE Teil 1: Konzept (~75s)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 4);
  slideTitle(s, "Hauptfeature: On-Device-Inferenz",
    "Die Vorhersage entsteht direkt auf dem Handy - ohne Internet, ohne Server");

  s.addText("Was heisst 'on-device'?", {
    x: 0.6, y: 1.5, w: 4.4, h: 0.4,
    fontSize: 16, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "Das ML-Modell liegt als ", options: {} },
    { text: ".tflite-Datei", options: { fontFace: "Consolas", bold: true } },
    { text: " im Assets-Ordner der App.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Jede Vorhersage wird vom TFLite-Interpreter lokal auf der CPU des Phones gerechnet.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Keine Cloud, kein Account, kein Netz - die App funktioniert vollstaendig offline.", options: { italic: true, color: COL.thws } },
  ], {
    x: 0.6, y: 1.95, w: 4.4, h: 3.0,
    fontSize: 12, color: COL.text, fontFace: "Calibri",
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.3, y: 1.45, w: 4.2, h: 3.6,
    fill: { color: COL.bgSoft }, line: { color: COL.thws, width: 2 }, rectRadius: 0.1,
  });
  s.addText("Warum das ein gutes Feature ist", {
    x: 5.4, y: 1.55, w: 4.0, h: 0.4,
    fontSize: 14, bold: true, color: COL.thws, fontFace: "Calibri",
  });

  const benefits = [
    { t: "Datenschutz",        d: "Sensor-Daten verlassen das Geraet nie." },
    { t: "Offline-faehig",      d: "Funktioniert auch im Flugzeug oder Funkloch." },
    { t: "Niedrige Latenz",     d: "Mikrosekunden statt Netz-Round-Trip." },
    { t: "Keine Server-Kosten", d: "Keine Backend-Infrastruktur noetig." },
  ];
  benefits.forEach((b, i) => {
    const y = 2.05 + i * 0.7;
    s.addShape(pres.shapes.OVAL, {
      x: 5.45, y: y + 0.07, w: 0.2, h: 0.2,
      fill: { color: COL.thws }, line: { type: "none" },
    });
    s.addText(b.t, {
      x: 5.75, y, w: 3.7, h: 0.35,
      fontSize: 13, bold: true, color: COL.primary, fontFace: "Calibri",
    });
    s.addText(b.d, {
      x: 5.75, y: y + 0.32, w: 3.7, h: 0.35,
      fontSize: 11, color: COL.text, fontFace: "Calibri",
    });
  });
}

// ============================================================
// SLIDE 5 - HAUPTFEATURE Teil 2: Wie es technisch laeuft (~60s)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 5);
  slideTitle(s, "Wie die Inferenz technisch laeuft",
    "Vom Sensor-Wert bis zur Vorhersage in der Notification");

  const steps = [
    { t: "Feature lesen",     d: "10 aktuelle Sensor-Werte auslesen." },
    { t: "Normalisieren",     d: "StandardScaler-Werte aus Training hardcoded in der App." },
    { t: "Ringpuffer fuellen", d: "Letzte 10 Messungen behalten (Sequenzlaenge des Modells)." },
    { t: "TFLite ausfuehren",  d: "Interpreter.run() liefert Restzeit in Stunden." },
    { t: "UI aktualisieren",   d: "Wert in App und Notification anzeigen." },
  ];
  steps.forEach((step, i) => {
    const y = 1.4 + i * 0.72;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.6, y, w: 0.55, h: 0.55,
      fill: { color: COL.thws }, line: { type: "none" }, rectRadius: 0.08,
    });
    s.addText((i + 1).toString(), {
      x: 0.6, y, w: 0.55, h: 0.55,
      fontSize: 18, bold: true, color: "FFFFFF",
      align: "center", valign: "middle", fontFace: "Calibri",
    });
    s.addText(step.t, {
      x: 1.3, y: y - 0.05, w: 3.3, h: 0.35,
      fontSize: 13, bold: true, color: COL.primary, fontFace: "Calibri",
    });
    s.addText(step.d, {
      x: 1.3, y: y + 0.28, w: 3.3, h: 0.35,
      fontSize: 11, color: COL.text, fontFace: "Calibri",
    });
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.3, y: 1.4, w: 4.2, h: 3.6,
    fill: { color: COL.bgDark }, line: { type: "none" }, rectRadius: 0.1,
  });
  s.addText("Modell-Steckbrief", {
    x: 5.5, y: 1.5, w: 3.9, h: 0.4,
    fontSize: 15, bold: true, color: COL.thws, fontFace: "Calibri",
  });

  const facts = [
    { k: "Typ",             v: "Conv1D, ~6k Parameter" },
    { k: "Eingabe",          v: "10 Zeitschritte x 10 Features" },
    { k: "Ausgabe",          v: "1 Float = Stunden bis leer" },
    { k: "Format",           v: "TFLite INT8 quantisiert" },
    { k: "Groesse",          v: "14.4 KB" },
    { k: "Latenz/Inferenz",  v: "~5 us auf CPU" },
  ];
  facts.forEach((f, i) => {
    const y = 2.0 + i * 0.45;
    s.addText(f.k, {
      x: 5.45, y, w: 1.8, h: 0.3,
      fontSize: 11, color: "9CB4DE", fontFace: "Calibri",
    });
    s.addText(f.v, {
      x: 7.2, y, w: 2.25, h: 0.3,
      fontSize: 11, bold: true, color: "FFFFFF", fontFace: "Consolas",
    });
  });
}

// ============================================================
// SLIDE 6 - Service-Robustheit (~45s)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 6);
  slideTitle(s, "Das groesste App-Problem",
    "Damit das Hauptfeature ueberhaupt funktioniert, muss der Service weiterlaufen");

  const events = [
    { t: "Tag 1",   text: "App gestartet, Daten fliessen rein, Vorhersage laeuft.", isFix: false },
    { t: "Tag 2",   text: "App aus dem Task-Switcher weggewischt - Service tot.",   isFix: false },
    { t: "Tag 3",   text: "Geraete-Neustart - Sammlung kommt nicht zurueck.",        isFix: false },
    { t: "Loesung", text: "Foreground-Service + AlarmManager-Restart + BootReceiver.", isFix: true },
  ];
  events.forEach((e, i) => {
    const y = 1.5 + i * 0.75;
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

  s.addText("Speziell auf Xiaomi/MIUI killt das System Hintergrund-Services aggressiv. Drei kombinierte Mechanismen halten den Service am Leben - ohne sie waere die Live-Vorhersage praktisch unbrauchbar.", {
    x: 0.6, y: 4.65, w: 8.8, h: 0.6,
    fontSize: 12, italic: true, color: COL.muted, align: "center", fontFace: "Calibri",
  });
}

// ============================================================
// SLIDE 7 - Datenschutz + Stand (~45s)
// ============================================================
{
  const s = pres.addSlide();
  chrome(s, 7);
  slideTitle(s, "Datenschutz und aktueller Stand",
    "Alles lokal, nichts geht ungefragt raus");

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.5, w: 4.5, h: 3.5,
    fill: { color: COL.bgSoft }, line: { color: COL.border, width: 1 }, rectRadius: 0.1,
  });
  s.addText("Datenschutz", {
    x: 0.7, y: 1.6, w: 4.0, h: 0.4,
    fontSize: 16, bold: true, color: COL.primary, fontFace: "Calibri",
  });
  s.addText([
    { text: "+ ", options: { color: COL.good, bold: true } },
    { text: "Keine Standort-, Mikro-, Kamera-Permission.", options: { breakLine: true } },
    { text: "+ ", options: { color: COL.good, bold: true } },
    { text: "App-Kategorie (0-5), nicht Paketname.",        options: { breakLine: true } },
    { text: "+ ", options: { color: COL.good, bold: true } },
    { text: "CSV liegt nur in der App-Sandbox (filesDir).", options: { breakLine: true } },
    { text: "+ ", options: { color: COL.good, bold: true } },
    { text: "Export nur per expliziten Share-Intent.",      options: { breakLine: true } },
    { text: "+ ", options: { color: COL.good, bold: true } },
    { text: "Kein Auto-Upload, kein Backend, kein Account.", options: {} },
  ], {
    x: 0.8, y: 2.05, w: 4.0, h: 2.9,
    fontSize: 12, color: COL.text, fontFace: "Calibri",
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.2, y: 1.5, w: 4.3, h: 3.5,
    fill: { color: COL.bgSoft }, line: { color: COL.border, width: 1 }, rectRadius: 0.1,
  });
  s.addText("Stand am 11.5.2026", {
    x: 5.4, y: 1.6, w: 4.0, h: 0.4,
    fontSize: 16, bold: true, color: COL.primary, fontFace: "Calibri",
  });

  const stats = [
    { v: "4",      l: "Geraete im Feldtest (Xiaomi + 3 Pixel)" },
    { v: "45",     l: "Tage Laufzeit" },
    { v: "66 001", l: "Messpunkte gesammelt" },
    { v: "180",    l: "Sessions" },
  ];
  stats.forEach((st, i) => {
    const y = 2.1 + i * 0.65;
    s.addText(st.v, {
      x: 5.4, y, w: 1.4, h: 0.55,
      fontSize: 22, bold: true, color: COL.thws,
      align: "right", valign: "middle", fontFace: "Calibri",
    });
    s.addText(st.l, {
      x: 6.95, y, w: 2.5, h: 0.55,
      fontSize: 11, color: COL.text, fontFace: "Calibri", valign: "middle",
    });
  });
}

// ============================================================
// SLIDE 8 - Fragen (~10s + Puffer)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.bgDark };

  s.addText("Fragen zur App?", {
    x: 0.6, y: 1.6, w: 8.8, h: 0.8,
    fontSize: 40, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri",
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 4.3, y: 2.55, w: 1.4, h: 0.06,
    fill: { color: COL.thws }, line: { type: "none" },
  });

  s.addText("Gerne auch zum Service-Lifecycle, MIUI-Survival oder dem Kotlin/TFLite-Code.", {
    x: 0.6, y: 2.85, w: 8.8, h: 0.6,
    fontSize: 16, italic: true, color: "CADCFC", align: "center", fontFace: "Calibri",
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
// Speichern
// ============================================================
pres.writeFile({ fileName: path.join(__dirname, "App_Kurzpraesi.pptx") })
  .then(file => console.log("Erstellt: " + file))
  .catch(err => { console.error("Fehler: ", err); process.exit(1); });

# Paper

LaTeX-Quellen des Forschungspapers.

## Dateien

- `main.tex` — Hauptdokument (IEEE Conference Style, ~7-8 Seiten)
- `references.bib` — alle BibTeX-Einträge

## Bauen

### Variante 1: lokal mit `latexmk` (empfohlen)
```powershell
cd paper
latexmk -pdf main.tex
```

### Variante 2: manuell
```powershell
cd paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

### Variante 3: Overleaf
1. Repository als ZIP exportieren oder Ordner `paper/` zusammen mit `reports/figures/` hochladen
2. In Overleaf: Main document = `main.tex`, Compiler = `pdflatex`
3. **Wichtig**: Figures werden via `\graphicspath{{../reports/figures/}}` referenziert. Wenn der Overleaf-Build nicht klappt, entweder:
   - die figures-Ordner direkt nach `paper/figures/` kopieren und `\graphicspath{{figures/}}` setzen, oder
   - die acht PNGs aus `reports/figures/` neben `main.tex` ablegen.

## Was du noch anpassen musst

1. **Autoren-Block** in `main.tex` (Zeile ~30): aktuell nur `Keno Schürger` — Co-Autoren / Betreuer / Affiliation ergänzen falls nötig.
2. **Titel**: aktuell *„App-Level TinyML for Smartphone Battery-Life Prediction: A Methodologically Honest Negative Result"* — falls dein Lehrstuhl einen anderen Stil bevorzugt, anpassen.
3. **Abstract**: ~200 Wörter, ehrlicher negativer Tenor. Falls du es positiver framen willst, hier umschreiben.
4. **Vorlage**: Aktuell IEEE Conference (`IEEEtran`). Falls dein Modul ACM, Springer LNCS, oder eine THWS-Vorlage erwartet, Klassenzeile oben anpassen und ggf. Abschnitte umstrukturieren.
5. **Sprache**: Englisch. Falls du eine deutsche Version brauchst, sag Bescheid — kein dramatischer Aufwand.

## Was bereits drin ist

- Vollständige 6-Sektionen-Struktur (Intro, Related Work, Method, Results, Discussion, Limitations, Conclusion)
- 4 Tabellen (Leakage-Effekt, 6-Wege-Accuracy mit CIs, Significance-Tests, Effizienz)
- 1 Figure (Cumulative Error Distribution)
- Alle Zahlen aus `reports/REPORT.md` und `reports/main_table.csv` übernommen
- Reproducibility Statement
- 12 Bibliographie-Einträge (alle aus `RELATED_WORK.md`)

## Geschätzte Seitenzahl

Mit Standard-IEEEtran-Margins und 10pt-Schrift sind das vermutlich **6-7 Seiten** ohne Bibliographie, **7-8 Seiten** mit. Falls dein Modul eine andere Länge erwartet:
- Kürzen: Sektion „Discussion" und „Related Work" sind die ersten Kandidaten
- Verlängern: weitere Figures aus `reports/figures/` einbinden (Scatter, Histogramm, Trainings-Kurven), Per-Bucket-Tabelle ausarbeiten

## Verifikation

Jede numerische Aussage im Paper ist in einem JSON-File unter `reports/` referenzierbar. Bei Änderung der Daten/Hyperparameter die Pipeline neu laufen lassen und Zahlen im Paper aktualisieren:

```powershell
python run_pipeline.py
# danach: alle Zahlen in main.tex gegen reports/REPORT.md prüfen
```

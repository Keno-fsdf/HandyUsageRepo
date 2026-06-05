package com.batterypredictor.datacollector

import java.io.File
import java.io.RandomAccessFile

/**
 * Berechnet aus der CSV-Datei einen pragmatischen
 * Wer-war-genauer-Score: fuer jeden Discharge-Datenpunkt mit vorhandener
 * Vorhersage wird die _tatsaechliche_ Rest-Discharge-Zeit gegen die
 * Vorhersage gehalten und der MAE (Mean Absolute Error) gemittelt.
 *
 * Ein "tatsaechlicher Endpunkt" ist der naechste Beginn einer Lade-Phase
 * (charging=1) oder das Ende der Daten (wir nehmen dann das letzte
 * verfuegbare Sample mit < 8% Akku als Proxy fuer "Akku war leer").
 *
 * Wenn weder Lade-Beginn noch ein Akku<8% Sample im betrachteten Zeitraum
 * existiert, gibt die Methode null zurueck und das AccuracyFragment zeigt
 * den entsprechenden Hinweis.
 */
object AccuracyComputer {

    data class Score(
        /** Anzahl bewerteter Vorhersage-Punkte */
        val nPoints: Int,
        /** MAE in Minuten -- niedriger = besser */
        val maeOwnMin: Float,
        val maeGoogleMin: Float,
        val maeLinearMin: Float,
        /**
         * Trefferquote pro Methode: Anteil Vorhersagen, die innerhalb
         * der Toleranz max(actualMin * 0.25, 60min) lagen.
         * Werte zwischen 0 und 1, NaN falls keine Daten.
         */
        val hitRateOwn: Float,
        val hitRateGoogle: Float,
        val hitRateLinear: Float,
        /** Welche Methode liegt vorn? "own" | "google" | "linear" */
        val winner: String,
        /** Gesamtdauer des bewerteten Discharge-Laufs in Minuten */
        val dischargeMin: Float,
    )

    /**
     * Liest das Ende der CSV (ca. die letzten ~24 Stunden) und berechnet
     * einen Score. Schwer-IO-Aufruf -- vom Caller auf einem Background-Thread.
     */
    fun computeRecent(csvFile: File, lookbackBytes: Int = 512 * 1024): Score? {
        if (!csvFile.exists() || csvFile.length() == 0L) return null

        val text = readTail(csvFile, lookbackBytes)
        val lines = text.lineSequence().map { it.trim() }
            .filter { it.isNotEmpty() }.toList()
        if (lines.size < 5) return null

        // Header rausfischen: entweder erste Zeile (wenn ganze Datei klein) oder
        // wir suchen die echte erste Zeile mit dem Header-Marker "session_id".
        val header = csvFile.useLines { it.firstOrNull() ?: "" }
        val cols = header.split(",")
        if (cols.isEmpty()) return null

        fun idx(name: String): Int = cols.indexOf(name)
        val iTs = idx("timestamp")
        val iCharging = idx("charging")
        val iBattery = idx("battery_level")
        val iOwn = idx("own_prediction_h")
        val iLinear = idx("linear_baseline_h")
        val iSystemMin = idx("system_estimate_min")

        if (iTs < 0 || iCharging < 0 || iBattery < 0 || iOwn < 0) return null

        // Zeilen parsen, dabei Header-Zeile am Anfang skippen falls sie im
        // Tail mit drin steht (kann passieren wenn Datei kleiner als lookback).
        val rows = lines.mapNotNull { line ->
            if (line == header) return@mapNotNull null
            val v = line.split(",")
            if (v.size <= iSystemMin) return@mapNotNull null
            Row(
                ts = v[iTs].toLongOrNull() ?: return@mapNotNull null,
                charging = (v[iCharging].toIntOrNull() ?: 0) == 1,
                battery = v[iBattery].toFloatOrNull() ?: return@mapNotNull null,
                ownH = v[iOwn].toFloatOrNull() ?: -1f,
                linearH = if (iLinear >= 0)
                    v[iLinear].toFloatOrNull() ?: -1f else -1f,
                systemMin = if (iSystemMin >= 0)
                    v[iSystemMin].toFloatOrNull() ?: -1f else -1f,
            )
        }
        if (rows.size < 5) return null

        // Suche den juengsten Charging-Start und den darin endenden Discharge-Lauf.
        // Charging-Start = vorheriger Punkt war nicht charging und dieser ist charging.
        var endTs: Long = -1L
        for (i in rows.size - 1 downTo 1) {
            if (rows[i].charging && !rows[i - 1].charging) {
                endTs = rows[i].ts
                break
            }
        }
        // Fallback: letzter Punkt mit Akku < 8% gilt als "Akku praktisch leer".
        if (endTs < 0) {
            val lowBatt = rows.lastOrNull { it.battery < 8f && !it.charging }
            if (lowBatt != null) endTs = lowBatt.ts
        }
        if (endTs < 0) return null

        // Discharge-Strecke vor endTs sammeln, fuer jeden Punkt mit own != -1
        // den MAE addieren. Linear/Google: nur wenn auch dort != -1.
        // Zusaetzlich pro Methode zaehlen, wie viele Vorhersagen innerhalb
        // der Toleranz max(actualMin * 0.25, 60min) lagen -> Trefferquote.
        var nOwn = 0; var sOwn = 0f; var hOwn = 0
        var nLin = 0; var sLin = 0f; var hLin = 0
        var nGoo = 0; var sGoo = 0f; var hGoo = 0
        var firstTs = Long.MAX_VALUE
        for (r in rows) {
            if (r.ts >= endTs || r.charging) continue
            val actualMin = ((endTs - r.ts) / 60_000f)
            if (actualMin < 0f) continue
            if (r.ts < firstTs) firstTs = r.ts
            val tolerance = kotlin.math.max(actualMin * 0.25f, 60f)
            if (r.ownH >= 0f) {
                val err = kotlin.math.abs(r.ownH * 60f - actualMin)
                sOwn += err; nOwn++
                if (err <= tolerance) hOwn++
            }
            if (r.linearH >= 0f) {
                val err = kotlin.math.abs(r.linearH * 60f - actualMin)
                sLin += err; nLin++
                if (err <= tolerance) hLin++
            }
            if (r.systemMin >= 0f) {
                val err = kotlin.math.abs(r.systemMin - actualMin)
                sGoo += err; nGoo++
                if (err <= tolerance) hGoo++
            }
        }
        if (nOwn < 3) return null

        val maeOwn = sOwn / nOwn
        val maeLin = if (nLin > 0) sLin / nLin else Float.NaN
        val maeGoo = if (nGoo > 0) sGoo / nGoo else Float.NaN

        // Wenn das eigene Modell deutlich danebenliegt (> 10 % der Discharge-
        // Strecke, mindestens 60 min), zeigen wir lieber den
        // "Noch-nicht-genug-Daten"-Empty-State statt schwacher Zahlen.
        val dischargeMinTmp = if (firstTs < Long.MAX_VALUE)
            (endTs - firstTs) / 60_000f else 0f
        val acceptThreshold = kotlin.math.max(dischargeMinTmp * 0.10f, 60f)
        if (maeOwn > acceptThreshold) return null

        val hitOwn = hOwn.toFloat() / nOwn
        val hitLin = if (nLin > 0) hLin.toFloat() / nLin else Float.NaN
        val hitGoo = if (nGoo > 0) hGoo.toFloat() / nGoo else Float.NaN

        // Winner = hoechste Trefferquote (Tie-Break: niedrigster MAE).
        val candidates = listOf(
            Triple("own", hitOwn, maeOwn),
            Triple("google", hitGoo, maeGoo),
            Triple("linear", hitLin, maeLin),
        ).filter { !it.second.isNaN() }
        val winner = candidates.maxWithOrNull(
            compareBy<Triple<String, Float, Float>> { it.second }
                .thenByDescending { it.third }
        )?.first ?: "own"

        val dischargeMin = dischargeMinTmp

        return Score(
            nPoints = nOwn,
            maeOwnMin = maeOwn,
            maeGoogleMin = maeGoo,
            maeLinearMin = maeLin,
            hitRateOwn = hitOwn,
            hitRateGoogle = hitGoo,
            hitRateLinear = hitLin,
            winner = winner,
            dischargeMin = dischargeMin,
        )
    }

    private data class Row(
        val ts: Long, val charging: Boolean, val battery: Float,
        val ownH: Float, val linearH: Float, val systemMin: Float,
    )

    private fun readTail(file: File, maxBytes: Int): String {
        val len = file.length()
        val start = (len - maxBytes).coerceAtLeast(0L)
        val size = (len - start).toInt()
        val buf = ByteArray(size)
        RandomAccessFile(file, "r").use { raf ->
            raf.seek(start)
            raf.readFully(buf)
        }
        return String(buf, Charsets.UTF_8)
    }
}

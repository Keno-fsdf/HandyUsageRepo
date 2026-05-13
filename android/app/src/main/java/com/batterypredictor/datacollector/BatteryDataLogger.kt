package com.batterypredictor.datacollector

import android.content.Context
import java.io.BufferedWriter
import java.io.File
import java.io.FileWriter
import java.io.RandomAccessFile
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.atomic.AtomicLong

/**
 * Schreibt BatteryDataPoints in eine CSV-Datei im App-internen Speicher.
 *
 * Singleton: Service und MainActivity nutzen dieselbe Instanz. Frueher wurden
 * zwei voneinander unabhaengige Logger erzeugt -- beide haben Schema-Drift-Init
 * gelaufen lassen, mit Race-Conditions auf der Datei.
 *
 * Threadsafe:
 *  - `log()` ist @Synchronized fuer den File-Write-Pfad.
 *  - `getCount()` liefert aus einem AtomicLong, kein File-IO im Hot-Path
 *    (frueher: ganze CSV alle 10s vom UI-Thread gelesen -> ANR-Risiko).
 *  - `getLastEntries()` liest nur das Datei-Ende per RandomAccessFile.
 */
class BatteryDataLogger private constructor(context: Context) {

    private val appContext: Context = context.applicationContext

    private val csvFile: File
        get() = File(appContext.filesDir, "battery_data.csv")

    private val countRef = AtomicLong(0L)

    init {
        val expectedHeader = "session_id,timestamp,datetime,${BatteryDataPoint.CSV_HEADER}"

        if (!csvFile.exists() || csvFile.length() == 0L) {
            csvFile.writeText("$expectedHeader\n")
        } else {
            // Schema-Drift: alte CSV (z.B. ohne system_personalized) parken,
            // neue beginnen. Sonst werden Spalten falsch zugeordnet.
            val firstLine = csvFile.useLines { it.firstOrNull() ?: "" }
            if (firstLine != expectedHeader) {
                val backup = File(appContext.filesDir,
                    "battery_data_legacy_${System.currentTimeMillis()}.csv")
                csvFile.copyTo(backup, overwrite = true)
                csvFile.writeText("$expectedHeader\n")
            }
        }

        // ---- Legacy-Migration ----
        // Datenpunkte aus früheren Schema-Versionen (battery_data_legacy_*.csv)
        // werden mit "-1" für fehlende Spalten in die aktuelle CSV überführt
        // und danach archiviert. So bleibt der Datenpunkt-Zähler korrekt.
        migrateLegacyCsvs(expectedHeader)

        countRef.set(countLinesFast(csvFile) - 1L)
    }

    /**
     * Importiert alle vorhandenen battery_data_legacy_*.csv in die aktuelle CSV.
     * By-name-Mapping schuetzt vor Position-Drift bei eingefuegten Spalten.
     */
    private fun migrateLegacyCsvs(expectedHeader: String) {
        val legacyFiles = appContext.filesDir.listFiles { file ->
            file.name.startsWith("battery_data_legacy_") && file.name.endsWith(".csv")
        } ?: return

        if (legacyFiles.isEmpty()) return

        val expectedCols = expectedHeader.split(",")
        var migrated = 0
        BufferedWriter(FileWriter(csvFile, true)).use { writer ->
            for (legacy in legacyFiles) {
                val lines = legacy.readLines()
                if (lines.size <= 1) continue
                val oldCols = lines.first().split(",")
                // Fuer jede Ziel-Spalte den Index in der alten Spaltenliste.
                // Spalten ohne Aequivalent in der alten CSV -> -1 (Sentinel).
                val colMap = expectedCols.map { name -> oldCols.indexOf(name) }

                for (i in 1 until lines.size) {
                    val line = lines[i].trim()
                    if (line.isEmpty()) continue
                    val values = line.split(",")
                    val rebuilt = colMap.joinToString(",") { srcIdx ->
                        if (srcIdx >= 0 && srcIdx < values.size) values[srcIdx] else "-1"
                    }
                    writer.write("$rebuilt\n")
                    migrated++
                }
            }
        }

        for (legacy in legacyFiles) {
            legacy.renameTo(File(legacy.parentFile, legacy.name + ".migrated"))
        }

        android.util.Log.i("BatteryDataLogger",
            "Migrated $migrated rows from ${legacyFiles.size} legacy file(s)")
    }

    @Synchronized
    fun log(data: BatteryDataPoint, sessionId: String) {
        val dateStr = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US)
            .format(Date(data.timestamp))

        BufferedWriter(FileWriter(csvFile, true)).use { writer ->
            writer.write("$sessionId,${data.timestamp},$dateStr,${data.toCsvLine()}\n")
        }
        countRef.incrementAndGet()
    }

    /**
     * O(1) -- liest aus In-Memory-Counter, kein File-IO.
     * Wichtig: muss vom UI-Thread sicher aufrufbar sein (Timer alle 10s).
     */
    fun getCount(): Int = countRef.get().toInt().coerceAtLeast(0)

    fun getFile(): File = csvFile

    /**
     * Liest nur das Datei-Ende statt der gesamten Datei (frueher: 5 MB
     * komplett in den Speicher bei 47k Zeilen).
     */
    fun getLastEntries(n: Int = 5): String {
        if (!csvFile.exists() || csvFile.length() == 0L) return "Keine Daten vorhanden"

        // Header (kurz, immer am Anfang) separat lesen.
        val header = csvFile.useLines { it.firstOrNull() ?: "" }

        val tail = readTail(csvFile, maxBytes = 16 * 1024)
        val lines = tail.lineSequence()
            .map { it.trim() }
            .filter { it.isNotEmpty() && it != header }
            .toList()
        if (lines.isEmpty()) return "$header\n(keine Daten)"
        val lastN = lines.takeLast(n)
        return "$header\n${lastN.joinToString("\n")}"
    }

    /**
     * Exportiert die CSV-Datei in den externen Downloads-Ordner.
     */
    fun exportToDownloads(): File {
        val downloadsDir = android.os.Environment.getExternalStoragePublicDirectory(
            android.os.Environment.DIRECTORY_DOWNLOADS
        )
        val exportFile = File(downloadsDir, "battery_data_export.csv")
        csvFile.copyTo(exportFile, overwrite = true)
        return exportFile
    }

    companion object {
        @Volatile
        private var INSTANCE: BatteryDataLogger? = null

        fun getInstance(context: Context): BatteryDataLogger {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: BatteryDataLogger(context).also { INSTANCE = it }
            }
        }

        /** Zaehlt Zeilen ueber Byte-Stream, nicht durch readLines() (kein 5-MB-Heap-Hit). */
        private fun countLinesFast(file: File): Long {
            if (!file.exists()) return 0L
            var n = 0L
            file.inputStream().buffered().use { input ->
                val buf = ByteArray(8192)
                while (true) {
                    val read = input.read(buf)
                    if (read <= 0) break
                    for (i in 0 until read) {
                        if (buf[i] == '\n'.code.toByte()) n++
                    }
                }
            }
            return n
        }

        /** Liest die letzten `maxBytes` Bytes der Datei als UTF-8-String. */
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
}

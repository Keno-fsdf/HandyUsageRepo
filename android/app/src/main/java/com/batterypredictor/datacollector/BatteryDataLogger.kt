package com.batterypredictor.datacollector

import android.content.Context
import java.io.File
import java.io.FileWriter
import java.io.BufferedWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Schreibt BatteryDataPoints in eine CSV-Datei im App-internen Speicher.
 * Threadsafe durch synchronized.
 */
class BatteryDataLogger(private val context: Context) {

    private val csvFile: File
        get() = File(context.filesDir, "battery_data.csv")

    private var count = 0

    init {
        // Header schreiben falls Datei neu
        if (!csvFile.exists() || csvFile.length() == 0L) {
            csvFile.writeText("session_id,timestamp,datetime,${BatteryDataPoint.CSV_HEADER}\n")
        }
        // Bestehende Zeilen zählen
        count = if (csvFile.exists()) {
            csvFile.readLines().size - 1 // minus Header
        } else 0
    }

    @Synchronized
    fun log(data: BatteryDataPoint, sessionId: String) {
        val dateStr = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US)
            .format(Date(data.timestamp))

        val writer = BufferedWriter(FileWriter(csvFile, true))
        writer.write("$sessionId,${data.timestamp},$dateStr,${data.toCsvLine()}\n")
        writer.close()
        count++
    }

    fun getCount(): Int = count

    fun getFile(): File = csvFile

    /**
     * Gibt die letzten N Datenpunkte als lesbaren String zurück.
     */
    fun getLastEntries(n: Int = 5): String {
        if (!csvFile.exists()) return "Keine Daten vorhanden"
        val lines = csvFile.readLines()
        if (lines.size <= 1) return "Keine Daten vorhanden"

        val header = lines.first()
        val lastN = lines.takeLast(n)
        return "$header\n${lastN.joinToString("\n")}"
    }

    /**
     * Exportiert die CSV-Datei in den externen Downloads-Ordner.
     * Gibt den Pfad zurück.
     */
    fun exportToDownloads(): File {
        val downloadsDir = android.os.Environment.getExternalStoragePublicDirectory(
            android.os.Environment.DIRECTORY_DOWNLOADS
        )
        val exportFile = File(downloadsDir, "battery_data_export.csv")
        csvFile.copyTo(exportFile, overwrite = true)
        return exportFile
    }
}

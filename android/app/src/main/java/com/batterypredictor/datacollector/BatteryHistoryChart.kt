package com.batterypredictor.datacollector

import android.content.Context
import android.graphics.Canvas
import android.graphics.DashPathEffect
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.os.Handler
import android.os.Looper
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import java.io.File
import java.io.RandomAccessFile
import java.util.concurrent.Executors

/**
 * Sparkline der letzten X Stunden Akku-Verlauf + gestrichelte
 * Extrapolation in die Zukunft mit der aktuellen TinyML-Vorhersage.
 *
 * Liest die CSV im Background-Thread (Executor) und rendert auf dem
 * UI-Thread. Daten-Refresh-Aufruf ueber [refresh].
 */
class BatteryHistoryChart @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val historyColor = ContextCompat.getColor(context, R.color.prediction_text)
    private val futureColor = ContextCompat.getColor(context, R.color.brand_primary)
    private val gridColor = ContextCompat.getColor(context, R.color.card_outline)
    private val labelColor = ContextCompat.getColor(context, R.color.sensor_card_label)

    private val historyPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = historyColor
        style = Paint.Style.STROKE
        strokeWidth = dp(2.5f)
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }
    private val historyFillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = historyColor
        style = Paint.Style.FILL
        alpha = 30
    }
    private val futurePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = futureColor
        style = Paint.Style.STROKE
        strokeWidth = dp(2.5f)
        strokeCap = Paint.Cap.ROUND
        pathEffect = DashPathEffect(floatArrayOf(dp(8f), dp(6f)), 0f)
    }
    private val nowDotPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = futureColor
        style = Paint.Style.FILL
    }
    private val nowDotRingPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = futureColor
        style = Paint.Style.STROKE
        strokeWidth = dp(2f)
        alpha = 120
    }
    private val gridPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = gridColor
        style = Paint.Style.STROKE
        strokeWidth = dp(1f)
        alpha = 100
    }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = labelColor
        textSize = dp(10f)
    }
    private val placeholderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = labelColor
        textSize = dp(13f)
        textAlign = Paint.Align.CENTER
    }

    private data class HistoryPoint(val ts: Long, val battery: Float)

    @Volatile
    private var history: List<HistoryPoint> = emptyList()

    @Volatile
    private var predictionH: Float = -1f

    private val ioExecutor = Executors.newSingleThreadExecutor()
    private val uiHandler = Handler(Looper.getMainLooper())

    /**
     * Lädt die letzten ca. 3 Stunden aus der CSV und das aktuelle
     * Prediction-Ergebnis. Triggert anschliessend invalidate().
     */
    fun refresh(csvFile: File, predictionHours: Float) {
        predictionH = predictionHours
        ioExecutor.execute {
            val loaded = try {
                loadRecentHistory(csvFile, lookbackHours = 3)
            } catch (e: Exception) {
                emptyList()
            }
            uiHandler.post {
                history = loaded
                invalidate()
            }
        }
    }

    private fun loadRecentHistory(csvFile: File, lookbackHours: Int): List<HistoryPoint> {
        if (!csvFile.exists() || csvFile.length() == 0L) return emptyList()

        // Header lesen, um die richtigen Spalten zu finden.
        val header = csvFile.useLines { it.firstOrNull() ?: "" }
        val cols = header.split(",")
        val iTs = cols.indexOf("timestamp")
        val iBattery = cols.indexOf("battery_level")
        val iCharging = cols.indexOf("charging")
        if (iTs < 0 || iBattery < 0) return emptyList()

        // Tail-Read: die letzten ~256KB reichen fuer ca. 3h bei 30s-Takt.
        val maxBytes = 256 * 1024
        val len = csvFile.length()
        val start = (len - maxBytes).coerceAtLeast(0L)
        val size = (len - start).toInt()
        val buf = ByteArray(size)
        RandomAccessFile(csvFile, "r").use { raf ->
            raf.seek(start)
            raf.readFully(buf)
        }
        val text = String(buf, Charsets.UTF_8)
        val cutoff = System.currentTimeMillis() - lookbackHours * 3_600_000L

        val out = mutableListOf<HistoryPoint>()
        for (line in text.lineSequence()) {
            val trimmed = line.trim()
            if (trimmed.isEmpty() || trimmed == header) continue
            val v = trimmed.split(",")
            if (v.size <= maxOf(iTs, iBattery)) continue
            val ts = v[iTs].toLongOrNull() ?: continue
            if (ts < cutoff) continue
            // Lade-Phasen skippen, damit die Sparkline nicht "huepft".
            if (iCharging >= 0 && iCharging < v.size && v[iCharging].toIntOrNull() == 1) continue
            val battery = v[iBattery].toFloatOrNull() ?: continue
            out += HistoryPoint(ts, battery)
        }
        return out
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0 || h <= 0) return

        // Plot-Bereich mit Padding fuer Labels.
        val padL = dp(34f); val padR = dp(16f)
        val padT = dp(14f); val padB = dp(20f)
        val plotL = padL; val plotR = w - padR
        val plotT = padT; val plotB = h - padB
        val plotW = plotR - plotL
        val plotH = plotB - plotT

        // Grid: 0%, 50%, 100% horizontal.
        for (pct in intArrayOf(0, 50, 100)) {
            val y = plotB - plotH * (pct / 100f)
            canvas.drawLine(plotL, y, plotR, y, gridPaint)
            canvas.drawText("${pct}%", dp(4f), y + dp(3f), labelPaint)
        }

        val data = history
        if (data.size < 3) {
            canvas.drawText(
                "Sammle Verlaufsdaten…",
                w / 2f, h / 2f,
                placeholderPaint
            )
            return
        }

        // X-Achse Zeit: tNow - 3h .. tNow
        val tNow = System.currentTimeMillis()
        val lookbackMs = 3 * 3_600_000L
        val tStart = tNow - lookbackMs

        fun xForTs(ts: Long): Float {
            val rel = ((ts - tStart).coerceAtLeast(0L)).toFloat() / lookbackMs.toFloat()
            return plotL + plotW * rel.coerceIn(0f, 1f)
        }
        fun yForBattery(b: Float): Float {
            return plotB - plotH * (b / 100f).coerceIn(0f, 1f)
        }

        // ---- Historischer Pfad ----
        val historyPath = Path()
        val fillPath = Path()
        var first = true
        for (p in data) {
            val x = xForTs(p.ts)
            val y = yForBattery(p.battery)
            if (first) {
                historyPath.moveTo(x, y)
                fillPath.moveTo(x, plotB)
                fillPath.lineTo(x, y)
                first = false
            } else {
                historyPath.lineTo(x, y)
                fillPath.lineTo(x, y)
            }
        }
        // Fill schliessen
        val last = data.last()
        val lastX = xForTs(last.ts)
        fillPath.lineTo(lastX, plotB)
        fillPath.close()

        canvas.drawPath(fillPath, historyFillPaint)
        canvas.drawPath(historyPath, historyPaint)

        // ---- "Jetzt"-Marker ----
        val nowX = xForTs(last.ts)
        val nowY = yForBattery(last.battery)
        canvas.drawCircle(nowX, nowY, dp(7f), nowDotRingPaint)
        canvas.drawCircle(nowX, nowY, dp(4.5f), nowDotPaint)

        // ---- Gestrichelte Vorhersage-Extension ----
        // Wenn Vorhersage > 0: zeichne eine Linie vom (nowX, nowY) bis
        // zu einem Endpunkt, der die Restlaufzeit in Stunden representiert.
        // Wir nehmen plot-rechte Kante als 1h voraus (visualisierte Skala),
        // ggf clamp auf plotR.
        if (predictionH > 0f) {
            val futureHoursVisible = 1f  // 1h Ausblick rechts vom now-Marker
            val futureLen = plotR - nowX
            if (futureLen > dp(8f)) {
                // Lineare Abnahme: aktueller Akku / predictionH ist Drain pro Stunde
                val drainPerHour = last.battery / predictionH
                val batteryIn1h = (last.battery - drainPerHour * futureHoursVisible)
                    .coerceAtLeast(0f)
                val endX = nowX + futureLen
                val endY = yForBattery(batteryIn1h)
                val futurePath = Path().apply {
                    moveTo(nowX, nowY)
                    lineTo(endX, endY)
                }
                canvas.drawPath(futurePath, futurePaint)

                // kleines Label "in 1h"
                canvas.drawText("in 1h", endX - dp(20f), endY - dp(8f), labelPaint)
            }
        }

        // Achsen-Label rechts: jetzt
        canvas.drawText("jetzt", nowX - dp(10f), plotB + dp(14f), labelPaint)
        canvas.drawText("-3h", plotL, plotB + dp(14f), labelPaint)
    }

    private fun dp(value: Float): Float = value * resources.displayMetrics.density
}

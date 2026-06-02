package com.batterypredictor.datacollector

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.sin
import kotlin.random.Random

/**
 * Visualisiert die Architektur des TinyML-Modells (Conv1D + GlobalAvgPool +
 * Dense), nicht nur den Datenfluss. Zeigt vier vertikal angeordnete
 * Schichten:
 *
 *   1. Input         10 Features x 10 Zeitschritte als Matrix
 *                    (jede Zelle = ein Messwert).
 *   2. Conv1D        16 Feature-Maps als horizontale Streifen
 *                    (kernel size 3, gleitet ueber die Zeit-Achse).
 *   3. GlobalAvgPool 16 vertikale Saeulen (eine Zahl pro Feature-Map).
 *   4. Dense         1 Output-Wert.
 *
 * Animation: der "Forward-Pass" leuchtet sequentiell von oben nach unten
 * (Eingangs-Matrix -> Conv -> Pool -> Output) und faengt unten wieder von
 * vorne an. So sieht man dem Modell zu, wie es eine Vorhersage berechnet.
 */
class ConvLayerView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val brandPrimary = ContextCompat.getColor(context, R.color.brand_primary)
    private val textColor = ContextCompat.getColor(context, R.color.prediction_text)
    private val mutedColor = ContextCompat.getColor(context, R.color.sensor_card_label)
    private val cellBase = ContextCompat.getColor(context, R.color.sensor_bar_inactive)
    private val cellActive = ContextCompat.getColor(context, R.color.sensor_bar_active)
    private val cardOutline = ContextCompat.getColor(context, R.color.card_outline)

    private val cellPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }
    private val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = cardOutline
        style = Paint.Style.STROKE
        strokeWidth = dp(1f)
    }
    private val arrowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = mutedColor
        style = Paint.Style.STROKE
        strokeWidth = dp(1.5f)
    }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = textColor
        textSize = dp(11f)
        isFakeBoldText = true
    }
    private val subLabelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = mutedColor
        textSize = dp(10f)
    }
    private val brandFillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = brandPrimary
        style = Paint.Style.FILL
    }
    private val brandStrokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = brandPrimary
        style = Paint.Style.STROKE
        strokeWidth = dp(2f)
    }

    /**
     * Input-Matrix: 10 Sensoren x 10 Zeitschritte. Wird live durch
     * [setInputCells] mit normalisierten Sensor-Werten (0..1) gefuettert
     * -- das macht den Input-Layer ehrlich (das, was das Modell wirklich
     * sieht).
     *
     * Die spaeteren Schichten (Conv, Pool) bleiben simuliert, weil
     * INT8-Zwischenaktivierungen visuell nicht aussagekraeftig waeren
     * und der TFLite-Interpreter sie standardmaessig auch nicht
     * exponiert.
     */
    private val rng = Random(seed = 42)
    private val inputCells = Array(10) { FloatArray(10) { rng.nextFloat() * 0.4f + 0.1f } }
    private val convCells = Array(16) { FloatArray(10) { rng.nextFloat() * 0.85f + 0.15f } }
    private val poolValues = FloatArray(16) { rng.nextFloat() * 0.8f + 0.2f }
    private val outputValue = 0.78f

    /**
     * Setzt die Input-Matrix mit echten, bereits normalisierten Sensor-
     * Werten. Erwartet eine 10x10-Matrix: [sensorIndex][zeitschritt],
     * Wert in [0..1].
     */
    fun setInputCells(cells: Array<FloatArray>) {
        if (cells.size != 10) return
        for (sIdx in 0 until 10) {
            val row = cells[sIdx]
            if (row.size != 10) continue
            for (tIdx in 0 until 10) {
                inputCells[sIdx][tIdx] = row[tIdx].coerceIn(0f, 1f)
            }
        }
        invalidate()
    }

    private var animProgress = 0f  // 0..4, durchlaeuft die vier Schichten
    private val animator = ValueAnimator.ofFloat(0f, 4f).apply {
        duration = 4500L
        repeatCount = ValueAnimator.INFINITE
        addUpdateListener {
            animProgress = it.animatedValue as Float
            invalidate()
        }
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        if (!animator.isStarted) animator.start()
    }

    override fun onDetachedFromWindow() {
        animator.cancel()
        super.onDetachedFromWindow()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0 || h <= 0) return

        val padH = dp(12f)
        val rightLabelW = dp(110f)
        val plotL = padH
        val plotR = w - padH - rightLabelW
        val plotW = plotR - plotL

        // Vertikale Aufteilung in 4 Layer-Blocks + Pfeile dazwischen
        val layerHeights = listOf(0.34f, 0.26f, 0.20f, 0.20f)
        val arrowGap = dp(10f)

        val totalArrowGap = arrowGap * (layerHeights.size - 1)
        val totalLayerH = h - totalArrowGap
        val layerYs = mutableListOf<Pair<Float, Float>>()
        var yCursor = 0f
        for (frac in layerHeights) {
            val hh = totalLayerH * frac
            layerYs += yCursor to (yCursor + hh)
            yCursor += hh + arrowGap
        }

        // ------------------ Layer 1: Input ------------------
        val (l1Top, l1Bot) = layerYs[0]
        val intensity1 = layerActivation(0)
        drawInputMatrix(canvas, plotL, l1Top, plotR, l1Bot, intensity1)
        drawSideLabel(canvas, plotR + dp(8f), (l1Top + l1Bot) / 2f,
            "Eingabe", "10 Sensoren x 10 Schritte")

        // Pfeil
        drawArrow(canvas, (plotL + plotR) / 2f, l1Bot, (plotL + plotR) / 2f, l1Bot + arrowGap)

        // ------------------ Layer 2: Conv1D Feature Maps ------------------
        val (l2Top, l2Bot) = layerYs[1]
        val intensity2 = layerActivation(1)
        drawFeatureMaps(canvas, plotL, l2Top, plotR, l2Bot, intensity2)
        drawSideLabel(canvas, plotR + dp(8f), (l2Top + l2Bot) / 2f,
            "Conv1D", "16 Filter, Kernel 3")

        drawArrow(canvas, (plotL + plotR) / 2f, l2Bot, (plotL + plotR) / 2f, l2Bot + arrowGap)

        // ------------------ Layer 3: Pooled Values ------------------
        val (l3Top, l3Bot) = layerYs[2]
        val intensity3 = layerActivation(2)
        drawPoolBars(canvas, plotL, l3Top, plotR, l3Bot, intensity3)
        drawSideLabel(canvas, plotR + dp(8f), (l3Top + l3Bot) / 2f,
            "Pooling", "16 Werte gemittelt")

        drawArrow(canvas, (plotL + plotR) / 2f, l3Bot, (plotL + plotR) / 2f, l3Bot + arrowGap)

        // ------------------ Layer 4: Dense Output ------------------
        val (l4Top, l4Bot) = layerYs[3]
        val intensity4 = layerActivation(3)
        drawDenseOutput(canvas, plotL, l4Top, plotR, l4Bot, intensity4)
        drawSideLabel(canvas, plotR + dp(8f), (l4Top + l4Bot) / 2f,
            "Dense", "1 Vorhersage")
    }

    /**
     * Intensitaet pro Layer, basierend auf [animProgress].
     * Wenn die "Forward-Welle" gerade an dieser Schicht ist, geht
     * der Wert auf ~1; sonst dimmt er auf 0.35 ab.
     */
    private fun layerActivation(layerIndex: Int): Float {
        val dist = abs(animProgress - layerIndex)
        return if (dist > 1f) 0.35f else {
            // Smooth peak bei dist == 0
            val pulse = sin((1f - dist) * PI / 2).toFloat()
            0.35f + 0.65f * pulse
        }
    }

    private fun drawInputMatrix(
        canvas: Canvas, l: Float, t: Float, r: Float, b: Float, intensity: Float
    ) {
        // 10x10 Matrix
        val cols = 10; val rows = 10
        val gap = dp(1.5f)
        val w = (r - l - gap * (cols - 1)) / cols
        val hh = (b - t - gap * (rows - 1)) / rows
        for (rIdx in 0 until rows) {
            for (cIdx in 0 until cols) {
                val v = inputCells[rIdx][cIdx]
                val alpha = (60 + 195 * v * intensity).toInt().coerceIn(60, 255)
                cellPaint.color = blend(cellBase, cellActive, v)
                cellPaint.alpha = alpha
                val x = l + cIdx * (w + gap)
                val y = t + rIdx * (hh + gap)
                canvas.drawRoundRect(
                    RectF(x, y, x + w, y + hh),
                    dp(1.5f), dp(1.5f), cellPaint
                )
            }
        }
    }

    private fun drawFeatureMaps(
        canvas: Canvas, l: Float, t: Float, r: Float, b: Float, intensity: Float
    ) {
        val rows = 16
        val gap = dp(1f)
        val rowH = (b - t - gap * (rows - 1)) / rows
        for (i in 0 until rows) {
            val y = t + i * (rowH + gap)
            // Streifen-Hintergrund
            cellPaint.color = cellBase
            cellPaint.alpha = 90
            canvas.drawRoundRect(RectF(l, y, r, y + rowH), dp(1f), dp(1f), cellPaint)
            // Pulsierende Aktivierungs-Punkte entlang des Streifens
            val cells = convCells[i]
            val wPer = (r - l) / cells.size
            for (j in cells.indices) {
                val v = cells[j]
                cellPaint.color = brandPrimary
                cellPaint.alpha = (40 + 215 * v * intensity).toInt().coerceIn(20, 255)
                val cx = l + j * wPer + wPer / 2f
                canvas.drawCircle(cx, y + rowH / 2f, rowH * 0.42f, cellPaint)
            }
        }
    }

    private fun drawPoolBars(
        canvas: Canvas, l: Float, t: Float, r: Float, b: Float, intensity: Float
    ) {
        val cols = 16
        val gap = dp(2f)
        val barW = (r - l - gap * (cols - 1)) / cols
        for (i in 0 until cols) {
            val v = poolValues[i]
            val barH = (b - t) * v
            val x = l + i * (barW + gap)
            val y0 = b
            val y1 = b - barH
            // Hintergrund (volle Höhe)
            cellPaint.color = cellBase
            cellPaint.alpha = 80
            canvas.drawRoundRect(RectF(x, t, x + barW, b), dp(2f), dp(2f), cellPaint)
            // Aktiver Bar
            cellPaint.color = brandPrimary
            cellPaint.alpha = (80 + 175 * intensity).toInt().coerceIn(80, 255)
            canvas.drawRoundRect(RectF(x, y1, x + barW, y0), dp(2f), dp(2f), cellPaint)
        }
    }

    private fun drawDenseOutput(
        canvas: Canvas, l: Float, t: Float, r: Float, b: Float, intensity: Float
    ) {
        val cx = (l + r) / 2f
        val cy = (t + b) / 2f
        val radius = ((b - t) / 2f) - dp(4f)
        // Glow ring (pulsing)
        val glowAlpha = (120 * intensity).toInt().coerceIn(20, 200)
        brandFillPaint.color = brandPrimary
        brandFillPaint.alpha = glowAlpha
        canvas.drawCircle(cx, cy, radius + dp(8f), brandFillPaint)

        // Solid kernel
        brandFillPaint.alpha = 255
        canvas.drawCircle(cx, cy, radius * 0.7f, brandFillPaint)
        canvas.drawCircle(cx, cy, radius, brandStrokePaint)
    }

    private fun drawArrow(canvas: Canvas, x1: Float, y1: Float, x2: Float, y2: Float) {
        canvas.drawLine(x1, y1, x2, y2, arrowPaint)
        val ah = dp(4f)
        canvas.drawLine(x2, y2, x2 - ah, y2 - ah, arrowPaint)
        canvas.drawLine(x2, y2, x2 + ah, y2 - ah, arrowPaint)
    }

    private fun drawSideLabel(
        canvas: Canvas, x: Float, yCenter: Float, title: String, sub: String
    ) {
        canvas.drawText(title, x, yCenter - dp(2f), labelPaint)
        canvas.drawText(sub, x, yCenter + dp(12f), subLabelPaint)
    }

    /** Lineare Farb-Interpolation, kompakt. */
    private fun blend(a: Int, b: Int, t: Float): Int {
        val tc = t.coerceIn(0f, 1f)
        val ar = (a shr 16) and 0xFF; val ag = (a shr 8) and 0xFF; val ab = a and 0xFF
        val br = (b shr 16) and 0xFF; val bg = (b shr 8) and 0xFF; val bb = b and 0xFF
        val r = (ar + (br - ar) * tc).toInt()
        val g = (ag + (bg - ag) * tc).toInt()
        val bl = (ab + (bb - ab) * tc).toInt()
        return (0xFF shl 24) or (r shl 16) or (g shl 8) or bl
    }

    private fun dp(value: Float): Float = value * resources.displayMetrics.density
}

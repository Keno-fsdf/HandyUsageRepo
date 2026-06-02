package com.batterypredictor.datacollector

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import kotlin.math.abs
import kotlin.math.sin

/**
 * Animierte Datenfluss-Visualisierung fuer den Algorithmus-Tab.
 *
 * Layout (horizontal):
 *   [10 Sensor-Dots (links, pulsierend)]
 *      --> animierte Partikel fliessen nach rechts --->
 *   [Modell-Box (Mitte, leuchtet)]
 *      --> Partikel kommen rechts wieder raus --->
 *   [Vorhersage-Kreis (rechts, gross)]
 *
 * Komplett ohne dritt-library. Endlos-Loop, ca. 3 Sekunden pro Zyklus.
 */
class DataflowView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val brandPrimary = ContextCompat.getColor(context, R.color.brand_primary)
    private val predictionText = ContextCompat.getColor(context, R.color.prediction_text)
    private val sensorBarActive = ContextCompat.getColor(context, R.color.sensor_bar_active)
    private val cardOutline = ContextCompat.getColor(context, R.color.card_outline)

    // Pinsel fuer alle Zeichen-Operationen, mit verschiedenen Configs.
    private val sensorPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = sensorBarActive
        style = Paint.Style.FILL
    }
    private val sensorGlowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = sensorBarActive
        style = Paint.Style.FILL
        alpha = 60
    }
    private val particlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = brandPrimary
        style = Paint.Style.FILL
    }
    private val modelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = predictionText
        style = Paint.Style.STROKE
        strokeWidth = dp(2f)
    }
    private val modelFillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = predictionText
        style = Paint.Style.FILL
        alpha = 16
    }
    private val modelGlowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = brandPrimary
        style = Paint.Style.FILL
        alpha = 0
    }
    private val outputPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = predictionText
        style = Paint.Style.FILL
    }
    private val outputRingPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = brandPrimary
        style = Paint.Style.STROKE
        strokeWidth = dp(3f)
    }
    private val gridPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = cardOutline
        style = Paint.Style.STROKE
        strokeWidth = dp(1f)
    }

    /** 0..1 -- ein voller Animationszyklus dauert ca. 3 Sekunden. */
    private var progress = 0f

    /** Phase fuer das Pulsen der Sensoren (entkoppelt vom Partikel-Flow). */
    private var pulsePhase = 0f

    private val animator = ValueAnimator.ofFloat(0f, 1f).apply {
        duration = 3000L
        repeatCount = ValueAnimator.INFINITE
        addUpdateListener {
            progress = it.animatedValue as Float
            pulsePhase = (pulsePhase + 0.012f) % 1f
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

        // Layout: Sensoren bei x=15%, Modell-Box bei 45%-65%, Output bei x=87%
        val sensorX = w * 0.12f
        val modelLeft = w * 0.40f
        val modelRight = w * 0.66f
        val outputX = w * 0.88f
        val midY = h / 2f
        val modelTop = h * 0.18f
        val modelBottom = h * 0.82f

        // ---- Hintergrund-Grid ----
        // Leichte horizontale Linien, gibt Tiefe.
        val gridStep = h / 6f
        for (i in 0..6) {
            val y = i * gridStep
            canvas.drawLine(0f, y, w, y, gridPaint.apply { alpha = 30 })
        }

        // ---- 10 Sensor-Dots links (pulsing) ----
        val sensorCount = 10
        val sensorSpacing = h / (sensorCount + 1)
        val pulse = (sin(pulsePhase * 2 * Math.PI).toFloat() + 1f) / 2f
        val sensorRadius = dp(3.5f) + pulse * dp(1.5f)
        val glowRadius = dp(7f) + pulse * dp(3f)

        for (i in 0 until sensorCount) {
            val y = sensorSpacing * (i + 1)
            canvas.drawCircle(sensorX, y, glowRadius, sensorGlowPaint)
            canvas.drawCircle(sensorX, y, sensorRadius, sensorPaint)
        }

        // ---- Verbindungslinien Sensoren -> Modell ----
        // Subtile Linien, damit der Flow nachvollziehbar ist.
        val connPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = cardOutline
            style = Paint.Style.STROKE
            strokeWidth = dp(1f)
            alpha = 80
        }
        for (i in 0 until sensorCount) {
            val y = sensorSpacing * (i + 1)
            canvas.drawLine(sensorX + dp(6f), y, modelLeft, midY, connPaint)
        }

        // ---- Modell-Box mit Glow (pulst staerker waehrend Partikel drin sind) ----
        val box = RectF(modelLeft, modelTop, modelRight, modelBottom)
        val corners = dp(12f)

        // Glow: am staerksten in der "Mitte" des Zyklus, wenn Partikel im Modell sind
        val particleInModel = (progress > 0.35f && progress < 0.65f)
        modelGlowPaint.alpha = if (particleInModel) (140 * (1f - abs(progress - 0.5f) * 2f)).toInt() else 0
        if (modelGlowPaint.alpha > 0) {
            canvas.drawRoundRect(
                box.left - dp(8f), box.top - dp(8f),
                box.right + dp(8f), box.bottom + dp(8f),
                corners + dp(4f), corners + dp(4f),
                modelGlowPaint
            )
        }
        canvas.drawRoundRect(box, corners, corners, modelFillPaint)
        canvas.drawRoundRect(box, corners, corners, modelPaint)

        // Mini-Knoten innerhalb der Box, deuten Neuronen an
        val nodePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = predictionText
            style = Paint.Style.FILL
            alpha = 130
        }
        val cx = (modelLeft + modelRight) / 2f
        val nodeRadius = dp(3f)
        // 3 Reihen x 2 Knoten
        for (r in 0..2) {
            val y = modelTop + (modelBottom - modelTop) * (0.25f + r * 0.25f)
            canvas.drawCircle(cx - dp(14f), y, nodeRadius, nodePaint)
            canvas.drawCircle(cx + dp(14f), y, nodeRadius, nodePaint)
        }

        // Label im Model-Box-Bereich
        val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = predictionText
            textSize = dp(11f)
            textAlign = Paint.Align.CENTER
            isFakeBoldText = true
        }
        canvas.drawText("TinyML", cx, modelTop - dp(6f), labelPaint)

        // ---- Animierte Partikel ----
        // Drei Partikel-Wellen pro Zyklus, leicht versetzt, in der Modell-Box gebuendelt.
        val particleCount = 3
        for (p in 0 until particleCount) {
            // Phase pro Partikel um 0.07 versetzt, ergibt einen "Strom" statt Einzel-Punkten
            val offset = p * 0.07f
            val pPhase = ((progress + offset) % 1f)
            val particle = particlePosition(
                pPhase,
                sensorX, modelLeft, modelRight, outputX, midY
            )
            val baseAlpha = ((1f - abs(pPhase - 0.5f)) * 255).toInt().coerceIn(60, 255)
            particlePaint.alpha = baseAlpha
            canvas.drawCircle(particle.first, particle.second, dp(4.5f), particlePaint)
        }

        // ---- Output-Kreis rechts ----
        canvas.drawCircle(outputX, midY, dp(16f), outputPaint)
        canvas.drawCircle(outputX, midY, dp(22f), outputRingPaint)

        // Output-Label
        val outLabelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = predictionText
            textSize = dp(10f)
            textAlign = Paint.Align.CENTER
            isFakeBoldText = true
        }
        canvas.drawText("Vorhersage", outputX, midY + dp(40f), outLabelPaint)

        // Sensor-Label links
        canvas.drawText("10 Sensoren", sensorX, h - dp(6f), outLabelPaint)
    }

    /**
     * Berechnet die Position eines Partikels in einem Animationszyklus.
     *
     *   pPhase in [0..1]:
     *     0.0  -> startet bei sensorX (links)
     *     0.4  -> erreicht modelLeft (Eintritt)
     *     0.6  -> verlaesst modelRight (Austritt)
     *     1.0  -> Ende bei outputX
     */
    private fun particlePosition(
        pPhase: Float,
        sensorX: Float, modelLeft: Float, modelRight: Float, outputX: Float, midY: Float
    ): Pair<Float, Float> {
        return when {
            pPhase < 0.4f -> {
                // Sensoren -> Modell-Eingang
                val t = pPhase / 0.4f
                val x = sensorX + (modelLeft - sensorX) * t
                Pair(x, midY)
            }
            pPhase < 0.6f -> {
                // In der Modell-Box: bleibt in der Mitte (deutet "Verarbeitung" an)
                val x = modelLeft + (modelRight - modelLeft) * ((pPhase - 0.4f) / 0.2f)
                Pair(x, midY)
            }
            else -> {
                // Modell-Ausgang -> Vorhersage-Kreis
                val t = (pPhase - 0.6f) / 0.4f
                val x = modelRight + (outputX - modelRight) * t
                Pair(x, midY)
            }
        }
    }

    private fun dp(value: Float): Float = value * resources.displayMetrics.density

    @Suppress("unused")
    private fun makeGlowColor(@Suppress("SameParameterValue") baseColor: Int, alpha: Int): Int {
        return Color.argb(alpha, Color.red(baseColor), Color.green(baseColor), Color.blue(baseColor))
    }
}

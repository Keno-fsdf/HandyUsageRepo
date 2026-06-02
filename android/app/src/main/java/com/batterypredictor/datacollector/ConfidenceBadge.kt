package com.batterypredictor.datacollector

import android.content.Context
import android.util.AttributeSet
import android.view.LayoutInflater
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat

/**
 * Kleine Pille mit Punkt + Text, die die [ConfidenceLevel] anzeigt.
 * Wird im LiveFragment direkt unter der Hauptvorhersage angezeigt.
 */
class ConfidenceBadge @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : LinearLayout(context, attrs, defStyleAttr) {

    private val dotView: TextView
    private val labelView: TextView

    init {
        LayoutInflater.from(context).inflate(R.layout.view_confidence_badge, this, true)
        orientation = HORIZONTAL
        dotView = findViewById(R.id.confidenceDot)
        labelView = findViewById(R.id.confidenceLabel)
        setConfidence(ConfidenceLevel.LOW)
    }

    fun setConfidence(level: ConfidenceLevel) {
        when (level) {
            ConfidenceLevel.HIGH -> {
                background = ContextCompat.getDrawable(context, R.drawable.bg_confidence_high)
                dotView.text = "●"
                dotView.setTextColor(ContextCompat.getColor(context, R.color.confidence_high_text))
                labelView.text = context.getString(R.string.live_confidence_high)
                labelView.setTextColor(ContextCompat.getColor(context, R.color.confidence_high_text))
            }
            ConfidenceLevel.MEDIUM -> {
                background = ContextCompat.getDrawable(context, R.drawable.bg_confidence_med)
                dotView.text = "●"
                dotView.setTextColor(ContextCompat.getColor(context, R.color.confidence_med_text))
                labelView.text = context.getString(R.string.live_confidence_med)
                labelView.setTextColor(ContextCompat.getColor(context, R.color.confidence_med_text))
            }
            ConfidenceLevel.LOW -> {
                background = ContextCompat.getDrawable(context, R.drawable.bg_confidence_low)
                dotView.text = "●"
                dotView.setTextColor(ContextCompat.getColor(context, R.color.confidence_low_text))
                labelView.text = context.getString(R.string.live_confidence_low)
                labelView.setTextColor(ContextCompat.getColor(context, R.color.confidence_low_text))
            }
        }
    }
}

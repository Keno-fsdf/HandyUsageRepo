package com.batterypredictor.datacollector

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment

/**
 * Live-Tab: zeigt die aktuelle Vorhersage gross und prominent, ein
 * Confidence-Badge und darunter alle 10 Sensor-Werte, die das Modell
 * gerade als Eingabe sieht. Update kommt via Broadcast vom
 * [DataCollectorService].
 *
 * Ziel: der Nutzer (und der Prof) "schaut dem Modell beim Denken zu".
 */
class LiveFragment : Fragment() {

    private lateinit var predictionLabel: TextView
    private lateinit var predictionText: TextView
    private lateinit var predictionDetail: TextView
    private lateinit var confidenceBadge: ConfidenceBadge
    private lateinit var sensorsContainer: LinearLayout

    // Sensor-Spec: Label-Key, Emoji, Wert-Formatter, Balken-Funktion (0..1) oder null
    private data class SensorSpec(
        val labelRes: Int,
        val emoji: String,
        val key: String,
        val format: (Float) -> String,
        val barRatio: ((Float) -> Float)?,
    )

    private val sensorSpecs = listOf(
        SensorSpec(R.string.sensor_battery, "🔋", "battery_level",
            { "${it.toInt()}%" }, { (it / 100f).coerceIn(0f, 1f) }),
        SensorSpec(R.string.sensor_brightness, "🔆", "brightness",
            { "${it.toInt()}%" }, { (it / 100f).coerceIn(0f, 1f) }),
        SensorSpec(R.string.sensor_screen, "📱", "screen_on",
            { if (it >= 0.5f) "an" else "aus" }, null),
        SensorSpec(R.string.sensor_app, "🎯", "active_app_category",
            { appCategoryLabel(it.toInt()) }, null),
        SensorSpec(R.string.sensor_wifi, "📶", "wifi_on",
            { if (it >= 0.5f) "verbunden" else "aus" }, null),
        SensorSpec(R.string.sensor_mobile, "📡", "mobile_data_on",
            { if (it >= 0.5f) "aktiv" else "aus" }, null),
        SensorSpec(R.string.sensor_charging, "⚡", "charging",
            { if (it >= 0.5f) "lädt" else "entlädt" }, null),
        SensorSpec(R.string.sensor_cpu, "💻", "cpu_usage",
            { "${it.toInt()}%" }, { (it / 100f).coerceIn(0f, 1f) }),
        SensorSpec(R.string.sensor_temp, "🌡", "temperature",
            { "%.1f°C".format(it) }, { ((it - 20f) / 30f).coerceIn(0f, 1f) }),
        SensorSpec(R.string.sensor_hotspot, "📡", "hotspot_on",
            { if (it >= 0.5f) "an" else "aus" }, null),
    )

    private val sensorRows = mutableListOf<SensorRow>()

    private class SensorRow(
        val container: View,
        val valueText: TextView,
        val bar: View,
        val barFull: View,
    )

    private val predictionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            updateFromBroadcast(intent)
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        val root = inflater.inflate(R.layout.fragment_live, container, false)
        predictionLabel = root.findViewById(R.id.livePredictionLabel)
        predictionText = root.findViewById(R.id.livePredictionText)
        predictionDetail = root.findViewById(R.id.livePredictionDetail)
        confidenceBadge = root.findViewById(R.id.liveConfidenceBadge)
        sensorsContainer = root.findViewById(R.id.liveSensorsContainer)

        buildSensorRows(inflater)
        return root
    }

    private fun buildSensorRows(inflater: LayoutInflater) {
        sensorsContainer.removeAllViews()
        sensorRows.clear()
        sensorSpecs.forEach { spec ->
            val row = inflater.inflate(R.layout.item_sensor_row, sensorsContainer, false)
            (row.findViewById<TextView>(R.id.sensorEmoji)).text = spec.emoji
            (row.findViewById<TextView>(R.id.sensorLabel)).text = getString(spec.labelRes)
            val valueText = row.findViewById<TextView>(R.id.sensorValue)
            val bar = row.findViewById<View>(R.id.sensorBar)
            val barFull = row.findViewById<View>(R.id.sensorBarFull)
            if (spec.barRatio == null) {
                bar.visibility = View.GONE
                barFull.visibility = View.GONE
            }
            sensorRows += SensorRow(row, valueText, bar, barFull)
            sensorsContainer.addView(row)
        }
    }

    override fun onResume() {
        super.onResume()
        val filter = IntentFilter("com.batterypredictor.PREDICTION_UPDATE")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requireContext().registerReceiver(
                predictionReceiver, filter,
                AppCompatActivity.RECEIVER_NOT_EXPORTED
            )
        } else {
            @Suppress("UnspecifiedRegisterReceiverFlag")
            requireContext().registerReceiver(predictionReceiver, filter)
        }
        showInitialState()
    }

    /**
     * Zeigt einen klaren Status, BEVOR der erste Broadcast kommt.
     * Bei laufendem Service: \glqq{}Sammle Werte\grqq{} + REFRESH triggern,
     * damit die Daten in 1-2s da sind statt erst nach dem naechsten 30s-Tick.
     * Bei gestopptem Service: klarer Hinweis, dass im Settings-Tab gestartet
     * werden muss.
     */
    private fun showInitialState() {
        val ctx = context ?: return
        val enabled = ctx.getSharedPreferences("battery_collector", AppCompatActivity.MODE_PRIVATE)
            .getBoolean("service_enabled", false)
        if (enabled) {
            predictionLabel.text = getString(R.string.live_prediction_label)
            predictionText.text = getString(R.string.live_initial_main)
            predictionDetail.text = getString(R.string.live_initial_sub)
            confidenceBadge.visibility = View.INVISIBLE
            // Sofort einen Messpunkt vom Service holen, statt 30s zu warten.
            try {
                val refresh = Intent(ctx, DataCollectorService::class.java).apply {
                    action = "REFRESH"
                }
                androidx.core.content.ContextCompat.startForegroundService(ctx, refresh)
            } catch (_: Exception) { /* best-effort */ }
        } else {
            predictionLabel.text = getString(R.string.live_status_label)
            predictionText.text = getString(R.string.live_service_stopped_main)
            predictionDetail.text = getString(R.string.live_service_stopped_sub)
            confidenceBadge.visibility = View.INVISIBLE
        }
    }

    override fun onPause() {
        try { requireContext().unregisterReceiver(predictionReceiver) } catch (_: Exception) {}
        super.onPause()
    }

    private fun updateFromBroadcast(intent: Intent) {
        val prediction = intent.getFloatExtra("prediction", -1f)
        val bufferSize = intent.getIntExtra("buffer_size", 0)
        val batteryLevel = intent.getFloatExtra("battery_level", -1f)
        val isCharging = intent.getFloatExtra("charging", 0f) >= 0.5f
        val isFull = batteryLevel >= 99f

        // Hauptvorhersage -- mit Sonderfaellen "laedt" und "voll".
        // Label oben wird dynamisch angepasst, damit "AKKU NOCH Laedt" nicht
        // entsteht.
        when {
            isCharging -> {
                predictionLabel.text = getString(R.string.live_status_label)
                predictionText.text = getString(R.string.live_charging_main)
                predictionDetail.text = getString(
                    R.string.live_charging_sub, batteryLevel.toInt()
                )
                confidenceBadge.visibility = View.INVISIBLE
            }
            isFull -> {
                predictionLabel.text = getString(R.string.live_status_label)
                predictionText.text = getString(R.string.live_full_main)
                predictionDetail.text = getString(R.string.live_full_sub)
                confidenceBadge.visibility = View.INVISIBLE
            }
            prediction >= 0f -> {
                predictionLabel.text = getString(R.string.live_prediction_label)
                predictionText.text = formatHoursShort(prediction)
                predictionDetail.text = "Akkustand ${batteryLevel.toInt()}%"
                val level = ConfidenceLevel.fromBufferAndBattery(bufferSize, batteryLevel)
                confidenceBadge.setConfidence(level)
                confidenceBadge.visibility = View.VISIBLE
            }
            else -> {
                predictionLabel.text = getString(R.string.live_prediction_label)
                predictionText.text = getString(R.string.live_buffer_label) + "… ${bufferSize}/10"
                val remaining = (10 - bufferSize).coerceAtLeast(0)
                predictionDetail.text = "Noch $remaining Messungen à 30 Sekunden"
                confidenceBadge.visibility = View.INVISIBLE
            }
        }

        // Live-Sensoren
        sensorSpecs.forEachIndexed { i, spec ->
            val value = intent.getFloatExtra(spec.key, Float.NaN)
            val row = sensorRows[i]
            if (value.isNaN()) {
                row.valueText.text = "—"
                row.barFull.layoutParams = row.barFull.layoutParams.apply {
                    width = 0
                }
                row.barFull.requestLayout()
            } else {
                row.valueText.text = spec.format(value)
                spec.barRatio?.let { ratioFn ->
                    val ratio = ratioFn(value)
                    val parent = row.bar.layoutParams.width
                    val target = (parent * ratio).toInt().coerceAtLeast(0)
                    row.barFull.layoutParams = row.barFull.layoutParams.apply {
                        width = if (target > 0) target else 1
                    }
                    row.barFull.requestLayout()
                }
            }
        }
    }

    private fun formatHoursShort(h: Float): String {
        val hours = h.toInt()
        val mins = ((h - hours) * 60).toInt()
        return "${hours}h ${mins}min"
    }

    companion object {
        fun appCategoryLabel(cat: Int): String = when (cat) {
            0 -> "Leerlauf"
            1 -> "Social"
            2 -> "Video"
            3 -> "Spiele"
            4 -> "Browser"
            5 -> "Produktiv"
            else -> "—"
        }
    }
}

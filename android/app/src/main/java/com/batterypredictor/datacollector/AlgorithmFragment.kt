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
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment

/**
 * Algorithmus-Tab: zeigt
 *   1. eine animierte Datenfluss-Visualisierung (DataflowView, statisch animiert)
 *   2. einen Live-Akku-Verlaufs-Chart mit Vorhersage-Extension (BatteryHistoryChart)
 *   3. die textuelle 4-Schritt-Erklaerung + USP-Block (statisch im XML)
 *
 * Reagiert auf den Prediction-Broadcast vom DataCollectorService: bei jedem
 * neuen Datenpunkt wird die Sparkline neu aus der CSV gelesen.
 */
class AlgorithmFragment : Fragment() {

    private var batteryChart: BatteryHistoryChart? = null
    private var convLayer: ConvLayerView? = null

    /**
     * Ringpuffer der letzten 10 Sensor-Snapshots. Index 0 = aelteste
     * Messung, letztes Element = juengste. Jeder Snapshot enthaelt die
     * 10 Features in derselben Reihenfolge wie das Modell sie als Input
     * erwartet:
     *   0 battery_level | 1 brightness | 2 screen_on | 3 active_app_category
     *   4 wifi_on | 5 mobile_data_on | 6 charging | 7 cpu_usage
     *   8 temperature | 9 hotspot_on
     */
    private val sensorHistory = ArrayDeque<FloatArray>(10)

    private val predictionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val prediction = intent.getFloatExtra("prediction", -1f)
            refreshChart(prediction)
            pushSnapshotFromBroadcast(intent)
            pushHistoryToConvLayer()
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        val root = inflater.inflate(R.layout.fragment_algorithm, container, false)
        batteryChart = root.findViewById(R.id.algBatteryChart)
        convLayer = root.findViewById(R.id.algConvLayer)

        // Tap auf die Architektur-Karte oeffnet den Deep-Dive-Sheet
        root.findViewById<View>(R.id.algArchCard).setOnClickListener {
            ModelDeepDiveSheet().show(parentFragmentManager, ModelDeepDiveSheet.TAG)
        }

        return root
    }

    /**
     * Liest die 10 Sensor-Features aus dem PREDICTION_UPDATE-Broadcast,
     * normalisiert sie auf 0..1 (jedes Feature mit seinem eigenen
     * Wertebereich) und schiebt das Ergebnis in den Ringpuffer.
     */
    private fun pushSnapshotFromBroadcast(intent: Intent) {
        val snap = floatArrayOf(
            (intent.getFloatExtra("battery_level", 0f) / 100f).coerceIn(0f, 1f),
            (intent.getFloatExtra("brightness", 0f) / 100f).coerceIn(0f, 1f),
            intent.getFloatExtra("screen_on", 0f).coerceIn(0f, 1f),
            (intent.getFloatExtra("active_app_category", 0f) / 5f).coerceIn(0f, 1f),
            intent.getFloatExtra("wifi_on", 0f).coerceIn(0f, 1f),
            intent.getFloatExtra("mobile_data_on", 0f).coerceIn(0f, 1f),
            intent.getFloatExtra("charging", 0f).coerceIn(0f, 1f),
            (intent.getFloatExtra("cpu_usage", 0f) / 100f).coerceIn(0f, 1f),
            ((intent.getFloatExtra("temperature", 25f) - 20f) / 30f).coerceIn(0f, 1f),
            intent.getFloatExtra("hotspot_on", 0f).coerceIn(0f, 1f),
        )
        if (sensorHistory.size >= 10) sensorHistory.removeFirst()
        sensorHistory.addLast(snap)
    }

    /**
     * Baut aus dem Ringpuffer die 10x10-Input-Matrix
     * (Sensoren x Zeitschritte) und schickt sie an die ConvLayerView,
     * damit die "Eingabe"-Schicht der Architektur live mit echten Werten
     * pulsiert. Fehlende Zeitschritte (Buffer noch nicht voll) bleiben
     * als 0.
     */
    private fun pushHistoryToConvLayer() {
        val view = convLayer ?: return
        val grid = Array(10) { sensor ->
            FloatArray(10) { t ->
                if (t < sensorHistory.size) sensorHistory[t][sensor] else 0f
            }
        }
        view.setInputCells(grid)
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
        // Direkt einmal initial laden, ohne auf den naechsten Broadcast warten zu muessen.
        refreshChart(predictionHours = -1f)
    }

    override fun onPause() {
        try { requireContext().unregisterReceiver(predictionReceiver) } catch (_: Exception) {}
        super.onPause()
    }

    private fun refreshChart(predictionHours: Float) {
        val ctx = context ?: return
        val csv = BatteryDataLogger.getInstance(ctx).getFile()
        batteryChart?.refresh(csv, predictionHours)
    }
}

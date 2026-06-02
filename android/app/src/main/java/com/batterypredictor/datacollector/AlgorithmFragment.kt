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

    private val predictionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val prediction = intent.getFloatExtra("prediction", -1f)
            refreshChart(prediction)
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        val root = inflater.inflate(R.layout.fragment_algorithm, container, false)
        batteryChart = root.findViewById(R.id.algBatteryChart)
        return root
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

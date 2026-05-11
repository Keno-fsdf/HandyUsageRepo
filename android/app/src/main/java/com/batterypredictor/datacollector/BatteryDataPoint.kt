package com.batterypredictor.datacollector

/**
 * Ein einzelner Datenpunkt mit 10 Features + Vergleichswerte.
 *
 * Spaltenreihenfolge in der CSV ist Vertrag mit der Python-Pipeline
 * (configs/default.yaml feature-Liste). Aenderungen hier benoetigen
 * eine Anpassung dort und ein erneutes Training.
 */
data class BatteryDataPoint(
    val timestamp: Long,

    // Features fuer das TinyML-Modell (Reihenfolge muss zur Python-Config passen):
    val batteryLevel: Float,     // 0-100
    val screenOn: Int,           // 0/1
    val brightness: Float,       // 0-100
    val activeAppCategory: Int,  // 0-5
    val wifiOn: Int,             // 0/1
    val mobileDataOn: Int,       // 0/1
    val charging: Int,           // 0/1
    val cpuUsage: Float,         // 0-100
    val temperature: Float,      // °C
    val hotspotOn: Int,          // 0/1

    // Vergleichswerte (KEINE Features fuer das Modell):
    val systemEstimateMin: Float,// Google API in Minuten (-1 = nicht verfuegbar)
    val systemPersonalized: Int, // isBatteryDischargePredictionPersonalized: 0/1/-1=unknown
    val ownPredictionH: Float,   // TinyML-Vorhersage in Stunden (-1 = Buffer noch leer)
    val linearBaselineH: Float,  // Naive Linear: charge_counter / current_avg (-1 = nicht verfuegbar)
) {
    fun toCsvLine(): String {
        return "${batteryLevel.fmt()},${screenOn},${brightness.fmt()},${activeAppCategory}," +
               "${wifiOn},${mobileDataOn},${charging},${cpuUsage.fmt()}," +
               "${temperature.fmt()},${hotspotOn}," +
               "${systemEstimateMin.fmt()},${systemPersonalized}," +
               "${ownPredictionH.fmt(3)},${linearBaselineH.fmt(3)}"
    }

    private fun Float.fmt(decimals: Int = 1): String =
        String.format(java.util.Locale.US, "%.${decimals}f", this)

    companion object {
        const val CSV_HEADER =
            "battery_level,screen_on,brightness,active_app_category," +
            "wifi_on,mobile_data_on,charging,cpu_usage,temperature,hotspot_on," +
            "system_estimate_min,system_personalized," +
            "own_prediction_h,linear_baseline_h"
    }
}

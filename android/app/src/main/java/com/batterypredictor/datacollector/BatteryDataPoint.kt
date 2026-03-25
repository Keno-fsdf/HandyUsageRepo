package com.batterypredictor.datacollector

/**
 * Ein einzelner Datenpunkt mit 10 Features + System-Schätzung zum Vergleich.
 */
data class BatteryDataPoint(
    val timestamp: Long,
    val batteryLevel: Float,     // 0-100
    val screenOn: Int,           // 0/1
    val brightness: Float,       // 0-100
    val activeAppCategory: Int,  // 0-5
    val wifiOn: Int,             // 0/1
    val mobileDataOn: Int,       // 0/1
    val charging: Int,           // 0/1
    val cpuUsage: Float,         // 0-100
    val temperature: Float,      // °C (z.B. 25.0 - 45.0)
    val hotspotOn: Int,          // 0/1
    val systemEstimateMin: Float,// Native Android-Schätzung in Minuten (-1 = nicht verfügbar)
) {
    fun toCsvLine(): String {
        return "${batteryLevel.fmt()},${screenOn},${brightness.fmt()},${activeAppCategory}," +
               "${wifiOn},${mobileDataOn},${charging},${cpuUsage.fmt()}," +
               "${temperature.fmt()},${hotspotOn},${systemEstimateMin.fmt()}"
    }

    private fun Float.fmt(): String = String.format(java.util.Locale.US, "%.1f", this)

    companion object {
        const val CSV_HEADER =
            "battery_level,screen_on,brightness,active_app_category," +
            "wifi_on,mobile_data_on,charging,cpu_usage,temperature,hotspot_on," +
            "system_estimate_min"
    }
}

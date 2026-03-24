package com.batterypredictor.datacollector

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat

/**
 * Startet den DataCollectorService automatisch nach Geräte-Neustart,
 * falls er vorher aktiv war.
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            val prefs = context.getSharedPreferences("battery_collector", Context.MODE_PRIVATE)
            if (prefs.getBoolean("service_enabled", false)) {
                val serviceIntent = Intent(context, DataCollectorService::class.java)
                ContextCompat.startForegroundService(context, serviceIntent)
            }
        }
    }
}

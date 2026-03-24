package com.batterypredictor.datacollector

import android.app.*
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.*
import android.provider.Settings
import android.app.usage.UsageStatsManager
import androidx.core.app.NotificationCompat
import java.io.BufferedReader
import java.io.FileReader

/**
 * Foreground Service der alle 5 Minuten die 8 Battery-Features sammelt
 * und in eine CSV-Datei schreibt.
 *
 * Läuft auch wenn die App geschlossen ist (Foreground Notification).
 */
class DataCollectorService : Service() {

    companion object {
        const val CHANNEL_ID = "battery_collector_channel"
        const val NOTIFICATION_ID = 1
        const val INTERVAL_MS = 30 * 1000L // 30 Sekunden

        // App-Kategorie-Mapping: Package-Prefix -> Kategorie
        // 0=idle, 1=social, 2=video, 3=gaming, 4=browser, 5=productivity
        private val APP_CATEGORIES = mapOf(
            // Social
            "com.instagram" to 1, "com.facebook" to 1, "com.twitter" to 1,
            "com.whatsapp" to 1, "com.snapchat" to 1, "org.telegram" to 1,
            "com.tiktok" to 1, "com.zhiliaoapp.musically" to 1, // TikTok alt
            "com.discord" to 1, "com.reddit" to 1, "com.pinterest" to 1,
            "com.linkedin" to 1, "com.viber" to 1, "com.skype" to 1,
            "org.thunderdog.challegram" to 1, // Telegram X
            "com.bereal" to 1, "com.tumblr" to 1,
            // Video/Streaming
            "com.google.android.youtube" to 2, "com.netflix" to 2,
            "com.amazon.avod" to 2, "com.disney" to 2, "tv.twitch" to 2,
            "com.spotify" to 2, "com.soundcloud" to 2, "com.deezer" to 2,
            "com.apple.android.music" to 2, "com.plexapp" to 2,
            // Gaming (explizite)
            "com.supercell" to 3, "com.kiloo" to 3, "com.king" to 3,
            "com.mojang" to 3, "com.ea" to 3, "com.gameloft" to 3,
            "com.epicgames" to 3, "com.miHoYo" to 3, "com.riotgames" to 3,
            // Browser
            "com.google.android.apps.chrome" to 4, "org.mozilla" to 4,
            "com.opera" to 4, "com.brave" to 4, "com.mi.globalbrowser" to 4,
            "com.UCMobile" to 4, "com.kiwibrowser" to 4,
            "com.android.chrome" to 4, "com.sec.android.app.sbrowser" to 4,
            // Productivity
            "com.google.android.apps.docs" to 5, "com.microsoft" to 5,
            "com.slack" to 5, "com.google.android.gm" to 5,
            "com.google.android.apps.meetings" to 5, "us.zoom" to 5,
            "com.google.android.calendar" to 5,
            // System/Idle
            "com.miui.home" to 0, "com.miui.securitycenter" to 0,
            "com.android.launcher" to 0, "com.google.android.apps.nexuslauncher" to 0,
            "com.android.systemui" to 0, "com.android.settings" to 0,
            "com.miui.miwallpaper" to 0, "com.android.deskclock" to 0,
            "com.xiaomi" to 0,
        )
    }

    private val handler = Handler(Looper.getMainLooper())
    private lateinit var logger: BatteryDataLogger
    private var sessionId = ""

    private val collectRunnable = object : Runnable {
        override fun run() {
            collectAndLog()
            handler.postDelayed(this, INTERVAL_MS)
        }
    }

    override fun onCreate() {
        super.onCreate()
        logger = BatteryDataLogger(this)
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Neue Session bei jedem Service-Start
        sessionId = java.util.UUID.randomUUID().toString().take(8)

        val notification = buildNotification()
        startForeground(NOTIFICATION_ID, notification)

        // Merken dass Service aktiv ist (für BootReceiver)
        getSharedPreferences("battery_collector", MODE_PRIVATE)
            .edit().putBoolean("service_enabled", true).apply()

        // Sofort erste Messung, dann alle 5 min
        handler.removeCallbacks(collectRunnable)
        handler.post(collectRunnable)

        return START_STICKY // Neustart nach Kill durch System
    }

    override fun onDestroy() {
        handler.removeCallbacks(collectRunnable)
        getSharedPreferences("battery_collector", MODE_PRIVATE)
            .edit().putBoolean("service_enabled", false).apply()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    // ========== Datensammlung ==========

    private fun collectAndLog() {
        val data = BatteryDataPoint(
            timestamp = System.currentTimeMillis(),
            batteryLevel = getBatteryLevel(),
            screenOn = if (isScreenOn()) 1 else 0,
            brightness = getScreenBrightness(),
            activeAppCategory = getActiveAppCategory(),
            wifiOn = if (isWifiConnected()) 1 else 0,
            mobileDataOn = if (isMobileDataActive()) 1 else 0,
            charging = if (isCharging()) 1 else 0,
            cpuUsage = getCpuUsage(),
            temperature = getBatteryTemperature(),
            hotspotOn = if (isHotspotOn()) 1 else 0,
        )

        logger.log(data, sessionId)

        // Notification aktualisieren mit letztem Datenpunkt
        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(NOTIFICATION_ID, buildNotification(
            "Akku: ${data.batteryLevel}% | ${data.temperature}°C | CPU: ${data.cpuUsage}% | " +
            "${logger.getCount()} Messungen"
        ))
    }

    // ---- Feature 1: Battery Level ----
    private fun getBatteryLevel(): Float {
        val bm = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY).toFloat()
    }

    // ---- Feature 2: Screen On/Off ----
    private fun isScreenOn(): Boolean {
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        return pm.isInteractive
    }

    // ---- Feature 3: Brightness (0-100) ----
    private fun getScreenBrightness(): Float {
        return try {
            val raw = Settings.System.getInt(contentResolver, Settings.System.SCREEN_BRIGHTNESS)
            // Android: 0-255 -> normalisieren auf 0-100
            (raw / 255f * 100f).coerceIn(0f, 100f)
        } catch (e: Exception) {
            50f // Fallback
        }
    }

    // ---- Feature 4: Active App Category ----
    private fun getActiveAppCategory(): Int {
        // Screen aus = idle, egal welche App zuletzt lief
        if (!isScreenOn()) return 0

        return try {
            val usm = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
            val endTime = System.currentTimeMillis()
            val startTime = endTime - 60_000 // Letzte Minute

            val stats = usm.queryUsageStats(
                UsageStatsManager.INTERVAL_DAILY, startTime, endTime
            )

            if (stats.isNullOrEmpty()) return 0

            val recentApp = stats.maxByOrNull { it.lastTimeUsed }
            val packageName = recentApp?.packageName ?: return 0

            // Package nach Kategorie auflösen
            val category = APP_CATEGORIES.entries
                .firstOrNull { packageName.startsWith(it.key) }
                ?.value ?: classifyByPackageName(packageName)

            // Unbekannte Packages loggen (damit wir sie nachmappen können)
            if (category == 0 && !packageName.contains("launcher") &&
                !packageName.contains("systemui") && !packageName.contains("miui") &&
                !packageName.contains("xiaomi") && !packageName.contains("android.settings")) {
                android.util.Log.d("BatteryCollector", "Unbekanntes Package: $packageName -> cat=0")
            }

            category
        } catch (e: Exception) {
            0 // idle als Fallback
        }
    }

    private fun classifyByPackageName(pkg: String): Int {
        return when {
            pkg.contains("game", ignoreCase = true) -> 3
            pkg.contains("video", ignoreCase = true) || pkg.contains("player", ignoreCase = true) -> 2
            pkg.contains("music", ignoreCase = true) || pkg.contains("audio", ignoreCase = true) -> 2
            pkg.contains("browser", ignoreCase = true) || pkg.contains("chrome", ignoreCase = true) -> 4
            pkg.contains("launcher", ignoreCase = true) || pkg.contains("systemui", ignoreCase = true) -> 0
            pkg.contains("miui", ignoreCase = true) || pkg.contains("xiaomi", ignoreCase = true) -> 0
            pkg.contains("android.settings", ignoreCase = true) -> 0
            pkg.contains("camera", ignoreCase = true) || pkg.contains("gallery", ignoreCase = true) -> 5
            pkg.contains("mail", ignoreCase = true) || pkg.contains("office", ignoreCase = true) -> 5
            pkg.contains("social", ignoreCase = true) || pkg.contains("chat", ignoreCase = true) -> 1
            else -> 0 // Unbekannt = idle/sonstig (nicht 5!)
        }
    }

    // ---- Feature 5: WiFi Connected ----
    private fun isWifiConnected(): Boolean {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = cm.activeNetwork ?: return false
        val caps = cm.getNetworkCapabilities(network) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }

    // ---- Feature 6: Mobile Data Active ----
    private fun isMobileDataActive(): Boolean {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = cm.activeNetwork ?: return false
        val caps = cm.getNetworkCapabilities(network) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)
    }

    // ---- Feature 7: Charging ----
    private fun isCharging(): Boolean {
        val bm = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return bm.isCharging
    }

    // ---- Feature 9: Battery Temperature (°C) ----
    private fun getBatteryTemperature(): Float {
        return try {
            val intent = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            val tempTenths = intent?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) ?: 0
            // Android gibt Temperatur in 1/10 °C zurück (z.B. 310 = 31.0°C)
            tempTenths / 10f
        } catch (e: Exception) {
            25f // Fallback Raumtemperatur
        }
    }

    // ---- Feature 10: Hotspot aktiv ----
    @Suppress("DEPRECATION")
    private fun isHotspotOn(): Boolean {
        return try {
            val wm = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val method = wm.javaClass.getDeclaredMethod("isWifiApEnabled")
            method.isAccessible = true
            method.invoke(wm) as Boolean
        } catch (e: Exception) {
            false
        }
    }

    // ---- Feature 8: CPU Usage (%) ----
    // /proc/stat ist seit Android 8 für Apps gesperrt.
    // Wir messen stattdessen die CPU-Frequenz über alle Kerne —
    // das korreliert direkt mit dem Stromverbrauch (P ∝ f·V², und V steigt mit f).

    private fun getCpuUsage(): Float {
        return try {
            getAvgCpuFrequencyPercent()
        } catch (e: Exception) {
            try {
                getLoadAvg()
            } catch (e2: Exception) {
                0f
            }
        }
    }

    /**
     * Primär: Durchschnittliche CPU-Frequenz über ALLE Kerne (% von max).
     * Liest /sys/devices/system/cpu/cpu{N}/cpufreq/ für jeden aktiven Kern.
     * Höherer Wert = CPU arbeitet härter = mehr Stromverbrauch.
     */
    private fun getAvgCpuFrequencyPercent(): Float {
        val numCores = Runtime.getRuntime().availableProcessors()
        var totalRatio = 0f
        var readCores = 0

        for (i in 0 until numCores) {
            try {
                val curFile = java.io.File("/sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq")
                val maxFile = java.io.File("/sys/devices/system/cpu/cpu$i/cpufreq/cpuinfo_max_freq")

                if (!curFile.canRead() || !maxFile.canRead()) continue

                val cur = curFile.readText().trim().toLong()
                val max = maxFile.readText().trim().toLong()
                if (max <= 0) continue

                totalRatio += cur.toFloat() / max
                readCores++
            } catch (_: Exception) { }
        }

        if (readCores == 0) throw Exception("No CPU freq readable")
        return (totalRatio / readCores * 100f).coerceIn(0f, 100f)
    }

    /**
     * Fallback: System Load Average aus /proc/loadavg (1-min).
     * Kann auf manchen Geräten auch gesperrt sein.
     */
    private fun getLoadAvg(): Float {
        val reader = BufferedReader(FileReader("/proc/loadavg"))
        val line = reader.readLine()
        reader.close()
        val load1min = line.split(" ")[0].toFloat()
        val cores = Runtime.getRuntime().availableProcessors().coerceAtLeast(1)
        return (load1min / cores * 100f).coerceIn(0f, 100f)
    }

    // ========== Notification ==========

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Battery Data Collector",
            NotificationManager.IMPORTANCE_LOW // kein Sound
        ).apply {
            description = "Sammelt Akkudaten alle 5 Minuten"
        }
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(channel)
    }

    private fun buildNotification(text: String = "Datensammlung aktiv..."): Notification {
        val openIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, openIntent, PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Battery Collector")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setOngoing(true)
            .setContentIntent(pendingIntent)
            .build()
    }
}

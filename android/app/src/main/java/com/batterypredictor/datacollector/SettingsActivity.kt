package com.batterypredictor.datacollector

import android.Manifest
import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.os.Process
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider

/**
 * Sammelt alle Infrastruktur-Bedienelemente (Service-Steuerung, Permissions,
 * CSV-Export, Modell-Infos) in einem Screen, damit die Haupt-UI sauber auf
 * dem einen USP-Feature (Vorhersage) bleibt.
 *
 * Erreichbar ueber das Zahnrad-Icon in der MainActivity-Toolbar.
 */
class SettingsActivity : AppCompatActivity() {

    private lateinit var statusText: TextView
    private lateinit var countText: TextView
    private lateinit var permissionText: TextView
    private lateinit var logger: BatteryDataLogger

    private val notificationPermLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) doStart() else Toast.makeText(
            this, "Notification-Permission benoetigt", Toast.LENGTH_SHORT
        ).show()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        logger = BatteryDataLogger.getInstance(this)

        statusText = findViewById(R.id.settingsStatusText)
        countText = findViewById(R.id.settingsCountText)
        permissionText = findViewById(R.id.settingsPermissionText)

        findViewById<Button>(R.id.btnSettingsBack).setOnClickListener { finish() }

        findViewById<Button>(R.id.btnSettingsStart).setOnClickListener { startCollection() }
        findViewById<Button>(R.id.btnSettingsStop).setOnClickListener { stopCollection() }
        findViewById<Button>(R.id.btnSettingsRefresh).setOnClickListener {
            val refreshIntent = Intent(this, DataCollectorService::class.java).apply {
                action = "REFRESH"
            }
            ContextCompat.startForegroundService(this, refreshIntent)
            Toast.makeText(this, "Neue Messung ausgeloest", Toast.LENGTH_SHORT).show()
        }
        findViewById<Button>(R.id.btnSettingsUsageStats).setOnClickListener {
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }
        findViewById<Button>(R.id.btnSettingsBatteryOpt).setOnClickListener {
            requestBatteryOptimizationExemption()
        }
        findViewById<Button>(R.id.btnSettingsExport).setOnClickListener { exportData() }

        findViewById<Button>(R.id.btnSettingsShowOnboarding).setOnClickListener {
            val intent = Intent(this, OnboardingActivity::class.java).apply {
                putExtra(OnboardingActivity.EXTRA_MODE, OnboardingActivity.MODE_REVIEW)
            }
            startActivity(intent)
        }

        findViewById<Button>(R.id.btnSettingsTrainOwn).setOnClickListener {
            startActivity(Intent(this, TrainOwnModelActivity::class.java))
        }
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
    }

    private fun refreshStatus() {
        val enabled = getSharedPreferences("battery_collector", MODE_PRIVATE)
            .getBoolean("service_enabled", false)
        statusText.text = if (enabled)
            getString(R.string.settings_collection_running, formatRunningSince())
        else
            getString(R.string.settings_collection_stopped)

        countText.text = getString(R.string.settings_collection_count, logger.getCount())

        permissionText.text = if (hasUsageStatsPermission())
            getString(R.string.settings_permission_ok)
        else
            getString(R.string.settings_permission_missing)
    }

    private fun formatRunningSince(): String {
        val started = getSharedPreferences("battery_collector", MODE_PRIVATE)
            .getLong("service_started_at", 0L)
        if (started == 0L) return "kurzem"
        val durationMs = System.currentTimeMillis() - started
        val hours = (durationMs / 3_600_000L).toInt()
        val days = hours / 24
        return when {
            days >= 1 -> "$days Tagen"
            hours >= 1 -> "$hours Stunden"
            else -> "wenigen Minuten"
        }
    }

    private fun startCollection() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                return
            }
        }
        if (!hasUsageStatsPermission()) {
            Toast.makeText(this,
                "Bitte 'Nutzungsdatenzugriff' fuer diese App aktivieren",
                Toast.LENGTH_LONG
            ).show()
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
            return
        }
        doStart()
    }

    private fun doStart() {
        val prefs = getSharedPreferences("battery_collector", MODE_PRIVATE)
        if (!prefs.getBoolean("service_enabled", false)) {
            prefs.edit().putLong("service_started_at", System.currentTimeMillis()).apply()
        }
        val intent = Intent(this, DataCollectorService::class.java)
        ContextCompat.startForegroundService(this, intent)
        refreshStatus()
    }

    private fun stopCollection() {
        getSharedPreferences("battery_collector", MODE_PRIVATE)
            .edit()
            .putBoolean("service_enabled", false)
            .remove("service_started_at")
            .apply()
        stopService(Intent(this, DataCollectorService::class.java))
        refreshStatus()
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.unsafeCheckOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            Process.myUid(),
            packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun requestBatteryOptimizationExemption() {
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        if (!pm.isIgnoringBatteryOptimizations(packageName)) {
            val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                data = Uri.parse("package:$packageName")
            }
            startActivity(intent)
        } else {
            Toast.makeText(this, "Bereits deaktiviert", Toast.LENGTH_SHORT).show()
        }
    }

    private fun exportData() {
        val file = logger.getFile()
        if (!file.exists() || file.length() == 0L) {
            Toast.makeText(this, "Keine Daten zum Exportieren", Toast.LENGTH_SHORT).show()
            return
        }
        val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", file)
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/csv"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(shareIntent, "CSV exportieren"))
    }
}

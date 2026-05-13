package com.batterypredictor.datacollector

import android.Manifest
import android.app.AppOpsManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import java.util.Timer
import java.util.TimerTask

class MainActivity : AppCompatActivity() {

    private lateinit var statusText: TextView
    private lateinit var dataPreview: TextView
    private lateinit var countText: TextView
    private lateinit var predictionText: TextView
    private lateinit var predictionDetail: TextView
    private lateinit var predTinyML: TextView
    private lateinit var predGoogle: TextView
    private lateinit var predLinear: TextView
    private lateinit var logger: BatteryDataLogger

    private val uiTimer = Timer()

    // Empfängt Vorhersagen vom Service
    private val predictionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val prediction = intent.getFloatExtra("prediction", -1f)
            val bufferSize = intent.getIntExtra("buffer_size", 0)
            val batteryLevel = intent.getFloatExtra("battery_level", -1f)
            val systemEstimateMin = intent.getFloatExtra("system_estimate", -1f)
            val linearBaselineH = intent.getFloatExtra("linear_baseline", -1f)

            // ---- Hauptzeile (TinyML, prominent) ----
            if (prediction >= 0f) {
                predictionText.text = "Noch ${formatHoursShort(prediction)}"
                predictionDetail.text = "Akku: ${batteryLevel.toInt()}%"
            } else {
                predictionText.text = "Sammle Daten... ($bufferSize/10)"
                predictionDetail.text =
                    "Braucht 10 Messungen (${10 - bufferSize} übrig à 30s)"
            }

            // ---- Vergleichs-Block: alle drei Methoden ----
            predTinyML.text = formatPredictionHours(prediction)
            predGoogle.text = formatPredictionMinutes(systemEstimateMin, batteryLevel)
            predLinear.text = formatPredictionHours(linearBaselineH)
        }
    }

    /** Kompakte Anzeige fuer Stunden-Eingabe, z.B. "13h 57min" oder "—". */
    private fun formatHoursShort(h: Float): String {
        val hours = h.toInt()
        val mins = ((h - hours) * 60).toInt()
        return "${hours}h ${mins}min"
    }

    private fun formatPredictionHours(h: Float): String {
        if (h < 0f) return "—"
        return formatHoursShort(h)
    }

    /** Google-API liefert Minuten und ist beim Laden / 100% oft -1. */
    private fun formatPredictionMinutes(min: Float, batteryLevel: Float): String {
        if (min <= 0f) {
            return if (batteryLevel >= 99f) "n/v (lädt)" else "n/v"
        }
        val hours = (min / 60f).toInt()
        val mins = (min % 60f).toInt()
        return "${hours}h ${mins}min"
    }

    // Permission-Launcher für Notification (Android 13+)
    private val notificationPermLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) checkAndStart()
        else Toast.makeText(this, "Notification-Permission benötigt", Toast.LENGTH_SHORT).show()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.statusText)
        dataPreview = findViewById(R.id.dataPreview)
        countText = findViewById(R.id.countText)
        predictionText = findViewById(R.id.predictionText)
        predictionDetail = findViewById(R.id.predictionDetail)
        predTinyML = findViewById(R.id.predTinyML)
        predGoogle = findViewById(R.id.predGoogle)
        predLinear = findViewById(R.id.predLinear)
        logger = BatteryDataLogger.getInstance(this)

        // ---- Buttons ----

        findViewById<Button>(R.id.btnStart).setOnClickListener {
            checkAndStart()
        }

        findViewById<Button>(R.id.btnStop).setOnClickListener {
            // Explizit deaktivieren, damit onTaskRemoved nicht neu startet
            getSharedPreferences("battery_collector", MODE_PRIVATE)
                .edit().putBoolean("service_enabled", false).apply()
            stopService(Intent(this, DataCollectorService::class.java))
            statusText.text = "Status: Gestoppt"
        }

        findViewById<Button>(R.id.btnExport).setOnClickListener {
            exportData()
        }

        findViewById<Button>(R.id.btnUsageStats).setOnClickListener {
            // User zur Einstellungsseite für UsageStats leiten
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }

        findViewById<Button>(R.id.btnBatteryOptimize).setOnClickListener {
            requestBatteryOptimizationExemption()
        }

        findViewById<Button>(R.id.btnRefresh).setOnClickListener {
            val refreshIntent = Intent(this, DataCollectorService::class.java).apply {
                action = "REFRESH"
            }
            ContextCompat.startForegroundService(this, refreshIntent)
        }

        // UI alle 10s aktualisieren
        uiTimer.scheduleAtFixedRate(object : TimerTask() {
            override fun run() {
                runOnUiThread { updateUI() }
            }
        }, 0, 10_000)
    }

    override fun onDestroy() {
        uiTimer.cancel()
        super.onDestroy()
    }

    override fun onResume() {
        super.onResume()
        val filter = IntentFilter("com.batterypredictor.PREDICTION_UPDATE")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(predictionReceiver, filter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(predictionReceiver, filter)
        }

        // Status korrekt anzeigen beim Öffnen
        val serviceEnabled = getSharedPreferences("battery_collector", MODE_PRIVATE)
            .getBoolean("service_enabled", false)
        statusText.text = if (serviceEnabled) "Status: Läuft ✓" else "Status: Gestoppt"
    }

    override fun onPause() {
        try { unregisterReceiver(predictionReceiver) } catch (_: Exception) {}
        super.onPause()
    }

    private fun checkAndStart() {
        // 1) Notification Permission (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                return
            }
        }

        // 2) UsageStats prüfen
        if (!hasUsageStatsPermission()) {
            Toast.makeText(this,
                "Bitte 'Nutzungsdatenzugriff' für diese App aktivieren",
                Toast.LENGTH_LONG
            ).show()
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
            return
        }

        // 3) Service starten
        val serviceIntent = Intent(this, DataCollectorService::class.java)
        ContextCompat.startForegroundService(this, serviceIntent)
        statusText.text = "Status: Läuft ✓"
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.unsafeCheckOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
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
            Toast.makeText(this, "Batterie-Optimierung bereits deaktiviert ✓", Toast.LENGTH_SHORT).show()
        }
    }

    private fun exportData() {
        val file = logger.getFile()
        if (!file.exists() || file.length() == 0L) {
            Toast.makeText(this, "Keine Daten zum Exportieren", Toast.LENGTH_SHORT).show()
            return
        }

        // Per Share-Intent teilen (Mail, Drive, Bluetooth, etc.)
        val uri = FileProvider.getUriForFile(
            this,
            "$packageName.fileprovider",
            file
        )
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/csv"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(shareIntent, "CSV exportieren"))
    }

    private fun updateUI() {
        countText.text = "Gesammelte Datenpunkte: ${logger.getCount()}"
        dataPreview.text = logger.getLastEntries(5)
    }
}

package com.batterypredictor.datacollector

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.ImageButton
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView

/**
 * Haupt-Activity: nur noch zwei-Tab-Container mit den Fragmenten
 * [LiveFragment] und [AccuracyFragment].
 *
 * Alle Infrastruktur-Buttons (Service-Start, Permissions, Export) leben
 * in der [SettingsActivity] hinter dem Zahnrad-Icon. So bleibt die
 * Hauptbuehne der App auf dem einen USP-Feature (Live-Vorhersage)
 * fokussiert.
 */
class MainActivity : AppCompatActivity() {

    private val notificationPermLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* Ergebnis interessiert uns hier nicht direkt, Service wird beim
         naechsten Start in den Settings ggf. erneut versucht. */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Beim ersten Start: Onboarding statt MainActivity zeigen.
        if (!OnboardingActivity.isSeen(this)) {
            startActivity(Intent(this, OnboardingActivity::class.java))
            finish()
            return
        }

        setContentView(R.layout.activity_main)

        // Notification-Permission (Android 13+) frueh erfragen, damit der
        // Service spaeter ohne Hakelei laufen kann.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }

        // Settings-Icon in der Top-Bar
        findViewById<ImageButton>(R.id.mainSettingsButton).setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }

        val bottomNav = findViewById<BottomNavigationView>(R.id.mainBottomNav)
        bottomNav.setOnItemSelectedListener { item ->
            val fragment: Fragment = when (item.itemId) {
                R.id.tab_live -> LiveFragment()
                R.id.tab_algorithm -> AlgorithmFragment()
                R.id.tab_accuracy -> AccuracyFragment()
                else -> return@setOnItemSelectedListener false
            }
            supportFragmentManager.beginTransaction()
                .replace(R.id.mainFragmentContainer, fragment)
                .commit()
            true
        }

        if (savedInstanceState == null) {
            bottomNav.selectedItemId = R.id.tab_live
        }

        // Falls der Service noch nie gestartet wurde, einmalig anwerfen.
        // Den Soft-Start verlassen wir, falls UsageStats fehlt -- der Nutzer
        // wird im Settings-Screen ohnehin erinnert.
        val prefs = getSharedPreferences("battery_collector", MODE_PRIVATE)
        if (!prefs.contains("service_started_at")) {
            tryStartService(prefs)
        }
    }

    private fun tryStartService(prefs: android.content.SharedPreferences) {
        // Hard requirement Android 13+: ohne POST_NOTIFICATIONS kann der
        // Foreground-Service kein Notification anzeigen -> wir warten lieber,
        // bis der Nutzer es im Settings-Tab anstoesst.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED) {
            return
        }
        try {
            prefs.edit()
                .putLong("service_started_at", System.currentTimeMillis())
                .apply()
            val intent = Intent(this, DataCollectorService::class.java)
            ContextCompat.startForegroundService(this, intent)
        } catch (_: Exception) { }
    }
}

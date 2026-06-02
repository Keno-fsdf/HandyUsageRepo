package com.batterypredictor.datacollector

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity

/**
 * Anleitungs-Activity: erklaert in fuenf Schritten, wie ein Nutzer
 * (oder der Pruefer) sein eigenes TinyML-Modell aus den selbst
 * gesammelten Daten trainiert und in die App deployt. Aufrufbar
 * ueber den Button "Modell selbst trainieren" im Settings-Screen.
 */
class TrainOwnModelActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_train_own_model)

        findViewById<Button>(R.id.btnTrainBack).setOnClickListener { finish() }

        findViewById<Button>(R.id.btnTrainGithub).setOnClickListener {
            val url = getString(R.string.train_github_url)
            try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            } catch (_: Exception) { /* kein Browser installiert */ }
        }
    }
}

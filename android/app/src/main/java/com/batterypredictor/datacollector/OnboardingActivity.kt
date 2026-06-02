package com.batterypredictor.datacollector

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.viewpager2.widget.ViewPager2

/**
 * Drei-Slide-Onboarding, das beim ersten App-Start gezeigt wird.
 *
 * Slide 1: Wir sammeln 10 Sensor-Werte alle 30 Sekunden.
 * Slide 2: Ein winziges Modell lernt am PC dein Verhalten.
 * Slide 3: Du siehst deine Restlaufzeit live - mit dem Modell-Groesse-Vergleich
 *          als Wow-Element ("14,4 KB").
 *
 * Nach dem Onboarding wird ein Flag in SharedPreferences gesetzt, damit es
 * beim naechsten Start uebersprungen wird.
 */
class OnboardingActivity : AppCompatActivity() {

    companion object {
        const val PREFS = "battery_collector"
        const val KEY_SEEN = "onboarding_seen"
        const val EXTRA_MODE = "mode"
        const val MODE_REVIEW = "review"

        private const val SLIDE_COUNT = 4
        private const val LAST_INDEX = SLIDE_COUNT - 1

        /** Hat der Nutzer das Onboarding schon gesehen? */
        fun isSeen(context: android.content.Context): Boolean {
            return context.getSharedPreferences(PREFS, MODE_PRIVATE)
                .getBoolean(KEY_SEEN, false)
        }
    }

    private lateinit var pager: ViewPager2
    private lateinit var btnNext: Button
    private lateinit var btnSkip: TextView
    private lateinit var dots: List<View>

    private val isReviewMode: Boolean
        get() = intent.getStringExtra(EXTRA_MODE) == MODE_REVIEW

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_onboarding)

        pager = findViewById(R.id.onboardingPager)
        btnNext = findViewById(R.id.btnOnbNext)
        btnSkip = findViewById(R.id.btnOnbSkip)
        dots = listOf(
            findViewById(R.id.onbDot0),
            findViewById(R.id.onbDot1),
            findViewById(R.id.onbDot2),
            findViewById(R.id.onbDot3),
        )

        pager.adapter = OnboardingPagerAdapter()
        pager.registerOnPageChangeCallback(object : ViewPager2.OnPageChangeCallback() {
            override fun onPageSelected(position: Int) {
                updateForPage(position)
            }
        })
        updateForPage(0)

        btnNext.setOnClickListener {
            if (pager.currentItem < LAST_INDEX) {
                pager.currentItem = pager.currentItem + 1
            } else {
                finishOnboarding()
            }
        }

        btnSkip.setOnClickListener { finishOnboarding() }
    }

    private fun updateForPage(position: Int) {
        dots.forEachIndexed { i, v ->
            v.alpha = if (i == position) 1.0f else 0.3f
        }
        btnNext.text = if (position == LAST_INDEX)
            getString(R.string.onb_start)
        else
            getString(R.string.onb_next)
        btnSkip.visibility = if (position == LAST_INDEX) View.INVISIBLE else View.VISIBLE
    }

    private fun finishOnboarding() {
        getSharedPreferences(PREFS, MODE_PRIVATE).edit()
            .putBoolean(KEY_SEEN, true)
            .apply()
        if (isReviewMode) {
            // Vom Settings-Screen aus aufgerufen -> einfach zurueck
            finish()
        } else {
            startActivity(Intent(this, MainActivity::class.java))
            finish()
        }
    }
}

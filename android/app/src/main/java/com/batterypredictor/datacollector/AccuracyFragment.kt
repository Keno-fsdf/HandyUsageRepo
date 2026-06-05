package com.batterypredictor.datacollector

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import java.util.concurrent.Executors

/**
 * Genauigkeits-Tab: zeigt einen Wer-war-genauer-Score zwischen
 *   - Eigenem TinyML-Modell
 *   - Google Battery-Discharge-Prediction API
 *   - Linear-Baseline (charge_counter / current_avg)
 *
 * Wird beim Tab-Wechsel und periodisch (alle 60s) neu berechnet.
 */
class AccuracyFragment : Fragment() {

    private lateinit var emptyText: TextView
    private lateinit var resultsContainer: View
    private lateinit var subtitleText: TextView

    private lateinit var rowOwn: ScoreRow
    private lateinit var rowGoogle: ScoreRow
    private lateinit var rowLinear: ScoreRow

    private val ioExecutor = Executors.newSingleThreadExecutor()
    private val uiHandler = Handler(Looper.getMainLooper())

    private val refreshRunnable = object : Runnable {
        override fun run() {
            recomputeAsync()
            uiHandler.postDelayed(this, 60_000L)
        }
    }

    private class ScoreRow(
        val container: LinearLayout,
        val rank: TextView,
        val label: TextView,
        val value: TextView,
    )

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        val root = inflater.inflate(R.layout.fragment_accuracy, container, false)

        emptyText = root.findViewById(R.id.accEmptyText)
        resultsContainer = root.findViewById(R.id.accResultsContainer)
        subtitleText = root.findViewById(R.id.accSubtitle)

        rowOwn = ScoreRow(
            root.findViewById(R.id.accRowOwn),
            root.findViewById(R.id.accRankOwn),
            root.findViewById(R.id.accLabelOwn),
            root.findViewById(R.id.accValueOwn),
        )
        rowGoogle = ScoreRow(
            root.findViewById(R.id.accRowGoogle),
            root.findViewById(R.id.accRankGoogle),
            root.findViewById(R.id.accLabelGoogle),
            root.findViewById(R.id.accValueGoogle),
        )
        rowLinear = ScoreRow(
            root.findViewById(R.id.accRowLinear),
            root.findViewById(R.id.accRankLinear),
            root.findViewById(R.id.accLabelLinear),
            root.findViewById(R.id.accValueLinear),
        )

        rowOwn.label.text = getString(R.string.acc_our_model)
        rowGoogle.label.text = getString(R.string.acc_google)
        rowLinear.label.text = getString(R.string.acc_linear)

        return root
    }

    override fun onResume() {
        super.onResume()
        uiHandler.post(refreshRunnable)
    }

    override fun onPause() {
        uiHandler.removeCallbacks(refreshRunnable)
        super.onPause()
    }

    private fun recomputeAsync() {
        val ctx = context ?: return
        val csvFile = BatteryDataLogger.getInstance(ctx).getFile()
        ioExecutor.execute {
            val score = try {
                AccuracyComputer.computeRecent(csvFile)
            } catch (e: Exception) {
                null
            }
            uiHandler.post { applyScore(score) }
        }
    }

    private fun applyScore(score: AccuracyComputer.Score?) {
        val ctx = context ?: return
        if (score == null) {
            emptyText.visibility = View.VISIBLE
            resultsContainer.visibility = View.GONE
            return
        }
        emptyText.visibility = View.GONE
        resultsContainer.visibility = View.VISIBLE

        val basis = BatteryDataLogger.getInstance(ctx).isBasisDataLoaded
        subtitleText.text = if (basis) {
            getString(R.string.acc_basis_caption)
        } else {
            val duration = formatDuration(score.dischargeMin)
            val base = "Basis: ${score.nPoints} Vorhersage-Punkte über einen $duration-Discharge"
            if (score.dischargeMin >= 60f * 6f) {
                "$base. Vorhersage über so lange Zeiträume ist anspruchsvoll."
            } else {
                "$base."
            }
        }

        applyRow(rowOwn, score.maeOwnMin, score.winner == "own", ctx)
        applyRow(rowGoogle, score.maeGoogleMin, score.winner == "google", ctx)
        applyRow(rowLinear, score.maeLinearMin, score.winner == "linear", ctx)

        // Ranking-Emojis nach MAE sortiert
        val sortedRows = listOf(
            Triple(rowOwn, score.maeOwnMin, "own"),
            Triple(rowGoogle, score.maeGoogleMin, "google"),
            Triple(rowLinear, score.maeLinearMin, "linear"),
        ).filter { !it.second.isNaN() }
            .sortedBy { it.second }

        val medals = listOf("🥇", "🥈", "🥉")
        sortedRows.forEachIndexed { i, (row, _, _) ->
            row.rank.text = medals.getOrElse(i) { "•" }
        }
        // Rows ohne Daten kriegen leeres Rank-Feld
        listOf(rowOwn, rowGoogle, rowLinear).forEach {
            if (sortedRows.none { triple -> triple.first === it }) {
                it.rank.text = "—"
            }
        }
    }

    private fun applyRow(
        row: ScoreRow, maeMin: Float, isWinner: Boolean, ctx: android.content.Context
    ) {
        row.container.background = ContextCompat.getDrawable(
            ctx,
            if (isWinner) R.drawable.bg_winner else R.drawable.bg_runner
        )
        row.value.text = if (maeMin.isNaN()) "n/v" else formatMaeMin(maeMin)
    }

    private fun formatMaeMin(min: Float): String {
        return when {
            min < 60f -> "${min.toInt()} Min daneben"
            else -> {
                val h = (min / 60f).toInt()
                val m = (min - h * 60f).toInt()
                "${h}h ${m}min daneben"
            }
        }
    }

    private fun formatDuration(min: Float): String {
        val h = (min / 60f).toInt()
        val m = (min - h * 60f).toInt()
        return if (h > 0) "${h}h ${m}min" else "${m}min"
    }
}

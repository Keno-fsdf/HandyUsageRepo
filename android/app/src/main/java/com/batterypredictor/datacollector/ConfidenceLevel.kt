package com.batterypredictor.datacollector

/**
 * Vertrauen in eine aktuelle Vorhersage. Aktuell rein heuristisch
 * abgeleitet (siehe [BufferConfidence]). Spaeter koennen wir das z.B. durch
 * Modell-Quantile oder einen Validation-MAE pro Akkustand-Bereich verfeinern.
 */
enum class ConfidenceLevel {
    HIGH, MEDIUM, LOW;

    companion object {
        /**
         * Erste Heuristik:
         *   - bufferSize < 10  -> noch im "warm-up", LOW
         *   - bufferSize 10..29 -> erst paar Minuten gesammelt, MEDIUM
         *   - bufferSize >= 30 -> stabile Historie, HIGH
         *
         * Zusatz: bei sehr niedrigem Akku (<10%) ist die Restlaufzeit
         * volatil -> downgrade.
         */
        fun fromBufferAndBattery(bufferSize: Int, batteryLevel: Float): ConfidenceLevel {
            val base = when {
                bufferSize < 10 -> LOW
                bufferSize < 30 -> MEDIUM
                else -> HIGH
            }
            return if (batteryLevel in 0f..9.9f) {
                // ein Stufe runter, mindestens LOW
                when (base) {
                    HIGH -> MEDIUM
                    MEDIUM -> LOW
                    LOW -> LOW
                }
            } else base
        }
    }
}

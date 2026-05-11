package com.batterypredictor.datacollector

import android.content.Context
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel

/**
 * TFLite-Inference für Batterie-Restlaufzeit.
 *
 * Modell: Conv1D, Input (1,10,10), Output (1,1) = Stunden verbleibend.
 * Features müssen mit dem gleichen StandardScaler normalisiert werden
 * wie beim Training.
 */
class BatteryPredictor(context: Context) {

    companion object {
        private const val MODEL_FILE = "battery_model.tflite"
        const val SEQUENCE_LENGTH = 10
        const val NUM_FEATURES = 10

        // StandardScaler-Parameter aus dem Training.
        // WICHTIG: Nach jedem Re-Training neu generieren mit
        //     python -m methods.tinyml.export_scaler_for_android
        // Die Reihenfolge muss exakt der Feature-Liste in configs/default.yaml entsprechen:
        //   battery_level, screen_on, brightness, active_app_category,
        //   wifi_on, mobile_data_on, charging, cpu_usage, temperature, hotspot_on
        // Aktuelle Werte aus multi-device Training (4 Geräte, models/scaler.joblib).
        // Regenerieren via: python -m methods.tinyml.export_scaler_for_android
        private val SCALER_MEAN = floatArrayOf(
            68.785519f, 0.826048f, 8.473016f, 1.311179f, 0.080822f,
            0.918920f, 0.000000f, 46.353606f, 33.004194f, 0.071038f
        )
        private val SCALER_SCALE = floatArrayOf(
            29.605581f, 0.379068f, 13.013102f, 1.169956f, 0.272561f,
            0.272959f, 1.000000f, 16.927498f, 4.214697f, 0.256888f
        )
    }

    private val interpreter: Interpreter
    private val recentData = ArrayDeque<FloatArray>(SEQUENCE_LENGTH)
    private var lastPrediction: Float = -1f

    init {
        val model = loadModelFile(context)
        val options = Interpreter.Options().apply {
            setNumThreads(2)
        }
        interpreter = Interpreter(model, options)
    }

    private fun loadModelFile(context: Context): MappedByteBuffer {
        val fd = context.assets.openFd(MODEL_FILE)
        val inputStream = FileInputStream(fd.fileDescriptor)
        val channel = inputStream.channel
        return channel.map(FileChannel.MapMode.READ_ONLY, fd.startOffset, fd.declaredLength)
    }

    /**
     * Neuen Datenpunkt hinzufügen und Vorhersage machen (falls genug Daten).
     * @param features Feature-Array in der Reihenfolge aus configs/default.yaml.
     * @return Restlaufzeit in Stunden, oder -1f wenn noch nicht genug Daten (braucht 10 Punkte)
     */
    fun addDataAndPredict(features: FloatArray): Float {
        require(features.size == NUM_FEATURES) {
            "expected $NUM_FEATURES features, got ${features.size}"
        }

        // Normalisieren (StandardScaler: (x - mean) / scale)
        val normalized = FloatArray(NUM_FEATURES) { i ->
            if (SCALER_SCALE[i] != 0f) {
                (features[i] - SCALER_MEAN[i]) / SCALER_SCALE[i]
            } else {
                0f
            }
        }

        // Ring-Buffer: älteste raus wenn voll
        if (recentData.size >= SEQUENCE_LENGTH) {
            recentData.removeFirst()
        }
        recentData.addLast(normalized)

        // Braucht SEQUENCE_LENGTH (10) Datenpunkte für eine Vorhersage
        if (recentData.size < SEQUENCE_LENGTH) {
            return -1f
        }

        // Input-Tensor bauen: Shape (1, 10, 10), INT8 quantisiert
        // TFLite INT8 erwartet ByteBuffer
        val inputBuffer = ByteBuffer.allocateDirect(1 * SEQUENCE_LENGTH * NUM_FEATURES * 4)
        inputBuffer.order(ByteOrder.nativeOrder())

        for (step in recentData) {
            for (value in step) {
                inputBuffer.putFloat(value)
            }
        }

        // Output: Shape (1, 1)
        val outputBuffer = ByteBuffer.allocateDirect(1 * 4)
        outputBuffer.order(ByteOrder.nativeOrder())

        // Inference
        inputBuffer.rewind()
        interpreter.run(inputBuffer, outputBuffer)

        outputBuffer.rewind()
        val prediction = outputBuffer.float

        // Ergebnis: Stunden verbleibend (mindestens 0)
        lastPrediction = prediction.coerceAtLeast(0f)
        return lastPrediction
    }

    fun getLastPrediction(): Float = lastPrediction

    fun hasEnoughData(): Boolean = recentData.size >= SEQUENCE_LENGTH

    fun getBufferSize(): Int = recentData.size

    fun close() {
        interpreter.close()
    }
}

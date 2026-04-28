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

        // StandardScaler Parameter aus dem Training (scaler_real.joblib)
        // Reihenfolge: battery_level, screen_on, brightness, active_app_category,
        //              wifi_on, mobile_data_on, charging, cpu_usage, temperature, hotspot_on
        private val SCALER_MEAN = floatArrayOf(
            84.694f, 0.810f, 9.339f, 1.779f, 0.0f,
            1.0f, 0.0f, 53.982f, 31.925f, 0.0f
        )
        private val SCALER_SCALE = floatArrayOf(
            17.481f, 0.392f, 11.558f, 1.254f, 1.0f,
            1.0f, 1.0f, 13.401f, 4.773f, 1.0f
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
     * @return Restlaufzeit in Stunden, oder -1f wenn noch nicht genug Daten (braucht 10 Punkte)
     */
    fun addDataAndPredict(data: BatteryDataPoint): Float {
        val features = floatArrayOf(
            data.batteryLevel,
            data.screenOn.toFloat(),
            data.brightness,
            data.activeAppCategory.toFloat(),
            data.wifiOn.toFloat(),
            data.mobileDataOn.toFloat(),
            data.charging.toFloat(),
            data.cpuUsage,
            data.temperature,
            data.hotspotOn.toFloat()
        )

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

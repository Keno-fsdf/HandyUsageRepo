package com.batterypredictor.datacollector

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import com.google.android.material.bottomsheet.BottomSheetDialogFragment

/**
 * Bottom-Sheet, das ausfuehrliche Hintergrund-Erklaerungen zum
 * TinyML-Modell zeigt (TinyML allgemein, Conv1D-Architektur,
 * Training, INT8-Quantisierung, die 10 Sensoren im Detail).
 *
 * Wird durch Tap auf die Modell-Architektur-Karte im
 * Algorithmus-Tab geoeffnet.
 */
class ModelDeepDiveSheet : BottomSheetDialogFragment() {

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        return inflater.inflate(R.layout.sheet_model_deepdive, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        view.findViewById<Button>(R.id.deepdiveClose).setOnClickListener { dismiss() }
    }

    companion object {
        const val TAG = "ModelDeepDiveSheet"
    }
}

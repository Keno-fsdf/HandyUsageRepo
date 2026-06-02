package com.batterypredictor.datacollector

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView

/**
 * Drei einfache Slide-Layouts: slide1 / slide2 / slide3.
 * Jeder Slide hat ein eigenes Layout, keine dynamische Befuellung noetig.
 */
class OnboardingPagerAdapter : RecyclerView.Adapter<OnboardingPagerAdapter.SlideHolder>() {

    private val layouts = intArrayOf(
        R.layout.item_onboarding_slide0,
        R.layout.item_onboarding_slide1,
        R.layout.item_onboarding_slide2,
        R.layout.item_onboarding_slide3,
    )

    class SlideHolder(view: View) : RecyclerView.ViewHolder(view)

    override fun getItemViewType(position: Int): Int = layouts[position]

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SlideHolder {
        val v = LayoutInflater.from(parent.context).inflate(viewType, parent, false)
        return SlideHolder(v)
    }

    override fun onBindViewHolder(holder: SlideHolder, position: Int) {
        // Nichts dynamisch zu binden - Inhalte stehen direkt in den Layouts.
    }

    override fun getItemCount(): Int = layouts.size
}

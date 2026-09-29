package org.agentbench.demo

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val message = TextView(this).apply {
            text = "Agent Benchmark Android fixture"
            textSize = 20f
            gravity = Gravity.CENTER
        }
        setContentView(message)
    }
}

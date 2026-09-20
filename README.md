# ⚡ Physics-Informed Audit & TinyML Sensor Fault Isolation for Transformer Predictive Maintenance

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TinyML](https://img.shields.io/badge/TinyML-Edge--AI-brightgreen.svg)]()
[![Domain](https://img.shields.io/badge/Domain-Predictive%20Maintenance-red.svg)]()

> **Critical Discovery:** A physics-informed thermodynamic audit proving that $99\%+$ accuracy Predictive Maintenance (PdM) models trained on public transformer telemetry are overfitting on **sensor/ADC railing glitches** rather than actual thermal degradation. Includes a ultra-lightweight ($O(1)$) Stage-1 TinyML C++ filter for edge devices.

---

## 📌 Executive Summary

Many machine learning models targeting Transformer Oil Temperature Indicator (`OTI`) trip flags achieve near-perfect accuracy ($99\%+$). However, applying **First-Principles Thermodynamics** (IEC 60076-7 ODEs) and rigorous statistical checks on field telemetry reveals that the high-temperature trips ($\ge 236^\circ\text{C}$) are **sensor artifacts (ADC Upper Railing / Upscale Burnout)** rather than physical oil overheating.

### Key Findings:
1. **Strict Mathematical Separability:** The Trip Flag (`OTI_T`) is deterministically mapped to $(\text{OTI} \ge 236^\circ\text{C})$ across $100\%$ of data points ($19,376$ rows). ML models simply learn `if OTI >= 236` instead of thermal dynamics.
2. **Physically Impossible Bimodality Gap:** There is a **$166^\circ\text{C}$ void gap** ($70^\circ\text{C}$ to $236^\circ\text{C}$) containing **zero readings**, proving an electronic step-discontinuity rather than gradual thermal heating.
3. **Cooling Impossibility:** Dropping from $248^\circ\text{C}$ to $52^\circ\text{C}$ in $8\text{ minutes}$ requires **$232.7\text{ kW}$** of cooling power in a standard Natural Oil Natural Air (ONAN) transformer—a thermodynamic impossibility for passive cooling with a 2-3 hour thermal time constant.
4. **Pessimistic Heating Bound:** Even if $100\%$ of total electrical power ($98.7\text{ kW}$) dissipated instantly as heat into the $300\text{ kg}$ oil mass, maximum possible heating is $+20.8^\circ\text{C}/2\text{ min}$, whereas telemetry shows $+182^\circ\text{C}$.

---

## 🔬 Thermodynamic Proofs & Physics Bounds

### 1. The Cooling Impossibility Proof
For an estimated oil mass $m = 300\text{ kg}$ and specific heat capacity $c = 1900\text{ J/kg}\cdot^\circ\text{C}$:
$$\Delta T = -196^\circ\text{C} \quad \text{in } 8\text{ minutes } (480\text{ s})$$
$$Q_{\text{released}} = m \cdot c \cdot \Delta T = 300 \times 1900 \times 196 \approx 111.72\text{ MJ}$$
$$P_{\text{cooling}} = \frac{111.72\text{ MJ}}{480\text{ s}} \approx \mathbf{232.7\text{ kW}}$$

*An ONAN transformer dissipating $232.7\text{ kW}$ passively in 8 minutes violates fundamental heat transfer limits.*

### 2. Empirical Rate-of-Change Calibration ($\vert{}d\text{OTI}/dt\vert{}$)
Statistical distribution of temperature rate of change across $19,376$ telemetry samples:

| Operation State | Rate Metrics | Value |
| :--- | :--- | :--- |
| **Quiet Operation** ($\text{OTI} < 150^\circ\text{C}$) | Median | $0.067^\circ\text{C}/\text{min}$ |
| | 99th Percentile ($p99$) | $0.333^\circ\text{C}/\text{min}$ |
| | **99.9th Percentile ($p99.9$)** | **$2.000^\circ\text{C}/\text{min}$** |
| **Glitch / Artifact Events** ($\text{OTI} > 200^\circ\text{C}$) | Average Glitch Rate | $8.20^\circ\text{C}/\text{min}$ |
| | **Max Recorded Glitch Rate** | **$91.00^\circ\text{C}/\text{min}$** |

---

## 🛠️ TinyML Stage-1 Architecture (Edge Isolation)

Instead of running heavy ML models on corrupted input, we propose a two-stage edge architecture deployable on low-power microcontrollers (STM32, ESP32, Cortex-M0):

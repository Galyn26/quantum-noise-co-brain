# Project Co-Brain 🧠🌀

> **"I don't understand quantum mechanics yet. I'm just a DevOps mind using standard infrastructure to build a sandbox for the bleeding edge."**

Welcome to **Project Co-Brain**—an open-source, local-to-cloud infrastructure framework dedicated to solving one of the greatest bottlenecks in modern computing: **Quantum Noise Mitigation in Noisy 
Intermediate-Scale Quantum (NISQ) processors.**

This framework bridges systems engineering and quantum physics from the top down. By tracking real-time QPU chip drift via live telemetry streams, Co-Brain acts as a middleware orchestration 
layer—pre-compensating for environmental decoherence (such as bit-flip and pulse drift) before circuit execution on physical backends.

---

## 🕹️ Three Modes of Operation

### 1. 🎛️ Standalone Desktop Console (BetaV1.0.0)
Skip the command line entirely. The native desktop app bundles our full 3D WebGL Bloch Sphere visualizer and parameter orchestration panel into a high-performance, standalone frontend shell.
*   📥 **Get the App:** Head to the **[Latest GitHub Release](https://github.com/Galyn26/quantum-noise-co-brain/releases/latest)** and pull the package matching your node:
    *   🍏 **macOS:** `QuantumCoBrain-MacOS.zip` *(Extract and launch `QuantumCoBrain.app`)*
    *   🪟 **Windows (x64):** `QuantumCoBrain-Windows-x64.zip` *(Extract and launch `QuantumCoBrain.exe`)*
    *   🐧 **Linux (x64):** `QuantumCoBrain-Linux-x64.tar.gz` *(Extract and execute binary)*

### 2. 🌐 Production Cloud Dashboard
Track parameters securely from any device. The interactive visualization layer is fully scaled into a multi-tenant cloud workspace backed by an Auth0 Federated Gateway and a persistent, cross-platform 
relational database pipeline.
*   🛰️ **Live Web Application:** [https://quantum-noise-co-brain.onrender.com](https://quantum-noise-co-brain.onrender.com)
*   🔒 **Isolated State Planes:** State tracking automatically provisions private database records per operator upon login. Slider adjustments and telemetry toggles persist natively across active 
sessions.

### 3. 🧪 Local Terminal & Medical Data Sandbox
For engineers wanting to hack the underlying Python algorithms, run benchmarks, or experiment with raw datasets locally.

#### Quickstart: Running the Noise Baseline
Ensure you have Python 3.10+ initialized inside an isolated local virtual environment:
```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime scikit-learn
```

* **Run Quantum Error**: Watch 5% simulated bit-flip corrupt an entangled 2-qubit system in real time:
```bash
python3 noise_baseline.py
```

* **Execute Medical Mitigation Battle**: Watch the Co-Brain's active Pauli-Twirling middleware go head-to-head against unmitigated channels using real clinical records (Breast Cancer Wisconsin 
Dataset):
```bash
python3 phase2_cobrain_mitigator.py
```

* **Scrape Live Production QPU's**: Query live, utility-scale physical quantum hardware over the IBM Quantum Cloud to pull real-time error floats:
```bash
python3 ibm_telemetry_provider.py
```

# 🛠️ Project Roadmap & Core Benchmarks

We are actively pushing high-dimensional medical imaging and molecular analysis data arrays across the cloud port to map and pre-emptively bypass hardware instability:

* 🩻**Chest X-Ray Dataset** (Spatial data compression mapping) — Status: Successful

* 🧪**QM7 Dataset** (Molecular analysis & feature mapping) — Status: Successful

* 🧬**Breast Cancer Wisconsin Dataset** (Diagnostic accuracy mapping) — Status: Successful

# 🤝 The Open Invitation & Public Contribution

This project is intentionally open to public contribution—we need your math. If you are a Quantum Information Scientist, Physics Post-Doc, QML Engineer, or open-source enthusiast looking to build 
stable pre-execution compiler blocks, we want your code.

Review our dedicated CONTRIBUTING.md to explore architecture layouts, database routing rules, and local development sandbox configurations.

# Project Co-Brain (Working Title) 🧠🌀

> **"I don't understand quantum mechanics yet. I'm just a DevOps mind using standard infrastructure to build a sandbox for the bleeding edge."**

Welcome to **Project Co-Brain**. This is an open-source, local-to-cloud infrastructure sandbox dedicated to solving one of the greatest bottlenecks in modern computing: **Quantum Noise Mitigation in Noisy Intermediate-Scale Quantum (NISQ) processors.**

The goal of this project is to build an intelligent, predictive classical "co-brain" framework that sits inside a local containerized stack, scrapes live hardware telemetry from cloud quantum processing units (QPUs), and dynamically maps/orchestrates circuit routing to pre-emptively bypass hardware instability—specifically applied to high-dimensional medical imaging and molecular analysis.

---

## 🚀 The Core Philosophy: Systems Engineering vs. Physics
Hardware physicists are working from the bottom up to fix quantum noise with better hardware. This project approaches the problem from the top down: **using intelligent software orchestration to make unstable hardware predictable.**

Instead of intercepting data or altering quantum states midway (which triggers measurement collapse), Co-Brain aims to act as a dynamic, telemetry-driven compiler pre-compensating for chip drift before execution.

## 🛠️ Current Project Status & Architecture
The "garage sandbox" pipeline is officially operational. Current infrastructure features:
* **The Stack:** Lightweight, local environment orchestrated entirely via containerized microservices (**Docker**, running locally).
* **The Pipe:** Secure API routing pinging live **IBM Quantum QPU** backends.
* **The Proof of Concept:** Successfully processed a chest X-ray dataset, compressing pixel arrays into a single qubit configuration across the cloud port.

### 📊 Active Benchmarking Roadmap
We are currently pushing three core datasets through the pipeline to map how standard NISQ noise affects high-dimensional targets:
1. 🩻 **Chest X-Ray Dataset** (Spatial data/compression baseline) — *Status: Successful*
2. 🧪 **QM7 Dataset** (Molecular analysis & chemical-quantum feature mapping) — *Status: In Progress*
3. 🧬 **Breast Cancer Wisconsin Dataset** (Classification & diagnostic accuracy mapping) — *Status: Planned*

---

## 🤝 The Open Invitation (Call for Collaborators)

**I am a systems/CS undergraduate, not a quantum physicist.** I know how to build stable pipelines, configure automated environments, and scrape telemetry data. I do *not* know the deep linear algebra or quantum mechanics required to write a custom variational quantum autoencoder yet. 

This repository is intentionally, deeply open to public contribution. **We need your math.**

### 🔮 Who we are looking for:
* **Quantum Information Scientists / Physics Post-Docs:** To explain the nuances of T1/T2 relaxation, gate faults, and how to programmatically leverage spectator qubits.
* **QML Engineers:** To help design a predictive, spatial-mapping framework that can take raw IBM telemetry streams and turn them into intelligent routing paths.
* **Open Source Enthusiasts:** Anyone who thinks it’s cool to fight quantum decoherence using legacy local hardware and a "why not" attitude.

## 📈 How to Contribute
1. Look at the current open issues (or open one if you spot a flaw in my circuit mapping).
2. Check out the current Docker setup and script structures.
3. Drop an idea in the Discussions tab—no idea is too chaotic. Let's see what happens.

---
*Inspired by the absolute drive to make science fiction reality. Built in a home sandbox.*

## 🧪 Quickstart: Running the Noise Baseline

To understand exactly what bottleneck this project is solving without needing a physics degree, you can run a local baseline simulation on your machine to watch quantum decoherence happen in real time.

### 1. Prerequisites & Installation
Ensure you have Python 3.10+ and a virtual environment activated on your node:

```bash
# Create and activate environment
python3 -m venv env
source env/bin/activate

# Install the exact execution dependencies
pip install --upgrade pip
pip install qiskit qiskit-aer
```
### 2. Running the Co-Brain Feedback Simulator

To watch the Co-Brain actively scrape telemetry, monitor chip drift, and execute dynamic pre-execution circuit mitigation, run the live control loop skeleton:

```bash
python3 cobrain_orchestrator.py
```
## Run the Diagnostic

Execute the baseline script to generate an ideal versus a noisy quantum environment

```bash
python3 noise_baseline.py
```
## Interpreting the Telemetry Output

When the script finishes, it outputs two distinct bitstring distributions. Here is what they actually mean:

=== BASELINE TELEMETRY COMPILED ===
Ideal Expected Output (Should be ~50/50 split of 00 and 11):
   --> {'00': 519, '11': 481}

Noisy Output (Notice the random corruptions/shifts leaking in):
   --> {'11': 489, '00': 511}

* **The Ideal Run**: We initialized a 2-qubit system and applied a Hadamard and a CNOT gate to put them into an entangled state. In a perfect universe, measuring these qubits should ONLY ever result in 00 or 11 (a perfect binary correlation)
* **The Noisy Run**: We injected a simulated 5% Bit-Flip Drift Channel (mimicking real-world environmental noise on an IBM processor chip). Because the physical hardware is unstable, the qubits fluctuate, throwing errors into the final matrix.

# The QCNB Objective:

How do we write a predictive, data-driven "co-brain" framework that tracks these hardware shifts via live telemetry streams and dynamically routes or corrects the circuit instructions BEFORE execution, bypassing this corruption entirely?

## 🕹️ The Contributor's Playground (How to Hack the Code)

You don't need a math degree to start experimenting with this pipeline. The `cobrain_orchestrator.py` script is intentionally modular so you can drop in your own logic and watch how it affects the final matrix leakage live. 

Here are the three specific dials you can tweak right now to test out your ideas:

### 1. Upgrade the Quantum EQ (The Interception Strategy)
Right now, the Co-Brain uses a basic identity-equivalent sequence (two $X$ gates) to simulate dynamic interception inside the `inject_dynamical_decoupling` function. 

**Where to look:** 
```python
def inject_dynamical_decoupling(qc):
    # YOUR EXPERIMENT HERE: Tear this open and implement advanced 
    # dynamical decoupling sequences (e.g., XY4, CPMG, or custom phase-rotations)
    mitigated_qc.x(1)
    mitigated_qc.x(1)
    ...
```
* **The Challenge**: Can you write a sequence that lowers the `Matrix Leakage` percentage even further when the noise spike hits extreme levels (e.g., >10%)

### 2. Tweak the Decision Threshold (The Brain's sensitivity)

Inside the `run_telemetry_loop`, there is a hardcoded threshold parameter that determines exactly when the Co-Brain decides to intercept the deployment pipeline.

```python
threshold = 0.045  # 4.5% Gate Error Rate
```
* **The Experiment**: Try lowering this to 0.01 to make the compiler hyper-aggressive, or raise it to 0.08 to see how long the native hardware can survive high-noise states before the data completely corrupts.

### 3. Hook it to live Telemetry Hardware

Currently,`get_simulated_qpu_telemetry` utilizes a randomized sine-wave drift to model real-world environmental shifts.

* Where to look:

```python
def get_simulated_qpu_telemetry(timestamp):
    # Currently simulates drift algorithmically
    base_drift = 0.04 + 0.03 * random.uniform(-1, 1)
    ...
```
* **The Integration Project**: If you have an active IBM Quantum API token, rewrite this function to authenticate via `qiskit-ibm-runtime`, scrape the live backend calibration properties of a machine like `ibm_brisbane`, and pass real-world chip telemetry straight into the simulator loop!

## 📊 Running the Advanced Medical Data Sandbox

If you want to move past the simulated baseline and see how the Co-Brain handles real-world medical data, you can execute the Phase 1 and Phase 2 data pipelines. These scripts use the **Breast Cancer Wisconsin Dataset** to benchmark true classification stability.

### 1. Install Data Dependencies
Ensure you have `scikit-learn` installed in your virtual environment:
```bash
pip install scikit-learn
```

### 2. Execute Phase 1: Map the Corruption Baseline

Run the data mapper to compress the medical features down to 2 dimensions using PCA, encode them into qubits, and watch how classification accuracy naturally degrades as noise increases:
```python
python3 phase1_data_mapper.py
```

### 3. Execute Phase 2: Run the Co-Brain Mitigation Battle

Run the comparative benchmarking engine to see the native unmitigated path go head-to-head against the Co-Brain's active Pauli-Twirling middleware under a critical 12% drift:
```python
python3 phase2_cobrain_mitigator.py
```
* **What you're watching**: The Co-Brain dynamically intercepts the deep processing layers and applies randomized gate twirling, actively rescuing data points from fatal classification inversions in real time.

### 4. Execute Phase 3: Pull Live Production Hardware Telemetry
Query real, utility-scale physical quantum processors (like the Eagle-architecture `ibm_fez`) over the IBM Quantum Cloud to scrape live hardware calibration metrics:
```bash
python3 ibm_telemetry_provider.py
```

* **What you're watching**: The telemetry provider dynamically handshakes with your IBM open-tier account, filters out simulators, identifies the machine's native physical entangling gate (cz, ecr, or cx), and extracts the real-time physical error float from the active hardware target layout.
* **The closed loop connection**: In production, these real-time floats feed directly back into the Co-Brain's middleware orchestration layer to trigger the Phase 2 mitigation layers automatically when physical chip stability degrades.


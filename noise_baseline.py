import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise

print("⚡ Initializing Noisy Sandbox Environment on Linux Node... ⚡")

# 1. Create a basic 2-qubit circuit (mimicking a compressed data mapping)
circuit = QuantumCircuit(2, 2)
circuit.h(0)         # Put qubit 0 into superposition
circuit.cx(0, 1)     # Entangle qubit 0 and 1
circuit.measure([0, 1], [0, 1])

# 2. Construct a simulated 5% Bit-Flip Noise Channel (The problem to solve)
p_error = 0.05
bit_flip_error = noise.pauli_error([('X', p_error), ('I', 1 - p_error)])

# Create a custom noise model container
custom_noise_model = noise.NoiseModel()
# Apply this specific error to all single-qubit gates (like our H gate)
custom_noise_model.add_all_qubit_quantum_error(bit_flip_error, ['h'])

# 3. Spin up two distinct backends to compare outcomes
simulator_ideal = AerSimulator()
simulator_noisy = AerSimulator(noise_model=custom_noise_model)

# 4. Execute the trials
print("\n[1/2] Executing Ideal Simulation (No Noise)...")
job_ideal = simulator_ideal.run(transpile(circuit, simulator_ideal), shots=1000)
counts_ideal = job_ideal.result().get_counts()

print("[2/2] Executing Noisy Simulation (5% Bit-Flip Drift Loaded)...")
job_noisy = simulator_noisy.run(transpile(circuit, simulator_noisy), shots=1000)
counts_noisy = job_noisy.result().get_counts()

# 5. Output raw telemetry results to the console
print("\n=== BASELINE TELEMETRY COMPILED ===")
print(f"Ideal Expected Output (Should be ~50/50 split of 00 and 11):")
print(f"   --> {counts_ideal}")
print(f"\nNoisy Output (Notice the random '01' and '10' corruptions leaking in):")
print(f"   --> {counts_noisy}")
print("====================================")

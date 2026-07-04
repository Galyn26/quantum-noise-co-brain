import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

def load_and_compress_data():
    """Loads the Breast Cancer dataset and compresses it to 2 features using PCA."""
    data = load_breast_cancer()
    X, y = data.data, data.target
    
    # 1. Take a small 50-sample subset to keep the local simulation incredibly fast
    X_subset, _, y_subset, _ = train_test_split(X, y, train_size=50, random_state=42, stratify=y)
    
    # 2. Compress the 30 continuous features down to 2 principal components
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_subset)
    
    # 3. Normalize the values between 0 and pi so they map perfectly onto qubit rotation angles (0 to 180 degrees)
    scaler = MinMaxScaler(feature_range=(0, np.pi))
    X_angles = scaler.fit_transform(X_pca)
    
    return X_angles, y_subset

def encode_data_to_circuit(data_point):
    """
    Applies Angle Encoding and simulates a deep Variational Quantum Circuit workload.
    Deepening the circuit depth allows depolarizing noise to compound over time.
    """
    qc = QuantumCircuit(2)
    
    # --- 1. FEATURE MAP (Data Ingestion) ---
    qc.ry(data_point[0], 0)
    qc.ry(data_point[1], 1)
    
    # --- 2. DEEP PROCESSING LAYERS (The Workload Model) ---
    # We repeat entanglement and rotation steps to artificially compound the gate depth
    for _ in range(5):  # 5 processing layers deep
        qc.cx(0, 1)
        # Apply arbitrary parameter shifts (simulating variational weights)
        qc.rx(0.5, 0)
        qc.ry(0.2, 1)
        qc.cx(1, 0)
        
    qc.measure_all()
    return qc

def run_noise_experiment():
    print("="*60)
    print("🧬 PHASE 1: COMPILING QUANTUM DATA CORRUPTION BASELINE 🧬")
    print("="*60)
    
    X_angles, y_true = load_and_compress_data()
    simulator = AerSimulator()
    
    # 1. Establish the absolute Ideal Baseline first (0% noise)
    # We store the clean prediction for every single data point
    ideal_predictions = []
    for data_point in X_angles:
        qc = encode_data_to_circuit(data_point)
        compiled_qc = transpile(qc, simulator)
        clean_result = simulator.run(compiled_qc, shots=500).result()
        clean_counts = clean_result.get_counts()
        ideal_predictions.append(max(clean_counts, key=clean_counts.get))

    # 2. Test across distinct hardware drift conditions
    noise_scenarios = [0.02, 0.05, 0.12]
    print(f"Loaded {len(X_angles)} medical data points. Commencing simulation sweep...\n")
    
    for noise_rate in noise_scenarios:
        print(f"⚙️  Testing Environment Noise Level: {noise_rate * 100:.1f}%")
        
        # Build the dynamic multi-qubit noise model
        noise_model = NoiseModel()
        err_1 = depolarizing_error(noise_rate, 1)
        err_2 = depolarizing_error(noise_rate, 2)
        noise_model.add_all_qubit_quantum_error(err_1, ['ry'])
        noise_model.add_all_qubit_quantum_error(err_2, ['cx'])
            
        corrupted_runs = 0
        
        # Run every single data sample through this specific noise environment
        for i, data_point in enumerate(X_angles):
            qc = encode_data_to_circuit(data_point)
            compiled_qc = transpile(qc, simulator)
            
            result = simulator.run(compiled_qc, noise_model=noise_model, shots=500).result()
            counts = result.get_counts()
            
            # Find the dominant state under noisy conditions
            predicted_state = max(counts, key=counts.get)
            
            # COMPARE TO GROUND TRUTH: Did the noise cause it to deviate from the ideal run?
            if predicted_state != ideal_predictions[i]:
                corrupted_runs += 1
                
        corruption_rate = (corrupted_runs / len(X_angles)) * 100
        print(f"📊 Result: {corruption_rate:.1f}% of datasets suffered fatal classification inversion.")
        print("-" * 60)

if __name__ == "__main__":
    run_noise_experiment()

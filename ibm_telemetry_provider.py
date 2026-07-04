from qiskit_ibm_runtime import QiskitRuntimeService

def get_real_qpu_telemetry():
    # 1. Authenticate with your secure local token profile
    service = QiskitRuntimeService(channel="ibm_quantum_platform")
    
    # 2. Grab real, active physical hardware available to your open-instance
    available_backends = service.backends(simulator=False, operational=True)
    if not available_backends:
        raise RuntimeError("No operational physical QPUs detected on your IBM Account.")
        
    backend = available_backends[0]
    print(f"📡 Dynamically connected to active QPU node: [{backend.name}]")
    
    # 3. Modern Qiskit Target Scraping: Find the primary 2-qubit gate name
    # Checks if the chip uses 'cz' or 'ecr' instead of the legacy 'cx'
    native_gates = backend.target.operation_names
    two_qubit_gate = None
    for gate in ['cz', 'ecr', 'cx']:
        if gate in native_gates:
            two_qubit_gate = gate
            break
            
    if not two_qubit_gate:
        raise ValueError(f"Could not identify a supported 2-qubit entangling gate for {backend.name}")
        
    print(f"🛠️  Detected native hardware entangling gate: '{two_qubit_gate}'")
    
    # 4. Extract the exact instruction error from the backend's live target layout
    try:
        # Check connection error rate between physical Qubit 0 and Qubit 1
        instruction_props = backend.target[two_qubit_gate][(0, 1)]
        gate_error = instruction_props.error
    except KeyError:
        # If qubits 0 and 1 aren't directly coupled on this specific lattice, grab the first available pair
        available_pairs = list(backend.target[two_qubit_gate].keys())
        instruction_props = backend.target[two_qubit_gate][available_pairs[0]]
        gate_error = instruction_props.error
        
    return backend.name, two_qubit_gate, gate_error

if __name__ == "__main__":
    print("📡 Querying IBM Cloud for active Open-Plan QPU resources...")
    try:
        backend_name, gate_name, err = get_real_qpu_telemetry()
        print(f"📊 Live {backend_name} '{gate_name}' Channel Error Rate: {err * 100:.4f}%")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

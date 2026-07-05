import sys
import json

def write_jsonrpc(response):
    """Writes a clean, unbuffered JSON-RPC frame back to Cursor."""
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def log_error(msg):
    """Logs internal updates to standard error so they show in Cursor's debug console."""
    sys.stderr.write(f"📡 [QUANTUM MCP LOG]: {msg}\n")
    sys.stderr.flush()

def main():
    log_error("Server initialized, awaiting Cursor handshake...")

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line.strip())
            req_id = request.get("id")
            method = request.get("method")

            # 1. Handle the mandatory initialization handshake
            if method == "initialize":
                initialize_response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {
                            "name": "quantum-co-brain",
                            "version": "1.0.0"
                        }
                    }
                }
                write_jsonrpc(initialize_response)
                log_error("Handshake completed successfully!")

            # 2. Cursor asks for the tool list right after initialization
            elif method == "tools/list":
                tools_response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "dial_quantum_knobs",
                                "description": "Actively tune noise amplitude and gate drift vectors inside the running Co-Brain matrix.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "noise_amplitude": {
                                            "type": "number", 
                                            "minimum": 0.0, 
                                            "maximum": 0.5,
                                            "description": "The environmental decoherence scaling factor."
                                        },
                                        "gate_drift": {
                                            "type": "number", 
                                            "minimum": 0.0, 
                                            "maximum": 15.0,
                                            "description": "Simulated physical gate degradation shift rate percentage."
                                        }
                                    },
                                    "required": ["noise_amplitude", "gate_drift"]
                                }
                            }
                        ]
                    }
                }
                write_jsonrpc(tools_response)
                log_error("Broadcasted tool manifest safely to client.")

            # 3. Handle the actual execution command when you ask Cursor to dial the knobs
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name == "dial_quantum_knobs":
                    # Import urllib to hit your local running FastAPI app instantly
                    import urllib.request
                    
                    req = urllib.request.Request(
                        "http://127.0.0.1:8000/api/tune",
                        data=json.dumps(arguments).encode(),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    with urllib.request.urlopen(req) as response:
                        res_data = json.loads(response.read().decode())

                    call_response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Successfully shifted operational vectors. State profile: {res_data}"
                                }
                            ]
                        }
                    }
                    write_jsonrpc(call_response)
                    log_error(f"Executed loop intercept parameters: {arguments}")

        except Exception as e:
            log_error(f"Error handling frame: {str(e)}")

if __name__ == "__main__":
    main()

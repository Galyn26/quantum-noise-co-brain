import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Direct native import from your Phase 3 backend!
try:
    from ibm_telemetry_provider import get_real_qpu_telemetry
    _, _, real_err = get_real_qpu_telemetry()
    initial_drift = round(real_err * 100, 4)
except Exception:
    initial_drift = 1.1792  # Fallback to your historic victory float if offline

app = FastAPI(title="Quantum Noise Co-Brain Operator Console")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Central operational state plane
cockpit_state = {
    "pauli_twirling": True,
    "noise_amplitude": 0.12,
    "gate_drift": initial_drift,
    "target_backend": "ibm_fez"
}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request}) 

@app.get("/api/state")
async def get_state():
    return JSONResponse(content=cockpit_state)

@app.post("/api/tune")
async def tune_knobs(payload: Request):
    global cockpit_state
    data = await payload.json()
    for key in data:
        if key in cockpit_state:
            cockpit_state[key] = data[key]
    print(f"🎛️  [MCP CORE SIGNAL] Active Parameter Shift: {data}")
    return JSONResponse(content={"status": "success", "updated_state": cockpit_state})

@app.get("/api/download-dataset")
async def download_dataset():
    # Point directly to your companion cockpit's historical ledger data safely
    snapshot_path = os.path.join(BASE_DIR, "../../quantum-cockpit/data/production_hardware_snapshots.json")
    if os.path.exists(snapshot_path):
        with open(snapshot_path, "r") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"error": "Snapshot file not found in cockpit database folder."}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Firing up Live Co-Brain Control Node on local port 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)

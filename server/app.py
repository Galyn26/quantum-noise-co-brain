import sys
import os
import json
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, text

app = FastAPI(title="Quantum Noise Co-Brain Operator Console")

# 🔐 Session & OAuth Infrastructure
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "local_secret_key_1337"))

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"https://{os.environ.get('AUTH0_DOMAIN')}/.well-known/openid-configuration"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 📂 MOUNT STATIC ASSETS ROUTING
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Direct native import from your Phase 3 backend!
try:
    from ibm_telemetry_provider import get_real_qpu_telemetry
    _, _, real_err = get_real_qpu_telemetry()
    DEFAULT_DRIFT = round(real_err * 100, 4)
except Exception:
    DEFAULT_DRIFT = 1.1792  # Fallback float if offline


# --- 🗄️ DYNAMIC CROSS-COMPATIBLE DATABASE ENGINE ---
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Adjust Render connection prefix to match strict SQLAlchemy requirements
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print("🐘 CONNECTED: Live Cloud PostgreSQL Cluster Active.")
else:
    # Flawless backward compatibility fallback to your local SQLite file
    DB_PATH = os.path.join(BASE_DIR, "quantum_operators.db")
    engine = create_engine(f"sqlite:///{DB_PATH}")
    print("💾 CONNECTED: Local Desktop SQLite Fallback Active.")


def init_db():
    """Initializes the relational database table layouts cross-dialect."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_states (
                user_id TEXT PRIMARY KEY,
                pauli_twirling BOOLEAN,
                noise_amplitude REAL,
                gate_drift REAL,
                target_backend TEXT
            )
        """))

# Run database initialization on server boot sequence
init_db()


def get_or_create_user_state(user_id: str) -> dict:
    """Queries user rows via cross-dialect execution parameters."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT user_id, pauli_twirling, noise_amplitude, gate_drift, target_backend FROM user_states WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if result:
            state = dict(result._mapping)
            state["pauli_twirling"] = bool(state["pauli_twirling"])
            return state

    # Seed fresh accounts natively
    defaults = {
        "user_id": user_id,
        "pauli_twirling": True,
        "noise_amplitude": 0.12,
        "gate_drift": DEFAULT_DRIFT,
        "target_backend": "ibm_fez"
    }
    
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO user_states (user_id, pauli_twirling, noise_amplitude, gate_drift, target_backend)
            VALUES (:user_id, :pauli_twirling, :noise_amplitude, :gate_drift, :target_backend)
        """), defaults)
        
    return defaults


def update_user_state_in_db(user_id: str, updates: dict):
    """Dynamically applies active parameters to the operator's record layer."""
    current_state = get_or_create_user_state(user_id)
    
    # Merge incoming updates
    for key in updates:
        if key in current_state and key != "user_id":
            current_state[key] = updates[key]

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE user_states 
            SET pauli_twirling = :pauli_twirling,
                noise_amplitude = :noise_amplitude,
                gate_drift = :gate_drift,
                target_backend = :target_backend
            WHERE user_id = :user_id
        """), current_state)


# --- 🔐 AUTH0 ID LOGIC HANDSHAKES ---

@app.get("/login")
async def login(request: Request):
    """Kicks off redirect flow to the secure Auth0 hosted page."""
    redirect_uri = request.url_for("auth_callback")
    if "onrender.com" in str(redirect_uri) and not str(redirect_uri).startswith("https"):
        redirect_uri = str(redirect_uri).replace("http", "https")
        
    return await oauth.auth0.authorize_redirect(request, redirect_uri)


@app.get("/callback")
async def auth_callback(request: Request):
    """Auth0 drops the secure code payload here; we decode the user id token."""
    token = await oauth.auth0.authorize_access_token(request)
    user_info = token.get("userinfo")
    if user_info:
        request.session["user_id"] = user_info["sub"]
        request.session["user_name"] = user_info.get("name", "Operator")
    return RedirectResponse(url="/")


@app.get("/logout")
async def logout(request: Request):
    """Clears localized cookie session metrics."""
    request.session.clear()
    domain = os.environ.get("AUTH0_DOMAIN")
    client_id = os.environ.get("AUTH0_CLIENT_ID")
    return RedirectResponse(
        url=f"https://{domain}/v2/logout?client_id={client_id}&returnTo={request.base_url}"
    )


# --- 📂 INTERACTIVE ROUTING PLANES ---

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Protected Dashboard Surface (Classic Cyber-Green Base Layer)."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")
        
    current_state = get_or_create_user_state(user_id)
    return templates.TemplateResponse(
        request, "index.html", 
        {"request": request, "state": current_state, "username": request.session.get("user_name")}
    )


@app.get("/sleek", response_class=HTMLResponse)
async def get_sleek_dashboard(request: Request):
    """Protected Dashboard Surface (Ultra Sleek Gold & Purple Layer)."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")
        
    current_state = get_or_create_user_state(user_id)
    return templates.TemplateResponse(
        request, "ultra_sleek.html", 
        {"request": request, "state": current_state, "username": request.session.get("user_name")}
    )


# --- NATIVE DUAL CHANNELS OVERRIDES ---

@app.get("/api/state")
async def get_state(request: Request):
    user_id = request.session.get("user_id") or request.headers.get("X-QCB-User-Id")
    if not user_id:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    return JSONResponse(content=get_or_create_user_state(user_id))


@app.post("/api/tune")
async def tune_knobs(request: Request):
    user_id = request.session.get("user_id") or request.headers.get("X-QCB-User-Id")
    if not user_id:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
        
    data = await request.json()
    update_user_state_in_db(user_id, data)
    
    user_state = get_or_create_user_state(user_id)
    print(f"🎛️  [DATABASE WRITE] [USER:{user_id}] Parameter Shift Committed: {data}")
    return JSONResponse(content={"status": "success", "updated_state": user_state})


@app.post("/api/simulate")
async def execute_simulation_math(request: Request):
    user_id = request.session.get("user_id") or request.headers.get("X-QCB-User-Id")
    if not user_id:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
        
    state = get_or_create_user_state(user_id)
    noise = float(state.get("noise_amplitude", 0.12))
    drift = float(state.get("gate_drift", 1.1792))
    twirling_active = bool(state.get("pauli_twirling", False))
    
    base_leakage = (noise * 0.75) + ((drift / 100.0) * 0.25)
    
    if twirling_active:
        mitigated_leakage = base_leakage * 0.28 
        fidelity_loss = mitigated_leakage * 0.4
        insight = "Pauli Twirling ACTIVE: Coherent noise vector effectively randomized into standard stochastic channels. Error scaling transformed to sub-linear propagation profile."
        leakage_final = mitigated_leakage
    else:
        fidelity_loss = base_leakage * 1.35
        insight = "WARNING: Unmitigated coherent pulse drift active. Matrix leakage compounding line-by-line. Circuit depth calculation execution threshold compromised."
        leakage_final = base_leakage

    leakage_pct = f"{min(max(leakage_final * 100, 0.0), 100.0):.2f}%"
    fidelity_pct = f"{min(max((1.0 - fidelity_loss) * 100, 0.0), 100.0):.2f}%"
    hardware_status = "STABLE" if leakage_final < 0.04 else "DEGRADED" if leakage_final < 0.12 else "CRITICAL ERROR"

    return JSONResponse(content={
        "status": hardware_status,
        "leakage": leakage_pct,
        "fidelity": fidelity_pct,
        "insight": insight
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

import os
import json
import sqlite3
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Quantum Noise Co-Brain Operator Console")

# 🔐 Session & OAuth Infrastructure
# SessionMiddleware handles client cookies securely; inject a random key on Render env
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

# Direct native import from your Phase 3 backend!
try:
    from ibm_telemetry_provider import get_real_qpu_telemetry
    _, _, real_err = get_real_qpu_telemetry()
    DEFAULT_DRIFT = round(real_err * 100, 4)
except Exception:
    DEFAULT_DRIFT = 1.1792  # Fallback float if offline

# --- 🗄️ PERMANENT SQLITE DATABASE LAYER ---
DB_PATH = os.path.join(BASE_DIR, "quantum_operators.db")

def init_db():
    """Initializes the relational database table layout if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            user_id TEXT PRIMARY KEY,
            pauli_twirling BOOLEAN,
            noise_amplitude REAL,
            gate_drift REAL,
            target_backend TEXT
        )
    """)
    conn.commit()
    conn.close()

# Run database initialization on server boot sequence
init_db()

def get_or_create_user_state(user_id: str) -> dict:
    """Queries the SQL table by the unique Auth0 user key, or seeds defaults if new."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows fetching columns as dictionary keys
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_states WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        state = dict(row)
        # Ensure boolean typecasting from SQL integer storage
        state["pauli_twirling"] = bool(state["pauli_twirling"])
        conn.close()
        return state
    
    # Seed new accounts natively
    defaults = {
        "user_id": user_id,
        "pauli_twirling": 1,  # SQLite saves booleans as 1 or 0
        "noise_amplitude": 0.12,
        "gate_drift": DEFAULT_DRIFT,
        "target_backend": "ibm_fez"
    }
    cursor.execute("""
        INSERT INTO user_states (user_id, pauli_twirling, noise_amplitude, gate_drift, target_backend)
        VALUES (:user_id, :pauli_twirling, :noise_amplitude, :gate_drift, :target_backend)
    """, defaults)
    conn.commit()
    conn.close()
    
    defaults["pauli_twirling"] = True
    return defaults


def update_user_state_in_db(user_id: str, updates: dict):
    """Dynamically applies active parameters to the operator's private SQL row."""
    current_state = get_or_create_user_state(user_id)
    
    # Merge updates into historical record values
    for key in updates:
        if key in current_state and key != "user_id":
            current_state[key] = updates[key]
            
    # Handle boolean conversion for storage compatibility
    if "pauli_twirling" in current_state:
        current_state["pauli_twirling"] = 1 if current_state["pauli_twirling"] else 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_states 
        SET pauli_twirling = :pauli_twirling,
            noise_amplitude = :noise_amplitude,
            gate_drift = :gate_drift,
            target_backend = :target_backend
        WHERE user_id = :user_id
    """, current_state)
    conn.commit()
    conn.close()


# --- 🔐 AUTH0 ID LOGIC HANDSHAKES ---

@app.get("/login")
async def login(request: Request):
    """Kicks off redirect flow to the secure Auth0 hosted page."""
    # Ensure Render's secure path handling stays native on callbacks
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
        # Save the distinct identity primary key directly into the encrypted cookie session
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
    """Protected Dashboard Surface."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")
        
    current_state = get_or_create_user_state(user_id)
    return templates.TemplateResponse(
        request, "index.html", 
        {"request": request, "state": current_state, "username": request.session.get("user_name")}
    )


@app.get("/api/state")
async def get_state(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    return JSONResponse(content=get_or_create_user_state(user_id))


@app.post("/api/tune")
async def tune_knobs(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
        
    data = await request.json()
    # Write directly to the local SQL relational layer
    update_user_state_in_db(user_id, data)
    
    user_state = get_or_create_user_state(user_id)
    print(f"🎛️  [DATABASE WRITE] [USER:{user_id}] Parameter Shift Committed: {data}")
    return JSONResponse(content={"status": "success", "updated_state": user_state})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

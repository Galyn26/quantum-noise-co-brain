import os
import json
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

# 🗄️ IN-MEMORY SIMULATED USER DATABASE
# Keys will be unique Auth0 string tokens (e.g., "auth0|61234b...")
user_database = {}

def get_or_create_user_state(user_id: str) -> dict:
    """Simulates looking up user parameters by primary key in a DB table."""
    if user_id not in user_database:
        user_database[user_id] = {
            "pauli_twirling": True,
            "noise_amplitude": 0.12,
            "gate_drift": DEFAULT_DRIFT,
            "target_backend": "ibm_fez"
        }
    return user_database[user_id]


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
    user_state = get_or_create_user_state(user_id)
    
    for key in data:
        if key in user_state:
            user_state[key] = data[key]
            
    print(f"🎛️  [USER:{user_id}] Parameter Shift: {data}")
    return JSONResponse(content={"status": "success", "updated_state": user_state})


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

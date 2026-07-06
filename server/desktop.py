from __future__ import annotations
import os
import sys
import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import webview  # 🛰️ The ultra-lightweight, cross-platform engine

@dataclass(frozen=True)
class DesktopConfig:
    production_url: str = "https://quantum-noise-co-brain-desktop.onrender.com" 
    auth0_domain: str = "dev-cn0kk0ltplgxom8s.us.auth0.com"
    auth0_client_id: str = "ZYlx455K5OyuZrnukz7mGBuK76dqIolm"

    @property
    def server_url(self) -> str:
        return self.production_url

    @property
    def redirect_uri(self) -> str:
        # 🎯 Switch from localhost to your secure Render domain
        return "https://quantum-noise-co-brain-desktop.onrender.com/callback"

    @property
    def authorize_url(self) -> str:
        return f"https://{self.auth0_domain}/authorize"

    @property
    def token_url(self) -> str:
        return f"https://{self.auth0_domain}/oauth/token"


CONFIG = DesktopConfig()
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".quantumcobrain")
TOKEN_PATH = os.path.join(CONFIG_DIR, "session_token.json")


def _decode_jwt_payload(jwt_token: str) -> Dict[str, Any]:
    payload_b64 = jwt_token.split(".")[1]
    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
    payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
    return json.loads(payload_json)


def _generate_pkce_pair() -> tuple[str, str]:
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode("utf-8").rstrip("=")
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


class SessionTokenStore:
    def __init__(self, token_path: str):
        self._token_path = token_path

    def load_valid(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self._token_path):
            return None
        try:
            with open(self._token_path, "r", encoding="utf-8") as token_file:
                token_payload = json.load(token_file)
        except (OSError, json.JSONDecodeError):
            return None

        expires_at = int(token_payload.get("expires_at", 0))
        if expires_at <= int(time.time()):
            self.clear()
            return None
        return token_payload

    def save(self, token_payload: Dict[str, Any]) -> None:
        payload = dict(token_payload)
        expires_in = int(payload.get("expires_in", 3600))
        payload["expires_at"] = int(time.time()) + max(expires_in - 30, 30)
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(self._token_path, "w", encoding="utf-8") as token_file:
            json.dump(payload, token_file)

    def clear(self) -> None:
        try:
            if os.path.exists(self._token_path):
                os.remove(self._token_path)
        except OSError:
            pass


class LocalApiClient:
    def __init__(self, config: DesktopConfig):
        self._config = config

    def call(
        self,
        method: str,
        path: str,
        token_payload: Optional[Dict[str, Any]],
        user_context: Optional[Dict[str, str]],
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self._config.server_url}{path}"
        headers: Dict[str, str] = {"Accept": "application/json"}
        params = {}

        if token_payload:
            auth_token = token_payload.get("access_token") or token_payload.get("id_token")
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

        if user_context:
            user_id = user_context.get("user_id")
            username = user_context.get("username")
            if user_id:
                headers["X-QCB-User-Id"] = user_id
                params["user_id"] = user_id
            if username:
                headers["X-QCB-User-Name"] = username
                params["username"] = username

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params or None,
                    json=json_body,
                )
            payload = response.json() if response.content else {}
            if response.is_error:
                return {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": payload if isinstance(payload, dict) else {"error": str(payload)},
                }
            return {"ok": True, "status_code": response.status_code, "data": payload}
        except (httpx.HTTPError, ValueError) as exc:
            return {"ok": False, "status_code": 0, "error": {"error": str(exc)}}


class NativeBridge:
    def __init__(self):
        self.config = CONFIG
        self.token_store = SessionTokenStore(TOKEN_PATH)
        self.api_client = LocalApiClient(CONFIG)
        self.token_payload: Optional[Dict[str, Any]] = None
        self.user_context: Optional[Dict[str, str]] = None
        self.pkce_verifier: Optional[str] = None
        self.pkce_state: Optional[str] = None
        self.window = None

    def initialize_runtime(self, window_instance):
        self.window = window_instance
        
        if getattr(sys, "_MEIPASS", None):
            server_dir = os.path.join(sys._MEIPASS, "server")
        else:
            server_dir = os.path.dirname(os.path.abspath(__file__))
            
        desktop_template_path = os.path.join(server_dir, "templates", "desktop.html")
        
        token_payload = self.token_store.load_valid()
        if not token_payload:
            self.start_pkce_login(force_prompt=False)
            return

        self.token_payload = token_payload
        self.user_context = self._extract_user_context(token_payload)
        
        if os.path.exists(desktop_template_path):
            self.window.load_url(f"file://{desktop_template_path}")
        else:
            self.window.load_url(self.config.server_url)

    def start_pkce_login(self, force_prompt: bool = True) -> None:
        self.pkce_verifier, challenge = _generate_pkce_pair()
        self.pkce_state = secrets.token_urlsafe(24)

        auth_params = {
            "response_type": "code",
            "client_id": self.config.auth0_client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": "openid profile email",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": self.pkce_state,
        }
        if force_prompt:
            auth_params["prompt"] = "login"
            auth_params["max_age"] = "0"

        authorize_url = f"{self.config.authorize_url}?{urlencode(auth_params)}"
        self.window.load_url(authorize_url)

    def handle_url_shift(self, url: str):
        current_url = url.lower()
        if any(x in current_url for x in ("desktop-logged-out", "logged-out", "/logout", "/login")):
            self.perform_logout()
            return

        # 🎯 FIX: Changed .startswith() to an inclusive substring query to account for WebKit trailing slashes
        if self.config.redirect_uri in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            state = params.get("state", [None])[0]

            if code and state == self.pkce_state:
                self._exchange_code_for_token(code)

    def _exchange_code_for_token(self, authorization_code: str) -> None:
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.config.token_url,
                    json={
                        "grant_type": "authorization_code",
                        "client_id": self.config.auth0_client_id,
                        "code_verifier": self.pkce_verifier,
                        "code": authorization_code,
                        "redirect_uri": self.config.redirect_uri,
                    },
                )
                response.raise_for_status()
                token_payload = response.json()
        except Exception:
            self.start_pkce_login(force_prompt=True)
            return

        user_context = self._extract_user_context(token_payload)
        if not user_context:
            self.start_pkce_login(force_prompt=True)
            return

        self.token_store.save(token_payload)
        self.token_payload = token_payload
        self.user_context = user_context
        
        if getattr(sys, "_MEIPASS", None):
            server_dir = os.path.join(sys._MEIPASS, "server")
        else:
            server_dir = os.path.dirname(os.path.abspath(__file__))
        desktop_template_path = os.path.join(server_dir, "templates", "desktop.html")
        
        if os.path.exists(desktop_template_path):
            self.window.load_url(f"file://{desktop_template_path}")
        else:
            self.window.load_url(self.config.server_url)

    def _extract_user_context(self, token_payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
        id_token = token_payload.get("id_token")
        if not id_token:
            return None
        try:
            claims = _decode_jwt_payload(id_token)
        except Exception:
            return None
        user_id = claims.get("sub")
        if not user_id:
            return None
        username = claims.get("name") or claims.get("nickname") or "Operator"
        return {"user_id": str(user_id), "username": str(username)}

    def perform_logout(self) -> None:
        self.token_payload = None
        self.user_context = None
        self.pkce_verifier = None
        self.pkce_state = None
        self.token_store.clear()
        
        self.window.clear_cookies()
        self.start_pkce_login(force_prompt=True)

    def get_user_context(self):
        ctx = self.user_context or {}
        return {str(k): str(v) for k, v in ctx.items() if v is not None}

    def trigger_native_logout(self):
        self.perform_logout()
        return "LOGOUT_COMPLETE" # 🎯 FIX: Keeps the asynchronous JS promise callback happy

    def push_tuning_parameters(self, patch):
        return self.api_client.call("POST", "/api/tune", self.token_payload, self.user_context, json_body=patch)

    def run_nisq_experiment(self):
        return self.api_client.call("POST", "/api/simulate", self.token_payload, self.user_context)

    def fetch_backend_state(self):
        return self.api_client.call("GET", "/api/state", self.token_payload, self.user_context)
   
    def save_snapshot_dialog(self, json_data_str: str) -> None:
        """Opens a secure native file window saving the snapshot without changing pages."""
        try:
            file_path = self.window.create_file_dialog(
                webview.SAVE_DIALOG, # 🎯 FIX: Changed from SAVE_FILE to SAVE_DIALOG
                directory=os.path.expanduser("~"),
                file_types=("JSON Files (*.json)",),
                save_filename=f"quantum_snapshot_{int(time.time())}.json"
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(json_data_str)
                print(f"💾 Snapshot captured and successfully committed to: {file_path}")
        except Exception as e:
            print(f"❌ Failed to run local disk save pipeline: {e}")

def run_background_engine(window, bridge):
    """Runs isolated on its own independent background thread."""
    bridge.initialize_runtime(window)


def main():
    print("🛰️  Initializing Native Desktop Co-Brain Engine via System Web-Core...")

    bridge = NativeBridge()

    window = webview.create_window(
        title="Quantum Noise Co-Brain Operator Console",
        url="http://127.0.0.1:8443", 
        js_api=bridge,
        width=1280,
        height=800,
        min_size=(1024, 768),
        text_select=True
    )

    def handle_navigation(w=None):
        url = window.get_current_url() or ""
        # 🎯 Only wake up when the final token landing page actually hits the frame
        if "quantum-noise-co-brain-desktop.onrender.com/callback" in url:
            print(f"📡 Auth0 Handshake Detected! Processing endpoint: {url}")
            bridge.handle_url_shift(url)

    window.events.loaded += handle_navigation
    webview.start(run_background_engine, (window, bridge), debug=False)


if __name__ == "__main__":
    main()

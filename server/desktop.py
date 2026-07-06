import os
import sys

# 🛰️ Force QtWebEngineProcess Path Identification for Mac Bundles FIRST
if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
    # Calculate the absolute path inside the bundled application structure
    bundle_dir = os.path.dirname(sys.executable)
    # Standard PyInstaller location for the engine process helper
    qt_engine_path = os.path.join(bundle_dir, "..", "Frameworks", "QtWebEngineCore.framework", "Helpers", "QtWebEngineProcess.app", "Contents", "MacOS", "QtWebEngineProcess")
    
    # Alternate layout check (internal internal internal backup paths)
    if not os.path.exists(qt_engine_path):
        qt_engine_path = os.path.join(bundle_dir, "_internal", "PyQt5", "Qt5", "lib", "QtWebEngineCore.framework", "Helpers", "QtWebEngineProcess.app", "Contents", "MacOS", "QtWebEngineProcess")

    # Force set the environment variable so the core module handshakes perfectly
    os.environ["QTWEBENGINEPROCESS_PATH"] = os.path.abspath(qt_engine_path)
    print(f"🎯 Target Engine Process Lock: {os.environ['QTWEBENGINEPROCESS_PATH']}")

# Now it is safe to pull in your core dependencies safely
import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dotenv import load_dotenv
from PyQt5.QtCore import QObject, Qt, QUrl, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngine import QtWebEngine
from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineView
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget


@dataclass(frozen=True)
class DesktopConfig:
    # TODO: Replace with your actual live Render app URL
    production_url: str = "https://quantum-noise-co-brain-desktop.onrender.com" 
    auth0_domain: str = "dev-cn0kk0ltplgxom8s.us.auth0.com"
    auth0_client_id: str = "ZYlx455K5OyuZrnukz7mGBuK76dqIolm"

    @property
    def server_url(self) -> str:
        return self.production_url

    @property
    def redirect_uri(self) -> str:
        return "http://127.0.0.1:8443/desktop-callback"

    @property
    def authorize_url(self) -> str:
        return f"https://{self.auth0_domain}/authorize"

    @property
    def token_url(self) -> str:
        return f"https://{self.auth0_domain}/oauth/token"


CONFIG = DesktopConfig()
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".quantumcobrain")
TOKEN_PATH = os.path.join(CONFIG_DIR, "session_token.json")

if getattr(sys, "_MEIPASS", None):
    SERVER_DIR = os.path.join(sys._MEIPASS, "server")
else:
    SERVER_DIR = os.path.dirname(os.path.abspath(__file__))


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


class AuthView(QWidget):
    def __init__(self):
        super().__init__()
        self.status_label = QLabel("Sign in required.")
        self.status_label.setWordWrap(True)
        self.sign_in_button = QPushButton("Sign in with Auth0")
        self.web_view = QWebEngineView()
        # Clean slate initializing - avoids pre-render crashes
        
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.sign_in_button)
        layout.addWidget(self.web_view, stretch=1)
        self.setLayout(layout)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.web_view = QWebEngineView()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
        self.setLayout(layout)


class NativeBridge(QObject):
    def __init__(self, main_window: "DesktopWindow"):
        super().__init__()
        self.main_window = main_window

    @pyqtSlot(result="QVariantMap")
    def get_user_context(self):
        ctx = self.main_window._user_context or {}
        return {str(k): str(v) for k, v in ctx.items() if v is not None}

    @pyqtSlot()
    def trigger_native_logout(self):
        self.main_window.perform_logout()

    @pyqtSlot("QVariantMap", result="QVariantMap")
    def push_tuning_parameters(self, patch):
        return self.main_window._api_client.call(
            "POST", "/api/tune",
            self.main_window._token_payload,
            self.main_window._user_context,
            json_body=patch
        )

    @pyqtSlot(result="QVariantMap")
    def run_nisq_experiment(self):
        return self.main_window._api_client.call(
            "POST", "/api/simulate", 
            self.main_window._token_payload, 
            self.main_window._user_context
        )

    @pyqtSlot(result="QVariantMap")
    def fetch_backend_state(self):
        return self.main_window._api_client.call(
            "GET", "/api/state",
            self.main_window._token_payload,
            self.main_window._user_context
        )


class DesktopWindow(QWidget):
    AUTH_STATE_INDEX = 0
    DASHBOARD_STATE_INDEX = 1

    def __init__(self, config: DesktopConfig, server_manager: Optional[Any] = None):
        super().__init__()
        self._config = config
        self._server_manager = server_manager
        self._token_store = SessionTokenStore(TOKEN_PATH)
        self._api_client = LocalApiClient(config)
        self._token_payload: Optional[Dict[str, Any]] = None
        self._user_context: Optional[Dict[str, str]] = None
        self._pkce_verifier: Optional[str] = None
        self._pkce_state: Optional[str] = None

        self.setWindowTitle("Quantum Noise Co-Brain Operator Console")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 768)

        self.stack = QStackedWidget()
        self.auth_view = AuthView()
        self.dashboard_view = DashboardView()
        self.stack.addWidget(self.auth_view)
        self.stack.addWidget(self.dashboard_view)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

        self.bridge = NativeBridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("pyBridge", self.bridge)
        self.dashboard_view.web_view.page().setWebChannel(self.channel)

        self.auth_view.sign_in_button.clicked.connect(lambda: self.start_pkce_login(force_prompt=True))
        self.auth_view.web_view.urlChanged.connect(self._on_auth_webview_url_changed)
        self.dashboard_view.web_view.urlChanged.connect(self._on_dashboard_url_changed)

        self._bootstrap_from_local_session()

    def _on_dashboard_url_changed(self, qurl: QUrl) -> None:
        current_url = qurl.toString().lower()
        if any(x in current_url for x in ("desktop-logged-out", "logged-out", "/logout", "/login")):
            self.perform_logout()

    def _bootstrap_from_local_session(self) -> None:
        token_payload = self._token_store.load_valid()
        if not token_payload:
            self.stack.setCurrentIndex(self.AUTH_STATE_INDEX)
            self.auth_view.set_status("Secure token session missing. Routing to live authorization gateway...")
            # Automatically load your live Render app's secure login channel!
            self.auth_view.web_view.setUrl(QUrl(f"{self._config.server_url}/login"))
            return

        user_context = self._extract_user_context(token_payload)
        if not user_context:
            self.perform_logout()
            return

        self._set_authenticated_session(token_payload, user_context)

    def _extract_user_context(self, token_payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
        id_token = token_payload.get("id_token")
        if not id_token:
            return None

        try:
            claims = _decode_jwt_payload(id_token)
        except (ValueError, IndexError, json.JSONDecodeError):
            return None

        user_id = claims.get("sub")
        if not user_id:
            return None

        username = claims.get("name") or claims.get("nickname") or "Operator"
        return {"user_id": str(user_id), "username": str(username)}

    def _set_authenticated_session(self, token_payload: Dict[str, Any], user_context: Dict[str, str]) -> None:
        self._token_payload = token_payload
        self._user_context = user_context

        desktop_template_path = os.path.join(SERVER_DIR, "templates", "desktop.html")
        if os.path.exists(desktop_template_path):
            self.dashboard_view.web_view.setUrl(QUrl.fromLocalFile(desktop_template_path))
        else:
            self.dashboard_view.web_view.setHtml(
                "<html><body>desktop.html not found in server/templates.</body></html>"
            )

        self.stack.setCurrentIndex(self.DASHBOARD_STATE_INDEX)

    def start_pkce_login(self, force_prompt: bool = False) -> None:
        self._pkce_verifier, challenge = _generate_pkce_pair()
        self._pkce_state = secrets.token_urlsafe(24)

        auth_params = {
            "response_type": "code",
            "client_id": self._config.auth0_client_id,
            "redirect_uri": self._config.redirect_uri,
            "scope": "openid profile email",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": self._pkce_state,
        }
        if force_prompt:
            auth_params["prompt"] = "login"
            auth_params["max_age"] = "0"

        authorize_url = f"{self._config.authorize_url}?{urlencode(auth_params)}"
        self.auth_view.set_status("Waiting for Auth0 sign-in...")
        self.stack.setCurrentIndex(self.AUTH_STATE_INDEX)
        self.auth_view.web_view.setUrl(QUrl(authorize_url))

    def _on_auth_webview_url_changed(self, qurl: QUrl) -> None:
        current_url = qurl.toString()
        if not current_url.startswith(self._config.redirect_uri):
            return

        parsed = urlparse(current_url)
        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        oauth_error = params.get("error", [None])[0]

        if oauth_error:
            self.auth_view.set_status(f"Authentication failed: {oauth_error}")
            return

        if not code or state != self._pkce_state:
            self.auth_view.set_status("Authentication failed: invalid callback state.")
            return

        self.auth_view.web_view.setHtml("<html><body>Completing secure token exchange...</body></html>")
        self._exchange_code_for_token(code)

    def _exchange_code_for_token(self, authorization_code: str) -> None:
        if not self._pkce_verifier:
            self.auth_view.set_status("Authentication failed: missing PKCE verifier.")
            return

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self._config.token_url,
                    json={
                        "grant_type": "authorization_code",
                        "client_id": self._config.auth0_client_id,
                        "code_verifier": self._pkce_verifier,
                        "code": authorization_code,
                        "redirect_uri": self._config.redirect_uri,
                    },
                )
                response.raise_for_status()
                token_payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            self.auth_view.set_status(f"Token exchange failed: {exc}")
            return

        user_context = self._extract_user_context(token_payload)
        if not user_context:
            self.auth_view.set_status("Token exchange failed: id_token is missing required claims.")
            return

        try:
            self._token_store.save(token_payload)
        except OSError as exc:
            self.auth_view.set_status(f"Token persistence failed: {exc}")
            return

        self._set_authenticated_session(token_payload, user_context)

    def perform_logout(self) -> None:
        self._token_payload = None
        self._user_context = None
        self._pkce_verifier = None
        self._pkce_state = None
        self._token_store.clear()

        profile = QWebEngineProfile.defaultProfile()
        profile.cookieStore().deleteAllCookies()
        profile.clearHttpCache()

        self.auth_view.set_status("Session cleared locally.")
        self.stack.setCurrentIndex(self.AUTH_STATE_INDEX)
        self.start_pkce_login(force_prompt=True)

    def closeEvent(self, event):  # noqa: N802
        if self._server_manager:
            self._server_manager.stop()
        super().closeEvent(event)


def main() -> int:
    print("🛰️  Initializing Native Desktop Co-Brain Engine...")

    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    QtWebEngine.initialize()

    from PyQt5.QtWebEngineWidgets import QWebEngineSettings
    QWebEngineSettings.globalSettings().setAttribute(
        QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
    )

    window = DesktopWindow(CONFIG, server_manager=None) 
    window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

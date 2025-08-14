# app.py
import os
import json
import base64
import requests
import bcrypt
import yaml
import streamlit as st
from pathlib import Path
from typing import Dict, List

# =======================
# ❖ Config / Constants  |
# =======================
APP_TITLE = "RSM Assistant"
APP_ICON = "💬"
APP_LAYOUT = "centered"  # "wide" or "centered"

CREDENTIALS_PATH = Path("credentials.yaml")
LOGO_PATH = Path(".streamlit/rsm logo.png")

# ---------- Secrets / API ----------
LLM_API_KEY = os.getenv("AZURE_API_KEY", "")
LLM_ENDPOINT = os.getenv("AZURE_API_ENDPOINT", "")

# ---------- Session Keys ----------
SK_AUTH = "authenticated"
SK_USER = "username"
SK_MSGS = "messages"

MAX_CONTEXT_MESSAGES = 12
SYSTEM_PROMPT_PREFIX = "You are a helpful assistant. Here is chat context:\n"

# =========================
# ❖ Page / Global Styling |
# =========================
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=APP_LAYOUT)

def inject_css() -> None:
    st.markdown(
        """
        <style>
            /* Fonts */
            @font-face {
                font-family: 'Prelo';
                src: url('assets/fonts/Prelo-Light.woff2') format('woff2'),
                     url('assets/fonts/Prelo-Light.woff') format('woff');
                font-weight: 300;
                font-style: normal;
                font-display: swap;
            }
            @font-face {
                font-family: 'Prelo';
                src: url('assets/fonts/Prelo-Light.woff2') format('woff2'),
                     url('assets/fonts/Prelo-Light.woff') format('woff');
                font-weight: 400;
                font-style: normal;
                font-display: swap;
            }

            :root {
                --brand-primary: #009CDE;
                --brand-user:    #3F9C35;
                --text-muted:    #6b7280;
                --card-bg:       #ffffff;
                --app-bg:        #f7fafc;
                --radius:        16px;
                --shadow:        0 6px 24px rgba(0,0,0,0.08);
            }

            html, body, [class*="css"]  {
                font-family: 'Prelo', -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif !important;
                background: var(--app-bg);
            }

            /* Login card */
            .login-card {
                background: var(--card-bg);
                padding: 1.75rem;
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                width: 100%;
                max-width: 420px;
                margin: 2.5rem auto 1rem auto;
            }
            .login-title { text-align: center; margin: 0 0 1rem 0; font-weight: 700; }
            .brand-muted { color: var(--text-muted); }

            /* Logo */
            .brand-logo {
                display: block;
                margin: 1rem auto 0.5rem auto;
                width: 120px;
                max-width: 45vw;
            }

            /* Chat layout */
            .chat-wrapper {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
                margin-top: 0.75rem;
            }
            .msg-row { display: flex; width: 100%; }
            .msg-row.assistant { justify-content: flex-start; }
            .msg-row.user      { justify-content: flex-end; }

            .msg-bubble {
                max-width: min(72ch, 78%);
                padding: 0.9rem 1rem;
                color: #fff;
                line-height: 1.4;
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                word-wrap: break-word;
                white-space: pre-wrap;
                font-weight: 400;
            }
            .assistant .msg-bubble { background: var(--brand-primary); border-top-left-radius: 6px; }
            .user .msg-bubble      { background: var(--brand-user);    border-top-right-radius: 6px; }

            /* Hide hamburger on login for cleaner look */
            [data-testid="collapsedControl"] { display: none; }

            /* ===== Sidebar ordering ===== */
            [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
                display: flex;
                flex-direction: column;
            }
            .branding-top { order: 0; }
            [data-testid="stSidebarNav"] { order: 1; margin-top: 0.5rem; }
            .sidebar-rest { order: 2; }

        </style>
        """,
        unsafe_allow_html=True,
    )

def logo_img_base64() -> str | None:
    if LOGO_PATH and LOGO_PATH.exists():
        try:
            return base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
        except Exception:
            return None
    return None

def show_logo(center: bool = True) -> None:
    b64 = logo_img_base64()
    if b64:
        align = "margin-left:auto;margin-right:auto;" if center else ""
        st.markdown(
            f'<img class="brand-logo" src="data:image/png;base64,{b64}" style="{align}" />',
            unsafe_allow_html=True,
        )

# ==========================
# ❖ Credentials / Auth     |
# ==========================
def load_credentials(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    try:
        cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return (cfg.get("credentials", {}) or {}).get("users", {}) or {}
    except Exception:
        return {}

def verify_user(users: Dict[str, Dict[str, str]], username: str, password: str) -> bool:
    user = users.get(username)
    if not user:
        return False
    hashed = (user.get("password") or "").encode("utf-8")
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except ValueError:
        return False

def logout() -> None:
    for k in (SK_AUTH, SK_USER, SK_MSGS):
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# ---------- Conversation helpers ----------
def clear_conversation():
    """Clears all messages (no greeting)."""
    st.session_state[SK_MSGS] = []
    st.rerun()

def new_chat():
    """Starts a brand-new chat with the default assistant greeting."""
    st.session_state[SK_MSGS] = [{"role": "assistant", "content": "Hi! How can I help today?"}]
    st.rerun()

# ==========================
# ❖ LLM Call               |
# ==========================
def get_llm_response(prompt: str, context: str) -> str:
    if not LLM_API_KEY or not LLM_ENDPOINT:
        raise RuntimeError("Missing LLM configuration. Set AZURE_API_KEY and AZURE_API_ENDPOINT.")

    headers = {"Content-Type": "application/json", "api-key": LLM_API_KEY}
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PREFIX + context},
        {"role": "user", "content": prompt},
    ]

    try:
        resp = requests.post(LLM_ENDPOINT, headers=headers, json={"messages": messages}, timeout=60)
    except requests.RequestException as e:
        raise RuntimeError(f"Network error calling LLM: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"LLM error {resp.status_code}: {resp.text}")

    data = resp.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        content = data.get("output") or data.get("reply") or json.dumps(data)
    return content

# ==========================
# ❖ UI Helpers             |
# ==========================
def render_chat_history(messages: List[Dict[str, str]]) -> None:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for m in messages:
        role = m.get("role", "assistant")
        content = m.get("content", "")
        st.markdown(
            f"""
            <div class="msg-row {role}">
                <div class="msg-bubble">{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# ❖ UI: Login              |
# ==========================
def login_ui() -> None:
    with st.sidebar:
        st.empty()

    show_logo(center=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="login-title">{APP_ICON} Sign in</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p class="brand-muted" style="text-align:center;margin-top:-0.5rem;">Welcome back — please authenticate to continue.</p>',
        unsafe_allow_html=True,
    )

    users = load_credentials(CREDENTIALS_PATH)
    if not users:
        with st.expander("Setup help (credentials.yaml not found or empty)"):
            st.code(
                """# credentials.yaml
credentials:
  users:
    YourUser:
      name: "Your Name"
      # bcrypt hash; generate with Python/bcrypt or an online tool
      password: "$2b$12$examplehashreplacewithreal"
""",
                language="yaml",
            )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if not username or not password:
            st.warning("Please enter both username and password.")
        elif verify_user(users, username, password):
            st.session_state[SK_AUTH] = True
            st.session_state[SK_USER] = username
            st.session_state.setdefault(
                SK_MSGS,
                [{"role": "assistant", "content": "Hi! How can I help today?"}],
            )
            st.success("Login successful. Loading chat…")
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================
# ❖ UI: Chat               |
# ==========================
def chat_ui() -> None:
    with st.sidebar:
        # ---------- Top branding (ordered first via CSS) ----------
        st.markdown('<div class="branding-top">', unsafe_allow_html=True)
        show_logo(center=False)
        st.markdown(
            f'<div style="font-size:0.925rem;color:#6b7280;margin:0.5rem 0 0.5rem 0;">'
            f'Signed in as <b>{st.session_state.get(SK_USER)}</b></div>',
            unsafe_allow_html=True,
        )
        st.button("Log out", type="secondary", on_click=logout)
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- Session controls (ordered after the nav) ----------
        st.markdown('<div class="sidebar-rest">', unsafe_allow_html=True)
        st.markdown("---")
        st.caption("Session")
        c1, c2 = st.columns(2)
        with c1:
            st.button("New chat", on_click=new_chat)
        with c2:
            st.button("Clear conversation", on_click=clear_conversation)
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Main chat area ----------
    st.title(APP_TITLE)
    st.header("Chat", anchor=False)
    st.caption("Assistant on the left, you on the right. Recent history is sent as context to the model.")

    st.session_state.setdefault(SK_MSGS, [])
    render_chat_history(st.session_state[SK_MSGS])

    prompt = st.chat_input("Type your message…")
    if prompt:
        st.session_state[SK_MSGS].append({"role": "user", "content": prompt})
        render_chat_history([{"role": "user", "content": prompt}])

        recent = st.session_state[SK_MSGS][-MAX_CONTEXT_MESSAGES:]
        context_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

        with st.spinner("Thinking…"):
            try:
                reply = get_llm_response(prompt, context_text)
            except Exception as e:
                reply = f"Sorry, I hit an error calling the model:\n\n```\n{e}\n```"

        render_chat_history([{"role": "assistant", "content": reply}])
        st.session_state[SK_MSGS].append({"role": "assistant", "content": reply})

# ==========================
# ❖ App Entry              |
# ==========================
def main() -> None:
    inject_css()
    if not st.session_state.get(SK_AUTH):
        login_ui()
    else:
        chat_ui()

if __name__ == "__main__":
    main()

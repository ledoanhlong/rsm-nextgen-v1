# app.py
from __future__ import annotations
import os
import json
import base64
import html
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import bcrypt
import requests
import streamlit as st
import yaml
import streamlit.components.v1 as components

# =======================
# ❖ Config / Constants  |
# =======================
APP_TITLE = "RSM NextGen Home Page"
APP_ICON = "💬"
APP_LAYOUT = "wide"   # wide for more room

CREDENTIALS_PATH = Path("credentials.yaml")
LOGO_PATH = Path(".streamlit/rsm logo.png")

# ---------- LLM Settings ----------
LLM_API_KEY = os.getenv("AZURE_API_KEY", "")
LLM_ENDPOINT = os.getenv("AZURE_API_ENDPOINT", "")

SK_AUTH = "authenticated"
SK_USER = "username"
SK_MSGS = "messages"

MAX_CONTEXT_MESSAGES = 12
SYSTEM_PROMPT_PREFIX = "You are a helpful assistant. Here is chat context:\n"

# ---------- Power BI org-embed URL ----------
PBI_EMBED_URL = os.getenv(
    "PBI_EMBED_URL",
    "https://app.powerbi.com/reportEmbed?reportId=90e24eba-e8f2-47a5-905c-f6365f006497&autoAuth=true&ctid=8b279c2c-479d-4b14-8903-efe33db3d877"
)

# =========================
# ❖ Page / Global Styling |
# =========================
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=APP_LAYOUT)

def inject_css() -> None:
    st.markdown(
        """
        <style>
            /* Prelo font (served from /static/fonts) */
            @font-face {
                font-family: 'Prelo';
                src: url('/static/fonts/Prelo-Light.woff2') format('woff2'),
                     url('/static/fonts/Prelo-Light.woff') format('woff');
                font-weight: 300;
                font-style: normal;
                font-display: swap;
            }

            :root {
                --brand-primary: #009CDE;
                --brand-user:    #3F9C35;
                --text-muted:    #9aa0a6;
                --card-bg:       #ffffff;
                --app-bg:        #0b1220; /* darker app background */
                --expander-bg:   #0b1220; /* dark chat panel */
                --expander-head: #0f172a; /* darker header band */
                --radius:        20px;
                --shadow:        0 16px 40px rgba(0,0,0,0.25);
            }

            html, body, [class*="css"] {
                font-family: 'Prelo', -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif !important;
                background: var(--app-bg);
            }

            .block-container { max-width: 100%; padding-top: 1.25rem; }

            .login-card {
                background: #0f172a;
                color: #e5e7eb;
                padding: 1.75rem;
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                width: 100%;
                max-width: 420px;
                margin: 2.5rem auto 1rem auto;
                border: 1px solid rgba(255,255,255,0.06);
            }
            .login-title { text-align: center; margin: 0 0 1rem 0; font-weight: 700; }
            .brand-muted { color: var(--text-muted); }

            .brand-logo {
                display: block;
                margin: 2rem auto 0.75rem auto;
                width: 120px;
                max-width: 45vw;
            }

            /* Chat bubbles */
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
                max-width: min(80ch, 78%);
                padding: 0.9rem 1rem;
                color: #fff;
                line-height: 1.45;
                border-radius: 16px;
                box-shadow: 0 12px 28px rgba(0,0,0,0.35);
                word-wrap: break-word;
                white-space: pre-wrap;
                font-weight: 400;
            }
            .assistant .msg-bubble { background: var(--brand-primary); border-top-left-radius: 6px; }
            .user .msg-bubble      { background: var(--brand-user);    border-top-right-radius: 6px; }

            /* Power BI card (light) */
            .pbi-card {
                position: relative;
                width: 100%;
                border-radius: var(--radius);
                overflow: hidden;
                box-shadow: var(--shadow);
                background: #fff;
                border: 1px solid rgba(0,0,0,0.05);
            }
            .pbi-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: .8rem 1rem;
                border-bottom: 1px solid rgba(0,0,0,0.06);
                background: linear-gradient(180deg, #fff, #fafafa);
            }
            .pbi-title { font-weight: 600; color: #111827; }
            .pbi-actions { display: flex; gap: .5rem; }
            .pbi-btn {
                border: 0;
                border-radius: 999px;
                padding: .4rem .8rem;
                cursor: pointer;
                background: #f1f5f9;
            }
            .pbi-btn:hover { background: #e5e7eb; }

            .pbi-frame { width: 100%; height: 100%; border: 0; display: block; }

            /* Scoped expander styling
               - Dashboard expander: light (inside .pbi-expander)
               - Chat expander: dark (inside .chat-card)
            */
            .pbi-expander [data-testid="stExpander"] > details {
                border-radius: var(--radius);
                border: 1px solid rgba(0,0,0,0.06);
                box-shadow: var(--shadow);
                background: #fff;
                overflow: hidden;
            }
            .pbi-expander [data-testid="stExpander"] > details > summary {
                padding: .8rem 1rem !important;
                background: linear-gradient(180deg, #fff, #f8fafc);
                font-weight: 600;
                color: #111827;
            }
            .pbi-expander [data-testid="stExpander"] [data-testid="stExpanderContent"] {
                padding: 0 .75rem 1rem .75rem;
                background: #fff;
                color: #111827;
            }

            .chat-card [data-testid="stExpander"] > details {
                border-radius: var(--radius);
                border: 1px solid rgba(255,255,255,0.08);
                box-shadow: var(--shadow);
                background: var(--expander-bg);
                overflow: hidden;
            }
            .chat-card [data-testid="stExpander"] > details > summary {
                padding: .8rem 1rem !important;
                background: linear-gradient(180deg, var(--expander-head), var(--expander-bg));
                font-weight: 600;
                color: #e5e7eb;
            }
            .chat-card [data-testid="stExpander"] [data-testid="stExpanderContent"] {
                padding: 0 .75rem 1rem .75rem;
                background: var(--expander-bg);
                color: #e5e7eb;
            }

            /* Dark inputs */
            textarea, input, select {
                background-color: #0f172a !important;
                color: #e5e7eb !important;
                border-color: rgba(255,255,255,0.12) !important;
            }

            [data-testid="collapsedControl"] { display: none; }
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
    content = (data.get("choices", [{}])[0].get("message", {}).get("content"))
    if not content:
        content = data.get("output") or data.get("reply") or json.dumps(data)
    return content

# ==========================
# ❖ Power BI               |
# ==========================
def _with_hidden_panes(url: str) -> str:
    """
    Ensure org-embed URL hides the nav + filter panes and removes chrome.
    Force 'fullscreen' and FitToWidth.
    """
    try:
        parsed = urlparse(url)
        q = dict(parse_qsl(parsed.query))

        q["navContentPaneEnabled"] = "false"
        q["filterPaneEnabled"]     = "false"
        q["chromeless"]            = "true"
        q["pageView"]              = "FitToWidth"
        q["fullscreen"]            = "true"

        new_q = urlencode(q, doseq=True)
        return urlunparse(parsed._replace(query=new_q))
    except Exception:
        return url

def render_pbi_iframe_pretty(src_url: str, title: str = "Power BI Dashboard") -> None:
    """
    Dashboard embed. Hidden panes + chromeless applied.
    """
    url = _with_hidden_panes(src_url)

    st.markdown(f"### {title}")
    st.caption("Users must be signed into Power BI to see the dashboard.")

    # Centered, horizontally scrollable host so nothing gets clipped.
    st.markdown(
        '<div style="width:100%; overflow-x:auto; display:flex; justify-content:center;">',
        unsafe_allow_html=True,
    )
    # “Fullscreen-like” default sizing
    components.iframe(url, width=1450, height=750, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# ❖ UI Helpers             |
# ==========================
def render_chat_history(messages: List[Dict[str, str]]) -> None:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for m in messages:
        role = m.get("role", "assistant")
        content = m.get("content", "")
        safe = html.escape(str(content))  # escape to avoid XSS
        st.markdown(
            f"""
            <div class="msg-row {role}">
                <div class="msg-bubble">{safe}</div>
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
# ❖ UI: Dashboard Section  |
# ==========================
def dashboard_section() -> None:
    # Expandable LIGHT card for the dashboard
    st.markdown('<div class="pbi-expander">', unsafe_allow_html=True)
    with st.expander("📊 Work Overview Dashboard", expanded=True):
        try:
            render_pbi_iframe_pretty(PBI_EMBED_URL, title="Business Strategy Consulting Work Overview")
        except Exception as e:
            st.error(f"Embed error: {e}")
            st.info("Ensure the URL is correct and your tenant allows iFrame embedding (and you're signed in).")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# ❖ UI: Chat (dark, framed)|
# ==========================
def chat_ui() -> None:
    # ---- Sidebar ----
    with st.sidebar:
        show_logo(center=False)
        st.markdown(
            f'<div style="font-size:0.925rem;color:#e5e7eb;margin-bottom:0.5rem;">Signed in as <b>{st.session_state.get(SK_USER)}</b></div>',
            unsafe_allow_html=True,
        )
        st.button("Log out", type="secondary", on_click=logout)

        st.markdown("---")
        st.caption("Session")
        if st.button("Clear conversation"):
            st.session_state[SK_MSGS] = [{"role": "assistant", "content": "Hi! How can I help today?"}]
            st.rerun()

    # ---- Chat Card (DARK expander) ----
    st.markdown('<div class="chat-card">', unsafe_allow_html=True)
    with st.expander("💬 Chat", expanded=True):
        st.title("RSM Brain")
        st.caption("Your question will appear on the right and the Assistant will answer on the left.")
        st.session_state.setdefault(SK_MSGS, [])
        render_chat_history(st.session_state[SK_MSGS])

        # Inline chat input within the frame
        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_area("Type your message…", height=80, label_visibility="collapsed", key="chat_prompt")
            send = st.form_submit_button("Send")
        if send and prompt and prompt.strip():
            st.session_state[SK_MSGS].append({"role": "user", "content": prompt.strip()})

            recent = st.session_state[SK_MSGS][-MAX_CONTEXT_MESSAGES:]
            context_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

            with st.spinner("Thinking…"):
                try:
                    reply = get_llm_response(prompt.strip(), context_text)
                except Exception as e:
                    reply = f"Sorry, I hit an error calling the model:\n\n```\n{e}\n```"

            st.session_state[SK_MSGS].append({"role": "assistant", "content": reply})

            # Optional: keep only last N messages to control growth
            if len(st.session_state[SK_MSGS]) > MAX_CONTEXT_MESSAGES:
                st.session_state[SK_MSGS] = st.session_state[SK_MSGS][-MAX_CONTEXT_MESSAGES:]

            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# ❖ App Entry              |
# ==========================
def main() -> None:
    inject_css()
    if not st.session_state.get(SK_AUTH):
        login_ui()
    else:
        # Title at the very top
        st.title(APP_TITLE)
        # Dashboard (now expandable, light)
        dashboard_section()
        # Dark, framed, expandable Chat
        chat_ui()

if __name__ == "__main__":
    main()

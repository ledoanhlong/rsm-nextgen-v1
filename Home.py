from __future__ import annotations
import os
import json
import base64
import html
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import time
import re
import bcrypt
import requests
import streamlit as st
import yaml

# Try to use an Image object for the page icon to avoid path-with-space issues
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# =======================
# ❖ Config / Constants  |
# =======================
APP_TITLE = "RSM NextGen – Home"
APP_ICON = ".streamlit/rsm logo with blue background.png"

CREDENTIALS_PATH = Path("credentials.yaml")
LOGO_PATH = Path(".streamlit/rsm logo.png")

# ---- Registered tool pages (label -> path)
TOOLS: Dict[str, str] = {
    "VAT Checker": "pages/VAT_Checker.py",
    "Audit Assistant": "pages/Audit_assistant.py",  
    "Transfer Pricing Tool": "pages/TP_tool.py",
    "Value Chain Agent": "pages/Value_Chain_Agent.py",
    "Intake Form": "pages/Intake_Form.py",
    "Work Overview Dashboard": "pages/Work Overview Dashboard.py",
    "Support": "pages/Support.py",
}

# ---------- LLM Settings ----------
LLM_API_KEY = os.getenv("AZURE_API_KEY", "")
LLM_ENDPOINT = os.getenv("AZURE_API_ENDPOINT", "")

SK_AUTH = "authenticated"
SK_USER = "username"
SK_MSGS = "messages"

MAX_CONTEXT_MESSAGES = 12
SYSTEM_PROMPT_PREFIX = "You are a helpful assistant. Here is chat context:\n"
DISABLE_DEFAULT_FILTER = False

# ---------- Power BI org-embed URL ----------
PBI_EMBED_URL = os.getenv(
    "PBI_EMBED_URL",
    "https://app.powerbi.com/reportEmbed?reportId=90e24eba-e8f2-47a5-905c-f6365f006497&autoAuth=true&ctid=8b279c2c-479d-4b14-8903-efe33db3d877"
)

# =========================
# ❖ Page / Global Styling |
# =========================
# Safer page icon handling (PIL image object if available)
if PIL_AVAILABLE and Path(APP_ICON).exists():
    try:
        _icon_obj = Image.open(APP_ICON)
    except Exception:
        _icon_obj = APP_ICON
else:
    _icon_obj = APP_ICON

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=_icon_obj,
    initial_sidebar_state="expanded",
)

def inject_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --primary-color: #009CDE;
                --background-color: #2a2a2a;
                --app-bg: #2a2a2a;
                --secondary-background-color: #888B8D;
                --text-color:#ffffff;
                --link-color: #3F9C35;
                --border-color: #7c7c7c;
                --code-bg: #121212;
                --base-radius: 0.3rem;
                --button-radius: 9999px;
            }

            html, body, .stApp, [class*="css"] {
                background: var(--background-color) !important;
                color: var(--text-color) !important;
            }

            a { color: var(--link-color) !important; }
            pre, code, kbd, samp { background: var(--code-bg) !important; color: var(--text-color) !important; }

            .stButton>button {
                background: var(--primary-color) !important;
                color: #fff !important;
                border: none !important;
                border-radius: var(--button-radius) !important;
            }
            .stButton>button:hover { filter: brightness(1.05); }

            section[data-testid="stSidebar"] {
                background: #121212 !important;
                border-right: 1px solid #696968 !important;
                color: var(--text-color) !important;
            }

            .sidebar-section-title {
                font-size: 0.95rem;
                letter-spacing: .02em;
                color: #cfd2d6;
                text-transform: uppercase;
                margin: .5rem 0 .25rem 0;
            }

            [data-testid="stSidebarNav"] { display: none !important; }

            [data-testid="chat-message-user"] [data-testid="chatAvatarIcon-user"] {
                display: none !important;
            }
            [data-testid="chatAvatarIcon-assistant"] {
                background: transparent !important;
                border-radius: 50% !important;
                overflow: hidden !important;
                margin-top: 2px !important;
            }

            .chat-margin-container {
                margin-left: 100px !important;
                margin-right: 100px !important;
            }

            @media (max-width: 900px) {
                .chat-margin-container {
                    margin-left: 10px !important;
                    margin-right: 10px !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def hide_sidebar_completely() -> None:
    st.markdown(
        """
        <style>
          section[data-testid="stSidebar"] { display: none !important; }
          div[data-testid="collapsedControl"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def logo_img_base64() -> Optional[str]:
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
# ❖ Prompt Flow helpers    |
# ==========================
def to_pf_chat_history(msgs: List[Dict[str, str]], max_pairs: int = 6) -> List[Dict]:
    pairs = []
    cur_user = None
    for m in msgs:
        role = m.get("role")
        text = (m.get("content") or "").strip()
        if not text:
            continue
        if role == "user":
            cur_user = text
        elif role == "assistant" and cur_user is not None:
            pairs.append({"inputs": {"chat_input": cur_user},
                          "outputs": {"chat_output": text}})
            cur_user = None
    return pairs[-max_pairs:]

def parse_pf_response(data: dict) -> Optional[str]:
    out = (data.get("outputs") or {}).get("chat_output")
    if out:
        return out
    out = data.get("chat_output")
    if out:
        return out
    out = (data.get("outputs") or {}).get("output") or data.get("output")
    if out:
        return out
    try:
        return (data.get("choices", [{}])[0].get("message", {}) or {}).get("content")
    except Exception:
        return None

# ==========================
# ❖ LLM Call               |
# ==========================

DEFAULT_SIGNATURES = [
    "steps to create a compute instance",
    "install the azureml sdk v2",
    "from azure.ai.ml import mlclient",
    "from azure.ai.ml.entities import computeinstance",
    "from azure.identity import defaultazurecredential",
    "ml_client.compute.begin_create_or_update(compute_instance)",
    "standard_ds3_v2",
    "stopping a compute instance",
]

def looks_like_default(text: str) -> bool:
    if DISABLE_DEFAULT_FILTER:
        return False
    t = (text or "").strip().lower()
    if len(t) < 120:
        return False
    hits = sum(sig in t for sig in DEFAULT_SIGNATURES)
    aml_combo = (
        ("compute instance" in t and "azureml sdk" in t) or
        ("compute instance" in t and "ml_client" in t) or
        ("azure.ai.ml" in t and "computeinstance" in t)
    )
    return hits >= 2 or aml_combo

def get_llm_response(prompt: str, context: str) -> str:
    if not LLM_API_KEY or not LLM_ENDPOINT:
        raise RuntimeError("Missing LLM configuration. Set AZURE_API_KEY and AZURE_API_ENDPOINT.")

    endpoint_lower = LLM_ENDPOINT.lower()
    is_aml = ".inference.ml.azure.com" in endpoint_lower
    is_foundry = (".inference.azureai.io" in endpoint_lower) or ("ai.azure.com" in endpoint_lower)

    headers = {"Content-Type": "application/json"}
    if is_aml:
        # AML managed online endpoints use Bearer
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    else:
        # Foundry / AOAI serverless endpoints use api-key
        headers["api-key"] = LLM_API_KEY

    # Build Prompt Flow-style chat history
    history_pf = to_pf_chat_history(st.session_state.get(SK_MSGS, []))

    # If you want to ensure non-empty history to avoid “default”, seed a neutral turn:
    if not history_pf:
        history_pf = [{"inputs": {"chat_input": "Hi"}, "outputs": {"chat_output": "Hello!"}}]

    # Three candidate bodies (order chosen to maximize success):
    payloads = []

    # 1) Foundry/AOAI serverless: {"inputs": {...}}
    payloads.append((
        "foundry.inputs",
        {"inputs": {"chat_input": prompt, "chat_history": history_pf}}
    ))

    # 2) AML managed online endpoint: {"input_data":{"inputs":{...}}}
    payloads.append((
        "aml.input_data.inputs",
        {"input_data": {"inputs": {"chat_input": prompt, "chat_history": history_pf}}}
    ))

    # 3) Raw top-level fallback (some custom runtimes accept this)
    payloads.append((
        "raw.top",
        {"chat_input": prompt, "chat_history": history_pf}
    ))

    last_status = None
    last_text = None
    last_json = None
    last_tag = None

    for tag, body in payloads:
        try:
            resp = requests.post(LLM_ENDPOINT, headers=headers, json=body, timeout=90)
            last_status = resp.status_code
            last_text = resp.text
            last_tag = tag

            if resp.status_code != 200:
                continue

            # Try to parse JSON
            try:
                data = resp.json()
                last_json = data
            except Exception:
                txt = (resp.text or "").strip()
                if txt and not looks_like_default(txt):
                    return txt
                else:
                    continue

            # Extract content from common shapes
            content = (
                (data.get("outputs") or {}).get("chat_output")
                or data.get("chat_output")
                or data.get("output")
            )

            if not content:
                # Some runtimes return { "prediction": "..."} or nested shapes:
                content = data.get("prediction") or data.get("result") or data.get("value")

            if not content:
                # If no content, try stringify (for debugging)
                cand = json.dumps(data, ensure_ascii=False)
                if cand and not looks_like_default(cand):
                    return cand[:4000]
                continue

            if looks_like_default(content):
                # Try next schema; this one likely hit the default branch
                continue

            return content

        except requests.RequestException as e:
            last_text = f"Network error calling LLM: {e}"
            continue

    # If we got here, everything failed or returned the default content.
    debug = f"[{last_tag}] HTTP {last_status}; Body (first 800 chars): {str(last_text)[:800]}"
    raise RuntimeError(
        "The endpoint responded but appears to return the flow's default sample output "
        "(schema mismatch). Try the other schema in the code, or copy the exact 'Request body' "
        "from the endpoint's Test tab and match it. \n\n" + debug
    )
# ==========================
# ❖ UI Helpers             |
# ==========================
def _tidy_llm_text(text: str) -> str:
    """Normalize spacing, bullets, and a few headings (still Markdown)."""
    t = (text or "").strip().replace("\r\n", "\n")
    # Collapse 3+ newlines to 2
    t = re.sub(r"\n{3,}", "\n\n", t)
    # Strip trailing spaces per line
    t = "\n".join(line.rstrip() for line in t.split("\n"))
    # Convert common **TL;DR:** into a markdown heading
    t = re.sub(r"^\s*\*\*TL;DR:\*\*\s*$", "### TL;DR", t, flags=re.IGNORECASE | re.MULTILINE)
    # Normalize bullets: •, –, * → -
    t = re.sub(r"^\s*[•–*]\s+", "- ", t, flags=re.MULTILINE)
    return t

def _md_to_html_basic(md: str) -> str:
    """
    Lightweight Markdown -> HTML (no external deps).
    Supports:
      - headings (#, ##, ###)
      - **bold**, *italic*
      - horizontal rules (---)
      - unordered lists (- item)
      - ordered lists (1. item)
      - paragraphs / blank lines
    """
    md = _tidy_llm_text(md)
    lines = md.split("\n")
    out = []
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def fmt_inline(s: str) -> str:
        s = html.escape(s)
        # bold (**text**)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        # italic (*text*)
        s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
        # inline code `code`
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        # links [text](url) – URL escaped but left as href
        s = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', s)
        return s

    for raw in lines:
        ln = raw.rstrip()

        # Horizontal rule
        if re.match(r"^\s*---+\s*$", ln):
            close_lists()
            out.append("<hr/>")
            continue

        # Headings
        m = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", ln)
        if m:
            close_lists()
            level = len(m.group(1))
            out.append(f"<h{level}>{fmt_inline(m.group(2))}</h{level}>")
            continue

        # Ordered list item: "1. text"
        m = re.match(r"^\s*\d+\.\s+(.+)$", ln)
        if m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{fmt_inline(m.group(1))}</li>")
            continue

        # Unordered list item: "- text"
        m = re.match(r"^\s*-\s+(.+)$", ln)
        if m:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{fmt_inline(m.group(1))}</li>")
            continue

        # Blank line => paragraph break
        if not ln.strip():
            close_lists()
            out.append("")  # preserve spacing
            continue

        # Paragraph text
        close_lists()
        out.append(f"<p>{fmt_inline(ln)}</p>")

    close_lists()
    return "\n".join(out)

def format_llm_reply_to_html(raw_text: str) -> str:
    """Public helper: convert LLM markdown-ish text to safe, readable HTML."""
    return _md_to_html_basic(raw_text)

def render_chat_history(messages: List[Dict[str, str]]) -> None:
    for m in messages:
        role = m.get("role", "assistant")
        content = (m.get("content", "") or "").strip()
        chat_role = "user" if role == "user" else "assistant"

        # Assistant: format to HTML (headers, lists, etc). User: plain, escaped text.
        if chat_role == "assistant":
            inner_html = format_llm_reply_to_html(content)
        else:
            inner_html = html.escape(content).replace("\n", "<br>")

        with st.chat_message(chat_role):
            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:flex-start;
                    width:100%;
                ">
                  <div style="
                      /*background:#2a2a2a;*/
                      color:#fff;
                      border-radius:0;
                      padding:0;
                      box-shadow:none;
                      max-width:100%;
                      line-height:1.5;
                      word-wrap:break-word;
                      white-space:normal;
                  ">{inner_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==========================
# ❖ UI: Login              |
# ==========================
def login_ui() -> None:
    hide_sidebar_completely()
    show_logo(center=True)

    st.session_state.setdefault("login_fail_count", 0)
    st.session_state.setdefault("login_lock_until", 0)

    now = time.time()
    if st.session_state["login_lock_until"] > now:
        wait = int(st.session_state["login_lock_until"] - now)
        st.error(f"Too many failed attempts. Try again in {wait}s.")
        return

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background-color: var(--app-bg); border-radius: 10px; padding: 1.25rem; text-align: center; margin-bottom: 1.5rem;">
            <h2 class="login-title" style="margin: 0 0 0.5rem 0;">Sign in</h2>
            <p class="brand-muted" style="margin: 0;">Welcome back — please authenticate to continue.</p>
        </div>
        """,
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
      # bcrypt hash of your password (use a utility to generate)
      password: "$2b$12$examplehashreplacewithreal"
""",
                language="yaml",
            )

    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in")
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not username or not password:
            st.warning("Please enter both username and password.")
        elif verify_user(users, username, password):
            st.session_state[SK_AUTH] = True
            st.session_state[SK_USER] = username
            st.session_state.setdefault(SK_MSGS, [{"role": "assistant", "content": "Hi! How can I help today?"}])
            st.session_state["login_fail_count"] = 0
            st.success("Login successful. Loading chat…")
            st.rerun()
        else:
            st.session_state["login_fail_count"] += 1
            if st.session_state["login_fail_count"] >= 5:
                st.session_state["login_lock_until"] = time.time() + 300  # 5 minutes
            st.error("Invalid username or password.")

# ==========================
# ❖ UI: Chat               |
# ==========================
def chat_ui() -> None:
    # ---- SIDEBAR
    with st.sidebar:
        show_logo(center=True)

        # ========== SECTION 1: Navigation ==========
        st.markdown("---")

        # Flat page links (prefer page_link; fallback to buttons)
        try:
            st.page_link("Home.py", label="Home", icon="🏠")
            st.page_link("pages/Application.py", label="Applications", icon="🧰")
            st.page_link("pages/Support.py", label="Support", icon="🛠️")
        except Exception:
            st.button("Home", use_container_width=True)
            if st.button("Applications", use_container_width=True):
                st.switch_page("pages/Application.py")

        st.markdown("#### Search tools")
        selected_tool = st.selectbox(
            "Search or jump to a tool",
            options=list(TOOLS.keys()),
            index=None,
            placeholder="Search tools…",
            label_visibility="collapsed",
            key="__tool_search_sidebar__",
        )
        if selected_tool:
            st.switch_page(TOOLS[selected_tool])

        st.markdown("---")

        # ========== SECTION 2: Session ==========
        st.markdown(
            f'<div style="font-size:0.9rem;color:#e5e7eb;margin-bottom:0.5rem;">Signed in as <b>{st.session_state.get(SK_USER, "user")}</b></div>',
            unsafe_allow_html=True,
        )
        if st.button("Log out", type="secondary", use_container_width=True):
            logout()

        st.markdown("---")

        # ========== SECTION 3: Conversation ==========
        if st.button("Clear conversation", use_container_width=True):
            st.session_state[SK_MSGS] = [{"role": "assistant", "content": "Hi! How can I help today?"}]
            st.rerun()

    # ---- MAIN CONTENT (single instance)
    st.title(APP_TITLE)
    st.markdown("---")
    st.header("🧠 RSM Brain")

    # Add a container div with increased left/right margin
    st.markdown(
        """
        <div class="chat-margin-container">
        """,
        unsafe_allow_html=True,
    )

    st.session_state.setdefault(SK_MSGS, [])
    render_chat_history(st.session_state[SK_MSGS])

    prompt = st.chat_input(
        "Type your message and press enter",
        key="chat_prompt",
    )

    if prompt and prompt.strip():
        st.session_state[SK_MSGS].append({"role": "user", "content": prompt.strip()})
        recent = st.session_state[SK_MSGS][-MAX_CONTEXT_MESSAGES:]
        context_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
        with st.spinner("Thinking…"):
            try:
                reply = get_llm_response(prompt.strip(), context_text)
            except Exception as e:
                reply = f"Sorry, I hit an error calling the model:\n\n```\n{e}\n```"
        st.session_state[SK_MSGS].append({"role": "assistant", "content": reply})
        if len(st.session_state[SK_MSGS]) > MAX_CONTEXT_MESSAGES:
            st.session_state[SK_MSGS] = st.session_state[SK_MSGS][-MAX_CONTEXT_MESSAGES:]
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)  # Close chat-margin-container

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
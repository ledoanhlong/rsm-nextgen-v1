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
APP_ICON = ".streamlit/rsm logo.png"
APP_LAYOUT = "wide"

CREDENTIALS_PATH = Path("credentials.yaml")
LOGO_PATH = Path(".streamlit/rsm logo.png")

# ---- Registered tool pages (label -> path)
TOOLS: Dict[str, str] = {
    "VAT Checker": "pages/VAT_Checker.py",
    "Audit Assistant": "pages/Audit_assistant.py",  # <-- this page
    "Transfer Pricing Tool": "pages/TP_tool.py",
    "Value Chain Agent": "pages/Value_Chain_Agent.py",
    "Intake Form": "pages/Intake_Form.py",
    "Work Overview Dashboard": "pages/Work Overview Dashboard.py",
}

# ---------- LLM Settings ----------
LLM_API_KEY = os.getenv("AZURE_API_KEY", "")
LLM_ENDPOINT = os.getenv("AZURE_API_ENDPOINT", "")

SK_AUTH = "authenticated"
SK_USER = "username"
SK_MSGS = "messages"

MAX_CONTEXT_MESSAGES = 12
SYSTEM_PROMPT_PREFIX = "You are a helpful assistant. Here is chat context:\n"

DEFAULT_SIGNATURES = [
    "Steps to Create a Compute Instance Using AzureML SDK v2",
    "TL;DR: To create an Azure Machine Learning compute instance",
    "Use the AzureML SDK v2 to define and create a compute instance",
]
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
    layout=APP_LAYOUT,
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
                /*font-family: 'Prelo', -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif !important;*/
            }

            a { color: var(--link-color) !important; }
            pre, code, kbd, samp { background: var(--code-bg) !important; color: var(--text-color) !important; }
            .block-container { max-width: 100%; padding-top: 1.25rem; }

            textarea, input, select, .stTextInput input, .stTextArea textarea {
                background-color: var(--code-bg) !important;
                color: var(--text-color) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: var(--base-radius) !important;
            }

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

            /* Subtle section titles in sidebar */
            .sidebar-section-title {
                font-size: 0.95rem;
                letter-spacing: .02em;
                color: #cfd2d6;
                text-transform: uppercase;
                margin: .5rem 0 .25rem 0;
            }

            /* Hide default multipage nav */
            [data-testid="stSidebarNav"] { display: none !important; }

            /* Chat avatars */
            [data-testid="chat-message-user"] [data-testid="chatAvatarIcon-user"] {
                display: none !important;
            }
            [data-testid="chatAvatarIcon-assistant"] {
                background: transparent !important;
                border-radius: 50% !important;
                overflow: hidden !important;
                margin-top: 2px !important;
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

def looks_like_default(text: str) -> bool:
    if DISABLE_DEFAULT_FILTER:
        return False
    t = (text or "").strip()
    for sig in DEFAULT_SIGNATURES:
        if sig.lower() in t.lower():
            return True
    return False

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
def get_llm_response(prompt: str, context: str) -> str:
    if not LLM_API_KEY or not LLM_ENDPOINT:
        raise RuntimeError("Missing LLM configuration. Set AZURE_API_KEY and AZURE_API_ENDPOINT.")

    endpoint_lower = LLM_ENDPOINT.lower()
    is_aml = ".inference.ml.azure.com" in endpoint_lower
    is_ai_studio = ".inference.azureai.io" in endpoint_lower or "ai.azure.com" in endpoint_lower

    headers = {"Content-Type": "application/json"}
    if is_aml:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    else:
        headers["api-key"] = LLM_API_KEY

    history_pf = to_pf_chat_history(st.session_state.get(SK_MSGS, []))

    inputs_block = {"chat_input": prompt, "chat_history": history_pf}
    messages_ooai = [
        {"role": "system", "content": SYSTEM_PROMPT_PREFIX + context},
        {"role": "user", "content": prompt},
    ]

    payload_attempts: List[Tuple[str, dict]] = []
    if is_aml:
        payload_attempts.extend([
            ("aml.input_data.inputs",         {"input_data": {"inputs": inputs_block}}),
            ("aml.input_data.flat",           {"input_data": inputs_block}),
            ("aml.flat",                      inputs_block),
            ("aml.openai_messages_in_input",  {"input_data": {"inputs": {"messages": messages_ooai}}}),
        ])
    else:
        payload_attempts.extend([
            ("ai.inputs",                     {"inputs": inputs_block}),
            ("ai.inputs.messages",            {"inputs": {"messages": messages_ooai}}),
            ("ai.flat",                       inputs_block),
        ])

    last_status = None
    last_text = None

    for _, payload in payload_attempts:
        try:
            resp = requests.post(LLM_ENDPOINT, headers=headers, json=payload, timeout=60)
            last_status = resp.status_code
            last_text = resp.text
            if resp.status_code != 200:
                continue

            try:
                data = resp.json()
            except Exception:
                if last_text and not looks_like_default(last_text):
                    return last_text
                else:
                    continue

            content = parse_pf_response(data)
            if not content:
                candidate = json.dumps(data, ensure_ascii=False)
                if candidate and not looks_like_default(candidate):
                    return candidate
                continue

            if looks_like_default(content):
                continue

            return content

        except requests.RequestException as e:
            last_text = f"Network error calling LLM: {e}"
            continue

    details = f"Last status: {last_status}; Last body: {last_text}"
    raise RuntimeError(
        "Endpoint accepted the call but appears to ignore inputs (still returns the flow's default). "
        "This usually means the managed online endpoint expects a different request schema. "
        "Tried multiple payload shapes without success.\n\n" + details
    )

# ==========================
# ❖ Power BI               |
# ==========================
def _with_hidden_panes(url: str) -> str:
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
    url = _with_hidden_panes(src_url)
    st.markdown(f"### {title}")
    st.caption("Users must be signed into Power BI to see the dashboard.")
    st.markdown(
        f"""
        <div style="position:relative;padding-top:56.25%;width:100%;max-width:1600px;margin:0 auto;">
          <iframe src="{html.escape(url)}" frameborder="0" allowfullscreen
                  style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>
        </div>
        """,
        unsafe_allow_html=True,
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

        # Colors
        bubble_color = "#009CDE" if chat_role == "assistant" else "#3F9C35"

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
                      background:{bubble_color};
                      color:#fff;
                      border-radius:16px;
                      padding:0.9rem 1rem;
                      box-shadow:0 12px 28px rgba(0,0,0,0.35);
                      max-width:min(80ch, 78%);
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

    with st.expander("💬 Chat", expanded=True):
        st.header("🧠 RSM Brain")
        st.session_state.setdefault(SK_MSGS, [])
        render_chat_history(st.session_state[SK_MSGS])

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
            if len(st.session_state[SK_MSGS]) > MAX_CONTEXT_MESSAGES:
                st.session_state[SK_MSGS] = st.session_state[SK_MSGS][-MAX_CONTEXT_MESSAGES:]
            st.rerun()

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
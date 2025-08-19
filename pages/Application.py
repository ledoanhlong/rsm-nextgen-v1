# pages/Application.py
from __future__ import annotations
import base64
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

# ====== Config (match Home) ======
APP_TITLE = "Applications"
APP_LAYOUT = "wide"
LOGO_PATH = Path(".streamlit/rsm logo.png")

# Session keys (match Home.py)
SK_USER = "username"
SK_MSGS = "messages"

# ---- Registered tool pages (label -> path) — keep in sync with Home.py
TOOLS: Dict[str, str] = {
    "VAT Checker": "pages/VAT_Checker.py",
    "Audit Assistant": "pages/Audit_assistant.py",
    "Transfer Pricing Tool": "pages/TP_tool.py",
    "Value Chain Agent": "pages/Value_Chain_Agent.py",
    "Intake Form": "pages/Intake_Form.py",
    "Work Overview Dashboard": "pages/Work_Overview_Dashboard.py",
}

# ====== Page config ======
st.set_page_config(page_title=APP_TITLE, layout=APP_LAYOUT, initial_sidebar_state="expanded")

# ====== Styling (same look as Home) ======
def inject_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --primary-color: #009CDE;
                --background-color: #2a2a2a;
                --app-bg: #2a2a2a;
                --secondary-background-color: #888B8D;
                --text-color: #ffffff;
                --link-color: #3F9C35;
                --border-color: #7c7c7c;
                --code-bg: #121212;
                --base-radius: 0.3rem;
                --button-radius: 9999px;
            }

            html, body, .stApp, [class*="css"] {
                background: var(--background-color) !important;
                color: var(--text-color) !important;
                font-family: 'Prelo', -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif !important;
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
        </style>
        """,
        unsafe_allow_html=True,
    )

def logo_img_base64() -> Optional[str]:
    if LOGO_PATH.exists():
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

inject_css()

# ====== Sidebar (same structure as Home) ======
with st.sidebar:
    show_logo(center=True)

    # --- Section 1: Navigation
    st.markdown("---")
    # Flat page links
    try:
        st.page_link("Home.py", label="Home", icon="🏠")
        st.page_link("pages/Application.py", label="Applications", icon="🧰")
    except Exception:
        # Fallback (older Streamlit)
        if st.button("← Home", use_container_width=True):
            st.switch_page("Home.py")

    # Search tools
    st.markdown("#### Search tools")
    selected_tool = st.selectbox(
        "Search or jump to a tool",
        options=list(TOOLS.keys()),
        index=None,
        placeholder="Search tools…",
        label_visibility="collapsed",
        key="__tool_search_sidebar_apps__",
    )
    if selected_tool:
        st.switch_page(TOOLS[selected_tool])

    st.markdown("---")

    # --- Section 2: Session
    st.markdown(
        f'<div style="font-size:0.9rem;color:#e5e7eb;margin-bottom:0.5rem;">Signed in as <b>{st.session_state.get(SK_USER, "user")}</b></div>',
        unsafe_allow_html=True,
    )
    # Logout (calls back into Home.py's logout if you expose it; otherwise reload Home)
    # If you want real logout, create a small helper in a shared module. Here we soft-reset.
    if st.button("Log out", type="secondary", use_container_width=True):
        for k in ("authenticated", SK_USER, SK_MSGS):
            if k in st.session_state:
                del st.session_state[k]
        st.switch_page("Home.py")

    st.markdown("---")

# ====== Main content (Applications) ======
st.title(APP_TITLE)

# Back to Home button (page body)
col_back, col_space = st.columns([1, 5])
with col_back:
    try:
        st.page_link("Home.py", label="← Back to Home")
    except Exception:
        if st.button("← Back to Home"):
            st.switch_page("Home.py")

# Deep-link support: ?goto=Tool%20Name
qp = st.query_params
target = qp.get("goto")
if isinstance(target, list):
    target = target[0]
if target and target in TOOLS:
    st.switch_page(TOOLS[target])

# Cards grid
st.markdown("### All tools")
cols = st.columns(3, gap="large")
for i, (label, page_path) in enumerate(TOOLS.items()):
    with cols[i % 3]:
        with st.container(border=True):
            st.subheader(label)
            st.caption("Open this tool.")
            if st.button(f"Open {label}", key=f"open_{label}"):
                st.switch_page(page_path)
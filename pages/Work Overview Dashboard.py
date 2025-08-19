# pages/Work_Overview_Dashboard.py
from __future__ import annotations
import os
import html
import base64
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import streamlit as st

# ====== Config ======
PAGE_TITLE = "Work Overview Dashboard"
APP_LAYOUT = "wide"
LOGO_PATH = Path(".streamlit/rsm logo.png")

# Session keys (consistent with Home/Application)
SK_USER = "username"
SK_MSGS = "messages"

# ---- Registered tool pages (keep in sync with Home/Application)
TOOLS: Dict[str, str] = {
    "VAT Checker": "pages/VAT_Checker.py",
    "Audit Assistant": "pages/Audit_assistant.py",  # <-- this page
    "Transfer Pricing Tool": "pages/TP_tool.py",
    "Value Chain Agent": "pages/Value_Chain_Agent.py",
    "Intake Form": "pages/Intake_Form.py",
    "Work Overview Dashboard": "pages/Work Overview Dashboard.py",
}

# ====== Page config ======
st.set_page_config(page_title=PAGE_TITLE, layout=APP_LAYOUT, initial_sidebar_state="expanded")

# ====== Styling (same look as Home/Application) ======
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

def _logo_b64() -> Optional[str]:
    if LOGO_PATH.exists():
        try:
            return base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
        except Exception:
            return None
    return None

def show_logo(center: bool = True) -> None:
    b64 = _logo_b64()
    if b64:
        align = "margin-left:auto;margin-right:auto;" if center else ""
        st.markdown(
            f'<img class="brand-logo" src="data:image/png;base64,{b64}" style="{align}" />',
            unsafe_allow_html=True,
        )

inject_css()

# ====== Sidebar (Navigation / Session / Conversation) ======
with st.sidebar:
    show_logo(center=True)

    # Section 1: Navigation
    st.markdown("---")
    try:
        st.page_link("Home.py", label="Home", icon="🏠")
        st.page_link("pages/Application.py", label="Applications", icon="🧰")
    except Exception:
        # Fallback for older Streamlit
        if st.button("← Home", use_container_width=True):
            st.switch_page("Home.py")
        if st.button("Applications", use_container_width=True):
            st.switch_page("pages/Application.py")

    st.markdown("#### Search tools")
    selected_tool = st.selectbox(
        "Search or jump to a tool",
        options=list(TOOLS.keys()),
        index=None,
        placeholder="Search tools…",
        label_visibility="collapsed",
        key="__tool_search_sidebar_workdash__",
    )
    if selected_tool:
        st.switch_page(TOOLS[selected_tool])

    st.markdown("---")

    # Section 2: Session
    st.markdown(
        f'<div style="font-size:0.9rem;color:#e5e7eb;margin-bottom:0.5rem;">Signed in as <b>{st.session_state.get(SK_USER, "user")}</b></div>',
        unsafe_allow_html=True,
    )
    # Soft logout (same approach as Applications page)
    if st.button("Log out", type="secondary", use_container_width=True):
        for k in ("authenticated", SK_USER, SK_MSGS):
            if k in st.session_state:
                del st.session_state[k]
        st.switch_page("Home.py")

# ====== Helpers (Power BI) ======
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

# ====== Env var for PBI (same as Home) ======
PBI_EMBED_URL = os.getenv(
    "PBI_EMBED_URL",
    "https://app.powerbi.com/reportEmbed?reportId=90e24eba-e8f2-47a5-905c-f6365f006497&autoAuth=true&ctid=8b279c2c-479d-4b14-8903-efe33db3d877"
)

# ====== Main content ======
st.title("📊 Work Overview Dashboard")

# Back links
cols = st.columns([1, 1, 6])
with cols[0]:
    try:
        st.page_link("Home.py", label="← Back to Home")
    except Exception:
        if st.button("← Back to Home"):
            st.switch_page("Home.py")
with cols[1]:
    try:
        st.page_link("pages/Application.py", label="← Applications")
    except Exception:
        if st.button("← Applications"):
            st.switch_page("pages/Application.py")
# PBI iframe
render_pbi_iframe_pretty(PBI_EMBED_URL, title="")

# pages/Support.py
from __future__ import annotations
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

# ========= Config (match Home/Application) =========
PAGE_TITLE = "Support & Feedback"
PAGE_ICON  = "🛟"
LOGO_PATH  = Path(".streamlit/rsm logo.png")

SUPPORT_EMAIL = "lle@rsmnl.nl"   # <-- change me

# Session keys
SK_AUTH = "authenticated"
SK_USER = "username"
SK_MSGS = "messages"

# Registered tools (keep in sync with your app)
TOOLS: Dict[str, str] = {
    "VAT Checker": "pages/VAT_Checker.py",
    "Audit Assistant": "pages/Audit_assistant.py",  
    "Transfer Pricing Tool": "pages/TP_tool.py",
    "Value Chain Agent": "pages/Value_Chain_Agent.py",
    "Intake Form": "pages/Intake_Form.py",
    "Work Overview Dashboard": "pages/Work Overview Dashboard.py",
    "Support": "pages/Support.py",
}
# ========= Page config =========
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, initial_sidebar_state="expanded")

# ========= Styling =========
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
        st.markdown(f'<img class="brand-logo" src="data:image/png;base64,{b64}" style="{align}" />', unsafe_allow_html=True)

inject_css()

# ========= Sidebar =========
with st.sidebar:
    show_logo(center=True)
    st.markdown("---")
    try:
        st.page_link("Home.py", label="Home", icon="🏠")
        st.page_link("pages/Application.py", label="Applications", icon="🧰")
        st.page_link("pages/Support.py", label="Support", icon="🛟")
    except Exception:
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
        key="__tool_search_sidebar_support__",
    )
    if selected_tool:
        st.switch_page(TOOLS[selected_tool])

    st.markdown("---")
    st.markdown(
        f'<div style="font-size:0.9rem;color:#e5e7eb;margin-bottom:0.5rem;">Signed in as <b>{st.session_state.get(SK_USER, "user")}</b></div>',
        unsafe_allow_html=True,
    )
    if st.button("Log out", type="secondary", use_container_width=True):
        for k in (SK_AUTH, SK_USER, SK_MSGS):
            if k in st.session_state:
                del st.session_state[k]
        st.switch_page("Home.py")


# ========= Auth gate =========
if not st.session_state.get(SK_AUTH):
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.error("Please log in to send feedback.")
    st.stop()

# ========= Main content =========
st.title(f"{PAGE_ICON} {PAGE_TITLE}")

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

st.markdown("---")

# ========= Feedback (direct Outlook Web) =========
st.subheader("Send feedback about a tool")

tool = st.selectbox("Which tool?", options=list(TOOLS.keys()), index=None, placeholder="Select a tool…")
category = st.selectbox("Category", ["Bug", "Feature request", "Usability", "Performance", "Other"])
severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
description = st.text_area("Describe the issue or suggestion *", height=140, placeholder="What happened? What should change?")
steps = st.text_area("Steps to reproduce (optional)", height=100, placeholder="1) … 2) … 3) …")
email = st.text_input("Your contact email (optional)")

def build_outlook_web_link(to_addr: str, subject: str, body: str) -> str:
    return (
        "https://outlook.office.com/mail/deeplink/compose"
        f"?to={quote(to_addr)}&subject={quote(subject)}&body={quote(body)}"
    )

if st.button("Open in Outlook Web", use_container_width=True):
    if not tool or not description.strip():
        st.warning("Please fill at least Tool and Description.")
    else:
        user = st.session_state.get(SK_USER, "anonymous")
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        subject = f"[Feedback] {tool} – {category} ({severity})"
        body_lines = [
            f"Tool: {tool}",
            f"Category: {category}",
            f"Severity: {severity}",
            f"Rating: {rating}/5",
            f"Submitted by: {user}",
            f"Timestamp (UTC): {ts}",
            "",
            "Description:",
            description.strip(),
            "",
            "Steps to reproduce:",
            (steps.strip() or "(not provided)"),
            "",
            f"Contact email: {email or '(not provided)'}",
            "",
            "Attachments:",
            "- Please add any screenshots/files to this email before sending.",
        ]
        body = "\n".join(body_lines)

        outlook_url = build_outlook_web_link(SUPPORT_EMAIL, subject, body)
        st.markdown(f"[👉 Open in Outlook Web]({outlook_url})", unsafe_allow_html=True)
        st.expander("Preview email body").code(body)

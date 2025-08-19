# pages/Work_Overview_Dashboard.py
from __future__ import annotations
import os
import html
import streamlit as st
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

# ---------- Page config (safe if this page loads first) ----------
st.set_page_config(page_title="Work Overview Dashboard", layout="wide")

# ---------- Read the same env var as app.py ----------
PBI_EMBED_URL = os.getenv(
    "PBI_EMBED_URL",
    "https://app.powerbi.com/reportEmbed?reportId=90e24eba-e8f2-47a5-905c-f6365f006497&autoAuth=true&ctid=8b279c2c-479d-4b14-8903-efe33db3d877"
)

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

# ---------- Page body ----------
st.title("📊 Work Overview Dashboard")
render_pbi_iframe_pretty(PBI_EMBED_URL, title="Business Strategy Consulting Work Overview")

# pages/5_RAG_Audit_Assistant.py
import streamlit as st
from widgets.Value_Chain_Analysis.streamlit2 import render

st.set_page_config(page_title="Value Chain Analysis Agent", page_icon="🔺", layout="wide")

# (Optional auth)
if not st.session_state.get("authenticated"):
    st.error("Please log in to access this page.")
    st.stop()

# Render (CSS is injected inside render() each run)
render(
    form_url="https://rsmnl-trial.app.n8n.cloud/form/0afc21e5-8997-481d-aea3-669658fcd72c",
    title="🔺 Value Chain Analysis Agent"
)

# pages/4_RAG_Audit_Assistant.py
import streamlit as st
from widgets.audit_risk_assessment.streamlit2 import render

# Optional: keep behind login like your other pages
if not st.session_state.get("authenticated"):
    st.error("Please log in to access this page.")
    st.stop()

st.set_page_config(page_title="RAG Audit Assistant", page_icon="🔍", layout="wide")
st.title("🔍 RAG Audit Assistant")

render()

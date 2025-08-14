# pages/3_TP_Template_Filler.py
import streamlit as st
from widgets.Tp_tool_clean.streamlit_app import render

# Optional: keep behind login, consistent with your other pages
if not st.session_state.get("authenticated"):
    st.error("Please log in to access this page.")
    st.stop()

st.set_page_config(page_title="TP Template Filler", page_icon="📄", layout="wide")
st.title("📄 TP Template Filler")

render()

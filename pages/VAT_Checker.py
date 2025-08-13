# pages/2_VAT_Checker.py
import streamlit as st
from widgets.vat_checker.app import render as render_vat_checker  # expects your widget's render()

# (Optional) keep it behind login, since your main app uses auth
if not st.session_state.get("authenticated"):
    st.error("Please log in to access the VAT Checker.")
    st.stop()

st.set_page_config(page_title="VAT Checker", page_icon="🧾", layout="wide")
st.title("🧾 VAT Checker")
render_vat_checker()

import streamlit as st
from widgets.Diamond_Form_embbed.Intake_form import render as render_intake_form  

# (Optional) keep it behind login, since your main app uses auth
if not st.session_state.get("authenticated"):
    st.error("Please log in to access the Intake Form.")
    st.stop()

st.set_page_config(page_title="Intake Form", page_icon="🧾", layout="wide")
st.title("🧾 Intake Form")
render_intake_form()

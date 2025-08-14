import streamlit as st
import streamlit.components.v1 as components

# Title of the Streamlit page
st.title("Embedded Chat Interface")

# Embed the webpage as an iframe
iframe_url = "http://localhost:5678/webhook/a0d18321-dd2f-4f5f-8273-121b5831d2aa/chat"

# Embed the iframe within the Streamlit app
components.iframe(iframe_url, width=800, height=600)


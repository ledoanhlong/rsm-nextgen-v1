# widgets/Diamond_Form_embbed/Intake_form.py

import streamlit as st

def render():
    st.set_page_config(page_title="RSM VAT AID ", layout="wide")
    st.title("ICS Idea Intake Form")

    # --- Form URL (provided)
    FORM_URL = "https://rsmnl.diamondforms.net/Internal_Idea_Input"

    # --- Embed using iframeResizer script injection with full width and height
    embed_html = f"""
    <script type="text/javascript" src="https://rsmnl.diamondforms.net/Content/Scripts/iframeResizer.min.js"></script>
    <iframe id="diamondForm" src="{FORM_URL}" style="border:0; width:100%; height:100vh;"></iframe>
    <script type="text/javascript">
        iFrameResize({{ heightCalculationMethod: 'taggedElement', checkOrigin: false }}, '#diamondForm');
    </script>
    """

    st.components.v1.html(embed_html, width=1500, height=1000, scrolling=False)

    # --- Troubleshooting fallback
    st.markdown("---")
    st.link_button("Open form in new tab", FORM_URL, use_container_width=True)

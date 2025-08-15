import streamlit as st

st.set_page_config(page_title="RSM VAT AID ", layout="wide")

st.title("RSM VAT aid for services in and from abroad")

# --- Form URL (provided)
FORM_URL = (
    "https://rsmnl.diamondforms.net/Diamant/Form?args="
    "rwfouRzQR-4q6DXqI3iqWmS2UicOa1P_ZoLWa8wWZXlTUqmO4DRgNbtEuomTtvfG3Lz6cAD1I_ALyTRhrAgXhq3uMRewqtClAHukNPBASA8AuRadR_Ducpi53xAQGNhYCfeTzSFwWq8bkFkX98yUi0mBtv3iVHyAHYR_BSdHJ_E32tPH6fAZq4eTi4nm9yLVK45Yep9acmz3OBA7sNhtHcjwB_JKtRprFgtn-m3RzJvv59naQM5V2h5siFK5BP4jng9epSBdDPuUz3h2H9KcQvpn8Gd0VQ2nvxc6ljlSLqkUsniODorEeqSqdoV92L6CxOqmbHkNN8TD3H69_84Ucqk7_k0nX7TT4l77Ez9sNwXUUkztYMJQ8JwNcaks_6F1Vfp87tERg3ZWdijFbEsg0daynnqIpOj6cl9YtPfSdZs%3D&lang=en-US"
)

# --- Embed using iframeResizer script injection with full width and height
embed_html = f"""
<script type=\"text/javascript\" src=\"https://rsmnl.diamondforms.net/Content/Scripts/iframeResizer.min.js\"></script>
<iframe id=\"diamondForm\" src=\"{FORM_URL}\" style=\"border:0; width:100%; height:100vh;\"></iframe>
<script type=\"text/javascript\">
    iFrameResize({{ heightCalculationMethod: 'taggedElement', checkOrigin: false }}, '#diamondForm');
</script>
"""

st.components.v1.html(embed_html, width=1500, height=1000, scrolling=False)

# --- Troubleshooting fallback
st.markdown("---")
st.link_button("Open form in new tab", FORM_URL, use_container_width=True)

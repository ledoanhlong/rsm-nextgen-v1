# widget/tp_template_filler/app.py  (path can be whatever you use; avoid hyphens in folder names)
import streamlit as st
from widgets.Tp_tool_clean.processor import configure, process_and_fill
import pandas as pd

# --- one-time backend init (safe across reruns) ---
@st.cache_resource(show_spinner=False)
def _init_backend(api_key: str, endpoint: str) -> bool:
    configure(api_key, endpoint)
    return True

def render() -> None:
    # Configure backend with secrets once
    _init_backend(
        st.secrets["AZURE_API_KEY"],
        st.secrets["AZURE_API_ENDPOINT"]
    )

    # File uploader
    uploaded = st.file_uploader(
        "Upload OECD text, transcript.docx, analysis.pdf, variables.xlsx, template.docx:",
        type=["txt", "docx", "pdf", "xlsx"],
        accept_multiple_files=True
    )

    # Only build file_map when files are provided
    file_map = {}
    if uploaded and len(uploaded) >= 5:
        for f in uploaded:
            n = f.name.lower()
            if n.endswith('.txt'):
                file_map['guidelines'] = f
            elif n.endswith('.docx') and 'template' not in n:
                file_map['transcript'] = f
            elif n.endswith('.pdf'):
                file_map['pdf'] = f
            elif n.endswith('.xlsx'):
                file_map['excel'] = f
            elif 'template' in n and n.endswith('.docx'):
                file_map['template'] = f

    # Show missing file warnings
    required = {'guidelines', 'transcript', 'pdf', 'excel', 'template'}
    missing = required - set(file_map.keys())
    if missing:
        if uploaded and len(uploaded) >= 5:
            st.warning(f"Missing files: {', '.join(sorted(missing))}. Please upload all five.")
        else:
            st.info("Awaiting 5 files...")

    # Always show the button when at least 5 uploads are present
    if uploaded and len(uploaded) >= 5:
        if st.button("Generate filled.docx"):
            if missing:
                st.error("Cannot generate: please upload all required files listed above.")
            else:
                with st.spinner("Processing..."):
                    try:
                        path = process_and_fill(file_map)
                        st.success("Done—download below:")
                        st.download_button(
                            "Download filled.docx",
                            open(path, 'rb'),
                            file_name="filled.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")

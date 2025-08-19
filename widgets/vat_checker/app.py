# widget/vat_checker/app.py
import io
from datetime import datetime
from typing import List
import pandas as pd
import pytz
import streamlit as st

from widgets.vat_checker.vat_utils import check_vat  # your existing helper



cet = pytz.timezone("Europe/Paris")  # CET/CEST timestamps

def render() -> None:
    """Render the VAT checker as a self-contained widget (no login, no credits)."""
    # Input: upload OR text area
    uploaded = st.file_uploader("Upload a CSV/XLSX with VAT codes", type=["csv", "xlsx"])
    vat_list: List[str] = []

    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Failed to read file: {e}")
            return

        st.write("Columns:", list(df.columns))
        col = st.text_input("Enter column name or **index** for VAT codes")
        if col:
            try:
                if col.isdigit():
                    vat_list = df.iloc[:, int(col)].dropna().astype(str).tolist()
                else:
                    vat_list = df[col].dropna().astype(str).tolist()
            except Exception as e:
                st.error(f"Invalid column: {e}")
                return
    else:
        text_input = st.text_area("Or enter VAT numbers (one per line):", height=150)
        vat_list = [v.strip() for v in text_input.splitlines() if v.strip()]

    if st.button("Check VAT numbers"):
        if not vat_list:
            st.warning("No VAT numbers provided.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()
        table_placeholder = st.empty()

        results_df = pd.DataFrame(
            columns=["Country", "VAT Number", "Status", "Name", "Address", "Timestamp"]
        )

        total = len(vat_list)
        for i, vat in enumerate(vat_list, start=1):
            country, number = vat[:2].upper(), vat[2:].replace(" ", "")
            try:
                r = check_vat(country, number)
                status = r.get("status", "Unknown")
                name = r.get("name", "")
                address = r.get("address", "")
            except Exception as e:
                status, name, address = "Invalid", str(e), ""

            results_df = pd.concat(
                [results_df,
                 pd.DataFrame([{
                     "Country": country,
                     "VAT Number": number,
                     "Status": status,
                     "Name": name,
                     "Address": address,
                     "Timestamp": datetime.now(cet).strftime("%Y-%m-%d %H:%M:%S"),
                 }])],
                ignore_index=True,
            )

            # Incremental UI updates
            progress_bar.progress(i / total)
            status_text.text(f"Processing {i} of {total} VAT checks...")
            table_placeholder.dataframe(results_df, width=800)

        status_text.text("Done!")

        # Download as Excel
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="openpyxl") as writer:
            results_df.to_excel(writer, index=False, sheet_name="VAT Results")
        towrite.seek(0)
        st.download_button(
            label="Download results as Excel",
            data=towrite.getvalue(),
            file_name="vat_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

import streamlit as st
import requests

# FastAPI Backend URL
API_URL = "http://127.0.0.1:8000/extract"

# Streamlit UI
st.set_page_config(page_title="Legal Compliance AI", layout="wide")
st.title("📜 Legal Contract Clause Extractor")
st.write("Upload a **PDF** or **TXT** file, and AI will extract key legal clauses.")

# File Upload
uploaded_file = st.file_uploader("Upload Contract File (PDF/TXT)", type=["pdf", "txt"])

if uploaded_file is not None:
    st.write(f"📂 Processing file: **{uploaded_file.name}**")

    if st.button("Extract Legal Clauses 🚀"):
        with st.spinner("Analyzing contract... ⏳"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post(API_URL, files=files)

            if response.status_code == 200:
                summary = response.json()["summary"]
                transformed_summary = response.json()["transformed_summary"]
                st.success("✅ Extraction Complete!")
                st.title("Summary")
                st.markdown(summary, unsafe_allow_html=True)
                st.title("Transformed Summary (Simplifed Technical Jargons)")
                st.markdown(transformed_summary, unsafe_allow_html=True)
            else:
                st.error(f"❌ Error: {response.json()['detail']}")
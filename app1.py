# test_pdf.py

import streamlit as st
from pypdf import PdfReader
from io import BytesIO

st.title("PDF Debug")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:

    st.write("Filename:", uploaded_file.name)

    pdf_bytes = uploaded_file.read()

    st.write("PDF Size:", len(pdf_bytes))

    reader = PdfReader(BytesIO(pdf_bytes))

    st.write("Pages:", len(reader.pages))

    all_text = ""

    for i, page in enumerate(reader.pages):
        text = page.extract_text()

        st.write(f"Page {i+1} Length:", len(text) if text else 0)

        if text:
            all_text += text

    st.write("Total Length:", len(all_text))

    st.text_area("Extracted Text", all_text, height=400)
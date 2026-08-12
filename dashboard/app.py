import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "query"))
sys.path.insert(0, str(Path(__file__).parent.parent / "extraction"))
from search import search
from extract import INDUSTRIES

st.set_page_config(page_title="Find My Job Please", layout="centered")
st.title("Find My Job Please")

industry = st.selectbox("Industry", options=["All"] + INDUSTRIES, index=0)
query_text = st.text_input("What kind of role are you looking for?", placeholder="e.g. machine learning engineer at an early-stage startup")

col1, col2 = st.columns(2)
with col1:
    location = st.text_input("Location filter (optional)", placeholder="e.g. SF, remote")
with col2:
    top_k = st.slider("Number of results", min_value=5, max_value=30, value=10)

if st.button("Search", type="primary") and query_text:
    with st.spinner("Searching..."):
        results = search(
            query_text,
            location=location or None,
            industry=None if industry == "All" else industry,
            top_k=top_k,
        )

    if not results:
        st.info("No results found.")
    else:
        for r in results:
            with st.container(border=True):
                st.subheader(f"{r['company']}")
                if r.get("title"):
                    st.write(r["title"])
                if r.get("industry") and r["industry"] != "OTHER":
                    st.caption(r["industry"])

import streamlit as st 
st.set_page_config(page_title="Image Chat with Gemini", layout="wide")
import pdfgem
import imfin 
import excle
import dynamicdb

apps={
    "pdf": pdfgem,
    "image": imfin,
    "excel": excle,
    "database": dynamicdb
}

selection = st.sidebar.selectbox("Choose app",list(apps.keys()))
apps[selection].run()
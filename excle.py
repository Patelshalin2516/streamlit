import streamlit as st
import pandas as pd
import google.generativeai as genai

genai.configure(api_key="API_KEY")

st.set_page_config(page_title="Chat with Excel using Gemini", layout="wide")
st.title("Chat with Excel using Gemini 1.5")

if "last_uploaded_files" not in st.session_state:
    st.session_state.last_uploaded_files = []
if "excel_text" not in st.session_state:
    st.session_state.excel_text = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

upload_files = st.file_uploader("Upload Excel files", type="xlsx", accept_multiple_files=True)

def extract_text_from_excel(files):
    text = ""
    for file in files:
        excel_data = pd.read_excel(file, sheet_name=None)
        for sheet_name, df in excel_data.items():
            text += f"\n--- Sheet: {sheet_name} ---\n"
            text += df.to_string(index=False)
            text += "\n"
    return text

if upload_files:
    current_files_names = [file.name for file in upload_files]

    if current_files_names != st.session_state.last_uploaded_files:
        # New files detected
        st.session_state.excel_text = extract_text_from_excel(upload_files)
        st.session_state.chat_history = []  # Clear chat for new files
        st.session_state.last_uploaded_files = current_files_names
        st.success("New Excel files uploaded and text extracted!")
    else:
        st.success("Same files re-uploaded. Chat history preserved.")

if st.session_state.excel_text:
    user_input = st.chat_input("Ask a question about the Excel data")

    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        chunks = [st.session_state.excel_text[i:i+3000] for i in range(0, len(st.session_state.excel_text), 3000)]

        prompt = "You are an AI assistant. Use the following Excel data to answer the user's question:\n\n"
        for i, chunk in enumerate(chunks):
            prompt += f"--- excel data part {i+1} ---\n{chunk}\n\n"
        prompt += f"--- user's question ---\n{user_input}"

        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            reply = response.text.strip()

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.chat_history.append(("assistant", reply))
        except Exception as e:
            st.error(f"An error occurred: {e}")

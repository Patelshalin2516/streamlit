print(" This is the correct version of the script.")

import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ✅ Direct Gemini API key here (for local testing only)
genai.configure(api_key="API_KEY")

st.set_page_config(page_title="Chat with PDF using Gemini", layout="wide")
st.title("Chat with your PDF using Gemini Pro")

# Initialize session state
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Upload PDF
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

# Extract text from uploaded PDF
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# If PDF uploaded
if uploaded_file is not None:
    st.session_state.pdf_text = extract_text_from_pdf(uploaded_file)
    st.success("PDF uploaded and text extracted!")

# Show chat input if PDF text is present
if st.session_state.pdf_text:
    user_input = st.chat_input("Ask a question about the PDF")

    # Show chat history
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        # Chunk the PDF to avoid token overflow
        chunks = [st.session_state.pdf_text[i:i + 3000] for i in range(0, len(st.session_state.pdf_text), 3000)]

        # Generate a prompt using all chunks
        prompt = "You are an AI assistant. Use the following document content to answer the user's question:\n\n"
        for i, chunk in enumerate(chunks):
            prompt += f"--- Document Part {i+1} ---\n{chunk}\n\n"
        prompt += f"--- User's Question ---\n{user_input}"

        # Use Gemini 1.5 Pro
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            reply = response.text.strip()

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.chat_history.append(("assistant", reply))

        except Exception as e:
            st.error(f"An error occurred: {e}")

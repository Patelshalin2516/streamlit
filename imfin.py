print("Image-only Gemini chat with follow-up questions enabled.")

import streamlit as st
from PIL import Image
import google.generativeai as genai

# ✅ Set Gemini API key
genai.configure(api_key="AIzaSyDj-GmVC0GJl9lFyTciiKhOl4Sc08S1Y6k")

st.set_page_config(page_title="Image Chat with Gemini", layout="wide")
st.title("Chat with your Image using Gemini 1.5")

# Initialize state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "image" not in st.session_state:
    st.session_state.image = None
if "last_file_name" not in st.session_state:
    st.session_state.last_file_name = ""

# Upload image
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

# Reset everything if new image is uploaded
def reset_all():
    st.session_state.chat_history = []
    st.session_state.image = None

# When a new image is uploaded
if uploaded_file is not None:
    if uploaded_file.name != st.session_state.last_file_name:
        reset_all()
        st.session_state.last_file_name = uploaded_file.name
        st.session_state.image = Image.open(uploaded_file)

        # Show uploaded image
        st.image(st.session_state.image, caption="Uploaded Image", use_column_width=True)

        st.success("Image uploaded! Asking Gemini for a description...")

        # Ask initial question
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            {"role": "user", "parts": ["What do you see in this image?", st.session_state.image]}
        ])
        reply = response.text.strip()

        st.session_state.chat_history.append(("assistant", reply))

# Show chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# If image uploaded, allow follow-up questions
if st.session_state.image:
    user_input = st.chat_input("Ask a follow-up question about the image")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        # Send the image + follow-up question to Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            {"role": "user", "parts": [user_input, st.session_state.image]}
        ])
        reply = response.text.strip()

        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.chat_history.append(("assistant", reply))

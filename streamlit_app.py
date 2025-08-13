import os
import tempfile
import streamlit as st
from converter import convert

st.set_page_config(page_title="Ottoman Converter (Chat)", page_icon="🕌", layout="centered")
st.title("Ottoman Letter Converter — Chat")
st.caption("Type Turkish text; the assistant returns Ottoman Arabic script using Gemini 2.5 Pro.")

# Configuration (no sidebar)
API_KEY = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-pro"
TEMPERATURE = 0.0
NORMALIZE = True
FORCE_NG_FINAL = True

# Knowledgebase path handling (auto-use ottoman.pdf if present)
kb_path = None
default_pdf = os.path.join(os.path.dirname(__file__), "ottoman.pdf")
if os.path.exists(default_pdf):
    kb_path = default_pdf
    st.info(f"Using knowledgebase: {os.path.basename(default_pdf)}")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("Türkçe metni yazın…")
if prompt:
    if not API_KEY:
        st.error("Please set GOOGLE_API_KEY in Streamlit secrets or environment variables.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant reply
        with st.chat_message("assistant"):
            with st.spinner("Converting…"):
                output = convert(
                    text=prompt,
                    kb_path=kb_path,
                    api_key=API_KEY,
                    model_name=MODEL,
                    temperature=TEMPERATURE,
                    normalize=NORMALIZE,
                    force_ng_final=FORCE_NG_FINAL,
                )
            st.code(output)
        # Save assistant reply
        st.session_state.messages.append({"role": "assistant", "content": output})

import os
import tempfile
import streamlit as st
from converter import convert
import logging
import html

st.set_page_config(page_title="Ottoman Converter (Chat)", page_icon="🕌", layout="centered")
st.title("Ottoman Letter Converter — Chat")
st.caption("Type Turkish text; the assistant returns Ottoman Arabic script using Gemini 2.5 Pro.")

# Simple CSS to wrap long RTL text and avoid horizontal scrolling
st.markdown(
    """
    <style>
    .ottoman-output {
        white-space: pre-wrap;       /* respect newlines */
        overflow-wrap: anywhere;     /* wrap long sequences */
        word-break: break-word;      /* extra safety */
        direction: rtl;              /* right-to-left for Arabic script */
        text-align: right;
        font-size: 1.1rem;
        line-height: 1.8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        # Wrap prior assistant outputs using the same CSS class
        if msg["role"] == "assistant":
            st.markdown(f"<div class='ottoman-output'>{html.escape(msg['content'])}</div>", unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("Türkçe metni yazın…")
if prompt:
    if not API_KEY:
        st.error("The system is not available right now. Please try again later.")
        logging.error("Missing GOOGLE_API_KEY in secrets/env")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant reply with robust error handling
        with st.chat_message("assistant"):
            try:
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
                # Detect known error strings returned by converter and show friendly UI message
                if (isinstance(output, str) and (
                    output.startswith("Model call failed:") or
                    output.startswith("No text returned by the model.") or
                    "error" in output.lower()
                )):
                    logging.error(output)
                    st.error("The system is not available right now due to heavy access. Please try again later.")
                else:
                    st.markdown(f"<div class='ottoman-output'>{html.escape(output)}</div>", unsafe_allow_html=True)
                    # Save assistant reply
                    st.session_state.messages.append({"role": "assistant", "content": output})
            except Exception as exc:
                # Log full details to server console; show friendly message to user
                logging.exception("Convert failed: %s", exc)
                st.error("The system is not available right now due to heavy access. Please try again later.")

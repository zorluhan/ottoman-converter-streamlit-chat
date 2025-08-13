import os
import tempfile
import html
import traceback
import streamlit as st
from converter import convert

st.set_page_config(page_title="Ottoman Converter (Chat)", page_icon="🕌", layout="centered")
st.title("Ottoman Letter Converter — Chat")
st.caption("Type Turkish text; the assistant returns Ottoman Arabic script using Gemini 2.5 Pro.")

# Global styles for wrapped, RTL output
st.markdown(
    """
    <style>
    .ottoman-output {
        white-space: pre-wrap; /* preserve newlines */
        word-wrap: break-word;
        overflow-wrap: anywhere;
        direction: rtl; /* right-to-left */
        font-size: 1.25rem;
        line-height: 1.8;
        border-radius: 8px;
        padding: 12px 14px;
        background: #111318;
        border: 1px solid #272a33;
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
        # Render assistant messages with wrapped RTL styling
        if msg["role"] == "assistant":
            st.markdown(f'<div class="ottoman-output">{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("Türkçe metni yazın…")
if prompt:
    if not API_KEY:
        st.error("System configuration error: API key not set. Please set GOOGLE_API_KEY in secrets or environment.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant reply with robust error handling
        try:
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

                # Detect backend error strings and show user-friendly message
                if isinstance(output, str) and (output.startswith("Model call failed:") or output.startswith("No text returned")):
                    # Log full technical message to server console
                    print("[Gemini error]", output)
                    st.warning("The system is not available right now due to heavy load. Please try again shortly.")
                    # Save a short note to history instead of raw error
                    st.session_state.messages.append({"role": "assistant", "content": "(temporary service issue)"})
                else:
                    st.markdown(f'<div class="ottoman-output">{html.escape(output)}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": output})
        except Exception as exc:
            # Log stack trace to console for debugging
            print("[Unhandled error]", exc)
            traceback.print_exc()
            with st.chat_message("assistant"):
                st.warning("The system is not available right now due to heavy access. Please try again later.")
            st.session_state.messages.append({"role": "assistant", "content": "(temporary service issue)"})

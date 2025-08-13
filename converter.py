import os
import unicodedata
from typing import Optional, List

KB_MAX_CHARS = 200_000

ARABIC_RANGES = [
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
]
NG_FINAL = "\uFBD3"  # ﯓ ARABIC LETTER NG FINAL FORM


def is_arabic_char(ch: str) -> bool:
    cp = ord(ch)
    return any(start <= cp <= end for start, end in ARABIC_RANGES)


def replace_last_arabic_with_ng_final(text: str) -> str:
    chars = list(text)
    for i in range(len(chars) - 1, -1, -1):
        if is_arabic_char(chars[i]):
            chars[i] = NG_FINAL
            return "".join(chars)
    return text + NG_FINAL


def read_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def read_pdf(file_path: str) -> str:
    import pypdf
    reader = pypdf.PdfReader(file_path)
    parts: List[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts)


def read_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)


def load_kb_text(path: Optional[str]) -> str:
    if not path:
        return ""
    lower = path.lower()
    if lower.endswith(".txt"):
        raw = read_text_file(path)
    elif lower.endswith(".pdf"):
        raw = read_pdf(path)
    elif lower.endswith(".docx"):
        raw = read_docx(path)
    else:
        raise ValueError("Unsupported doc type. Use .txt, .pdf, or .docx")
    return raw[:KB_MAX_CHARS] if len(raw) > KB_MAX_CHARS else raw


def init_model(model_name: str, api_key: Optional[str] = None):
    api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Provide Google Gemini API key via parameter, st.secrets/env var GOOGLE_API_KEY or GEMINI_API_KEY.")
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    system_instruction = (
        "You are an expert Ottoman Turkish scribe. Convert modern Turkish (Latin alphabet) input "
        "into Ottoman Turkish written with the Ottoman Arabic script. Do not translate meaning; "
        "produce orthographic rendering in Ottoman letters. Preserve punctuation and numbers. "
        "Use standard Ottoman orthography; when ambiguous, prefer the most common historical form. "
        "If reference context is provided, follow its conventions. Output only the Ottoman-script text."
    )
    try:
        return genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
    except TypeError:
        return genai.GenerativeModel(model_name=model_name)


def build_messages(user_text: str, kb_text: str) -> list:
    parts = []
    if kb_text:
        parts.append({"role": "user", "parts": ["Reference context about Ottoman orthography:\n\n" + kb_text]})
    instruction = (
        "Convert the following modern Turkish text to Ottoman Turkish (Arabic script). "
        "Return only the converted Ottoman-script text, no explanations."
    )
    parts.append({"role": "user", "parts": [instruction + "\n\nText:\n" + user_text]})
    return parts


def generate(model, messages: list, temperature: float = 0.0) -> str:
    try:
        resp = model.generate_content(messages, generation_config={"temperature": temperature})
        try:
            text = getattr(resp, "text", None)
        except Exception:
            text = None
        if text:
            return text.strip()
        # Retry once
        resp2 = model.generate_content(messages, generation_config={"temperature": max(0.1, temperature + 0.1)})
        try:
            text2 = getattr(resp2, "text", None)
        except Exception:
            text2 = None
        if text2:
            return text2.strip()
    except Exception as exc:
        return f"Model call failed: {exc}"
    return "No text returned by the model."


def convert(
    text: str,
    kb_path: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-pro",
    temperature: float = 0.0,
    normalize: bool = True,
    force_ng_final: bool = False,
) -> str:
    model = init_model(model_name, api_key=api_key)
    kb_text = load_kb_text(kb_path) if kb_path else ""
    out = generate(model, build_messages(text, kb_text), temperature)
    if normalize:
        out = unicodedata.normalize("NFKC", out)
    if force_ng_final and text.strip().lower().endswith(("n", "ng")):
        out = replace_last_arabic_with_ng_final(out)
    return out

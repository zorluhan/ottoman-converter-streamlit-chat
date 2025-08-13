# Ottoman Letter Converter (Streamlit)

Convert modern Turkish (Latin) text to Ottoman Turkish (Arabic script) using Google's Gemini 2.5 Pro.

## Features
- Upload a knowledgebase document (.txt/.pdf/.docx) to steer orthography
- Optional default `ottoman.pdf` auto-used if present in the app folder
- Temperature control (defaults to 0.0)
- Unicode normalization toggle and optional forced NG final glyph (ﯓ)

## Local Setup
```bash
# 1) Create and activate a virtual environment (optional)
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Provide your Gemini API key
# Option A: Streamlit secrets (recommended)
mkdir -p ~/.streamlit
cat > ~/.streamlit/secrets.toml << 'EOF'
GOOGLE_API_KEY = "YOUR_GEMINI_KEY"
EOF
# Option B: Environment variable
export GOOGLE_API_KEY="YOUR_GEMINI_KEY"

# 4) Run the app
streamlit run streamlit_app.py
```

## Usage
- Paste or type your text
- Upload a knowledgebase file (optional) or place `ottoman.pdf` next to `streamlit_app.py`
- Click Convert

## Deploy
- Streamlit Community Cloud: push this repo to GitHub and deploy via the Streamlit UI
  - App URL: `streamlit_app.py`
  - Add secret `GOOGLE_API_KEY`
- Docker (optional): create a container with this repo and run `streamlit run streamlit_app.py`

## Security
- Do not commit secrets. Use Streamlit secrets or environment variables.

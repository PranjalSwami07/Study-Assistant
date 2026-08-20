# AI Study Assistant

Upload study material (PDF or TXT), then generate structured study notes,
take an interactive quiz, and generate extra high-yield practice questions —
all powered by Gemini (`gemini-2.5-flash`).

## Project Structure

```
study_assistant/
├── app.py                 # Frontend — Streamlit UI, layout, session state
├── backend.py              # Backend — Gemini client, schemas, generation logic
├── requirements.txt        # Python dependencies
├── .env.example             # Template for required environment variables
├── assets/
│   └── style.css            # Custom CSS for the frontend
└── .streamlit/
    └── config.toml          # Streamlit theme / server config
```

`app.py` contains no AI logic — it only handles UI and calls into `backend.py`.
`backend.py` contains no Streamlit imports — it can be tested independently.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
   (or copy `.env.example` to `.env` and load it with your tool of choice)

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Notes

- PDFs are uploaded to Gemini's Files API (`client.files.upload`) so the
  model can process them natively.
- TXT files are read and inlined directly into the prompt.
- The quiz and practice-question generators use `response_schema` with
  Pydantic models (`Quiz`, `PracticeSet` in `backend.py`) to force
  structured JSON output.
- Theme colors and upload size limits live in `.streamlit/config.toml`;
  visual tweaks (spacing, tabs, cards) live in `assets/style.css`.

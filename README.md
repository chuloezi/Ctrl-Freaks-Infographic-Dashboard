# Every Life, Counted — Ctrl Freaks

A Rwanda CRVS infographic project, built with Python analytics and an interactive React dashboard. The optional chatbot uses CSV retrieval and Gemini for grounded explanations.

**Live dashboard:** https://chuloezi.github.io/Ctrl-Freaks-Infographic-Dashboard/

## Project structure

- `static/` — static PDF infographic
- `dynamic/` — React interactive dashboard
- `analytics/` — Python analysis and JSON export
- `data/` — raw and processed data
- `backend/` — Python CSV RAG API (Gemini integration)
- `.github/workflows/pages.yml` — automatic GitHub Pages deployment

## View without installing anything

Open the live dashboard link above. The public chatbot works after you deploy the backend on Render and configure Gemini as described in [`backend/GEMINI_RENDER_SETUP.md`](backend/GEMINI_RENDER_SETUP.md).

## Update the repository from the project ZIP

Copy `backend/rag_server.py`, `backend/requirements.txt`, `backend/GEMINI_RENDER_SETUP.md`, `dynamic/src/App.jsx`, `README.md`, and (if needed) `dynamic/public/config.js` into your cloned repository. Commit and push to `main`.

## Run locally (optional developer setup)

From the repository root:

```powershell
python -m pip install -r requirements.txt
python analytics/export_dashboard_json.py
$env:GEMINI_API_KEY = "YOUR_PRIVATE_KEY"
$env:CORS_ORIGIN = "http://localhost:5173"
python backend/rag_server.py
```

In another terminal:

```powershell
cd dynamic
npm install
npm run dev
```

React's Vite development server forwards `/api` requests to the Python backend. No Ollama installation is needed. Never commit an API key.

## GitHub Pages

GitHub Actions builds React and regenerates the dashboard JSON automatically on pushes to `main`. Enable **Settings → Pages → GitHub Actions**. Visitors do not need Python or Node.js installed.

## RAG data and evidence

The backend searches the processed CRVS CSV rows, calculates supported year-over-year comparisons in Python, and provides only retrieved rows and calculated evidence to Gemini. Numeric statements must cite the returned CSV row IDs. If the retrieved evidence is insufficient, the chatbot should say so.

Some supplemental dashboard figures were inherited from earlier work and are flagged for verification in `data/processed/dashboard_supplemental_source.csv`. Verify these against the original NISR source material before competition submission. The 2025 marriage workbook trend and factsheet count also differ; this distinction is preserved.

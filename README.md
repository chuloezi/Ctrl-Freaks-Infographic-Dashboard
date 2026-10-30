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

## Run locally (optional developer setup)

From the repository root:

```powershell
python -m pip install -r requirements.txt
python analytics/analyze_crvs.py
python analytics/export_dashboard_json.py
python analytics/verify_dashboard.py
python backend/eval_questions.py
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

GitHub Actions regenerates the dashboard JSON, checks every figure against the workbook rows, tests the chatbot's retrieval and builds React on pushes to `main`. A failed check stops the deployment. Enable **Settings → Pages → GitHub Actions**. Visitors do not need Python or Node.js installed.

## RAG data and evidence

The backend searches the processed CRVS CSV rows, calculates supported year-over-year comparisons in Python, and provides only retrieved rows and calculated evidence to Gemini. Numeric statements must cite the returned CSV row IDs. If the retrieved evidence is insufficient, the chatbot should say so.

The retriever is keyword-based rather than embedding-based, and citations are checked for valid row IDs, not for every claim. The API allows 10 questions per minute per visitor (`RATE_LIMIT_PER_MINUTE`) and caches Gemini answers in memory.

## Data sources and known discrepancies

`analytics/analyze_crvs.py` reads every chart series and indicator from the NISR workbooks, and `analytics/verify_dashboard.py` checks the published figures against those rows.

- **Marriages, 2025:** workbook Tables 18 and 20 give 50,256; the published factsheet prints 50,236. The dashboard uses 50,256. The static PDF cites the factsheet and shows 50,236.
- **Workbook labels:** Figures 23 and 26 appear to swap their row labels. The dashboard follows Figures 24 and 25 and Table 10.9.
- **Divorces by province:** Table 24 counts each couple by the wife's and the husband's residence, so the dashboard shows both.

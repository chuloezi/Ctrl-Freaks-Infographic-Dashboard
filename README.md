# Every Life, Counted — Ctrl Freaks

A Rwanda Civil Registration and Vital Statistics project using Python for data analysis and React for the interactive infographic. Data comes from NISR CRVS workbooks. This is an independent student project, not an official NISR website.

**Live dashboard:** Add the GitHub Pages URL here after publishing.

## Project folders

```text
static/                       Static infographic (PDF)
dynamic/                      Interactive React infographic
  src/                        Dashboard components, charts, styles and data
  public/                     Public files, including the PDF download
  package.json                JavaScript dependencies
analytics/                    Python analysis and JSON export scripts
data/raw/                     Original Excel workbooks
data/processed/               Calculated data and source notes
backend/                      Optional Ollama question-answering server
requirements.txt              Python dependencies
.github/workflows/pages.yml   Automatic GitHub Pages deployment
```

## View the infographics

- **Static:** Open `static/static_infographic.pdf` in any PDF reader. The PDF is also included in the published site as `static_infographic.pdf`.
- **Dynamic:** Open the live GitHub Pages URL in your browser. No installation is needed to view the dashboard.

## Run the project locally

Install Python 3.10+, Node.js LTS (includes npm), and Git. Ollama is only needed for local AI questions.

1. Clone this repository and open a terminal at its root:

   ```powershell
   git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
   cd YOUR-REPO
   ```

2. Install the Python libraries and prepare the dashboard data:

   ```powershell
   python -m pip install -r requirements.txt
   python analytics/export_dashboard_json.py
   ```

   To rerun the analysis from the Excel workbooks first, run `python analytics/analyze_crvs.py` and then run the export command again.

3. Start React:

   ```powershell
   cd dynamic
   npm install
   npm run dev
   ```

   Open the local address shown in the terminal, usually `http://localhost:5173/`. If PowerShell blocks `npm`, use `npm.cmd` instead. For a production build, run `npm run build` from `dynamic/`.

## Run the local AI assistant (optional)

Install [Ollama](https://ollama.com/) and download the model:

```powershell
ollama pull qwen2.5:3b
ollama serve
```

If the Ollama app already runs the service, you do not need to start it twice. In another terminal, from the **repository root**, run:

```powershell
python -m pip install -r requirements.txt
$env:CORS_ORIGIN = 'http://localhost:5173'
python backend/rag_server.py
```

Keep React running in its own terminal. The development server forwards `/api` requests to the Python backend. For a publicly working chatbot, the backend and a compatible LLM must be hosted separately and configured in `dynamic/public/config.js`. GitHub Pages alone cannot run Ollama.

## Publish to GitHub Pages

1. Upload the repository files, including the `.github/` folder, to GitHub.
2. In repository **Settings → Pages**, set the source to **GitHub Actions**.
3. Push to the `main` branch, then check the **Actions** tab for a successful build.
4. Copy the Pages URL into the **Live dashboard** line at the top of this README and into your GitHub repository About section.

The workflow exports Python results, installs React dependencies, builds `dynamic/` and publishes `dynamic/dist/`. Visitors need only a browser.

## Data sources and checking results

The Python scripts use the NISR CRVS 2023–2025 workbooks in `data/raw/`. The React dashboard reads `dynamic/src/analytics-data.json`, exported from the processed CSV files.

Some supplemental chart values were transferred from an earlier dashboard and are marked `needs_source_verification` in `data/processed/dashboard_supplemental_source.csv`. Check them against the original source tables before submission. The reported 2025 marriage count also differs between the workbook trend (50,256) and the factsheet headline (50,236); the dashboard keeps that distinction.

The public dashboard is usable without the AI server, but the chatbot is not publicly functional until you deploy its backend separately.

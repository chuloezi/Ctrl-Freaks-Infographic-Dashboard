# Deploy the Ctrl Freaks CSV RAG chatbot with Gemini + Render

The React dashboard stays on GitHub Pages. Render runs a small Python API that searches CSV data. Gemini generates responses from the retrieved evidence. Judges use the website and install nothing.

## 1. Create an API key

1. Open https://aistudio.google.com/api-keys and create a Gemini API key. Confirm your account has free-tier access to `gemini-2.5-flash` (availability and limits vary).
2. Never put the key in GitHub, `config.js`, or frontend JavaScript.
3. The default model is `gemini-2.5-flash`. You may change it to an available free-tier model with the `GEMINI_MODEL` environment variable.

## 2. Push the updated code to GitHub

The Render service must use the updated `backend/rag_server.py`. Commit and push it before creating the web service.

## 3. Create a Render Web Service

- Render Dashboard → New → Web Service → connect your GitHub repository.
- Name: `ctrl-freaks-api` (or another available name)
- Language: Python
- Branch: `main`
- Root directory: repository root (leave blank)
- Build command: `pip install -r backend/requirements.txt`
- Start command: `python backend/rag_server.py`
- Health check: `/api/health`
- Instance type: choose a tier that meets your competition availability needs.

Environment variables:

| Key | Value |
| --- | --- |
| `GEMINI_API_KEY` | your private key from AI Studio |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `HOST` | `0.0.0.0` |
| `CORS_ORIGIN` | `https://chuloezi.github.io` |

Render sets `PORT` automatically; don't hardcode it.

Once deployed, open `https://YOUR-RENDER-SERVICE.onrender.com/api/health`. It should show `status: ok`, `model_ready: true` and the indexed CSV row count. This only verifies configuration, not a successful Gemini response.

## 4. Connect the React dashboard

Edit `dynamic/public/config.js`:

```js
window.CRVS_API_BASE = 'https://YOUR-RENDER-SERVICE.onrender.com';
```

Commit and push. GitHub Pages will rebuild the React site. Your Gemini API key stays only in Render.

## 5. Test an actual question

From the public dashboard ask: "How many registered births were there in 2025?" The response should include CSV citations and show `Mode: gemini_csv_rag`.

You can also test directly using a PowerShell terminal:

```powershell
$body = @{question='How many registered births were there in 2025?'} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'https://YOUR-RENDER-SERVICE.onrender.com/api/ask' -ContentType 'application/json' -Body $body
```

If the answer says Gemini is unavailable, inspect Render logs and check free-tier quota, model access, and the API key. The service falls back to retrieved CSV evidence when the model request fails. Health status does not test the API key's validity.

## 6. Important notes for a public competition

- Gemini free-tier quotas are limited, can vary, and may change. Check AI Studio's rate limit dashboard and pricing before the event.
- Free-tier API content can be used by Google to improve its products: send only information approved for public disclosure.
- Render free web services can sleep during inactivity. This can slow the first chatbot response; use an appropriate always-on tier if required.
- The endpoint is public; add rate limiting or abuse protection before sustained public use to reduce exhaustion of the free API quota.
- The retriever is keyword-based, not embedding-based. CSV citations are checked for IDs but not every factual claim is mechanically verified. Verify the original NISR values.

# Sentiment Classifier

A FastAPI web application using `distilbert-base-uncased-finetuned-sst-2-english` to classify text as `POSITIVE` or `NEGATIVE`.

## Configuration

Set the required Hugging Face token in a local `.env` file (never commit it):

```text
HF_TOKEN=hf_your_read_token_here
```

The application loads the token from the `HF_TOKEN` environment variable. It is used only while loading the model and is never returned by the API or sent to the browser.

## Run locally

PowerShell:

```powershell
Set-Location d:\training
\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:HF_TOKEN = (Get-Content .env | Where-Object { $_ -match '^HF_TOKEN=' } | ForEach-Object { $_.Substring(9) })
uvicorn classification_practice:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000. The production-style start command is:

```text
uvicorn classification_practice:app --host 0.0.0.0 --port ${PORT:-8000}
```

On PowerShell, use `$env:PORT = "8000"` before starting if a custom port is needed. The application also accepts `PORT` when run with `python classification_practice.py`.

## API

`GET /health` returns `{"status":"healthy"}` after the model has loaded.

`POST /predict` accepts:

```json
{"text":"I really enjoyed this course."}
```

and returns the original text, model label, and confidence score:

```json
{"text":"I really enjoyed this course.","label":"POSITIVE","score":0.99}
```

Text must not be empty and is limited to 5,000 characters. Invalid requests return HTTP 422; unavailable model or inference failures return HTTP 503 or 502.

## Docker

Build and run the production image without including `.venv` or `.env`:

```powershell
docker build -t sentiment-classifier .
docker run --rm -p 8000:8000 -e HF_TOKEN=$env:HF_TOKEN sentiment-classifier
```

The image uses Uvicorn, binds to `0.0.0.0`, and honors the platform-provided `PORT` environment variable.

## Deploy to Render

The included `render.yaml` configures a native Python web service. It does not require Docker locally.

1. Put this project in a GitHub repository, excluding `.env` and `.venv`.
2. In Render, choose **New > Blueprint**, connect the repository, and select it.
3. When prompted, enter `HF_TOKEN` as a secret environment variable using a Hugging Face Read token.
4. Create the service. Render runs the build and start commands from `render.yaml` and provides `PORT`.
5. After deployment, verify `https://<your-render-service>.onrender.com/health` returns `{"status":"healthy"}`.
6. Open the service URL to use the web interface, or test the API:

```powershell
Invoke-RestMethod -Uri https://<your-render-service>.onrender.com/predict -Method Post -ContentType 'application/json' -Body '{"text":"I really enjoyed this course."}'
```

The exact production start command configured for Render is:

```text
uvicorn classification_practice:app --host 0.0.0.0 --port $PORT
```

The final public URL is assigned by Render after deployment. No public URL can be reported until a Render account is connected to the repository.

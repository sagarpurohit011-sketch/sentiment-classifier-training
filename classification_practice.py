"""FastAPI application for sentiment classification with Hugging Face."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
from transformers import pipeline

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
MAX_TEXT_LENGTH = 5_000
STATIC_DIR = Path(__file__).parent / "static"


class PredictionRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH)

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class PredictionResponse(BaseModel):
    text: str
    label: str
    score: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the classifier once per application process."""
    load_dotenv()
    token = os.getenv("HF_TOKEN") or None

    app.state.classifier = None
    app.state.model_error = None
    try:
        app.state.classifier = pipeline(
            "text-classification",
            model=MODEL_NAME,
            token=token,
        )
    except Exception:
        # Keep the process available so health checks expose the failure without
        # returning implementation details or credentials.
        app.state.model_error = "The classification model could not be loaded."
    yield


app = FastAPI(
    title="Sentiment Classifier",
    description="Classify text as positive or negative sentiment.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    if request.app.state.classifier is None:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})
    return JSONResponse(content={"status": "healthy"})


@app.post("/predict", response_model=PredictionResponse)
async def predict(payload: PredictionRequest, request: Request) -> PredictionResponse:
    classifier = request.app.state.classifier
    if classifier is None:
        raise HTTPException(status_code=503, detail="The classification model is unavailable.")

    try:
        prediction: dict[str, Any] = classifier(payload.text)[0]
    except Exception as error:
        raise HTTPException(status_code=502, detail="The classification service failed.") from error

    return PredictionResponse(
        text=payload.text,
        label=str(prediction["label"]),
        score=float(prediction["score"]),
    )


def main() -> None:
    """Run the API for local development."""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("classification_practice:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

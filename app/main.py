"""FastAPI application for Clinical BERT inference."""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.model import get_model
from app.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    logger.info("Starting up API...")
    try:
        # Warm up model
        get_model()
        logger.info("Model initialized")
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise
    yield
    logger.info("Shutting down API...")


app = FastAPI(
    title="Clinical BERT Real-Time Inference API",
    description="API for clinical text classification",
    version=API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Clinical BERT Real-Time Inference API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    try:
        model = get_model()
        model_loaded = bool(model.model) and bool(model.tokenizer)
        return HealthResponse(
            status="healthy" if model_loaded else "unhealthy",
            model_loaded=model_loaded,
            version=API_VERSION,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            version=API_VERSION,
        )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    start = time.time()
    try:
        model = get_model()
        label, score = model.predict(request.sentence)
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"Predict done in {elapsed_ms:.2f}ms")
        return PredictionResponse(label=label, score=score)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch(request: BatchPredictionRequest):
    start = time.time()
    try:
        if len(request.sentences) > 100:
            raise HTTPException(status_code=400, detail="Batch size exceeds 100")
        model = get_model()
        results = model.predict_batch(request.sentences)
        preds = [PredictionResponse(label=l, score=s) for l, s in results]
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"Batch predict ({len(preds)}) in {elapsed_ms:.2f}ms")
        return BatchPredictionResponse(predictions=preds)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail="Batch prediction failed")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
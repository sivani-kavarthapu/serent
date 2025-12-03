"""FastAPI application for Clinical BERT inference."""
import logging
import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
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

# API version
API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: Load model
    logger.info("Starting up Clinical BERT API...")
    try:
        model = get_model()
        logger.info("Model loaded successfully during startup")
    except Exception as e:
        logger.error(f"Failed to load model during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown: Cleanup if needed
    logger.info("Shutting down Clinical BERT API...")


# Create FastAPI app
app = FastAPI(
    title="Clinical BERT Real-Time Inference API",
    description="API for clinical text classification using Hugging Face Clinical BERT model",
    version=API_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Clinical BERT Real-Time Inference API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        model = get_model()
        model_loaded = model.model is not None and model.tokenizer is not None
        return HealthResponse(
            status="healthy" if model_loaded else "unhealthy",
            model_loaded=model_loaded,
            version=API_VERSION,
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            version=API_VERSION,
        )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    """
    Predict assertion status for a single clinical sentence.
    
    Expected labels:
    - PRESENT: Medical concept is present
    - ABSENT: Medical concept is absent/denied
    - CONDITIONAL: Medical concept is conditional/hypothetical
    """
    start_time = time.time()
    
    try:
        model = get_model()
        label, score = model.predict(request.sentence)
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.info(f"Prediction completed in {elapsed_time:.2f}ms")
        
        return PredictionResponse(label=label, score=score)
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict assertion status for multiple clinical sentences (batch processing).
    
    This endpoint is more efficient for processing multiple sentences at once.
    """
    start_time = time.time()
    
    try:
        if len(request.sentences) > 100:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size exceeds maximum of 100 sentences"
            )
        
        model = get_model()
        results = model.predict_batch(request.sentences)
        
        predictions = [
            PredictionResponse(label=label, score=score)
            for label, score in results
        ]
        
        elapsed_time = (time.time() - start_time) * 1000
        logger.info(
            f"Batch prediction completed in {elapsed_time:.2f}ms for "
            f"{len(request.sentences)} sentences"
        )
        
        return BatchPredictionResponse(predictions=predictions)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


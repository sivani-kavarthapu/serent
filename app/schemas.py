"""Pydantic schemas for request/response validation."""
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field

class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions."""
    sentences: Annotated[List[str], Field(min_length=1)] = Field(
        ..., description="List of clinical sentences to classify"
    )

class PredictionResponse(BaseModel):
    """Response schema for single prediction."""
    label: Literal["PRESENT", "ABSENT", "CONDITIONAL"] = Field(
        ..., description="Predicted label (PRESENT, ABSENT, CONDITIONAL)"
    )
    score: float = Field(..., description="Confidence score", ge=0.0, le=1.0)

class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions."""
    predictions: List[PredictionResponse] = Field(
        ..., description="List of predictions"
    )

class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="API version")

    model_config = {
        "protected_namespaces": (),
    }
"""Pydantic schemas for request/response validation."""
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    sentence: str = Field(..., min_length=1, description="Clinical sentence to classify")

class BatchPredictionRequest(BaseModel):
    sentences: Annotated[List[str], Field(min_length=1)] = Field(
        ..., description="List of clinical sentences to classify"
    )

class PredictionResponse(BaseModel):
    label: Literal["PRESENT", "ABSENT", "CONDITIONAL"] = Field(
        ..., description="Predicted label"
    )
    score: float = Field(..., description="Confidence score", ge=0.0, le=1.0)

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse] = Field(..., description="List of predictions")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="API version")
    model_config = {"protected_namespaces": ()}
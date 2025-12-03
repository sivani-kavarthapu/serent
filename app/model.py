"""Model loading and prediction logic."""
import logging
from typing import List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "bvanaken/clinical-assertion-negation-bert"
LABEL_MAPPING = {0: "ABSENT", 1: "PRESENT", 2: "CONDITIONAL"}


class ClinicalBERTModel:
    """Wrapper class for Clinical BERT model."""
    
    def __init__(self):
        """Initialize the model (loads on first instantiation)."""
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()
    
    def _load_model(self):
        """Load the model and tokenizer from Hugging Face."""
        try:
            logger.info(f"Loading model: {MODEL_NAME}")
            logger.info(f"Using device: {self.device}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def predict(self, sentence: str) -> Tuple[str, float]:
        """
        Predict assertion status for a single sentence.
        
        Args:
            sentence: Clinical sentence to classify
            
        Returns:
            Tuple of (label, confidence_score)
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                sentence,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            label = LABEL_MAPPING.get(predicted_class, "UNKNOWN")
            return label, confidence
            
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            raise
    
    def predict_batch(self, sentences: List[str]) -> List[Tuple[str, float]]:
        """
        Predict assertion status for multiple sentences.
        
        Args:
            sentences: List of clinical sentences to classify
            
        Returns:
            List of tuples (label, confidence_score)
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")
        
        try:
            # Tokenize all inputs
            inputs = self.tokenizer(
                sentences,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                predicted_classes = torch.argmax(probabilities, dim=-1)
                confidences = torch.max(probabilities, dim=-1).values
            
            results = []
            for pred_class, conf in zip(predicted_classes, confidences):
                label = LABEL_MAPPING.get(pred_class.item(), "UNKNOWN")
                results.append((label, conf.item()))
            
            return results
            
        except Exception as e:
            logger.error(f"Error during batch prediction: {str(e)}")
            raise


# Global model instance (loaded once at startup)
_model_instance = None


def get_model() -> ClinicalBERTModel:
    """Get or create the global model instance."""
    global _model_instance
    if _model_instance is None:
        _model_instance = ClinicalBERTModel()
    return _model_instance


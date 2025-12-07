"""Model loading and prediction logic (Hugging Face)."""
import logging
from typing import List, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

MODEL_NAME = "bvanaken/clinical-assertion-negation-bert"

# Map model labels to API labels used in tests
# Many assertion models use labels like: "PRESENT", "ABSENT", "CONDITIONAL"
# If the model uses different names, normalize them below.
LABEL_NORMALIZATION = {
    "present": "PRESENT",
    "absent": "ABSENT",
    "conditional": "CONDITIONAL",
    "possible": "CONDITIONAL",  # Map POSSIBLE to CONDITIONAL
    "negated": "ABSENT",
    "affirmed": "PRESENT",
    "hypothetical": "CONDITIONAL",
}

class ClinicalBERTModel:
    """Wrapper around a Hugging Face sequence classification model."""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.id2label = {}
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading model: {MODEL_NAME} on {self.device}")
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            self.model.to(self.device)
            self.model.eval()

            # Build id2label map and normalize to API labels
            raw_id2label = getattr(self.model.config, "id2label", {})
            self.id2label = {}
            for idx, raw in raw_id2label.items():
                norm = LABEL_NORMALIZATION.get(raw.lower(), raw.upper())
                self.id2label[idx] = norm

            logger.info(f"Model loaded. Labels: {self.id2label}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def _postprocess_label(self, idx: int) -> str:
        return self.id2label.get(idx, "PRESENT")  # default to PRESENT

    def predict(self, sentence: str) -> Tuple[str, float]:
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")

        try:
            inputs = self.tokenizer(
                sentence,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=-1)
                pred_idx = int(torch.argmax(probs, dim=-1).item())
                score = float(probs[0][pred_idx].item())

            label = self._postprocess_label(pred_idx)
            return label, score
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise

    def predict_batch(self, sentences: List[str]) -> List[Tuple[str, float]]:
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")

        try:
            inputs = self.tokenizer(
                sentences,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=-1)
                pred_indices = torch.argmax(probs, dim=-1).tolist()
                scores = torch.max(probs, dim=-1).values.tolist()

            return [(self._postprocess_label(i), float(s)) for i, s in zip(pred_indices, scores)]
        except Exception as e:
            logger.error(f"Error during batch prediction: {e}")
            raise


# Global singleton
_model_instance: ClinicalBERTModel | None = None

def get_model() -> ClinicalBERTModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = ClinicalBERTModel()
    return _model_instance
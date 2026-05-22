"""
Inference module for text summarization.

Uses sshleifer/distilbart-cnn-12-6 via HuggingFace Transformers.
Calls the model directly (no pipeline) for compatibility with all transformers versions.
"""

import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

# Module-level singletons — loaded once, reused across all requests
_model = None
_tokenizer = None

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"

# Length → token bounds
LENGTH_BOUNDS = {
    "short":  {"min_length": 20,  "max_length": 60},
    "medium": {"min_length": 60,  "max_length": 130},
    "long":   {"min_length": 130, "max_length": 250},
}


def _get_pipeline():
    """Load the model and tokenizer once and cache them."""
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        logger.info("Loading %s (first load may take a minute)...", MODEL_NAME)
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        _model.eval()
        logger.info("Model loaded successfully.")
    return _model, _tokenizer


def summarize(
    text: str,
    model_path: str = None,
    min_length: int = None,
    max_length: int = None,
    length: str = "medium",
) -> str:
    """
    Summarize the given text using sshleifer/distilbart-cnn-12-6.

    Args:
        text:       Input article text (up to 10,000 characters).
        model_path: Ignored — kept for backward compatibility.
        min_length: Minimum summary length in tokens.
        max_length: Maximum summary length in tokens.
        length:     "short", "medium", or "long".

    Returns:
        Decoded summary string.
    """
    model, tokenizer = _get_pipeline()

    # Resolve token bounds
    bounds = LENGTH_BOUNDS.get(length, LENGTH_BOUNDS["medium"])
    resolved_min = min_length if min_length is not None else bounds["min_length"]
    resolved_max = max_length if max_length is not None else bounds["max_length"]

    # Tokenize — BART has a 1024-token input limit
    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=1024,
        truncation=True,
    )

    with torch.no_grad():
        summary_ids = model.generate(
            inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            num_beams=4,
            min_length=resolved_min,
            max_length=resolved_max,
            length_penalty=2.0,
            early_stopping=True,
        )

    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

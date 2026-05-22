
import os

class Config:
    # Paths
    BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR        = os.path.join(BASE_DIR, "data")
    RAW_DIR         = os.path.join(DATA_DIR, "raw")
    PROCESSED_DIR   = os.path.join(DATA_DIR, "processed")
    MODEL_DIR       = os.path.join(BASE_DIR, "models", "saved_model")

    # Dataset (CNN/DailyMail via HuggingFace datasets)
    DATASET_NAME    = "cnn_dailymail"
    DATASET_VERSION = "3.0.0"
    MAX_ARTICLE_LEN = 512
    MAX_SUMMARY_LEN = 128

    # Model hyperparameters
    EMBED_DIM       = 256
    HIDDEN_DIM      = 512
    NUM_LAYERS      = 2
    DROPOUT         = 0.3
    VOCAB_SIZE      = 32000          # SentencePiece vocab

    # Training
    BATCH_SIZE      = 32
    EPOCHS          = 10
    LEARNING_RATE   = 3e-4
    CLIP_GRAD       = 1.0
    TEACHER_FORCING = 0.5
    DEVICE          = "cuda" if __import__("torch").cuda.is_available() else "cpu"

    # Tokenizer
    TOKENIZER_MODEL = "t5-small"     # used for BPE tokenization

    # Inference
    BEAM_SIZE       = 4
    LENGTH_PENALTY  = 0.6


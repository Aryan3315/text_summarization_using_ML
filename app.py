
import os
import sys
import logging
import traceback
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"txt", "pdf"}
MAX_CHARS = 10_000

# ── Length → token bounds ────────────────────────────────────────────────────
LENGTH_BOUNDS = {
    "short":  {"min_length": 20,  "max_length": 60},
    "medium": {"min_length": 60,  "max_length": 130},
    "long":   {"min_length": 130, "max_length": 250},
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def count_words(text: str) -> int:
    return len(text.split())


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """
    POST /api/summarize
    Body: { "text": str, "length": "short"|"medium"|"long" }
    Returns: { "summary": str, "word_count": int }
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Request body must be JSON.", "code": "INVALID_REQUEST"}), 400

        text = data.get("text", "")
        length = data.get("length", "medium")

        # Validate text
        if not text or not text.strip():
            return jsonify({
                "error": "The text field is required and was not provided.",
                "code": "TEXT_REQUIRED"
            }), 400

        if len(text) > MAX_CHARS:
            return jsonify({
                "error": f"Text exceeds the {MAX_CHARS:,} character limit.",
                "code": "TEXT_TOO_LONG"
            }), 400

        # Validate length
        if length not in LENGTH_BOUNDS:
            return jsonify({
                "error": "Invalid length. Valid values are: short, medium, long.",
                "code": "INVALID_LENGTH"
            }), 400

        # Run summarization using the inference module
        from src.inference import summarize
        bounds = LENGTH_BOUNDS[length]
        summary = summarize(
            text,
            min_length=bounds["min_length"],
            max_length=bounds["max_length"],
            length=length,
        )

        if not summary or not summary.strip():
            return jsonify({
                "error": "Summarization failed. Please try again.",
                "code": "SUMMARIZATION_FAILED"
            }), 500

        return jsonify({
            "summary": summary.strip(),
            "word_count": count_words(summary.strip())
        }), 200

    except FileNotFoundError:
        logger.error("Model checkpoint not found:\n%s", traceback.format_exc())
        return jsonify({
            "error": "Model checkpoint not found. Please train the model first by running: python src/train.py",
            "code": "MODEL_UNAVAILABLE"
        }), 503

    except Exception as exc:
        logger.error("Summarization error:\n%s", traceback.format_exc())
        # In debug mode expose the real error; in production keep it generic
        error_detail = str(exc) if app.debug else "Summarization failed. Please try again."
        return jsonify({
            "error": error_detail,
            "code": "SUMMARIZATION_FAILED"
        }), 500


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    POST /api/upload
    Body: multipart/form-data with field "file" (.txt or .pdf, ≤ 5 MB)
    Returns: { "text": str }
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided.", "code": "NO_FILE"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected.", "code": "NO_FILE"}), 400

        if not allowed_file(file.filename):
            return jsonify({
                "error": "Unsupported file format. Accepted formats: .txt, .pdf",
                "code": "UNSUPPORTED_FORMAT"
            }), 400

        file_bytes = file.read()

        if len(file_bytes) == 0:
            return jsonify({"error": "The uploaded file is empty.", "code": "EMPTY_FILE"}), 400

        ext = file.filename.rsplit(".", 1)[1].lower()

        if ext == "txt":
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1")

        elif ext == "pdf":
            text = _extract_pdf_text(file_bytes)
            if text is None:
                return jsonify({
                    "error": "Text extraction from the PDF failed. Please paste your text manually.",
                    "code": "EXTRACTION_FAILED"
                }), 422

        return jsonify({"text": text.strip()}), 200

    except Exception as exc:
        logger.error("Upload error:\n%s", traceback.format_exc())
        return jsonify({
            "error": "File processing failed. Please try again.",
            "code": "UPLOAD_FAILED"
        }), 500


def _extract_pdf_text(file_bytes: bytes) -> str | None:
    """Try PyMuPDF first, fall back to pypdf."""
    # Primary: PyMuPDF
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        if text.strip():
            return text
    except Exception:
        pass

    # Fallback: pypdf
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
        if text.strip():
            return text
    except Exception:
        pass

    return None


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({
        "error": "File size exceeds the 5 MB limit.",
        "code": "FILE_TOO_LARGE"
    }), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found.", "code": "NOT_FOUND"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed.", "code": "METHOD_NOT_ALLOWED"}), 405


if __name__ == "__main__":
    # Pre-load the model before accepting requests
    logger.info("Pre-loading summarization model...")
    try:
        from src.inference import _get_pipeline
        _get_pipeline()
        logger.info("Model ready.")
    except Exception as e:
        logger.warning("Model pre-load failed: %s — will retry on first request.", e)
    app.run(debug=True, host="0.0.0.0", port=5000)

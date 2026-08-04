"""Local-only OCR support for user-provided JPEG documents."""

from __future__ import annotations

import io
import threading
from pathlib import Path


MAX_IMAGE_PIXELS = 30_000_000
MIN_LINE_CONFIDENCE = 0.45
SUPPORTED_RASTER_FORMATS = {"JPEG", "MPO", "PNG", "WEBP"}

_ENGINE = None
_ENGINE_LOCK = threading.Lock()


class LocalOCRUnavailable(RuntimeError):
    """Raised when the local OCR runtime or its Latin model is unavailable."""


def _build_engine():
    try:
        import rapidocr
        from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR
    except ImportError as exc:
        raise LocalOCRUnavailable(
            "L’OCR local est absent. Installez requirements-optional.txt puis relancez Nexus."
        ) from exc

    models_root = Path(rapidocr.__file__).resolve().parent / "models"
    detector_path = models_root / "PP-OCRv6_det_small.onnx"
    classifier_path = models_root / "ch_ppocr_mobile_v2.0_cls_mobile.onnx"
    recognizer_path = models_root / "latin_PP-OCRv5_rec_mobile.onnx"
    if not all(path.is_file() for path in (detector_path, classifier_path, recognizer_path)):
        raise LocalOCRUnavailable(
            "Un modèle OCR local est absent. Réinstallez le composant OCR avant de relancer Nexus."
        )

    return RapidOCR(
        params={
            "Global.log_level": "critical",
            "Det.model_path": str(detector_path),
            "Cls.model_path": str(classifier_path),
            "Rec.lang_type": LangRec.LATIN,
            "Rec.model_type": ModelType.MOBILE,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.model_path": str(recognizer_path),
        }
    )


def _engine():
    global _ENGINE
    if _ENGINE is None:
        with _ENGINE_LOCK:
            if _ENGINE is None:
                _ENGINE = _build_engine()
    return _ENGINE


def extract_text_from_jpeg(content: bytes) -> list[dict[str, str]]:
    """Normalize a JPEG-compatible image and return confident local OCR lines."""

    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError as exc:
        raise LocalOCRUnavailable(
            "La lecture d’images locale est absente. Installez requirements-optional.txt."
        ) from exc

    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in SUPPORTED_RASTER_FORMATS:
                raise ValueError("Le fichier fourni n’est pas une image compatible et lisible.")
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                raise ValueError("L’image JPEG est vide ou possède une résolution trop élevée.")
            image.load()
            normalized_image = ImageOps.exif_transpose(image).convert("RGB")
            normalized_stream = io.BytesIO()
            normalized_image.save(normalized_stream, format="JPEG", quality=95)
            normalized_content = normalized_stream.getvalue()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("L’image JPEG est invalide ou illisible.") from exc

    try:
        result = _engine()(normalized_content)
    except LocalOCRUnavailable:
        raise
    except Exception as exc:
        raise ValueError("La lecture OCR locale de l’image JPEG a échoué.") from exc

    texts = tuple(getattr(result, "txts", ()) or ())
    scores = tuple(getattr(result, "scores", ()) or ())
    passages = []
    for index, text in enumerate(texts, start=1):
        normalized = " ".join(str(text or "").split()).strip()
        score = float(scores[index - 1]) if index - 1 < len(scores) else 0.0
        if normalized and score >= MIN_LINE_CONFIDENCE:
            passages.append({"reference": f"OCR ligne {index}", "text": normalized})
    if not passages:
        raise ValueError(
            "Aucun texte suffisamment lisible n’a été trouvé dans l’image JPEG. "
            "Utilisez une photo nette, droite et bien éclairée."
        )
    return passages

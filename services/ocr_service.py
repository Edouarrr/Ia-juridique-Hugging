"""Service d'OCR basé sur Tesseract."""

from typing import Any

from PIL import Image
import pytesseract


class OCRService:
    """Fournit une extraction de texte simple depuis une image."""

    def extract_text(self, image_path: str) -> str:
        """Retourne le texte présent dans l'image donnée."""
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)


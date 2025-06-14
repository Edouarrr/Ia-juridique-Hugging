"""Évaluation simple de la pertinence d'une jurisprudence."""

from typing import List

from modules.jurisprudence_models import JurisprudenceReference, VerificationResult


class JurisprudenceEvaluator:
    """Vérifie si un texte mentionne une jurisprudence connue."""

    def __init__(self, references: List[JurisprudenceReference]):
        self.references = references

    def evaluate(self, text: str) -> VerificationResult:
        """Retourne un résultat simple basé sur la présence d'un numéro."""
        for ref in self.references:
            if ref.numero and ref.numero in text:
                return VerificationResult(reference=ref, success=True, details="reference found")
        return VerificationResult(reference=JurisprudenceReference(), success=False, details="not found")


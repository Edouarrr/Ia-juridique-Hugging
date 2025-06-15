from dataclasses import dataclass
from typing import Any, Optional

class SourceJurisprudence:
    pass

@dataclass
class JurisprudenceReference:
    numero: str = ""
    date: Optional[str] = None
    juridiction: str = ""
    source: Optional[SourceJurisprudence] = None

@dataclass
class VerificationResult:
    reference: JurisprudenceReference
    success: bool = False
    details: Any = None

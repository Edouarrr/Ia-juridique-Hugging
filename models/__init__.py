# models/__init__.py - Version explicite
from .dataclasses import (
    TypePersonne,
    TypeSanction,
    Personne,
    Infraction,
    AnalyseJuridique,
    DocumentJuridique,
    RechercheJuridique,
    CasJuridique,
    Sanction,
    ElementConstitutif,
    Prescription,
    AnalyseRisque
)

from .jurisprudence_models import (
    SourceJurisprudence,
    TypeJuridiction,
    JurisprudenceReference,
    JurisprudenceDetail,
    VerificationResult,
    JurisprudenceSearch,
    JurisprudenceAnalysis,
    JurisprudenceCollection
)
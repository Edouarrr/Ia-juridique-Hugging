# models/configurations.py
"""
Configurations par défaut pour l'application juridique
"""

from modules.dataclasses import StyleConfig

# ========== CONFIGURATIONS DE STYLE PAR DÉFAUT ==========

DEFAULT_STYLE_CONFIGS = {
    "formel": StyleConfig(
        name="Formel traditionnel",
        formality_level="tres_formel",
        sentence_length_target=25,
        paragraph_length_target=150,
        use_numbering=True,
        numbering_style="numeric",
        common_phrases=[
            "Il convient de relever que",
            "Il résulte de ce qui précède que",
            "Force est de constater que",
            "Il apparaît que",
            "Il en découle que",
            "Au surplus",
            "En tout état de cause",
            "Attendu que",
            "Considérant que",
            "Il échet de préciser que"
        ],
        transition_words=[
            "toutefois", "cependant", "néanmoins", "par ailleurs",
            "en outre", "de plus", "ainsi", "donc", "par conséquent",
            "dès lors", "en effet", "or", "mais", "enfin",
            "d'une part", "d'autre part", "au demeurant", "partant"
        ],
        preferred_conjunctions=[
            "toutefois", "néanmoins", "cependant", "or", "partant"
        ],
        technical_terms_density="high",
        active_voice_preference=0.3,
        citation_style="detailed"
    ),
    
    "moderne": StyleConfig(
        name="Moderne simplifié",
        formality_level="moderne",
        sentence_length_target=15,
        paragraph_length_target=80,
        use_numbering=True,
        numbering_style="dash",
        common_phrases=[
# utils/legal_utils.py
"""
Fonctions utilitaires spécifiques au domaine juridique
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import des types avec gestion d'erreur
try:
    from models.dataclasses import QueryAnalysis
except ImportError:
    try:
        from modules.dataclasses import QueryAnalysis
    except ImportError:
        # Fallback
        class QueryAnalysis:
            def __init__(self, original_query, intent, entities, confidence, details):
                self.original_query = original_query
                self.intent = intent
                self.entities = entities
                self.confidence = confidence
                self.details = details


def extract_legal_references(text: str) -> Dict[str, List[str]]:
    """Extrait les références juridiques d'un texte"""
    references = {
        'articles': [],
        'jurisprudence': [],
        'lois': [],
        'decrets': [],
        'directives': [],
        'reglements': []
    }
    
    # Articles de loi
    article_patterns = [
        r'article\s+[LR]?\s*\d+(?:-\d+)?(?:\s+et\s+[LR]?\s*\d+)*',
        r'articles?\s+\d+(?:\s*,\s*\d+)*\s+(?:du|de\s+la|des)\s+[^,\.\n]+',
        r'art\.\s+\d+(?:-\d+)?',
    ]
    
    for pattern in article_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references['articles'].extend(matches)
    
    # Jurisprudence
    juris_patterns = [
        r'(?:Cass\.|Cour de cassation)[^,\.\n]+\d{4}',
        r'(?:CE|Conseil d\'État)[^,\.\n]+\d{4}',
        r'(?:CA|Cour d\'appel)\s+[^,\.\n]+\d{4}',
        r'(?:TGI|Tribunal de grande instance)[^,\.\n]+\d{4}',
        r'(?:TC|Tribunal de commerce)[^,\.\n]+\d{4}',
        r'CJUE[^,\.\n]+\d{4}',
        r'CEDH[^,\.\n]+\d{4}'
    ]
    
    for pattern in juris_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references['jurisprudence'].extend(matches)
    
    # Lois
    loi_pattern = r'loi\s+(?:n°\s*)?\d{4}-\d+\s+du\s+\d{1,2}\s+\w+\s+\d{4}'
    lois = re.findall(loi_pattern, text, re.IGNORECASE)
    references['lois'] = lois
    
    # Décrets
    decret_pattern = r'décret\s+(?:n°\s*)?\d{4}-\d+\s+du\s+\d{1,2}\s+\w+\s+\d{4}'
    decrets = re.findall(decret_pattern, text, re.IGNORECASE)
    references['decrets'] = decrets
    
    # Directives européennes
    directive_pattern = r'directive\s+\d{4}/\d+/(?:CE|UE)'
    directives = re.findall(directive_pattern, text, re.IGNORECASE)
    references['directives'] = directives
    
    # Règlements européens
    reglement_pattern = r'règlement\s+\(?(?:CE|UE)\)?\s+n°\s*\d+/\d{4}'
    reglements = re.findall(reglement_pattern, text, re.IGNORECASE)
    references['reglements'] = reglements
    
    # Dédupliquer et nettoyer
    for key in references:
        # Dédupliquer
        references[key] = list(set(references[key]))
        # Nettoyer les espaces
        references[key] = [ref.strip() for ref in references[key]]
    
    return references


def analyze_query_intent(query: str) -> QueryAnalysis:
    """Analyse l'intention d'une requête utilisateur"""
    query_lower = query.lower()
    
    # Patterns d'intention
    intent_patterns = {
        'redaction': [
            r'\b(rédiger|créer|écrire|composer|préparer)\b.*\b(conclusions?|plainte|assignation|mémoire|courrier|requête)\b',
            r'\b(conclusions?|plainte|assignation|mémoire)\b.*\b(défense|demandeur)\b'
        ],
        'plaidoirie': [
            r'\b(plaidoirie|plaider|audience|plaidoyer)\b',
            r'\b(préparer|créer).*\b(plaidoirie|argumentation orale)\b'
        ],
        'preparation_client': [
            r'\b(préparer|coaching|entraîner)\b.*\b(client|témoin|partie)\b',
            r'\b(questions?\s*réponses?|Q&A|interrogatoire|audition)\b.*\b(client|préparer)\b'
        ],
        'timeline': [
            r'\b(chronologie|timeline|frise|calendrier)\b',
            r'\b(ordre|séquence)\b.*\b(chronologique|temporel|événements?)\b'
        ],
        'mapping': [
            r'\b(cartographie|carte|mapping|réseau)\b',
            r'\b(relations?|liens?)\b.*\b(entre|sociétés?|personnes?)\b'
        ],
        'comparison': [
            r'\b(comparer|comparaison|différences?|divergences?)\b',
            r'\b(évolution|changements?)\b.*\b(entre|versions?)\b'
        ],
        'analysis': [
            r'\b(analyser|analyse|identifier|évaluer)\b.*\b(risques?|conformité|stratégie)\b',
            r'\b(risques?|dangers?|exposition)\b.*\b(juridiques?|pénaux?)\b'
        ],
        'jurisprudence': [
            r'\b(jurisprudence|arrêts?|décisions?)\b',
            r'\b(rechercher|trouver)\b.*\b(jurisprudence|précédents?)\b'
        ],
        'synthesis': [
            r'\b(synthèse|synthétiser|résumer|résumé)\b',
            r'\b(points?\s+clés?|essentiel|principal)\b'
        ],
        'acte_juridique': [
            r'\b(acte|procédure|document)\s+(?:juridique|judiciaire)\b',
            r'\b(plainte|citation|assignation|constitution)\b',
            r'\b(défense|demandeur|partie civile)\b'
        ]
    }
    
    # Détection de l'intention
    detected_intent = 'search'  # Par défaut
    max_confidence = 0.0
    
    for intent, patterns in intent_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                matches = len(re.findall(pattern, query_lower))
                confidence = min(matches * 0.5, 1.0)
                
                if confidence > max_confidence:
                    detected_intent = intent
                    max_confidence = confidence
                break
    
    # Extraction des entités
    entities = extract_query_entities(query)
    
    # Détails supplémentaires
    details = extract_intent_details(query, detected_intent)
    
    try:
        return QueryAnalysis(
            original_query=query,
            intent=detected_intent,
            entities=entities,
            confidence=max_confidence,
            details=details
        )
    except:
        # Fallback
        return {
            'original_query': query,
            'intent': detected_intent,
            'entities': entities,
            'confidence': max_confidence,
            'details': details
        }


def extract_query_entities(query: str) -> Dict[str, Any]:
    """Extrait les entités d'une requête juridique"""
    entities = {
        'references': [],
        'dates': [],
        'persons': [],
        'organizations': [],
        'document_types': [],
        'legal_terms': [],
        'infractions': [],
        'juridictions': []
    }
    
    # Références @
    references = re.findall(r'@(\w+)', query)
    entities['references'] = references
    
    # Dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b'
    ]
    
    for pattern in date_patterns:
        dates = re.findall(pattern, query, re.IGNORECASE)
        entities['dates'].extend(dates)
    
    # Types de documents juridiques
    doc_types = [
        'conclusions', 'plainte', 'assignation', 'mémoire', 
        'ordonnance', 'jugement', 'arrêt', 'requête',
        'citation', 'procès-verbal', 'expertise', 'rapport'
    ]
    
    for doc_type in doc_types:
        if doc_type in query.lower():
            entities['document_types'].append(doc_type)
    
    # Infractions
    infractions = [
        'abus de biens sociaux', 'escroquerie', 'faux', 
        'blanchiment', 'corruption', 'recel', 'abus de confiance',
        'détournement', 'fraude', 'vol', 'extorsion'
    ]
    
    for infraction in infractions:
        if infraction in query.lower():
            entities['infractions'].append(infraction)
    
    # Juridictions
    juridictions = [
        'tribunal correctionnel', 'cour d\'appel', 'cour de cassation',
        'tribunal de commerce', 'conseil d\'état', 'tribunal administratif',
        'cour d\'assises', 'juge d\'instruction', 'parquet'
    ]
    
    for juridiction in juridictions:
        if juridiction in query.lower():
            entities['juridictions'].append(juridiction)
    
    # Termes juridiques
    legal_terms = extract_legal_terms(query)
    entities['legal_terms'] = legal_terms
    
    # Extraction basique de noms propres
    potential_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
    entities['persons'] = [name for name in potential_names if len(name.split()) >= 2]
    
    return entities


def extract_intent_details(query: str, intent: str) -> Dict[str, Any]:
    """Extrait des détails spécifiques selon l'intention"""
    details = {}
    query_lower = query.lower()
    
    if intent == 'redaction':
        # Type de document
        if 'conclusions' in query_lower:
            details['document_type'] = 'conclusions'
            if 'défense' in query_lower:
                details['partie'] = 'defense'
            elif 'demandeur' in query_lower:
                details['partie'] = 'demandeur'
        elif 'plainte' in query_lower:
            details['document_type'] = 'plainte'
            if 'constitution' in query_lower and 'partie civile' in query_lower:
                details['document_type'] = 'constitution_pc'
        elif 'assignation' in query_lower:
            details['document_type'] = 'assignation'
    
    elif intent == 'acte_juridique':
        # Type d'acte
        if 'plainte' in query_lower:
            details['type_acte'] = 'plainte'
        elif 'citation' in query_lower:
            details['type_acte'] = 'citation_directe'
        elif 'constitution' in query_lower and 'partie civile' in query_lower:
            details['type_acte'] = 'constitution_partie_civile'
        
        # Phase procédurale
        if 'instruction' in query_lower:
            details['phase'] = 'instruction'
        elif 'jugement' in query_lower:
            details['phase'] = 'jugement'
    
    elif intent == 'timeline':
        # Type de chronologie
        if 'faits' in query_lower:
            details['timeline_type'] = 'faits'
        elif 'procédure' in query_lower:
            details['timeline_type'] = 'procedure'
        else:
            details['timeline_type'] = 'complete'
    
    elif intent == 'mapping':
        # Type de cartographie
        if 'société' in query_lower or 'entreprise' in query_lower:
            details['mapping_type'] = 'societes'
        elif 'personne' in query_lower:
            details['mapping_type'] = 'personnes'
        elif 'flux' in query_lower or 'financier' in query_lower:
            details['mapping_type'] = 'flux_financiers'
    
    return details


def extract_legal_terms(text: str) -> List[str]:
    """Extrait les termes juridiques d'un texte"""
    # Liste de termes juridiques courants
    legal_terms_list = [
        'demandeur', 'défendeur', 'partie civile', 'prévenu', 'accusé',
        'magistrat', 'procureur', 'avocat', 'huissier', 'expert',
        'préjudice', 'dommages-intérêts', 'réparation', 'indemnisation',
        'prescription', 'forclusion', 'péremption', 'délai',
        'nullité', 'irrecevabilité', 'incompétence', 'exception',
        'appel', 'pourvoi', 'opposition', 'tierce opposition',
        'mesure conservatoire', 'référé', 'injonction', 'saisie'
    ]
    
    found_terms = []
    text_lower = text.lower()
    
    for term in legal_terms_list:
        if term in text_lower:
            found_terms.append(term)
    
    return found_terms


def format_legal_amount(amount: float, currency: str = "€") -> str:
    """Formate un montant selon les conventions juridiques"""
    # Formater avec espaces comme séparateurs de milliers
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    
    # Ajouter la devise
    if currency == "€":
        return f"{formatted} euros"
    else:
        return f"{formatted} {currency}"


def validate_reference(reference: str) -> bool:
    """Valide le format d'une référence juridique"""
    # Format attendu : lettres, chiffres, tirets, underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, reference))


def categorize_legal_document(content: str) -> str:
    """Catégorise un document juridique selon son contenu"""
    content_lower = content.lower()
    
    # Patterns pour identifier le type
    patterns = {
        'jugement': [r'\bpar ces motifs\b', r'\bcondamne\b', r'\ble tribunal\b'],
        'arrêt': [r'\bla cour\b', r'\bcasse et annule\b', r'\brejette le pourvoi\b'],
        'ordonnance': [r'\bordonnons\b', r'\bréféré\b', r'\bmesure provisoire\b'],
        'conclusions': [r'\bpour ces motifs\b', r'\bplaise au tribunal\b', r'\bconcluant\b'],
        'assignation': [r'\bassignation\b', r'\bà comparaître\b', r'\bdevant le tribunal\b'],
        'plainte': [r'\bporte plainte\b', r'\bfaits suivants\b', r'\binfraction\b'],
        'contrat': [r'\bentre les soussignés\b', r'\bconvenu ce qui suit\b', r'\barticle \d+\b'],
        'procès-verbal': [r'\bconstatons\b', r'\bavons procédé\b', r'\bprocès-verbal\b']
    }
    
    scores = {}
    for doc_type, type_patterns in patterns.items():
        score = 0
        for pattern in type_patterns:
            if re.search(pattern, content_lower):
                score += 1
        if score > 0:
            scores[doc_type] = score
    
    if scores:
        # Retourner le type avec le score le plus élevé
        return max(scores, key=scores.get)
    
    return 'document juridique'


def extract_parties(text: str) -> Dict[str, List[str]]:
    """Extrait les parties d'un document juridique"""
    parties = {
        'demandeurs': [],
        'defendeurs': [],
        'autres': []
    }
    
    # Patterns pour identifier les parties
    patterns = {
        'demandeurs': [
            r'(?:demandeur|requérant|appelant|demandeur)s?\s*:\s*([^,\n]+)',
            r'(?:Monsieur|Madame|La société)\s+([^,\n]+)\s*,?\s*demandeur'
        ],
        'defendeurs': [
            r'(?:défendeur|intimé|défendeur)s?\s*:\s*([^,\n]+)',
            r'(?:Monsieur|Madame|La société)\s+([^,\n]+)\s*,?\s*défendeur'
        ]
    }
    
    for party_type, party_patterns in patterns.items():
        for pattern in party_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            parties[party_type].extend(matches)
    
    # Dédupliquer
    for key in parties:
        parties[key] = list(set(parties[key]))
    
    return parties


def highlight_legal_terms(text: str, terms: List[str] = None) -> str:
    """Surligne les termes juridiques importants dans un texte"""
    if terms is None:
        # Utiliser une liste par défaut de termes importants
        terms = [
            'condamne', 'relaxe', 'prescription', 'nullité',
            'irrecevabilité', 'rejet', 'infraction', 'préjudice'
        ]
    
    highlighted = text
    
    for term in terms:
        # Pattern case-insensitive avec limites de mots
        pattern = rf'\b{re.escape(term)}\b'
        highlighted = re.sub(
            pattern,
            f'**{term}**',
            highlighted,
            flags=re.IGNORECASE
        )
    
    return highlighted
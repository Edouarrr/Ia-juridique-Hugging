# utils/helpers.py
"""Fonctions utilitaires pour l'application juridique"""

import streamlit as st
import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import unicodedata

from modules.dataclasses import QueryAnalysis, Document, Entity

def initialize_session_state():
    """Initialise l'état de la session Streamlit"""
    
    # État principal
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'recherche'
    
    # Documents et données
    if 'azure_documents' not in st.session_state:
        st.session_state.azure_documents = {}
    
    if 'pieces_selectionnees' not in st.session_state:
        st.session_state.pieces_selectionnees = {}
    
    if 'selected_pieces' not in st.session_state:
        st.session_state.selected_pieces = []
    
    # Résultats
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    # Managers (seront initialisés dans app.py)
    if 'azure_blob_manager' not in st.session_state:
        st.session_state.azure_blob_manager = None
    
    if 'azure_search_manager' not in st.session_state:
        st.session_state.azure_search_manager = None
    
    # Templates personnalisés
    if 'saved_templates' not in st.session_state:
        st.session_state.saved_templates = {}
    
    # Préférences utilisateur
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'results_per_page': 20,
            'default_view': 'Compact',
            'auto_jurisprudence': True,
            'create_hyperlinks': True,
            'default_doc_length': 'Très détaillé'
        }

def clean_key(text: str) -> str:
    """Nettoie une chaîne pour l'utiliser comme clé"""
    if not text:
        return ""
    
    # Normaliser les caractères Unicode
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Remplacer les caractères spéciaux
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '_', text)
    
    # Limiter la longueur
    return text[:50]

def generate_document_id(title: str, source: str = "") -> str:
    """Génère un ID unique pour un document"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Créer un hash court du titre
    title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
    
    if source:
        return f"{clean_key(source)}_{title_hash}_{timestamp}"
    else:
        return f"doc_{title_hash}_{timestamp}"

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
        'import': [
            r'\b(importer|charger|upload|télécharger)\b.*\b(documents?|fichiers?)\b',
            r'\b(ajouter|intégrer)\b.*\b(documents?|pièces?)\b'
        ],
        'export': [
            r'\b(exporter|télécharger|download|sauvegarder)\b',
            r'\b(format|convertir)\b.*\b(word|pdf|excel)\b'
        ],
        'email': [
            r'\b(envoyer|email|mail|courrier électronique)\b',
            r'\b(partager|transmettre)\b.*\b(par\s+mail|email)\b'
        ],
        'synthesis': [
            r'\b(synthèse|synthétiser|résumer|résumé)\b',
            r'\b(points?\s+clés?|essentiel|principal)\b'
        ],
        'piece_selection': [
            r'\b(sélectionner|choisir|trier)\b.*\b(pièces?|documents?)\b',
            r'\b(pièces?)\b.*\b(pertinentes?|importantes?)\b'
        ],
        'bordereau': [
            r'\b(bordereau|liste)\b.*\b(pièces?|communication)\b',
            r'\b(créer|générer)\b.*\bordereau\b'
        ],
        'template': [
            r'\b(template|modèle|gabarit)\b',
            r'\b(utiliser|appliquer|créer)\b.*\b(template|modèle)\b'
        ]
    }
    
    # Détection de l'intention
    detected_intent = 'search'  # Par défaut
    max_confidence = 0.0
    
    for intent, patterns in intent_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                # Calculer un score de confiance basique
                matches = len(re.findall(pattern, query_lower))
                confidence = min(matches * 0.5, 1.0)
                
                if confidence > max_confidence:
                    detected_intent = intent
                    max_confidence = confidence
                break
    
    # Extraction des entités
    entities = extract_query_entities(query)
    
    # Détails supplémentaires selon l'intention
    details = extract_intent_details(query, detected_intent)
    
    return QueryAnalysis(
        original_query=query,
        intent=detected_intent,
        entities=entities,
        confidence=max_confidence,
        details=details
    )

def extract_query_entities(query: str) -> Dict[str, Any]:
    """Extrait les entités d'une requête"""
    
    entities = {
        'references': [],
        'dates': [],
        'persons': [],
        'organizations': [],
        'document_types': [],
        'legal_terms': []
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
    
    # Types de documents
    doc_types = ['conclusions', 'plainte', 'assignation', 'mémoire', 'ordonnance', 'jugement', 'arrêt']
    for doc_type in doc_types:
        if doc_type in query.lower():
            entities['document_types'].append(doc_type)
    
    # Termes juridiques
    legal_terms = ['abus de biens sociaux', 'escroquerie', 'faux', 'blanchiment', 'corruption']
    for term in legal_terms:
        if term in query.lower():
            entities['legal_terms'].append(term)
    
    # Extraction basique de noms propres (majuscules)
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
        
        # Infractions
        infractions = ['abus de biens sociaux', 'escroquerie', 'faux', 'blanchiment']
        for infraction in infractions:
            if infraction in query_lower:
                details['infraction'] = infraction
                break
    
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
        else:
            details['mapping_type'] = 'complete'
    
    elif intent == 'import':
        # Types de fichiers
        file_types = []
        if 'pdf' in query_lower:
            file_types.append('pdf')
        if 'word' in query_lower or 'docx' in query_lower:
            file_types.append('docx')
        if 'excel' in query_lower or 'xlsx' in query_lower:
            file_types.append('xlsx')
        
        details['file_types'] = file_types if file_types else ['pdf', 'docx', 'txt']
    
    elif intent == 'export':
        # Format d'export
        if 'word' in query_lower or 'docx' in query_lower:
            details['format'] = 'docx'
        elif 'pdf' in query_lower:
            details['format'] = 'pdf'
        elif 'excel' in query_lower:
            details['format'] = 'xlsx'
        else:
            details['format'] = 'docx'
    
    return details

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extrait les entités d'un texte (personnes, organisations, lieux)"""
    
    entities = {
        'persons': [],
        'organizations': [],
        'locations': [],
        'dates': []
    }
    
    # Extraction simple basée sur des patterns
    # Personnes (noms propres composés)
    person_pattern = r'\b(?:M\.|Mme|Me|Dr|Pr)?\.?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
    potential_persons = re.findall(person_pattern, text)
    
    # Filtrer les faux positifs courants
    false_positives = ['La République', 'Le Tribunal', 'La Cour', 'Le Ministère']
    entities['persons'] = [p for p in potential_persons if p not in false_positives]
    
    # Organisations (mots en majuscules, acronymes)
    org_patterns = [
        r'\b[A-Z]{2,}\b',  # Acronymes
        r'\bSociété\s+[A-Z]\w+(?:\s+[A-Z]\w+)*\b',  # Société X
        r'\b(?:SARL|SAS|SA|EURL|SCI)\s+[A-Z]\w+\b'  # Formes juridiques
    ]
    
    for pattern in org_patterns:
        orgs = re.findall(pattern, text)
        entities['organizations'].extend(orgs)
    
    # Lieux
    location_pattern = r'\b(?:à|de|en)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
    potential_locations = re.findall(location_pattern, text)
    entities['locations'] = list(set(potential_locations))
    
    # Dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b'
    ]
    
    for pattern in date_patterns:
        dates = re.findall(pattern, text, re.IGNORECASE)
        entities['dates'].extend(dates)
    
    # Dédupliquer
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return entities

def extract_dates(text: str) -> List[Dict[str, Any]]:
    """Extrait les dates d'un texte avec leur contexte"""
    
    dates = []
    
    # Patterns pour différents formats de dates
    date_patterns = [
        # Format JJ/MM/AAAA ou JJ-MM-AAAA
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', 'dmy'),
        # Format AAAA/MM/JJ ou AAAA-MM-JJ
        (r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b', 'ymd'),
        # Format JJ mois AAAA
        (r'\b(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})\b', 'dmy_text'),
        # Format mois AAAA
        (r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})\b', 'my_text')
    ]
    
    months_fr = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
    }
    
    for pattern, format_type in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                if format_type == 'dmy':
                    day, month, year = match.groups()
                    date_obj = datetime(int(year), int(month), int(day))
                
                elif format_type == 'ymd':
                    year, month, day = match.groups()
                    date_obj = datetime(int(year), int(month), int(day))
                
                elif format_type == 'dmy_text':
                    day, month_text, year = match.groups()
                    month = months_fr.get(month_text.lower(), 1)
                    date_obj = datetime(int(year), month, int(day))
                
                elif format_type == 'my_text':
                    month_text, year = match.groups()
                    month = months_fr.get(month_text.lower(), 1)
                    date_obj = datetime(int(year), month, 1)
                
                # Extraire le contexte (50 caractères avant et après)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                dates.append({
                    'date': date_obj,
                    'text': match.group(0),
                    'context': context,
                    'position': match.start()
                })
                
            except (ValueError, KeyError):
                # Ignorer les dates invalides
                continue
    
    # Trier par date
    dates.sort(key=lambda x: x['date'])
    
    return dates

def format_legal_date(date: Union[datetime, str], include_day_name: bool = False) -> str:
    """Formate une date au format juridique français"""
    
    if isinstance(date, str):
        # Essayer de parser la date
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                date = datetime.strptime(date, fmt)
                break
            except:
                continue
        else:
            # Si le parsing échoue, retourner la chaîne originale
            return date
    
    if isinstance(date, datetime):
        months = [
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
        ]
        
        days = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        
        if include_day_name:
            day_name = days[date.weekday()]
            return f"{day_name} {date.day} {months[date.month - 1]} {date.year}"
        else:
            return f"{date.day} {months[date.month - 1]} {date.year}"
    
    return str(date)

def format_date(date: Union[datetime, str], format: str = "%d/%m/%Y") -> str:
    """Formate une date de manière cohérente"""
    
    if isinstance(date, str):
        # Essayer de parser la date
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                date = datetime.strptime(date, fmt)
                break
            except:
                continue
        else:
            return date  # Retourner tel quel si parsing échoue
    
    if isinstance(date, datetime):
        return date.strftime(format)
    
    return str(date)

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calcule la similarité entre deux textes (0-1)"""
    
    # Normaliser les textes
    text1_lower = text1.lower().strip()
    text2_lower = text2.lower().strip()
    
    # Si identiques
    if text1_lower == text2_lower:
        return 1.0
    
    # Tokenizer simple
    words1 = set(text1_lower.split())
    words2 = set(text2_lower.split())
    
    # Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def extract_section(text: str, section_title: str) -> Optional[str]:
    """Extrait une section spécifique d'un texte"""
    
    # Patterns pour identifier le début d'une section
    patterns = [
        rf"(?:^|\n)\s*{re.escape(section_title)}\s*:?\s*\n",
        rf"(?:^|\n)\s*\*\*{re.escape(section_title)}\*\*\s*:?\s*\n",
        rf"(?:^|\n)\s*#{1,3}\s*{re.escape(section_title)}\s*\n"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            start = match.end()
            
            # Trouver la fin de la section (prochaine section ou fin du texte)
            next_section = re.search(r'\n\s*(?:\*\*[A-Z]|\#{1,3}\s*[A-Z]|^[A-Z][A-Z\s]+:)', text[start:], re.MULTILINE)
            
            if next_section:
                end = start + next_section.start()
            else:
                end = len(text)
            
            return text[start:end].strip()
    
    return None

def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:
    """Divise un texte en chunks avec overlap"""
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Trouver la fin du chunk
        end = start + chunk_size
        
        # Si on n'est pas à la fin, essayer de couper à une phrase
        if end < len(text):
            # Chercher la fin de phrase la plus proche
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start:
                end = sentence_end + 1
        
        chunks.append(text[start:end])
        
        # Prochain chunk avec overlap
        start = end - overlap
    
    return chunks

def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour le rendre sûr"""
    
    # Remplacer les caractères interdits
    forbidden_chars = '<>:"/\\|?*'
    for char in forbidden_chars:
        filename = filename.replace(char, '_')
    
    # Limiter la longueur
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}.{ext}" if ext else name

def format_file_size(size_bytes: int) -> str:
    """Formate une taille de fichier en unité lisible"""
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

def is_valid_email(email: str) -> bool:
    """Vérifie si une adresse email est valide"""
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_summary(text: str, max_length: int = 500) -> str:
    """Génère un résumé simple d'un texte"""
    
    if len(text) <= max_length:
        return text
    
    # Prendre le début jusqu'à la dernière phrase complète
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    
    if last_period > max_length * 0.8:  # Si on trouve un point pas trop tôt
        return truncated[:last_period + 1]
    else:
        return truncated + "..."

def merge_documents(docs: List[Document], separator: str = "\n\n---\n\n") -> Document:
    """Fusionne plusieurs documents en un seul"""
    
    if not docs:
        raise ValueError("Aucun document à fusionner")
    
    if len(docs) == 1:
        return docs[0]
    
    # Fusionner les contenus
    merged_content = separator.join(doc.content for doc in docs)
    
    # Fusionner les métadonnées
    merged_metadata = {
        'merged_from': [doc.id for doc in docs],
        'merge_date': datetime.now().isoformat(),
        'document_count': len(docs)
    }
    
    # Fusionner les tags
    all_tags = []
    for doc in docs:
        all_tags.extend(doc.tags)
    unique_tags = list(set(all_tags))
    
    # Créer le document fusionné
    merged_doc = Document(
        id=generate_document_id("Document fusionné", "merge"),
        title=f"Fusion de {len(docs)} documents",
        content=merged_content,
        source="Fusion",
        metadata=merged_metadata,
        tags=unique_tags
    )
    
    return merged_doc

def extract_legal_references(text: str) -> Dict[str, List[str]]:
    """Extrait les références juridiques d'un texte"""
    
    references = {
        'articles': [],
        'jurisprudence': [],
        'lois': []
    }
    
    # Articles de loi
    article_patterns = [
        r'article\s+[LR]?\s*\d+(?:-\d+)?(?:\s+et\s+[LR]?\s*\d+)*',
        r'articles?\s+\d+(?:\s*,\s*\d+)*\s+(?:du|de\s+la|des)\s+[^,\.\n]+',
    ]
    
    for pattern in article_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references['articles'].extend(matches)
    
    # Jurisprudence
    juris_patterns = [
        r'(?:Cass\.|Cour de cassation)[^,\.\n]+\d{4}',
        r'(?:CE|Conseil d\'État)[^,\.\n]+\d{4}',
        r'(?:CA|Cour d\'appel)\s+[^,\.\n]+\d{4}'
    ]
    
    for pattern in juris_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references['jurisprudence'].extend(matches)
    
    # Lois
    loi_pattern = r'loi\s+(?:n°\s*)?\d{4}-\d+\s+du\s+\d{1,2}\s+\w+\s+\d{4}'
    lois = re.findall(loi_pattern, text, re.IGNORECASE)
    references['lois'] = lois
    
    # Dédupliquer
    for key in references:
        references[key] = list(set(references[key]))
    
    return references

def highlight_text(text: str, keywords: List[str], color: str = "yellow") -> str:
    """Surligne des mots-clés dans un texte (HTML)"""
    
    if not keywords:
        return text
    
    # Échapper les caractères spéciaux HTML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Surligner chaque mot-clé
    for keyword in keywords:
        if keyword:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            text = pattern.sub(f'<mark style="background-color: {color};">{keyword}</mark>', text)
    
    return text

def create_breadcrumb(path: List[str]) -> str:
    """Crée un fil d'Ariane à partir d'un chemin"""
    
    if not path:
        return ""
    
    parts = []
    for i, part in enumerate(path):
        if i < len(path) - 1:
            parts.append(f"{part} >")
        else:
            parts.append(f"**{part}**")
    
    return " ".join(parts)

def calculate_read_time(text: str, words_per_minute: int = 200) -> int:
    """Calcule le temps de lecture estimé en minutes"""
    
    word_count = len(text.split())
    read_time = word_count / words_per_minute
    
    # Arrondir au supérieur
    return max(1, int(read_time + 0.5))

def get_file_icon(filename: str) -> str:
    """Retourne l'icône appropriée selon l'extension du fichier"""
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    icons = {
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'txt': '📃',
        'xlsx': '📊',
        'xls': '📊',
        'csv': '📊',
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'zip': '📦',
        'rar': '📦'
    }
    
    return icons.get(ext, '📎')

def format_duration(seconds: int) -> str:
    """Formate une durée en format lisible"""
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"

def validate_reference(reference: str) -> bool:
    """Valide le format d'une référence juridique"""
    
    # Format attendu : lettres, chiffres, tirets, underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, reference))

def extract_monetary_amounts(text: str) -> List[Dict[str, Any]]:
    """Extrait les montants monétaires d'un texte"""
    
    amounts = []
    
    # Patterns pour différents formats
    patterns = [
        (r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€', 'EUR'),
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$', 'USD'),
        (r'€\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', 'EUR'),
        (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD')
    ]
    
    for pattern, currency in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            amount_str = match.group(1)
            
            # Convertir en nombre
            try:
                # Normaliser le format
                amount_str = amount_str.replace('.', '').replace(',', '.')
                amount = float(amount_str)
                
                amounts.append({
                    'amount': amount,
                    'currency': currency,
                    'text': match.group(0),
                    'position': match.start()
                })
            except ValueError:
                continue
    
    return amounts

def normalize_whitespace(text: str) -> str:
    """Normalise les espaces dans un texte"""
    
    # Remplacer les espaces multiples par un seul
    text = re.sub(r'\s+', ' ', text)
    
    # Supprimer les espaces en début/fin de ligne
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    
    # Reconstruire avec des sauts de ligne simples
    return '\n'.join(lines)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale.
    
    Args:
        text: Le texte à tronquer
        max_length: La longueur maximale (par défaut 100)
        suffix: Le suffixe à ajouter (par défaut "...")
        
    Returns:
        Le texte tronqué
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Calculer la longueur disponible pour le texte
    available_length = max_length - len(suffix)
    
    if available_length <= 0:
        return suffix
    
    # Tronquer et ajouter le suffixe
    return text[:available_length] + suffix
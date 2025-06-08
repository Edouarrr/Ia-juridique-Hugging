# utils/helpers.py
"""Fonctions utilitaires pour l'application juridique"""

import re
import unicodedata
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import hashlib
import base64
import json
import os
from pathlib import Path

def clean_key(text: str) -> str:
    """Nettoie une chaîne pour en faire une clé valide"""
    if not text:
        return ""
    
    # Supprimer les accents
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
    
    # Remplacer les espaces et caractères spéciaux par des underscores
    text = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    
    # Supprimer les underscores multiples
    text = re.sub(r'_+', '_', text)
    
    # Supprimer les underscores au début et à la fin
    text = text.strip('_')
    
    # Limiter la longueur
    if len(text) > 64:
        text = text[:64]
    
    # S'assurer qu'il n'est pas vide
    if not text:
        text = "key_" + hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
    
    return text.lower()

def extract_date(text: str) -> Optional[datetime]:
    """Extrait une date d'un texte"""
    # Patterns de dates courants
    date_patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%d/%m/%Y'),
        (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '%d.%m.%Y'),
        (r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})', None),
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y-%m-%d'),
    ]
    
    # Mapping des mois français
    mois_fr = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
    }
    
    for pattern, date_format in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if date_format:
                try:
                    return datetime.strptime(match.group(0), date_format)
                except ValueError:
                    continue
            else:
                # Format avec mois en français
                try:
                    day = int(match.group(1))
                    month = mois_fr.get(match.group(2).lower())
                    year = int(match.group(3))
                    if month:
                        return datetime(year, month, day)
                except (ValueError, AttributeError):
                    continue
    
    return None

def extract_dates(text: str) -> List[Tuple[datetime, str]]:
    """Extrait toutes les dates d'un texte avec leur contexte"""
    dates = []
    sentences = text.split('.')
    
    for sentence in sentences:
        date = extract_date(sentence)
        if date:
            # Nettoyer le contexte
            context = sentence.strip()
            if len(context) > 200:
                context = context[:200] + "..."
            dates.append((date, context))
    
    # Trier par date
    dates.sort(key=lambda x: x[0])
    
    return dates

def extract_amounts(text: str) -> List[Tuple[float, str]]:
    """Extrait les montants monétaires d'un texte"""
    amounts = []
    
    # Patterns pour les montants
    amount_patterns = [
        r'(\d{1,3}(?:\s?\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
        r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
        r'(\d+(?:,\d{2})?)\s*(?:€|EUR|euros?)',
    ]
    
    for pattern in amount_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amount_str = match.group(1)
            # Normaliser le format
            amount_str = amount_str.replace(' ', '').replace('.', '')
            amount_str = amount_str.replace(',', '.')
            
            try:
                amount = float(amount_str)
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                amounts.append((amount, context))
            except ValueError:
                continue
    
    # Dédupliquer et trier
    amounts = list(set(amounts))
    amounts.sort(key=lambda x: x[0], reverse=True)
    
    return amounts

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extrait les entités nommées d'un texte"""
    entities = {
        'persons': [],
        'organizations': [],
        'locations': [],
        'dates': [],
        'amounts': [],
        'legal_refs': []
    }
    
    # Personnes (patterns simples)
    # Noms propres (2-3 mots commençant par majuscule)
    person_pattern = r'\b([A-Z][a-zàâäéèêëïîôùûç]+ (?:[A-Z][a-zàâäéèêëïîôùûç]+ ?){0,2})\b'
    persons = re.findall(person_pattern, text)
    entities['persons'] = list(set(persons))
    
    # Organisations (SA, SARL, SAS, etc.)
    org_pattern = r'\b([A-Z][A-Za-zàâäéèêëïîôùûç\-]+(?: [A-Z][A-Za-zàâäéèêëïîôùûç\-]+)*)\s*(?:SA|SARL|SAS|SCI|EURL|GIE|S\.A\.|S\.A\.R\.L\.|S\.A\.S\.)\b'
    orgs = re.findall(org_pattern, text)
    entities['organizations'] = list(set(orgs))
    
    # Lieux (villes, adresses)
    location_keywords = ['rue', 'avenue', 'boulevard', 'place', 'Paris', 'Lyon', 'Marseille']
    for keyword in location_keywords:
        pattern = rf'\b(\d+\s+)?{keyword}\s+[A-Z][a-zàâäéèêëïîôùûç\-]+(?:\s+[A-Z]?[a-zàâäéèêëïîôùûç\-]+)*\b'
        locations = re.findall(pattern, text, re.IGNORECASE)
        entities['locations'].extend(locations)
    
    entities['locations'] = list(set(entities['locations']))
    
    # Dates
    dates = extract_dates(text)
    entities['dates'] = [date[0].strftime('%d/%m/%Y') for date in dates]
    
    # Montants
    amounts = extract_amounts(text)
    entities['amounts'] = [f"{amount[0]:,.2f} €" for amount in amounts]
    
    # Références juridiques
    legal_refs = extract_legal_references(text)
    entities['legal_refs'] = legal_refs
    
    return entities

def extract_legal_references(text: str) -> List[str]:
    """Extrait les références juridiques (articles, jurisprudence)"""
    references = []
    
    # Articles de loi
    article_patterns = [
        r'articles?\s+L\.?\s*\d+(?:-\d+)?(?:\s+et\s+L\.?\s*\d+(?:-\d+)?)*',
        r'articles?\s+R\.?\s*\d+(?:-\d+)?(?:\s+et\s+R\.?\s*\d+(?:-\d+)?)*',
        r'articles?\s+\d+(?:-\d+)?(?:\s+et\s+\d+(?:-\d+)?)*\s+du\s+code\s+\w+',
        r'articles?\s+\d+(?:-\d+)?(?:\s+(?:et|à)\s+\d+(?:-\d+)?)*',
    ]
    
    for pattern in article_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references.extend(matches)
    
    # Jurisprudence
    juris_patterns = [
        r'Cass\.?\s*(?:civ\.|crim\.|com\.|soc\.)?,?\s*\d{1,2}\s+\w+\s+\d{4}',
        r'C\.?\s*cass\.?,?\s*\d{1,2}\s+\w+\s+\d{4}',
        r'CA\s+[A-Z][a-z]+,?\s*\d{1,2}\s+\w+\s+\d{4}',
        r'CE,?\s*\d{1,2}\s+\w+\s+\d{4}',
        r'Cons\.\s*const\.,?\s*\d{1,2}\s+\w+\s+\d{4}',
    ]
    
    for pattern in juris_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references.extend(matches)
    
    return list(set(references))

def format_legal_date(date: datetime) -> str:
    """Formate une date au format juridique français"""
    mois = [
        'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
    ]
    
    return f"{date.day} {mois[date.month - 1]} {date.year}"

def generate_document_id(prefix: str = "doc") -> str:
    """Génère un ID unique pour un document"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    random_part = hashlib.md5(os.urandom(16)).hexdigest()[:8]
    return f"{prefix}_{timestamp}_{random_part}"

def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Calcule le temps de lecture estimé en minutes"""
    word_count = len(text.split())
    return max(1, round(word_count / words_per_minute))

def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Tronque un texte en préservant les mots complets"""
    if len(text) <= max_length:
        return text
    
    # Trouver le dernier espace avant la limite
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix

def highlight_text(text: str, terms: List[str], tag: str = "mark") -> str:
    """Surligne des termes dans un texte"""
    if not terms:
        return text
    
    # Échapper les caractères spéciaux regex
    escaped_terms = [re.escape(term) for term in terms]
    pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'
    
    def replace_func(match):
        return f'<{tag}>{match.group(0)}</{tag}>'
    
    return re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

def extract_section(content: str, section_title: str) -> Optional[str]:
    """Extrait une section spécifique d'un document"""
    # Patterns pour identifier les sections
    patterns = [
        rf'^{re.escape(section_title)}.*?(?=^[IVX]+\.|^[A-Z]\.|$)',
        rf'^[IVX]+\.\s*{re.escape(section_title)}.*?(?=^[IVX]+\.|$)',
        rf'^[A-Z]\.\s*{re.escape(section_title)}.*?(?=^[A-Z]\.|^[IVX]+\.|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return None

def normalize_whitespace(text: str) -> str:
    """Normalise les espaces dans un texte"""
    # Remplacer les espaces multiples par un seul
    text = re.sub(r'\s+', ' ', text)
    # Supprimer les espaces en début et fin de ligne
    lines = [line.strip() for line in text.split('\n')]
    # Rejoindre en préservant les sauts de ligne significatifs
    return '\n'.join(line for line in lines if line)

def create_summary(text: str, max_sentences: int = 3) -> str:
    """Crée un résumé simple basé sur les premières phrases"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text
    
    summary = '. '.join(sentences[:max_sentences])
    if not summary.endswith('.'):
        summary += '.'
    
    return summary

def format_file_size(size_bytes: int) -> str:
    """Formate une taille de fichier en unités lisibles"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def is_valid_email(email: str) -> bool:
    """Vérifie si une adresse email est valide"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour le rendre sûr"""
    # Remplacer les caractères interdits
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limiter la longueur
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    return name + ext

def parse_reference(reference: str) -> Dict[str, str]:
    """Parse une référence juridique"""
    result = {
        'type': 'unknown',
        'jurisdiction': '',
        'date': '',
        'number': '',
        'full': reference
    }
    
    # Cour de cassation
    if re.search(r'Cass\.?|C\.\s*cass\.?', reference, re.IGNORECASE):
        result['type'] = 'cassation'
        result['jurisdiction'] = 'Cour de cassation'
        
        # Extraire la chambre
        chamber = re.search(r'(civ\.|crim\.|com\.|soc\.)', reference, re.IGNORECASE)
        if chamber:
            result['chamber'] = chamber.group(1)
    
    # Cour d'appel
    elif re.search(r'CA\s+', reference, re.IGNORECASE):
        result['type'] = 'appel'
        city = re.search(r'CA\s+([A-Z][a-z]+)', reference)
        if city:
            result['jurisdiction'] = f"CA {city.group(1)}"
    
    # Date
    date = extract_date(reference)
    if date:
        result['date'] = date.strftime('%d/%m/%Y')
    
    return result

def detect_language(text: str) -> str:
    """Détecte la langue d'un texte (basique)"""
    # Mots français courants
    fr_words = ['le', 'de', 'un', 'et', 'la', 'les', 'des', 'que', 'pour', 'dans']
    # Mots anglais courants
    en_words = ['the', 'of', 'and', 'to', 'in', 'is', 'it', 'that', 'for', 'with']
    
    text_lower = text.lower()
    text_words = text_lower.split()
    
    fr_count = sum(1 for word in text_words if word in fr_words)
    en_count = sum(1 for word in text_words if word in en_words)
    
    if fr_count > en_count:
        return 'fr'
    elif en_count > fr_count:
        return 'en'
    else:
        return 'unknown'

def merge_documents(docs: List[Dict[str, Any]], separator: str = "\n\n---\n\n") -> str:
    """Fusionne plusieurs documents en un seul texte"""
    merged = []
    
    for doc in docs:
        header = f"# {doc.get('title', 'Sans titre')}\n"
        if doc.get('date'):
            header += f"Date: {doc['date']}\n"
        if doc.get('source'):
            header += f"Source: {doc['source']}\n"
        
        content = doc.get('content', '')
        merged.append(header + "\n" + content)
    
    return separator.join(merged)

def calculate_similarity(text1: str, text2: str) -> float:
    """Calcule la similarité entre deux textes (méthode basique)"""
    # Tokenisation simple
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Coefficient de Jaccard
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def extract_questions(text: str) -> List[str]:
    """Extrait les questions d'un texte"""
    # Patterns pour les questions
    sentences = re.split(r'[.!?]+', text)
    questions = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        # Vérifier si c'est une question
        if sentence and ('?' in sentence or 
                        sentence.lower().startswith(('qui', 'que', 'quoi', 'quand', 
                                                    'où', 'comment', 'pourquoi', 
                                                    'est-ce', 'combien'))):
            if not sentence.endswith('?'):
                sentence += '?'
            questions.append(sentence)
    
    return questions

def format_duration(minutes: int) -> str:
    """Formate une durée en heures et minutes"""
    if minutes < 60:
        return f"{minutes} minutes"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if mins == 0:
        return f"{hours} heure{'s' if hours > 1 else ''}"
    else:
        return f"{hours}h{mins:02d}"

def extract_phone_numbers(text: str) -> List[str]:
    """Extrait les numéros de téléphone"""
    # Pattern pour les numéros français
    pattern = r'(?:(?:\+33|0)\s?[1-9](?:\s?\d{2}){4})'
    phones = re.findall(pattern, text)
    
    # Normaliser
    normalized = []
    for phone in phones:
        # Supprimer les espaces
        phone = re.sub(r'\s', '', phone)
        # Format standard
        if phone.startswith('+33'):
            phone = '0' + phone[3:]
        # Ajouter les espaces
        if len(phone) == 10:
            phone = ' '.join([phone[i:i+2] for i in range(0, 10, 2)])
        normalized.append(phone)
    
    return list(set(normalized))

def create_safe_dict(data: Any) -> Dict[str, Any]:
    """Crée un dictionnaire sûr à partir de données potentiellement invalides"""
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k and isinstance(k, str)}
    elif hasattr(data, '__dict__'):
        return create_safe_dict(data.__dict__)
    else:
        return {}

def format_percentage(value: float, decimals: int = 1) -> str:
    """Formate un pourcentage"""
    return f"{value * 100:.{decimals}f}%"

def generate_unique_id(prefix: str = "") -> str:
    """Génère un ID unique"""
    timestamp = int(datetime.now().timestamp() * 1000000)
    random_part = hashlib.md5(os.urandom(16)).hexdigest()[:6]
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}"
    else:
        return f"{timestamp}_{random_part}"

# Fonctions de validation
def validate_document(doc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valide un document et retourne les erreurs"""
    errors = []
    
    if not doc.get('title'):
        errors.append("Le titre est requis")
    
    if not doc.get('content'):
        errors.append("Le contenu est requis")
    elif len(doc['content']) < 10:
        errors.append("Le contenu est trop court")
    
    if not doc.get('source'):
        errors.append("La source est requise")
    
    return len(errors) == 0, errors

def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extrait les métadonnées d'un fichier"""
    metadata = {}
    
    try:
        stat = os.stat(file_path)
        metadata['size'] = stat.st_size
        metadata['created'] = datetime.fromtimestamp(stat.st_ctime)
        metadata['modified'] = datetime.fromtimestamp(stat.st_mtime)
        metadata['extension'] = os.path.splitext(file_path)[1]
    except Exception:
        pass
    
    return metadata
# utils/text_processing.py
"""
Fonctions de traitement de texte
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple


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
    """Tronque un texte à une longueur maximale"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    available_length = max_length - len(suffix)
    if available_length <= 0:
        return suffix
    
    return text[:available_length] + suffix


def extract_section(text: str, section_title: str) -> Optional[str]:
    """Extrait une section spécifique d'un texte"""
    patterns = [
        rf"(?:^|\n)\s*{re.escape(section_title)}\s*:?\s*\n",
        rf"(?:^|\n)\s*\*\*{re.escape(section_title)}\*\*\s*:?\s*\n",
        rf"(?:^|\n)\s*#{1,3}\s*{re.escape(section_title)}\s*\n"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            start = match.end()
            
            # Trouver la fin de la section
            next_section = re.search(
                r'\n\s*(?:\*\*[A-Z]|\#{1,3}\s*[A-Z]|^[A-Z][A-Z\s]+:)', 
                text[start:], 
                re.MULTILINE
            )
            
            end = start + next_section.start() if next_section else len(text)
            return text[start:end].strip()
    
    return None


def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:
    """Divise un texte en chunks avec overlap"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Essayer de couper à une phrase
        if end < len(text):
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start:
                end = sentence_end + 1
        
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calcule la similarité entre deux textes (0-1)"""
    # Normaliser
    text1_lower = text1.lower().strip()
    text2_lower = text2.lower().strip()
    
    if text1_lower == text2_lower:
        return 1.0
    
    # Tokenizer simple
    words1 = set(text1_lower.split())
    words2 = set(text2_lower.split())
    
    # Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def highlight_text(text: str, keywords: List[str], color: str = "yellow") -> str:
    """Surligne des mots-clés dans un texte (HTML)"""
    if not keywords:
        return text
    
    # Échapper les caractères HTML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Surligner chaque mot-clé
    for keyword in keywords:
        if keyword:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            text = pattern.sub(
                f'<mark style="background-color: {color};">{keyword}</mark>', 
                text
            )
    
    return text


def extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
    """Extrait les phrases clés d'un texte"""
    sentences = text.split('.')
    key_phrases = []
    
    for sentence in sentences[:max_phrases * 2]:  # Prendre plus pour filtrer
        sentence = sentence.strip()
        # Phrases significatives (ni trop courtes, ni trop longues)
        if 20 < len(sentence) < 200:
            key_phrases.append(sentence + '.')
    
    return key_phrases[:max_phrases]


def generate_summary(text: str, max_length: int = 500) -> str:
    """Génère un résumé simple d'un texte"""
    if len(text) <= max_length:
        return text
    
    # Prendre le début jusqu'à la dernière phrase complète
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    
    if last_period > max_length * 0.8:
        return truncated[:last_period + 1]
    else:
        return truncated + "..."


def calculate_read_time(text: str, words_per_minute: int = 200) -> int:
    """Calcule le temps de lecture estimé en minutes"""
    word_count = len(text.split())
    read_time = word_count / words_per_minute
    
    return max(1, int(read_time + 0.5))


def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extrait les entités d'un texte (personnes, organisations, lieux)"""
    entities = {
        'persons': [],
        'organizations': [],
        'locations': [],
        'dates': []
    }
    
    # Personnes (noms propres composés)
    person_pattern = r'\b(?:M\.|Mme|Me|Dr|Pr)?\.?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
    potential_persons = re.findall(person_pattern, text)
    
    # Filtrer les faux positifs
    false_positives = ['La République', 'Le Tribunal', 'La Cour', 'Le Ministère']
    entities['persons'] = [p for p in potential_persons if p not in false_positives]
    
    # Organisations
    org_patterns = [
        r'\b[A-Z]{2,}\b',  # Acronymes
        r'\bSociété\s+[A-Z]\w+(?:\s+[A-Z]\w+)*\b',
        r'\b(?:SARL|SAS|SA|EURL|SCI)\s+[A-Z]\w+\b'
    ]
    
    for pattern in org_patterns:
        orgs = re.findall(pattern, text)
        entities['organizations'].extend(orgs)
    
    # Lieux
    location_pattern = r'\b(?:à|de|en)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
    entities['locations'] = list(set(re.findall(location_pattern, text)))
    
    # Dédupliquer
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return entities


def extract_monetary_amounts(text: str) -> List[Dict[str, Any]]:
    """Extrait les montants monétaires d'un texte"""
    amounts = []
    
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


def clean_legal_text(text: str) -> str:
    """Nettoie un texte juridique en préservant la mise en forme"""
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    # Corriger la ponctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])(\w)', r'\1 \2', text)
    
    # Corriger les guillemets
    text = re.sub(r'"\s*([^"]+)\s*"', r'« \1 »', text)
    
    # Préserver les sauts de paragraphe
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()


def format_legal_citations(text: str) -> str:
    """Formate les citations juridiques selon les conventions"""
    patterns = [
        # Cour de cassation
        (r'\bCass\.?\s*', 'Cass. '),
        (r'\b(civ|crim|com|soc)\.?\s*(\d)', r'\1. \2'),
        
        # Conseil d'État
        (r'\bCE\b', 'CE'),
        (r'\bConseil d\'Etat\b', 'Conseil d\'État'),
        
        # Articles
        (r'\bart\.?\s*', 'art. '),
        (r'\barticles?\s+', 'art. '),
        
        # Autres
        (r'\bc\.\s*', 'c. '),  # contre
        (r'\bp\.\s*', 'p. '),  # page
        (r'\bn°\s*', 'n° '),  # numéro
    ]
    
    formatted_text = text
    for pattern, replacement in patterns:
        formatted_text = re.sub(pattern, replacement, formatted_text, flags=re.IGNORECASE)
    
    return formatted_text
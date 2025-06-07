# utils/helpers.py
"""Fonctions utilitaires pour l'application"""

import re
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
import hashlib
import unicodedata
from html.parser import HTMLParser

def format_date(date_obj: Union[datetime, date, str], format: str = "%d/%m/%Y") -> str:
    """Formate une date selon le format spécifié"""
    if isinstance(date_obj, str):
        # Essayer de parser la string
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
        except:
            try:
                date_obj = datetime.strptime(date_obj, "%d/%m/%Y")
            except:
                return date_obj  # Retourner tel quel si parsing impossible
    
    if isinstance(date_obj, (datetime, date)):
        return date_obj.strftime(format)
    return str(date_obj)

def format_currency(amount: float, currency: str = "€", decimal_places: int = 2) -> str:
    """Formate un montant en devise"""
    if currency == "€":
        return f"{amount:,.{decimal_places}f} €".replace(",", " ").replace(".", ",")
    else:
        return f"{currency} {amount:,.{decimal_places}f}"

def sanitize_text(text: str) -> str:
    """Nettoie et sécurise un texte"""
    if not text:
        return ""
    
    # Supprimer les caractères de contrôle
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
    
    # Normaliser les espaces
    text = ' '.join(text.split())
    
    # Échapper les caractères HTML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    return text.strip()

def extract_numbers(text: str) -> List[str]:
    """Extrait tous les nombres d'un texte"""
    # Pattern pour capturer différents formats de nombres
    pattern = r'\b\d+(?:[.,]\d+)*\b'
    return re.findall(pattern, text)

def calculate_risk_score(factors: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calcule un score de risque pondéré
    factors: dict avec les facteurs et leurs valeurs (0-1)
    weights: dict avec les poids de chaque facteur
    """
    if not factors:
        return 0.0
    
    if not weights:
        # Poids égaux par défaut
        weights = {k: 1.0 for k in factors.keys()}
    
    total_weight = sum(weights.get(k, 1.0) for k in factors.keys())
    weighted_sum = sum(factors[k] * weights.get(k, 1.0) for k in factors.keys())
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0

def generate_unique_id(prefix: str = "", length: int = 8) -> str:
    """Génère un identifiant unique"""
    unique_part = str(uuid.uuid4()).replace('-', '')[:length]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    if prefix:
        return f"{prefix}_{timestamp}_{unique_part}"
    return f"{timestamp}_{unique_part}"

def validate_email(email: str) -> bool:
    """Valide une adresse email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str, country: str = "FR") -> bool:
    """Valide un numéro de téléphone"""
    # Nettoyer le numéro
    phone = re.sub(r'[^\d+]', '', phone)
    
    if country == "FR":
        # Format français: 10 chiffres ou +33
        pattern = r'^(?:\+33|0)[1-9](?:\d{8})$'
        return bool(re.match(pattern, phone))
    
    # Format international générique
    return len(phone) >= 7 and len(phone) <= 15

class HTMLStripper(HTMLParser):
    """Classe pour supprimer les balises HTML"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
        
    def handle_data(self, data):
        self.text.append(data)
        
    def get_data(self):
        return ''.join(self.text)

def clean_html(html_text: str) -> str:
    """Supprime toutes les balises HTML d'un texte"""
    if not html_text:
        return ""
        
    stripper = HTMLStripper()
    stripper.feed(html_text)
    return stripper.get_data()

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Tronque un texte à une longueur maximale"""
    if len(text) <= max_length:
        return text
        
    # Trouver le dernier espace avant la limite
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Si l'espace est assez proche
        truncated = truncated[:last_space]
        
    return truncated + suffix

def highlight_text(text: str, terms: List[str], css_class: str = "highlight") -> str:
    """Surligne des termes dans un texte avec HTML"""
    if not terms:
        return text
        
    # Échapper les termes pour regex
    escaped_terms = [re.escape(term) for term in terms]
    pattern = '|'.join(escaped_terms)
    
    # Remplacer avec balise de surlignage
    highlighted = re.sub(
        f'({pattern})',
        r'<span class="{}">\1</span>'.format(css_class),
        text,
        flags=re.IGNORECASE
    )
    
    return highlighted

def create_summary(text: str, max_sentences: int = 3, min_sentence_length: int = 10) -> str:
    """Crée un résumé simple d'un texte"""
    if not text:
        return ""
    
    # Diviser en phrases
    sentences = re.split(r'[.!?]+', text)
    
    # Filtrer les phrases trop courtes
    valid_sentences = [
        s.strip() for s in sentences 
        if len(s.strip()) >= min_sentence_length
    ]
    
    # Prendre les premières phrases
    summary_sentences = valid_sentences[:max_sentences]
    
    # Rejoindre avec ponctuation
    summary = '. '.join(summary_sentences)
    if summary and not summary.endswith('.'):
        summary += '.'
        
    return summary

def calculate_hash(content: str) -> str:
    """Calcule le hash SHA256 d'un contenu"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def parse_legal_reference(reference: str) -> Dict[str, str]:
    """Parse une référence juridique pour extraire ses composants"""
    result = {
        'juridiction': '',
        'date': '',
        'numero': '',
        'original': reference
    }
    
    # Pattern pour différents formats
    patterns = [
        r'([\w\s.]+?),?\s*(\d{1,2}\s+\w+\s+\d{4}),?\s*n°\s*([\d\-\.]+)',
        r'([\w\s.]+?),?\s*(\d{1,2}[\s\-/]\d{1,2}[\s\-/]\d{4}),?\s*n°\s*([\d\-\.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, reference, re.IGNORECASE)
        if match:
            result['juridiction'] = match.group(1).strip()
            result['date'] = match.group(2).strip()
            result['numero'] = match.group(3).strip()
            break
            
    return result

def normalize_whitespace(text: str) -> str:
    """Normalise tous les espaces blancs dans un texte"""
    # Remplacer tous les espaces multiples, tabs, retours à la ligne par un seul espace
    return ' '.join(text.split())

def is_valid_jurisprudence_number(numero: str) -> bool:
    """Vérifie si un numéro de jurisprudence semble valide"""
    # Nettoyer le numéro
    clean_numero = re.sub(r'[^\d\-.]', '', numero)
    
    # Vérifier qu'il contient au moins quelques chiffres
    if len(re.sub(r'[^\d]', '', clean_numero)) < 4:
        return False
        
    # Patterns valides courants
    patterns = [
        r'^\d{2}-\d{2}\.\d{3}$',  # Format Cour de cassation
        r'^\d{6}$',  # Format Conseil d'État
        r'^\d{2}/\d{5}$',  # Format Cour d'appel
    ]
    
    return any(re.match(pattern, clean_numero) for pattern in patterns)
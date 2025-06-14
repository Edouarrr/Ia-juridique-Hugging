"""Fonctions utilitaires pour l'application IA Juridique"""

import re
import unicodedata
from typing import Optional, Dict, List, Any
import hashlib
import json
from datetime import datetime

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale
    
    Args:
        text: Le texte à tronquer
        max_length: Longueur maximale du texte
        suffix: Suffixe à ajouter si le texte est tronqué
        
    Returns:
        Le texte tronqué
    """
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    available_length = max_length - len(suffix)
    return text[:available_length] + suffix

def clean_key(key: str) -> str:
    """
    Nettoie une clé pour la rendre utilisable comme identifiant
    
    Args:
        key: La clé à nettoyer
        
    Returns:
        La clé nettoyée
    """
    if not key:
        return ""
    key = str(key)
    # Supprimer les accents
    key = ''.join(c for c in unicodedata.normalize('NFD', key) 
                  if unicodedata.category(c) != 'Mn')
    key = key.lower()
    key = re.sub(r'[^a-z0-9]+', '_', key)
    key = key.strip('_')
    key = re.sub(r'_+', '_', key)
    return key

def generate_unique_id(prefix: str = "") -> str:
    """
    Génère un identifiant unique
    
    Args:
        prefix: Préfixe optionnel pour l'identifiant
        
    Returns:
        Un identifiant unique
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}" if prefix else unique_id

def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille de fichier en unité lisible
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        Taille formatée (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def extract_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Extrait une date depuis un nom de fichier
    
    Args:
        filename: Nom du fichier
        
    Returns:
        Date extraite ou None
    """
    # Patterns de dates courants
    patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
        r'(\d{4})(\d{2})(\d{2})',    # YYYYMMDD
        r'(\d{2})(\d{2})(\d{4})',    # DDMMYYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY en premier
                    return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                else:  # DD en premier
                    return datetime(int(groups[2]), int(groups[1]), int(groups[0]))
            except ValueError:
                continue
    return None

def normalize_document_type(filename: str, content: str = "") -> str:
    """
    Détermine le type de document juridique
    
    Args:
        filename: Nom du fichier
        content: Contenu du document (optionnel)
        
    Returns:
        Type de document normalisé
    """
    filename_lower = filename.lower()
    content_lower = content.lower() if content else ""
    
    # Règles de catégorisation
    if any(term in filename_lower for term in ['pv', 'proces-verbal', 'audition']):
        return 'pv'
    elif any(term in filename_lower for term in ['expertise', 'expert', 'rapport']):
        return 'expertise'
    elif any(term in filename_lower for term in ['contrat', 'convention', 'accord']):
        return 'contrat'
    elif any(term in filename_lower for term in ['facture', 'devis', 'bon']):
        return 'facture'
    elif any(term in filename_lower for term in ['lettre', 'courrier', 'mail']):
        return 'courrier'
    elif any(term in filename_lower for term in ['procedure', 'jugement', 'ordonnance']):
        return 'procedure'
    else:
        return 'autre'

def calculate_document_hash(content: bytes) -> str:
    """
    Calcule le hash SHA-256 d'un document
    
    Args:
        content: Contenu du document en bytes
        
    Returns:
        Hash SHA-256 en hexadécimal
    """
    return hashlib.sha256(content).hexdigest()

def is_valid_email(email: str) -> bool:
    """
    Vérifie si une adresse email est valide
    
    Args:
        email: Adresse email à vérifier
        
    Returns:
        True si l'email est valide
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre sûr
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    # Remplacer les caractères dangereux
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limiter la longueur
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 200:
        name = name[:200]
    return f"{name}.{ext}" if ext else name

def parse_search_query(query: str) -> Dict[str, Any]:
    """
    Parse une requête de recherche avancée
    
    Args:
        query: Requête de recherche
        
    Returns:
        Dictionnaire avec les éléments parsés
    """
    result = {
        'container': None,
        'terms': [],
        'operators': [],
        'date_filter': None,
        'type_filter': None,
        'raw_query': query
    }
    
    # Extraire le container (@xxx)
    container_match = re.match(r'@(\w+)\s*,?\s*(.*)', query)
    if container_match:
        result['container'] = container_match.group(1)
        query = container_match.group(2)
    
    # Extraire les filtres de date
    date_match = re.search(r'DATE:(\d{4})', query)
    if date_match:
        result['date_filter'] = date_match.group(1)
        query = query.replace(date_match.group(0), '')
    
    # Extraire les termes entre guillemets
    quoted_terms = re.findall(r'"([^"]+)"', query)
    result['terms'].extend(quoted_terms)
    for term in quoted_terms:
        query = query.replace(f'"{term}"', '')
    
    # Extraire les opérateurs
    for op in ['ET', 'OU', 'SAUF']:
        if op in query:
            result['operators'].append(op)
    
    # Termes restants
    remaining_terms = query.split()
    result['terms'].extend([t for t in remaining_terms if t not in ['ET', 'OU', 'SAUF']])
    
    return result

def format_legal_date(date: datetime) -> str:
    """
    Formate une date au format juridique français
    
    Args:
        date: Date à formater
        
    Returns:
        Date formatée (ex: "15 janvier 2024")
    """
    months = [
        'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
    ]
    return f"{date.day} {months[date.month - 1]} {date.year}"

def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estime le temps de lecture d'un texte
    
    Args:
        text: Texte à analyser
        words_per_minute: Vitesse de lecture moyenne
        
    Returns:
        Temps de lecture estimé en minutes
    """
    if not text:
        return 0
    word_count = len(text.split())
    return max(1, round(word_count / words_per_minute))

def generate_document_summary(content: str, max_sentences: int = 3) -> str:
    """
    Génère un résumé simple d'un document
    
    Args:
        content: Contenu du document
        max_sentences: Nombre maximum de phrases
        
    Returns:
        Résumé du document
    """
    if not content:
        return ""
    
    # Diviser en phrases
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Prendre les premières phrases
    summary_sentences = sentences[:max_sentences]
    return '. '.join(summary_sentences) + '.'

def validate_container_name(name: str) -> bool:
    """
    Valide un nom de container Azure
    
    Args:
        name: Nom du container
        
    Returns:
        True si le nom est valide
    """
    # Règles Azure : 3-63 caractères, lettres minuscules, chiffres et tirets
    if not name or len(name) < 3 or len(name) > 63:
        return False
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name):
        return False
    if '--' in name:
        return False
    return True

def merge_document_metadata(doc1: Dict, doc2: Dict) -> Dict:
    """
    Fusionne les métadonnées de deux documents
    
    Args:
        doc1: Premier document
        doc2: Deuxième document
        
    Returns:
        Métadonnées fusionnées
    """
    merged = doc1.copy()
    
    # Fusionner les champs spécifiques
    for key in ['tags', 'categories', 'authors']:
        if key in doc2:
            if key in merged:
                merged[key] = list(set(merged[key] + doc2[key]))
            else:
                merged[key] = doc2[key]
    
    # Prendre la date la plus récente
    if 'last_modified' in doc2:
        if 'last_modified' not in merged or doc2['last_modified'] > merged['last_modified']:
            merged['last_modified'] = doc2['last_modified']
    
    return merged

# Fonctions spécifiques pour la gestion des erreurs
def format_error_message(error: Exception, context: str = "") -> str:
    """
    Formate un message d'erreur de manière conviviale
    
    Args:
        error: Exception capturée
        context: Contexte de l'erreur
        
    Returns:
        Message d'erreur formaté
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"{context} : {error_type} - {error_msg}"
    else:
        return f"{error_type} : {error_msg}"

def create_error_report(errors: List[Dict]) -> str:
    """
    Crée un rapport d'erreurs formaté
    
    Args:
        errors: Liste des erreurs
        
    Returns:
        Rapport formaté
    """
    if not errors:
        return "Aucune erreur détectée"
    
    report = f"# Rapport d'erreurs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for i, error in enumerate(errors, 1):
        report += f"## Erreur {i}\n"
        report += f"- **Module** : {error.get('module', 'Inconnu')}\n"
        report += f"- **Type** : {error.get('type', 'Inconnu')}\n"
        report += f"- **Message** : {error.get('message', 'Pas de message')}\n"
        report += f"- **Timestamp** : {error.get('timestamp', 'Non défini')}\n\n"
    
    return report
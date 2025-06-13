# utils/helpers.py
"""
Fonctions utilitaires générales pour l'application juridique
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional, Union
import json
import hashlib
from datetime import datetime

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale en ajoutant un suffixe.
    
    Args:
        text: Le texte à tronquer
        max_length: La longueur maximale (par défaut 100)
        suffix: Le suffixe à ajouter si le texte est tronqué (par défaut "...")
    
    Returns:
        Le texte tronqué
    """
    if not text:
        return ""
    
    # Convertir en string si nécessaire
    text = str(text)
    
    # Si le texte est déjà plus court, le retourner tel quel
    if len(text) <= max_length:
        return text
    
    # Calculer la longueur disponible pour le texte
    available_length = max_length - len(suffix)
    
    # Tronquer et ajouter le suffixe
    return text[:available_length] + suffix

def clean_key(key: str) -> str:
    """
    Nettoie une clé pour la rendre utilisable comme identifiant.
    Supprime les caractères spéciaux et normalise le texte.
    
    Args:
        key: La clé à nettoyer
    
    Returns:
        La clé nettoyée
    """
    if not key:
        return ""
    
    # Convertir en string
    key = str(key)
    
    # Supprimer les accents
    key = ''.join(c for c in unicodedata.normalize('NFD', key) 
                  if unicodedata.category(c) != 'Mn')
    
    # Convertir en minuscules
    key = key.lower()
    
    # Remplacer les espaces et caractères spéciaux par des underscores
    key = re.sub(r'[^a-z0-9]+', '_', key)
    
    # Supprimer les underscores en début et fin
    key = key.strip('_')
    
    # Éviter les doubles underscores
    key = re.sub(r'_+', '_', key)
    
    return key

def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier en supprimant les caractères interdits.
    
    Args:
        filename: Le nom de fichier à nettoyer
    
    Returns:
        Le nom de fichier nettoyé
    """
    # Caractères interdits dans les noms de fichiers
    invalid_chars = '<>:"/\\|?*'
    
    # Remplacer les caractères interdits par des underscores
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Supprimer les espaces en début et fin
    filename = filename.strip()
    
    # Limiter la longueur
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            available_length = max_length - len(ext) - 1
            filename = f"{name[:available_length]}.{ext}"
        else:
            filename = filename[:max_length]
    
    return filename

def generate_unique_id(prefix: str = "") -> str:
    """
    Génère un identifiant unique basé sur le timestamp et un hash.
    
    Args:
        prefix: Préfixe optionnel pour l'identifiant
    
    Returns:
        Un identifiant unique
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    hash_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    if prefix:
        return f"{clean_key(prefix)}_{timestamp}_{hash_part}"
    else:
        return f"{timestamp}_{hash_part}"

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusionne deux dictionnaires de manière récursive.
    
    Args:
        dict1: Premier dictionnaire
        dict2: Deuxième dictionnaire (ses valeurs écrasent celles du premier)
    
    Returns:
        Le dictionnaire fusionné
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def safe_get(dictionary: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Récupère une valeur dans un dictionnaire imbriqué de manière sûre.
    
    Args:
        dictionary: Le dictionnaire source
        path: Le chemin vers la valeur (ex: "user.profile.name")
        default: Valeur par défaut si le chemin n'existe pas
    
    Returns:
        La valeur trouvée ou la valeur par défaut
    """
    keys = path.split('.')
    value = dictionary
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value

def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille de fichier en unité lisible.
    
    Args:
        size_bytes: Taille en octets
    
    Returns:
        Taille formatée (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Divise une liste en sous-listes de taille fixe.
    
    Args:
        lst: La liste à diviser
        chunk_size: La taille de chaque sous-liste
    
    Returns:
        Liste de sous-listes
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Charge un JSON de manière sûre avec une valeur par défaut en cas d'erreur.
    
    Args:
        json_string: La chaîne JSON à parser
        default: Valeur par défaut en cas d'erreur
    
    Returns:
        L'objet Python ou la valeur par défaut
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default

def remove_duplicates(lst: List[Any], key: Optional[callable] = None) -> List[Any]:
    """
    Supprime les doublons d'une liste tout en préservant l'ordre.
    
    Args:
        lst: La liste source
        key: Fonction optionnelle pour extraire la clé de comparaison
    
    Returns:
        Liste sans doublons
    """
    seen = set()
    result = []
    
    for item in lst:
        check_value = key(item) if key else item
        if check_value not in seen:
            seen.add(check_value)
            result.append(item)
    
    return result
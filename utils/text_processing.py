# utils/text_processing.py
"""
Fonctions de traitement de texte pour l'application juridique
"""
import re
import unicodedata
from typing import List, Tuple, Optional, Dict
import string

def clean_text(text: str) -> str:
    """
    Nettoie un texte en supprimant les caractères indésirables.
    
    Args:
        text: Le texte à nettoyer
        
    Returns:
        Le texte nettoyé
    """
    if not text:
        return ""
    
    # Convertir en string si nécessaire
    text = str(text)
    
    # Supprimer les caractères de contrôle
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
    
    # Normaliser les espaces
    text = ' '.join(text.split())
    
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    # Supprimer les espaces en début et fin
    text = text.strip()
    
    return text

def process_text(text: str) -> str:
    """
    Traite un texte pour le préparer à l'analyse.
    
    Args:
        text: Le texte à traiter
        
    Returns:
        Le texte traité
    """
    if not text:
        return ""
    
    # Nettoyer le texte
    text = clean_text(text)
    
    # Corriger la ponctuation
    text = fix_punctuation(text)
    
    # Normaliser les guillemets
    text = normalize_quotes(text)
    
    return text

def fix_punctuation(text: str) -> str:
    """
    Corrige la ponctuation dans un texte.
    
    Args:
        text: Le texte à corriger
        
    Returns:
        Le texte avec la ponctuation corrigée
    """
    # Ajouter des espaces après la ponctuation si nécessaire
    text = re.sub(r'([.!?;:,])([A-Za-zÀ-ÿ])', r'\1 \2', text)
    
    # Supprimer les espaces avant la ponctuation
    text = re.sub(r'\s+([.!?;:,])', r'\1', text)
    
    # Corriger les points de suspension
    text = re.sub(r'\.{3,}', '...', text)
    
    return text

def normalize_quotes(text: str) -> str:
    """
    Normalise les différents types de guillemets.
    
    Args:
        text: Le texte à normaliser
        
    Returns:
        Le texte avec des guillemets normalisés
    """
    # Remplacer les guillemets typographiques par des guillemets simples
    quotes_map = {
        '"': '"',
        '"': '"',
        '„': '"',
        '«': '"',
        '»': '"',
        ''': "'",
        ''': "'",
        '‚': "'",
        '‹': "'",
        '›': "'"
    }
    
    for old_quote, new_quote in quotes_map.items():
        text = text.replace(old_quote, new_quote)
    
    return text

def extract_sentences(text: str) -> List[str]:
    """
    Extrait les phrases d'un texte.
    
    Args:
        text: Le texte source
        
    Returns:
        Liste des phrases
    """
    if not text:
        return []
    
    # Séparer sur les points, points d'exclamation et d'interrogation
    # mais pas sur les abréviations courantes
    abbreviations = ['M.', 'Mme', 'Dr', 'Me', 'art.', 'al.', 'cf.', 'etc.', 'p.', 'pp.']
    
    # Remplacer temporairement les abréviations
    temp_text = text
    for i, abbr in enumerate(abbreviations):
        temp_text = temp_text.replace(abbr, f"ABBR{i}")
    
    # Séparer les phrases
    sentences = re.split(r'[.!?]+', temp_text)
    
    # Restaurer les abréviations et nettoyer
    result = []
    for sentence in sentences:
        for i, abbr in enumerate(abbreviations):
            sentence = sentence.replace(f"ABBR{i}", abbr)
        
        sentence = sentence.strip()
        if sentence:
            result.append(sentence)
    
    return result

def extract_paragraphs(text: str) -> List[str]:
    """
    Extrait les paragraphes d'un texte.
    
    Args:
        text: Le texte source
        
    Returns:
        Liste des paragraphes
    """
    if not text:
        return []
    
    # Séparer sur les doubles retours à la ligne
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Nettoyer et filtrer
    result = []
    for para in paragraphs:
        para = para.strip()
        if para:
            result.append(para)
    
    return result

def count_words(text: str) -> int:
    """
    Compte le nombre de mots dans un texte.
    
    Args:
        text: Le texte à analyser
        
    Returns:
        Le nombre de mots
    """
    if not text:
        return 0
    
    # Nettoyer le texte
    text = clean_text(text)
    
    # Compter les mots
    words = text.split()
    return len(words)

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extrait les mots-clés principaux d'un texte.
    
    Args:
        text: Le texte source
        max_keywords: Nombre maximum de mots-clés à extraire
        
    Returns:
        Liste des mots-clés
    """
    if not text:
        return []
    
    # Mots vides à ignorer (stop words français)
    stop_words = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais',
        'donc', 'or', 'ni', 'car', 'que', 'qui', 'quoi', 'dont', 'où', 'à',
        'au', 'aux', 'avec', 'ce', 'ces', 'dans', 'sur', 'sous', 'par', 'pour',
        'en', 'vers', 'chez', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
        'je', 'tu', 'me', 'te', 'se', 'leur', 'lui', 'y', 'est', 'sont', 'été',
        'être', 'avoir', 'fait', 'faire', 'dit', 'dire', 'aller', 'tout', 'tous',
        'toute', 'toutes', 'autre', 'autres', 'même', 'mêmes', 'tel', 'telle',
        'tels', 'telles', 'quel', 'quelle', 'quels', 'quelles', 'sans', 'plus',
        'moins', 'très', 'bien', 'peu', 'plu', 'soit', 'ne', 'pas', 'point',
        'non', 'cette', 'cet', 'mon', 'ton', 'son', 'ma', 'ta', 'sa', 'mes',
        'tes', 'ses', 'notre', 'votre', 'nos', 'vos', 'leurs'
    }
    
    # Convertir en minuscules et extraire les mots
    words = re.findall(r'\b[a-zà-ÿ]+\b', text.lower())
    
    # Filtrer les mots vides et les mots courts
    keywords = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Compter les occurrences
    word_count = {}
    for word in keywords:
        word_count[word] = word_count.get(word, 0) + 1
    
    # Trier par fréquence et retourner les plus fréquents
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, count in sorted_words[:max_keywords]]

def highlight_text(text: str, keywords: List[str], tag: str = "mark") -> str:
    """
    Met en évidence des mots-clés dans un texte.
    
    Args:
        text: Le texte source
        keywords: Liste des mots-clés à mettre en évidence
        tag: Tag HTML à utiliser (par défaut "mark")
        
    Returns:
        Le texte avec les mots-clés mis en évidence
    """
    if not text or not keywords:
        return text
    
    # Créer un pattern pour tous les mots-clés
    pattern = '|'.join(re.escape(keyword) for keyword in keywords)
    
    # Remplacer en ignorant la casse
    def replace_func(match):
        return f'<{tag}>{match.group()}</{tag}>'
    
    highlighted = re.sub(f'\\b({pattern})\\b', replace_func, text, flags=re.IGNORECASE)
    
    return highlighted

def remove_html_tags(text: str) -> str:
    """
    Supprime les balises HTML d'un texte.
    
    Args:
        text: Le texte contenant des balises HTML
        
    Returns:
        Le texte sans balises HTML
    """
    if not text:
        return ""
    
    # Pattern pour détecter les balises HTML
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def normalize_whitespace(text: str) -> str:
    """
    Normalise les espaces blancs dans un texte.
    
    Args:
        text: Le texte à normaliser
        
    Returns:
        Le texte avec des espaces normalisés
    """
    if not text:
        return ""
    
    # Remplacer tous les types d'espaces par des espaces simples
    text = re.sub(r'[\s\u00A0\u2000-\u200B\u2028\u2029\u202F\u205F\u3000]+', ' ', text)
    
    # Supprimer les espaces en début et fin
    text = text.strip()
    
    return text

def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Divise un texte en morceaux de taille fixe avec chevauchement.
    
    Args:
        text: Le texte à diviser
        chunk_size: Taille de chaque morceau en caractères
        overlap: Nombre de caractères de chevauchement
        
    Returns:
        Liste des morceaux de texte
    """
    if not text or chunk_size <= 0:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Calculer la fin du chunk
        end = start + chunk_size
        
        # Si ce n'est pas le dernier chunk, essayer de couper à la fin d'une phrase
        if end < text_length:
            # Chercher le dernier point, point d'exclamation ou d'interrogation
            last_sentence_end = max(
                text.rfind('.', start, end),
                text.rfind('!', start, end),
                text.rfind('?', start, end)
            )
            
            if last_sentence_end > start:
                end = last_sentence_end + 1
        
        # Ajouter le chunk
        chunks.append(text[start:end].strip())
        
        # Passer au chunk suivant avec chevauchement
        start = end - overlap if end < text_length else end
    
    return chunks
# utils/text_processing.py
"""
Fonctions de traitement de texte pour l'application juridique
"""
import re
import string
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple


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

def clean_key(key: str) -> str:
    """
    Nettoie une clé pour la rendre utilisable comme identifiant
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

def normalize_whitespace(text: str) -> str:
    """
    Normalise les espaces blancs dans un texte.
    """
    if not text:
        return ""
    
    # Remplacer tous les types d'espaces par des espaces simples
    text = re.sub(r'[\s\u00A0\u2000-\u200B\u2028\u2029\u202F\u205F\u3000]+', ' ', text)
    
    # Supprimer les espaces en début et fin
    text = text.strip()
    
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale
    """
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    available_length = max_length - len(suffix)
    return text[:available_length] + suffix

def extract_section(text: str, start_marker: str, end_marker: str = None) -> str:
    """
    Extrait une section de texte entre deux marqueurs
    """
    if not text or not start_marker:
        return ""
    
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return ""
    
    start_idx += len(start_marker)
    
    if end_marker:
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            return text[start_idx:].strip()
        return text[start_idx:end_idx].strip()
    else:
        return text[start_idx:].strip()

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Divise un texte en morceaux avec chevauchement
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

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calcule la similarité entre deux textes (0 à 1)
    """
    if not text1 or not text2:
        return 0.0
    
    # Normaliser les textes
    text1 = normalize_whitespace(text1.lower())
    text2 = normalize_whitespace(text2.lower())
    
    # Utiliser SequenceMatcher pour calculer la similarité
    return SequenceMatcher(None, text1, text2).ratio()

def highlight_text(text: str, keywords: List[str], tag: str = "mark") -> str:
    """
    Met en évidence des mots-clés dans un texte.
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

def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
    """
    Extrait les phrases clés d'un texte
    """
    if not text:
        return []
    
    # Pour l'instant, on utilise une extraction simple basée sur les n-grammes
    # Dans une version plus avancée, on pourrait utiliser du NLP
    
    # Nettoyer le texte
    clean = clean_text(text).lower()
    
    # Extraire les n-grammes de 2-4 mots
    words = clean.split()
    phrases = []
    
    for n in range(2, 5):  # 2-grammes à 4-grammes
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i+n])
            if len(phrase) > 10:  # Au moins 10 caractères
                phrases.append(phrase)
    
    # Compter les occurrences
    phrase_count = {}
    for phrase in phrases:
        phrase_count[phrase] = phrase_count.get(phrase, 0) + 1
    
    # Trier par fréquence
    sorted_phrases = sorted(phrase_count.items(), key=lambda x: x[1], reverse=True)
    
    return [phrase for phrase, _ in sorted_phrases[:max_phrases]]

def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Génère un résumé automatique d'un texte
    """
    if not text:
        return ""
    
    sentences = extract_sentences(text)
    if not sentences:
        return text[:200] + "..." if len(text) > 200 else text
    
    # Pour l'instant, on prend les premières phrases
    # Une version plus avancée pourrait utiliser de l'extractive summarization
    summary_sentences = sentences[:max_sentences]
    
    return '. '.join(summary_sentences) + '.'

def calculate_read_time(text: str, words_per_minute: int = 200) -> int:
    """
    Calcule le temps de lecture estimé en minutes
    """
    if not text:
        return 0
    
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    
    return max(1, round(minutes))

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extrait les entités nommées d'un texte (version simplifiée)
    """
    entities = {
        'persons': [],
        'organizations': [],
        'locations': [],
        'dates': [],
        'amounts': []
    }
    
    if not text:
        return entities
    
    # Extraction basique des noms propres (mots commençant par une majuscule)
    potential_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    
    # Filtrer les noms de personnes probables (prénom + nom)
    for name in potential_names:
        parts = name.split()
        if len(parts) >= 2:
            entities['persons'].append(name)
        elif len(parts) == 1 and len(name) > 3:
            # Pourrait être une organisation ou un lieu
            entities['organizations'].append(name)
    
    # Extraction des dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b'
    ]
    
    for pattern in date_patterns:
        dates = re.findall(pattern, text, re.IGNORECASE)
        entities['dates'].extend(dates)
    
    # Extraction des montants
    amount_patterns = [
        r'\b\d+(?:\.\d{3})*(?:,\d{2})?\s*(?:€|EUR|euros?)\b',
        r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:\$|USD|dollars?)\b'
    ]
    
    for pattern in amount_patterns:
        amounts = re.findall(pattern, text, re.IGNORECASE)
        entities['amounts'].extend(amounts)
    
    # Dédupliquer
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return entities

def extract_monetary_amounts(text: str) -> List[Dict[str, Any]]:
    """
    Extrait les montants monétaires d'un texte
    """
    amounts = []
    
    if not text:
        return amounts
    
    # Patterns pour différents formats
    patterns = [
        # Format européen avec €
        (r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)', 'EUR'),
        # Format américain avec $
        (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        # Format avec devise textuelle
        (r'(\d{1,3}(?:\s\d{3})*(?:,\d{2})?)\s*(euros?|dollars?)', None)
    ]
    
    for pattern, default_currency in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            amount_str = match.group(1)
            
            # Normaliser le montant
            amount_str = amount_str.replace('.', '').replace(' ', '').replace(',', '.')
            
            try:
                amount = float(amount_str)
                
                # Déterminer la devise
                if default_currency:
                    currency = default_currency
                else:
                    currency_text = match.group(2).lower()
                    currency = 'EUR' if 'euro' in currency_text else 'USD'
                
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
    """
    Nettoie un texte juridique en conservant la structure
    """
    if not text:
        return ""
    
    # Nettoyer les caractères spéciaux tout en préservant la structure
    text = clean_text(text)
    
    # Normaliser les références juridiques
    text = format_legal_citations(text)
    
    # Corriger la ponctuation
    text = fix_punctuation(text)
    
    return text

def format_legal_citations(text: str) -> str:
    """
    Formate les citations juridiques de manière cohérente
    """
    if not text:
        return ""
    
    # Normaliser les articles
    text = re.sub(r'\bart\.?\s*(\d+)', r'article \1', text, flags=re.IGNORECASE)
    
    # Normaliser les alinéas
    text = re.sub(r'\bal\.?\s*(\d+)', r'alinéa \1', text, flags=re.IGNORECASE)
    
    # Normaliser les références de jurisprudence
    text = re.sub(r'Cass\.?\s+', 'Cass. ', text)
    text = re.sub(r'C\.?\s*cass\.?\s+', 'Cour de cassation, ', text, flags=re.IGNORECASE)
    
    return text

def process_text(text: str) -> str:
    """
    Traite un texte pour le préparer à l'analyse.
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

def remove_html_tags(text: str) -> str:
    """
    Supprime les balises HTML d'un texte.
    """
    if not text:
        return ""
    
    # Pattern pour détecter les balises HTML
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Divise un texte en morceaux de taille fixe avec chevauchement.
    """
    return chunk_text(text, chunk_size, overlap)
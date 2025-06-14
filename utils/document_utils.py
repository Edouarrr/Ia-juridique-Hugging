# utils/document_utils.py
"""
Fonctions utilitaires pour la gestion des documents
"""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Import des types nécessaires avec gestion d'erreur
try:
    from models.dataclasses import Document
except ImportError:
    try:
        from modules.dataclasses import Document
    except ImportError:
        # Fallback simple
        class Document:
            def __init__(self, id, title, content, source="", metadata=None, tags=None):
                self.id = id
                self.title = title
                self.content = content
                self.source = source
                self.metadata = metadata or {}
                self.tags = tags or []


def generate_document_id(title: str, source: str = "") -> str:
    """Génère un ID unique pour un document"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Créer un hash court du titre
    title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
    
    if source:
        # Nettoyer la source
        clean_source = re.sub(r'[^\w\s-]', '', source.lower())
        clean_source = re.sub(r'[-\s]+', '_', clean_source)[:20]
        return f"{clean_source}_{title_hash}_{timestamp}"
    else:
        return f"doc_{title_hash}_{timestamp}"


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
        'document_count': len(docs),
        'original_titles': [doc.title for doc in docs]
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


def split_document(doc: Document, max_size: int = 5000) -> List[Document]:
    """Divise un document en plusieurs parties"""
    if len(doc.content) <= max_size:
        return [doc]
    
    parts = []
    content = doc.content
    part_number = 1
    
    while content:
        # Prendre une partie
        part_content = content[:max_size]
        
        # Essayer de couper à une phrase
        if len(content) > max_size:
            last_period = part_content.rfind('.')
            if last_period > max_size * 0.8:
                part_content = part_content[:last_period + 1]
        
        # Créer le document partie
        part_doc = Document(
            id=f"{doc.id}_part_{part_number}",
            title=f"{doc.title} - Partie {part_number}",
            content=part_content,
            source=doc.source,
            metadata={
                **doc.metadata,
                'original_id': doc.id,
                'part_number': part_number,
                'total_parts': None  # Sera mis à jour
            },
            tags=doc.tags
        )
        
        parts.append(part_doc)
        content = content[len(part_content):]
        part_number += 1
    
    # Mettre à jour le nombre total de parties
    for part in parts:
        part.metadata['total_parts'] = len(parts)
    
    return parts


def extract_document_metadata(content: str) -> Dict[str, Any]:
    """Extrait des métadonnées automatiques d'un document"""
    metadata = {
        'length': len(content),
        'word_count': len(content.split()),
        'line_count': content.count('\n') + 1,
        'has_tables': bool(re.search(r'\|.*\|', content)),
        'has_lists': bool(re.search(r'^\s*[-*•]\s', content, re.MULTILINE)),
        'has_headers': bool(re.search(r'^#+\s', content, re.MULTILINE)),
        'extraction_date': datetime.now().isoformat()
    }
    
    # Détecter la langue (simple)
    if re.search(r'\b(le|la|les|de|du|des)\b', content[:1000], re.IGNORECASE):
        metadata['language'] = 'fr'
    else:
        metadata['language'] = 'unknown'
    
    # Extraire un résumé
    first_paragraph = content.split('\n\n')[0] if '\n\n' in content else content[:200]
    metadata['summary'] = first_paragraph[:200] + '...' if len(first_paragraph) > 200 else first_paragraph
    
    return metadata


def create_document_index(docs: List[Document]) -> Dict[str, Any]:
    """Crée un index de documents"""
    index = {
        'documents': {},
        'tags': {},
        'sources': {},
        'dates': {},
        'stats': {
            'total_documents': len(docs),
            'total_words': 0,
            'unique_tags': set(),
            'unique_sources': set()
        }
    }
    
    for doc in docs:
        # Index par ID
        index['documents'][doc.id] = {
            'title': doc.title,
            'source': doc.source,
            'tags': doc.tags,
            'word_count': len(doc.content.split())
        }
        
        # Index par tags
        for tag in doc.tags:
            if tag not in index['tags']:
                index['tags'][tag] = []
            index['tags'][tag].append(doc.id)
            index['stats']['unique_tags'].add(tag)
        
        # Index par source
        if doc.source:
            if doc.source not in index['sources']:
                index['sources'][doc.source] = []
            index['sources'][doc.source].append(doc.id)
            index['stats']['unique_sources'].add(doc.source)
        
        # Stats
        index['stats']['total_words'] += len(doc.content.split())
    
    # Convertir les sets en listes pour la sérialisation
    index['stats']['unique_tags'] = list(index['stats']['unique_tags'])
    index['stats']['unique_sources'] = list(index['stats']['unique_sources'])
    
    return index


def compare_documents(doc1: Document, doc2: Document) -> Dict[str, Any]:
    """Compare deux documents"""
    from .text_processing import calculate_text_similarity
    
    comparison = {
        'similarity_score': calculate_text_similarity(doc1.content, doc2.content),
        'length_diff': abs(len(doc1.content) - len(doc2.content)),
        'common_tags': list(set(doc1.tags).intersection(set(doc2.tags))),
        'unique_tags_doc1': list(set(doc1.tags) - set(doc2.tags)),
        'unique_tags_doc2': list(set(doc2.tags) - set(doc1.tags)),
        'same_source': doc1.source == doc2.source
    }
    
    # Comparer les métadonnées
    if hasattr(doc1, 'metadata') and hasattr(doc2, 'metadata'):
        common_keys = set(doc1.metadata.keys()).intersection(set(doc2.metadata.keys()))
        comparison['common_metadata_keys'] = list(common_keys)
    
    return comparison


def create_document_summary(doc: Document, max_sentences: int = 3) -> str:
    """Crée un résumé d'un document"""
    sentences = doc.content.split('.')
    summary_sentences = []
    
    for sentence in sentences[:max_sentences * 2]:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Phrases significatives
            summary_sentences.append(sentence)
            if len(summary_sentences) >= max_sentences:
                break
    
    return '. '.join(summary_sentences) + '.' if summary_sentences else doc.content[:200] + '...'


def get_document_statistics(doc: Document) -> Dict[str, Any]:
    """Calcule des statistiques sur un document"""
    content = doc.content
    
    stats = {
        'id': doc.id,
        'title': doc.title,
        'character_count': len(content),
        'word_count': len(content.split()),
        'line_count': content.count('\n') + 1,
        'paragraph_count': len(content.split('\n\n')),
        'average_word_length': 0,
        'sentence_count': content.count('.') + content.count('!') + content.count('?'),
        'tag_count': len(doc.tags),
        'has_metadata': bool(hasattr(doc, 'metadata') and doc.metadata)
    }
    
    # Longueur moyenne des mots
    words = content.split()
    if words:
        stats['average_word_length'] = sum(len(word) for word in words) / len(words)
    
    return stats


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
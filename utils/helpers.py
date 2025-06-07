# utils/helpers.py
"""Fonctions utilitaires pour l'application"""

import re
import os
import io
import streamlit as st
from typing import Dict, List, Any
from collections import defaultdict, Counter

from models.dataclasses import Document, PieceSelectionnee

try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

def clean_key(text: str) -> str:
    """Nettoie une chaîne pour en faire une clé Streamlit valide"""
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ô': 'o', 'ö': 'o',
        'î': 'i', 'ï': 'i',
        'ç': 'c',
        ' ': '_', '-': '_', "'": '_', '"': '_',
        '.': '_', ',': '_', '(': '_', ')': '_',
        '[': '_', ']': '_', '/': '_', '\\': '_'
    }
    
    cleaned = text.lower()
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    cleaned = ''.join(c if c.isalnum() or c == '_' else '_' for c in cleaned)
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = cleaned.strip('_')
    
    return cleaned

def initialize_session_state():
    """Initialise toutes les variables de session"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.dossier_actif = None
        st.session_state.dossiers = {}
        st.session_state.pieces_selectionnees = {}
        st.session_state.current_page = 1
        st.session_state.search_query = ""
        st.session_state.docs_for_analysis = []
        st.session_state.document_content = ""
        st.session_state.custom_templates = {}
        st.session_state.letterhead = None
        st.session_state.citation_manager = None
        st.session_state.victimes_adapter = []
        st.session_state.plainte_originale = None
        st.session_state.plaintes_adaptees = {}
        st.session_state.azure_documents = {}
        st.session_state.selected_container = None
        st.session_state.current_folder_path = ""
        st.session_state.style_models = {}
        st.session_state.learned_styles = {}
        st.session_state.vector_store = None
        st.session_state.azure_search_client = None
        st.session_state.azure_blob_manager = None
        st.session_state.azure_search_manager = None
        st.session_state.dynamic_search_prompts = {}
        st.session_state.dynamic_templates = {}
        st.session_state.selected_folders = set()
        st.session_state.letterhead_template = None
        st.session_state.letterhead_image = None

def clean_env_for_azure():
    """Nettoie l'environnement pour Azure sur Hugging Face Spaces"""
    # Supprimer les variables de proxy qui interfèrent avec Azure
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'NO_PROXY', 'no_proxy', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']
    
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    
    # Désactiver les proxies dans requests
    os.environ['CURL_CA_BUNDLE'] = ""
    os.environ['REQUESTS_CA_BUNDLE'] = ""

def create_env_example() -> str:
    """Crée un fichier .env exemple"""
    return """# Azure Search
AZURE_SEARCH_ENDPOINT=https://search-rag-juridique.search.windows.net
AZURE_SEARCH_KEY=Votre_Clé_Azure_Search

# Azure OpenAI pour les embeddings
AZURE_OPENAI_ENDPOINT=https://openai-juridique-rag2.openai.azure.com
AZURE_OPENAI_KEY=Votre_Clé_Azure_OpenAI
AZURE_OPENAI_DEPLOYMENT=text-embedding-ada-002

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=VOTRE_COMPTE;AccountKey=VOTRE_CLE;EndpointSuffix=core.windows.net

# Autres IA (optionnel)
ANTHROPIC_API_KEY=Votre_Clé_Anthropic
OPENAI_API_KEY=Votre_Clé_OpenAI
GOOGLE_API_KEY=Votre_Clé_Google
PERPLEXITY_API_KEY=Votre_Clé_Perplexity"""

def create_letterhead_from_template(template, content: str) -> io.BytesIO:
    """Crée un document avec papier en-tête à partir d'un template"""
    if not DOCX_AVAILABLE:
        return None
    
    try:
        doc = DocxDocument()
        
        # Définir les marges
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(template.margins['top'])
            section.bottom_margin = Inches(template.margins['bottom'])
            section.left_margin = Inches(template.margins['left'])
            section.right_margin = Inches(template.margins['right'])
        
        # Ajouter l'en-tête
        if template.header_content:
            header = doc.sections[0].header
            header_para = header.paragraphs[0]
            header_para.text = template.header_content
            header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Ajouter le contenu principal
        paragraphs = content.split('\n')
        for para_text in paragraphs:
            p = doc.add_paragraph(para_text)
            p.style.font.name = template.font_family
            p.style.font.size = Pt(template.font_size)
            p.paragraph_format.line_spacing = template.line_spacing
        
        # Ajouter le pied de page
        if template.footer_content:
            footer = doc.sections[0].footer
            footer_para = footer.paragraphs[0]
            footer_para.text = template.footer_content
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Sauvegarder en mémoire
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        
        return docx_buffer
        
    except Exception as e:
        st.error(f"Erreur création document avec papier en-tête: {e}")
        return None

# Fonctions de fusion pour les styles
def merge_structures(structures: List[Dict]) -> Dict[str, Any]:
    """Fusionne plusieurs structures de documents"""
    if not structures:
        return {}
    
    merged = {
        'sections_communes': [],
        'longueur_moyenne': 0
    }
    
    # Trouver les sections communes
    all_sections = []
    for struct in structures:
        all_sections.extend([s['titre'] for s in struct.get('sections', [])])
    
    # Compter les occurrences
    section_counts = Counter(all_sections)
    
    # Garder les sections présentes dans au moins 50% des documents
    threshold = len(structures) / 2
    merged['sections_communes'] = [
        section for section, count in section_counts.items()
        if count >= threshold
    ]
    
    # Ajouter les informations Word si présentes
    word_styles = []
    for struct in structures:
        if 'word_styles' in struct:
            word_styles.extend(struct['word_styles'])
    
    if word_styles:
        merged['word_styles'] = list(set(word_styles))
    
    return merged

def merge_formules(formules_list: List[List[str]]) -> List[str]:
    """Fusionne les formules types"""
    all_formules = []
    for formules in formules_list:
        all_formules.extend(formules)
    
    # Compter et garder les plus fréquentes
    formule_counts = Counter(all_formules)
    
    return [formule for formule, count in formule_counts.most_common(20)]

def merge_formatting(formats: List[Dict]) -> Dict[str, Any]:
    """Fusionne les paramètres de mise en forme"""
    if not formats:
        return {}
    
    merged = {}
    
    # Moyennes et valeurs communes
    for key in formats[0].keys():
        values = [f.get(key) for f in formats if key in f]
        
        if all(isinstance(v, bool) for v in values):
            # Pour les booléens, prendre la majorité
            merged[key] = sum(values) > len(values) / 2
        elif all(isinstance(v, (int, float)) for v in values):
            # Pour les nombres, prendre la moyenne
            merged[key] = sum(values) / len(values)
        else:
            # Pour le reste, prendre la valeur la plus fréquente
            merged[key] = Counter(values).most_common(1)[0][0] if values else None
    
    return merged

def merge_vocabulary(vocab_list: List[Dict[str, int]]) -> Dict[str, int]:
    """Fusionne les vocabulaires"""
    merged = defaultdict(int)
    
    for vocab in vocab_list:
        for word, count in vocab.items():
            merged[word] += count
    
    # Garder les 100 mots les plus fréquents
    return dict(sorted(merged.items(), key=lambda x: x[1], reverse=True)[:100])

# Gestionnaire de pièces sélectionnées
class GestionnairePiecesSelectionnees:
    """Gère la sélection et l'organisation des pièces pour un dossier"""
    
    def __init__(self):
        self.pieces: Dict[str, PieceSelectionnee] = {}
        self.categories = [
            "📄 Procédure",
            "💰 Comptabilité",
            "📊 Expertise",
            "📧 Correspondances",
            "📋 Contrats",
            "🏢 Documents sociaux",
            "🔍 Preuves",
            "📑 Autres"
        ]
    
    def ajouter_piece(self, document: Document, categorie: str, notes: str = "", pertinence: int = 5):
        """Ajoute une pièce à la sélection"""
        piece = PieceSelectionnee(
            document_id=document.id,
            titre=document.title,
            categorie=categorie,
            notes=notes,
            pertinence=pertinence
        )
        
        self.pieces[document.id] = piece
        
        # Sauvegarder dans session state
        if 'pieces_selectionnees' not in st.session_state:
            st.session_state.pieces_selectionnees = {}
        st.session_state.pieces_selectionnees[document.id] = piece
    
    def retirer_piece(self, document_id: str):
        """Retire une pièce de la sélection"""
        if document_id in self.pieces:
            del self.pieces[document_id]
        
        if document_id in st.session_state.pieces_selectionnees:
            del st.session_state.pieces_selectionnees[document_id]
    
    def get_pieces_par_categorie(self) -> Dict[str, List[PieceSelectionnee]]:
        """Retourne les pièces organisées par catégorie"""
        pieces_par_cat = {cat: [] for cat in self.categories}
        
        for piece in self.pieces.values():
            if piece.categorie in pieces_par_cat:
                pieces_par_cat[piece.categorie].append(piece)
        
        return pieces_par_cat
    
    def gen
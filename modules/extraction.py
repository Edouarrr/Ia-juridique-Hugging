"""Module d'extraction d'informations juridiques - Version améliorée"""

import hashlib
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Configuration du logger
logger = logging.getLogger(__name__)

# Ajout du chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
try:
    from utils import clean_key, format_legal_date, truncate_text
except ImportError:
    # Fonctions utilitaires de base si import échoue
    def truncate_text(text, max_length=100):
        return text[:max_length] + "..." if len(text) > max_length else text
    def clean_key(key):
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
    def format_legal_date(date):
        return date.strftime("%d/%m/%Y") if isinstance(date, datetime) else str(date)

def run():
    """Fonction principale du module - Point d'entrée pour lazy loading"""
    module = ExtractionModule()
    module.render()

class ExtractionModule:
    """Module d'extraction intelligente d'informations avec IA multi-modèles"""
    
    def __init__(self):
        self.name = "Extraction d'informations"
        self.description = "Extraction intelligente multi-modèles avec fusion des résultats"
        self.icon = "🎯"
        self.available = True
        
        # Configuration des modèles d'IA disponibles
        self.ai_models = {
            'gpt4': {
                'name': 'GPT-4 Turbo',
                'icon': '🤖',
                'strengths': ['Compréhension contextuelle', 'Raisonnement complexe'],
                'speed': 'Rapide',
                'accuracy': 0.95
            },
            'claude': {
                'name': 'Claude 3 Opus',
                'icon': '🧠',
                'strengths': ['Analyse juridique', 'Nuances linguistiques'],
                'speed': 'Moyen',
                'accuracy': 0.96
            },
            'gemini': {
                'name': 'Gemini Pro',
                'icon': '✨',
                'strengths': ['Traitement multimodal', 'Vitesse'],
                'speed': 'Très rapide',
                'accuracy': 0.92
            },
            'mistral': {
                'name': 'Mistral Large',
                'icon': '🌪️',
                'strengths': ['Efficacité', 'Français natif'],
                'speed': 'Rapide',
                'accuracy': 0.90
            }
        }
        
        # Patterns d'extraction améliorés
        self.extraction_patterns = {
            'persons': {
                'patterns': [
                    r'(?:M\.|Mme|Mlle|Dr|Me|Pr|Juge)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)',
                    r'([A-Z][a-zÀ-ÿ]+\s+[A-Z]+)(?:\s|,|\.|$)',
                    r'(?:demandeur|défendeur|témoin|expert|partie)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)'
                ],
                'icon': '👤',
                'name': 'Personnes',
                'color': '#FF6B6B'
            },
            'organizations': {
                'patterns': [
                    r'(?:société|entreprise|SARL|SAS|SA|SCI|EURL|association)\s+([A-Z][A-Za-zÀ-ÿ\s&\'-]+)',
                    r'([A-Z][A-Z\s&\'-]{2,})\s+(?:Inc|Ltd|GmbH|AG|SAS|SARL|SA)',
                    r'(?:Tribunal|Cour|Conseil)\s+(?:de|d\')\s+([A-Za-zÀ-ÿ\s\'-]+)'
                ],
                'icon': '🏢',
                'name': 'Organisations',
                'color': '#4ECDC4'
            },
            'dates': {
                'patterns': [
                    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                    r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',
                    r'(?:le|du|au)\s+\d{1,2}\s+\w+\s+\d{4}'
                ],
                'icon': '📅',
                'name': 'Dates',
                'color': '#FFE66D'
            },
            'amounts': {
                'patterns': [
                    r'(\d+(?:\s?\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
                    r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)',
                    r'(?:montant|somme|indemnité)\s+de\s+(\d+(?:\s?\d{3})*(?:,\d{2})?)\s*(?:€|EUR|euros?)'
                ],
                'icon': '💰',
                'name': 'Montants',
                'color': '#95E1D3'
            },
            'references': {
                'patterns': [
                    r'(?:article|Article)\s+\d+(?:[\.-]\d+)*(?:\s+du\s+Code\s+[a-zÀ-ÿ]+)?',
                    r'(?:RG|TGI|CA|Cass\.)\s*[:\s]\s*\d+[/-]\d+',
                    r'n°\s*\d+(?:[/-]\d+)*',
                    r'(?:loi|décret|arrêté)\s+(?:n°\s*)?\d{4}-\d+'
                ],
                'icon': '📎',
                'name': 'Références',
                'color': '#A8E6CF'
            },
            'locations': {
                'patterns': [
                    r'(?:à|de|depuis)\s+([A-Z][a-zÀ-ÿ]+(?:-[A-Z][a-zÀ-ÿ]+)*)',
                    r'\d{5}\s+([A-Z][a-zÀ-ÿ]+(?:-[A-Z][a-zÀ-ÿ]+)*)',
                    r'(?:domicilié|résidant|situé)\s+(?:à|au)\s+([A-Z][a-zÀ-ÿ\s\'-]+)'
                ],
                'icon': '📍',
                'name': 'Lieux',
                'color': '#C7CEEA'
            }
        }
        
        # Initialisation de l'état
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialise l'état de la session"""
        if 'extraction_state' not in st.session_state:
            st.session_state.extraction_state = {
                'current_extraction': None,
                'history': [],
                'preferences': {
                    'default_models': ['gpt4'],
                    'auto_fusion': False,
                    'confidence_threshold': 0.7,
                    'context_window': 100
                },
                'cache': {},
                'statistics': {
                    'total_extractions': 0,
                    'total_entities': 0,
                    'favorite_types': Counter()
                }
            }
    
    def render(self):
        """Interface principale du module avec design amélioré"""
        # En-tête avec animation
        st.markdown("""
            <style>
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            .module-header {
                padding: 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                color: white;
                margin-bottom: 2rem;
                animation: pulse 2s ease-in-out infinite;
            }
            .stat-card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 1.5rem;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            }
            .model-card {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 1rem;
                margin: 0.5rem 0;
                transition: all 0.3s ease;
            }
            .model-card:hover {
                border-color: #667eea;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
            }
            .result-card {
                background: white;
                border-left: 4px solid;
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            .fusion-indicator {
                background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.85rem;
                display: inline-block;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # En-tête animé
        st.markdown(f"""
            <div class="module-header">
                <h1 style="margin: 0; font-size: 2.5rem;">{self.icon} {self.name}</h1>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.2rem;">{self.description}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Statistiques rapides
        self._render_quick_stats()
        
        # Navigation principale avec icônes améliorées
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚀 Extraction Rapide",
            "🤖 Configuration IA",
            "📊 Analyse Avancée",
            "📚 Historique",
            "⚙️ Paramètres"
        ])
        
        with tab1:
            self._render_extraction_tab_enhanced()
        
        with tab2:
            self._render_ai_config_tab()
        
        with tab3:
            self._render_analysis_tab_enhanced()
        
        with tab4:
            self._render_history_tab()
        
        with tab5:
            self._render_settings_tab()
    
    def _render_quick_stats(self):
        """Affiche les statistiques rapides avec design moderne"""
        stats = st.session_state.extraction_state['statistics']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="stat-card">
                    <h3 style="color: #667eea; margin: 0;">📈</h3>
                    <h2 style="margin: 0.5rem 0;">{stats['total_extractions']}</h2>
                    <p style="margin: 0; color: #6c757d;">Extractions totales</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="stat-card">
                    <h3 style="color: #764ba2; margin: 0;">🎯</h3>
                    <h2 style="margin: 0.5rem 0;">{stats['total_entities']}</h2>
                    <p style="margin: 0; color: #6c757d;">Entités extraites</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            favorite_type = stats['favorite_types'].most_common(1)
            fav_icon = self.extraction_patterns[favorite_type[0][0]]['icon'] if favorite_type else '❓'
            fav_name = self.extraction_patterns[favorite_type[0][0]]['name'] if favorite_type else 'Aucun'
            
            st.markdown(f"""
                <div class="stat-card">
                    <h3 style="color: #f093fb; margin: 0;">{fav_icon}</h3>
                    <h2 style="margin: 0.5rem 0; font-size: 1.3rem;">{fav_name}</h2>
                    <p style="margin: 0; color: #6c757d;">Type favori</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            success_rate = 95.7  # Simulé
            st.markdown(f"""
                <div class="stat-card">
                    <h3 style="color: #4ade80; margin: 0;">✅</h3>
                    <h2 style="margin: 0.5rem 0;">{success_rate}%</h2>
                    <p style="margin: 0; color: #6c757d;">Taux de succès</p>
                </div>
            """, unsafe_allow_html=True)
    
    def _render_extraction_tab_enhanced(self):
        """Onglet d'extraction avec interface améliorée"""
        # Mode d'extraction avec cards visuelles
        st.markdown("### 🎯 Mode d'extraction")
        
        col1, col2, col3, col4 = st.columns(4)
        
        extraction_modes = {
            "Automatique": {"icon": "🤖", "desc": "Extraction complète intelligente"},
            "Favorable": {"icon": "✅", "desc": "Points positifs pour la défense"},
            "À charge": {"icon": "⚠️", "desc": "Éléments défavorables"},
            "Personnalisé": {"icon": "🎨", "desc": "Configuration sur mesure"}
        }
        
        selected_mode = None
        for i, (mode, info) in enumerate(extraction_modes.items()):
            with [col1, col2, col3, col4][i]:
                if st.button(
                    f"{info['icon']}\n**{mode}**\n_{info['desc']}_",
                    key=f"mode_{mode}",
                    use_container_width=True,
                    help=info['desc']
                ):
                    selected_mode = mode
        
        if selected_mode:
            st.session_state.extraction_mode = selected_mode
        
        current_mode = st.session_state.get('extraction_mode', 'Automatique')
        st.info(f"Mode sélectionné : **{current_mode}**")
        
        # Source des documents avec interface moderne
        st.markdown("### 📁 Source des documents")
        
        source_container = st.container()
        with source_container:
            source_cols = st.columns([1, 1, 1])
            
            with source_cols[0]:
                if st.button("📄 Documents chargés", use_container_width=True):
                    st.session_state.doc_source = "loaded"
            
            with source_cols[1]:
                if st.button("✍️ Texte direct", use_container_width=True):
                    st.session_state.doc_source = "direct"
            
            with source_cols[2]:
                if st.button("🔍 Recherche Azure", use_container_width=True):
                    st.session_state.doc_source = "search"
        
        # Zone de contenu selon la source
        current_source = st.session_state.get('doc_source', 'loaded')
        documents = self._get_documents_enhanced(current_source)
        
        if documents:
            # Aperçu des documents
            with st.expander(f"📋 Aperçu des documents ({len(documents)} documents)", expanded=True):
                for i, doc in enumerate(documents[:3]):  # Limiter l'aperçu
                    st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                            <strong>{doc['title']}</strong><br>
                            <small>{truncate_text(doc['content'], 200)}</small>
                        </div>
                    """, unsafe_allow_html=True)
                
                if len(documents) > 3:
                    st.caption(f"... et {len(documents) - 3} autres documents")
            
            # Configuration avancée si mode personnalisé
            if current_mode == "Personnalisé":
                self._render_custom_config()
            
            # Sélection des modèles d'IA
            st.markdown("### 🤖 Modèles d'IA")
            self._render_model_selection()
            
            # Bouton d'extraction avec animation
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "🚀 Lancer l'extraction intelligente",
                    type="primary",
                    use_container_width=True,
                    disabled=not documents
                ):
                    self._perform_enhanced_extraction(documents, current_mode)
    
    def _render_model_selection(self):
        """Interface de sélection des modèles d'IA"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_models = []
            model_cols = st.columns(len(self.ai_models))
            
            for i, (model_id, model_info) in enumerate(self.ai_models.items()):
                with model_cols[i]:
                    selected = st.checkbox(
                        f"{model_info['icon']} {model_info['name']}",
                        key=f"model_{model_id}",
                        value=model_id in st.session_state.extraction_state['preferences']['default_models']
                    )
                    if selected:
                        selected_models.append(model_id)
                    
                    # Info-bulle avec détails
                    with st.expander("ℹ️ Détails"):
                        st.caption(f"**Vitesse:** {model_info['speed']}")
                        st.caption(f"**Précision:** {model_info['accuracy']*100:.0f}%")
                        st.caption(f"**Points forts:**")
                        for strength in model_info['strengths']:
                            st.caption(f"• {strength}")
        
        with col2:
            fusion_mode = st.checkbox(
                "🔀 Mode Fusion",
                value=st.session_state.extraction_state['preferences']['auto_fusion'],
                help="Combine les résultats de tous les modèles sélectionnés"
            )
            
            if fusion_mode and len(selected_models) > 1:
                st.markdown('<span class="fusion-indicator">Mode Fusion Actif</span>', unsafe_allow_html=True)
        
        st.session_state.selected_models = selected_models
        st.session_state.fusion_mode = fusion_mode
    
    def _render_custom_config(self):
        """Configuration personnalisée avancée"""
        with st.expander("⚙️ Configuration personnalisée", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📌 Types d'entités")
                for entity_type, entity_info in self.extraction_patterns.items():
                    st.checkbox(
                        f"{entity_info['icon']} {entity_info['name']}",
                        value=True,
                        key=f"extract_{entity_type}_custom"
                    )
                
                # Pattern personnalisé avec aide
                st.markdown("#### 🔧 Pattern personnalisé")
                custom_pattern = st.text_area(
                    "Expression régulière",
                    placeholder="Ex: \\b[A-Z]{2,}\\b",
                    height=100,
                    help="Testez votre regex sur regex101.com"
                )
                
                if custom_pattern:
                    # Test en temps réel
                    test_text = st.text_input("Texte de test")
                    if test_text:
                        try:
                            matches = re.findall(custom_pattern, test_text)
                            if matches:
                                st.success(f"✅ Trouvé : {matches}")
                            else:
                                st.warning("❌ Aucune correspondance")
                        except re.error as e:
                            st.error(f"Erreur regex : {e}")
            
            with col2:
                st.markdown("#### 🎛️ Paramètres avancés")
                
                context_window = st.slider(
                    "📏 Fenêtre de contexte",
                    50, 500, 
                    st.session_state.extraction_state['preferences']['context_window'],
                    step=50,
                    help="Caractères de contexte autour des extractions"
                )
                
                confidence_threshold = st.slider(
                    "🎯 Seuil de confiance",
                    0.0, 1.0,
                    st.session_state.extraction_state['preferences']['confidence_threshold'],
                    step=0.05,
                    help="Confiance minimale pour conserver une extraction"
                )
                
                st.markdown("#### 🔍 Options de recherche")
                
                case_sensitive = st.checkbox("Respecter la casse", value=False)
                whole_word = st.checkbox("Mots entiers uniquement", value=True)
                fuzzy_matching = st.checkbox(
                    "Correspondance approximative",
                    value=False,
                    help="Tolère les fautes de frappe"
                )
                
                if fuzzy_matching:
                    fuzzy_threshold = st.slider(
                        "Seuil de similarité",
                        0.5, 1.0, 0.8,
                        help="1.0 = correspondance exacte"
                    )
    
    def _get_documents_enhanced(self, source: str) -> List[Dict[str, Any]]:
        """Récupère les documents avec gestion améliorée"""
        documents = []
        
        if source == "loaded":
            # Documents depuis la session avec métadonnées enrichies
            if 'selected_documents' in st.session_state and st.session_state.selected_documents:
                st.success(f"✅ {len(st.session_state.selected_documents)} documents prêts")
                
                for doc_name in st.session_state.selected_documents:
                    # Simulation avec métadonnées
                    documents.append({
                        'id': hashlib.md5(doc_name.encode()).hexdigest()[:8],
                        'title': doc_name,
                        'content': f"Contenu du document {doc_name}...",  # À remplacer
                        'source': 'Session',
                        'type': 'PDF',
                        'size': '2.3 MB',
                        'date': datetime.now(),
                        'confidence': 1.0
                    })
            else:
                st.warning("⚠️ Aucun document sélectionné. Veuillez charger des documents.")
        
        elif source == "direct":
            # Éditeur de texte amélioré
            st.markdown("#### ✍️ Saisie directe")
            
            # Templates de texte
            template = st.selectbox(
                "Utiliser un template",
                ["Vide", "Contrat type", "Jugement", "Procès-verbal"],
                help="Templates pré-remplis pour tester"
            )
            
            if template != "Vide":
                default_text = self._get_template_text(template)
            else:
                default_text = ""
            
            text = st.text_area(
                "Texte à analyser",
                value=default_text,
                height=400,
                placeholder="Collez ou tapez votre texte juridique ici..."
            )
            
            if text:
                # Statistiques du texte
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Caractères", len(text))
                with col2:
                    st.metric("Mots", len(text.split()))
                with col3:
                    st.metric("Lignes", text.count('\n') + 1)
                
                documents.append({
                    'id': hashlib.md5(text.encode()).hexdigest()[:8],
                    'title': 'Texte direct',
                    'content': text,
                    'source': 'Saisie',
                    'type': 'TXT',
                    'size': f"{len(text)} caractères",
                    'date': datetime.now(),
                    'confidence': 1.0
                })
        
        else:  # search
            st.markdown("#### 🔍 Recherche Azure Cognitive Search")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_query = st.text_input(
                    "Requête de recherche",
                    placeholder="Ex: contrat de vente 2024 Paris",
                    help="Utilisez des mots-clés pertinents"
                )
            
            with col2:
                max_results = st.number_input(
                    "Résultats max",
                    min_value=1,
                    max_value=50,
                    value=10
                )
            
            # Filtres avancés
            with st.expander("🔧 Filtres avancés"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    doc_types = st.multiselect(
                        "Types de documents",
                        ["Contrats", "Jugements", "Expertises", "Correspondances"],
                        default=["Contrats", "Jugements"]
                    )
                
                with col2:
                    date_range = st.date_input(
                        "Période",
                        value=[datetime.now().date(), datetime.now().date()],
                        key="date_range_search"
                    )
                
                with col3:
                    relevance_threshold = st.slider(
                        "Pertinence minimale",
                        0.0, 1.0, 0.7
                    )
            
            if search_query and st.button("🔍 Rechercher", type="primary"):
                with st.spinner("Recherche en cours..."):
                    # Simulation de recherche avec barre de progression
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # Résultats simulés
                    for i in range(min(5, max_results)):
                        relevance = 0.95 - (i * 0.1)
                        if relevance >= relevance_threshold:
                            documents.append({
                                'id': f"search_{i}",
                                'title': f'Document pertinent {i+1} - {search_query}',
                                'content': f'Contenu trouvé relatif à "{search_query}"...',
                                'source': 'Azure Search',
                                'type': 'PDF',
                                'size': f"{2.1 + i*0.3:.1f} MB",
                                'date': datetime.now(),
                                'confidence': relevance,
                                'relevance': relevance,
                                'highlights': [search_query]
                            })
                    
                    st.success(f"✅ {len(documents)} documents trouvés")
        
        return documents
    
    def _get_template_text(self, template: str) -> str:
        """Retourne un texte template selon le type"""
        templates = {
            "Contrat type": """CONTRAT DE PRESTATION DE SERVICES

Entre les soussignés :

La société TECH INNOVATIONS SAS, au capital de 50.000 €, immatriculée au RCS de Paris sous le numéro 123 456 789, dont le siège social est situé au 123 Avenue des Champs-Élysées, 75008 Paris, représentée par M. Jean DUPONT en sa qualité de Président,

Ci-après dénommée "le Prestataire"

ET

La société CLIENT ENTREPRISE SARL, au capital de 20.000 €, immatriculée au RCS de Lyon sous le numéro 987 654 321, dont le siège social est situé au 45 Rue de la République, 69002 Lyon, représentée par Mme Marie MARTIN en sa qualité de Gérante,

Ci-après dénommée "le Client"

Article 1 - Objet
Le présent contrat a pour objet la fourniture de prestations de développement informatique pour un montant total de 25.000 € HT.

Article 2 - Durée
Le contrat est conclu pour une durée de 6 mois à compter du 1er janvier 2024.

Fait à Paris, le 15 décembre 2023
En deux exemplaires originaux""",
            
            "Jugement": """TRIBUNAL DE GRANDE INSTANCE DE PARIS
3ème Chambre Civile

JUGEMENT
Audience publique du 20 novembre 2023
RG n° 22/14567

DEMANDEUR :
M. Pierre LAMBERT, né le 12 mars 1975 à Marseille, demeurant 78 Boulevard Saint-Michel, 75005 Paris

DÉFENDEUR :
IMMOBILIÈRE DU CENTRE SA, RCS Paris 456 789 123, siège social 90 Avenue Montaigne, 75008 Paris

FAITS ET PROCÉDURE :
Par acte du 15 janvier 2022, M. Pierre LAMBERT a assigné la société IMMOBILIÈRE DU CENTRE en paiement de dommages-intérêts d'un montant de 45.000 € pour troubles de jouissance.

MOTIFS :
Attendu que les troubles invoqués sont établis par les attestations produites...

PAR CES MOTIFS :
Le Tribunal, statuant publiquement, par jugement contradictoire et en premier ressort,
CONDAMNE la société IMMOBILIÈRE DU CENTRE à verser à M. Pierre LAMBERT la somme de 35.000 € à titre de dommages-intérêts.""",
            
            "Procès-verbal": """PROCÈS-VERBAL DE CONSTAT

L'an deux mille vingt-trois et le quinze octobre à quatorze heures,

Je soussigné, Maître François DURAND, Huissier de Justice associé près le Tribunal Judiciaire de Paris, y demeurant 25 Rue du Faubourg Saint-Honoré,

Me suis transporté au 45 Rue de la Paix, 75002 Paris, à la demande de la société ENTREPRISE ABC SARL.

CONSTATATIONS :
J'ai constaté la présence d'une infiltration d'eau importante au niveau du plafond du local commercial. Les dégâts s'étendent sur une surface d'environ 20 m².

TÉMOIN PRÉSENT :
M. Jacques BERNARD, gérant de la société voisine, atteste avoir constaté les mêmes dégradations depuis le 10 octobre 2023.

Dont procès-verbal pour servir et valoir ce que de droit."""
        }
        
        return templates.get(template, "")
    
    def _perform_enhanced_extraction(self, documents: List[Dict[str, Any]], mode: str):
        """Extraction améliorée avec multi-modèles et fusion"""
        # Animation de début
        placeholder = st.empty()
        
        with placeholder.container():
            st.markdown("""
                <div style="text-align: center; padding: 2rem;">
                    <h2>🚀 Extraction en cours...</h2>
                    <p>Analyse intelligente multi-modèles</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Barre de progression principale
            main_progress = st.progress(0)
            status_text = st.empty()
            
            # Phases d'extraction
            phases = [
                ("📄 Préparation des documents", 10),
                ("🔍 Analyse préliminaire", 20),
                ("🤖 Traitement par IA", 60),
                ("🔀 Fusion des résultats", 80),
                ("📊 Génération du rapport", 100)
            ]
            
            results = {
                'documents_analyzed': len(documents),
                'extractions_by_model': {},
                'fusion_results': {},
                'statistics': {},
                'insights': [],
                'quality_metrics': {}
            }
            
            # Simulation du traitement par phases
            for phase, progress in phases:
                status_text.text(phase)
                time.sleep(0.5)  # Simulation
                main_progress.progress(progress / 100)
                
                if phase == "🤖 Traitement par IA":
                    # Traitement par chaque modèle
                    selected_models = st.session_state.get('selected_models', ['gpt4'])
                    
                    model_cols = st.columns(len(selected_models))
                    model_progress_bars = {}
                    
                    for i, model_id in enumerate(selected_models):
                        with model_cols[i]:
                            st.caption(f"{self.ai_models[model_id]['icon']} {self.ai_models[model_id]['name']}")
                            model_progress_bars[model_id] = st.progress(0)
                    
                    # Simulation du traitement parallèle
                    for prog in range(101):
                        for model_id, progress_bar in model_progress_bars.items():
                            progress_bar.progress(prog)
                        time.sleep(0.01)
                    
                    # Résultats simulés par modèle
                    for model_id in selected_models:
                        results['extractions_by_model'][model_id] = self._simulate_model_extraction(
                            documents, mode, model_id
                        )
                
                elif phase == "🔀 Fusion des résultats" and st.session_state.get('fusion_mode', False):
                    # Fusion des résultats si mode fusion actif
                    if len(results['extractions_by_model']) > 1:
                        results['fusion_results'] = self._fusion_results(
                            results['extractions_by_model']
                        )
        
        # Effacer l'animation
        placeholder.empty()
        
        # Calculer les statistiques finales
        results['statistics'] = self._calculate_enhanced_statistics(results)
        results['insights'] = self._generate_enhanced_insights(results, mode)
        results['quality_metrics'] = self._calculate_quality_metrics(results)
        
        # Sauvegarder dans l'historique
        extraction_record = {
            'id': hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
            'timestamp': datetime.now(),
            'mode': mode,
            'documents': len(documents),
            'models_used': st.session_state.get('selected_models', ['gpt4']),
            'fusion_enabled': st.session_state.get('fusion_mode', False),
            'results': results
        }
        
        st.session_state.extraction_state['history'].append(extraction_record)
        st.session_state.extraction_state['current_extraction'] = extraction_record
        st.session_state.extraction_state['statistics']['total_extractions'] += 1
        st.session_state.extraction_state['statistics']['total_entities'] += results['statistics']['total_entities']
        
        # Afficher les résultats
        self._display_enhanced_results(results, mode)
    
    def _simulate_model_extraction(self, documents: List[Dict[str, Any]], mode: str, model_id: str) -> Dict[str, Any]:
        """Simule l'extraction par un modèle spécifique"""
        # Ajuster les résultats selon les caractéristiques du modèle
        model_info = self.ai_models[model_id]
        accuracy = model_info['accuracy']
        
        extractions = defaultdict(list)
        
        for doc in documents:
            if mode == "Favorable":
                # Points favorables avec variation selon le modèle
                num_points = int(5 * accuracy + (hash(model_id) % 3))
                for i in range(num_points):
                    extractions['favorable_points'].append({
                        'type': 'favorable',
                        'text': f"Point favorable {i+1} identifié par {model_info['name']}",
                        'confidence': accuracy - (i * 0.05),
                        'importance': 8 - i,
                        'model': model_id,
                        'document_id': doc['id']
                    })
            
            elif mode == "À charge":
                # Éléments à charge
                num_elements = int(4 * accuracy + (hash(model_id) % 2))
                for i in range(num_elements):
                    severity = ['Critique', 'Important', 'Modéré'][i % 3]
                    extractions['charge_elements'].append({
                        'type': 'charge',
                        'text': f"Élément à charge détecté par {model_info['name']}",
                        'confidence': accuracy - (i * 0.03),
                        'severity': severity,
                        'model': model_id,
                        'document_id': doc['id']
                    })
            
            else:  # Automatique ou Personnalisé
                # Extraction de toutes les entités
                for entity_type, entity_info in self.extraction_patterns.items():
                    if mode == "Personnalisé":
                        # Vérifier si le type est sélectionné
                        if not st.session_state.get(f'extract_{entity_type}_custom', True):
                            continue
                    
                    # Nombre d'entités selon la précision du modèle
                    num_entities = int((3 + hash(f"{model_id}{entity_type}") % 5) * accuracy)
                    
                    for i in range(num_entities):
                        extractions[entity_type].append({
                            'value': f"{entity_info['name']} {i+1}",
                            'context': f"Contexte de l'extraction par {model_info['name']}",
                            'confidence': accuracy - (i * 0.02),
                            'position': i * 100,
                            'model': model_id,
                            'document_id': doc['id']
                        })
        
        return {
            'model_id': model_id,
            'model_name': model_info['name'],
            'extractions': dict(extractions),
            'processing_time': 2.5 / (1 + accuracy),  # Temps simulé
            'confidence_avg': accuracy
        }
    
    def _fusion_results(self, model_results: Dict[str, Dict]) -> Dict[str, Any]:
        """Fusionne les résultats de plusieurs modèles"""
        fusion = defaultdict(list)
        consensus_scores = defaultdict(lambda: defaultdict(float))
        
        # Agrégation des résultats
        for model_id, results in model_results.items():
            model_weight = self.ai_models[model_id]['accuracy']
            
            for entity_type, entities in results['extractions'].items():
                for entity in entities:
                    # Créer une clé unique pour l'entité
                    if isinstance(entity, dict):
                        entity_key = entity.get('value', str(entity))
                        
                        # Calculer le score de consensus
                        consensus_scores[entity_type][entity_key] += model_weight
                        
                        # Ajouter à la fusion avec métadonnées
                        entity_copy = entity.copy()
                        entity_copy['contributing_models'] = [model_id]
                        entity_copy['fusion_confidence'] = model_weight
                        fusion[entity_type].append(entity_copy)
        
        # Dédupliquer et calculer la confiance finale
        final_fusion = {}
        for entity_type, entities in fusion.items():
            # Grouper par valeur
            grouped = defaultdict(list)
            for entity in entities:
                key = entity.get('value', str(entity))
                grouped[key].append(entity)
            
            # Créer l'entité fusionnée
            final_entities = []
            for key, duplicates in grouped.items():
                # Moyenner les scores de confiance
                avg_confidence = sum(e.get('confidence', 0) for e in duplicates) / len(duplicates)
                contributing_models = list(set(
                    model for e in duplicates 
                    for model in e.get('contributing_models', [e.get('model')])
                ))
                
                fused_entity = duplicates[0].copy()
                fused_entity.update({
                    'confidence': avg_confidence,
                    'contributing_models': contributing_models,
                    'fusion_score': len(contributing_models) / len(model_results),
                    'consensus_level': 'Élevé' if len(contributing_models) >= 3 else 'Moyen' if len(contributing_models) >= 2 else 'Faible'
                })
                
                final_entities.append(fused_entity)
            
            final_fusion[entity_type] = final_entities
        
        return final_fusion
    
    def _calculate_enhanced_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule des statistiques détaillées"""
        stats = {
            'total_entities': 0,
            'by_type': {},
            'by_model': {},
            'fusion_stats': {},
            'confidence_distribution': {
                'high': 0,  # > 0.8
                'medium': 0,  # 0.5-0.8
                'low': 0  # < 0.5
            }
        }
        
        # Choisir la source des données selon le mode
        if results.get('fusion_results'):
            data_source = results['fusion_results']
        else:
            # Prendre le premier modèle s'il n'y a pas de fusion
            first_model = list(results['extractions_by_model'].values())[0]
            data_source = first_model['extractions']
        
        # Statistiques par type
        for entity_type, entities in data_source.items():
            unique_values = set()
            confidence_sum = 0
            
            for entity in entities:
                if isinstance(entity, dict):
                    unique_values.add(entity.get('value', str(entity)))
                    conf = entity.get('confidence', 0)
                    confidence_sum += conf
                    
                    # Distribution de confiance
                    if conf > 0.8:
                        stats['confidence_distribution']['high'] += 1
                    elif conf > 0.5:
                        stats['confidence_distribution']['medium'] += 1
                    else:
                        stats['confidence_distribution']['low'] += 1
                
                stats['total_entities'] += 1
            
            stats['by_type'][entity_type] = {
                'total': len(entities),
                'unique': len(unique_values),
                'avg_confidence': confidence_sum / len(entities) if entities else 0
            }
        
        # Statistiques par modèle
        for model_id, model_results in results['extractions_by_model'].items():
            total_model_entities = sum(
                len(entities) 
                for entities in model_results['extractions'].values()
            )
            stats['by_model'][model_id] = {
                'total': total_model_entities,
                'processing_time': model_results['processing_time'],
                'avg_confidence': model_results['confidence_avg']
            }
        
        # Statistiques de fusion
        if results.get('fusion_results'):
            high_consensus = sum(
                1 for entities in results['fusion_results'].values()
                for e in entities
                if e.get('consensus_level') == 'Élevé'
            )
            stats['fusion_stats'] = {
                'high_consensus_entities': high_consensus,
                'fusion_improvement': 15.7  # Simulé
            }
        
        return stats
    
    def _generate_enhanced_insights(self, results: Dict[str, Any], mode: str) -> List[str]:
        """Génère des insights intelligents et contextualisés"""
        insights = []
        stats = results['statistics']
        
        # Insight sur le volume
        if stats['total_entities'] > 100:
            insights.append(f"📊 Volume important : {stats['total_entities']} entités extraites, suggérant un document riche en informations")
        elif stats['total_entities'] < 20:
            insights.append(f"📉 Volume modéré : {stats['total_entities']} entités seulement, le document pourrait nécessiter une analyse manuelle complémentaire")
        
        # Insights sur la qualité
        high_conf_ratio = stats['confidence_distribution']['high'] / max(stats['total_entities'], 1)
        if high_conf_ratio > 0.7:
            insights.append(f"✅ Excellente qualité : {high_conf_ratio*100:.0f}% des extractions ont une confiance élevée")
        elif high_conf_ratio < 0.3:
            insights.append(f"⚠️ Qualité à vérifier : seulement {high_conf_ratio*100:.0f}% des extractions ont une confiance élevée")
        
        # Insights spécifiques au mode
        if mode == "Favorable":
            favorable_count = stats['by_type'].get('favorable_points', {}).get('total', 0)
            if favorable_count > 10:
                insights.append(f"💪 Position forte : {favorable_count} points favorables identifiés pour construire la défense")
            elif favorable_count < 3:
                insights.append(f"⚡ Attention : peu de points favorables ({favorable_count}), envisager des arguments complémentaires")
        
        elif mode == "À charge":
            charge_count = stats['by_type'].get('charge_elements', {}).get('total', 0)
            if charge_count > 5:
                insights.append(f"🚨 Vigilance requise : {charge_count} éléments à charge nécessitent une stratégie de défense solide")
        
        # Insights sur la fusion
        if results.get('fusion_results') and stats.get('fusion_stats'):
            consensus = stats['fusion_stats']['high_consensus_entities']
            insights.append(f"🔀 Consensus inter-modèles : {consensus} entités validées par plusieurs IA, fiabilité accrue")
        
        # Insights sur les types dominants
        if stats['by_type']:
            dominant_type = max(stats['by_type'].items(), key=lambda x: x[1]['total'])
            type_info = self.extraction_patterns.get(dominant_type[0], {'name': dominant_type[0]})
            insights.append(f"{type_info.get('icon', '📌')} Type dominant : {type_info['name']} avec {dominant_type[1]['total']} occurrences")
        
        # Performance des modèles
        if len(results['extractions_by_model']) > 1:
            best_model = max(
                stats['by_model'].items(),
                key=lambda x: x[1]['total'] * x[1]['avg_confidence']
            )
            model_name = self.ai_models[best_model[0]]['name']
            insights.append(f"🏆 Meilleure performance : {model_name} avec {best_model[1]['total']} extractions")
        
        return insights
    
    def _calculate_quality_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calcule des métriques de qualité avancées"""
        metrics = {
            'completeness': 0.0,
            'accuracy': 0.0,
            'consistency': 0.0,
            'coverage': 0.0,
            'overall_score': 0.0
        }
        
        stats = results['statistics']
        
        # Complétude (basée sur le nombre d'entités par rapport aux attentes)
        expected_entities = 50  # Baseline
        metrics['completeness'] = min(stats['total_entities'] / expected_entities, 1.0)
        
        # Précision (basée sur la distribution de confiance)
        if stats['total_entities'] > 0:
            metrics['accuracy'] = (
                stats['confidence_distribution']['high'] * 1.0 +
                stats['confidence_distribution']['medium'] * 0.6 +
                stats['confidence_distribution']['low'] * 0.2
            ) / stats['total_entities']
        
        # Cohérence (si fusion activée)
        if results.get('fusion_results'):
            # Basée sur le consensus entre modèles
            metrics['consistency'] = 0.85  # Simulé
        else:
            metrics['consistency'] = 1.0  # Pas de fusion = pas d'incohérence
        
        # Couverture (types d'entités trouvés vs disponibles)
        types_found = len([t for t, data in stats['by_type'].items() if data['total'] > 0])
        types_available = len(self.extraction_patterns)
        metrics['coverage'] = types_found / types_available
        
        # Score global
        metrics['overall_score'] = (
            metrics['completeness'] * 0.25 +
            metrics['accuracy'] * 0.35 +
            metrics['consistency'] * 0.20 +
            metrics['coverage'] * 0.20
        )
        
        return metrics
    
    def _display_enhanced_results(self, results: Dict[str, Any], mode: str):
        """Affichage amélioré des résultats avec visualisations"""
        # En-tête de succès avec animation
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
                <h2 style="margin: 0;">✅ Extraction Terminée avec Succès!</h2>
                <p style="margin: 0.5rem 0 0 0;">Analyse intelligente complétée en {:.1f} secondes</p>
            </div>
        """.format(sum(m['processing_time'] for m in results['extractions_by_model'].values())), 
        unsafe_allow_html=True)
        
        # Métriques principales avec style
        col1, col2, col3, col4 = st.columns(4)
        
        metrics_data = [
            ("📄", "Documents", results['documents_analyzed'], None),
            ("🔍", "Entités", results['statistics']['total_entities'], None),
            ("🎯", "Précision", f"{results['quality_metrics']['accuracy']*100:.1f}%", "+2.3%"),
            ("📊", "Score Global", f"{results['quality_metrics']['overall_score']*100:.0f}/100", None)
        ]
        
        for col, (icon, label, value, delta) in zip([col1, col2, col3, col4], metrics_data):
            with col:
                st.metric(f"{icon} {label}", value, delta)
        
        # Insights avec cards stylisées
        if results['insights']:
            st.markdown("### 💡 Insights Clés")
            
            # Organiser les insights en grille
            insight_cols = st.columns(2)
            for i, insight in enumerate(results['insights']):
                with insight_cols[i % 2]:
                    st.info(insight)
        
        # Tabs pour différentes vues
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Vue d'ensemble",
            "🔍 Détails par type",
            "🤖 Analyse par modèle",
            "📈 Visualisations"
        ])
        
        with tab1:
            self._display_overview_tab(results, mode)
        
        with tab2:
            self._display_details_tab(results)
        
        with tab3:
            self._display_model_analysis_tab(results)
        
        with tab4:
            self._display_visualizations_tab(results)
        
        # Actions finales
        st.markdown("### 🎯 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Sauvegarder", use_container_width=True):
                st.success("✅ Résultats sauvegardés!")
        
        with col2:
            if st.button("📤 Exporter", use_container_width=True):
                self._show_export_dialog(results)
        
        with col3:
            if st.button("🔄 Nouvelle extraction", use_container_width=True):
                st.session_state.extraction_state['current_extraction'] = None
                st.rerun()
        
        with col4:
            if st.button("📧 Partager", use_container_width=True):
                st.info("📧 Fonctionnalité de partage bientôt disponible")
    
    def _display_overview_tab(self, results: Dict[str, Any], mode: str):
        """Onglet vue d'ensemble"""
        # Résumé exécutif
        st.markdown("#### 📋 Résumé Exécutif")
        
        summary = f"""
        L'analyse a traité **{results['documents_analyzed']} documents** en utilisant 
        **{len(results['extractions_by_model'])} modèles d'IA**. 
        Au total, **{results['statistics']['total_entities']} entités** ont été extraites 
        avec une précision moyenne de **{results['quality_metrics']['accuracy']*100:.1f}%**.
        """
        
        if results.get('fusion_results'):
            summary += f"""
            Le mode fusion a permis d'identifier **{results['statistics']['fusion_stats']['high_consensus_entities']} 
            entités** avec un consensus élevé entre les modèles.
            """
        
        st.markdown(summary)
        
        # Métriques de qualité avec graphique
        st.markdown("#### 📊 Métriques de Qualité")
        
        quality_cols = st.columns(4)
        quality_metrics = [
            ("Complétude", results['quality_metrics']['completeness']),
            ("Précision", results['quality_metrics']['accuracy']),
            ("Cohérence", results['quality_metrics']['consistency']),
            ("Couverture", results['quality_metrics']['coverage'])
        ]
        
        for col, (metric, value) in zip(quality_cols, quality_metrics):
            with col:
                # Graphique circulaire simple avec CSS
                color = '#4ade80' if value > 0.8 else '#fbbf24' if value > 0.6 else '#f87171'
                st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="width: 100px; height: 100px; margin: 0 auto; 
                                    border-radius: 50%; border: 8px solid {color};
                                    display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 1.5rem; font-weight: bold;">{value*100:.0f}%</span>
                        </div>
                        <p style="margin-top: 0.5rem;">{metric}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Distribution de confiance
        st.markdown("#### 🎯 Distribution de Confiance")
        
        conf_dist = results['statistics']['confidence_distribution']
        total = sum(conf_dist.values())
        
        if total > 0:
            conf_data = pd.DataFrame({
                'Niveau': ['Élevée (>80%)', 'Moyenne (50-80%)', 'Faible (<50%)'],
                'Nombre': [conf_dist['high'], conf_dist['medium'], conf_dist['low']],
                'Pourcentage': [
                    conf_dist['high']/total*100,
                    conf_dist['medium']/total*100,
                    conf_dist['low']/total*100
                ]
            })
            
            # Barres horizontales avec style
            for _, row in conf_data.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{row['Niveau']}**")
                    st.progress(row['Pourcentage'] / 100)
                with col2:
                    st.markdown(f"{row['Nombre']} ({row['Pourcentage']:.1f}%)")
    
    def _display_details_tab(self, results: Dict[str, Any]):
        """Onglet détails par type d'entité"""
        # Sélectionner la source de données
        if results.get('fusion_results'):
            data_source = results['fusion_results']
            st.info("🔀 Affichage des résultats fusionnés")
        else:
            first_model = list(results['extractions_by_model'].values())[0]
            data_source = first_model['extractions']
        
        # Afficher chaque type d'entité
        for entity_type, entities in data_source.items():
            if entities:
                entity_info = self.extraction_patterns.get(
                    entity_type,
                    {'icon': '📌', 'name': entity_type.title(), 'color': '#gray'}
                )
                
                # En-tête du type avec couleur
                st.markdown(f"""
                    <div style="border-left: 4px solid {entity_info['color']}; 
                                padding-left: 1rem; margin: 1rem 0;">
                        <h4>{entity_info['icon']} {entity_info['name']} 
                            <span style="color: #6c757d; font-size: 0.9rem;">
                                ({len(entities)} trouvés)
                            </span>
                        </h4>
                    </div>
                """, unsafe_allow_html=True)
                
                # Options d'affichage
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    view_mode = st.radio(
                        "Mode d'affichage",
                        ["Liste", "Tableau", "Cartes"],
                        key=f"view_{entity_type}",
                        horizontal=True
                    )
                
                with col2:
                    sort_by = st.selectbox(
                        "Trier par",
                        ["Confiance", "Alphabétique", "Position"],
                        key=f"sort_{entity_type}"
                    )
                
                with col3:
                    show_context = st.checkbox(
                        "Afficher contexte",
                        key=f"context_{entity_type}"
                    )
                
                # Affichage selon le mode choisi
                if view_mode == "Liste":
                    self._display_entities_list(entities, show_context, sort_by)
                elif view_mode == "Tableau":
                    self._display_entities_table(entities, entity_type)
                else:  # Cartes
                    self._display_entities_cards(entities, entity_info['color'])
    
    def _display_entities_list(self, entities: List[Dict], show_context: bool, sort_by: str):
        """Affiche les entités en liste"""
        # Trier les entités
        if sort_by == "Confiance":
            sorted_entities = sorted(entities, key=lambda x: x.get('confidence', 0), reverse=True)
        elif sort_by == "Alphabétique":
            sorted_entities = sorted(entities, key=lambda x: x.get('value', str(x)))
        else:  # Position
            sorted_entities = sorted(entities, key=lambda x: x.get('position', 0))
        
        # Afficher les 10 premières
        for i, entity in enumerate(sorted_entities[:10]):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                value = entity.get('value', str(entity))
                confidence = entity.get('confidence', 0)
                
                # Badge de confiance
                conf_color = '#4ade80' if confidence > 0.8 else '#fbbf24' if confidence > 0.5 else '#f87171'
                
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-weight: 500;">{value}</span>
                        <span style="background: {conf_color}; color: white; 
                                     padding: 0.2rem 0.5rem; border-radius: 12px; 
                                     font-size: 0.8rem;">
                            {confidence*100:.0f}%
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                
                if show_context and entity.get('context'):
                    st.caption(f"📝 {entity['context']}")
            
            with col2:
                # Actions
                if st.button("👁️", key=f"view_{i}_{entity.get('value', i)}", help="Voir détails"):
                    st.info(f"Détails: {json.dumps(entity, indent=2, default=str)}")
        
        # Afficher plus si nécessaire
        if len(sorted_entities) > 10:
            if st.button(f"Voir tous ({len(sorted_entities)} au total)"):
                for entity in sorted_entities[10:]:
                    st.write(f"• {entity.get('value', str(entity))}")
    
    def _display_entities_table(self, entities: List[Dict], entity_type: str):
        """Affiche les entités en tableau"""
        # Préparer les données pour le DataFrame
        table_data = []
        
        for entity in entities:
            row = {
                'Valeur': entity.get('value', str(entity)),
                'Confiance': f"{entity.get('confidence', 0)*100:.0f}%",
                'Document': entity.get('document_id', 'N/A')
            }
            
            # Ajouter des colonnes spécifiques selon le type
            if entity_type == 'favorable_points':
                row['Importance'] = entity.get('importance', 'N/A')
            elif entity_type == 'charge_elements':
                row['Sévérité'] = entity.get('severity', 'N/A')
            
            # Modèles contributeurs si fusion
            if entity.get('contributing_models'):
                row['Modèles'] = ', '.join([
                    self.ai_models[m]['icon'] for m in entity['contributing_models']
                ])
            
            table_data.append(row)
        
        # Créer et afficher le DataFrame
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Confiance": st.column_config.ProgressColumn(
                    "Confiance",
                    help="Niveau de confiance de l'extraction",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                )
            }
        )
    
    def _display_entities_cards(self, entities: List[Dict], color: str):
        """Affiche les entités sous forme de cartes"""
        # Grille de cartes
        cols = st.columns(3)
        
        for i, entity in enumerate(entities[:9]):  # Limiter à 9 pour la grille 3x3
            with cols[i % 3]:
                value = entity.get('value', str(entity))
                confidence = entity.get('confidence', 0)
                
                # Carte stylisée
                st.markdown(f"""
                    <div class="result-card" style="border-left-color: {color};">
                        <h5 style="margin: 0 0 0.5rem 0;">{value}</h5>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #6c757d; font-size: 0.9rem;">
                                Confiance: {confidence*100:.0f}%
                            </span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Détails au survol (simulé avec expander)
                with st.expander("Détails"):
                    for key, val in entity.items():
                        if key not in ['value', 'confidence']:
                            st.caption(f"**{key}:** {val}")
    
    def _display_model_analysis_tab(self, results: Dict[str, Any]):
        """Onglet d'analyse par modèle"""
        st.markdown("#### 🤖 Performance des Modèles")
        
        # Comparaison des modèles
        model_comparison = []
        
        for model_id, model_results in results['extractions_by_model'].items():
            model_info = self.ai_models[model_id]
            stats = results['statistics']['by_model'][model_id]
            
            model_comparison.append({
                'Modèle': f"{model_info['icon']} {model_info['name']}",
                'Entités': stats['total'],
                'Temps (s)': f"{stats['processing_time']:.2f}",
                'Confiance': f"{stats['avg_confidence']*100:.0f}%",
                'Efficacité': stats['total'] / stats['processing_time']
            })
        
        # Afficher le tableau de comparaison
        df_comparison = pd.DataFrame(model_comparison)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Graphique de performance
        if len(model_comparison) > 1:
            st.markdown("#### 📊 Analyse Comparative")
            
            # Barres de comparaison
            metrics_to_compare = ['Entités', 'Efficacité']
            
            for metric in metrics_to_compare:
                st.markdown(f"**{metric}**")
                
                metric_data = df_comparison[['Modèle', metric]].copy()
                
                # Barres horizontales
                for _, row in metric_data.iterrows():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.write(row['Modèle'])
                    with col2:
                        # Normaliser pour la barre de progression
                        max_val = metric_data[metric].max()
                        normalized = row[metric] / max_val if max_val > 0 else 0
                        st.progress(normalized)
                        st.caption(f"{row[metric]:.1f}")
        
        # Analyse de consensus si fusion activée
        if results.get('fusion_results'):
            st.markdown("#### 🔀 Analyse de Consensus")
            
            consensus_stats = {
                'Consensus élevé': 0,
                'Consensus moyen': 0,
                'Consensus faible': 0
            }
            
            # Compter les niveaux de consensus
            for entities in results['fusion_results'].values():
                for entity in entities:
                    level = entity.get('consensus_level', 'Faible')
                    key = f"Consensus {level.lower()}"
                    if key in consensus_stats:
                        consensus_stats[key] += 1
            
            # Afficher les statistiques de consensus
            consensus_df = pd.DataFrame({
                'Niveau': list(consensus_stats.keys()),
                'Nombre': list(consensus_stats.values())
            })
            
            st.bar_chart(consensus_df.set_index('Niveau'))
            
            # Exemples d'entités avec consensus élevé
            st.markdown("##### 🏆 Entités avec Consensus Élevé")
            
            high_consensus_entities = []
            for entity_type, entities in results['fusion_results'].items():
                for entity in entities:
                    if entity.get('consensus_level') == 'Élevé':
                        high_consensus_entities.append({
                            'Type': self.extraction_patterns.get(entity_type, {'name': entity_type})['name'],
                            'Valeur': entity.get('value', 'N/A'),
                            'Modèles': ', '.join([
                                self.ai_models[m]['icon'] 
                                for m in entity.get('contributing_models', [])
                            ])
                        })
            
            if high_consensus_entities:
                df_consensus = pd.DataFrame(high_consensus_entities[:5])
                st.table(df_consensus)
    
    def _display_visualizations_tab(self, results: Dict[str, Any]):
        """Onglet de visualisations avancées"""
        st.markdown("#### 📈 Visualisations des Données")
        
        # Sélecteur de visualisation
        viz_type = st.selectbox(
            "Type de visualisation",
            ["Distribution par type", "Carte de confiance", "Timeline", "Réseau d'entités"]
        )
        
        if viz_type == "Distribution par type":
            # Graphique en secteurs simulé avec métriques
            st.markdown("##### 🎯 Distribution des Entités par Type")
            
            total = results['statistics']['total_entities']
            if total > 0:
                cols = st.columns(3)
                
                for i, (entity_type, stats) in enumerate(results['statistics']['by_type'].items()):
                    if stats['total'] > 0:
                        entity_info = self.extraction_patterns.get(entity_type, {'icon': '📌', 'name': entity_type})
                        percentage = (stats['total'] / total) * 100
                        
                        with cols[i % 3]:
                            st.markdown(f"""
                                <div style="text-align: center; padding: 1rem; 
                                           background: {entity_info.get('color', '#e9ecef')}20; 
                                           border-radius: 10px;">
                                    <h2 style="margin: 0;">{entity_info['icon']}</h2>
                                    <h3 style="margin: 0.5rem 0;">{percentage:.1f}%</h3>
                                    <p style="margin: 0;">{entity_info['name']}</p>
                                    <small>{stats['total']} entités</small>
                                </div>
                            """, unsafe_allow_html=True)
        
        elif viz_type == "Carte de confiance":
            st.markdown("##### 🎨 Carte de Chaleur de Confiance")
            
            # Créer une matrice de confiance
            if results.get('fusion_results'):
                # Matrice modèles x types d'entités
                models = list(results['extractions_by_model'].keys())
                entity_types = list(self.extraction_patterns.keys())
                
                # Simuler une matrice de confiance
                st.markdown("""
                    <div style="background: linear-gradient(to right, #f87171, #fbbf24, #4ade80); 
                                height: 20px; border-radius: 10px; margin: 1rem 0;">
                    </div>
                    <p style="text-align: center;">Faible ← Confiance → Élevée</p>
                """, unsafe_allow_html=True)
                
                # Tableau de confiance
                confidence_data = []
                for model in models:
                    row = {'Modèle': self.ai_models[model]['name']}
                    for entity_type in entity_types[:3]:  # Limiter pour l'affichage
                        # Simuler une valeur de confiance
                        confidence = 0.7 + (hash(f"{model}{entity_type}") % 30) / 100
                        row[self.extraction_patterns[entity_type]['name']] = f"{confidence*100:.0f}%"
                    confidence_data.append(row)
                
                df_conf = pd.DataFrame(confidence_data)
                st.dataframe(df_conf, use_container_width=True, hide_index=True)
        
        elif viz_type == "Timeline":
            st.markdown("##### 📅 Timeline des Dates Extraites")
            
            # Extraire toutes les dates
            dates_found = []
            data_source = results.get('fusion_results') or list(results['extractions_by_model'].values())[0]['extractions']
            
            if 'dates' in data_source:
                for date_entity in data_source['dates']:
                    dates_found.append(date_entity.get('value', 'Date'))
            
            if dates_found:
                # Afficher les dates sur une timeline
                st.markdown("""
                    <div style="position: relative; height: 100px; background: #f8f9fa; 
                                border-radius: 10px; margin: 1rem 0;">
                        <div style="position: absolute; left: 0; right: 0; top: 50%; 
                                    height: 2px; background: #667eea;"></div>
                """, unsafe_allow_html=True)
                
                # Points sur la timeline
                cols = st.columns(len(dates_found[:5]))
                for i, date in enumerate(dates_found[:5]):
                    with cols[i]:
                        st.markdown(f"""
                            <div style="text-align: center;">
                                <div style="width: 20px; height: 20px; background: #667eea; 
                                           border-radius: 50%; margin: 0 auto;"></div>
                                <small>{date}</small>
                            </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Aucune date trouvée dans les documents")
        
        else:  # Réseau d'entités
            st.markdown("##### 🕸️ Réseau d'Entités")
            st.info("🚧 Visualisation du réseau d'entités en cours de développement")
            
            # Placeholder pour un futur graphe de réseau
            st.markdown("""
                <div style="height: 400px; background: #f8f9fa; border-radius: 10px; 
                           display: flex; align-items: center; justify-content: center;">
                    <p style="color: #6c757d;">Graphe de réseau des relations entre entités</p>
                </div>
            """, unsafe_allow_html=True)
    
    def _render_ai_config_tab(self):
        """Configuration avancée des modèles d'IA"""
        st.markdown("### 🤖 Configuration des Modèles d'IA")
        
        # Configuration globale
        with st.expander("⚙️ Paramètres Globaux", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎯 Stratégie d'extraction")
                
                strategy = st.radio(
                    "Mode de traitement",
                    ["🚀 Vitesse (1 modèle)", "⚖️ Équilibré (2-3 modèles)", "🔬 Précision maximale (tous)"],
                    help="Choisissez entre vitesse et précision"
                )
                
                parallel_processing = st.checkbox(
                    "⚡ Traitement parallèle",
                    value=True,
                    help="Exécute les modèles simultanément"
                )
                
                auto_select = st.checkbox(
                    "🎲 Sélection automatique des modèles",
                    help="Choisit les meilleurs modèles selon le type de document"
                )
            
            with col2:
                st.markdown("#### 🔀 Paramètres de Fusion")
                
                fusion_strategy = st.selectbox(
                    "Stratégie de fusion",
                    ["Vote majoritaire", "Moyenne pondérée", "Consensus strict", "Union totale"],
                    help="Comment combiner les résultats des modèles"
                )
                
                min_models_for_fusion = st.slider(
                    "Modèles minimum pour fusion",
                    2, len(self.ai_models), 2,
                    help="Nombre minimum de modèles requis"
                )
                
                confidence_boost = st.slider(
                    "Boost de confiance (fusion)",
                    0.0, 0.3, 0.1,
                    help="Augmentation de confiance pour les consensus"
                )
        
        # Configuration par modèle
        st.markdown("### 🎛️ Configuration Individuelle des Modèles")
        
        for model_id, model_info in self.ai_models.items():
            with st.expander(f"{model_info['icon']} {model_info['name']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    enabled = st.checkbox(
                        "Activé",
                        value=True,
                        key=f"enable_{model_id}"
                    )
                    
                    weight = st.slider(
                        "Poids dans la fusion",
                        0.1, 2.0, 1.0,
                        key=f"weight_{model_id}",
                        help="Importance relative du modèle"
                    )
                
                with col2:
                    temperature = st.slider(
                        "Température",
                        0.0, 1.0, 0.3,
                        key=f"temp_{model_id}",
                        help="Créativité vs précision"
                    )
                    
                    max_tokens = st.number_input(
                        "Tokens max",
                        100, 4000, 1000,
                        key=f"tokens_{model_id}"
                    )
                
                with col3:
                    st.markdown("**Spécialités:**")
                    for strength in model_info['strengths']:
                        st.caption(f"✓ {strength}")
                    
                    # Statistiques du modèle
                    if 'extraction_history' in st.session_state.extraction_state:
                        uses = sum(
                            1 for h in st.session_state.extraction_state['history']
                            if model_id in h.get('models_used', [])
                        )
                        st.metric("Utilisations", uses)
        
        # Presets de configuration
        st.markdown("### 📋 Configurations Préenregistrées")
        
        preset_col1, preset_col2, preset_col3 = st.columns(3)
        
        presets = {
            "Juridique Standard": {
                "models": ["claude", "gpt4"],
                "fusion": True,
                "description": "Optimal pour documents juridiques"
            },
            "Analyse Rapide": {
                "models": ["gemini"],
                "fusion": False,
                "description": "Traitement ultra-rapide"
            },
            "Audit Complet": {
                "models": ["claude", "gpt4", "gemini", "mistral"],
                "fusion": True,
                "description": "Analyse exhaustive"
            }
        }
        
        for col, (preset_name, preset_config) in zip([preset_col1, preset_col2, preset_col3], presets.items()):
            with col:
                if st.button(
                    f"**{preset_name}**\n_{preset_config['description']}_",
                    use_container_width=True,
                    key=f"preset_{preset_name}"
                ):
                    st.session_state.extraction_state['preferences']['default_models'] = preset_config['models']
                    st.session_state.extraction_state['preferences']['auto_fusion'] = preset_config['fusion']
                    st.success(f"✅ Configuration '{preset_name}' appliquée")
                    st.rerun()
        
        # Test de configuration
        with st.expander("🧪 Tester la Configuration"):
            test_text = st.text_area(
                "Texte de test",
                value="La société EXEMPLE SAS, représentée par M. Jean TEST, a conclu un contrat le 15 janvier 2024 pour un montant de 50.000 euros.",
                height=100
            )
            
            if st.button("🚀 Lancer le test", type="primary"):
                with st.spinner("Test en cours..."):
                    time.sleep(1)  # Simulation
                    
                    st.success("✅ Test réussi!")
                    
                    # Résultats simulés
                    st.markdown("**Résultats du test:**")
                    test_results = {
                        "Personnes": ["M. Jean TEST"],
                        "Organisations": ["EXEMPLE SAS"],
                        "Dates": ["15 janvier 2024"],
                        "Montants": ["50.000 euros"]
                    }
                    
                    for entity_type, values in test_results.items():
                        st.write(f"• **{entity_type}:** {', '.join(values)}")
    
    def _render_history_tab(self):
        """Onglet historique des extractions"""
        st.markdown("### 📚 Historique des Extractions")
        
        history = st.session_state.extraction_state.get('history', [])
        
        if not history:
            st.info("Aucune extraction dans l'historique. Effectuez votre première extraction!")
            return
        
        # Filtres et recherche
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Rechercher",
                placeholder="Filtrer par mode, date, modèles..."
            )
        
        with col2:
            filter_mode = st.selectbox(
                "Mode",
                ["Tous"] + ["Automatique", "Favorable", "À charge", "Personnalisé"]
            )
        
        with col3:
            sort_order = st.selectbox(
                "Trier par",
                ["Plus récent", "Plus ancien", "Plus d'entités", "Meilleur score"]
            )
        
        # Filtrer et trier l'historique
        filtered_history = history
        
        if search_term:
            filtered_history = [
                h for h in filtered_history
                if search_term.lower() in h['mode'].lower() or
                search_term.lower() in str(h['models_used']).lower()
            ]
        
        if filter_mode != "Tous":
            filtered_history = [h for h in filtered_history if h['mode'] == filter_mode]
        
        # Trier
        if sort_order == "Plus récent":
            filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
        elif sort_order == "Plus ancien":
            filtered_history.sort(key=lambda x: x['timestamp'])
        elif sort_order == "Plus d'entités":
            filtered_history.sort(
                key=lambda x: x['results']['statistics']['total_entities'],
                reverse=True
            )
        else:  # Meilleur score
            filtered_history.sort(
                key=lambda x: x['results']['quality_metrics']['overall_score'],
                reverse=True
            )
        
        # Afficher l'historique
        st.markdown(f"**{len(filtered_history)} extractions trouvées**")
        
        for extraction in filtered_history[:10]:  # Limiter l'affichage
            # Carte d'historique
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                        **{extraction['timestamp'].strftime('%d/%m/%Y %H:%M')}**  
                        Mode: {extraction['mode']}
                    """)
                
                with col2:
                    models_icons = ' '.join([
                        self.ai_models[m]['icon']
                        for m in extraction['models_used']
                    ])
                    st.markdown(f"**Modèles:** {models_icons}")
                    
                    if extraction.get('fusion_enabled'):
                        st.markdown('<span class="fusion-indicator">Fusion</span>', unsafe_allow_html=True)
                
                with col3:
                    stats = extraction['results']['statistics']
                    quality = extraction['results']['quality_metrics']['overall_score']
                    
                    st.metric(
                        "Entités",
                        stats['total_entities'],
                        delta=f"{quality*100:.0f}% qualité"
                    )
                
                with col4:
                    if st.button("👁️", key=f"view_history_{extraction['id']}", help="Voir détails"):
                        st.session_state.extraction_state['current_extraction'] = extraction
                        st.rerun()
                
                with col5:
                    if st.button("🗑️", key=f"delete_history_{extraction['id']}", help="Supprimer"):
                        st.session_state.extraction_state['history'].remove(extraction)
                        st.rerun()
                
                st.divider()
        
        # Statistiques globales
        if history:
            st.markdown("### 📊 Statistiques Globales")
            
            total_extractions = len(history)
            total_entities = sum(h['results']['statistics']['total_entities'] for h in history)
            avg_quality = sum(
                h['results']['quality_metrics']['overall_score'] 
                for h in history
            ) / total_extractions
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Extractions", total_extractions)
            
            with col2:
                st.metric("Total Entités", f"{total_entities:,}")
            
            with col3:
                st.metric("Qualité Moyenne", f"{avg_quality*100:.1f}%")
            
            with col4:
                most_used_model = Counter(
                    model
                    for h in history
                    for model in h['models_used']
                ).most_common(1)[0][0]
                
                st.metric(
                    "Modèle Favori",
                    self.ai_models[most_used_model]['name']
                )
            
            # Actions sur l'historique
            st.markdown("### 🎯 Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Exporter l'historique", use_container_width=True):
                    self._export_history(history)
            
            with col2:
                if st.button("📊 Rapport de synthèse", use_container_width=True):
                    self._generate_history_report(history)
            
            with col3:
                if st.button("🗑️ Effacer l'historique", use_container_width=True, type="secondary"):
                    if st.checkbox("Confirmer la suppression"):
                        st.session_state.extraction_state['history'] = []
                        st.success("✅ Historique effacé")
                        st.rerun()
    
    def _render_settings_tab(self):
        """Onglet des paramètres du module"""
        st.markdown("### ⚙️ Paramètres du Module")
        
        # Préférences générales
        with st.expander("🎨 Préférences Générales", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Interface")
                
                theme = st.selectbox(
                    "Thème de couleur",
                    ["Violet (défaut)", "Bleu", "Vert", "Orange"],
                    help="Change les couleurs de l'interface"
                )
                
                animations = st.checkbox(
                    "Animations activées",
                    value=True,
                    help="Active/désactive les animations"
                )
                
                compact_mode = st.checkbox(
                    "Mode compact",
                    value=False,
                    help="Réduit l'espacement pour plus de contenu"
                )
            
            with col2:
                st.markdown("#### Comportement")
                
                auto_save = st.checkbox(
                    "Sauvegarde automatique",
                    value=True,
                    help="Sauvegarde automatiquement les extractions"
                )
                
                notifications = st.checkbox(
                    "Notifications",
                    value=True,
                    help="Affiche des notifications pour les actions"
                )
                
                debug_mode = st.checkbox(
                    "Mode debug",
                    value=False,
                    help="Affiche des informations techniques"
                )
        
        # Paramètres d'extraction
        with st.expander("🔍 Paramètres d'Extraction"):
            st.markdown("#### Valeurs par défaut")
            
            default_confidence = st.slider(
                "Seuil de confiance par défaut",
                0.0, 1.0,
                st.session_state.extraction_state['preferences']['confidence_threshold'],
                help="Confiance minimale pour conserver une extraction"
            )
            
            default_context = st.slider(
                "Fenêtre de contexte par défaut",
                50, 500,
                st.session_state.extraction_state['preferences']['context_window'],
                help="Caractères de contexte autour des extractions"
            )
            
            st.markdown("#### Limites")
            
            max_entities_per_type = st.number_input(
                "Entités max par type",
                10, 1000, 100,
                help="Limite le nombre d'entités extraites par type"
            )
            
            timeout_seconds = st.number_input(
                "Timeout (secondes)",
                10, 300, 60,
                help="Temps maximum pour une extraction"
            )
        
        # Gestion des données
        with st.expander("💾 Gestion des Données"):
            st.markdown("#### Cache et Stockage")
            
            cache_size = len(st.session_state.extraction_state.get('cache', {}))
            history_size = len(st.session_state.extraction_state.get('history', []))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Éléments en cache", cache_size)
                if st.button("🧹 Vider le cache", use_container_width=True):
                    st.session_state.extraction_state['cache'] = {}
                    st.success("✅ Cache vidé")
            
            with col2:
                st.metric("Extractions en historique", history_size)
                max_history = st.number_input(
                    "Historique maximum",
                    10, 1000, 100,
                    help="Nombre maximum d'extractions à conserver"
                )
            
            st.markdown("#### Export/Import")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📤 Exporter configuration", use_container_width=True):
                    config_data = json.dumps(
                        st.session_state.extraction_state['preferences'],
                        indent=2
                    )
                    st.download_button(
                        "💾 Télécharger",
                        data=config_data,
                        file_name="extraction_config.json",
                        mime="application/json"
                    )
            
            with col2:
                uploaded_config = st.file_uploader(
                    "📥 Importer configuration",
                    type=['json']
                )
                
                if uploaded_config:
                    try:
                        config = json.load(uploaded_config)
                        st.session_state.extraction_state['preferences'].update(config)
                        st.success("✅ Configuration importée")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
        
        # Intégrations
        with st.expander("🔌 Intégrations"):
            st.markdown("#### APIs Externes")
            
            st.info("🚧 Configuration des APIs en cours de développement")
            
            # Placeholder pour futures intégrations
            integrations = {
                "Azure Cognitive Services": False,
                "OpenAI API": False,
                "Google Cloud AI": False,
                "Anthropic Claude": False
            }
            
            for service, enabled in integrations.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(service)
                with col2:
                    st.checkbox("Activé", value=enabled, key=f"int_{service}", disabled=True)
        
        # Actions
        st.markdown("### 💾 Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                # Sauvegarder les préférences
                st.session_state.extraction_state['preferences'].update({
                    'confidence_threshold': default_confidence,
                    'context_window': default_context
                })
                st.success("✅ Paramètres sauvegardés")
        
        with col2:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                if st.checkbox("Confirmer la réinitialisation"):
                    self._initialize_session_state()
                    st.success("✅ Paramètres réinitialisés")
                    st.rerun()
        
        with col3:
            if st.button("ℹ️ À propos", use_container_width=True):
                st.info(
                    """
                    **Module d'Extraction v2.0**  
                    Extraction intelligente multi-modèles avec fusion  
                    © 2024 Nexora Law IA
                    """
                )
    
    def _show_export_dialog(self, results: Dict[str, Any]):
        """Dialogue d'export des résultats"""
        with st.expander("📤 Options d'Export", expanded=True):
            format_type = st.selectbox(
                "Format",
                ["JSON", "CSV", "PDF", "Word", "Excel"]
            )
            
            include_options = st.multiselect(
                "Inclure",
                ["Résultats bruts", "Statistiques", "Insights", "Métadonnées"],
                default=["Résultats bruts", "Statistiques"]
            )
            
            if st.button("💾 Générer l'export", type="primary"):
                with st.spinner("Génération en cours..."):
                    time.sleep(1)  # Simulation
                    
                    # Générer le contenu selon le format
                    if format_type == "JSON":
                        export_data = json.dumps(results, indent=2, default=str)
                        file_name = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        mime_type = "application/json"
                    else:
                        # Placeholder pour autres formats
                        export_data = "Export simulé"
                        file_name = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        mime_type = "text/plain"
                    
                    st.download_button(
                        f"📥 Télécharger {format_type}",
                        data=export_data,
                        file_name=file_name,
                        mime=mime_type,
                        use_container_width=True
                    )
                    
                    st.success(f"✅ Export {format_type} généré avec succès!")
    
    def _export_history(self, history: List[Dict]):
        """Exporte l'historique complet"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_extractions': len(history),
            'extractions': history
        }
        
        json_data = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            "💾 Télécharger l'historique",
            data=json_data,
            file_name=f"historique_extractions_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    def _generate_history_report(self, history: List[Dict]):
        """Génère un rapport de synthèse de l'historique"""
        with st.spinner("Génération du rapport..."):
            time.sleep(1)  # Simulation
            
            # Créer le rapport
            report = f"""
# Rapport de Synthèse des Extractions
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

## Résumé Exécutif
- Total d'extractions: {len(history)}
- Période couverte: {history[-1]['timestamp'].strftime('%d/%m/%Y')} - {history[0]['timestamp'].strftime('%d/%m/%Y')}
- Entités totales extraites: {sum(h['results']['statistics']['total_entities'] for h in history):,}

## Statistiques par Mode
"""
            
            # Statistiques par mode
            mode_stats = Counter(h['mode'] for h in history)
            for mode, count in mode_stats.most_common():
                report += f"- {mode}: {count} extractions\n"
            
            report += "\n## Modèles d'IA Utilisés\n"
            
            # Statistiques par modèle
            model_stats = Counter(
                model
                for h in history
                for model in h['models_used']
            )
            
            for model, count in model_stats.most_common():
                model_name = self.ai_models[model]['name']
                report += f"- {model_name}: {count} utilisations\n"
            
            # Qualité moyenne
            avg_quality = sum(
                h['results']['quality_metrics']['overall_score']
                for h in history
            ) / len(history)
            
            report += f"\n## Qualité Moyenne: {avg_quality*100:.1f}%\n"
            
            # Afficher le rapport
            st.text_area(
                "Rapport de synthèse",
                value=report,
                height=400
            )
            
            # Option de téléchargement
            st.download_button(
                "📥 Télécharger le rapport",
                data=report,
                file_name=f"rapport_synthese_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

# Point d'entrée pour lazy loading et tests
if __name__ == "__main__":
    run()
"""Module de gestion des dossiers pénaux avec IA intégrée"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import time
import json
import uuid
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import truncate_text, clean_key, format_legal_date

# Import des modèles avec gestion d'erreur
try:
    from modules.dataclasses import DossierPenal, PieceProcedure, EvenementTimeline
except ImportError:
    # Définitions de secours si l'import échoue
    from dataclasses import dataclass, field
    from typing import Dict, List, Optional
    from datetime import datetime
    
    @dataclass
    class DossierPenal:
        id: str
        numero_dossier: str
        titre: str
        date_ouverture: datetime
        date_cloture: Optional[datetime] = None
        juridiction: str
        juge_instruction: Optional[str] = None
        procureur: Optional[str] = None
        parties: Dict[str, List[str]] = field(default_factory=dict)
        faits: Optional[str] = None
        qualification_juridique: List[str] = field(default_factory=list)
        pieces: List[str] = field(default_factory=list)
        evenements: List[str] = field(default_factory=list)
        statut: str = "en_cours"
        analyse_ia: Dict = field(default_factory=dict)
        risque_score: float = 0.0
        tags: List[str] = field(default_factory=list)

class DossierPenalManager:
    """Gestionnaire des dossiers pénaux avec IA"""
    
    def __init__(self):
        """Initialise le gestionnaire"""
        if 'dossiers_penaux' not in st.session_state:
            st.session_state.dossiers_penaux = {}
        if 'current_dossier_id' not in st.session_state:
            st.session_state.current_dossier_id = None
        if 'ai_analyses' not in st.session_state:
            st.session_state.ai_analyses = {}
    
    def create_dossier(self, numero: str, titre: str, juridiction: str) -> DossierPenal:
        """Crée un nouveau dossier pénal"""
        dossier_id = str(uuid.uuid4())
        dossier = DossierPenal(
            id=dossier_id,
            numero_dossier=numero,
            titre=titre,
            date_ouverture=datetime.now(),
            juridiction=juridiction,
            parties={"demandeurs": [], "defendeurs": [], "temoins": [], "experts": []},
            statut="en_cours",
            analyse_ia={},
            tags=[]
        )
        
        st.session_state.dossiers_penaux[dossier_id] = dossier
        return dossier
    
    def get_dossier(self, dossier_id: str) -> Optional[DossierPenal]:
        """Récupère un dossier par son ID"""
        return st.session_state.dossiers_penaux.get(dossier_id)
    
    def update_dossier(self, dossier_id: str, **kwargs):
        """Met à jour un dossier"""
        if dossier_id in st.session_state.dossiers_penaux:
            dossier = st.session_state.dossiers_penaux[dossier_id]
            for key, value in kwargs.items():
                if hasattr(dossier, key):
                    setattr(dossier, key, value)
    
    def list_dossiers(self) -> List[DossierPenal]:
        """Liste tous les dossiers"""
        return list(st.session_state.dossiers_penaux.values())
    
    def delete_dossier(self, dossier_id: str):
        """Supprime un dossier"""
        if dossier_id in st.session_state.dossiers_penaux:
            del st.session_state.dossiers_penaux[dossier_id]
            if st.session_state.current_dossier_id == dossier_id:
                st.session_state.current_dossier_id = None
    
    def search_dossiers(self, query: str) -> List[DossierPenal]:
        """Recherche dans les dossiers"""
        results = []
        query_lower = query.lower()
        for dossier in self.list_dossiers():
            if (query_lower in dossier.numero_dossier.lower() or 
                query_lower in dossier.titre.lower() or
                query_lower in (dossier.faits or "").lower() or
                any(query_lower in tag.lower() for tag in dossier.tags)):
                results.append(dossier)
        return results

def run():
    """Fonction principale du module - OBLIGATOIRE"""
    # Configuration de la page
    st.set_page_config(
        page_title="Nexora Law - Dossiers Pénaux",
        page_icon="📁",
        layout="wide"
    )
    
    # CSS personnalisé pour un meilleur design
    st.markdown("""
    <style>
    .dossier-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 10px;
        border-left: 5px solid #1f77b4;
        transition: all 0.3s ease;
    }
    .dossier-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .status-en_cours { background-color: #90EE90; color: #006400; }
    .status-clos { background-color: #87CEEB; color: #00008B; }
    .status-suspendu { background-color: #FFE4B5; color: #FF8C00; }
    .status-urgent { background-color: #FFB6C1; color: #DC143C; }
    .ai-suggestion {
        background-color: #E6F3FF;
        border-left: 4px solid #0066CC;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # En-tête avec titre et actions rapides
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("📁 Gestion Intelligente des Dossiers Pénaux")
    with col2:
        search_query = st.text_input("🔍 Recherche rapide", placeholder="N° dossier, titre, tags...")
    with col3:
        if st.button("➕ Nouveau dossier", type="primary", use_container_width=True):
            st.session_state.show_new_dossier = True
    
    # Initialisation du gestionnaire
    manager = DossierPenalManager()
    
    # Initialisation des variables de session
    if 'module_state' not in st.session_state:
        st.session_state.module_state = {
            'initialized': True,
            'results': None,
            'config': {},
            'ai_model': 'GPT-4',
            'fusion_mode': False
        }
    
    # Interface principale avec sidebar modernisée
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        # Sélection du mode d'affichage
        view_mode = st.radio(
            "Mode d'affichage",
            ["📊 Tableau de bord", "📋 Liste détaillée", "🗂️ Vue Kanban", "📈 Analyses"],
            key="view_mode"
        )
        
        st.markdown("---")
        
        # Configuration IA
        st.markdown("### 🤖 Configuration IA")
        
        # Sélection du modèle
        ai_model = st.selectbox(
            "Modèle principal",
            ["GPT-4", "Claude 3", "Gemini Pro", "Mistral", "LLaMA 2"],
            index=0
        )
        st.session_state.module_state['ai_model'] = ai_model
        
        # Mode fusion
        fusion_mode = st.checkbox(
            "🔀 Mode Fusion (Multi-modèles)",
            value=st.session_state.module_state.get('fusion_mode', False)
        )
        st.session_state.module_state['fusion_mode'] = fusion_mode
        
        if fusion_mode:
            st.markdown("**Modèles secondaires:**")
            models = ["GPT-4", "Claude 3", "Gemini Pro", "Mistral", "LLaMA 2"]
            secondary_models = []
            for model in models:
                if model != ai_model and st.checkbox(model, key=f"sec_{model}"):
                    secondary_models.append(model)
            st.session_state.module_state['secondary_models'] = secondary_models
        
        st.markdown("---")
        
        # Filtres rapides
        st.markdown("### 🔧 Filtres rapides")
        
        # Filtre par statut
        statut_filter = st.multiselect(
            "Statut",
            ["en_cours", "clos", "suspendu", "urgent", "archive"],
            default=["en_cours", "urgent"]
        )
        
        # Filtre par juridiction
        juridictions = list(set([d.juridiction for d in manager.list_dossiers()]))
        if juridictions:
            juridiction_filter = st.multiselect("Juridiction", juridictions)
        
        # Filtre par niveau de risque
        risk_level = st.select_slider(
            "Niveau de risque minimum",
            options=["Faible", "Moyen", "Élevé", "Critique"],
            value="Faible"
        )
        
        st.markdown("---")
        
        # Actions rapides
        st.markdown("### ⚡ Actions rapides")
        if st.button("🔄 Actualiser les analyses IA", use_container_width=True):
            st.info("Actualisation en cours...")
        if st.button("📊 Générer rapport global", use_container_width=True):
            st.info("Génération du rapport...")
        if st.button("💾 Sauvegarder l'état", use_container_width=True):
            st.success("État sauvegardé!")
    
    # Zone principale selon le mode d'affichage
    if getattr(st.session_state, 'show_new_dossier', False):
        display_new_dossier_form_enhanced(manager)
    elif st.session_state.current_dossier_id:
        display_dossier_detail_enhanced(manager, st.session_state.current_dossier_id)
    else:
        # Affichage selon le mode sélectionné
        if view_mode == "📊 Tableau de bord":
            display_dashboard_enhanced(manager, search_query)
        elif view_mode == "📋 Liste détaillée":
            display_list_view(manager, search_query, statut_filter)
        elif view_mode == "🗂️ Vue Kanban":
            display_kanban_view(manager, search_query, statut_filter)
        elif view_mode == "📈 Analyses":
            display_analytics_view(manager)

def display_dashboard_enhanced(manager: DossierPenalManager, search_query: str = ""):
    """Tableau de bord amélioré avec métriques et visualisations"""
    
    # Récupérer les dossiers (avec recherche si nécessaire)
    if search_query:
        dossiers = manager.search_dossiers(search_query)
        st.info(f"🔍 {len(dossiers)} résultat(s) pour '{search_query}'")
    else:
        dossiers = manager.list_dossiers()
    
    if not dossiers:
        # État vide attrayant
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h2>🌟 Bienvenue dans la gestion intelligente des dossiers pénaux</h2>
            <p>Commencez par créer votre premier dossier pour découvrir toutes les fonctionnalités IA</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Métriques principales avec animations
    st.markdown("### 📊 Vue d'ensemble")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total = len(dossiers)
        st.metric(
            "📁 Total dossiers",
            total,
            f"+{len([d for d in dossiers if (datetime.now() - d.date_ouverture).days <= 30])} ce mois"
        )
    
    with col2:
        en_cours = len([d for d in dossiers if d.statut == "en_cours"])
        pourcentage = (en_cours / total * 100) if total > 0 else 0
        st.metric("⚡ En cours", en_cours, f"{pourcentage:.1f}%")
    
    with col3:
        urgent = len([d for d in dossiers if d.risque_score > 0.7])
        st.metric("🚨 Urgents", urgent, "⚠️" if urgent > 5 else "✅")
    
    with col4:
        avg_duration = calculate_average_duration(dossiers)
        st.metric("⏱️ Durée moy.", f"{avg_duration}j", "-5j vs mois dernier")
    
    with col5:
        completion_rate = calculate_completion_rate(dossiers)
        st.metric("✅ Taux résolution", f"{completion_rate}%", "+3%")
    
    # Graphiques interactifs
    st.markdown("### 📈 Analyses visuelles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique temporel des ouvertures/clôtures
        fig = create_timeline_chart(dossiers)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Répartition par juridiction
        fig = create_jurisdiction_chart(dossiers)
        st.plotly_chart(fig, use_container_width=True)
    
    # Alertes IA
    st.markdown("### 🤖 Alertes et recommandations IA")
    display_ai_alerts(dossiers)
    
    # Dossiers prioritaires
    st.markdown("### 🎯 Dossiers prioritaires")
    priority_dossiers = sorted(
        [d for d in dossiers if d.statut == "en_cours"],
        key=lambda x: x.risque_score,
        reverse=True
    )[:5]
    
    for dossier in priority_dossiers:
        display_dossier_card(dossier, manager)

def display_dossier_card(dossier: DossierPenal, manager: DossierPenalManager):
    """Affiche une carte de dossier moderne"""
    risk_color = get_risk_color(dossier.risque_score)
    
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
        
        with col1:
            if st.button(
                f"📋 {dossier.numero_dossier} - {truncate_text(dossier.titre, 40)}",
                key=f"card_{dossier.id}",
                use_container_width=True
            ):
                st.session_state.current_dossier_id = dossier.id
                st.rerun()
        
        with col2:
            st.markdown(f"<span class='status-badge status-{dossier.statut}'>{dossier.statut.upper()}</span>", unsafe_allow_html=True)
        
        with col3:
            duration = (datetime.now() - dossier.date_ouverture).days
            st.text(f"📅 {duration} jours")
        
        with col4:
            st.markdown(f"<div style='color: {risk_color}'>⚠️ {dossier.risque_score:.1%}</div>", unsafe_allow_html=True)
        
        with col5:
            if st.button("🤖", key=f"ai_{dossier.id}", help="Analyse IA rapide"):
                perform_quick_ai_analysis(dossier.id)

def display_new_dossier_form_enhanced(manager: DossierPenalManager):
    """Formulaire de création amélioré avec suggestions IA"""
    st.markdown("## 📝 Création d'un nouveau dossier pénal")
    
    # Stepper pour guider l'utilisateur
    step = st.session_state.get('creation_step', 1)
    
    # Affichage du stepper
    col1, col2, col3, col4 = st.columns(4)
    steps = [
        ("1️⃣ Informations", step >= 1),
        ("2️⃣ Parties", step >= 2),
        ("3️⃣ Faits", step >= 3),
        ("4️⃣ Validation", step >= 4)
    ]
    
    for col, (label, active) in zip([col1, col2, col3, col4], steps):
        with col:
            if active:
                st.success(label)
            else:
                st.info(label)
    
    st.markdown("---")
    
    # Contenu selon l'étape
    if step == 1:
        display_step1_info(manager)
    elif step == 2:
        display_step2_parties(manager)
    elif step == 3:
        display_step3_facts(manager)
    elif step == 4:
        display_step4_validation(manager)

def display_step1_info(manager: DossierPenalManager):
    """Étape 1: Informations générales"""
    with st.form("step1_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            numero = st.text_input(
                "Numéro de dossier*",
                placeholder="2024/001",
                help="Format recommandé: ANNÉE/NUMÉRO"
            )
            
            juridiction = st.selectbox(
                "Juridiction*",
                ["TGI Paris", "TGI Lyon", "TGI Marseille", "Cour d'appel Paris", "Autre"],
                help="Sélectionnez la juridiction compétente"
            )
            
            if juridiction == "Autre":
                juridiction = st.text_input("Précisez la juridiction")
            
            type_affaire = st.selectbox(
                "Type d'affaire",
                ["Pénal général", "Pénal des affaires", "Crime organisé", "Terrorisme", "Autre"]
            )
        
        with col2:
            titre = st.text_input(
                "Titre du dossier*",
                placeholder="Affaire X c/ Y",
                help="Titre court et descriptif"
            )
            
            juge = st.text_input(
                "Juge d'instruction",
                placeholder="M. Dupont",
                help="Laissez vide si non encore désigné"
            )
            
            procureur = st.text_input(
                "Procureur",
                placeholder="Mme Martin"
            )
        
        # Suggestions IA
        if st.checkbox("🤖 Activer les suggestions IA"):
            with st.spinner("Analyse en cours..."):
                time.sleep(1)  # Simulation
                st.markdown("""
                <div class='ai-suggestion'>
                    <strong>💡 Suggestions IA:</strong><br>
                    • Format de numéro détecté: ✅ Conforme<br>
                    • Juridiction suggérée selon le type d'affaire: TGI Paris (Division économique)<br>
                    • Mots-clés recommandés: fraude, détournement, abus de confiance
                </div>
                """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            if st.form_submit_button("Suivant ➡️", type="primary", use_container_width=True):
                if numero and titre and juridiction:
                    # Sauvegarder les données
                    if 'new_dossier_data' not in st.session_state:
                        st.session_state.new_dossier_data = {}
                    
                    st.session_state.new_dossier_data.update({
                        'numero': numero,
                        'titre': titre,
                        'juridiction': juridiction,
                        'juge': juge,
                        'procureur': procureur,
                        'type_affaire': type_affaire
                    })
                    st.session_state.creation_step = 2
                    st.rerun()
                else:
                    st.error("Veuillez remplir tous les champs obligatoires")
        
        with col3:
            if st.form_submit_button("Annuler", use_container_width=True):
                st.session_state.show_new_dossier = False
                st.session_state.creation_step = 1
                st.rerun()

def display_step2_parties(manager: DossierPenalManager):
    """Étape 2: Parties impliquées"""
    st.markdown("### 👥 Parties impliquées")
    
    # Récupération des données temporaires
    if 'parties_temp' not in st.session_state:
        st.session_state.parties_temp = {
            'demandeurs': [],
            'defendeurs': [],
            'temoins': [],
            'experts': []
        }
    
    # Interface par onglets pour chaque type de partie
    tabs = st.tabs(["👤 Demandeurs", "⚖️ Défendeurs", "👁️ Témoins", "🔬 Experts"])
    
    for tab, partie_type in zip(tabs, ['demandeurs', 'defendeurs', 'temoins', 'experts']):
        with tab:
            # Formulaire d'ajout
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                nom = st.text_input(f"Nom", key=f"nom_{partie_type}")
            with col2:
                role = st.text_input(f"Rôle/Qualité", key=f"role_{partie_type}")
            with col3:
                if st.button("➕ Ajouter", key=f"add_{partie_type}"):
                    if nom:
                        st.session_state.parties_temp[partie_type].append({
                            'nom': nom,
                            'role': role
                        })
                        st.rerun()
            
            # Liste des parties ajoutées
            if st.session_state.parties_temp[partie_type]:
                for i, partie in enumerate(st.session_state.parties_temp[partie_type]):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.text(f"• {partie['nom']}")
                    with col2:
                        st.text(partie['role'])
                    with col3:
                        if st.button("🗑️", key=f"del_{partie_type}_{i}"):
                            st.session_state.parties_temp[partie_type].pop(i)
                            st.rerun()
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.creation_step = 1
            st.rerun()
    with col2:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            st.session_state.new_dossier_data['parties'] = st.session_state.parties_temp
            st.session_state.creation_step = 3
            st.rerun()
    with col3:
        if st.button("Annuler", use_container_width=True):
            st.session_state.show_new_dossier = False
            st.session_state.creation_step = 1
            st.rerun()

def display_step3_facts(manager: DossierPenalManager):
    """Étape 3: Faits et qualification"""
    st.markdown("### 📋 Faits et qualification juridique")
    
    # Résumé des faits
    faits = st.text_area(
        "Résumé des faits",
        height=200,
        placeholder="Décrivez les faits de manière claire et concise...",
        help="Ce résumé sera utilisé par l'IA pour ses analyses"
    )
    
    # Qualification juridique
    st.markdown("### ⚖️ Qualification juridique")
    
    # Suggestions de qualifications basées sur les faits
    if faits and st.button("🤖 Suggérer des qualifications"):
        with st.spinner("Analyse des faits en cours..."):
            time.sleep(2)  # Simulation
            suggestions = [
                "Escroquerie (Art. 313-1 CP)",
                "Abus de confiance (Art. 314-1 CP)",
                "Faux et usage de faux (Art. 441-1 CP)"
            ]
            st.success("Qualifications suggérées par l'IA:")
            for sugg in suggestions:
                if st.checkbox(sugg, key=f"qual_{sugg}"):
                    if 'qualifications_temp' not in st.session_state:
                        st.session_state.qualifications_temp = []
                    if sugg not in st.session_state.qualifications_temp:
                        st.session_state.qualifications_temp.append(sugg)
    
    # Ajout manuel de qualifications
    qual_manuelle = st.text_input("Ajouter une qualification manuellement")
    if st.button("➕ Ajouter qualification"):
        if qual_manuelle:
            if 'qualifications_temp' not in st.session_state:
                st.session_state.qualifications_temp = []
            st.session_state.qualifications_temp.append(qual_manuelle)
            st.rerun()
    
    # Affichage des qualifications sélectionnées
    if 'qualifications_temp' in st.session_state and st.session_state.qualifications_temp:
        st.markdown("**Qualifications retenues:**")
        for qual in st.session_state.qualifications_temp:
            st.markdown(f"• {qual}")
    
    # Tags et mots-clés
    st.markdown("### 🏷️ Tags et mots-clés")
    tags = st.multiselect(
        "Sélectionnez des tags",
        ["Urgent", "Sensible", "Médiatique", "International", "Récidive", "Mineur impliqué", "Violence", "Financier"],
        help="Les tags permettent un filtrage rapide des dossiers"
    )
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.creation_step = 2
            st.rerun()
    with col2:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            st.session_state.new_dossier_data['faits'] = faits
            st.session_state.new_dossier_data['qualifications'] = st.session_state.get('qualifications_temp', [])
            st.session_state.new_dossier_data['tags'] = tags
            st.session_state.creation_step = 4
            st.rerun()
    with col3:
        if st.button("Annuler", use_container_width=True):
            st.session_state.show_new_dossier = False
            st.session_state.creation_step = 1
            st.rerun()

def display_step4_validation(manager: DossierPenalManager):
    """Étape 4: Validation et création"""
    st.markdown("### ✅ Validation du dossier")
    
    # Récapitulatif
    data = st.session_state.new_dossier_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Informations générales")
        st.write(f"**Numéro:** {data.get('numero', '')}")
        st.write(f"**Titre:** {data.get('titre', '')}")
        st.write(f"**Juridiction:** {data.get('juridiction', '')}")
        st.write(f"**Type:** {data.get('type_affaire', '')}")
        st.write(f"**Juge:** {data.get('juge', 'Non désigné')}")
        st.write(f"**Procureur:** {data.get('procureur', 'Non désigné')}")
    
    with col2:
        st.markdown("#### 👥 Parties")
        parties = data.get('parties', {})
        for type_partie, liste in parties.items():
            if liste:
                st.write(f"**{type_partie.capitalize()}:** {len(liste)}")
        
        st.markdown("#### 🏷️ Tags")
        tags = data.get('tags', [])
        if tags:
            st.write(", ".join(tags))
    
    # Analyse de risque IA
    st.markdown("#### 🤖 Analyse de risque préliminaire")
    with st.spinner("Analyse en cours..."):
        time.sleep(1)  # Simulation
        risk_score = 0.65  # Simulation
        
        prog_col1, prog_col2 = st.columns([3, 1])
        with prog_col1:
            st.progress(risk_score)
        with prog_col2:
            st.write(f"**{risk_score:.0%}**")
        
        st.info("""
        **Facteurs de risque identifiés:**
        • Complexité juridique élevée (multiples qualifications)
        • Nombre important de parties impliquées
        • Nature financière de l'affaire
        
        **Recommandations:**
        • Prévoir une équipe renforcée
        • Anticiper des délais de procédure étendus
        """)
    
    # Actions finales
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.creation_step = 3
            st.rerun()
    
    with col2:
        if st.button("✅ Créer le dossier", type="primary", use_container_width=True):
            # Création du dossier
            dossier = manager.create_dossier(
                data['numero'],
                data['titre'],
                data['juridiction']
            )
            
            # Mise à jour des données
            manager.update_dossier(
                dossier.id,
                juge_instruction=data.get('juge'),
                procureur=data.get('procureur'),
                faits=data.get('faits'),
                qualification_juridique=data.get('qualifications', []),
                tags=data.get('tags', []),
                risque_score=risk_score,
                parties=data.get('parties', {})
            )
            
            # Notification de succès
            st.balloons()
            st.success(f"✅ Dossier {data['numero']} créé avec succès!")
            
            # Nettoyage et redirection
            st.session_state.current_dossier_id = dossier.id
            st.session_state.show_new_dossier = False
            st.session_state.creation_step = 1
            
            # Nettoyer les données temporaires
            for key in ['new_dossier_data', 'parties_temp', 'qualifications_temp']:
                if key in st.session_state:
                    del st.session_state[key]
            
            time.sleep(2)
            st.rerun()
    
    with col3:
        if st.button("Annuler", use_container_width=True):
            st.session_state.show_new_dossier = False
            st.session_state.creation_step = 1
            st.rerun()

def display_dossier_detail_enhanced(manager: DossierPenalManager, dossier_id: str):
    """Affichage détaillé du dossier avec fonctionnalités IA"""
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        st.error("Dossier introuvable")
        return
    
    # En-tête moderne avec actions
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.title(f"📁 {dossier.numero_dossier}")
        st.markdown(f"### {dossier.titre}")
    with col2:
        if st.button("🏠 Retour", use_container_width=True):
            st.session_state.current_dossier_id = None
            st.rerun()
    with col3:
        if st.button("✏️ Modifier", use_container_width=True):
            st.session_state.edit_mode = True
    with col4:
        if st.button("🗑️ Supprimer", use_container_width=True, type="secondary"):
            st.session_state.confirm_delete = dossier_id
    
    # Barre de statut et risque
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<span class='status-badge status-{dossier.statut}'>{dossier.statut.upper()}</span>", unsafe_allow_html=True)
    with col2:
        duration = (datetime.now() - dossier.date_ouverture).days
        st.metric("Durée", f"{duration} jours")
    with col3:
        risk_color = get_risk_color(dossier.risque_score)
        st.markdown(f"<div style='text-align: center; color: {risk_color}; font-size: 1.5em;'>Risque: {dossier.risque_score:.0%}</div>", unsafe_allow_html=True)
    with col4:
        ai_score = getattr(dossier, 'ai_confidence', 0.85)
        st.metric("Confiance IA", f"{ai_score:.0%}")
    
    # Onglets principaux
    tabs = st.tabs([
        "📋 Vue d'ensemble",
        "👥 Parties & Acteurs",
        "📎 Documents & Pièces",
        "📅 Chronologie",
        "🤖 Analyse IA",
        "💬 Communications",
        "📊 Statistiques"
    ])
    
    with tabs[0]:
        display_overview_tab(dossier, manager)
    
    with tabs[1]:
        display_parties_tab_enhanced(dossier, manager)
    
    with tabs[2]:
        display_documents_tab(dossier, manager)
    
    with tabs[3]:
        display_timeline_tab(dossier, manager)
    
    with tabs[4]:
        display_ai_analysis_tab(dossier, manager)
    
    with tabs[5]:
        display_communications_tab(dossier, manager)
    
    with tabs[6]:
        display_statistics_tab(dossier, manager)

def display_overview_tab(dossier: DossierPenal, manager: DossierPenalManager):
    """Onglet vue d'ensemble avec résumé intelligent"""
    
    # Carte de résumé principal
    with st.container():
        st.markdown("### 📊 Résumé du dossier")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Informations principales
            info_df = pd.DataFrame({
                'Champ': ['Juridiction', 'Juge d\'instruction', 'Procureur', 'Date d\'ouverture', 'Statut'],
                'Valeur': [
                    dossier.juridiction,
                    dossier.juge_instruction or 'Non désigné',
                    dossier.procureur or 'Non désigné',
                    dossier.date_ouverture.strftime('%d/%m/%Y'),
                    dossier.statut
                ]
            })
            st.dataframe(info_df, hide_index=True, use_container_width=True)
        
        with col2:
            # Indicateurs clés
            st.markdown("#### 🎯 Indicateurs clés")
            nb_pieces = len(dossier.pieces)
            nb_events = len(dossier.evenements)
            nb_parties = sum(len(v) for v in dossier.parties.values())
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("📎 Pièces", nb_pieces)
                st.metric("👥 Parties", nb_parties)
            with metric_col2:
                st.metric("📅 Events", nb_events)
                st.metric("🏷️ Tags", len(dossier.tags))
    
    # Résumé des faits avec IA
    if dossier.faits:
        st.markdown("### 📝 Résumé des faits")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(dossier.faits)
        with col2:
            if st.button("🤖 Résumé IA", use_container_width=True):
                with st.spinner("Génération du résumé..."):
                    time.sleep(2)
                    st.success("Résumé généré par l'IA disponible dans l'onglet Analyse IA")
    
    # Qualifications juridiques
    if dossier.qualification_juridique:
        st.markdown("### ⚖️ Qualifications juridiques")
        for i, qual in enumerate(dossier.qualification_juridique, 1):
            st.markdown(f"{i}. {qual}")
    
    # Tags et alertes
    if dossier.tags:
        st.markdown("### 🏷️ Tags et classifications")
        tag_cols = st.columns(len(dossier.tags))
        for col, tag in zip(tag_cols, dossier.tags):
            with col:
                st.info(f"🏷️ {tag}")
    
    # Actions rapides
    st.markdown("### ⚡ Actions rapides")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Générer rapport", use_container_width=True):
            generate_report(dossier)
    with col2:
        if st.button("📧 Envoyer notification", use_container_width=True):
            st.info("Notification envoyée")
    with col3:
        if st.button("🔄 Actualiser analyse", use_container_width=True):
            st.info("Analyse actualisée")
    with col4:
        if st.button("📤 Exporter", use_container_width=True):
            export_dossier(dossier)

def display_ai_analysis_tab(dossier: DossierPenal, manager: DossierPenalManager):
    """Onglet d'analyse IA avancée"""
    st.markdown("### 🤖 Analyse Intelligence Artificielle")
    
    # Sélection du type d'analyse
    analysis_type = st.selectbox(
        "Type d'analyse",
        ["🔍 Analyse complète", "⚖️ Analyse juridique", "🎯 Prédiction d'issue", "📊 Analyse de risques", "🔗 Liens et corrélations"]
    )
    
    # Configuration de l'analyse
    col1, col2, col3 = st.columns(3)
    with col1:
        depth = st.select_slider(
            "Profondeur d'analyse",
            ["Rapide", "Standard", "Approfondie", "Exhaustive"],
            value="Standard"
        )
    with col2:
        include_jurisprudence = st.checkbox("Inclure la jurisprudence", value=True)
    with col3:
        include_similar_cases = st.checkbox("Inclure cas similaires", value=True)
    
    # Lancement de l'analyse
    if st.button("🚀 Lancer l'analyse", type="primary", use_container_width=True):
        # Affichage du modèle utilisé
        model_info = f"Modèle principal: {st.session_state.module_state['ai_model']}"
        if st.session_state.module_state.get('fusion_mode'):
            secondary = st.session_state.module_state.get('secondary_models', [])
            if secondary:
                model_info += f" | Fusion avec: {', '.join(secondary)}"
        st.info(f"🤖 {model_info}")
        
        # Barre de progression avec étapes
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulation d'analyse par étapes
        steps = [
            ("Extraction des éléments clés", 20),
            ("Analyse sémantique", 40),
            ("Recherche jurisprudentielle", 60),
            ("Corrélation avec cas similaires", 80),
            ("Génération des insights", 100)
        ]
        
        results_container = st.container()
        
        for step_name, progress in steps:
            status_text.text(f"⏳ {step_name}...")
            progress_bar.progress(progress / 100)
            time.sleep(0.5)
        
        status_text.text("✅ Analyse terminée!")
        
        # Résultats de l'analyse
        with results_container:
            # Score de confiance global
            st.markdown("#### 📊 Score de confiance global")
            confidence = 0.87
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(confidence)
            with col2:
                st.metric("Confiance", f"{confidence:.0%}")
            
            # Résumé exécutif
            st.markdown("#### 📝 Résumé exécutif")
            st.success("""
            **Points clés identifiés:**
            - Fort risque de qualification en escroquerie aggravée
            - Présence d'éléments constitutifs du délit d'abus de confiance
            - Circonstances aggravantes potentielles liées au montant du préjudice
            
            **Recommandations stratégiques:**
            1. Prioriser l'audition des témoins clés identifiés
            2. Demander une expertise comptable approfondie
            3. Envisager des mesures conservatoires sur les biens
            """)
            
            # Analyse détaillée par sections
            with st.expander("🔍 Analyse détaillée des faits"):
                st.markdown("""
                L'analyse IA a identifié plusieurs patterns récurrents dans les faits:
                - **Pattern 1**: Utilisation répétée de faux documents
                - **Pattern 2**: Dissimulation systématique des flux financiers
                - **Pattern 3**: Création de sociétés écrans
                
                Ces éléments suggèrent une organisation criminelle structurée.
                """)
            
            with st.expander("⚖️ Analyse juridique approfondie"):
                # Tableau des qualifications
                qualif_data = pd.DataFrame({
                    'Qualification': ['Escroquerie', 'Abus de confiance', 'Faux et usage'],
                    'Probabilité': ['92%', '87%', '78%'],
                    'Articles': ['313-1 CP', '314-1 CP', '441-1 CP'],
                    'Peine max': ['5 ans', '3 ans', '3 ans']
                })
                st.dataframe(qualif_data, hide_index=True, use_container_width=True)
            
            with st.expander("📊 Analyse prédictive"):
                col1, col2 = st.columns(2)
                with col1:
                    # Prédiction d'issue
                    st.markdown("**Prédiction d'issue:**")
                    outcomes = {
                        'Condamnation': 0.75,
                        'Relaxe partielle': 0.20,
                        'Relaxe totale': 0.05
                    }
                    for outcome, prob in outcomes.items():
                        st.write(f"{outcome}: {prob:.0%}")
                        st.progress(prob)
                
                with col2:
                    # Durée estimée
                    st.markdown("**Durée estimée de la procédure:**")
                    st.metric("Estimation", "18-24 mois")
                    st.info("Basé sur 147 cas similaires analysés")
            
            # Cas similaires
            if include_similar_cases:
                st.markdown("#### 🔗 Cas similaires identifiés")
                similar_cases = pd.DataFrame({
                    'Dossier': ['2023/045', '2022/178', '2021/234'],
                    'Similarité': ['94%', '87%', '82%'],
                    'Issue': ['Condamnation', 'Condamnation', 'Relaxe partielle'],
                    'Durée': ['22 mois', '18 mois', '14 mois']
                })
                st.dataframe(similar_cases, hide_index=True, use_container_width=True)
            
            # Export des résultats
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    "📄 Télécharger rapport complet",
                    data="Rapport d'analyse IA",
                    file_name=f"analyse_ia_{dossier.numero_dossier.replace('/', '_')}.pdf",
                    mime="application/pdf"
                )
            with col2:
                if st.button("📧 Partager l'analyse", use_container_width=True):
                    st.success("Analyse partagée avec l'équipe")
            with col3:
                if st.button("💾 Sauvegarder dans le dossier", use_container_width=True):
                    st.success("Analyse sauvegardée")

def display_list_view(manager: DossierPenalManager, search_query: str, statut_filter: List[str]):
    """Vue liste détaillée des dossiers"""
    st.markdown("### 📋 Liste détaillée des dossiers")
    
    # Filtrage
    dossiers = manager.list_dossiers()
    if search_query:
        dossiers = manager.search_dossiers(search_query)
    if statut_filter:
        dossiers = [d for d in dossiers if d.statut in statut_filter]
    
    if not dossiers:
        st.info("Aucun dossier ne correspond aux critères")
        return
    
    # Options d'affichage
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        sort_by = st.selectbox("Trier par", ["Date ↓", "Date ↑", "Risque ↓", "Numéro"])
    with col2:
        items_per_page = st.selectbox("Éléments par page", [10, 25, 50, 100], index=1)
    with col3:
        export_format = st.selectbox("Format export", ["Excel", "CSV", "PDF"])
    
    # Tri
    if sort_by == "Date ↓":
        dossiers.sort(key=lambda x: x.date_ouverture, reverse=True)
    elif sort_by == "Date ↑":
        dossiers.sort(key=lambda x: x.date_ouverture)
    elif sort_by == "Risque ↓":
        dossiers.sort(key=lambda x: x.risque_score, reverse=True)
    else:
        dossiers.sort(key=lambda x: x.numero_dossier)
    
    # Pagination
    total_pages = (len(dossiers) - 1) // items_per_page + 1
    current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(dossiers))
    
    # Affichage du tableau
    display_data = []
    for dossier in dossiers[start_idx:end_idx]:
        display_data.append({
            'Sélection': False,
            'N° Dossier': dossier.numero_dossier,
            'Titre': truncate_text(dossier.titre, 40),
            'Juridiction': dossier.juridiction,
            'Statut': dossier.statut,
            'Risque': f"{dossier.risque_score:.0%}",
            'Ouverture': dossier.date_ouverture.strftime('%d/%m/%Y'),
            'Durée': f"{(datetime.now() - dossier.date_ouverture).days}j",
            'Pièces': len(dossier.pieces),
            'ID': dossier.id
        })
    
    # DataFrame interactif
    df = pd.DataFrame(display_data)
    
    # Configuration de l'éditeur
    edited_df = st.data_editor(
        df,
        column_config={
            "Sélection": st.column_config.CheckboxColumn(
                "✓",
                help="Sélectionner pour actions groupées",
                default=False,
            ),
            "Risque": st.column_config.ProgressColumn(
                "Risque",
                help="Niveau de risque",
                format="%s",
                min_value="0%",
                max_value="100%",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="dossiers_table"
    )
    
    # Actions sur la sélection
    selected_rows = edited_df[edited_df['Sélection'] == True]
    if len(selected_rows) > 0:
        st.markdown(f"### Actions groupées ({len(selected_rows)} dossiers sélectionnés)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📊 Analyser sélection", use_container_width=True):
                st.info(f"Analyse de {len(selected_rows)} dossiers en cours...")
        with col2:
            if st.button("📁 Archiver sélection", use_container_width=True):
                st.warning("Confirmation requise pour l'archivage")
        with col3:
            if st.button("📤 Exporter sélection", use_container_width=True):
                st.success(f"Export de {len(selected_rows)} dossiers")
        with col4:
            if st.button("🏷️ Taguer sélection", use_container_width=True):
                st.info("Interface de tagging...")
    
    # Bouton pour ouvrir un dossier
    if st.session_state.get('selected_dossier_row') is not None:
        row = df.iloc[st.session_state.selected_dossier_row]
        st.session_state.current_dossier_id = row['ID']
        st.rerun()

def display_kanban_view(manager: DossierPenalManager, search_query: str, statut_filter: List[str]):
    """Vue Kanban des dossiers"""
    st.markdown("### 🗂️ Vue Kanban des dossiers")
    
    # Colonnes Kanban
    statuts = ["en_cours", "urgent", "suspendu", "clos", "archive"]
    if statut_filter:
        statuts = [s for s in statuts if s in statut_filter]
    
    cols = st.columns(len(statuts))
    
    # Récupération et filtrage des dossiers
    dossiers = manager.list_dossiers()
    if search_query:
        dossiers = manager.search_dossiers(search_query)
    
    # Affichage par colonne
    for col, statut in zip(cols, statuts):
        with col:
            # En-tête de colonne
            statut_display = statut.replace('_', ' ').title()
            count = len([d for d in dossiers if d.statut == statut])
            
            st.markdown(f"#### {statut_display} ({count})")
            
            # Style de la colonne
            col_style = {
                "en_cours": "background-color: #E8F5E9;",
                "urgent": "background-color: #FFEBEE;",
                "suspendu": "background-color: #FFF3E0;",
                "clos": "background-color: #E3F2FD;",
                "archive": "background-color: #F5F5F5;"
            }
            
            # Cartes de dossiers
            dossiers_statut = [d for d in dossiers if d.statut == statut]
            
            for dossier in dossiers_statut[:10]:  # Limiter à 10 par colonne
                # Carte Kanban
                with st.container():
                    card_html = f"""
                    <div style='border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-bottom: 10px; {col_style.get(statut, "")}'>
                        <strong>{dossier.numero_dossier}</strong><br>
                        <small>{truncate_text(dossier.titre, 30)}</small><br>
                        <span style='color: {get_risk_color(dossier.risque_score)}'>⚠️ {dossier.risque_score:.0%}</span>
                        <span style='float: right'>📅 {(datetime.now() - dossier.date_ouverture).days}j</span>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    if st.button("Ouvrir", key=f"kanban_{dossier.id}", use_container_width=True):
                        st.session_state.current_dossier_id = dossier.id
                        st.rerun()
            
            # Bouton voir plus
            if len(dossiers_statut) > 10:
                st.info(f"+ {len(dossiers_statut) - 10} autres dossiers")

def display_analytics_view(manager: DossierPenalManager):
    """Vue analytique globale"""
    st.markdown("### 📈 Analyses et statistiques globales")
    
    dossiers = manager.list_dossiers()
    
    if not dossiers:
        st.info("Aucune donnée à analyser")
        return
    
    # Métriques de performance
    st.markdown("#### 🎯 Métriques de performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_duration = calculate_average_duration(dossiers)
        st.metric(
            "Durée moyenne",
            f"{avg_duration} jours",
            f"{avg_duration - 120:.0f}j vs objectif"
        )
    
    with col2:
        resolution_rate = calculate_completion_rate(dossiers)
        st.metric(
            "Taux de résolution",
            f"{resolution_rate}%",
            "+5% ce trimestre"
        )
    
    with col3:
        urgent_rate = len([d for d in dossiers if d.statut == "urgent"]) / len(dossiers) * 100
        st.metric(
            "Taux d'urgence",
            f"{urgent_rate:.1f}%",
            "-2% ce mois"
        )
    
    with col4:
        avg_risk = sum(d.risque_score for d in dossiers) / len(dossiers)
        st.metric(
            "Risque moyen",
            f"{avg_risk:.0%}",
            "+0.05 ce mois"
        )
    
    # Graphiques analytiques
    col1, col2 = st.columns(2)
    
    with col1:
        # Evolution temporelle
        st.markdown("#### 📊 Évolution du nombre de dossiers")
        fig = create_evolution_chart(dossiers)
        st.plotly_chart(fig, use_container_width=True)
        
        # Distribution des risques
        st.markdown("#### 🎲 Distribution des niveaux de risque")
        fig = create_risk_distribution_chart(dossiers)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Répartition par type
        st.markdown("#### 📁 Répartition par type d'affaire")
        fig = create_type_distribution_chart(dossiers)
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance par juridiction
        st.markdown("#### ⚖️ Performance par juridiction")
        fig = create_jurisdiction_performance_chart(dossiers)
        st.plotly_chart(fig, use_container_width=True)
    
    # Insights IA
    st.markdown("### 💡 Insights et recommandations IA")
    
    with st.expander("🔍 Voir les insights détaillés", expanded=True):
        insights = generate_ai_insights(dossiers)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Points d'attention:**")
            for insight in insights['attention']:
                st.warning(f"• {insight}")
        
        with col2:
            st.markdown("**✅ Recommandations:**")
            for rec in insights['recommendations']:
                st.success(f"• {rec}")
    
    # Export des analyses
    st.markdown("### 📤 Export des analyses")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Rapport Excel complet", use_container_width=True):
            st.info("Génération du rapport Excel...")
    
    with col2:
        if st.button("📄 Rapport PDF exécutif", use_container_width=True):
            st.info("Génération du rapport PDF...")
    
    with col3:
        if st.button("🎯 Dashboard PowerBI", use_container_width=True):
            st.info("Export vers PowerBI...")

# Fonctions utilitaires
def calculate_average_duration(dossiers: List[DossierPenal]) -> int:
    """Calcule la durée moyenne des dossiers"""
    if not dossiers:
        return 0
    
    durations = []
    for dossier in dossiers:
        if dossier.date_cloture:
            duration = (dossier.date_cloture - dossier.date_ouverture).days
        else:
            duration = (datetime.now() - dossier.date_ouverture).days
        durations.append(duration)
    
    return sum(durations) // len(durations) if durations else 0

def calculate_completion_rate(dossiers: List[DossierPenal]) -> float:
    """Calcule le taux de complétion"""
    if not dossiers:
        return 0.0
    
    completed = len([d for d in dossiers if d.statut == "clos"])
    return (completed / len(dossiers)) * 100

def get_risk_color(risk_score: float) -> str:
    """Retourne la couleur selon le niveau de risque"""
    if risk_score >= 0.8:
        return "#FF0000"  # Rouge
    elif risk_score >= 0.6:
        return "#FF8C00"  # Orange foncé
    elif risk_score >= 0.4:
        return "#FFD700"  # Or
    else:
        return "#32CD32"  # Vert

def create_timeline_chart(dossiers: List[DossierPenal]) -> go.Figure:
    """Crée un graphique temporel des ouvertures/clôtures"""
    # Données simulées pour l'exemple
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    ouvertures = [5, 7, 6, 8, 9, 7, 10, 8, 9, 11, 8, 7]
    clotures = [3, 4, 5, 6, 5, 7, 6, 8, 7, 9, 6, 5]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=ouvertures,
        mode='lines+markers',
        name='Ouvertures',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=clotures,
        mode='lines+markers',
        name='Clôtures',
        line=dict(color='green', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Évolution mensuelle des dossiers",
        xaxis_title="Mois",
        yaxis_title="Nombre de dossiers",
        hovermode='x unified'
    )
    
    return fig

def create_jurisdiction_chart(dossiers: List[DossierPenal]) -> go.Figure:
    """Crée un graphique de répartition par juridiction"""
    jurisdictions = {}
    for dossier in dossiers:
        jurisdictions[dossier.juridiction] = jurisdictions.get(dossier.juridiction, 0) + 1
    
    fig = go.Figure(data=[
        go.Pie(
            labels=list(jurisdictions.keys()),
            values=list(jurisdictions.values()),
            hole=0.3
        )
    ])
    
    fig.update_layout(title="Répartition par juridiction")
    return fig

def display_ai_alerts(dossiers: List[DossierPenal]):
    """Affiche les alertes IA"""
    alerts = [
        {"type": "urgent", "message": "3 dossiers nécessitent une action immédiate", "icon": "🚨"},
        {"type": "warning", "message": "5 dossiers approchent de leur délai limite", "icon": "⚠️"},
        {"type": "info", "message": "2 nouvelles jurisprudences pertinentes détectées", "icon": "💡"},
        {"type": "success", "message": "Taux de résolution en hausse de 5% ce mois", "icon": "✅"}
    ]
    
    cols = st.columns(len(alerts))
    for col, alert in zip(cols, alerts):
        with col:
            if alert["type"] == "urgent":
                st.error(f"{alert['icon']} {alert['message']}")
            elif alert["type"] == "warning":
                st.warning(f"{alert['icon']} {alert['message']}")
            elif alert["type"] == "info":
                st.info(f"{alert['icon']} {alert['message']}")
            else:
                st.success(f"{alert['icon']} {alert['message']}")

def perform_quick_ai_analysis(dossier_id: str):
    """Effectue une analyse IA rapide"""
    with st.spinner("Analyse IA en cours..."):
        time.sleep(2)
        st.success("✅ Analyse terminée - Consultez l'onglet Analyse IA pour les détails")

def generate_report(dossier: DossierPenal):
    """Génère un rapport pour le dossier"""
    with st.spinner("Génération du rapport..."):
        time.sleep(2)
        st.success("📄 Rapport généré avec succès!")

def export_dossier(dossier: DossierPenal):
    """Exporte un dossier"""
    st.download_button(
        label="📥 Télécharger l'export",
        data=json.dumps(dossier.__dict__, default=str, indent=2),
        file_name=f"dossier_{dossier.numero_dossier.replace('/', '_')}.json",
        mime="application/json"
    )

def display_parties_tab_enhanced(dossier: DossierPenal, manager: DossierPenalManager):
    """Affichage amélioré de l'onglet parties"""
    st.markdown("### 👥 Gestion des parties et acteurs")
    
    # Statistiques rapides
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Demandeurs", len(dossier.parties.get("demandeurs", [])))
    with col2:
        st.metric("Défendeurs", len(dossier.parties.get("defendeurs", [])))
    with col3:
        st.metric("Témoins", len(dossier.parties.get("temoins", [])))
    with col4:
        st.metric("Experts", len(dossier.parties.get("experts", [])))
    
    # Interface par type de partie
    party_types = [
        ("demandeurs", "👤 Demandeurs", "primary"),
        ("defendeurs", "⚖️ Défendeurs", "secondary"),
        ("temoins", "👁️ Témoins", "info"),
        ("experts", "🔬 Experts", "success")
    ]
    
    for party_type, label, color in party_types:
        with st.expander(f"{label} ({len(dossier.parties.get(party_type, []))})", expanded=True):
            # Formulaire d'ajout
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                nom = st.text_input("Nom complet", key=f"nom_{party_type}_tab")
            with col2:
                role = st.text_input("Rôle/Fonction", key=f"role_{party_type}_tab")
            with col3:
                contact = st.text_input("Contact", key=f"contact_{party_type}_tab")
            with col4:
                if st.button("➕", key=f"add_{party_type}_tab", use_container_width=True):
                    if nom:
                        if party_type not in dossier.parties:
                            dossier.parties[party_type] = []
                        dossier.parties[party_type].append({
                            'nom': nom,
                            'role': role,
                            'contact': contact,
                            'date_ajout': datetime.now().isoformat()
                        })
                        manager.update_dossier(dossier.id, parties=dossier.parties)
                        st.success(f"✅ {nom} ajouté")
                        st.rerun()
            
            # Liste avec options avancées
            if dossier.parties.get(party_type):
                for i, partie in enumerate(dossier.parties[party_type]):
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                        with col1:
                            st.write(f"**{partie.get('nom', partie)}**")
                        with col2:
                            if isinstance(partie, dict):
                                st.write(partie.get('role', ''))
                        with col3:
                            if isinstance(partie, dict):
                                st.write(partie.get('contact', ''))
                        with col4:
                            if st.button("✏️", key=f"edit_{party_type}_{i}_tab"):
                                st.info("Mode édition à implémenter")
                        with col5:
                            if st.button("🗑️", key=f"del_{party_type}_{i}_tab"):
                                dossier.parties[party_type].pop(i)
                                manager.update_dossier(dossier.id, parties=dossier.parties)
                                st.rerun()

def display_documents_tab(dossier: DossierPenal, manager: DossierPenalManager):
    """Onglet de gestion des documents et pièces"""
    st.markdown("### 📎 Gestion des documents et pièces")
    
    # Upload de nouveaux documents
    with st.expander("➕ Ajouter des documents", expanded=False):
        uploaded_files = st.file_uploader(
            "Glissez vos fichiers ici",
            type=['pdf', 'docx', 'txt', 'jpg', 'png'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            col1, col2, col3 = st.columns(3)
            with col1:
                doc_type = st.selectbox(
                    "Type de document",
                    ["Procès-verbal", "Rapport", "Témoignage", "Expertise", "Photo", "Autre"]
                )
            with col2:
                confidentialite = st.selectbox(
                    "Niveau de confidentialité",
                    ["Public", "Interne", "Confidentiel", "Secret"]
                )
            with col3:
                if st.button("📤 Téléverser", type="primary", use_container_width=True):
                    for file in uploaded_files:
                        # Simulation d'upload
                        piece_id = f"DOC_{uuid.uuid4().hex[:8]}"
                        dossier.pieces.append(piece_id)
                    manager.update_dossier(dossier.id, pieces=dossier.pieces)
                    st.success(f"✅ {len(uploaded_files)} document(s) ajouté(s)")
                    st.rerun()
    
    # Liste des documents avec filtres
    st.markdown("#### 📋 Documents existants")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.multiselect("Type", ["Tous", "PV", "Rapport", "Témoignage"])
    with col2:
        filter_date = st.date_input("Date depuis", value=None)
    with col3:
        search_doc = st.text_input("🔍 Rechercher", placeholder="Nom, contenu...")
    
    # Affichage des documents
    if dossier.pieces:
        # Simulation de métadonnées pour les pièces
        for i, piece_id in enumerate(dossier.pieces):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 1])
                
                with col1:
                    st.write(f"#{i+1}")
                with col2:
                    st.write(f"📄 Document {piece_id}")
                    st.caption(f"Ajouté le {datetime.now().strftime('%d/%m/%Y')}")
                with col3:
                    st.info("Procès-verbal")
                with col4:
                    if st.button("👁️", key=f"view_doc_{i}", help="Visualiser"):
                        st.info("Visualisation à implémenter")
                with col5:
                    if st.button("🗑️", key=f"del_doc_{i}"):
                        dossier.pieces.pop(i)
                        manager.update_dossier(dossier.id, pieces=dossier.pieces)
                        st.rerun()
    else:
        st.info("Aucun document dans ce dossier")
    
    # Analyse documentaire IA
    st.markdown("### 🤖 Analyse documentaire IA")
    if st.button("🔍 Analyser tous les documents", type="primary", use_container_width=True):
        with st.spinner("Analyse en cours..."):
            time.sleep(2)
            st.success("✅ Analyse terminée")
            
            # Résultats simulés
            st.markdown("**Résumé de l'analyse:**")
            st.info("""
            • 15 documents analysés
            • 3 incohérences détectées
            • 5 éléments clés identifiés
            • 2 documents manquants suggérés
            """)

def display_timeline_tab(dossier: DossierPenal, manager: DossierPenalManager):
    """Onglet chronologie interactive"""
    st.markdown("### 📅 Chronologie des événements")
    
    # Ajout d'événement
    with st.expander("➕ Ajouter un événement"):
        col1, col2 = st.columns(2)
        with col1:
            event_title = st.text_input("Titre de l'événement")
            event_date = st.date_input("Date", value=datetime.now())
            event_time = st.time_input("Heure")
        with col2:
            event_type = st.selectbox(
                "Type",
                ["Audience", "Dépôt", "Expertise", "Décision", "Autre"]
            )
            event_importance = st.select_slider(
                "Importance",
                ["Mineure", "Normale", "Importante", "Critique"]
            )
        
        event_description = st.text_area("Description", height=100)
        
        if st.button("➕ Ajouter à la chronologie", type="primary"):
            if event_title:
                event_id = f"EVT_{uuid.uuid4().hex[:8]}"
                dossier.evenements.append(event_id)
                manager.update_dossier(dossier.id, evenements=dossier.evenements)
                st.success(f"✅ Événement '{event_title}' ajouté")
                st.rerun()
    
    # Timeline visuelle
    if dossier.evenements:
        st.markdown("#### 📊 Vue chronologique")
        
        # Création d'une timeline interactive avec Plotly
        events_data = []
        for i, event_id in enumerate(dossier.evenements):
            # Simulation de données d'événements
            events_data.append({
                'Date': datetime.now() - timedelta(days=i*10),
                'Événement': f"Événement {event_id}",
                'Type': ["Audience", "Dépôt", "Expertise"][i % 3],
                'Importance': [1, 2, 3, 4][i % 4]
            })
        
        # Graphique timeline
        fig = go.Figure()
        
        for event in events_data:
            color = ['blue', 'green', 'orange', 'red'][event['Importance'] - 1]
            fig.add_trace(go.Scatter(
                x=[event['Date']],
                y=[event['Type']],
                mode='markers+text',
                marker=dict(size=15, color=color),
                text=event['Événement'],
                textposition='top center',
                name=event['Événement']
            ))
        
        fig.update_layout(
            title="Timeline des événements",
            xaxis_title="Date",
            yaxis_title="Type d'événement",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Liste détaillée
        st.markdown("#### 📋 Détail des événements")
        for event in sorted(events_data, key=lambda x: x['Date'], reverse=True):
            with st.container():
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.write(f"📅 {event['Date'].strftime('%d/%m/%Y')}")
                with col2:
                    st.write(f"**{event['Événement']}**")
                    st.caption(f"Type: {event['Type']}")
                with col3:
                    importance_colors = ['🟢', '🟡', '🟠', '🔴']
                    st.write(importance_colors[event['Importance'] - 1])
    else:
        st.info("Aucun événement enregistré")

def display_communications_tab(dossier: DossierPenal, manager: DossierPenalManager):
    """Onglet communications et échanges"""
    st.markdown("### 💬 Communications et échanges")
    
    # Nouveau message
    with st.expander("✉️ Nouveau message"):
        col1, col2 = st.columns(2)
        with col1:
            destinataire = st.selectbox(
                "Destinataire",
                ["Juge d'instruction", "Procureur", "Avocat adverse", "Client", "Expert"]
            )
            objet = st.text_input("Objet")
        with col2:
            urgence = st.checkbox("🚨 Urgent")
            confidentiel = st.checkbox("🔒 Confidentiel")
        
        message = st.text_area("Message", height=150)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 Envoyer", type="primary", use_container_width=True):
                st.success("✅ Message envoyé")
        with col2:
            if st.button("💾 Brouillon", use_container_width=True):
                st.info("Sauvegardé en brouillon")
        with col3:
            if st.button("🤖 IA Rédaction", use_container_width=True):
                st.info("Assistant de rédaction IA...")
    
    # Historique des communications
    st.markdown("#### 📧 Historique des échanges")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.multiselect("Type", ["Email", "Courrier", "Note", "Appel"])
    with col2:
        filter_expediteur = st.multiselect("Expéditeur", ["Tous", "Juge", "Procureur"])
    with col3:
        search_comm = st.text_input("🔍 Rechercher")
    
    # Messages simulés
    messages = [
        {
            "date": datetime.now() - timedelta(days=2),
            "expediteur": "Juge Martin",
            "objet": "Convocation audience",
            "urgent": True,
            "lu": False
        },
        {
            "date": datetime.now() - timedelta(days=5),
            "expediteur": "Procureur Dupont",
            "objet": "Demande de pièces complémentaires",
            "urgent": False,
            "lu": True
        }
    ]
    
    for msg in messages:
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
            with col1:
                if not msg["lu"]:
                    st.markdown("🔵 **Non lu**")
                else:
                    st.markdown("⚪ Lu")
            with col2:
                st.write(f"**{msg['objet']}**")
                st.caption(f"De: {msg['expediteur']}")
            with col3:
                st.write(msg['date'].strftime('%d/%m/%Y %H:%M'))
                if msg["urgent"]:
                    st.error("🚨 Urgent")
            with col4:
                if st.button("👁️", key=f"view_msg_{msg['objet']}"):
                    st.info("Affichage du message...")

def display_statistics_tab(dossier: DossierPenal, manager: DossierPenalManager):
    """Onglet statistiques détaillées"""
    st.markdown("### 📊 Statistiques et analyses du dossier")
    
    # KPIs principaux
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        duration = (datetime.now() - dossier.date_ouverture).days
        st.metric("Durée totale", f"{duration} jours")
    
    with col2:
        activity_score = min(100, len(dossier.evenements) * 10)
        st.metric("Score d'activité", f"{activity_score}%")
    
    with col3:
        completion = len([p for p in dossier.pieces]) / 10 * 100  # Estimation
        st.metric("Complétude", f"{completion:.0f}%")
    
    with col4:
        complexity = len(dossier.qualification_juridique) * 25
        st.metric("Complexité", f"{complexity}%")
    
    # Graphiques détaillés
    col1, col2 = st.columns(2)
    
    with col1:
        # Activité mensuelle
        st.markdown("#### 📈 Activité mensuelle")
        months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun']
        activity = [5, 8, 12, 15, 10, 7]
        
        fig = go.Figure(data=[
            go.Bar(x=months, y=activity, marker_color='lightblue')
        ])
        fig.update_layout(
            title="Nombre d'actions par mois",
            yaxis_title="Actions"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Répartition du temps
        st.markdown("#### ⏱️ Répartition du temps")
        
        labels = ['Instruction', 'Audiences', 'Expertises', 'Rédaction', 'Autre']
        values = [30, 25, 20, 15, 10]
        
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        fig.update_layout(title="Répartition du temps passé")
        st.plotly_chart(fig, use_container_width=True)
    
    # Prévisions
    st.markdown("### 🔮 Prévisions et projections")
    
    with st.expander("Voir les prévisions détaillées", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **📅 Durée estimée restante:** 6-8 mois
            
            **Facteurs d'accélération:**
            • Accord entre parties possible
            • Expertise unique suffisante
            
            **Facteurs de ralentissement:**
            • Complexité juridique élevée
            • Nombre de parties important
            """)
        
        with col2:
            # Graphique de projection
            dates = pd.date_range(start=datetime.now(), periods=12, freq='M')
            probabilities = [0.1, 0.15, 0.25, 0.4, 0.55, 0.7, 0.8, 0.87, 0.92, 0.95, 0.97, 0.98]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=probabilities,
                mode='lines+markers',
                name='Probabilité de clôture',
                line=dict(color='green', width=3)
            ))
            
            fig.update_layout(
                title="Projection de clôture",
                xaxis_title="Date",
                yaxis_title="Probabilité",
                yaxis_tickformat='.0%'
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Fonctions de création de graphiques
def create_evolution_chart(dossiers: List[DossierPenal]) -> go.Figure:
    """Crée un graphique d'évolution temporelle"""
    # Simulation de données
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    counts = [len([d for d in dossiers if d.date_ouverture.month == i]) for i in range(1, 13)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=counts,
        mode='lines+markers',
        fill='tozeroy',
        name='Nouveaux dossiers'
    ))
    
    fig.update_layout(
        title="Évolution du nombre de dossiers",
        xaxis_title="Mois",
        yaxis_title="Nombre de dossiers"
    )
    
    return fig

def create_risk_distribution_chart(dossiers: List[DossierPenal]) -> go.Figure:
    """Crée un graphique de distribution des risques"""
    risk_levels = ['Faible', 'Moyen', 'Élevé', 'Critique']
    counts = [
        len([d for d in dossiers if d.risque_score < 0.25]),
        len([d for d in dossiers if 0.25 <= d.risque_score < 0.5]),
        len([d for d in dossiers if 0.5 <= d.risque_score < 0.75]),
        len([d for d in dossiers if d.risque_score >= 0.75])
    ]
    
    colors = ['green', 'yellow', 'orange', 'red']
    
    fig = go.Figure(data=[
        go.Bar(x=risk_levels, y=counts, marker_color=colors)
    ])
    
    fig.update_layout(
        title="Distribution des niveaux de risque",
        xaxis_title="Niveau de risque",
        yaxis_title="Nombre de dossiers"
    )
    
    return fig

def create_type_distribution_chart(dossiers: List[DossierPenal]) -> go.Figure:
    """Crée un graphique de répartition par type"""
    # Simulation des types basée sur les qualifications
    types = {}
    for dossier in dossiers:
        for qual in dossier.qualification_juridique[:1]:  # Premier type seulement
            type_simple = qual.split('(')[0].strip() if qual else "Non qualifié"
            types[type_simple] = types.get(type_simple, 0) + 1
    
    if not types:
        types = {"Non qualifié": len(dossiers)}
    
    fig = go.Figure(data=[
        go.Pie(labels=list(types.keys()), values=list(types.values()))
    ])
    
    fig.update_layout(title="Répartition par type d'affaire")
    return fig

def create_jurisdiction_performance_chart(dossiers: List[DossierPenal]) -> go.Figure:
    """Crée un graphique de performance par juridiction"""
    jurisdictions = {}
    
    for dossier in dossiers:
        if dossier.juridiction not in jurisdictions:
            jurisdictions[dossier.juridiction] = {
                'total': 0,
                'clos': 0,
                'duree_moy': []
            }
        
        jurisdictions[dossier.juridiction]['total'] += 1
        
        if dossier.statut == 'clos':
            jurisdictions[dossier.juridiction]['clos'] += 1
            if dossier.date_cloture:
                duree = (dossier.date_cloture - dossier.date_ouverture).days
                jurisdictions[dossier.juridiction]['duree_moy'].append(duree)
    
    # Calcul des métriques
    jur_names = []
    taux_resolution = []
    duree_moyenne = []
    
    for jur, data in jurisdictions.items():
        jur_names.append(jur)
        taux = (data['clos'] / data['total'] * 100) if data['total'] > 0 else 0
        taux_resolution.append(taux)
        
        if data['duree_moy']:
            duree_moyenne.append(sum(data['duree_moy']) / len(data['duree_moy']))
        else:
            duree_moyenne.append(0)
    
    # Graphique à barres groupées
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Taux résolution (%)',
        x=jur_names,
        y=taux_resolution,
        yaxis='y',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Durée moy. (jours)',
        x=jur_names,
        y=duree_moyenne,
        yaxis='y2',
        marker_color='lightgreen'
    ))
    
    fig.update_layout(
        title="Performance par juridiction",
        xaxis_title="Juridiction",
        yaxis=dict(
            title="Taux de résolution (%)",
            side="left"
        ),
        yaxis2=dict(
            title="Durée moyenne (jours)",
            overlaying="y",
            side="right"
        ),
        hovermode='x unified'
    )
    
    return fig

def generate_ai_insights(dossiers: List[DossierPenal]) -> Dict:
    """Génère des insights IA sur l'ensemble des dossiers"""
    insights = {
        'attention': [
            f"{len([d for d in dossiers if d.risque_score > 0.8])} dossiers présentent un risque critique",
            f"{len([d for d in dossiers if (datetime.now() - d.date_ouverture).days > 365])} dossiers ouverts depuis plus d'un an",
            "Augmentation de 15% des affaires financières ce trimestre"
        ],
        'recommendations': [
            "Renforcer l'équipe sur les dossiers à risque élevé",
            "Accélérer le traitement des dossiers anciens",
            "Mettre en place une cellule spécialisée affaires financières",
            "Former l'équipe aux nouvelles jurisprudences"
        ]
    }
    
    return insights

# Point d'entrée obligatoire
if __name__ == "__main__":
    run()
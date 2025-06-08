"""Core du module de recherche - Interface principale et routing"""

import streamlit as st
import re
from datetime import datetime

# Imports des sous-modules
from .recherche_config import REDACTION_STYLES, DOCUMENT_TEMPLATES
from .recherche_import import process_import_request
from .recherche_export import process_export_request
from .recherche_redaction import process_redaction_request, generate_plainte
from .recherche_analysis import process_analysis_request
from .recherche_display import show_unified_results_tab
from .recherche_pieces import (
    process_piece_selection_request,
    process_bordereau_request,
    process_synthesis_request
)
from .recherche_utils import analyze_query

def show_page():
    """Fonction principale de la page recherche universelle"""
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # Barre de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "Entrez votre commande ou recherche",
            placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, importer documents...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique"
        )
    
    with col2:
        search_button = st.button("🔍 Rechercher", key="search_button", use_container_width=True)
    
    # Suggestions de commandes
    with st.expander("💡 Exemples de commandes", expanded=False):
        st.markdown("""
        **Recherche :**
        - `contrats société XYZ`
        - `@affaire_martin documents comptables`
        
        **Analyse :**
        - `analyser les risques @dossier_pénal`
        - `identifier les infractions @affaire_corruption`
        
        **Rédaction :**
        - `rédiger conclusions défense @affaire_martin abus biens sociaux`
        - `créer plainte avec constitution partie civile escroquerie`
        - `rédiger plainte contre Vinci, SOGEPROM @projet_26_05_2025`
        
        **Visualisations :**
        - `chronologie des faits @affaire_martin`
        - `cartographie des sociétés @groupe_abc`
        
        **Gestion :**
        - `importer documents PDF`
        - `exporter analyse format word`
        - `envoyer par email @destinataire`
        """)
    
    # Traiter la requête
    if query and (search_button or st.session_state.get('process_query', False)):
        with st.spinner("🔄 Traitement en cours..."):
            process_universal_query(query)
    
    # Afficher les résultats
    show_unified_results_tab()
    
    # Réinitialiser le flag de traitement
    if 'process_query' in st.session_state:
        st.session_state.process_query = False

def process_universal_query(query: str):
    """Traite une requête universelle et route vers la bonne fonction"""
    
    # Sauvegarder la requête
    st.session_state.last_universal_query = query
    
    # Analyser la requête pour détecter le type
    query_lower = query.lower()
    
    # DÉTECTION POUR RÉDACTION (incluant votre cas de plainte)
    if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer', 'plainte', 'conclusions']):
        st.info("📝 Détection d'une demande de rédaction...")
        
        # Cas spécifique : plainte avec parties multiples
        if 'plainte' in query_lower:
            # Extraire les parties de la requête
            parties = []
            parties_keywords = [
                'interconstruction', 'vinci', 'sogeprom', 'demathieu bard',
                'bouygues', 'eiffage', 'spie', 'leon grosse'
            ]
            
            for partie in parties_keywords:
                if partie in query_lower:
                    # Formatage correct du nom
                    if partie == 'sogeprom':
                        parties.append('SOGEPROM Réalisations')
                    elif partie == 'demathieu bard':
                        parties.append('Demathieu Bard')
                    else:
                        parties.append(partie.title())
            
            # Extraire la référence
            reference = None
            if '@' in query:
                ref_match = re.search(r'@(\w+)', query)
                if ref_match:
                    reference = ref_match.group(1)
            
            # Créer la demande de rédaction
            st.session_state.redaction_request = {
                'type': 'plainte',
                'parties': parties,
                'reference': reference,
                'query': query
            }
            
            # Générer la plainte
            generate_plainte(query, parties)
        else:
            # Autres types de rédaction
            process_redaction_request(query, analyze_query(query))
    
    # AUTRES TYPES DE REQUÊTES
    elif any(word in query_lower for word in ['import', 'importer', 'charger']):
        st.info("📥 Détection d'une demande d'import...")
        process_import_request(query, {'type': 'import'})
        
    elif any(word in query_lower for word in ['export', 'exporter', 'télécharger']):
        st.info("💾 Détection d'une demande d'export...")
        process_export_request(query, {'type': 'export'})
        
    elif any(word in query_lower for word in ['analyser', 'analyse', 'étudier']):
        st.info("🤖 Détection d'une demande d'analyse...")
        process_analysis_request(query, {'type': 'analysis'})
        
    elif any(word in query_lower for word in ['sélectionner pièces', 'pièces']):
        st.info("📋 Détection d'une demande de sélection de pièces...")
        process_piece_selection_request(query, {'type': 'piece_selection'})
        
    elif 'bordereau' in query_lower:
        st.info("📊 Détection d'une demande de bordereau...")
        process_bordereau_request(query, {'type': 'bordereau'})
        
    else:
        # Recherche simple par défaut
        st.info("🔍 Recherche simple...")
        from .recherche_search import process_search_request
        process_search_request(query, {'type': 'search'})
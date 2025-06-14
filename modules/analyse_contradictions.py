"""Module d'analyse des contradictions dans les documents juridiques"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import clean_key, format_legal_date, truncate_text
from utils.decorators import decorate_public_functions

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])


def run():
    """Fonction principale du module"""
    st.title("🔍 Analyse des Contradictions")
    st.markdown("Détectez automatiquement les incohérences et contradictions dans vos documents juridiques.")
    
    # Métriques de session
    if 'analysis_stats' not in st.session_state:
        st.session_state.analysis_stats = {
            'analyses_count': 0,
            'contradictions_found': 0,
            'documents_analyzed': 0
        }
    
    # Onglets pour l'organisation
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Sélection", "⚙️ Configuration", "🔍 Analyse", "📊 Résultats"])
    
    with tab1:
        st.markdown("### Sélection des documents à analyser")
        
        # Sélection du mode
        selection_mode = st.radio(
            "Mode de sélection",
            ["📁 Depuis un container Azure", "⬆️ Upload de fichiers", "🔍 Recherche avancée"],
            horizontal=True
        )
        
        if selection_mode == "📁 Depuis un container Azure":
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Récupération du container actif depuis la session
                active_container = st.session_state.get('active_container', None)
                containers = ["juridique", "expertises", "procedures", "correspondances", "factures"]
                
                container = st.selectbox(
                    "Container",
                    containers,
                    index=containers.index(active_container) if active_container in containers else 0
                )
                
                # Filtre par date
                date_filter = st.date_input(
                    "Filtrer après le",
                    value=None,
                    help="Laisser vide pour voir tous les documents"
                )
            
            with col2:
                # Simulation de documents disponibles
                if container:
                    documents_data = {
                        'juridique': [
                            ("PV_audition_temoin1_2024-03-15.pdf", "235 KB", "15/03/2024"),
                            ("PV_audition_temoin2_2024-03-16.pdf", "189 KB", "16/03/2024"),
                            ("Conclusions_partie_adverse.pdf", "456 KB", "20/03/2024"),
                            ("Memoire_en_replique.pdf", "789 KB", "25/03/2024")
                        ],
                        'expertises': [
                            ("Expertise_medicale_2024.pdf", "1.2 MB", "10/03/2024"),
                            ("Rapport_expert_comptable.pdf", "890 KB", "12/03/2024"),
                            ("Expertise_technique_batiment.pdf", "2.1 MB", "18/03/2024")
                        ],
                        'procedures': [
                            ("Assignation_TGI_Paris.pdf", "345 KB", "01/03/2024"),
                            ("Ordonnance_refere.pdf", "234 KB", "05/03/2024"),
                            ("Jugement_premiere_instance.pdf", "567 KB", "28/03/2024")
                        ]
                    }
                    
                    documents = documents_data.get(container, [])
                    
                    # Affichage sous forme de dataframe sélectionnable
                    df = pd.DataFrame(documents, columns=['Fichier', 'Taille', 'Date'])
                    
                    selected_indices = st.multiselect(
                        "Sélectionnez les documents à analyser",
                        options=list(range(len(df))),
                        format_func=lambda x: df.iloc[x]['Fichier'],
                        help="Sélectionnez au moins 2 documents pour une analyse comparative"
                    )
                    
                    if selected_indices:
                        st.info(f"✅ {len(selected_indices)} documents sélectionnés")
                        selected_docs = [df.iloc[i]['Fichier'] for i in selected_indices]
                        st.session_state.selected_documents = selected_docs
        
        elif selection_mode == "⬆️ Upload de fichiers":
            uploaded_files = st.file_uploader(
                "Chargez vos documents",
                type=['pdf', 'txt', 'docx', 'doc'],
                accept_multiple_files=True,
                help="Formats acceptés : PDF, TXT, DOCX, DOC"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} fichiers chargés")
                
                # Aperçu des fichiers
                file_data = []
                for file in uploaded_files:
                    file_data.append({
                        'Nom': file.name,
                        'Taille': f"{file.size / 1024:.1f} KB",
                        'Type': file.type
                    })
                
                df_files = pd.DataFrame(file_data)
                st.dataframe(df_files, use_container_width=True, hide_index=True)
        
        else:  # Recherche avancée
            st.markdown("### 🔍 Recherche de documents par mots-clés")
            
            search_query = st.text_input(
                "Mots-clés",
                placeholder="Ex: accident, témoin, expertise médicale..."
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                search_container = st.selectbox("Container", ["Tous"] + ["juridique", "expertises", "procedures"])
            with col2:
                search_date_start = st.date_input("Date début", value=None)
            with col3:
                search_date_end = st.date_input("Date fin", value=None)
            
            if st.button("🔍 Rechercher", type="primary", use_container_width=True):
                with st.spinner("Recherche en cours..."):
                    time.sleep(1)
                    st.success("5 documents trouvés correspondant aux critères")
    
    with tab2:
        st.markdown("### ⚙️ Configuration de l'analyse")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Types d'analyse")
            
            analysis_types = {
                'temporal': st.checkbox("⏰ Contradictions temporelles", value=True, 
                    help="Détecte les incohérences de dates, heures et chronologies"),
                'factual': st.checkbox("📋 Contradictions factuelles", value=True,
                    help="Identifie les versions différentes des mêmes faits"),
                'numerical': st.checkbox("🔢 Contradictions numériques", value=True,
                    help="Repère les différences dans les montants, quantités, mesures"),
                'identity': st.checkbox("👤 Contradictions d'identité", value=True,
                    help="Détecte les incohérences sur les personnes, lieux, entités"),
                'causal': st.checkbox("🔗 Contradictions causales", value=False,
                    help="Analyse les incohérences dans les relations de cause à effet")
            }
            
            st.session_state.analysis_config = analysis_types
        
        with col2:
            st.markdown("#### Paramètres avancés")
            
            sensitivity = st.slider(
                "Sensibilité de détection",
                min_value=1,
                max_value=10,
                value=7,
                help="Plus la valeur est élevée, plus l'analyse détecte de contradictions potentielles"
            )
            
            confidence_threshold = st.slider(
                "Seuil de confiance (%)",
                min_value=50,
                max_value=100,
                value=75,
                step=5,
                help="Ne montrer que les contradictions avec un score de confiance supérieur"
            )
            
            context_window = st.number_input(
                "Fenêtre de contexte (mots)",
                min_value=10,
                max_value=500,
                value=50,
                step=10,
                help="Nombre de mots à afficher autour de chaque contradiction"
            )
            
            # Mode d'analyse
            st.markdown("#### Mode d'analyse")
            analysis_mode = st.radio(
                "",
                ["🚀 Rapide (~ 30 sec)", "⚡ Standard (~ 2 min)", "🔬 Approfondie (~ 5 min)"],
                index=1,
                help="Le mode approfondi utilise des techniques d'analyse plus poussées"
            )
        
        # Sauvegarde de configuration
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Sauvegarder configuration", use_container_width=True):
                st.success("Configuration sauvegardée !")
        with col2:
            if st.button("🔄 Configuration par défaut", use_container_width=True):
                st.info("Configuration réinitialisée")
    
    with tab3:
        st.markdown("### 🔍 Lancement de l'analyse")
        
        # Vérification des prérequis
        ready_to_analyze = True
        
        if 'selected_documents' not in st.session_state or not st.session_state.selected_documents:
            st.warning("⚠️ Veuillez sélectionner au moins 2 documents dans l'onglet 'Sélection'")
            ready_to_analyze = False
        else:
            st.success(f"✅ {len(st.session_state.selected_documents)} documents prêts pour l'analyse")
        
        # Résumé de la configuration
        if 'analysis_config' in st.session_state:
            active_analyses = [k for k, v in st.session_state.analysis_config.items() if v]
            st.info(f"**Analyses actives:** {len(active_analyses)} types")
        
        # Bouton d'analyse principal
        if st.button(
            "🚀 Lancer l'analyse des contradictions",
            type="primary",
            use_container_width=True,
            disabled=not ready_to_analyze
        ):
            # Barre de progression détaillée
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Phases d'analyse
                phases = [
                    ("Chargement des documents", 10),
                    ("Extraction du contenu", 20),
                    ("Analyse linguistique", 30),
                    ("Détection des entités", 40),
                    ("Recherche de contradictions", 60),
                    ("Calcul des scores de confiance", 80),
                    ("Génération du rapport", 90),
                    ("Finalisation", 100)
                ]
                
                for phase, progress in phases:
                    status_text.text(f"⏳ {phase}...")
                    progress_bar.progress(progress)
                    time.sleep(0.5)
                
                status_text.text("✅ Analyse terminée !")
                time.sleep(0.5)
                
                # Mise à jour des statistiques
                st.session_state.analysis_stats['analyses_count'] += 1
                st.session_state.analysis_stats['documents_analyzed'] += len(st.session_state.selected_documents)
                st.session_state.analysis_complete = True
                
                # Métriques de résultat
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Temps d'analyse", "1m 23s")
                with col2:
                    st.metric("Passages analysés", "1,247")
                with col3:
                    st.metric("Taux de couverture", "94%")
    
    with tab4:
        if hasattr(st.session_state, 'analysis_complete') and st.session_state.analysis_complete:
            st.markdown("### 📊 Résultats de l'analyse")
            
            # Vue d'ensemble avec métriques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Documents analysés",
                    len(st.session_state.selected_documents),
                    help="Nombre total de documents traités"
                )
            with col2:
                contradictions_count = 12
                st.metric(
                    "Contradictions détectées",
                    contradictions_count,
                    delta="+3 vs dernière analyse",
                    help="Nombre total de contradictions identifiées"
                )
                st.session_state.analysis_stats['contradictions_found'] += contradictions_count
            with col3:
                st.metric(
                    "Score de cohérence",
                    "73%",
                    delta="-8%",
                    help="Cohérence globale du dossier"
                )
            with col4:
                st.metric(
                    "Alertes critiques",
                    "3",
                    help="Contradictions nécessitant une attention immédiate"
                )
            
            # Filtres de résultats
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_type = st.multiselect(
                    "Type de contradiction",
                    ["Temporelle", "Factuelle", "Numérique", "Identité"],
                    default=["Temporelle", "Factuelle", "Numérique", "Identité"]
                )
            with col2:
                filter_criticality = st.select_slider(
                    "Niveau de criticité",
                    options=["Toutes", "Faible", "Moyenne", "Élevée"],
                    value="Toutes"
                )
            with col3:
                filter_confidence = st.slider(
                    "Confiance min (%)",
                    50, 100, 75
                )
            
            # Tableau détaillé des contradictions
            st.markdown("### 📋 Détail des contradictions")
            
            # Données simulées
            contradictions_data = []
            criticality_levels = {
                'high': '<span class="criticality-high">⚠️ Élevée</span>',
                'medium': '<span class="criticality-medium">⚡ Moyenne</span>',
                'low': '<span class="criticality-low">💡 Faible</span>'
            }
            
            sample_contradictions = [
                {
                    'Type': '⏰ Temporelle',
                    'Document 1': 'PV_audition_temoin1.pdf',
                    'Extrait 1': 'L\'accident s\'est produit le 15 mars 2024 à 14h30',
                    'Document 2': 'PV_audition_temoin2.pdf',
                    'Extrait 2': 'J\'ai assisté à l\'accident le 15 mars 2024 vers 15h15',
                    'Analyse': 'Divergence de 45 minutes sur l\'heure de l\'accident',
                    'Confiance': 95,
                    'Criticité': 'high',
                    'Impact': 'Peut affecter la chronologie des événements'
                },
                {
                    'Type': '📋 Factuelle',
                    'Document 1': 'PV_audition_temoin1.pdf',
                    'Extrait 1': 'Le véhicule était stationné sur le parking nord',
                    'Document 2': 'Expertise_technique.pdf',
                    'Extrait 2': 'Les traces montrent que le véhicule était garé au parking sud',
                    'Analyse': 'Localisation contradictoire du véhicule',
                    'Confiance': 88,
                    'Criticité': 'medium',
                    'Impact': 'Nécessite clarification pour établir les faits'
                },
                {
                    'Type': '🔢 Numérique',
                    'Document 1': 'Expertise_medicale.pdf',
                    'Extrait 1': 'Le préjudice corporel est évalué à 15,000 euros',
                    'Document 2': 'Rapport_expert_comptable.pdf',
                    'Extrait 2': 'Total des préjudices corporels: 18,500 euros',
                    'Analyse': 'Écart de 3,500€ sur l\'évaluation du préjudice',
                    'Confiance': 92,
                    'Criticité': 'high',
                    'Impact': 'Impact direct sur les demandes d\'indemnisation'
                }
            ]
            
            # Création du dataframe
            for contradiction in sample_contradictions:
                contradictions_data.append({
                    'Type': contradiction['Type'],
                    'Documents': f"{contradiction['Document 1']} ↔ {contradiction['Document 2']}",
                    'Description': contradiction['Analyse'],
                    'Confiance': contradiction['Confiance'],
                    'Criticité': criticality_levels[contradiction['Criticité']],
                    'Impact': contradiction['Impact']
                })
            
            df_contradictions = pd.DataFrame(contradictions_data)
            
            # Affichage avec colonnes configurées
            st.dataframe(
                df_contradictions,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Confiance": st.column_config.ProgressColumn(
                        "Confiance",
                        help="Score de confiance de la détection",
                        min_value=0,
                        max_value=100,
                    ),
                    "Criticité": st.column_config.Column(
                        "Criticité",
                        help="Niveau d'importance de la contradiction"
                    )
                }
            )
            
            # Détails expandables pour chaque contradiction
            st.markdown("### 🔍 Analyse détaillée")
            
            for i, contradiction in enumerate(sample_contradictions):
                with st.expander(f"{contradiction['Type']} - {contradiction['Analyse']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Document 1:** {contradiction['Document 1']}")
                        st.info(f"« {contradiction['Extrait 1']} »")
                    
                    with col2:
                        st.markdown(f"**Document 2:** {contradiction['Document 2']}")
                        st.info(f"« {contradiction['Extrait 2']} »")
                    
                    st.markdown(f"**Analyse IA:** {contradiction['Analyse']}")
                    st.markdown(f"**Impact potentiel:** {contradiction['Impact']}")
                    
                    # Actions possibles
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.button("📝 Annoter", key=f"annotate_{i}")
                    with col2:
                        st.button("🔍 Voir contexte", key=f"context_{i}")
                    with col3:
                        st.button("✅ Résolu", key=f"resolve_{i}")
                    with col4:
                        st.button("🚫 Ignorer", key=f"ignore_{i}")
            
            # Visualisations
            st.markdown("### 📈 Visualisations")
            
            tab_viz1, tab_viz2, tab_viz3 = st.tabs(["Distribution", "Timeline", "Réseau"])
            
            with tab_viz1:
                st.markdown("#### Distribution des contradictions par type")
                # Ici, ajouter un graphique en barres ou camembert
                st.info("Graphique de distribution des types de contradictions")
            
            with tab_viz2:
                st.markdown("#### Timeline des contradictions")
                st.info("Visualisation chronologique des contradictions détectées")
            
            with tab_viz3:
                st.markdown("#### Réseau de contradictions")
                st.info("Graphe montrant les relations entre documents contradictoires")
            
            # Export et actions
            st.markdown("### 💾 Export et actions")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.download_button(
                    "📄 Rapport PDF",
                    data=b"Rapport PDF",  # Remplacer par la génération réelle
                    file_name=f"rapport_contradictions_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col2:
                # Génération du CSV
                csv = df_contradictions.to_csv(index=False)
                st.download_button(
                    "📊 Export Excel",
                    data=csv,
                    file_name=f"contradictions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col3:
                if st.button("📧 Envoyer par email", use_container_width=True):
                    st.success("Rapport envoyé !")
            
            with col4:
                if st.button("🔄 Nouvelle analyse", use_container_width=True):
                    st.session_state.analysis_complete = False
                    st.rerun()
            
            # Recommandations
            st.markdown("### 🎯 Recommandations")
            
            recommendations = [
                {
                    'priority': 'high',
                    'title': 'Clarifier les contradictions temporelles',
                    'description': 'Interroger à nouveau les témoins 1 et 2 sur l\'heure exacte de l\'accident',
                    'action': 'Planifier des auditions complémentaires'
                },
                {
                    'priority': 'high',
                    'title': 'Harmoniser les évaluations de préjudice',
                    'description': 'Les écarts entre expertises nécessitent une contre-expertise',
                    'action': 'Demander une expertise contradictoire'
                },
                {
                    'priority': 'medium',
                    'title': 'Vérifier les localisations',
                    'description': 'Confirmer l\'emplacement exact du véhicule avec des preuves matérielles',
                    'action': 'Obtenir les enregistrements de surveillance'
                }
            ]
            
            for rec in recommendations:
                priority_color = 'high' if rec['priority'] == 'high' else 'medium'
                st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 8px; border-left: 4px solid {'#1e3a8a' if priority_color == 'high' else '#3b82f6'};">
                    <h4 style="margin: 0; color: #1e3a8a;">{rec['title']}</h4>
                    <p style="margin: 0.5rem 0; color: #64748b;">{rec['description']}</p>
                    <p style="margin: 0; font-weight: 500; color: #3b82f6;">→ {rec['action']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Message si aucune analyse n'a été effectuée
            st.info("👆 Lancez d'abord une analyse dans l'onglet 'Analyse' pour voir les résultats")
            
            # Affichage des statistiques globales
            if st.session_state.analysis_stats['analyses_count'] > 0:
                st.markdown("### 📊 Statistiques globales")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Analyses effectuées", st.session_state.analysis_stats['analyses_count'])
                with col2:
                    st.metric("Documents traités", st.session_state.analysis_stats['documents_analyzed'])
                with col3:
                    st.metric("Contradictions trouvées", st.session_state.analysis_stats['contradictions_found'])

# Point d'entrée du module
if __name__ == "__main__":
    run()
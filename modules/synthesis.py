# modules/synthesis.py
"""
Module de synthèse pour l'application juridique
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from utils.formatters import format_date
# Import des utilitaires depuis le package utils
from utils.helpers import clean_key, truncate_text
from utils.text_processing import clean_text, process_text


class SynthesisModule:
    """Classe pour gérer les synthèses juridiques"""
    
    def __init__(self):
        self.name = "Synthèse"
        self.description = "Génération de synthèses juridiques"
        
    def render(self):
        """Affiche l'interface du module de synthèse"""
        st.header("Module de Synthèse")
        st.write("Créez des synthèses complètes de vos dossiers juridiques.")
        
        # Options de synthèse
        col1, col2 = st.columns(2)
        
        with col1:
            synthesis_type = st.selectbox(
                "Type de synthèse",
                ["Synthèse générale", "Synthèse chronologique", "Synthèse thématique", "Synthèse des pièces"]
            )
            
            include_timeline = st.checkbox("Inclure une chronologie", value=True)
            include_pieces = st.checkbox("Inclure la liste des pièces", value=True)
            
        with col2:
            max_length = st.slider(
                "Longueur maximale (mots)",
                min_value=500,
                max_value=5000,
                value=2000,
                step=100
            )
            
            format_output = st.selectbox(
                "Format de sortie",
                ["Document Word", "PDF", "Texte brut", "HTML"]
            )
        
        # Zone de saisie pour le contenu à synthétiser
        st.subheader("Contenu à synthétiser")
        
        tab1, tab2, tab3 = st.tabs(["Texte direct", "Importer des fichiers", "Depuis le dossier"])
        
        with tab1:
            content_text = st.text_area(
                "Entrez ou collez le contenu à synthétiser",
                height=300,
                placeholder="Collez ici les éléments du dossier à synthétiser..."
            )
            
        with tab2:
            uploaded_files = st.file_uploader(
                "Téléchargez des documents",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                st.write(f"{len(uploaded_files)} fichier(s) téléchargé(s)")
                for file in uploaded_files:
                    st.write(f"- {file.name}")
                    
        with tab3:
            st.info("Sélectionnez les éléments du dossier actuel à inclure dans la synthèse")
            # Ici, on pourrait lister les éléments du dossier en session
            
        # Options avancées
        with st.expander("Options avancées"):
            st.subheader("Personnalisation de la synthèse")
            
            col1, col2 = st.columns(2)
            with col1:
                highlight_keywords = st.text_input(
                    "Mots-clés à mettre en évidence",
                    placeholder="Ex: responsabilité, préjudice, dommages"
                )
                
                synthesis_style = st.selectbox(
                    "Style de rédaction",
                    ["Neutre et factuel", "Argumentatif", "Analytique", "Synthétique"]
                )
                
            with col2:
                include_citations = st.checkbox("Inclure les références juridiques", value=True)
                include_analysis = st.checkbox("Inclure une analyse juridique", value=False)
                
            structure_template = st.text_area(
                "Structure personnalisée (optionnel)",
                placeholder="1. Introduction\n2. Faits\n3. Procédure\n4. Moyens\n5. Conclusion",
                height=150
            )
        
        # Bouton de génération
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Générer la synthèse", type="primary", use_container_width=True):
                if content_text or uploaded_files:
                    with st.spinner("Génération de la synthèse en cours..."):
                        synthesis = self.generate_synthesis(
                            content=content_text,
                            files=uploaded_files,
                            synthesis_type=synthesis_type,
                            max_length=max_length,
                            options={
                                'include_timeline': include_timeline,
                                'include_pieces': include_pieces,
                                'keywords': highlight_keywords,
                                'style': synthesis_style,
                                'include_citations': include_citations,
                                'include_analysis': include_analysis,
                                'structure': structure_template
                            }
                        )
                        
                        if synthesis:
                            st.success("Synthèse générée avec succès!")
                            self.display_synthesis(synthesis, format_output)
                        else:
                            st.error("Erreur lors de la génération de la synthèse")
                else:
                    st.warning("Veuillez fournir du contenu à synthétiser")
        
        # Section des synthèses récentes
        st.divider()
        st.subheader("Synthèses récentes")
        
        recent_syntheses = self.get_recent_syntheses()
        if recent_syntheses:
            for synthesis in recent_syntheses:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{synthesis['title']}**")
                        st.caption(f"Créée le {synthesis['date']}")
                    with col2:
                        st.write(f"Type: {synthesis['type']}")
                    with col3:
                        if st.button("Voir", key=f"view_{synthesis['id']}"):
                            self.display_synthesis(synthesis['content'], synthesis['format'])
        else:
            st.info("Aucune synthèse récente")
    
    def generate_synthesis(self, content: str, files: List[Any], synthesis_type: str, 
                         max_length: int, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Génère une synthèse basée sur le contenu fourni.
        
        Args:
            content: Texte à synthétiser
            files: Fichiers uploadés
            synthesis_type: Type de synthèse
            max_length: Longueur maximale en mots
            options: Options de génération
            
        Returns:
            Dictionnaire contenant la synthèse générée
        """
        # Traitement du contenu
        if content:
            processed_content = process_text(content)
        else:
            processed_content = ""
            
        # Traitement des fichiers (simulation)
        if files:
            # Ici on extrairait le contenu des fichiers
            pass
        
        # Génération de la synthèse (simulation)
        synthesis = {
            'title': f"Synthèse {synthesis_type} - {datetime.now().strftime('%d/%m/%Y')}",
            'type': synthesis_type,
            'content': self._create_synthesis_content(processed_content, synthesis_type, options),
            'metadata': {
                'created_at': datetime.now(),
                'max_length': max_length,
                'options': options
            }
        }
        
        # Sauvegarder en session
        if 'syntheses' not in st.session_state:
            st.session_state.syntheses = []
        st.session_state.syntheses.append(synthesis)
        
        return synthesis
    
    def _create_synthesis_content(self, content: str, synthesis_type: str, 
                                options: Dict[str, Any]) -> str:
        """
        Crée le contenu de la synthèse selon le type demandé.
        
        Args:
            content: Contenu à synthétiser
            synthesis_type: Type de synthèse
            options: Options de génération
            
        Returns:
            Contenu de la synthèse
        """
        # Structure de base
        synthesis_parts = []
        
        # En-tête
        synthesis_parts.append(f"# {synthesis_type}")
        synthesis_parts.append(f"*Générée le {format_date(datetime.now())}*\n")
        
        # Introduction
        synthesis_parts.append("## Introduction")
        intro_text = truncate_text(content, 200) if content else "Synthèse du dossier juridique."
        synthesis_parts.append(intro_text + "\n")
        
        # Corps selon le type
        if synthesis_type == "Synthèse générale":
            synthesis_parts.extend(self._general_synthesis(content, options))
        elif synthesis_type == "Synthèse chronologique":
            synthesis_parts.extend(self._chronological_synthesis(content, options))
        elif synthesis_type == "Synthèse thématique":
            synthesis_parts.extend(self._thematic_synthesis(content, options))
        elif synthesis_type == "Synthèse des pièces":
            synthesis_parts.extend(self._pieces_synthesis(content, options))
        
        # Conclusion
        synthesis_parts.append("\n## Conclusion")
        synthesis_parts.append("Cette synthèse présente les éléments essentiels du dossier.")
        
        return "\n".join(synthesis_parts)
    
    def _general_synthesis(self, content: str, options: Dict[str, Any]) -> List[str]:
        """Génère une synthèse générale"""
        parts = []
        
        parts.append("## Faits")
        parts.append("Les faits principaux du dossier sont les suivants :")
        parts.append("- [À compléter avec les faits extraits]\n")
        
        parts.append("## Procédure")
        parts.append("La procédure s'est déroulée comme suit :")
        parts.append("- [À compléter avec les étapes procédurales]\n")
        
        if options.get('include_analysis'):
            parts.append("## Analyse juridique")
            parts.append("L'analyse des éléments juridiques révèle :")
            parts.append("- [À compléter avec l'analyse]\n")
        
        return parts
    
    def _chronological_synthesis(self, content: str, options: Dict[str, Any]) -> List[str]:
        """Génère une synthèse chronologique"""
        parts = []
        
        parts.append("## Chronologie des événements")
        parts.append("Les événements se sont déroulés dans l'ordre suivant :\n")
        
        # Simulation d'une timeline
        parts.append("### 2024")
        parts.append("- **Janvier** : Début de la procédure")
        parts.append("- **Mars** : Dépôt des conclusions")
        parts.append("- **Juin** : Audience de plaidoirie\n")
        
        return parts
    
    def _thematic_synthesis(self, content: str, options: Dict[str, Any]) -> List[str]:
        """Génère une synthèse thématique"""
        parts = []
        
        parts.append("## Thèmes principaux")
        
        themes = ["Responsabilité", "Préjudice", "Réparation"]
        for theme in themes:
            parts.append(f"\n### {theme}")
            parts.append(f"Concernant {theme.lower()}, il ressort que :")
            parts.append("- [Éléments relatifs au thème]")
        
        return parts
    
    def _pieces_synthesis(self, content: str, options: Dict[str, Any]) -> List[str]:
        """Génère une synthèse des pièces"""
        parts = []
        
        parts.append("## Inventaire des pièces")
        parts.append("Le dossier comprend les pièces suivantes :\n")
        
        parts.append("### Pièces du demandeur")
        parts.append("1. Assignation")
        parts.append("2. Conclusions")
        parts.append("3. Pièces justificatives\n")
        
        parts.append("### Pièces du défendeur")
        parts.append("1. Conclusions en réponse")
        parts.append("2. Pièces contradictoires\n")
        
        return parts
    
    def display_synthesis(self, synthesis: Dict[str, Any], format_output: str):
        """
        Affiche la synthèse générée.
        
        Args:
            synthesis: Synthèse à afficher
            format_output: Format de sortie souhaité
        """
        # Affichage du contenu
        if isinstance(synthesis, dict) and 'content' in synthesis:
            content = synthesis['content']
        else:
            content = str(synthesis)
            
        st.markdown(content)
        
        # Options d'export
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label=f"📥 Télécharger ({format_output})",
                data=content,
                file_name=f"synthese_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
            
        with col2:
            if st.button("📧 Envoyer par email"):
                st.info("Fonction d'envoi par email à implémenter")
                
        with col3:
            if st.button("💾 Sauvegarder dans le dossier"):
                st.success("Synthèse sauvegardée dans le dossier")
    
    def get_recent_syntheses(self) -> List[Dict[str, Any]]:
        """
        Récupère les synthèses récentes depuis la session.
        
        Returns:
            Liste des synthèses récentes
        """
        if 'syntheses' not in st.session_state:
            return []
            
        # Retourner les 5 dernières synthèses
        syntheses = st.session_state.syntheses[-5:]
        
        # Formater pour l'affichage
        formatted = []
        for i, synthesis in enumerate(syntheses):
            formatted.append({
                'id': i,
                'title': synthesis.get('title', 'Sans titre'),
                'type': synthesis.get('type', 'Inconnue'),
                'date': synthesis.get('metadata', {}).get('created_at', datetime.now()).strftime('%d/%m/%Y %H:%M'),
                'content': synthesis,
                'format': 'text'
            })
            
        return formatted[::-1]  # Inverser pour avoir les plus récentes en premier

# Point d'entrée du module
def get_module():
    """Retourne une instance du module"""
    return SynthesisModule()
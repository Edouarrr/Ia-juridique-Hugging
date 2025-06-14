# modules/redaction_unified.py
"""Module unifié de rédaction de documents juridiques avec IA"""

import asyncio
import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from config.app_config import (DOCUMENT_TEMPLATES, LEGAL_PHRASES,
                               REDACTION_STYLES, DocumentType, LLMProvider)
from managers.dynamic_generators import generate_dynamic_templates
from managers.multi_llm_manager import MultiLLMManager
from managers.style_analyzer import StyleAnalyzer
from modules.dataclasses import (JurisprudenceCase, LetterheadTemplate,
                                 RedactionResult, StylePattern)
from utils.helpers import (clean_key, create_formatted_docx,
                           create_letterhead_from_template,
                           extract_legal_references, format_legal_date)

try:
    from docx import Document as DocxDocument
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class UnifiedRedactionModule:
    """Module unifié pour toutes les opérations de rédaction"""
    
    def __init__(self):
        self.llm_manager = MultiLLMManager()
        self.style_analyzer = StyleAnalyzer()
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialise les variables de session nécessaires"""
        if 'style_analyzer' not in st.session_state:
            st.session_state.style_analyzer = self.style_analyzer
        
        if 'learned_styles' not in st.session_state:
            st.session_state.learned_styles = {}
        
        if 'custom_templates' not in st.session_state:
            st.session_state.custom_templates = {}
        
        if 'dynamic_templates' not in st.session_state:
            st.session_state.dynamic_templates = {}
    
    def process_redaction_request(self, query: str, analysis: dict):
        """Point d'entrée principal pour traiter une demande de rédaction"""
        
        # Déterminer le type de document
        doc_type = analysis['details'].get('document_type', 'general')
        
        # Router vers la méthode appropriée
        if doc_type == 'courrier':
            self.show_courrier_interface(analysis)
        elif doc_type in ['plainte', 'constitution_pc', 'conclusions']:
            self.show_juridical_document_interface(doc_type, analysis)
        else:
            self.show_general_redaction_interface(doc_type, analysis)
    
    def show_juridical_document_interface(self, doc_type: str, analysis: dict):
        """Interface pour documents juridiques complexes"""
        
        st.markdown(f"### ⚖️ Rédaction : {self.get_document_type_name(doc_type)}")
        
        # Configuration en colonnes
        config = self._display_configuration_interface(doc_type, analysis)
        
        # Bouton de génération principal
        if st.button("🚀 Générer le document", key="generate_document_button", type="primary"):
            self._generate_document(doc_type, config, analysis)
    
    def _display_configuration_interface(self, doc_type: str, analysis: dict) -> dict:
        """Affiche l'interface de configuration unifiée"""
        
        config = {}
        
        # Section 1: Style et format
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Style de rédaction
                config['style'] = st.selectbox(
                    "📝 Style de rédaction",
                    list(REDACTION_STYLES.keys()),
                    format_func=lambda x: f"{REDACTION_STYLES[x]['name']} - {REDACTION_STYLES[x]['description']}",
                    index=0,
                    key="redaction_style_select"
                )
                
                # Styles appris disponibles
                learned_styles = list(st.session_state.get('learned_styles', {}).keys())
                if learned_styles:
                    config['learned_style'] = st.selectbox(
                        "🎨 Appliquer un style appris",
                        ["Aucun"] + learned_styles,
                        key="learned_style_select"
                    )
            
            with col2:
                # Longueur cible
                config['length'] = st.select_slider(
                    "📏 Longueur",
                    options=["Concis", "Standard", "Détaillé", "Très détaillé", "Exhaustif"],
                    value="Très détaillé",
                    key="redaction_length_select"
                )
                
                # Ton
                config['tone'] = st.select_slider(
                    "🎯 Ton",
                    options=["Très formel", "Formel", "Équilibré", "Direct", "Combatif"],
                    value="Formel",
                    key="redaction_tone_select"
                )
            
            with col3:
                # IA et options avancées
                available_providers = self.llm_manager.get_available_providers()
                
                if not available_providers:
                    st.error("❌ Aucune IA configurée. Veuillez ajouter des clés API.")
                    return config
                
                config['providers'] = st.multiselect(
                    "🤖 IA à utiliser",
                    available_providers,
                    default=available_providers[:2] if len(available_providers) > 1 else available_providers,
                    key="redaction_providers_select"
                )
                
                # Options avancées
                with st.expander("⚙️ Options avancées"):
                    config['use_jurisprudence'] = st.checkbox(
                        "⚖️ Inclure jurisprudence",
                        value=True,
                        key="use_jurisprudence_check"
                    )
                    
                    if len(config['providers']) > 1:
                        config['fusion_mode'] = st.selectbox(
                            "🔄 Mode de fusion",
                            ["intelligent", "best_of", "synthesis"],
                            format_func=lambda x: {
                                "intelligent": "🎯 Fusion intelligente",
                                "best_of": "⭐ Meilleure version",
                                "synthesis": "🔗 Synthèse enrichie"
                            }.get(x, x),
                            key="fusion_mode_select"
                        )
        
        # Section 2: Informations du dossier
        config.update(self._get_case_information(analysis))
        
        # Section 3: Templates et modèles
        config['template'] = self._select_template(doc_type)
        
        # Section 4: Documents de référence
        config['reference_docs'] = self._select_reference_documents()
        
        return config
    
    def _get_case_information(self, analysis: dict) -> dict:
        """Collecte les informations du dossier"""
        
        info = {}
        
        with st.expander("📋 Informations du dossier", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                info['client'] = st.text_input(
                    "👤 Client/Demandeur",
                    value=analysis.get('client', ''),
                    key="client_input"
                )
                
                info['adversaire'] = st.text_input(
                    "⚔️ Partie adverse",
                    value=analysis.get('adversaire', ''),
                    key="adversaire_input"
                )
                
                info['infraction'] = st.text_input(
                    "📑 Infraction/Objet",
                    value=analysis.get('infraction', ''),
                    key="infraction_input"
                )
            
            with col2:
                info['juridiction'] = st.text_input(
                    "🏛️ Juridiction",
                    value=analysis.get('juridiction', 'Tribunal Judiciaire'),
                    key="juridiction_input"
                )
                
                info['reference'] = st.text_input(
                    "📎 Référence",
                    value=analysis.get('reference', ''),
                    key="reference_input"
                )
                
                info['date'] = st.date_input(
                    "📅 Date",
                    value=datetime.now(),
                    key="date_input"
                )
            
            # Contexte et faits
            info['contexte'] = st.text_area(
                "📝 Contexte et faits principaux",
                value=analysis.get('subject_matter', ''),
                height=150,
                key="contexte_textarea"
            )
            
            # Arguments spécifiques
            info['arguments'] = st.text_area(
                "💡 Arguments principaux à développer",
                placeholder="- Premier argument\n- Deuxième argument\n- Troisième argument",
                height=100,
                key="arguments_textarea"
            )
        
        return info
    
    def _select_template(self, doc_type: str) -> Optional[str]:
        """Sélection du template"""
        
        template = None
        
        # Templates disponibles
        available_templates = self.get_templates_for_type(doc_type)
        all_templates = ["Aucun"]
        
        # Templates prédéfinis
        if available_templates:
            all_templates.extend(list(available_templates.keys()))
        
        # Templates dynamiques
        dynamic_key = f"templates_{clean_key(doc_type)}"
        if dynamic_key in st.session_state.dynamic_templates:
            all_templates.extend(st.session_state.dynamic_templates[dynamic_key].keys())
        
        if len(all_templates) > 1:
            template = st.selectbox(
                "📋 Template à utiliser",
                all_templates,
                key="redaction_template_select"
            )
            
            # Option pour générer de nouveaux templates
            if st.button("🎯 Générer de nouveaux modèles", key="generate_templates_btn"):
                self._generate_dynamic_templates(doc_type)
        
        return template if template != "Aucun" else None
    
    def _select_reference_documents(self) -> List[str]:
        """Sélection des documents de référence"""
        
        reference_docs = []
        
        if st.session_state.get('azure_documents'):
            with st.expander("📄 Documents de référence (optionnel)"):
                st.info("Sélectionnez des documents similaires pour guider le style")
                
                for doc_id, doc in list(st.session_state.azure_documents.items())[:10]:
                    if st.checkbox(
                        doc.title[:80],
                        key=f"ref_doc_{doc_id}"
                    ):
                        reference_docs.append(doc_id)
        
        return reference_docs
    
    def _generate_document(self, doc_type: str, config: dict, analysis: dict):
        """Génère le document avec la configuration spécifiée"""
        
        if not config.get('providers'):
            st.error("❌ Aucune IA sélectionnée")
            return
        
        with st.spinner("🤖 Génération en cours... (peut prendre 1-2 minutes)"):
            # Construire les prompts
            prompt = self._build_generation_prompt(doc_type, config, analysis)
            system_prompt = self._build_system_prompt(doc_type, config)
            
            # Rechercher la jurisprudence si demandé
            jurisprudence_refs = []
            if config.get('use_jurisprudence'):
                jurisprudence_refs = self._search_relevant_jurisprudence(doc_type, config, analysis)
                if jurisprudence_refs:
                    prompt += "\n\nJURISPRUDENCE PERTINENTE À CITER:\n"
                    for juris in jurisprudence_refs[:5]:
                        prompt += f"- {juris.get_citation()}: {juris.summary}\n"
            
            # Déterminer les tokens selon la longueur
            max_tokens = self._get_max_tokens(config.get('length', 'Très détaillé'))
            
            # Générer le document
            result = self._execute_generation(
                config['providers'],
                prompt,
                system_prompt,
                max_tokens,
                config.get('fusion_mode'),
                doc_type,
                jurisprudence_refs
            )
            
            if result:
                st.session_state.redaction_result = result
                self._display_redaction_results(result)
            else:
                st.error("❌ Échec de la génération du document")
    
    def _build_generation_prompt(self, doc_type: str, config: dict, analysis: dict) -> str:
        """Construit le prompt de génération unifié"""
        
        # Base du prompt
        prompt = f"Rédige {self.get_document_type_name(doc_type)} complet et professionnel.\n\n"
        
        # Informations du dossier
        prompt += "INFORMATIONS DU DOSSIER:\n"
        for key, value in config.items():
            if key in ['client', 'adversaire', 'juridiction', 'reference', 'infraction']:
                if value:
                    prompt += f"- {key.capitalize()}: {value}\n"
        
        # Contexte et arguments
        if config.get('contexte'):
            prompt += f"\nCONTEXTE ET FAITS:\n{config['contexte']}\n"
        
        if config.get('arguments'):
            prompt += f"\nARGUMENTS À DÉVELOPPER:\n{config['arguments']}\n"
        
        # Style et ton
        style_info = REDACTION_STYLES.get(config.get('style', 'formel'))
        prompt += f"\nSTYLE DE RÉDACTION:\n"
        prompt += f"- Ton: {config.get('tone', style_info['tone'])}\n"
        prompt += f"- Vocabulaire: {style_info['vocabulary']}\n"
        
        # Style appris
        if config.get('learned_style') and config['learned_style'] != "Aucun":
            learned = st.session_state.learned_styles.get(config['learned_style'])
            if learned:
                prompt += f"\nAPPLIQUER LE STYLE APPRIS '{config['learned_style']}':\n"
                prompt += f"- Structure type: {learned['pattern']['structure']}\n"
                prompt += f"- Formules caractéristiques: {learned['pattern']['formules'][:3]}\n"
        
        # Template
        if config.get('template'):
            template_content = self._get_template_content(config['template'], doc_type)
            if template_content:
                prompt += f"\nSTRUCTURE À SUIVRE:\n{template_content}\n"
        
        # Exigences spécifiques par type
        prompt += self._get_type_specific_requirements(doc_type)
        
        # Longueur
        prompt += f"\nLONGUEUR: {self._get_length_instruction(config.get('length'))}\n"
        
        prompt += "\nLe document doit être immédiatement utilisable, sans placeholder, avec un contenu juridique solide."
        
        return prompt
    
    def _build_system_prompt(self, doc_type: str, config: dict) -> str:
        """Construit le prompt système unifié"""
        
        base = "Tu es un avocat expert en droit pénal des affaires français avec 20 ans d'expérience."
        
        # Spécialisation par type
        specializations = {
            'conclusions': "Tu excelles dans la rédaction de conclusions percutantes.",
            'plainte': "Tu maîtrises parfaitement la rédaction de plaintes pénales.",
            'constitution_pc': "Tu es spécialisé dans les constitutions de partie civile.",
            'courrier': "Tu rédiges des courriers professionnels clairs et efficaces.",
            'mise_en_demeure': "Tu rédiges des mises en demeure fermes mais courtoises.",
            'assignation': "Tu maîtrises la rédaction d'assignations conformes au CPC."
        }
        
        base += f" {specializations.get(doc_type, 'Tu maîtrises tous les types de documents juridiques.')}"
        
        # Style
        style_info = REDACTION_STYLES.get(config.get('style', 'formel'))
        base += f" Tu adoptes un style {style_info['name'].lower()} avec un ton {config.get('tone', style_info['tone']).lower()}."
        
        base += " Tu utilises les formules juridiques appropriées et cites la jurisprudence pertinente."
        
        return base
    
    def _execute_generation(self, providers: List[str], prompt: str, system_prompt: str, 
                          max_tokens: int, fusion_mode: Optional[str], doc_type: str,
                          jurisprudence_refs: List[JurisprudenceCase]) -> Optional[RedactionResult]:
        """Exécute la génération avec les providers sélectionnés"""
        
        if len(providers) == 1:
            # Génération simple
            provider = LLMProvider[providers[0]] if providers[0] in [p.name for p in LLMProvider] else providers[0]
            
            response = self.llm_manager.query_single_llm(
                provider,
                prompt,
                system_prompt,
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            if response['success']:
                return RedactionResult(
                    type=doc_type,
                    document=response['response'],
                    provider=providers[0],
                    style=st.session_state.get('redaction_style_select', 'formel'),
                    jurisprudence_used=bool(jurisprudence_refs),
                    jurisprudence_references=jurisprudence_refs,
                    responses=[response]
                )
        else:
            # Génération multiple avec fusion
            providers_enum = [LLMProvider[p] if p in [p.name for p in LLMProvider] else p for p in providers]
            
            responses = self.llm_manager.query_multiple_llms(
                providers_enum,
                prompt,
                system_prompt,
                temperature=0.7,
                max_tokens=max_tokens,
                parallel=True
            )
            
            # Fusionner selon le mode
            final_document = self._apply_fusion_strategy(responses, fusion_mode, doc_type)
            
            if final_document:
                return RedactionResult(
                    type=doc_type,
                    document=final_document,
                    provider="Multi-IA",
                    style=st.session_state.get('redaction_style_select', 'formel'),
                    jurisprudence_used=bool(jurisprudence_refs),
                    jurisprudence_references=jurisprudence_refs,
                    responses=responses
                )
        
        return None
    
    def _apply_fusion_strategy(self, responses: List[Dict[str, Any]], 
                              fusion_mode: str, doc_type: str) -> Optional[str]:
        """Applique la stratégie de fusion sélectionnée"""
        
        if fusion_mode == 'intelligent':
            return self.intelligent_document_fusion(responses, doc_type)
        elif fusion_mode == 'best_of':
            return self.select_best_document(responses, doc_type)
        else:  # synthesis
            return self.synthesize_documents(responses, doc_type)
    
    def _display_redaction_results(self, result: RedactionResult):
        """Affiche les résultats de la rédaction"""
        
        st.success("✅ Document généré avec succès!")
        
        # Affichage principal
        st.markdown("### 📄 Document généré")
        
        # Zone d'édition
        edited_content = st.text_area(
            "Vous pouvez modifier le document",
            value=result.document,
            height=600,
            key="edited_document"
        )
        
        # Métriques et statistiques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Mots", f"{len(edited_content.split()):,}")
        
        with col2:
            st.metric("📄 Pages estimées", len(edited_content.split()) // 250)
        
        with col3:
            st.metric("🤖 IA utilisée", result.provider)
        
        with col4:
            if result.jurisprudence_used:
                st.metric("⚖️ Jurisprudences", len(result.jurisprudence_references))
        
        # Options d'export
        st.markdown("### 💾 Export du document")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export texte
            st.download_button(
                "📄 Télécharger (.txt)",
                edited_content,
                f"{clean_key(result.type)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                key="download_txt"
            )
        
        with col2:
            if DOCX_AVAILABLE:
                # Export Word formaté
                docx_data = create_formatted_docx(edited_content, result.type)
                st.download_button(
                    "📘 Télécharger (.docx)",
                    docx_data,
                    f"{clean_key(result.type)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_docx"
                )
        
        with col3:
            # Copier dans le presse-papier
            if st.button("📋 Copier", key="copy_button"):
                st.write("Document copié! (utilisez Ctrl+C)")
                st.code(edited_content, language=None)
        
        # Analyse détaillée (optionnel)
        with st.expander("📊 Analyse détaillée", expanded=False):
            self._display_document_analysis(result, edited_content)
    
    def _display_document_analysis(self, result: RedactionResult, content: str):
        """Affiche une analyse détaillée du document"""
        
        # Structure du document
        structure = self.analyze_document_structure(content)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📑 Structure")
            st.write(f"- **Sections:** {len(structure['sections'])}")
            for section_name in list(structure['sections'].keys())[:5]:
                st.write(f"  - {section_name}")
        
        with col2:
            st.markdown("#### 📊 Éléments juridiques")
            legal_refs = extract_legal_references(content)
            st.write(f"- **Références légales:** {len(legal_refs)}")
            st.write(f"- **Jurisprudences citées:** {len(result.jurisprudence_references)}")
        
        # Si génération multiple, afficher la comparaison
        if len(result.responses) > 1:
            st.markdown("#### 🔄 Comparaison des versions")
            for i, response in enumerate(result.responses):
                if response.get('success'):
                    st.write(f"**{response['provider']}:** {len(response['response'].split())} mots")
    
    # === MÉTHODES SPÉCIALISÉES POUR COURRIER ===
    
    def show_courrier_interface(self, analysis: dict):
        """Interface spécialisée pour la rédaction de courriers"""
        
        # Vérifier le papier en-tête
        if 'letterhead_template' not in st.session_state:
            self._show_letterhead_setup()
            return
        
        st.markdown("### ✉️ Rédaction de courrier")
        
        # Configuration du courrier
        config = self._get_courrier_configuration(analysis)
        
        # Génération
        if st.button("🚀 Générer le courrier", key="generate_courrier_button", type="primary"):
            self._generate_courrier(config)
    
    def _show_letterhead_setup(self):
        """Configuration rapide du papier en-tête"""
        
        st.warning("⚠️ Aucun papier en-tête configuré.")
        
        with st.form("letterhead_setup"):
            st.markdown("### Configuration du papier en-tête")
            
            col1, col2 = st.columns(2)
            
            with col1:
                cabinet = st.text_input("Nom du cabinet")
                avocat = st.text_input("Nom de l'avocat")
                barreau = st.text_input("Barreau")
            
            with col2:
                adresse = st.text_area("Adresse")
                telephone = st.text_input("Téléphone")
                email = st.text_input("Email")
            
            if st.form_submit_button("Créer le papier en-tête"):
                header = f"{cabinet}\n{avocat}\nAvocat au {barreau}\n{adresse}\nTél : {telephone}\nEmail : {email}"
                footer = f"{cabinet} - {adresse} - Tél : {telephone}"
                
                st.session_state.letterhead_template = LetterheadTemplate(
                    name="Principal",
                    header_content=header,
                    footer_content=footer
                )
                st.rerun()
    
    def _get_courrier_configuration(self, analysis: dict) -> dict:
        """Collecte la configuration du courrier"""
        
        config = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            config['destinataire'] = st.text_input("Destinataire", key="dest_nom")
            config['qualite'] = st.text_input("Qualité", key="dest_qualite")
            config['adresse'] = st.text_area("Adresse", height=80, key="dest_adresse")
        
        with col2:
            config['objet'] = st.text_input("Objet", key="courrier_objet")
            config['reference'] = st.text_input("Référence", key="courrier_ref")
            config['date'] = st.date_input("Date", datetime.now(), key="courrier_date")
        
        # Type et contenu
        config['type'] = st.selectbox(
            "Type de courrier",
            ["Simple", "Demande", "Transmission", "Mise en demeure", "Notification"],
            key="courrier_type"
        )
        
        config['points'] = st.text_area(
            "Points à développer",
            height=150,
            key="courrier_points"
        )
        
        return config
    
    def _generate_courrier(self, config: dict):
        """Génère un courrier professionnel"""
        
        prompt = self._build_courrier_prompt(config)
        
        with st.spinner("Génération du courrier..."):
            response = self.llm_manager.query_single_llm(
                list(self.llm_manager.clients.keys())[0],
                prompt,
                "Tu es un avocat expert en rédaction de courriers professionnels.",
                temperature=0.7,
                max_tokens=2000
            )
            
            if response['success']:
                self._display_courrier_results(response['response'], config)
    
    def _build_courrier_prompt(self, config: dict) -> str:
        """Construit le prompt pour courrier"""
        
        return f"""Rédige un courrier professionnel avec les éléments suivants:
Type: {config['type']}
Destinataire: {config['destinataire']} ({config['qualite']})
Objet: {config['objet']}
Points à développer: {config['points']}
Le courrier doit inclure:
- Formule d'appel appropriée
- Introduction claire
- Développement structuré des points
- Conclusion adaptée
- Formule de politesse
Ne pas inclure l'en-tête (sera ajouté automatiquement)."""
    
    def _display_courrier_results(self, content: str, config: dict):
        """Affiche les résultats du courrier"""
        
        st.success("✅ Courrier généré!")
        
        # Édition
        edited = st.text_area("Modifier si nécessaire", content, height=400, key="edit_courrier")
        
        # Export avec papier en-tête
        if st.button("💾 Exporter avec papier en-tête"):
            template = st.session_state.letterhead_template
            full_letter = f"{template.header_content}\n\n{config['destinataire']}\n{config['qualite']}\n{config['adresse']}\n\n{config['date'].strftime('%d %B %Y')}\n\nObjet : {config['objet']}\n\n{edited}\n\n{template.footer_content}"
            
            st.download_button(
                "Télécharger",
                full_letter,
                f"courrier_{clean_key(config['objet'])}_{config['date'].strftime('%Y%m%d')}.txt",
                "text/plain"
            )
    
    # === MÉTHODES UTILITAIRES ===
    
    def get_document_type_name(self, doc_type: str) -> str:
        """Retourne le nom complet du type de document"""
        
        type_names = {
            'conclusions': 'Conclusions en défense',
            'plainte': 'Plainte pénale',
            'constitution_pc': 'Constitution de partie civile',
            'mise_en_demeure': 'Mise en demeure',
            'assignation': 'Assignation',
            'requete': 'Requête',
            'memoire': 'Mémoire',
            'courrier': 'Courrier juridique',
            'general': 'Document juridique'
        }
        
        return type_names.get(doc_type, doc_type.title())
    
    def get_templates_for_type(self, doc_type: str) -> Dict[str, Dict[str, Any]]:
        """Retourne les templates disponibles pour un type"""
        
        templates = {}
        
        # Templates prédéfinis
        for key, template in DOCUMENT_TEMPLATES.items():
            if doc_type in key.lower() or template.get('type', '').lower() == doc_type:
                templates[key] = template
        
        # Templates custom
        for key, template in st.session_state.get('custom_templates', {}).items():
            if doc_type in key.lower():
                templates[key] = {'name': key, 'content': template}
        
        return templates
    
    def _get_template_content(self, template_name: str, doc_type: str) -> Optional[str]:
        """Récupère le contenu d'un template"""
        
        # Template prédéfini
        if template_name in DOCUMENT_TEMPLATES:
            return DOCUMENT_TEMPLATES[template_name].get('structure', '')
        
        # Template custom
        if template_name in st.session_state.get('custom_templates', {}):
            return st.session_state.custom_templates[template_name]
        
        # Template dynamique
        dynamic_key = f"templates_{clean_key(doc_type)}"
        if dynamic_key in st.session_state.dynamic_templates:
            if template_name in st.session_state.dynamic_templates[dynamic_key]:
                return st.session_state.dynamic_templates[dynamic_key][template_name]
        
        return None
    
    def _get_type_specific_requirements(self, doc_type: str) -> str:
        """Retourne les exigences spécifiques par type de document"""
        
        requirements = {
            'conclusions': """
Le document doit inclure:
- En-tête complet avec identification des parties
- Faits détaillés et chronologiques
- Discussion juridique approfondie
- Dispositif clair avec demandes précises""",
            
            'plainte': """
Le document doit inclure:
- Destinataire (Procureur de la République)
- Exposé détaillé des faits
- Qualification juridique précise
- Préjudices subis
- Demandes claires""",
            
            'constitution_pc': """
Le document doit inclure:
- Déclaration de constitution de partie civile
- Exposé complet des faits
- Qualification juridique
- Préjudices détaillés et chiffrés
- Demandes d'indemnisation"""
        }
        
        return requirements.get(doc_type, "")
    
    def _get_length_instruction(self, length: str) -> str:
        """Retourne l'instruction de longueur"""
        
        instructions = {
            "Concis": "Document concis mais complet (5-8 pages)",
            "Standard": "Document standard (8-12 pages)",
            "Détaillé": "Document détaillé (12-20 pages)",
            "Très détaillé": "Document très détaillé (20-30 pages)",
            "Exhaustif": "Document exhaustif (30+ pages)"
        }
        
        return instructions.get(length, "Document standard")
    
    def _get_max_tokens(self, length: str) -> int:
        """Retourne le nombre max de tokens selon la longueur"""
        
        tokens = {
            "Concis": 2000,
            "Standard": 3000,
            "Détaillé": 4000,
            "Très détaillé": 6000,
            "Exhaustif": 8000
        }
        
        return tokens.get(length, 4000)
    
    def _search_relevant_jurisprudence(self, doc_type: str, config: dict, 
                                     analysis: dict) -> List[JurisprudenceCase]:
        """Recherche la jurisprudence pertinente"""
        
        # Simulation - dans la vraie app, interroger une base
        jurisprudence = []
        
        keywords = []
        if config.get('infraction'):
            keywords.append(config['infraction'].lower())
        if config.get('contexte'):
            keywords.extend(re.findall(r'\b\w+\b', config['contexte'].lower())[:5])
        
        # Exemples basés sur les mots-clés
        if any('abus' in k for k in keywords):
            jurisprudence.append(
                JurisprudenceCase(
                    id="cass_crim_2019_001",
                    title="Abus de biens sociaux",
                    jurisdiction="Cass. crim.",
                    date=datetime(2019, 3, 27),
                    reference="n° 18-82.855",
                    summary="L'usage personnel caractérise l'ABS même sans préjudice immédiat.",
                    keywords=["abus de biens sociaux", "dirigeant"]
                )
            )
        
        return jurisprudence
    
    def _generate_dynamic_templates(self, doc_type: str):
        """Génère des templates dynamiques pour un type de document"""
        
        with st.spinner("Génération de modèles intelligents..."):
            context = {
                'type': doc_type,
                'style': st.session_state.get('redaction_style_select', 'formel'),
                'jurisdiction': st.session_state.get('juridiction_input', '')
            }
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            templates = loop.run_until_complete(
                generate_dynamic_templates(doc_type, context)
            )
            
            cache_key = f"templates_{clean_key(doc_type)}"
            st.session_state.dynamic_templates[cache_key] = templates
            
            st.success(f"✅ {len(templates)} modèles générés!")
            st.rerun()
    
    # === MÉTHODES DE FUSION (reprises du module original) ===
    
    def intelligent_document_fusion(self, responses: List[Dict[str, Any]], 
                                  doc_type: str) -> str:
        """Fusionne intelligemment plusieurs versions"""
        
        valid_responses = [r for r in responses if r.get('success') and r.get('response')]
        
        if not valid_responses:
            return ""
        
        if len(valid_responses) == 1:
            return valid_responses[0]['response']
        
        # Analyser la structure de chaque document
        document_structures = []
        for resp in valid_responses:
            structure = self.analyze_document_structure(resp['response'])
            document_structures.append({
                'provider': resp['provider'],
                'content': resp['response'],
                'structure': structure
            })
        
        # Fusionner section par section
        merged = self._merge_document_sections(document_structures)
        
        return merged
    
    def analyze_document_structure(self, document: str) -> Dict[str, Any]:
        """Analyse la structure d'un document juridique"""
        
        structure = {
            'header': '',
            'sections': {},
            'conclusion': ''
        }
        
        lines = document.split('\n')
        current_section = None
        current_content = []
        in_header = True
        in_conclusion = False
        
        for line in lines:
            # Détecter les sections
            if re.match(r'^[IVX]+\.|^POUR :|^PLAISE', line):
                if in_header and current_content:
                    structure['header'] = '\n'.join(current_content)
                    current_content = []
                    in_header = False
            
            # Détecter la conclusion
            if re.match(r'^PAR CES MOTIFS|^EN CONSEQUENCE', line):
                if current_section and current_content:
                    structure['sections'][current_section] = '\n'.join(current_content)
                current_content = [line]
                in_conclusion = True
                current_section = None
                continue
            
            # Gérer les sections
            section_match = re.match(r'^([IVX]+\..*?)$', line)
            if section_match and not in_conclusion:
                if current_section and current_content:
                    structure['sections'][current_section] = '\n'.join(current_content)
                current_section = section_match.group(1)
                current_content = []
            else:
                current_content.append(line)
        
        # Finaliser
        if in_conclusion and current_content:
            structure['conclusion'] = '\n'.join(current_content)
        elif current_section and current_content:
            structure['sections'][current_section] = '\n'.join(current_content)
        
        return structure
    
    def _merge_document_sections(self, document_structures: List[Dict]) -> str:
        """Fusionne les sections de plusieurs documents"""
        
        merged = ""
        
        # En-tête - prendre le plus complet
        headers = [doc['structure'].get('header', '') for doc in document_structures]
        best_header = max(headers, key=len) if headers else ""
        merged += best_header + "\n\n"
        
        # Sections - fusionner intelligemment
        all_sections = set()
        for doc in document_structures:
            all_sections.update(doc['structure'].get('sections', {}).keys())
        
        for section_name in sorted(all_sections):
            contents = []
            for doc in document_structures:
                if section_name in doc['structure'].get('sections', {}):
                    contents.append(doc['structure']['sections'][section_name])
            
            if contents:
                merged += f"\n{section_name}\n"
                # Prendre le contenu le plus développé
                best_content = max(contents, key=len)
                merged += best_content + "\n"
        
        # Conclusion - prendre la plus percutante
        conclusions = [doc['structure'].get('conclusion', '') for doc in document_structures]
        best_conclusion = max(conclusions, key=lambda x: len(x) + x.count('.')) if conclusions else ""
        merged += "\n" + best_conclusion
        
        return merged
    
    def select_best_document(self, responses: List[Dict[str, Any]], 
                           doc_type: str) -> str:
        """Sélectionne le meilleur document parmi plusieurs"""
        
        valid_responses = [r for r in responses if r.get('success') and r.get('response')]
        
        if not valid_responses:
            return ""
        
        if len(valid_responses) == 1:
            return valid_responses[0]['response']
        
        # Scorer chaque document
        scored = []
        for resp in valid_responses:
            score = self._score_document(resp['response'], doc_type)
            scored.append((score, resp['response'], resp['provider']))
        
        # Retourner le meilleur
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]
    
    def _score_document(self, document: str, doc_type: str) -> float:
        """Score un document selon sa qualité"""
        
        score = 0.0
        
        # Longueur
        words = len(document.split())
        if 1000 <= words <= 3000:
            score += 10
        elif 3000 < words <= 5000:
            score += 15
        elif words > 5000:
            score += 20
        
        # Structure
        structure = self.analyze_document_structure(document)
        score += len(structure['sections']) * 5
        
        # Références juridiques
        legal_refs = extract_legal_references(document)
        score += min(len(legal_refs) * 2, 20)
        
        # Formules juridiques
        for phrase_list in LEGAL_PHRASES.values():
            for phrase in phrase_list:
                if phrase.lower() in document.lower():
                    score += 1.5
        
        # Éléments spécifiques par type
        if doc_type == 'conclusions' and 'PAR CES MOTIFS' in document:
            score += 10
        elif doc_type == 'plainte' and 'Monsieur le Procureur' in document:
            score += 5
        
        return score
    
    def synthesize_documents(self, responses: List[Dict[str, Any]], 
                           doc_type: str) -> str:
        """Synthétise plusieurs versions en une version enrichie"""
        
        # Utiliser la fusion intelligente comme base
        base = self.intelligent_document_fusion(responses, doc_type)
        
        # Enrichir avec les éléments uniques de chaque version
        valid_responses = [r for r in responses if r.get('success') and r.get('response')]
        
        for resp in valid_responses:
            # Extraire les références juridiques uniques
            doc_refs = set(extract_legal_references(resp['response']))
            base_refs = set(extract_legal_references(base))
            
            unique_refs = doc_refs - base_refs
            if unique_refs:
                # Les ajouter à la section appropriée
                # (implémentation simplifiée)
                pass
        
        return base


# Point d'entrée principal
def process_redaction_request(query: str, analysis: dict):
    """Point d'entrée pour le module de rédaction"""
    
    redactor = UnifiedRedactionModule()
    redactor.process_redaction_request(query, analysis)
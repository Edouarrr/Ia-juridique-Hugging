"""Module de génération de rapports juridiques"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class ReportModule:
    """Module de génération automatique de rapports juridiques"""
    
    def __init__(self):
        self.name = "Génération de rapports"
        self.description = "Créez automatiquement des rapports juridiques professionnels"
        self.icon = "📄"
        self.available = True
        
        # Templates de rapports
        self.report_templates = {
            'synthese': {
                'name': 'Synthèse d\'analyse',
                'sections': ['Résumé exécutif', 'Faits', 'Analyse', 'Conclusions', 'Recommandations'],
                'tone': 'professionnel'
            },
            'plaidoirie': {
                'name': 'Note de plaidoirie',
                'sections': ['En fait', 'En droit', 'Discussion', 'Par ces motifs'],
                'tone': 'formel'
            },
            'memo': {
                'name': 'Mémo juridique',
                'sections': ['Objet', 'Contexte', 'Analyse', 'Risques', 'Actions'],
                'tone': 'concis'
            },
            'conclusions': {
                'name': 'Conclusions',
                'sections': ['Rappel procédure', 'Faits', 'Moyens', 'Demandes'],
                'tone': 'très formel'
            },
            'expertise': {
                'name': 'Rapport d\'expertise',
                'sections': ['Mission', 'Méthodologie', 'Constatations', 'Analyse', 'Conclusions'],
                'tone': 'technique'
            }
        }
        
        # Styles de formatage
        self.formatting_styles = {
            'professionnel': {
                'font': 'Arial',
                'size': 11,
                'spacing': 1.5,
                'margins': 'normales'
            },
            'formel': {
                'font': 'Times New Roman',
                'size': 12,
                'spacing': 2.0,
                'margins': 'larges'
            },
            'moderne': {
                'font': 'Calibri',
                'size': 11,
                'spacing': 1.15,
                'margins': 'étroites'
            }
        }
    
    def render(self):
        """Interface principale du module"""
        st.markdown(f"### {self.icon} {self.name}")
        st.markdown(f"*{self.description}*")
        
        # Tabs principaux
        tab1, tab2, tab3, tab4 = st.tabs([
            "✍️ Nouveau rapport",
            "📚 Modèles",
            "🔄 Fusion",
            "❓ Aide"
        ])
        
        with tab1:
            self._render_new_report()
        
        with tab2:
            self._render_templates()
        
        with tab3:
            self._render_merge_reports()
        
        with tab4:
            self._render_help()
    
    def _render_new_report(self):
        """Interface de création de rapport"""
        
        # Type de rapport
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Type de document",
                list(self.report_templates.keys()),
                format_func=lambda x: self.report_templates[x]['name']
            )
            
            tone = st.select_slider(
                "Ton du document",
                ["Très formel", "Formel", "Professionnel", "Neutre", "Accessible"],
                value="Professionnel"
            )
        
        with col2:
            length = st.select_slider(
                "Longueur",
                ["Concis", "Standard", "Détaillé", "Exhaustif"],
                value="Standard"
            )
            
            style = st.selectbox(
                "Style de formatage",
                list(self.formatting_styles.keys()),
                format_func=lambda x: x.capitalize()
            )
        
        # Informations de base
        st.markdown("#### 📋 Informations générales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Titre du document",
                placeholder="Ex: Synthèse de l'affaire X c/ Y"
            )
            
            client = st.text_input(
                "Client/Demandeur",
                placeholder="Nom du client"
            )
            
            case_ref = st.text_input(
                "Référence",
                placeholder="RG n° XX/XXXXX"
            )
        
        with col2:
            jurisdiction = st.text_input(
                "Juridiction",
                placeholder="Ex: Tribunal de Commerce de Paris"
            )
            
            author = st.text_input(
                "Auteur",
                placeholder="Votre nom",
                value="Me. [Votre nom]"
            )
            
            date = st.date_input(
                "Date du document",
                value=datetime.now()
            )
        
        # Sources de contenu
        st.markdown("#### 📚 Sources de contenu")
        
        content_source = st.radio(
            "Utiliser",
            ["Données de session", "Saisie manuelle", "Import fichier", "Génération IA"],
            horizontal=True
        )
        
        content_data = self._get_content_data(content_source, report_type)
        
        # Sections à inclure
        st.markdown("#### 📑 Sections du rapport")
        
        template = self.report_templates[report_type]
        selected_sections = []
        
        cols = st.columns(2)
        for i, section in enumerate(template['sections']):
            with cols[i % 2]:
                if st.checkbox(section, value=True, key=f"section_{section}"):
                    selected_sections.append(section)
        
        # Options supplémentaires
        with st.expander("⚙️ Options avancées", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                include_toc = st.checkbox("Table des matières", value=True)
                include_annexes = st.checkbox("Annexes", value=False)
                include_bibliography = st.checkbox("Bibliographie", value=False)
                auto_numbering = st.checkbox("Numérotation automatique", value=True)
            
            with col2:
                include_header = st.checkbox("En-tête personnalisé", value=True)
                include_footer = st.checkbox("Pied de page", value=True)
                include_watermark = st.checkbox("Filigrane", value=False)
                digital_signature = st.checkbox("Signature numérique", value=False)
        
        # Génération
        if st.button("📝 Générer le rapport", type="primary", use_container_width=True):
            if title and selected_sections:
                config = {
                    'type': report_type,
                    'title': title,
                    'client': client,
                    'case_ref': case_ref,
                    'jurisdiction': jurisdiction,
                    'author': author,
                    'date': date,
                    'tone': tone,
                    'length': length,
                    'style': style,
                    'sections': selected_sections,
                    'content_data': content_data,
                    'options': {
                        'toc': include_toc,
                        'annexes': include_annexes,
                        'bibliography': include_bibliography,
                        'numbering': auto_numbering,
                        'header': include_header,
                        'footer': include_footer,
                        'watermark': include_watermark,
                        'signature': digital_signature
                    }
                }
                
                self._generate_report(config)
            else:
                st.warning("Veuillez remplir le titre et sélectionner au moins une section")
    
    def _get_content_data(self, source: str, report_type: str) -> Dict[str, Any]:
        """Récupère les données de contenu selon la source"""
        content_data = {}
        
        if source == "Données de session":
            # Collecter toutes les données disponibles en session
            st.info("📊 Collecte des données de session...")
            
            available_data = []
            
            # Documents
            if 'selected_documents' in st.session_state:
                available_data.append(f"📄 {len(st.session_state.selected_documents)} documents sélectionnés")
            
            # Analyses
            if 'comparison_history' in st.session_state:
                available_data.append(f"📊 {len(st.session_state.comparison_history)} comparaisons")
            
            if 'timeline_history' in st.session_state:
                available_data.append(f"📅 {len(st.session_state.timeline_history)} timelines")
            
            if 'extraction_history' in st.session_state:
                available_data.append(f"📑 {len(st.session_state.extraction_history)} extractions")
            
            if 'strategy_history' in st.session_state:
                available_data.append(f"⚖️ {len(st.session_state.strategy_history)} stratégies")
            
            if available_data:
                st.write("Données disponibles :")
                for data in available_data:
                    st.write(data)
                
                # Permettre la sélection
                use_comparisons = st.checkbox("Inclure les comparaisons")
                use_timelines = st.checkbox("Inclure les timelines")
                use_extractions = st.checkbox("Inclure les extractions")
                use_strategies = st.checkbox("Inclure les stratégies")
                
                # Compiler les données sélectionnées
                if use_comparisons and 'comparison_history' in st.session_state:
                    content_data['comparisons'] = st.session_state.comparison_history
                
                if use_timelines and 'timeline_history' in st.session_state:
                    content_data['timelines'] = st.session_state.timeline_history
                
                if use_extractions and 'extraction_history' in st.session_state:
                    content_data['extractions'] = st.session_state.extraction_history
                
                if use_strategies and 'strategy_history' in st.session_state:
                    content_data['strategies'] = st.session_state.strategy_history
            else:
                st.warning("Aucune donnée disponible en session")
        
        elif source == "Saisie manuelle":
            # Zones de texte pour chaque section potentielle
            st.info("✍️ Saisissez le contenu pour chaque section")
            
            template = self.report_templates[report_type]
            for section in template['sections']:
                content = st.text_area(
                    f"Contenu pour '{section}'",
                    height=150,
                    key=f"manual_{section}"
                )
                if content:
                    content_data[section] = content
        
        elif source == "Import fichier":
            uploaded_file = st.file_uploader(
                "Choisir un fichier",
                type=['txt', 'docx', 'pdf'],
                help="Le contenu sera extrait et utilisé pour le rapport"
            )
            
            if uploaded_file:
                # Simuler l'extraction
                content_data['imported'] = {
                    'filename': uploaded_file.name,
                    'content': "Contenu importé depuis le fichier..."
                }
                st.success(f"✅ Fichier '{uploaded_file.name}' importé")
        
        else:  # Génération IA
            st.info("🤖 Configuration de la génération par IA")
            
            # Paramètres pour l'IA
            col1, col2 = st.columns(2)
            
            with col1:
                ai_style = st.selectbox(
                    "Style d'écriture IA",
                    ["Juridique classique", "Moderne et clair", "Technique approfondi"]
                )
                
                ai_focus = st.multiselect(
                    "Points à développer",
                    ["Faits", "Procédure", "Arguments", "Jurisprudence", "Stratégie"]
                )
            
            with col2:
                ai_length = st.slider(
                    "Longueur par section (mots)",
                    100, 1000, 300
                )
                
                ai_creativity = st.slider(
                    "Créativité",
                    0.0, 1.0, 0.3,
                    help="0 = Factuel, 1 = Créatif"
                )
            
            content_data['ai_config'] = {
                'style': ai_style,
                'focus': ai_focus,
                'length': ai_length,
                'creativity': ai_creativity
            }
        
        return content_data
    
    def _generate_report(self, config: Dict[str, Any]):
        """Génère le rapport"""
        
        with st.spinner("Génération du rapport en cours..."):
            # Créer la structure du rapport
            report = {
                'id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'created_at': datetime.now(),
                'config': config,
                'content': {}
            }
            
            # Générer le contenu pour chaque section
            for section in config['sections']:
                report['content'][section] = self._generate_section_content(
                    section, 
                    config
                )
            
            # Ajouter les métadonnées
            report['metadata'] = {
                'word_count': sum(len(content.split()) for content in report['content'].values()),
                'page_estimate': 0,  # À calculer
                'reading_time': 0    # À calculer
            }
            
            # Estimer les pages et le temps de lecture
            report['metadata']['page_estimate'] = report['metadata']['word_count'] // 250
            report['metadata']['reading_time'] = report['metadata']['word_count'] // 200
            
            # Sauvegarder
            if 'report_history' not in st.session_state:
                st.session_state.report_history = []
            st.session_state.report_history.append(report)
            
            # Afficher
            self._display_report(report)
    
    def _generate_section_content(self, section: str, config: Dict[str, Any]) -> str:
        """Génère le contenu d'une section"""
        
        # Si contenu manuel disponible
        if section in config.get('content_data', {}):
            return config['content_data'][section]
        
        # Sinon, générer selon le type et la section
        content = []
        
        # Templates de contenu par section
        if section == "Résumé exécutif":
            content.append(
                f"Le présent document constitue une {config['type']} "
                f"dans l'affaire {config.get('case_ref', '[Référence]')} "
                f"opposant {config.get('client', '[Client]')} à [Partie adverse]."
            )
            content.append(
                "Cette analyse vise à présenter de manière synthétique "
                "les éléments clés du dossier et nos recommandations."
            )
        
        elif section == "Faits" or section == "En fait":
            content.append("Les faits de l'espèce peuvent être résumés comme suit :")
            
            # Utiliser les données de session si disponibles
            if 'timelines' in config.get('content_data', {}):
                # Extraire les événements clés
                timeline = config['content_data']['timelines'][-1] if config['content_data']['timelines'] else None
                if timeline and 'events' in timeline:
                    for event in timeline['events'][:5]:  # Top 5 événements
                        content.append(
                            f"- Le {event['date'].strftime('%d/%m/%Y')} : {event['description']}"
                        )
            else:
                # Contenu générique
                content.extend([
                    "- Première occurrence des faits litigieux",
                    "- Développement de la situation",
                    "- Tentatives de résolution amiable",
                    "- Échec des négociations et saisine de la juridiction"
                ])
        
        elif section == "Analyse" or section == "En droit":
            content.append("L'analyse juridique de la situation révèle plusieurs points essentiels :")
            
            # Utiliser les extractions si disponibles
            if 'extractions' in config.get('content_data', {}):
                extraction = config['content_data']['extractions'][-1] if config['content_data']['extractions'] else None
                if extraction and 'results' in extraction:
                    insights = extraction['results'].get('insights', [])
                    for insight in insights[:3]:
                        content.append(f"- {insight}")
            else:
                content.extend([
                    "- Qualification juridique des faits",
                    "- Fondements textuels applicables",
                    "- Jurisprudence pertinente"
                ])
        
        elif section == "Conclusions" or section == "Par ces motifs":
            content.append("Au vu de l'ensemble de ces éléments, nous concluons :")
            
            # Utiliser la stratégie si disponible
            if 'strategies' in config.get('content_data', {}):
                strategy = config['content_data']['strategies'][-1] if config['content_data']['strategies'] else None
                if strategy:
                    for obj in strategy['config'].get('objectives', [])[:3]:
                        content.append(f"- {obj}")
            else:
                content.extend([
                    "- Sur le bien-fondé de la demande",
                    "- Sur les moyens soulevés",
                    "- Sur les demandes reconventionnelles éventuelles"
                ])
        
        elif section == "Recommandations" or section == "Actions":
            content.append("Nous recommandons les actions suivantes :")
            
            if 'strategies' in config.get('content_data', {}):
                strategy = config['content_data']['strategies'][-1] if config['content_data']['strategies'] else None
                if strategy and 'action_plan' in strategy:
                    for phase in strategy['action_plan'][:2]:  # Premières phases
                        content.append(f"\n**{phase['phase']}**")
                        for task in phase['tasks'][:3]:
                            content.append(f"- {task}")
            else:
                content.extend([
                    "- Action immédiate recommandée",
                    "- Stratégie à moyen terme",
                    "- Précautions à prendre"
                ])
        
        # Ajuster la longueur selon la configuration
        if config['length'] == 'Concis':
            content = content[:3]
        elif config['length'] == 'Exhaustif':
            content.extend([
                "\nDéveloppement complémentaire...",
                "Analyse approfondie des implications...",
                "Examen détaillé des alternatives..."
            ])
        
        # Ajuster le ton
        if config['tone'] == 'Très formel':
            # Ajouter des formules de politesse juridiques
            content = [self._formalize_text(text) for text in content]
        
        return "\n\n".join(content)
    
    def _formalize_text(self, text: str) -> str:
        """Rend un texte plus formel"""
        replacements = {
            "nous recommandons": "il est respectueusement soumis",
            "nous concluons": "il appert de ce qui précède",
            "les faits": "les éléments factuels de l'espèce",
            "révèle": "fait apparaître",
            "plusieurs points": "diverses considérations d'importance"
        }
        
        formal_text = text
        for informal, formal in replacements.items():
            formal_text = formal_text.replace(informal, formal)
        
        return formal_text
    
    def _display_report(self, report: Dict[str, Any]):
        """Affiche le rapport généré"""
        st.success("✅ Rapport généré avec succès")
        
        # En-tête du rapport
        st.markdown(f"# {report['config']['title']}")
        
        # Métadonnées
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Type", self.report_templates[report['config']['type']]['name'])
        
        with col2:
            st.metric("Mots", f"{report['metadata']['word_count']:,}")
        
        with col3:
            st.metric("Pages estimées", report['metadata']['page_estimate'])
        
        with col4:
            st.metric("Temps lecture", f"{report['metadata']['reading_time']} min")
        
        # Options d'affichage
        col1, col2 = st.columns([3, 1])
        
        with col1:
            view_mode = st.radio(
                "Mode d'affichage",
                ["Aperçu", "Texte complet", "Mode édition"],
                horizontal=True
            )
        
        with col2:
            if st.button("🖨️ Imprimer", use_container_width=True):
                st.info("Utilisez Ctrl+P pour imprimer")
        
        # Affichage du contenu selon le mode
        if view_mode == "Aperçu":
            self._display_report_preview(report)
        elif view_mode == "Texte complet":
            self._display_report_full(report)
        else:
            self._display_report_edit(report)
        
        # Actions
        st.markdown("### 🛠️ Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Export Word
            doc_content = self._export_to_docx_format(report)
            st.download_button(
                "📄 Télécharger Word",
                data=doc_content,
                file_name=f"{report['id']}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # Export PDF (simulé)
            if st.button("📑 Générer PDF", use_container_width=True):
                st.info("Génération PDF en cours...")
        
        with col3:
            # Email
            if st.button("📧 Envoyer", use_container_width=True):
                st.info("Configuration email requise")
        
        with col4:
            # Sauvegarder comme template
            if st.button("💾 Sauver modèle", use_container_width=True):
                self._save_as_template(report)
    
    def _display_report_preview(self, report: Dict[str, Any]):
        """Affiche un aperçu du rapport"""
        
        # Simuler une mise en page document
        st.markdown(
            f"""
            <div style="background: white; padding: 2rem; border: 1px solid #ddd; 
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 1rem 0;">
                <div style="text-align: center; margin-bottom: 2rem;">
                    <h2 style="color: #1e3a5f; margin: 0;">{report['config']['title']}</h2>
                    <p style="color: #666; margin: 0.5rem 0;">
                        {report['config'].get('case_ref', '')}
                    </p>
                    <p style="color: #666; margin: 0;">
                        {report['config']['date'].strftime('%d %B %Y')}
                    </p>
                </div>
                
                <div style="border-top: 2px solid #1e3a5f; margin: 2rem 0;"></div>
            """,
            unsafe_allow_html=True
        )
        
        # Table des matières si activée
        if report['config']['options']['toc']:
            st.markdown("### Table des matières")
            for i, section in enumerate(report['config']['sections'], 1):
                st.markdown(f"{i}. {section}")
            st.markdown("---")
        
        # Aperçu des sections (premières lignes seulement)
        for section, content in report['content'].items():
            st.markdown(f"### {section}")
            
            # Afficher les 3 premières lignes
            lines = content.split('\n')
            preview = '\n'.join(lines[:3])
            if len(lines) > 3:
                preview += "\n\n*[...]*"
            
            st.markdown(preview)
            st.markdown("")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def _display_report_full(self, report: Dict[str, Any]):
        """Affiche le rapport complet"""
        
        # En-tête formel
        if report['config']['options']['header']:
            st.markdown(
                f"""
                ---
                **{report['config'].get('author', 'Auteur')}**  
                {report['config'].get('jurisdiction', '')}  
                {report['config']['date'].strftime('%d %B %Y')}
                
                ---
                """
            )
        
        # Table des matières
        if report['config']['options']['toc']:
            with st.expander("📑 Table des matières", expanded=False):
                for i, section in enumerate(report['config']['sections'], 1):
                    st.markdown(f"{i}. {section}")
        
        # Contenu complet
        for i, (section, content) in enumerate(report['content'].items(), 1):
            if report['config']['options']['numbering']:
                st.markdown(f"## {i}. {section}")
            else:
                st.markdown(f"## {section}")
            
            st.markdown(content)
            
            # Séparateur entre sections
            if i < len(report['content']):
                st.markdown("---")
        
        # Pied de page
        if report['config']['options']['footer']:
            st.markdown(
                f"""
                ---
                <div style="text-align: center; color: #666; font-size: 0.9rem;">
                    Page {report['metadata']['page_estimate']} | 
                    {report['config']['title']} | 
                    {report['config']['date'].strftime('%d/%m/%Y')}
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def _display_report_edit(self, report: Dict[str, Any]):
        """Mode édition du rapport"""
        st.info("✏️ Mode édition - Modifiez directement le contenu")
        
        edited_content = {}
        
        for section, content in report['content'].items():
            st.markdown(f"### {section}")
            
            edited = st.text_area(
                f"Contenu de '{section}'",
                value=content,
                height=200,
                key=f"edit_{section}",
                label_visibility="collapsed"
            )
            
            edited_content[section] = edited
        
        # Boutons d'action
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Sauvegarder les modifications", type="primary"):
                # Mettre à jour le rapport
                report['content'] = edited_content
                report['metadata']['word_count'] = sum(len(c.split()) for c in edited_content.values())
                report['metadata']['page_estimate'] = report['metadata']['word_count'] // 250
                st.success("✅ Modifications sauvegardées")
                st.rerun()
        
        with col2:
            if st.button("🔄 Annuler"):
                st.rerun()
        
        with col3:
            if st.button("📋 Copier tout"):
                full_text = "\n\n".join([f"{s}\n{'-'*len(s)}\n{c}" for s, c in edited_content.items()])
                st.code(full_text)
    
    def _export_to_docx_format(self, report: Dict[str, Any]) -> str:
        """Exporte le rapport au format Word (texte)"""
        lines = []
        
        # En-tête
        lines.append("="*60)
        lines.append(report['config']['title'].upper())
        lines.append("="*60)
        lines.append("")
        
        # Métadonnées
        if report['config'].get('case_ref'):
            lines.append(f"Référence : {report['config']['case_ref']}")
        if report['config'].get('client'):
            lines.append(f"Client : {report['config']['client']}")
        if report['config'].get('jurisdiction'):
            lines.append(f"Juridiction : {report['config']['jurisdiction']}")
        lines.append(f"Date : {report['config']['date'].strftime('%d %B %Y')}")
        if report['config'].get('author'):
            lines.append(f"Auteur : {report['config']['author']}")
        lines.append("")
        lines.append("-"*60)
        lines.append("")
        
        # Table des matières
        if report['config']['options']['toc']:
            lines.append("TABLE DES MATIÈRES")
            lines.append("-"*20)
            for i, section in enumerate(report['config']['sections'], 1):
                lines.append(f"{i}. {section}")
            lines.append("")
            lines.append("-"*60)
            lines.append("")
        
        # Contenu
        for i, (section, content) in enumerate(report['content'].items(), 1):
            if report['config']['options']['numbering']:
                lines.append(f"{i}. {section.upper()}")
            else:
                lines.append(section.upper())
            
            lines.append("-" * len(section))
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("")
        
        # Pied de page
        lines.append("-"*60)
        lines.append(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        lines.append(f"Total : {report['metadata']['word_count']} mots - "
                    f"Environ {report['metadata']['page_estimate']} pages")
        
        return "\n".join(lines)
    
    def _save_as_template(self, report: Dict[str, Any]):
        """Sauvegarde le rapport comme template"""
        if 'custom_templates' not in st.session_state:
            st.session_state.custom_templates = {}
        
        template_name = f"Template_{report['config']['type']}_{datetime.now().strftime('%Y%m%d')}"
        
        st.session_state.custom_templates[template_name] = {
            'name': report['config']['title'],
            'type': report['config']['type'],
            'sections': report['config']['sections'],
            'structure': {s: c[:100] + "..." for s, c in report['content'].items()},
            'created_at': datetime.now()
        }
        
        st.success(f"✅ Template '{template_name}' sauvegardé")
    
    def _render_templates(self):
        """Gestion des modèles de rapports"""
        st.markdown("#### 📚 Bibliothèque de modèles")
        
        # Tabs pour les différents types de templates
        tab1, tab2 = st.tabs(["Modèles standards", "Mes modèles"])
        
        with tab1:
            self._display_standard_templates()
        
        with tab2:
            self._display_custom_templates()
    
    def _display_standard_templates(self):
        """Affiche les templates standards"""
        st.markdown("##### Modèles prédéfinis")
        
        for template_id, template in self.report_templates.items():
            with st.expander(f"{template['name']}", expanded=False):
                st.write(f"**Ton recommandé :** {template['tone']}")
                st.write("**Sections :**")
                for section in template['sections']:
                    st.write(f"- {section}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📝 Utiliser", key=f"use_std_{template_id}"):
                        st.session_state.selected_template = template_id
                        st.info(f"Template '{template['name']}' sélectionné")
                
                with col2:
                    if st.button(f"👁️ Aperçu", key=f"preview_std_{template_id}"):
                        self._preview_template(template_id, template)
    
    def _display_custom_templates(self):
        """Affiche les templates personnalisés"""
        if 'custom_templates' not in st.session_state or not st.session_state.custom_templates:
            st.info("Aucun modèle personnalisé. Créez-en un en sauvegardant un rapport comme modèle.")
            return
        
        st.markdown("##### Mes modèles personnalisés")
        
        for template_id, template in st.session_state.custom_templates.items():
            with st.expander(
                f"{template['name']} - {template['created_at'].strftime('%d/%m/%Y')}",
                expanded=False
            ):
                st.write(f"**Type :** {self.report_templates.get(template['type'], {}).get('name', template['type'])}")
                st.write(f"**Sections :** {len(template['sections'])}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📝 Utiliser", key=f"use_custom_{template_id}"):
                        st.session_state.selected_custom_template = template
                        st.info("Template personnalisé sélectionné")
                
                with col2:
                    if st.button("✏️ Modifier", key=f"edit_custom_{template_id}"):
                        st.session_state.editing_template = template_id
                
                with col3:
                    if st.button("🗑️ Supprimer", key=f"del_custom_{template_id}"):
                        del st.session_state.custom_templates[template_id]
                        st.rerun()
    
    def _preview_template(self, template_id: str, template: Dict[str, Any]):
        """Aperçu d'un template"""
        st.markdown(f"### Aperçu : {template['name']}")
        
        st.markdown("#### Structure du document")
        
        for i, section in enumerate(template['sections'], 1):
            st.markdown(f"**{i}. {section}**")
            
            # Contenu exemple selon la section
            if section == "Résumé exécutif":
                st.markdown("*Synthèse de l'affaire et des enjeux principaux...*")
            elif section in ["Faits", "En fait"]:
                st.markdown("*Chronologie et description détaillée des événements...*")
            elif section in ["Analyse", "En droit"]:
                st.markdown("*Analyse juridique approfondie avec références...*")
            elif section == "Conclusions":
                st.markdown("*Conclusions et recommandations finales...*")
            else:
                st.markdown(f"*Contenu de la section {section}...*")
            
            st.markdown("")
    
    def _render_merge_reports(self):
        """Fusion de plusieurs rapports"""
        st.markdown("#### 🔄 Fusion de rapports")
        
        if 'report_history' not in st.session_state or len(st.session_state.report_history) < 2:
            st.info("Au moins 2 rapports sont nécessaires pour effectuer une fusion.")
            return
        
        # Sélection des rapports à fusionner
        st.markdown("##### Sélectionner les rapports à fusionner")
        
        report_options = []
        for i, report in enumerate(st.session_state.report_history):
            report_options.append(
                f"{report['config']['title']} - {report['created_at'].strftime('%d/%m/%Y %H:%M')}"
            )
        
        selected_indices = st.multiselect(
            "Rapports à fusionner",
            range(len(report_options)),
            format_func=lambda x: report_options[x],
            help="Sélectionnez 2 à 5 rapports"
        )
        
        if len(selected_indices) >= 2:
            # Options de fusion
            st.markdown("##### Options de fusion")
            
            col1, col2 = st.columns(2)
            
            with col1:
                merge_mode = st.selectbox(
                    "Mode de fusion",
                    ["Concaténation", "Synthèse", "Comparaison", "Consolidation"],
                    help="Comment combiner les contenus"
                )
                
                section_handling = st.radio(
                    "Gestion des sections",
                    ["Fusionner sections identiques", "Conserver toutes les sections", "Sélection manuelle"]
                )
            
            with col2:
                new_title = st.text_input(
                    "Titre du rapport fusionné",
                    value="Rapport consolidé"
                )
                
                keep_metadata = st.checkbox(
                    "Conserver les métadonnées",
                    value=True,
                    help="Références, dates, auteurs..."
                )
            
            # Aperçu de la structure
            if section_handling == "Sélection manuelle":
                st.markdown("##### Sélection des sections")
                
                # Collecter toutes les sections uniques
                all_sections = set()
                for idx in selected_indices:
                    all_sections.update(st.session_state.report_history[idx]['config']['sections'])
                
                selected_sections = []
                cols = st.columns(2)
                for i, section in enumerate(sorted(all_sections)):
                    with cols[i % 2]:
                        if st.checkbox(section, value=True, key=f"merge_section_{section}"):
                            selected_sections.append(section)
            
            # Bouton de fusion
            if st.button("🔄 Fusionner les rapports", type="primary", use_container_width=True):
                selected_reports = [st.session_state.report_history[i] for i in selected_indices]
                
                merge_config = {
                    'mode': merge_mode,
                    'section_handling': section_handling,
                    'selected_sections': selected_sections if section_handling == "Sélection manuelle" else None,
                    'new_title': new_title,
                    'keep_metadata': keep_metadata
                }
                
                self._perform_merge(selected_reports, merge_config)
    
    def _perform_merge(self, reports: List[Dict[str, Any]], config: Dict[str, Any]):
        """Effectue la fusion des rapports"""
        
        with st.spinner("Fusion en cours..."):
            # Créer le rapport fusionné
            merged_report = {
                'id': f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'created_at': datetime.now(),
                'config': {
                    'title': config['new_title'],
                    'type': 'merged',
                    'tone': 'Professionnel',
                    'length': 'Standard',
                    'style': 'professionnel',
                    'sections': [],
                    'options': reports[0]['config']['options']  # Prendre les options du premier
                },
                'content': {},
                'metadata': {
                    'source_reports': len(reports),
                    'merge_mode': config['mode']
                }
            }
            
            # Fusionner selon le mode
            if config['mode'] == 'Concaténation':
                merged_content = self._merge_concatenate(reports, config)
            elif config['mode'] == 'Synthèse':
                merged_content = self._merge_synthesize(reports, config)
            elif config['mode'] == 'Comparaison':
                merged_content = self._merge_compare(reports, config)
            else:  # Consolidation
                merged_content = self._merge_consolidate(reports, config)
            
            merged_report['content'] = merged_content
            merged_report['config']['sections'] = list(merged_content.keys())
            
            # Calculer les métadonnées
            total_words = sum(len(content.split()) for content in merged_content.values())
            merged_report['metadata']['word_count'] = total_words
            merged_report['metadata']['page_estimate'] = total_words // 250
            merged_report['metadata']['reading_time'] = total_words // 200
            
            # Sauvegarder
            st.session_state.report_history.append(merged_report)
            
            # Afficher
            st.success("✅ Rapports fusionnés avec succès")
            self._display_report(merged_report)
    
    def _merge_concatenate(self, reports: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, str]:
        """Fusion par concaténation simple"""
        merged_content = defaultdict(list)
        
        for i, report in enumerate(reports):
            # Ajouter un séparateur
            if i > 0:
                for section in merged_content:
                    merged_content[section].append("\n---\n")
            
            # Ajouter le contenu
            for section, content in report['content'].items():
                if config['section_handling'] == "Fusionner sections identiques":
                    merged_content[section].append(content)
                else:
                    # Préfixer avec le rapport source
                    section_key = f"{section} (Rapport {i+1})"
                    merged_content[section_key].append(content)
        
        # Convertir en dictionnaire simple
        return {section: "\n".join(contents) for section, contents in merged_content.items()}
    
    def _merge_synthesize(self, reports: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, str]:
        """Fusion avec synthèse du contenu"""
        merged_content = {}
        
        # Regrouper par section
        sections_content = defaultdict(list)
        for report in reports:
            for section, content in report['content'].items():
                sections_content[section].append(content)
        
        # Synthétiser chaque section
        for section, contents in sections_content.items():
            if len(contents) == 1:
                merged_content[section] = contents[0]
            else:
                # Créer une synthèse
                synthesis = [f"Synthèse de {len(contents)} sources :\n"]
                
                # Extraire les points clés de chaque contenu
                for i, content in enumerate(contents):
                    # Prendre les premières lignes significatives
                    lines = [l for l in content.split('\n') if l.strip()][:3]
                    synthesis.append(f"\n**Source {i+1} :**")
                    synthesis.extend([f"- {line}" for line in lines])
                
                merged_content[section] = "\n".join(synthesis)
        
        return merged_content
    
    def _merge_compare(self, reports: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, str]:
        """Fusion avec comparaison des contenus"""
        merged_content = {}
        
        # Introduction comparative
        merged_content['Introduction'] = (
            f"Ce document compare {len(reports)} rapports :\n\n" +
            "\n".join([f"- Rapport {i+1} : {r['config']['title']}" for i, r in enumerate(reports)])
        )
        
        # Comparer section par section
        all_sections = set()
        for report in reports:
            all_sections.update(report['config']['sections'])
        
        for section in sorted(all_sections):
            comparison = [f"## Comparaison : {section}\n"]
            
            for i, report in enumerate(reports):
                if section in report['content']:
                    comparison.append(f"### Rapport {i+1}")
                    comparison.append(report['content'][section])
                else:
                    comparison.append(f"### Rapport {i+1}")
                    comparison.append("*Section non présente dans ce rapport*")
                
                comparison.append("")
            
            merged_content[f"Comparaison - {section}"] = "\n".join(comparison)
        
        return merged_content
    
    def _merge_consolidate(self, reports: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, str]:
        """Fusion avec consolidation intelligente"""
        merged_content = {}
        
        # Regrouper les contenus similaires
        for section in ['Faits', 'Analyse', 'Conclusions']:
            contents = []
            for report in reports:
                for s, content in report['content'].items():
                    if section.lower() in s.lower():
                        contents.append(content)
            
            if contents:
                # Consolidation intelligente
                consolidated = self._consolidate_contents(contents, section)
                merged_content[section] = consolidated
        
        return merged_content
    
    def _consolidate_contents(self, contents: List[str], section: str) -> str:
        """Consolide plusieurs contenus en évitant les redondances"""
        if not contents:
            return ""
        
        if len(contents) == 1:
            return contents[0]
        
        # Stratégie simple : prendre le plus long et ajouter les éléments uniques des autres
        base_content = max(contents, key=len)
        consolidated = [base_content]
        
        # Ajouter les éléments uniques des autres contenus
        base_sentences = set(re.split(r'[.!?]+', base_content.lower()))
        
        for content in contents:
            if content != base_content:
                sentences = re.split(r'[.!?]+', content)
                unique_sentences = [
                    s.strip() for s in sentences 
                    if s.strip() and s.strip().lower() not in base_sentences
                ]
                
                if unique_sentences:
                    consolidated.append(f"\n\nÉléments additionnels :")
                    consolidated.extend([f"- {s}" for s in unique_sentences[:5]])
        
        return "\n".join(consolidated)
    
    def _render_help(self):
        """Affiche l'aide du module"""
        st.markdown("""
        #### ❓ Guide d'utilisation du module Rapports
        
        ##### 🎯 Objectif
        Ce module permet de générer automatiquement des documents juridiques professionnels à partir de vos analyses.
        
        ##### 📋 Types de documents disponibles
        
        1. **Synthèse d'analyse**
           - Vue d'ensemble d'une affaire
           - Points clés et recommandations
           - Format : 2-5 pages
        
        2. **Note de plaidoirie**
           - Structure formelle En fait / En droit
           - Arguments développés
           - Format : 5-15 pages
        
        3. **Mémo juridique**
           - Communication interne
           - Points d'action clairs
           - Format : 1-3 pages
        
        4. **Conclusions**
           - Document procédural formel
           - Respect des formes juridiques
           - Format : 10-30 pages
        
        5. **Rapport d'expertise**
           - Analyse technique détaillée
           - Méthodologie et conclusions
           - Format : 15-50 pages
        
        ##### 💡 Conseils de rédaction
        
        - **Ton** : Adaptez le ton au destinataire (juge, client, confrère)
        - **Longueur** : Commencez concis, développez si nécessaire
        - **Structure** : Respectez l'ordre logique des arguments
        - **Sources** : Utilisez les données de vos analyses précédentes
        
        ##### 🔧 Fonctionnalités avancées
        
        **Fusion de rapports**
        - Combinez plusieurs analyses en un document unique
        - 4 modes : Concaténation, Synthèse, Comparaison, Consolidation
        - Évite les redondances
        
        **Templates personnalisés**
        - Sauvegardez vos rapports comme modèles
        - Réutilisez la structure pour gagner du temps
        - Adaptez aux besoins spécifiques
        
        **Export multi-format**
        - Word : Pour édition ultérieure
        - PDF : Pour envoi final
        - Email : Envoi direct (configuration requise)
        
        ##### ⚡ Raccourcis
        
        - **Données de session** : Réutilise automatiquement vos analyses
        - **Mode édition** : Modifiez directement dans l'interface
        - **Aperçu** : Visualisez avant export
        - **Templates** : Gagnez du temps avec les modèles
        
        ##### 📝 Bonnes pratiques
        
        1. **Vérifiez toujours** le contenu généré
        2. **Personnalisez** selon le destinataire
        3. **Citez vos sources** (jurisprudence, articles)
        4. **Archivez** les versions importantes
        5. **Testez** les exports avant envoi
        """)


# Point d'entrée pour tests
if __name__ == "__main__":
    module = ReportModule()
    module.render()
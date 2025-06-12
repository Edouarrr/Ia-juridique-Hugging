"""Module d'intégration entre la recherche universelle et la génération juridique"""

import streamlit as st
from typing import Dict, List, Optional, Any
import re

# Import des modules
try:
    from modules.generation_juridique import (
        GenerateurActesJuridiques, 
        process_generation_request,
        determine_acte_type
    )
    GENERATION_AVAILABLE = True
except ImportError:
    GENERATION_AVAILABLE = False

try:
    from config.cahier_des_charges import (
        get_config_for_acte,
        PROMPTS_GENERATION,
        validate_acte
    )
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# ========================= ANALYSEUR DE REQUÊTES JURIDIQUES =========================

class AnalyseurRequeteJuridique:
    """Analyse les requêtes pour détecter les demandes de génération juridique"""
    
    # Mots-clés pour détecter une demande de génération
    KEYWORDS_GENERATION = {
        'rediger': ['rédiger', 'rédige', 'rédigez', 'rédaction'],
        'creer': ['créer', 'crée', 'créez', 'création', 'établir'],
        'generer': ['générer', 'génère', 'générez', 'génération'],
        'preparer': ['préparer', 'prépare', 'préparez', 'préparation'],
        'ecrire': ['écrire', 'écris', 'écrivez', 'écriture']
    }
    
    # Types d'actes détectables
    TYPES_ACTES = {
        'plainte': ['plainte', 'dépôt de plainte'],
        'plainte_cpc': ['plainte avec constitution de partie civile', 'cpc', 'partie civile'],
        'conclusions': ['conclusions', 'conclusion'],
        'conclusions_nullite': ['conclusions de nullité', 'nullité', 'in limine litis'],
        'assignation': ['assignation', 'assigner'],
        'citation': ['citation directe', 'citation'],
        'observations': ['observations', 'article 175', '175 cpp'],
        'courrier': ['courrier', 'lettre', 'correspondance']
    }
    
    # Patterns pour extraire les informations
    PATTERNS = {
        'parties': r'contre\s+([A-Za-zÀ-ÿ\s,&\-\.]+?)(?:\s+et\s+|,|\s+pour\s+|$)',
        'infractions': r'pour\s+([\w\s,]+?)(?:\s+contre\s+|\s+à\s+|$)',
        'reference': r'@(\w+)',
        'date': r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        'montant': r'(\d+(?:\s*\d{3})*(?:,\d{2})?\s*(?:€|euros?))'
    }
    
    def analyser_requete(self, query: str) -> Dict[str, Any]:
        """Analyse une requête pour extraire les informations juridiques"""
        
        query_lower = query.lower()
        
        # Détecter si c'est une demande de génération
        is_generation = self._detect_generation_request(query_lower)
        
        # Détecter le type d'acte
        type_acte = self._detect_acte_type(query_lower)
        
        # Extraire les parties
        parties = self._extract_parties(query)
        
        # Extraire les infractions
        infractions = self._extract_infractions(query)
        
        # Extraire la référence
        reference = self._extract_reference(query)
        
        # Extraire les dates
        dates = self._extract_dates(query)
        
        # Extraire les montants
        montants = self._extract_montants(query)
        
        # Déterminer le contexte procédural
        contexte = self._determine_contexte(query_lower)
        
        return {
            'is_generation': is_generation,
            'type_acte': type_acte,
            'parties': parties,
            'infractions': infractions,
            'reference': reference,
            'dates': dates,
            'montants': montants,
            'contexte': contexte,
            'query_original': query
        }
    
    def _detect_generation_request(self, query_lower: str) -> bool:
        """Détecte si la requête demande une génération de document"""
        for category, keywords in self.KEYWORDS_GENERATION.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return True
        return False
    
    def _detect_acte_type(self, query_lower: str) -> Optional[str]:
        """Détecte le type d'acte demandé"""
        # Vérifier d'abord les types spécifiques (plus longs)
        for acte_type, keywords in sorted(self.TYPES_ACTES.items(), 
                                         key=lambda x: -len(x[0])):
            for keyword in keywords:
                if keyword in query_lower:
                    return acte_type
        return None
    
    def _extract_parties(self, query: str) -> Dict[str, List[str]]:
        """Extrait les parties de la requête"""
        parties = {
            'demandeurs': [],
            'defendeurs': []
        }
        
        # Rechercher le pattern "contre"
        matches = re.findall(self.PATTERNS['parties'], query, re.IGNORECASE)
        for match in matches:
            # Nettoyer et séparer les parties multiples
            parties_list = [p.strip() for p in re.split(r',|et', match) if p.strip()]
            parties['defendeurs'].extend(parties_list)
        
        # Si pas de "contre", chercher "pour" (demandeur)
        if 'pour' in query.lower():
            pour_match = re.search(r'pour\s+([A-Za-zÀ-ÿ\s\-\.]+?)(?:\s+contre|\s*$)', 
                                 query, re.IGNORECASE)
            if pour_match:
                parties['demandeurs'].append(pour_match.group(1).strip())
        
        return parties
    
    def _extract_infractions(self, query: str) -> List[str]:
        """Extrait les infractions mentionnées"""
        infractions = []
        
        # Liste des infractions courantes
        infractions_courantes = [
            'abus de biens sociaux', 'abs',
            'corruption',
            'escroquerie',
            'abus de confiance',
            'blanchiment',
            'faux et usage de faux',
            'détournement de fonds',
            'prise illégale d\'intérêts',
            'favoritisme',
            'trafic d\'influence'
        ]
        
        query_lower = query.lower()
        for infraction in infractions_courantes:
            if infraction in query_lower:
                # Normaliser le nom de l'infraction
                if infraction == 'abs':
                    infractions.append('Abus de biens sociaux')
                else:
                    infractions.append(infraction.title())
        
        # Rechercher aussi avec le pattern
        infraction_matches = re.findall(self.PATTERNS['infractions'], query, re.IGNORECASE)
        for match in infraction_matches:
            infractions.extend([i.strip().title() for i in match.split(',') if i.strip()])
        
        # Dédupliquer
        return list(dict.fromkeys(infractions))
    
    def _extract_reference(self, query: str) -> Optional[str]:
        """Extrait la référence du dossier (@reference)"""
        match = re.search(self.PATTERNS['reference'], query)
        return match.group(1) if match else None
    
    def _extract_dates(self, query: str) -> List[str]:
        """Extrait les dates mentionnées"""
        return re.findall(self.PATTERNS['date'], query)
    
    def _extract_montants(self, query: str) -> List[str]:
        """Extrait les montants mentionnés"""
        return re.findall(self.PATTERNS['montant'], query)
    
    def _determine_contexte(self, query_lower: str) -> Dict[str, Any]:
        """Détermine le contexte procédural"""
        contexte = {
            'phase': 'enquete',  # par défaut
            'urgence': False,
            'complexite': 'normale'
        }
        
        # Détecter la phase
        if any(word in query_lower for word in ['instruction', 'juge d\'instruction', 'doyen']):
            contexte['phase'] = 'instruction'
        elif any(word in query_lower for word in ['audience', 'jugement', 'tribunal']):
            contexte['phase'] = 'jugement'
        elif any(word in query_lower for word in ['appel', 'cour d\'appel']):
            contexte['phase'] = 'appel'
        
        # Détecter l'urgence
        if any(word in query_lower for word in ['urgent', 'urgence', 'immédiat', 'rapidement']):
            contexte['urgence'] = True
        
        # Détecter la complexité
        if any(word in query_lower for word in ['complexe', 'détaillé', 'exhaustif', 'approfondi']):
            contexte['complexite'] = 'elevee'
        elif any(word in query_lower for word in ['simple', 'basique', 'standard']):
            contexte['complexite'] = 'simple'
        
        return contexte

# ========================= INTÉGRATION AVEC LA RECHERCHE =========================

def enhance_search_with_generation(search_interface):
    """Améliore l'interface de recherche avec les capacités de génération juridique"""
    
    # Ajouter l'analyseur juridique
    if not hasattr(search_interface, 'analyseur_juridique'):
        search_interface.analyseur_juridique = AnalyseurRequeteJuridique()
    
    # Wrapper pour process_universal_query
    original_process = search_interface.process_universal_query
    
    async def enhanced_process_universal_query(query: str):
        """Version améliorée qui détecte les demandes juridiques"""
        
        # Analyser la requête avec l'analyseur juridique
        analyse_juridique = search_interface.analyseur_juridique.analyser_requete(query)
        
        # Si c'est une demande de génération juridique
        if analyse_juridique['is_generation'] and analyse_juridique['type_acte']:
            return await process_juridical_generation(query, analyse_juridique)
        else:
            # Sinon, utiliser le processus original
            return await original_process(query)
    
    # Remplacer la méthode
    search_interface.process_universal_query = enhanced_process_universal_query
    
    return search_interface

async def process_juridical_generation(query: str, analyse: Dict[str, Any]):
    """Traite une demande de génération juridique"""
    
    st.info("⚖️ Détection d'une demande de génération d'acte juridique")
    
    if not GENERATION_AVAILABLE:
        st.error("❌ Module de génération juridique non disponible")
        st.info("Assurez-vous d'avoir créé le fichier modules/generation_juridique.py")
        return
    
    # Afficher l'analyse
    with st.expander("🔍 Analyse de la requête", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Type d'acte détecté:**", analyse['type_acte'])
            st.write("**Phase procédurale:**", analyse['contexte']['phase'])
            st.write("**Référence:**", analyse['reference'] or "Non spécifiée")
        
        with col2:
            st.write("**Parties défenderesses:**", ', '.join(analyse['parties']['defendeurs']) or "À définir")
            st.write("**Infractions:**", ', '.join(analyse['infractions']) or "À définir")
            st.write("**Urgence:**", "✅" if analyse['contexte']['urgence'] else "❌")
    
    # Interface de configuration
    st.markdown("### ⚖️ Configuration de l'acte juridique")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Type d'acte (avec possibilité de modifier)
        type_acte = st.selectbox(
            "Type d'acte",
            options=[
                'plainte_simple', 'plainte_cpc', 
                'conclusions', 'conclusions_nullite',
                'assignation', 'citation_directe',
                'observations_175', 'courrier'
            ],
            index=['plainte_simple', 'plainte_cpc', 'conclusions', 'conclusions_nullite',
                   'assignation', 'citation_directe', 'observations_175', 'courrier'
                  ].index(analyse['type_acte']) if analyse['type_acte'] in [
                      'plainte_simple', 'plainte_cpc', 'conclusions', 'conclusions_nullite',
                      'assignation', 'citation_directe', 'observations_175', 'courrier'
                  ] else 0,
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    with col2:
        # Phase procédurale
        phase = st.selectbox(
            "Phase procédurale",
            ["Enquête préliminaire", "Instruction", "Jugement", "Appel"],
            index=["enquete", "instruction", "jugement", "appel"].index(
                analyse['contexte']['phase']
            ) if analyse['contexte']['phase'] in ["enquete", "instruction", "jugement", "appel"] else 0
        )
    
    # Parties
    st.markdown("#### 👥 Parties")
    
    col1, col2 = st.columns(2)
    
    with col1:
        demandeurs = st.text_area(
            "Demandeurs / Plaignants",
            value='\n'.join(analyse['parties']['demandeurs']),
            height=100,
            placeholder="Un par ligne"
        )
    
    with col2:
        defendeurs = st.text_area(
            "Défendeurs / Mis en cause",
            value='\n'.join(analyse['parties']['defendeurs']),
            height=100,
            placeholder="Un par ligne"
        )
    
    # Infractions
    st.markdown("#### 🚨 Infractions")
    
    infractions_predefinies = [
        "Abus de biens sociaux",
        "Corruption", 
        "Escroquerie",
        "Abus de confiance",
        "Blanchiment",
        "Faux et usage de faux"
    ]
    
    infractions = st.multiselect(
        "Sélectionner les infractions",
        infractions_predefinies,
        default=[inf for inf in analyse['infractions'] if inf in infractions_predefinies]
    )
    
    # Options avancées
    with st.expander("⚙️ Options avancées"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            style = st.selectbox(
                "Style de rédaction",
                ["Standard", "Exhaustif", "Technique", "Argumentatif"],
                index=1 if analyse['contexte']['complexite'] == 'elevee' else 0
            )
        
        with col2:
            longueur = st.number_input(
                "Longueur cible (mots)",
                min_value=1000,
                max_value=10000,
                value=8000 if type_acte == 'plainte_cpc' else 3000,
                step=500
            )
        
        with col3:
            jurisprudence = st.checkbox(
                "Inclure jurisprudences",
                value=True
            )
    
    # Bouton de génération avec le style du cahier des charges
    if st.button("🚀 Générer l'acte juridique", type="primary", use_container_width=True):
        
        # Validation
        if not defendeurs.strip() and not demandeurs.strip():
            st.error("Veuillez renseigner au moins une partie")
            return
        
        if not infractions:
            st.error("Veuillez sélectionner au moins une infraction")
            return
        
        # Préparer les paramètres
        params = {
            'type_acte': type_acte,
            'parties': {
                'demandeurs': [d.strip() for d in demandeurs.split('\n') if d.strip()],
                'defendeurs': [d.strip() for d in defendeurs.split('\n') if d.strip()]
            },
            'infractions': infractions,
            'reference': analyse['reference'],
            'contexte': analyse['contexte'],
            'options': {
                'style': style.lower(),
                'longueur_cible': longueur,
                'inclure_jurisprudence': jurisprudence,
                'phase': phase.lower().split()[0]
            }
        }
        
        # Générer avec le module juridique
        with st.spinner("⏳ Génération en cours selon le cahier des charges..."):
            try:
                # Créer le générateur
                generateur = GenerateurActesJuridiques()
                generateur.current_phase = params['options']['phase']
                
                # Générer l'acte
                acte = generateur.generer_acte(type_acte, params)
                
                # Valider selon le cahier des charges
                if CONFIG_AVAILABLE:
                    validation = validate_acte(acte.contenu, type_acte)
                    
                    if not validation['valid']:
                        st.warning("⚠️ L'acte ne respecte pas entièrement le cahier des charges")
                        for error in validation['errors']:
                            st.error(f"❌ {error}")
                    else:
                        st.success("✅ Acte généré conformément au cahier des charges")
                
                # Stocker le résultat
                st.session_state.acte_genere = acte
                st.session_state.generation_result = {
                    'type': 'acte_juridique',
                    'acte': acte,
                    'params': params,
                    'validation': validation if CONFIG_AVAILABLE else None
                }
                
                # Afficher le résultat
                display_generated_acte(acte)
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération : {str(e)}")
                import traceback
                st.code(traceback.format_exc())

def display_generated_acte(acte):
    """Affiche l'acte généré avec toutes les options"""
    
    st.markdown("---")
    st.markdown(f"### 📄 {acte.titre}")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mots", f"{acte.metadata['longueur_mots']:,}")
    
    with col2:
        st.metric("Pages estimées", f"~{acte.metadata['longueur_mots'] // 250}")
    
    with col3:
        st.metric("Pièces", len(acte.pieces))
    
    # Zone d'édition avec aperçu du style Garamond
    st.markdown("#### 📝 Contenu de l'acte")
    
    # Note sur le style
    st.info("💡 L'acte sera exporté avec la police Garamond et la mise en forme conforme au cahier des charges")
    
    # Contenu éditable
    contenu_edite = st.text_area(
        "Éditer le contenu",
        value=acte.contenu,
        height=600,
        key="edit_acte_juridique"
    )
    
    # Actions
    st.markdown("#### 🎯 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        format_export = st.selectbox(
            "Format d'export",
            ["Word (.docx)", "PDF", "Texte (.txt)"],
            key="format_export_acte"
        )
    
    with col2:
        if st.button("📥 Télécharger", key="download_acte"):
            # Préparer l'export selon le format
            if format_export == "Word (.docx)":
                # TODO: Implémenter l'export Word avec python-docx
                file_content = contenu_edite.encode('utf-8')
                file_ext = "txt"  # Temporaire
                mime_type = "text/plain"
            elif format_export == "PDF":
                # TODO: Implémenter l'export PDF avec reportlab
                file_content = contenu_edite.encode('utf-8')
                file_ext = "txt"  # Temporaire
                mime_type = "text/plain"
            else:
                file_content = contenu_edite.encode('utf-8')
                file_ext = "txt"
                mime_type = "text/plain"
            
            st.download_button(
                "💾 Télécharger le fichier",
                file_content,
                f"{acte.type_acte}_{acte.metadata['date_creation'].strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                mime_type,
                key="download_final_acte"
            )
    
    with col3:
        if st.button("📧 Envoyer", key="send_acte"):
            st.info("Fonction d'envoi par email à implémenter")
    
    with col4:
        if st.button("🔄 Régénérer", key="regenerate_acte"):
            st.session_state.pop('acte_genere', None)
            st.session_state.pop('generation_result', None)
            st.rerun()
    
    # Analyse du style si disponible
    if hasattr(acte, 'metadata') and 'style_analysis' in acte.metadata:
        with st.expander("📊 Analyse du style"):
            analysis = acte.metadata['style_analysis']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Score de conformité", f"{analysis.get('conformity_score', 0):.0%}")
            with col2:
                st.metric("Complexité juridique", analysis.get('complexity', 'Normale'))

# ========================= EXPORT DES FONCTIONS =========================

__all__ = [
    'AnalyseurRequeteJuridique',
    'enhance_search_with_generation',
    'process_juridical_generation',
    'display_generated_acte'
]
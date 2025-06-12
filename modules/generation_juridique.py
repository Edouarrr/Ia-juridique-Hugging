"""Module de génération d'actes juridiques selon le cahier des charges"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass

# Import des managers nécessaires
try:
    from managers.llm_manager import get_llm_manager
    from managers.style_analyzer import StyleAnalyzer
    from managers.template_manager import TemplateManager
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# ========================= STRUCTURES DE DONNÉES =========================

@dataclass
class ActeJuridique:
    """Structure pour un acte juridique"""
    type_acte: str  # conclusions, plainte, assignation, etc.
    titre: str
    destinataire: str
    parties: Dict[str, List[str]]  # demandeurs, defendeurs
    infractions: List[str]
    contenu: str
    pieces: List[Dict]
    metadata: Dict

# ========================= TEMPLATES DE BASE =========================

TEMPLATES_ACTES = {
    "plainte_simple": {
        "structure": ["en_tete", "expose_faits", "qualification", "demande"],
        "style": "formel",
        "longueur_min": 2000
    },
    "plainte_cpc": {
        "structure": ["en_tete", "expose_faits", "discussion_juridique", "prejudices", "demandes"],
        "style": "exhaustif",
        "longueur_min": 8000
    },
    "conclusions_nullite": {
        "structure": ["in_limine_litis", "nullite_copj", "application", "dispositif"],
        "style": "technique",
        "longueur_min": 3000
    },
    "conclusions_fond": {
        "structure": ["faits_procedure", "discussion", "par_ces_motifs"],
        "style": "argumentatif",
        "longueur_min": 5000
    }
}

# ========================= STYLES ET MISE EN FORME =========================

STYLE_CONFIG = {
    "police": "Garamond",
    "taille_texte": 12,
    "taille_titre": 14,
    "hierarchie": {
        1: {"format": "I.", "style": "gras souligné"},
        2: {"format": "A.", "style": "gras souligné"},
        3: {"format": "1.", "style": "gras"},
        4: {"format": "a.", "style": "italique"},
        5: {"format": "(i)", "style": "italique"}
    }
}

FORMULES_POLITESSE = {
    "magistrat": "Je vous prie de croire, Monsieur le Juge, à l'expression de ma très haute considération.",
    "procureur": "Je vous prie d'agréer, Monsieur le Procureur de la République, l'expression de ma haute considération",
    "expert": "Je vous prie d'agréer, Monsieur l'Expert, l'expression de mes salutations distinguées.",
    "confrere": "Je vous prie de me croire. Votre bien dévoué Confrère"
}

# ========================= GÉNÉRATEUR PRINCIPAL =========================

class GenerateurActesJuridiques:
    """Générateur d'actes juridiques selon le cahier des charges"""
    
    def __init__(self):
        self.llm_manager = get_llm_manager() if LLM_AVAILABLE else None
        self.style_analyzer = StyleAnalyzer() if LLM_AVAILABLE else None
        self.current_phase = "enquete"  # enquete, instruction, jugement, appel
    
    def generer_acte(self, type_acte: str, params: Dict) -> ActeJuridique:
        """Génère un acte juridique complet"""
        
        # Vérifier le type d'acte
        if type_acte not in TEMPLATES_ACTES:
            raise ValueError(f"Type d'acte non reconnu : {type_acte}")
        
        # Préparer les données
        template = TEMPLATES_ACTES[type_acte]
        parties = self._preparer_parties(params.get('parties', {}))
        infractions = self._preparer_infractions(params.get('infractions', []))
        
        # Générer le contenu selon la structure
        contenu_sections = {}
        for section in template['structure']:
            contenu_sections[section] = self._generer_section(
                section, type_acte, parties, infractions, params
            )
        
        # Assembler l'acte
        contenu_final = self._assembler_acte(
            type_acte, contenu_sections, parties, params
        )
        
        # Appliquer le style Garamond et la mise en forme
        contenu_formate = self._appliquer_mise_en_forme(contenu_final)
        
        # Créer l'objet ActeJuridique
        acte = ActeJuridique(
            type_acte=type_acte,
            titre=self._generer_titre(type_acte, params),
            destinataire=self._determiner_destinataire(type_acte),
            parties=parties,
            infractions=infractions,
            contenu=contenu_formate,
            pieces=params.get('pieces', []),
            metadata={
                'date_creation': datetime.now(),
                'longueur_mots': len(contenu_formate.split()),
                'phase_procedure': self.current_phase
            }
        )
        
        return acte
    
    def _preparer_parties(self, parties_input: Dict) -> Dict[str, List[str]]:
        """Prépare et enrichit les informations des parties"""
        parties = {
            'demandeurs': [],
            'defendeurs': []
        }
        
        # Enrichir avec les informations sociétés si disponible
        for role, liste_parties in parties_input.items():
            for partie in liste_parties:
                if isinstance(partie, dict):
                    # Déjà enrichi
                    parties[role].append(partie)
                else:
                    # Enrichir si possible
                    partie_enrichie = self._enrichir_partie(partie)
                    parties[role].append(partie_enrichie)
        
        return parties
    
    def _enrichir_partie(self, nom_partie: str) -> Dict:
        """Enrichit les informations d'une partie (société)"""
        # TODO: Appeler l'API Pappers pour récupérer les infos
        return {
            'nom': nom_partie,
            'forme_juridique': '[À COMPLÉTER]',
            'siren': '[À COMPLÉTER]',
            'siege_social': '[À COMPLÉTER]',
            'representant': '[À COMPLÉTER]'
        }
    
    def _preparer_infractions(self, infractions_input: List[str]) -> List[str]:
        """Prépare la liste des infractions avec les articles de loi"""
        infractions_completes = []
        
        # Mapping infractions -> articles
        INFRACTIONS_MAPPING = {
            'abus de biens sociaux': 'Art. L. 241-3 et L. 242-6 du Code de commerce',
            'corruption': 'Art. 432-11 du Code pénal',
            'escroquerie': 'Art. 313-1 du Code pénal',
            'abus de confiance': 'Art. 314-1 du Code pénal',
            'blanchiment': 'Art. 324-1 du Code pénal'
        }
        
        for infraction in infractions_input:
            infraction_lower = infraction.lower()
            for key, article in INFRACTIONS_MAPPING.items():
                if key in infraction_lower:
                    infractions_completes.append(f"{infraction} ({article})")
                    break
            else:
                infractions_completes.append(infraction)
        
        return infractions_completes
    
    def _generer_section(self, section: str, type_acte: str, 
                        parties: Dict, infractions: List, params: Dict) -> str:
        """Génère une section spécifique de l'acte"""
        
        # Créer le prompt pour le LLM
        prompt = self._creer_prompt_section(
            section, type_acte, parties, infractions, params
        )
        
        if self.llm_manager:
            # Générer avec le LLM
            response = self.llm_manager.query_single_llm(
                provider="anthropic",  # ou autre selon config
                query=prompt,
                system_prompt="Tu es un avocat pénaliste français expert. Rédige dans un style juridique professionnel."
            )
            if response['success']:
                return response['response']
        
        # Fallback : template basique
        return self._generer_section_template(section, type_acte, parties, infractions)
    
    def _creer_prompt_section(self, section: str, type_acte: str,
                             parties: Dict, infractions: List, params: Dict) -> str:
        """Crée le prompt pour générer une section"""
        
        prompts_sections = {
            "en_tete": f"""
Rédige l'en-tête d'une {type_acte} en droit pénal français.
Destinataire : {self._determiner_destinataire(type_acte)}
Demandeurs : {', '.join([p['nom'] if isinstance(p, dict) else p for p in parties.get('demandeurs', [])])}
Défendeurs : {', '.join([p['nom'] if isinstance(p, dict) else p for p in parties.get('defendeurs', [])])}

Format attendu :
- Adresse au destinataire (centré, majuscules)
- Date et lieu
- Objet précis
- Identité complète des parties
""",
            "expose_faits": f"""
Rédige un exposé détaillé des faits pour une {type_acte}.
Contexte : {params.get('contexte', 'Affaire de droit pénal des affaires')}
Infractions suspectées : {', '.join(infractions)}

L'exposé doit être :
- Chronologique et précis
- Objectif (pas d'adjectifs superflus)
- Sourcé avec renvois aux pièces
- Entre 1000 et 2000 mots
""",
            "discussion_juridique": f"""
Rédige une discussion juridique approfondie sur les infractions suivantes :
{chr(10).join(['- ' + inf for inf in infractions])}

Pour CHAQUE infraction :
1. Rappel complet des textes applicables
2. Analyse détaillée des éléments constitutifs
3. Application aux faits de l'espèce
4. Jurisprudences pertinentes (au moins 3)
5. Réfutation des arguments contraires

Style : technique, précis, argumenté
Longueur : 2000-3000 mots minimum
""",
            "prejudices": """
Détaille les préjudices subis :
1. Préjudice financier (chiffré avec précision)
2. Préjudice moral (développé)
3. Préjudice d'image
4. Autres préjudices spécifiques

Chaque préjudice doit être :
- Justifié par les faits
- Évalué ou évaluable
- Appuyé par des pièces
""",
            "dispositif": f"""
Rédige le dispositif/les demandes pour une {type_acte}.
Phase procédurale : {self.current_phase}

Inclure :
- Demandes principales
- Demandes subsidiaires
- Demandes de mesures conservatoires si pertinent
- Formule de politesse adaptée
"""
        }
        
        return prompts_sections.get(section, f"Rédige la section {section} pour une {type_acte}")
    
    def _generer_section_template(self, section: str, type_acte: str,
                                 parties: Dict, infractions: List) -> str:
        """Génère une section avec un template basique (fallback)"""
        
        templates = {
            "en_tete": f"""
A MESDAMES ET/OU MESSIEURS LES PRÉSIDENT ET JUGES 
COMPOSANT LA [N]ᵉ CHAMBRE CORRECTIONNELLE 
DU TRIBUNAL JUDICIAIRE DE [VILLE]

[VILLE], le {datetime.now().strftime('%d/%m/%Y')}

POUR : [DEMANDEUR]
       [ADRESSE]
       
Ayant pour avocat : Me [NOM]
                   Avocat au Barreau de [VILLE]
                   
CONTRE : {', '.join([p['nom'] if isinstance(p, dict) else p for p in parties.get('defendeurs', [])])}
""",
            "expose_faits": """
PLAISE AU TRIBUNAL

I. EXPOSÉ DES FAITS

[DÉVELOPPEMENT CHRONOLOGIQUE DES FAITS]

Les faits de la présente affaire remontent à [DATE].

[SUITE DE L'EXPOSÉ - À COMPLÉTER]
""",
            "discussion_juridique": f"""
II. DISCUSSION JURIDIQUE

Les faits exposés caractérisent les infractions suivantes :

{chr(10).join(['- ' + inf for inf in infractions])}

A. SUR L'ABUS DE BIENS SOCIAUX

[DÉVELOPPEMENT JURIDIQUE - À COMPLÉTER]

B. [AUTRES INFRACTIONS]

[DÉVELOPPEMENT - À COMPLÉTER]
"""
        }
        
        return templates.get(section, f"[SECTION {section.upper()} - À COMPLÉTER]")
    
    def _assembler_acte(self, type_acte: str, sections: Dict[str, str],
                       parties: Dict, params: Dict) -> str:
        """Assemble toutes les sections en un acte complet"""
        
        # Ordre des sections selon le type d'acte
        ordre_sections = TEMPLATES_ACTES[type_acte]['structure']
        
        # Assembler
        contenu = []
        for i, section in enumerate(ordre_sections):
            if section in sections:
                # Ajouter la numérotation hiérarchique
                if i == 0:
                    contenu.append(sections[section])
                else:
                    numero = self._generer_numero_hierarchique(i, 1)
                    contenu.append(f"\n{numero} {section.upper().replace('_', ' ')}\n\n{sections[section]}")
        
        # Ajouter la conclusion
        contenu.append(self._generer_conclusion(type_acte, params))
        
        # Ajouter la liste des pièces
        if params.get('pieces'):
            contenu.append(self._generer_liste_pieces(params['pieces']))
        
        return '\n\n'.join(contenu)
    
    def _generer_numero_hierarchique(self, niveau: int, sous_niveau: int = 0) -> str:
        """Génère la numérotation hiérarchique selon le style"""
        numerotation = {
            1: lambda n: f"{self._roman(n)}.",
            2: lambda n: f"{chr(64 + n)}.",
            3: lambda n: f"{n}.",
            4: lambda n: f"{chr(96 + n)}.",
            5: lambda n: f"({self._roman(n).lower()})"
        }
        
        return numerotation.get(niveau, lambda n: f"{n}.")(sous_niveau or niveau)
    
    def _roman(self, num: int) -> str:
        """Convertit en chiffres romains"""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        roman_num = ''
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syms[i]
                num -= val[i]
            i += 1
        return roman_num
    
    def _appliquer_mise_en_forme(self, contenu: str) -> str:
        """Applique la mise en forme Garamond selon le cahier des charges"""
        
        # Marqueurs de style pour l'export
        contenu_formate = contenu
        
        # Remplacer les titres de niveau 1 (I., II., etc.)
        contenu_formate = re.sub(
            r'^(I{1,3}|IV|V|VI|VII|VIII|IX|X)\.\s+(.+)$',
            r'<h1 style="font-family: Garamond; font-size: 14pt; font-weight: bold; text-decoration: underline;">\1. \2</h1>',
            contenu_formate,
            flags=re.MULTILINE
        )
        
        # Remplacer les sous-titres (A., B., etc.)
        contenu_formate = re.sub(
            r'^([A-Z])\.\s+(.+)$',
            r'<h2 style="font-family: Garamond; font-size: 12pt; font-weight: bold; text-decoration: underline;">\1. \2</h2>',
            contenu_formate,
            flags=re.MULTILINE
        )
        
        # Ajouter les styles pour les pièces
        contenu_formate = re.sub(
            r'\(PIÈCE N° (\d+)\)',
            r'<span style="font-weight: bold; text-decoration: underline;">(PIÈCE N° \1)</span>',
            contenu_formate
        )
        
        return contenu_formate
    
    def _generer_conclusion(self, type_acte: str, params: Dict) -> str:
        """Génère la conclusion de l'acte"""
        
        destinataire_type = params.get('destinataire_type', 'magistrat')
        formule = FORMULES_POLITESSE.get(destinataire_type, FORMULES_POLITESSE['magistrat'])
        
        if type_acte == "plainte_cpc":
            conclusion = f"""
PAR CES MOTIFS

Il est demandé au Tribunal de :

- RECEVOIR la présente plainte avec constitution de partie civile ;
- ORDONNER l'ouverture d'une information judiciaire ;
- DIRE et JUGER que les faits constituent les infractions visées ;
- CONDAMNER les mis en cause aux peines prévues par la loi ;
- CONDAMNER solidairement les mis en cause à réparer le préjudice subi ;

Le tout sous réserve de tous autres droits et moyens.

{formule}

Fait à [VILLE], le {datetime.now().strftime('%d/%m/%Y')}

[SIGNATURE]
"""
        else:
            conclusion = f"""
SOUS TOUTES RÉSERVES

{formule}

Fait à [VILLE], le {datetime.now().strftime('%d/%m/%Y')}

[SIGNATURE]
"""
        
        return conclusion
    
    def _generer_liste_pieces(self, pieces: List[Dict]) -> str:
        """Génère la liste des pièces communiquées"""
        
        liste = "\n\nPIÈCES COMMUNIQUÉES :\n\n"
        
        for i, piece in enumerate(pieces, 1):
            titre = piece.get('titre', f'Pièce {i}')
            date = piece.get('date', '')
            liste += f"Pièce n° {i} : {titre}"
            if date:
                liste += f" - {date}"
            liste += "\n"
        
        return liste
    
    def _determiner_destinataire(self, type_acte: str) -> str:
        """Détermine le destinataire selon le type d'acte"""
        
        destinataires = {
            'plainte_simple': 'Monsieur le Procureur de la République',
            'plainte_cpc': 'Monsieur le Doyen des Juges d\'Instruction',
            'conclusions': 'le Tribunal',
            'assignation': 'le Tribunal',
            'citation_directe': 'le Tribunal'
        }
        
        return destinataires.get(type_acte, 'le Tribunal')
    
    def exporter_acte(self, acte: ActeJuridique, format: str = 'docx') -> bytes:
        """Exporte l'acte dans le format demandé"""
        
        if format == 'docx':
            return self._exporter_docx(acte)
        elif format == 'pdf':
            return self._exporter_pdf(acte)
        else:
            return acte.contenu.encode('utf-8')
    
    def _exporter_docx(self, acte: ActeJuridique) -> bytes:
        """Exporte en format Word avec mise en forme Garamond"""
        # TODO: Implémenter avec python-docx
        return acte.contenu.encode('utf-8')
    
    def _exporter_pdf(self, acte: ActeJuridique) -> bytes:
        """Exporte en format PDF avec mise en forme"""
        # TODO: Implémenter avec reportlab
        return acte.contenu.encode('utf-8')

# ========================= INTERFACE STREAMLIT =========================

def show_page():
    """Page principale du module de génération juridique"""
    
    st.markdown("## ⚖️ Générateur d'Actes Juridiques")
    
    # Initialiser le générateur
    if 'generateur_juridique' not in st.session_state:
        st.session_state.generateur_juridique = GenerateurActesJuridiques()
    
    generateur = st.session_state.generateur_juridique
    
    # Sélection du type d'acte
    col1, col2 = st.columns([2, 1])
    
    with col1:
        type_acte = st.selectbox(
            "Type d'acte à générer",
            options=list(TEMPLATES_ACTES.keys()),
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    with col2:
        phase = st.selectbox(
            "Phase procédurale",
            ["Enquête préliminaire", "Instruction", "Jugement", "Appel"]
        )
        generateur.current_phase = phase.lower().split()[0]
    
    # Configuration des parties
    st.markdown("### 👥 Parties")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Demandeurs / Plaignants**")
        demandeurs = st.text_area(
            "Un par ligne",
            height=100,
            key="demandeurs_gen",
            placeholder="Société X\nM. Y"
        ).split('\n')
        demandeurs = [d.strip() for d in demandeurs if d.strip()]
    
    with col2:
        st.markdown("**Défendeurs / Mis en cause**")
        defendeurs = st.text_area(
            "Un par ligne", 
            height=100,
            key="defendeurs_gen",
            placeholder="Société Z\nMme W"
        ).split('\n')
        defendeurs = [d.strip() for d in defendeurs if d.strip()]
    
    # Configuration des infractions
    st.markdown("### 🚨 Infractions")
    
    infractions_predefinies = [
        "Abus de biens sociaux",
        "Corruption",
        "Escroquerie", 
        "Abus de confiance",
        "Blanchiment",
        "Faux et usage de faux",
        "Détournement de fonds publics"
    ]
    
    infractions = st.multiselect(
        "Sélectionner les infractions",
        infractions_predefinies,
        key="infractions_gen"
    )
    
    # Infractions personnalisées
    infractions_custom = st.text_input(
        "Autres infractions (séparées par des virgules)",
        key="infractions_custom"
    )
    
    if infractions_custom:
        infractions.extend([i.strip() for i in infractions_custom.split(',')])
    
    # Contexte et options
    with st.expander("⚙️ Options avancées", expanded=False):
        contexte = st.text_area(
            "Contexte de l'affaire",
            height=150,
            placeholder="Décrivez brièvement le contexte..."
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            inclure_chronologie = st.checkbox("Chronologie détaillée", value=True)
        
        with col2:
            inclure_jurisprudence = st.checkbox("Citations jurisprudentielles", value=True)
        
        with col3:
            verification_pappers = st.checkbox("Vérifier sociétés (Pappers)", value=True)
    
    # Sélection des pièces
    st.markdown("### 📎 Pièces à communiquer")
    
    pieces = []
    if st.checkbox("Ajouter des pièces"):
        nb_pieces = st.number_input("Nombre de pièces", min_value=1, max_value=50, value=5)
        
        for i in range(nb_pieces):
            col1, col2 = st.columns([3, 1])
            with col1:
                titre = st.text_input(f"Pièce {i+1}", key=f"piece_titre_{i}")
            with col2:
                date = st.date_input(f"Date", key=f"piece_date_{i}")
            
            if titre:
                pieces.append({'titre': titre, 'date': date.strftime('%d/%m/%Y')})
    
    # Bouton de génération
    if st.button("🚀 Générer l'acte", type="primary", use_container_width=True):
        
        if not (demandeurs or defendeurs):
            st.error("Veuillez renseigner au moins une partie")
            return
        
        if not infractions:
            st.error("Veuillez sélectionner au moins une infraction")
            return
        
        # Préparer les paramètres
        params = {
            'parties': {
                'demandeurs': demandeurs,
                'defendeurs': defendeurs
            },
            'infractions': infractions,
            'contexte': contexte,
            'pieces': pieces,
            'options': {
                'inclure_chronologie': inclure_chronologie,
                'inclure_jurisprudence': inclure_jurisprudence,
                'verification_pappers': verification_pappers
            }
        }
        
        # Générer l'acte
        with st.spinner("⏳ Génération en cours... Cela peut prendre 1-2 minutes"):
            try:
                acte = generateur.generer_acte(type_acte, params)
                st.session_state.acte_genere = acte
                st.success("✅ Acte généré avec succès !")
                
                # Afficher les statistiques
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Mots", f"{acte.metadata['longueur_mots']:,}")
                with col2:
                    st.metric("Pages estimées", f"~{acte.metadata['longueur_mots'] // 250}")
                with col3:
                    st.metric("Pièces", len(acte.pieces))
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération : {str(e)}")
    
    # Afficher l'acte généré
    if 'acte_genere' in st.session_state:
        acte = st.session_state.acte_genere
        
        st.markdown("---")
        st.markdown(f"### 📄 {acte.titre}")
        
        # Zone d'édition
        contenu_edite = st.text_area(
            "Contenu de l'acte",
            value=acte.contenu,
            height=600,
            key="contenu_acte_edit"
        )
        
        # Actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            format_export = st.selectbox("Format", ["DOCX", "PDF", "TXT"])
        
        with col2:
            if st.button("📥 Télécharger"):
                # Exporter dans le format choisi
                export_data = generateur.exporter_acte(acte, format_export.lower())
                st.download_button(
                    "💾 Télécharger",
                    export_data,
                    f"{acte.type_acte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_export.lower()}",
                    key="download_acte"
                )
        
        with col3:
            if st.button("📧 Envoyer"):
                st.info("Fonction d'envoi à implémenter")
        
        with col4:
            if st.button("🔄 Régénérer"):
                st.session_state.pop('acte_genere', None)
                st.rerun()

# ========================= INTÉGRATION AVEC RECHERCHE =========================

def process_generation_request(query: str, analysis: Any):
    """Traite une demande de génération depuis le module de recherche"""
    
    # Extraire les paramètres de la requête
    params = extract_generation_params(query, analysis)
    
    # Déterminer le type d'acte
    type_acte = determine_acte_type(query)
    
    # Créer le générateur
    generateur = GenerateurActesJuridiques()
    
    # Générer l'acte
    acte = generateur.generer_acte(type_acte, params)
    
    return acte

def extract_generation_params(query: str, analysis: Any) -> Dict:
    """Extrait les paramètres de génération depuis la requête"""
    
    params = {
        'parties': {},
        'infractions': [],
        'contexte': '',
        'pieces': []
    }
    
    # Extraire depuis l'analyse si disponible
    if hasattr(analysis, 'parties'):
        params['parties'] = analysis.parties
    
    if hasattr(analysis, 'infractions'):
        params['infractions'] = analysis.infractions
    
    if hasattr(analysis, 'reference'):
        params['contexte'] = f"Affaire {analysis.reference}"
    
    return params

def determine_acte_type(query: str) -> str:
    """Détermine le type d'acte à générer"""
    
    query_lower = query.lower()
    
    if 'plainte' in query_lower:
        if 'partie civile' in query_lower or 'cpc' in query_lower:
            return 'plainte_cpc'
        else:
            return 'plainte_simple'
    elif 'conclusions' in query_lower:
        if 'nullité' in query_lower:
            return 'conclusions_nullite'
        else:
            return 'conclusions_fond'
    elif 'assignation' in query_lower:
        return 'assignation'
    elif 'citation' in query_lower:
        return 'citation_directe'
    else:
        return 'plainte_simple'  # Par défaut

if __name__ == "__main__":
    show_page()
"""Module unifié de génération et rédaction d'actes juridiques avec IA"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
import re
import json
import io
from dataclasses import dataclass, field
from enum import Enum
import base64

# ========================= ENUMS ET CONFIGURATIONS =========================

class TypeActe(Enum):
    """Types d'actes juridiques disponibles"""
    PLAINTE_SIMPLE = "plainte_simple"
    PLAINTE_CPC = "plainte_cpc"
    CONCLUSIONS_NULLITE = "conclusions_nullite"
    CONCLUSIONS_FOND = "conclusions_fond"
    ASSIGNATION = "assignation"
    CITATION_DIRECTE = "citation_directe"
    REQUETE = "requete"
    MEMOIRE = "memoire"

class StyleRedaction(Enum):
    """Styles de rédaction disponibles"""
    FORMEL = "formel"
    MODERNE = "moderne"
    TECHNIQUE = "technique"
    ARGUMENTATIF = "argumentatif"
    EXHAUSTIF = "exhaustif"

class PhaseProcedurale(Enum):
    """Phases de la procédure"""
    ENQUETE = "enquête"
    INSTRUCTION = "instruction"
    JUGEMENT = "jugement"
    APPEL = "appel"
    CASSATION = "cassation"

# ========================= STRUCTURES DE DONNÉES =========================

@dataclass
class Partie:
    """Représente une partie dans une procédure"""
    nom: str
    type_partie: str  # demandeur, defendeur, intervenant
    qualite: str = ""  # personne physique, société, association
    adresse: str = ""
    forme_juridique: str = ""
    siren: str = ""
    representant: str = ""
    avocat: str = ""
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v}

@dataclass
class Infraction:
    """Représente une infraction pénale"""
    nom: str
    articles: List[str] = field(default_factory=list)
    elements_constitutifs: List[str] = field(default_factory=list)
    jurisprudences: List[str] = field(default_factory=list)
    peines_encourues: str = ""

@dataclass
class Piece:
    """Représente une pièce jointe"""
    numero: int
    titre: str
    date: Optional[datetime] = None
    description: str = ""
    categorie: str = ""  # contrat, facture, courrier, etc.

@dataclass
class ActeJuridique:
    """Structure complète pour un acte juridique"""
    type_acte: TypeActe
    titre: str
    destinataire: str
    parties: Dict[str, List[Partie]]
    infractions: List[Infraction]
    pieces: List[Piece]
    contenu: str
    metadata: Dict[str, Any]
    style: StyleRedaction = StyleRedaction.FORMEL
    phase: PhaseProcedurale = PhaseProcedurale.ENQUETE
    
    def get_word_count(self) -> int:
        """Retourne le nombre de mots"""
        return len(self.contenu.split())
    
    def get_page_estimate(self) -> int:
        """Estime le nombre de pages"""
        return max(1, self.get_word_count() // 250)

# ========================= TEMPLATES ET CONFIGURATIONS =========================

# Templates détaillés par type d'acte
TEMPLATES_DETAILLES = {
    TypeActe.PLAINTE_SIMPLE: {
        "structure": [
            {"section": "en_tete", "titre": "En-tête", "obligatoire": True},
            {"section": "expose_faits", "titre": "Exposé des faits", "obligatoire": True},
            {"section": "qualification", "titre": "Qualification juridique", "obligatoire": True},
            {"section": "demande", "titre": "Demandes", "obligatoire": True}
        ],
        "style_defaut": StyleRedaction.FORMEL,
        "longueur_min": 2000,
        "longueur_cible": 3000,
        "destinataire": "Monsieur le Procureur de la République"
    },
    TypeActe.PLAINTE_CPC: {
        "structure": [
            {"section": "en_tete", "titre": "En-tête", "obligatoire": True},
            {"section": "expose_faits", "titre": "Exposé circonstancié des faits", "obligatoire": True},
            {"section": "discussion_juridique", "titre": "Discussion juridique approfondie", "obligatoire": True},
            {"section": "prejudices", "titre": "Préjudices subis", "obligatoire": True},
            {"section": "demandes", "titre": "Demandes", "obligatoire": True},
            {"section": "constitution", "titre": "Constitution de partie civile", "obligatoire": True}
        ],
        "style_defaut": StyleRedaction.EXHAUSTIF,
        "longueur_min": 8000,
        "longueur_cible": 12000,
        "destinataire": "Monsieur le Doyen des Juges d'Instruction"
    },
    TypeActe.CONCLUSIONS_NULLITE: {
        "structure": [
            {"section": "in_limine_litis", "titre": "In limine litis", "obligatoire": True},
            {"section": "nullite_citation", "titre": "Sur la nullité de la citation", "obligatoire": False},
            {"section": "nullite_procedure", "titre": "Sur les nullités de procédure", "obligatoire": True},
            {"section": "application_espece", "titre": "Application à l'espèce", "obligatoire": True},
            {"section": "dispositif", "titre": "Dispositif", "obligatoire": True}
        ],
        "style_defaut": StyleRedaction.TECHNIQUE,
        "longueur_min": 3000,
        "longueur_cible": 5000,
        "destinataire": "le Tribunal"
    },
    TypeActe.CONCLUSIONS_FOND: {
        "structure": [
            {"section": "rappel_faits", "titre": "Rappel des faits et de la procédure", "obligatoire": True},
            {"section": "discussion", "titre": "Discussion", "obligatoire": True},
            {"section": "sur_infraction_1", "titre": "Sur la première infraction", "obligatoire": False},
            {"section": "sur_infraction_2", "titre": "Sur la deuxième infraction", "obligatoire": False},
            {"section": "sur_relaxe", "titre": "Sur la demande de relaxe", "obligatoire": False},
            {"section": "par_ces_motifs", "titre": "Par ces motifs", "obligatoire": True}
        ],
        "style_defaut": StyleRedaction.ARGUMENTATIF,
        "longueur_min": 5000,
        "longueur_cible": 8000,
        "destinataire": "le Tribunal"
    }
}

# Base de données des infractions
INFRACTIONS_DB = {
    "abus de biens sociaux": {
        "articles": ["L. 241-3 du Code de commerce", "L. 242-6 du Code de commerce"],
        "elements": [
            "Usage des biens ou du crédit de la société",
            "Contraire à l'intérêt social",
            "À des fins personnelles ou favoriser une autre société",
            "Mauvaise foi"
        ],
        "peines": "5 ans d'emprisonnement et 375 000 euros d'amende"
    },
    "corruption": {
        "articles": ["432-11 du Code pénal", "433-1 du Code pénal"],
        "elements": [
            "Sollicitation ou agrément d'offres",
            "Dons, promesses ou avantages",
            "Pour accomplir ou s'abstenir d'accomplir un acte",
            "Acte de sa fonction"
        ],
        "peines": "10 ans d'emprisonnement et 1 000 000 euros d'amende"
    },
    "escroquerie": {
        "articles": ["313-1 du Code pénal"],
        "elements": [
            "Usage de faux nom ou fausse qualité",
            "Manœuvres frauduleuses",
            "Remise de fonds, valeurs ou biens",
            "Préjudice d'autrui"
        ],
        "peines": "5 ans d'emprisonnement et 375 000 euros d'amende"
    },
    "abus de confiance": {
        "articles": ["314-1 du Code pénal"],
        "elements": [
            "Détournement",
            "Fonds, valeurs ou biens remis",
            "À charge de restitution ou usage déterminé",
            "Préjudice d'autrui"
        ],
        "peines": "3 ans d'emprisonnement et 375 000 euros d'amende"
    },
    "blanchiment": {
        "articles": ["324-1 du Code pénal"],
        "elements": [
            "Faciliter la justification mensongère",
            "Produit d'un crime ou délit",
            "Concours à une opération de placement",
            "Dissimulation ou conversion"
        ],
        "peines": "5 ans d'emprisonnement et 375 000 euros d'amende"
    }
}

# Formules de politesse selon le destinataire
FORMULES_POLITESSE = {
    "magistrat": "Je vous prie de croire, Monsieur le Juge, à l'expression de ma très haute considération.",
    "procureur": "Je vous prie d'agréer, Monsieur le Procureur de la République, l'expression de ma haute considération.",
    "doyen": "Je vous prie d'agréer, Monsieur le Doyen, l'expression de ma haute considération.",
    "expert": "Je vous prie d'agréer, Monsieur l'Expert, l'expression de mes salutations distinguées.",
    "confrere": "Je vous prie de me croire, Votre bien dévoué Confrère.",
    "tribunal": "Sous toutes réserves."
}

# ========================= GÉNÉRATEUR PRINCIPAL =========================

class GenerateurActesJuridiques:
    """Générateur avancé d'actes juridiques"""
    
    def __init__(self):
        self.llm_manager = None
        self.style_analyzer = None
        self._init_managers()
        
    def _init_managers(self):
        """Initialise les managers si disponibles"""
        try:
            from managers.llm_manager import get_llm_manager
            self.llm_manager = get_llm_manager()
        except:
            pass
            
        try:
            from managers.style_analyzer import StyleAnalyzer
            self.style_analyzer = StyleAnalyzer()
        except:
            pass
    
    def generer_acte_complet(
        self,
        type_acte: TypeActe,
        parties: Dict[str, List[Partie]],
        infractions: List[str],
        contexte: str,
        pieces: List[Piece],
        style: StyleRedaction,
        phase: PhaseProcedurale,
        options: Dict[str, Any]
    ) -> ActeJuridique:
        """Génère un acte juridique complet avec toutes les sections"""
        
        # Récupérer le template
        template = TEMPLATES_DETAILLES[type_acte]
        
        # Enrichir les infractions
        infractions_completes = self._enrichir_infractions(infractions)
        
        # Générer chaque section
        sections = {}
        for section_config in template["structure"]:
            if section_config["obligatoire"] or self._section_necessaire(section_config, infractions_completes):
                contenu = self._generer_section_intelligente(
                    section_config["section"],
                    type_acte,
                    parties,
                    infractions_completes,
                    contexte,
                    style,
                    options
                )
                sections[section_config["section"]] = {
                    "titre": section_config["titre"],
                    "contenu": contenu
                }
        
        # Assembler l'acte
        contenu_final = self._assembler_acte_structure(
            type_acte, sections, parties, pieces, style
        )
        
        # Créer l'objet ActeJuridique
        acte = ActeJuridique(
            type_acte=type_acte,
            titre=self._generer_titre_intelligent(type_acte, parties, phase),
            destinataire=template["destinataire"],
            parties=parties,
            infractions=infractions_completes,
            pieces=pieces,
            contenu=contenu_final,
            metadata={
                'date_creation': datetime.now(),
                'longueur_mots': len(contenu_final.split()),
                'phase': phase.value,
                'style': style.value,
                'options': options
            },
            style=style,
            phase=phase
        )
        
        return acte
    
    def _enrichir_infractions(self, infractions_noms: List[str]) -> List[Infraction]:
        """Enrichit les infractions avec les informations légales"""
        infractions_completes = []
        
        for nom in infractions_noms:
            nom_lower = nom.lower()
            
            # Chercher dans la base de données
            infraction_data = None
            for key, data in INFRACTIONS_DB.items():
                if key in nom_lower:
                    infraction_data = data
                    break
            
            if infraction_data:
                infraction = Infraction(
                    nom=nom,
                    articles=infraction_data["articles"],
                    elements_constitutifs=infraction_data["elements"],
                    peines_encourues=infraction_data["peines"]
                )
            else:
                # Infraction personnalisée
                infraction = Infraction(nom=nom)
            
            infractions_completes.append(infraction)
        
        return infractions_completes
    
    def _section_necessaire(self, section_config: Dict, infractions: List[Infraction]) -> bool:
        """Détermine si une section optionnelle est nécessaire"""
        section = section_config["section"]
        
        # Logique pour déterminer si une section est nécessaire
        if section.startswith("sur_infraction_"):
            num = int(section.split("_")[-1])
            return len(infractions) >= num
        
        if section == "nullite_citation":
            return st.session_state.get('invoquer_nullite_citation', False)
        
        if section == "sur_relaxe":
            return st.session_state.get('demander_relaxe', False)
        
        return True
    
    def _generer_section_intelligente(
        self,
        section: str,
        type_acte: TypeActe,
        parties: Dict[str, List[Partie]],
        infractions: List[Infraction],
        contexte: str,
        style: StyleRedaction,
        options: Dict[str, Any]
    ) -> str:
        """Génère une section avec IA ou template intelligent"""
        
        # Essayer avec l'IA si disponible
        if self.llm_manager and options.get('utiliser_ia', True):
            prompt = self._creer_prompt_section_avance(
                section, type_acte, parties, infractions, contexte, style, options
            )
            
            try:
                response = self.llm_manager.query_single_llm(
                    provider="anthropic",
                    query=prompt,
                    system_prompt=self._get_system_prompt(style)
                )
                
                if response.get('success'):
                    return response['response']
            except:
                pass
        
        # Fallback vers template intelligent
        return self._generer_template_intelligent(
            section, type_acte, parties, infractions, contexte, style
        )
    
    def _creer_prompt_section_avance(
        self,
        section: str,
        type_acte: TypeActe,
        parties: Dict[str, List[Partie]],
        infractions: List[Infraction],
        contexte: str,
        style: StyleRedaction,
        options: Dict[str, Any]
    ) -> str:
        """Crée un prompt détaillé pour la génération IA"""
        
        # Contexte général
        prompt = f"""Tu es un avocat pénaliste français expert avec 20 ans d'expérience.
Tu rédiges la section '{section}' d'un(e) {type_acte.value.replace('_', ' ')}.

CONTEXTE:
{contexte}

PARTIES:
Demandeurs: {', '.join([p.nom for p in parties.get('demandeurs', [])])}
Défendeurs: {', '.join([p.nom for p in parties.get('defendeurs', [])])}

STYLE: {style.value} - {self._get_style_description(style)}
"""
        
        # Prompts spécifiques par section
        if section == "en_tete":
            prompt += f"""
Rédige un en-tête complet et formel comprenant:
1. L'adresse au destinataire ({TEMPLATES_DETAILLES[type_acte]['destinataire']})
2. La date et le lieu
3. L'objet précis de l'acte
4. L'identité complète des parties avec leurs qualités
5. Les avocats si mentionnés

Format attendu: en-tête juridique français classique
"""
        
        elif section == "expose_faits":
            prompt += f"""
Rédige un exposé des faits {'circonstancié et exhaustif' if type_acte == TypeActe.PLAINTE_CPC else 'clair et chronologique'}.

Intègre:
- Une chronologie précise des événements
- Les montants et dates exacts (à préciser avec [DATE] et [MONTANT])
- Les références aux pièces (PIÈCE N° X)
- {'Un niveau de détail très élevé' if style == StyleRedaction.EXHAUSTIF else 'Les faits essentiels'}

Longueur: {'2000-3000 mots' if type_acte == TypeActe.PLAINTE_CPC else '800-1200 mots'}
"""
        
        elif section == "discussion_juridique":
            prompt += f"""
Rédige une discussion juridique {'approfondie et exhaustive' if style == StyleRedaction.EXHAUSTIF else 'précise et argumentée'} sur:

INFRACTIONS À ANALYSER:
{self._format_infractions_pour_prompt(infractions)}

Pour CHAQUE infraction, développe:
1. Les textes applicables (cités intégralement)
2. Les éléments constitutifs (analyse détaillée)
3. L'application aux faits de l'espèce
4. La jurisprudence pertinente (au moins 3 arrêts)
5. {'La réfutation anticipée des arguments adverses' if options.get('anticiper_defense', True) else ''}

Utilise des sous-titres clairs (A., B., etc.)
Longueur minimale: {'3000 mots' if style == StyleRedaction.EXHAUSTIF else '1500 mots'}
"""
        
        elif section == "prejudices":
            prompt += f"""
Détaille tous les préjudices subis:

1. PRÉJUDICE FINANCIER
   - Montant principal: [À CHIFFRER]
   - Intérêts et pénalités
   - Manque à gagner
   
2. PRÉJUDICE MORAL
   - Impact psychologique
   - Atteinte à la réputation
   - Trouble dans les conditions d'existence
   
3. PRÉJUDICE D'IMAGE/COMMERCIAL
   - Perte de clientèle
   - Atteinte à la notoriété
   
Chaque préjudice doit être:
- Justifié par les faits
- Chiffré ou évaluable
- Référencé aux pièces justificatives
"""
        
        elif section == "dispositif" or section == "par_ces_motifs":
            prompt += f"""
Rédige le dispositif final avec:

PAR CES MOTIFS,

{'Plaise au Tribunal de:' if type_acte.value.startswith('conclusions') else 'Il est demandé de:'}

- DIRE ET JUGER que [demandes principales sur la culpabilité]
- CONDAMNER [demandes sur les peines]
- CONDAMNER [demandes sur les dommages-intérêts]
{'- ORDONNER [mesures complémentaires]' if options.get('mesures_complementaires', False) else ''}

Le tout sous réserve de tous autres droits et moyens.

Formule de politesse adaptée: {FORMULES_POLITESSE.get(self._get_destinataire_type(type_acte), FORMULES_POLITESSE['tribunal'])}
"""
        
        return prompt
    
    def _get_style_description(self, style: StyleRedaction) -> str:
        """Retourne la description du style de rédaction"""
        descriptions = {
            StyleRedaction.FORMEL: "Style juridique traditionnel, phrases complexes, vocabulaire soutenu",
            StyleRedaction.MODERNE: "Style plus direct, phrases plus courtes, reste professionnel",
            StyleRedaction.TECHNIQUE: "Ultra-précis, citations nombreuses, rigueur maximale",
            StyleRedaction.ARGUMENTATIF: "Persuasif, structuré, anticipation des contre-arguments",
            StyleRedaction.EXHAUSTIF: "Très détaillé, aucun élément omis, développements complets"
        }
        return descriptions.get(style, "Style juridique professionnel")
    
    def _get_system_prompt(self, style: StyleRedaction) -> str:
        """Retourne le prompt système selon le style"""
        base_prompt = """Tu es un avocat pénaliste français expert avec 20 ans d'expérience.
Tu maîtrises parfaitement:
- Le Code pénal et le Code de procédure pénale
- La jurisprudence de la Cour de cassation
- Les techniques de rédaction juridique
- La stratégie contentieuse pénale"""
        
        style_additions = {
            StyleRedaction.FORMEL: "\nTu rédiges dans un style très formel, avec un vocabulaire juridique soutenu.",
            StyleRedaction.MODERNE: "\nTu rédiges dans un style clair et moderne, accessible mais professionnel.",
            StyleRedaction.TECHNIQUE: "\nTu rédiges avec une précision technique maximale, multipliant les références.",
            StyleRedaction.ARGUMENTATIF: "\nTu rédiges de manière très persuasive, anticipant les contre-arguments.",
            StyleRedaction.EXHAUSTIF: "\nTu rédiges de manière exhaustive, sans omettre aucun détail pertinent."
        }
        
        return base_prompt + style_additions.get(style, "")
    
    def _format_infractions_pour_prompt(self, infractions: List[Infraction]) -> str:
        """Formate les infractions pour le prompt"""
        result = []
        for i, inf in enumerate(infractions, 1):
            txt = f"{i}. {inf.nom}"
            if inf.articles:
                txt += f"\n   Articles: {', '.join(inf.articles)}"
            if inf.elements_constitutifs:
                txt += f"\n   Éléments: {', '.join(inf.elements_constitutifs)}"
            result.append(txt)
        return '\n'.join(result)
    
    def _generer_template_intelligent(
        self,
        section: str,
        type_acte: TypeActe,
        parties: Dict[str, List[Partie]],
        infractions: List[Infraction],
        contexte: str,
        style: StyleRedaction
    ) -> str:
        """Génère une section avec un template intelligent (sans IA)"""
        
        # Templates par section
        if section == "en_tete":
            destinataire = TEMPLATES_DETAILLES[type_acte]["destinataire"]
            demandeurs_str = self._format_parties_list(parties.get('demandeurs', []))
            defendeurs_str = self._format_parties_list(parties.get('defendeurs', []))
            
            return f"""À {destinataire.upper()}
{self._get_tribunal_adresse()}

{self._get_ville_utilisateur()}, le {datetime.now().strftime('%d %B %Y')}

POUR : {demandeurs_str}

Ayant pour avocat : Me [NOM AVOCAT]
                    Avocat au Barreau de {self._get_ville_utilisateur()}
                    [ADRESSE CABINET]

CONTRE : {defendeurs_str}

OBJET : {self._generer_objet_acte(type_acte, infractions)}
"""
        
        elif section == "expose_faits":
            intro = "PLAISE AU TRIBUNAL,\n\n" if type_acte.value.startswith("conclusions") else ""
            
            return f"""{intro}I. EXPOSÉ DES FAITS

Les faits de la présente affaire remontent à [DATE DÉBUT].

{contexte if contexte else "[EXPOSÉ CHRONOLOGIQUE DES FAITS]"}

[DÉVELOPPEMENT DES FAITS AVEC RÉFÉRENCES AUX PIÈCES]

Il résulte de ces éléments que les agissements de {self._get_premier_defendeur(parties)} caractérisent les infractions qui seront analysées ci-après.
"""
        
        elif section == "discussion_juridique":
            contenu = "II. DISCUSSION JURIDIQUE\n\n"
            
            for i, infraction in enumerate(infractions, 1):
                lettre = chr(64 + i)  # A, B, C...
                contenu += f"{lettre}. SUR {infraction.nom.upper()}\n\n"
                
                # Textes applicables
                if infraction.articles:
                    contenu += f"L'infraction de {infraction.nom} est prévue et réprimée par les articles {', '.join(infraction.articles)}.\n\n"
                
                # Éléments constitutifs
                if infraction.elements_constitutifs:
                    contenu += "Cette infraction suppose la réunion des éléments constitutifs suivants :\n"
                    for elem in infraction.elements_constitutifs:
                        contenu += f"- {elem}\n"
                    contenu += "\n"
                
                # Application à l'espèce
                contenu += "En l'espèce, [APPLICATION DES ÉLÉMENTS AUX FAITS]\n\n"
                
                # Jurisprudence
                contenu += "La jurisprudence est constante sur ce point :\n"
                contenu += "- Cass. crim., [DATE], n° [NUMÉRO] : [PRINCIPE]\n"
                contenu += "- Cass. crim., [DATE], n° [NUMÉRO] : [PRINCIPE]\n\n"
            
            return contenu
        
        elif section == "prejudices":
            return """III. SUR LES PRÉJUDICES SUBIS

A. PRÉJUDICE FINANCIER

Le préjudice financier direct s'élève à [MONTANT] euros, correspondant à :
- [DÉTAIL 1] : [MONTANT] euros (PIÈCE N° X)
- [DÉTAIL 2] : [MONTANT] euros (PIÈCE N° Y)

B. PRÉJUDICE MORAL

Au-delà du préjudice financier, [PARTIE] a subi un préjudice moral considérable :
- [DESCRIPTION DU PRÉJUDICE MORAL]
- [IMPACT PSYCHOLOGIQUE]

Ce préjudice sera évalué par le Tribunal.

C. PRÉJUDICE D'IMAGE

[SI SOCIÉTÉ : DÉVELOPPEMENT SUR LE PRÉJUDICE D'IMAGE]
"""
        
        elif section == "dispositif" or section == "par_ces_motifs":
            return f"""PAR CES MOTIFS,

{'Plaise au Tribunal de :' if type_acte.value.startswith('conclusions') else 'Il est demandé de :'}

- {'RECEVOIR' if type_acte == TypeActe.PLAINTE_CPC else 'DIRE ET JUGER'} [DEMANDE PRINCIPALE]

- CONDAMNER [DÉFENDEUR] pour les faits de {', '.join([i.nom for i in infractions])}

- CONDAMNER [DÉFENDEUR] à payer à [DEMANDEUR] :
  * La somme de [MONTANT] euros au titre du préjudice financier
  * La somme de [MONTANT] euros au titre du préjudice moral
  * La somme de [MONTANT] euros au titre de l'article 475-1 du Code de procédure pénale

- ORDONNER l'exécution provisoire du jugement à intervenir

Le tout sous réserve de tous autres droits, moyens et instances.

{FORMULES_POLITESSE.get(self._get_destinataire_type(type_acte), FORMULES_POLITESSE['tribunal'])}

Fait à {self._get_ville_utilisateur()}, le {datetime.now().strftime('%d %B %Y')}

[SIGNATURE]
"""
        
        return f"[SECTION {section.upper()} - À COMPLÉTER]"
    
    def _format_parties_list(self, parties: List[Partie]) -> str:
        """Formate une liste de parties pour l'affichage"""
        if not parties:
            return "[PARTIES À DÉFINIR]"
        
        formatted = []
        for partie in parties:
            txt = partie.nom
            if partie.forme_juridique:
                txt += f", {partie.forme_juridique}"
            if partie.siren:
                txt += f", SIREN {partie.siren}"
            if partie.adresse:
                txt += f"\n        {partie.adresse}"
            if partie.representant:
                txt += f"\n        Représentée par {partie.representant}"
            formatted.append(txt)
        
        return "\n        ".join(formatted)
    
    def _get_tribunal_adresse(self) -> str:
        """Retourne l'adresse du tribunal"""
        ville = self._get_ville_utilisateur()
        return f"""TRIBUNAL JUDICIAIRE DE {ville.upper()}
[ADRESSE DU TRIBUNAL]"""
    
    def _get_ville_utilisateur(self) -> str:
        """Retourne la ville de l'utilisateur"""
        return st.session_state.get('ville_utilisateur', 'PARIS')
    
    def _generer_objet_acte(self, type_acte: TypeActe, infractions: List[Infraction]) -> str:
        """Génère l'objet de l'acte"""
        infractions_str = ", ".join([i.nom for i in infractions[:2]])
        if len(infractions) > 2:
            infractions_str += " et autres"
        
        objets = {
            TypeActe.PLAINTE_SIMPLE: f"Plainte pour {infractions_str}",
            TypeActe.PLAINTE_CPC: f"Plainte avec constitution de partie civile pour {infractions_str}",
            TypeActe.CONCLUSIONS_NULLITE: "Conclusions aux fins de nullité",
            TypeActe.CONCLUSIONS_FOND: f"Conclusions au fond - {infractions_str}",
            TypeActe.ASSIGNATION: f"Assignation devant le Tribunal correctionnel pour {infractions_str}",
            TypeActe.CITATION_DIRECTE: f"Citation directe pour {infractions_str}"
        }
        
        return objets.get(type_acte, f"Acte relatif à {infractions_str}")
    
    def _get_premier_defendeur(self, parties: Dict[str, List[Partie]]) -> str:
        """Retourne le nom du premier défendeur"""
        defendeurs = parties.get('defendeurs', [])
        if defendeurs:
            return defendeurs[0].nom
        return "[DÉFENDEUR]"
    
    def _get_destinataire_type(self, type_acte: TypeActe) -> str:
        """Détermine le type de destinataire"""
        mapping = {
            TypeActe.PLAINTE_SIMPLE: "procureur",
            TypeActe.PLAINTE_CPC: "doyen",
            TypeActe.CONCLUSIONS_NULLITE: "tribunal",
            TypeActe.CONCLUSIONS_FOND: "tribunal",
            TypeActe.ASSIGNATION: "tribunal",
            TypeActe.CITATION_DIRECTE: "tribunal"
        }
        return mapping.get(type_acte, "tribunal")
    
    def _assembler_acte_structure(
        self,
        type_acte: TypeActe,
        sections: Dict[str, Dict[str, str]],
        parties: Dict[str, List[Partie]],
        pieces: List[Piece],
        style: StyleRedaction
    ) -> str:
        """Assemble l'acte avec une structure hiérarchique"""
        
        contenu_parts = []
        
        # En-tête toujours en premier sans numérotation
        if "en_tete" in sections:
            contenu_parts.append(sections["en_tete"]["contenu"])
        
        # Autres sections avec numérotation
        numero_principal = 1
        for section_key, section_data in sections.items():
            if section_key != "en_tete":
                titre = section_data["titre"].upper()
                contenu = section_data["contenu"]
                
                # Numérotation principale
                if section_key in ["expose_faits", "discussion_juridique", "prejudices"]:
                    numero = self._to_roman(numero_principal)
                    contenu_parts.append(f"\n{numero}. {titre}\n\n{contenu}")
                    numero_principal += 1
                else:
                    # Sections sans numérotation (dispositif, etc.)
                    contenu_parts.append(f"\n{contenu}")
        
        # Ajouter la liste des pièces
        if pieces:
            contenu_parts.append(self._generer_bordereau_pieces(pieces))
        
        # Assembler
        contenu_final = "\n".join(contenu_parts)
        
        # Appliquer le formatage selon le style
        return self._appliquer_formatage_style(contenu_final, style)
    
    def _to_roman(self, num: int) -> str:
        """Convertit un nombre en chiffres romains"""
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
    
    def _generer_bordereau_pieces(self, pieces: List[Piece]) -> str:
        """Génère le bordereau de communication des pièces"""
        bordereau = "\n\nBORDEREAU DE COMMUNICATION DE PIÈCES\n\n"
        
        # Grouper par catégorie
        categories = {}
        for piece in pieces:
            cat = piece.categorie or "Autres"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(piece)
        
        # Afficher par catégorie
        for categorie, pieces_cat in categories.items():
            if len(categories) > 1:
                bordereau += f"\n{categorie.upper()}\n\n"
            
            for piece in pieces_cat:
                bordereau += f"Pièce n° {piece.numero} : {piece.titre}"
                if piece.date:
                    bordereau += f" ({piece.date.strftime('%d/%m/%Y')})"
                if piece.description:
                    bordereau += f"\n           {piece.description}"
                bordereau += "\n"
        
        return bordereau
    
    def _appliquer_formatage_style(self, contenu: str, style: StyleRedaction) -> str:
        """Applique le formatage selon le style choisi"""
        
        # Styles CSS selon le style de rédaction
        styles_css = {
            StyleRedaction.FORMEL: {
                "font": "Garamond",
                "size": "12pt",
                "line_height": "1.5",
                "paragraph_spacing": "12pt"
            },
            StyleRedaction.MODERNE: {
                "font": "Arial",
                "size": "11pt", 
                "line_height": "1.6",
                "paragraph_spacing": "10pt"
            },
            StyleRedaction.TECHNIQUE: {
                "font": "Times New Roman",
                "size": "11pt",
                "line_height": "1.4",
                "paragraph_spacing": "8pt"
            }
        }
        
        style_config = styles_css.get(style, styles_css[StyleRedaction.FORMEL])
        
        # Appliquer les marqueurs HTML pour l'export
        contenu_formate = contenu
        
        # Titres principaux (I., II., etc.)
        contenu_formate = re.sub(
            r'^([IVX]+)\.\s+(.+)$',
            r'<h1 style="font-family: {font}; font-size: 14pt; font-weight: bold; text-decoration: underline;">\1. \2</h1>'.format(**style_config),
            contenu_formate,
            flags=re.MULTILINE
        )
        
        # Sous-titres (A., B., etc.)
        contenu_formate = re.sub(
            r'^([A-Z])\.\s+(.+)$',
            r'<h2 style="font-family: {font}; font-size: 12pt; font-weight: bold;">\1. \2</h2>'.format(**style_config),
            contenu_formate,
            flags=re.MULTILINE
        )
        
        # Références aux pièces
        contenu_formate = re.sub(
            r'\(PIÈCE N° (\d+)\)',
            r'<span style="font-weight: bold; color: #0066cc;">(PIÈCE N° \1)</span>',
            contenu_formate,
            flags=re.IGNORECASE
        )
        
        return contenu_formate
    
    def _generer_titre_intelligent(
        self,
        type_acte: TypeActe,
        parties: Dict[str, List[Partie]],
        phase: PhaseProcedurale
    ) -> str:
        """Génère un titre intelligent pour l'acte"""
        
        demandeur = parties.get('demandeurs', [Partie(nom="[DEMANDEUR]", type_partie="demandeur")])[0].nom
        defendeur = parties.get('defendeurs', [Partie(nom="[DÉFENDEUR]", type_partie="defendeur")])[0].nom
        
        # Titre de base
        titre = type_acte.value.replace('_', ' ').title()
        
        # Ajouter le contexte procédural
        if phase != PhaseProcedurale.ENQUETE:
            titre += f" - Phase {phase.value}"
        
        # Ajouter les parties (version courte)
        titre += f"\n{self._truncate(demandeur, 30)} c/ {self._truncate(defendeur, 30)}"
        
        return titre
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Tronque un texte si trop long"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

# ========================= INTERFACE STREAMLIT AMÉLIORÉE =========================

def show_page():
    """Interface principale du générateur d'actes juridiques"""
    
    # Configuration de la page
    st.set_page_config(
        page_title="Générateur d'Actes Juridiques",
        page_icon="⚖️",
        layout="wide"
    )
    
    # CSS personnalisé
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-align: center;
        color: #1f2937;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #374151;
    }
    .info-box {
        background-color: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # En-tête
    st.markdown('<h1 class="main-header">⚖️ Générateur d\'Actes Juridiques</h1>', unsafe_allow_html=True)
    
    # Initialiser le générateur
    if 'generateur' not in st.session_state:
        st.session_state.generateur = GenerateurActesJuridiques()
    
    # Tabs principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Nouveau Document",
        "📂 Mes Brouillons",
        "🎯 Assistant Guidé",
        "⚙️ Paramètres"
    ])
    
    with tab1:
        show_new_document_tab()
    
    with tab2:
        show_drafts_tab()
    
    with tab3:
        show_guided_assistant_tab()
    
    with tab4:
        show_settings_tab()

def show_new_document_tab():
    """Onglet de création de nouveau document"""
    
    # Sélection rapide du type de document
    st.markdown('<h2 class="sub-header">Quel type de document souhaitez-vous créer ?</h2>', unsafe_allow_html=True)
    
    # Cartes de sélection rapide
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Plainte Simple", use_container_width=True, help="Pour signaler des faits au Procureur"):
            st.session_state.type_acte_selectionne = TypeActe.PLAINTE_SIMPLE
            st.session_state.show_form = True
    
    with col2:
        if st.button("⚖️ Plainte avec CPC", use_container_width=True, help="Pour déclencher l'action publique"):
            st.session_state.type_acte_selectionne = TypeActe.PLAINTE_CPC
            st.session_state.show_form = True
    
    with col3:
        if st.button("📄 Conclusions", use_container_width=True, help="Pour une procédure en cours"):
            st.session_state.show_conclusions_choice = True
    
    # Choix détaillé pour les conclusions
    if st.session_state.get('show_conclusions_choice', False):
        st.markdown("### Type de conclusions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚫 Conclusions de nullité", use_container_width=True):
                st.session_state.type_acte_selectionne = TypeActe.CONCLUSIONS_NULLITE
                st.session_state.show_form = True
        with col2:
            if st.button("💼 Conclusions au fond", use_container_width=True):
                st.session_state.type_acte_selectionne = TypeActe.CONCLUSIONS_FOND
                st.session_state.show_form = True
    
    # Plus d'options
    with st.expander("➕ Plus de types de documents"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Assignation", use_container_width=True):
                st.session_state.type_acte_selectionne = TypeActe.ASSIGNATION
                st.session_state.show_form = True
            if st.button("📨 Citation directe", use_container_width=True):
                st.session_state.type_acte_selectionne = TypeActe.CITATION_DIRECTE
                st.session_state.show_form = True
        with col2:
            if st.button("📑 Requête", use_container_width=True):
                st.session_state.type_acte_selectionne = TypeActe.REQUETE
                st.session_state.show_form = True
            if st.button("📜 Mémoire", use_container_width=True):
                st.session_state.type_acte_selectionne = TypeActe.MEMOIRE
                st.session_state.show_form = True
    
    # Afficher le formulaire si un type est sélectionné
    if st.session_state.get('show_form', False) and st.session_state.get('type_acte_selectionne'):
        st.markdown("---")
        show_document_form(st.session_state.type_acte_selectionne)

def show_document_form(type_acte: TypeActe):
    """Affiche le formulaire de création de document"""
    
    st.markdown(f'<h2 class="sub-header">Création : {type_acte.value.replace("_", " ").title()}</h2>', unsafe_allow_html=True)
    
    # Informations sur le type de document
    template_info = TEMPLATES_DETAILLES[type_acte]
    st.markdown(f"""
    <div class="info-box">
    <strong>Destinataire :</strong> {template_info['destinataire']}<br>
    <strong>Longueur recommandée :</strong> {template_info['longueur_cible']:,} mots<br>
    <strong>Style par défaut :</strong> {template_info['style_defaut'].value}
    </div>
    """, unsafe_allow_html=True)
    
    # Formulaire en colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Section Parties
        st.markdown("### 👥 Parties")
        
        # Demandeurs
        st.markdown("**Demandeurs / Plaignants**")
        nb_demandeurs = st.number_input(
            "Nombre de demandeurs",
            min_value=1,
            max_value=10,
            value=1,
            key="nb_demandeurs"
        )
        
        demandeurs = []
        for i in range(nb_demandeurs):
            with st.expander(f"Demandeur {i+1}", expanded=(i==0)):
                demandeur = create_partie_form(f"demandeur_{i}", "demandeur")
                if demandeur:
                    demandeurs.append(demandeur)
        
        # Défendeurs
        st.markdown("**Défendeurs / Mis en cause**")
        nb_defendeurs = st.number_input(
            "Nombre de défendeurs",
            min_value=1,
            max_value=10,
            value=1,
            key="nb_defendeurs"
        )
        
        defendeurs = []
        for i in range(nb_defendeurs):
            with st.expander(f"Défendeur {i+1}", expanded=(i==0)):
                defendeur = create_partie_form(f"defendeur_{i}", "defendeur")
                if defendeur:
                    defendeurs.append(defendeur)
        
        # Section Infractions
        st.markdown("### 🚨 Infractions")
        
        # Sélection rapide
        infractions_quick = st.multiselect(
            "Sélection rapide",
            list(INFRACTIONS_DB.keys()),
            format_func=lambda x: x.title(),
            key="infractions_quick"
        )
        
        # Infractions personnalisées
        infractions_custom = st.text_area(
            "Autres infractions (une par ligne)",
            height=100,
            key="infractions_custom",
            placeholder="Ex: Violation du secret professionnel\nRecel"
        )
        
        # Combiner les infractions
        all_infractions = list(infractions_quick)
        if infractions_custom:
            all_infractions.extend([i.strip() for i in infractions_custom.split('\n') if i.strip()])
        
        # Section Contexte
        st.markdown("### 📋 Contexte de l'affaire")
        
        contexte = st.text_area(
            "Décrivez les faits (ceci servira de base à la rédaction)",
            height=200,
            key="contexte_affaire",
            placeholder="Exposez chronologiquement les faits importants..."
        )
        
        # Section Pièces
        st.markdown("### 📎 Pièces justificatives")
        
        pieces = []
        nb_pieces = st.number_input(
            "Nombre de pièces",
            min_value=0,
            max_value=100,
            value=0,
            key="nb_pieces"
        )
        
        if nb_pieces > 0:
            # Catégories de pièces
            categories = ["Contrats", "Factures", "Courriers", "Relevés bancaires", "Expertises", "Autres"]
            
            for i in range(min(nb_pieces, 10)):  # Limiter l'affichage
                col_p1, col_p2, col_p3 = st.columns([3, 2, 1])
                with col_p1:
                    titre = st.text_input(f"Pièce {i+1}", key=f"piece_titre_{i}")
                with col_p2:
                    categorie = st.selectbox(
                        "Catégorie",
                        categories,
                        key=f"piece_cat_{i}"
                    )
                with col_p3:
                    date = st.date_input("Date", key=f"piece_date_{i}")
                
                if titre:
                    pieces.append(Piece(
                        numero=i+1,
                        titre=titre,
                        categorie=categorie,
                        date=date
                    ))
            
            if nb_pieces > 10:
                st.info(f"Affichage limité aux 10 premières pièces. Total : {nb_pieces} pièces.")
    
    with col2:
        # Options de génération
        st.markdown("### ⚙️ Options")
        
        # Phase procédurale
        phase = st.selectbox(
            "Phase procédurale",
            [p for p in PhaseProcedurale],
            format_func=lambda x: x.value.title(),
            key="phase_procedurale"
        )
        
        # Style de rédaction
        style = st.selectbox(
            "Style de rédaction",
            [s for s in StyleRedaction],
            format_func=lambda x: x.value.title(),
            index=[s for s in StyleRedaction].index(template_info['style_defaut']),
            key="style_redaction",
            help="Le style influence le ton et le niveau de détail"
        )
        
        # Options avancées
        with st.expander("Options avancées"):
            utiliser_ia = st.checkbox(
                "Utiliser l'IA pour la rédaction",
                value=True,
                help="Désactiver pour utiliser uniquement les templates"
            )
            
            anticiper_defense = st.checkbox(
                "Anticiper les arguments adverses",
                value=True,
                help="Ajoute des sections réfutant les arguments potentiels"
            )
            
            inclure_jurisprudence = st.checkbox(
                "Rechercher la jurisprudence",
                value=True,
                help="Ajoute des références jurisprudentielles pertinentes"
            )
            
            verification_societes = st.checkbox(
                "Vérifier les sociétés (Pappers)",
                value=False,
                help="Récupère automatiquement les infos légales",
                disabled=True
            )
        
        # Ville pour les mentions
        st.text_input(
            "Ville",
            value="Paris",
            key="ville_utilisateur",
            help="Pour les mentions de lieu"
        )
        
        # Actions
        st.markdown("### 🚀 Actions")
        
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            if st.button(
                "Générer",
                type="primary",
                use_container_width=True,
                disabled=not (demandeurs and all_infractions)
            ):
                generer_document(
                    type_acte=type_acte,
                    demandeurs=demandeurs,
                    defendeurs=defendeurs,
                    infractions=all_infractions,
                    contexte=contexte,
                    pieces=pieces,
                    phase=phase,
                    style=style,
                    options={
                        'utiliser_ia': utiliser_ia,
                        'anticiper_defense': anticiper_defense,
                        'inclure_jurisprudence': inclure_jurisprudence,
                        'verification_societes': verification_societes
                    }
                )
        
        with col_action2:
            if st.button(
                "Sauvegarder brouillon",
                use_container_width=True
            ):
                sauvegarder_brouillon(
                    type_acte, demandeurs, defendeurs,
                    all_infractions, contexte, pieces,
                    phase, style
                )
        
        # Aide contextuelle
        st.markdown("### ❓ Aide")
        st.markdown("""
        <div class="info-box">
        <strong>Conseils :</strong><br>
        • Soyez précis dans le contexte<br>
        • Listez toutes les infractions<br>
        • Numérotez vos pièces<br>
        • Vérifiez les informations des parties
        </div>
        """, unsafe_allow_html=True)

def create_partie_form(key_prefix: str, type_partie: str) -> Optional[Partie]:
    """Crée un formulaire pour une partie"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        nom = st.text_input("Nom complet", key=f"{key_prefix}_nom")
        qualite = st.selectbox(
            "Qualité",
            ["Personne physique", "Société", "Association", "Collectivité"],
            key=f"{key_prefix}_qualite"
        )
    
    with col2:
        if qualite == "Société":
            forme_juridique = st.selectbox(
                "Forme juridique",
                ["SAS", "SARL", "SA", "SCI", "EURL", "Autre"],
                key=f"{key_prefix}_forme"
            )
            siren = st.text_input("SIREN", key=f"{key_prefix}_siren")
        else:
            forme_juridique = ""
            siren = ""
    
    adresse = st.text_area(
        "Adresse complète",
        height=60,
        key=f"{key_prefix}_adresse"
    )
    
    if qualite in ["Société", "Association"]:
        representant = st.text_input(
            "Représentant légal",
            key=f"{key_prefix}_representant"
        )
    else:
        representant = ""
    
    avocat = st.text_input(
        "Avocat (optionnel)",
        key=f"{key_prefix}_avocat",
        placeholder="Me Nom, Barreau de..."
    )
    
    if nom:
        return Partie(
            nom=nom,
            type_partie=type_partie,
            qualite=qualite,
            adresse=adresse,
            forme_juridique=forme_juridique,
            siren=siren,
            representant=representant,
            avocat=avocat
        )
    
    return None

def generer_document(
    type_acte: TypeActe,
    demandeurs: List[Partie],
    defendeurs: List[Partie],
    infractions: List[str],
    contexte: str,
    pieces: List[Piece],
    phase: PhaseProcedurale,
    style: StyleRedaction,
    options: Dict[str, Any]
):
    """Lance la génération du document"""
    
    # Validation
    if not demandeurs:
        st.error("❌ Veuillez ajouter au moins un demandeur")
        return
    
    if not infractions:
        st.error("❌ Veuillez sélectionner au moins une infraction")
        return
    
    # Préparer les parties
    parties = {
        'demandeurs': demandeurs,
        'defendeurs': defendeurs
    }
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Génération
        status_text.text("⏳ Initialisation...")
        progress_bar.progress(10)
        
        generateur = st.session_state.generateur
        
        status_text.text("⏳ Analyse des infractions...")
        progress_bar.progress(20)
        
        status_text.text("⏳ Génération du contenu...")
        progress_bar.progress(40)
        
        acte = generateur.generer_acte_complet(
            type_acte=type_acte,
            parties=parties,
            infractions=infractions,
            contexte=contexte,
            pieces=pieces,
            style=style,
            phase=phase,
            options=options
        )
        
        status_text.text("⏳ Mise en forme...")
        progress_bar.progress(80)
        
        # Sauvegarder en session
        st.session_state.acte_genere = acte
        st.session_state.show_result = True
        
        progress_bar.progress(100)
        status_text.text("✅ Document généré avec succès !")
        
        # Afficher le résultat
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Erreur lors de la génération : {str(e)}")
        st.exception(e)

def show_drafts_tab():
    """Affiche l'onglet des brouillons"""
    
    st.markdown('<h2 class="sub-header">📂 Mes Brouillons</h2>', unsafe_allow_html=True)
    
    # Récupérer les brouillons
    brouillons = st.session_state.get('brouillons', [])
    
    if not brouillons:
        st.info("Aucun brouillon enregistré. Créez un nouveau document et sauvegardez-le comme brouillon.")
        return
    
    # Afficher les brouillons
    for i, brouillon in enumerate(brouillons):
        with st.expander(
            f"{brouillon['type_acte'].value.replace('_', ' ').title()} - {brouillon['date'].strftime('%d/%m/%Y %H:%M')}",
            expanded=False
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Parties:** {len(brouillon['demandeurs'])} demandeur(s), {len(brouillon['defendeurs'])} défendeur(s)")
                st.write(f"**Infractions:** {', '.join(brouillon['infractions'][:3])}")
                if len(brouillon['infractions']) > 3:
                    st.write(f"... et {len(brouillon['infractions']) - 3} autre(s)")
                st.write(f"**Phase:** {brouillon['phase'].value}")
                st.write(f"**Style:** {brouillon['style'].value}")
            
            with col2:
                if st.button("Reprendre", key=f"reprendre_{i}"):
                    # Charger le brouillon
                    charger_brouillon(brouillon)
                
                if st.button("Supprimer", key=f"supprimer_{i}"):
                    st.session_state.brouillons.pop(i)
                    st.rerun()

def show_guided_assistant_tab():
    """Affiche l'assistant guidé"""
    
    st.markdown('<h2 class="sub-header">🎯 Assistant de Rédaction Guidé</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    L'assistant vous guide pas à pas dans la création de votre document juridique.
    Répondez aux questions et l'assistant générera automatiquement le document adapté.
    </div>
    """, unsafe_allow_html=True)
    
    # Étapes de l'assistant
    if 'assistant_step' not in st.session_state:
        st.session_state.assistant_step = 0
    
    steps = [
        "Type de procédure",
        "Identification des parties",
        "Description des faits",
        "Qualification juridique",
        "Éléments de preuve",
        "Finalisation"
    ]
    
    # Progress
    current_step = st.session_state.assistant_step
    progress = current_step / len(steps)
    st.progress(progress)
    st.write(f"Étape {current_step + 1} sur {len(steps)} : **{steps[current_step]}**")
    
    # Contenu selon l'étape
    if current_step == 0:  # Type de procédure
        show_assistant_step_procedure()
    elif current_step == 1:  # Parties
        show_assistant_step_parties()
    elif current_step == 2:  # Faits
        show_assistant_step_faits()
    elif current_step == 3:  # Qualification
        show_assistant_step_qualification()
    elif current_step == 4:  # Preuves
        show_assistant_step_preuves()
    elif current_step == 5:  # Finalisation
        show_assistant_step_finalisation()
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_step > 0:
            if st.button("← Précédent", use_container_width=True):
                st.session_state.assistant_step -= 1
                st.rerun()
    
    with col3:
        if current_step < len(steps) - 1:
            if st.button("Suivant →", use_container_width=True):
                if validate_assistant_step(current_step):
                    st.session_state.assistant_step += 1
                    st.rerun()
        else:
            if st.button("Générer le document", type="primary", use_container_width=True):
                generer_depuis_assistant()

def show_assistant_step_procedure():
    """Étape 1 : Type de procédure"""
    
    st.markdown("### Dans quel contexte vous trouvez-vous ?")
    
    situation = st.radio(
        "Ma situation",
        [
            "Je souhaite porter plainte pour des faits pénaux",
            "Je suis convoqué(e) devant un tribunal",
            "Je représente une partie dans une procédure en cours",
            "Je souhaite engager des poursuites directement"
        ],
        key="assistant_situation"
    )
    
    if situation == "Je souhaite porter plainte pour des faits pénaux":
        st.markdown("### Quel est votre objectif ?")
        objectif = st.radio(
            "Je veux",
            [
                "Simplement signaler les faits au Procureur",
                "Me constituer partie civile et déclencher une enquête",
                "Obtenir des conseils sur la meilleure approche"
            ],
            key="assistant_objectif_plainte"
        )
        
        if objectif == "Simplement signaler les faits au Procureur":
            st.session_state.assistant_type_acte = TypeActe.PLAINTE_SIMPLE
            st.success("→ Nous allons préparer une **plainte simple**")
        elif objectif == "Me constituer partie civile et déclencher une enquête":
            st.session_state.assistant_type_acte = TypeActe.PLAINTE_CPC
            st.success("→ Nous allons préparer une **plainte avec constitution de partie civile**")
        else:
            st.info("""
            **Conseil :** 
            - La plainte simple est gratuite et rapide, mais le Procureur peut classer sans suite
            - La plainte avec constitution de partie civile garantit l'ouverture d'une enquête mais nécessite une consignation
            """)
    
    elif situation == "Je suis convoqué(e) devant un tribunal":
        role = st.radio(
            "Je suis",
            ["Prévenu(e) / Mis(e) en cause", "Partie civile", "Témoin assisté"],
            key="assistant_role_convocation"
        )
        
        if role == "Prévenu(e) / Mis(e) en cause":
            st.session_state.assistant_type_acte = TypeActe.CONCLUSIONS_FOND
            st.success("→ Nous allons préparer des **conclusions de défense**")
    
    # Phase procédurale
    st.markdown("### À quelle étape de la procédure êtes-vous ?")
    phase = st.selectbox(
        "Phase actuelle",
        ["Aucune procédure en cours", "Enquête préliminaire", "Instruction", "Renvoi devant le tribunal", "Appel"],
        key="assistant_phase"
    )
    
    # Mapper vers l'enum
    phase_mapping = {
        "Aucune procédure en cours": PhaseProcedurale.ENQUETE,
        "Enquête préliminaire": PhaseProcedurale.ENQUETE,
        "Instruction": PhaseProcedurale.INSTRUCTION,
        "Renvoi devant le tribunal": PhaseProcedurale.JUGEMENT,
        "Appel": PhaseProcedurale.APPEL
    }
    st.session_state.assistant_phase = phase_mapping.get(phase, PhaseProcedurale.ENQUETE)

def show_assistant_step_parties():
    """Étape 2 : Identification des parties"""
    
    st.markdown("### Qui êtes-vous dans cette affaire ?")
    
    # Type de demandeur
    type_demandeur = st.radio(
        "Je suis",
        ["Un particulier", "Une entreprise", "Une association", "Un représentant légal"],
        key="assistant_type_demandeur"
    )
    
    # Informations du demandeur
    if type_demandeur == "Un particulier":
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom complet", key="assistant_nom_demandeur")
        with col2:
            profession = st.text_input("Profession (optionnel)", key="assistant_profession")
        
        adresse = st.text_area("Adresse complète", height=80, key="assistant_adresse_demandeur")
        
    elif type_demandeur == "Une entreprise":
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Raison sociale", key="assistant_nom_entreprise")
            forme = st.selectbox("Forme juridique", ["SAS", "SARL", "SA", "SCI", "Autre"])
        with col2:
            siren = st.text_input("SIREN", key="assistant_siren")
            representant = st.text_input("Représentant légal", key="assistant_representant")
        
        adresse = st.text_area("Siège social", height=80, key="assistant_siege_social")
    
    # Contre qui ?
    st.markdown("### Contre qui agissez-vous ?")
    
    nb_defendeurs = st.number_input(
        "Nombre de parties adverses",
        min_value=1,
        max_value=10,
        value=1,
        key="assistant_nb_defendeurs"
    )
    
    # Stocker les infos
    if 'assistant_parties' not in st.session_state:
        st.session_state.assistant_parties = {'demandeurs': [], 'defendeurs': []}
    
    # Simple formulaire pour les défendeurs
    for i in range(nb_defendeurs):
        with st.expander(f"Partie adverse {i+1}"):
            nom_def = st.text_input("Nom ou raison sociale", key=f"assistant_def_nom_{i}")
            type_def = st.radio(
                "Type",
                ["Personne physique", "Société", "Inconnu"],
                key=f"assistant_def_type_{i}"
            )
            if type_def == "Société":
                st.text_input("SIREN si connu", key=f"assistant_def_siren_{i}")

def show_assistant_step_faits():
    """Étape 3 : Description des faits"""
    
    st.markdown("### Racontez-nous ce qui s'est passé")
    
    st.markdown("""
    <div class="info-box">
    <strong>Conseils pour bien décrire les faits :</strong><br>
    • Suivez l'ordre chronologique<br>
    • Indiquez les dates précises quand possible<br>
    • Mentionnez tous les protagonistes<br>
    • Décrivez les préjudices subis<br>
    • Restez factuel et objectif
    </div>
    """, unsafe_allow_html=True)
    
    # Questions guidées
    st.markdown("#### Quand les faits ont-ils commencé ?")
    date_debut = st.date_input("Date de début", key="assistant_date_debut")
    
    st.markdown("#### Résumé des faits principaux")
    resume = st.text_area(
        "En quelques phrases, décrivez l'essentiel",
        height=150,
        key="assistant_resume_faits",
        placeholder="Ex: M. X, gérant de ma société, a détourné des fonds en établissant de fausses factures..."
    )
    
    st.markdown("#### Chronologie détaillée")
    chronologie = st.text_area(
        "Développez chronologiquement (dates + événements)",
        height=300,
        key="assistant_chronologie",
        placeholder="""Ex:
- 15/01/2023 : Découverte d'anomalies dans les comptes
- 20/01/2023 : Confrontation avec M. X qui avoue
- 25/01/2023 : Dépôt de plainte au commissariat
- ..."""
    )
    
    st.markdown("#### Préjudices subis")
    col1, col2 = st.columns(2)
    
    with col1:
        prejudice_financier = st.number_input(
            "Préjudice financier (€)",
            min_value=0,
            value=0,
            key="assistant_prejudice_financier"
        )
        
        if prejudice_financier > 0:
            detail_financier = st.text_area(
                "Détaillez le calcul",
                height=100,
                key="assistant_detail_financier"
            )
    
    with col2:
        prejudice_moral = st.checkbox("Préjudice moral", key="assistant_prejudice_moral")
        prejudice_image = st.checkbox("Préjudice d'image/commercial", key="assistant_prejudice_image")
        autres_prejudices = st.checkbox("Autres préjudices", key="assistant_autres_prejudices")

def show_assistant_step_qualification():
    """Étape 4 : Qualification juridique"""
    
    st.markdown("### Qualification juridique des faits")
    
    st.markdown("""
    <div class="info-box">
    D'après votre récit, nous allons identifier les infractions potentielles.
    Cette qualification pourra être affinée par votre avocat.
    </div>
    """, unsafe_allow_html=True)
    
    # Analyse automatique basée sur les mots-clés
    if 'assistant_chronologie' in st.session_state:
        texte = st.session_state.assistant_chronologie.lower()
        infractions_suggerees = []
        
        # Détection simple par mots-clés
        if any(word in texte for word in ['détourné', 'détournement', 'soustrait']):
            infractions_suggerees.append("Abus de biens sociaux")
        if any(word in texte for word in ['faux', 'falsifié', 'fausses factures']):
            infractions_suggerees.append("Faux et usage de faux")
        if any(word in texte for word in ['trompé', 'mensonge', 'tromperie']):
            infractions_suggerees.append("Escroquerie")
        if any(word in texte for word in ['pot de vin', 'corruption', 'corrompu']):
            infractions_suggerees.append("Corruption")
        
        if infractions_suggerees:
            st.success(f"Infractions détectées : {', '.join(infractions_suggerees)}")
    
    # Sélection manuelle
    st.markdown("#### Sélectionnez les infractions qui correspondent à votre situation")
    
    # Grouper par catégorie
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Infractions économiques**")
        inf_eco = []
        if st.checkbox("Abus de biens sociaux", key="inf_abs"):
            inf_eco.append("Abus de biens sociaux")
        if st.checkbox("Escroquerie", key="inf_esc"):
            inf_eco.append("Escroquerie")
        if st.checkbox("Abus de confiance", key="inf_adc"):
            inf_eco.append("Abus de confiance")
        if st.checkbox("Faux et usage de faux", key="inf_faux"):
            inf_eco.append("Faux et usage de faux")
    
    with col2:
        st.markdown("**Autres infractions**")
        inf_autres = []
        if st.checkbox("Corruption", key="inf_cor"):
            inf_autres.append("Corruption")
        if st.checkbox("Blanchiment", key="inf_bla"):
            inf_autres.append("Blanchiment")
        if st.checkbox("Recel", key="inf_rec"):
            inf_autres.append("Recel")
        if st.checkbox("Vol", key="inf_vol"):
            inf_autres.append("Vol")
    
    # Stocker les infractions sélectionnées
    st.session_state.assistant_infractions = inf_eco + inf_autres
    
    # Afficher les détails des infractions sélectionnées
    if st.session_state.assistant_infractions:
        st.markdown("#### Détails des infractions sélectionnées")
        
        for infraction in st.session_state.assistant_infractions:
            if infraction.lower() in INFRACTIONS_DB:
                data = INFRACTIONS_DB[infraction.lower()]
                with st.expander(f"📖 {infraction}"):
                    st.write(f"**Articles :** {', '.join(data['articles'])}")
                    st.write(f"**Peine encourue :** {data['peines']}")
                    st.write("**Éléments à prouver :**")
                    for elem in data['elements']:
                        st.write(f"• {elem}")

def show_assistant_step_preuves():
    """Étape 5 : Éléments de preuve"""
    
    st.markdown("### Quelles preuves avez-vous ?")
    
    st.markdown("""
    <div class="info-box">
    Les preuves sont essentielles pour étayer votre dossier.
    Listez tous les documents, témoignages et éléments en votre possession.
    </div>
    """, unsafe_allow_html=True)
    
    # Types de preuves
    st.markdown("#### Documents")
    
    types_docs = {
        "Contrats et conventions": ["Contrat de travail", "Contrat commercial", "Statuts de société"],
        "Documents financiers": ["Factures", "Relevés bancaires", "Bilans comptables", "Chèques"],
        "Correspondances": ["Emails", "Courriers", "SMS", "Messages WhatsApp"],
        "Documents officiels": ["PV d'assemblée", "Décisions de justice", "Actes notariés"],
        "Expertises": ["Rapport d'expert-comptable", "Audit", "Expertise judiciaire"]
    }
    
    pieces_selectionnees = []
    
    for categorie, exemples in types_docs.items():
        with st.expander(f"📁 {categorie}"):
            for exemple in exemples:
                if st.checkbox(exemple, key=f"doc_{exemple.lower().replace(' ', '_')}"):
                    nb = st.number_input(
                        f"Nombre de {exemple.lower()}",
                        min_value=1,
                        value=1,
                        key=f"nb_{exemple.lower().replace(' ', '_')}"
                    )
                    for i in range(nb):
                        pieces_selectionnees.append({
                            'type': exemple,
                            'categorie': categorie,
                            'numero': len(pieces_selectionnees) + 1
                        })
    
    # Témoignages
    st.markdown("#### Témoignages")
    nb_temoins = st.number_input(
        "Nombre de témoins",
        min_value=0,
        max_value=20,
        value=0,
        key="assistant_nb_temoins"
    )
    
    if nb_temoins > 0:
        st.info(f"Vous avez {nb_temoins} témoin(s). Pensez à recueillir leurs attestations selon le modèle Cerfa.")
    
    # Autres preuves
    st.markdown("#### Autres éléments")
    autres_preuves = st.text_area(
        "Autres preuves (enregistrements, photos, etc.)",
        height=100,
        key="assistant_autres_preuves",
        placeholder="Ex: Enregistrement audio de l'aveu, captures d'écran..."
    )
    
    # Stocker les preuves
    st.session_state.assistant_pieces = pieces_selectionnees

def show_assistant_step_finalisation():
    """Étape 6 : Finalisation"""
    
    st.markdown("### Récapitulatif de votre dossier")
    
    # Récupérer toutes les infos
    type_acte = st.session_state.get('assistant_type_acte', TypeActe.PLAINTE_SIMPLE)
    phase = st.session_state.get('assistant_phase', PhaseProcedurale.ENQUETE)
    infractions = st.session_state.get('assistant_infractions', [])
    pieces = st.session_state.get('assistant_pieces', [])
    
    # Afficher le récap
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Type de document :**")
        st.write(type_acte.value.replace('_', ' ').title())
        
        st.markdown("**Phase procédurale :**")
        st.write(phase.value.title())
        
        st.markdown("**Infractions retenues :**")
        for inf in infractions:
            st.write(f"• {inf}")
    
    with col2:
        st.markdown("**Préjudices :**")
        if st.session_state.get('assistant_prejudice_financier', 0) > 0:
            st.write(f"• Financier : {st.session_state.assistant_prejudice_financier:,.2f} €")
        if st.session_state.get('assistant_prejudice_moral', False):
            st.write("• Moral")
        if st.session_state.get('assistant_prejudice_image', False):
            st.write("• Image/Commercial")
        
        st.markdown("**Pièces :**")
        st.write(f"{len(pieces)} pièce(s) identifiée(s)")
    
    # Options finales
    st.markdown("### Options de génération")
    
    col1, col2 = st.columns(2)
    
    with col1:
        style = st.selectbox(
            "Style de rédaction",
            [StyleRedaction.FORMEL, StyleRedaction.MODERNE, StyleRedaction.ARGUMENTATIF],
            format_func=lambda x: x.value.title(),
            key="assistant_style_final"
        )
    
    with col2:
        urgence = st.checkbox(
            "Procédure urgente",
            key="assistant_urgence",
            help="Ajoute des demandes de mesures conservatoires"
        )
    
    # Derniers conseils
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Important :</strong><br>
    • Ce document est un projet qui doit être relu et validé par un avocat<br>
    • Vérifiez toutes les informations avant utilisation<br>
    • Adaptez le contenu à votre situation spécifique<br>
    • Respectez les délais de procédure applicables
    </div>
    """, unsafe_allow_html=True)

def validate_assistant_step(step: int) -> bool:
    """Valide l'étape actuelle de l'assistant"""
    
    if step == 0:  # Type de procédure
        if 'assistant_type_acte' not in st.session_state:
            st.error("Veuillez sélectionner un type de document")
            return False
    
    elif step == 1:  # Parties
        # Validation basique
        return True
    
    elif step == 2:  # Faits
        if not st.session_state.get('assistant_chronologie', '').strip():
            st.error("Veuillez décrire les faits")
            return False
    
    elif step == 3:  # Qualification
        if not st.session_state.get('assistant_infractions', []):
            st.error("Veuillez sélectionner au moins une infraction")
            return False
    
    return True

def generer_depuis_assistant():
    """Génère le document depuis l'assistant"""
    
    # Rassembler toutes les données
    type_acte = st.session_state.get('assistant_type_acte', TypeActe.PLAINTE_SIMPLE)
    phase = st.session_state.get('assistant_phase', PhaseProcedurale.ENQUETE)
    style = st.session_state.get('assistant_style_final', StyleRedaction.FORMEL)
    
    # Créer les parties
    # TODO: Récupérer les vraies infos depuis l'assistant
    demandeurs = [Partie(
        nom=st.session_state.get('assistant_nom_demandeur', '[DEMANDEUR]'),
        type_partie="demandeur",
        qualite="Personne physique",
        adresse=st.session_state.get('assistant_adresse_demandeur', '')
    )]
    
    defendeurs = [Partie(
        nom="[DÉFENDEUR]",
        type_partie="defendeur",
        qualite="À déterminer"
    )]
    
    # Contexte enrichi
    contexte = f"""
{st.session_state.get('assistant_resume_faits', '')}

CHRONOLOGIE DÉTAILLÉE :
{st.session_state.get('assistant_chronologie', '')}
"""
    
    # Lancer la génération
    generer_document(
        type_acte=type_acte,
        demandeurs=demandeurs,
        defendeurs=defendeurs,
        infractions=st.session_state.get('assistant_infractions', []),
        contexte=contexte,
        pieces=[],  # TODO: Mapper les pièces
        phase=phase,
        style=style,
        options={
            'utiliser_ia': True,
            'anticiper_defense': True,
            'inclure_jurisprudence': True,
            'urgence': st.session_state.get('assistant_urgence', False)
        }
    )

def show_settings_tab():
    """Affiche l'onglet des paramètres"""
    
    st.markdown('<h2 class="sub-header">⚙️ Paramètres</h2>', unsafe_allow_html=True)
    
    # Paramètres utilisateur
    st.markdown("### 👤 Informations personnelles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input(
            "Nom de l'étude/Cabinet",
            value=st.session_state.get('nom_cabinet', ''),
            key='settings_nom_cabinet'
        )
        
        st.text_input(
            "Ville par défaut",
            value=st.session_state.get('ville_defaut', 'Paris'),
            key='settings_ville'
        )
    
    with col2:
        st.text_area(
            "Adresse complète",
            value=st.session_state.get('adresse_cabinet', ''),
            height=100,
            key='settings_adresse'
        )
    
    # Préférences de génération
    st.markdown("### 🎨 Préférences de génération")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox(
            "Style par défaut",
            [s for s in StyleRedaction],
            format_func=lambda x: x.value.title(),
            key='settings_style_defaut'
        )
        
        st.checkbox(
            "Utiliser l'IA par défaut",
            value=True,
            key='settings_ia_defaut'
        )
    
    with col2:
        st.selectbox(
            "Format d'export préféré",
            ["DOCX", "PDF", "HTML"],
            key='settings_format_export'
        )
        
        st.checkbox(
            "Inclure jurisprudence par défaut",
            value=True,
            key='settings_jurisprudence_defaut'
        )
    
    # Modèles personnalisés
    st.markdown("### 📋 Modèles personnalisés")
    
    st.info("Fonction à venir : Créez et sauvegardez vos propres modèles de documents")
    
    # API Keys
    st.markdown("### 🔑 Clés API")
    
    with st.expander("Configuration des services externes"):
        st.text_input(
            "Clé API Pappers",
            type="password",
            key='settings_pappers_key',
            help="Pour la vérification automatique des sociétés"
        )
        
        st.text_input(
            "Clé API Doctrine",
            type="password",
            key='settings_doctrine_key',
            help="Pour la recherche de jurisprudence"
        )
    
    # Sauvegarder
    if st.button("💾 Sauvegarder les paramètres", type="primary"):
        save_settings()
        st.success("✅ Paramètres sauvegardés")

def save_settings():
    """Sauvegarde les paramètres"""
    settings = {
        'nom_cabinet': st.session_state.get('settings_nom_cabinet', ''),
        'ville_defaut': st.session_state.get('settings_ville', 'Paris'),
        'adresse_cabinet': st.session_state.get('settings_adresse', ''),
        'style_defaut': st.session_state.get('settings_style_defaut', StyleRedaction.FORMEL),
        'ia_defaut': st.session_state.get('settings_ia_defaut', True),
        'format_export': st.session_state.get('settings_format_export', 'DOCX'),
        'jurisprudence_defaut': st.session_state.get('settings_jurisprudence_defaut', True)
    }
    
    # Sauvegarder dans la session
    for key, value in settings.items():
        st.session_state[key] = value

def sauvegarder_brouillon(
    type_acte: TypeActe,
    demandeurs: List[Partie],
    defendeurs: List[Partie],
    infractions: List[str],
    contexte: str,
    pieces: List[Piece],
    phase: PhaseProcedurale,
    style: StyleRedaction
):
    """Sauvegarde un brouillon"""
    
    if 'brouillons' not in st.session_state:
        st.session_state.brouillons = []
    
    brouillon = {
        'date': datetime.now(),
        'type_acte': type_acte,
        'demandeurs': demandeurs,
        'defendeurs': defendeurs,
        'infractions': infractions,
        'contexte': contexte,
        'pieces': pieces,
        'phase': phase,
        'style': style
    }
    
    st.session_state.brouillons.append(brouillon)
    st.success("✅ Brouillon sauvegardé")

def charger_brouillon(brouillon: Dict):
    """Charge un brouillon"""
    
    # Restaurer toutes les valeurs
    st.session_state.type_acte_selectionne = brouillon['type_acte']
    st.session_state.show_form = True
    
    # TODO: Restaurer les autres champs du formulaire
    
    # Rediriger vers l'onglet de création
    st.session_state.active_tab = 0
    st.rerun()

# ========================= AFFICHAGE DU RÉSULTAT =========================

def show_document_result():
    """Affiche le document généré"""
    
    if 'acte_genere' not in st.session_state:
        return
    
    acte = st.session_state.acte_genere
    
    # Header avec infos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type", acte.type_acte.value.replace('_', ' ').title())
    with col2:
        st.metric("Mots", f"{acte.get_word_count():,}")
    with col3:
        st.metric("Pages", f"~{acte.get_page_estimate()}")
    with col4:
        st.metric("Style", acte.style.value.title())
    
    # Onglets pour affichage
    tab1, tab2, tab3 = st.tabs(["📄 Document", "✏️ Édition", "📥 Export"])
    
    with tab1:
        # Affichage formaté
        st.markdown("""
        <div style="background-color: white; padding: 2rem; border: 1px solid #ddd; border-radius: 5px;">
        """ + acte.contenu + """
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        # Édition
        contenu_edite = st.text_area(
            "Contenu éditable",
            value=acte.contenu,
            height=600,
            key="edition_contenu"
        )
        
        if st.button("💾 Sauvegarder les modifications"):
            acte.contenu = contenu_edite
            st.success("✅ Modifications sauvegardées")
    
    with tab3:
        # Export
        col1, col2 = st.columns(2)
        
        with col1:
            format_export = st.selectbox(
                "Format d'export",
                ["DOCX", "PDF", "HTML", "TXT"],
                key="format_export_final"
            )
        
        with col2:
            if st.button("📥 Télécharger", use_container_width=True):
                export_document(acte, format_export)

def export_document(acte: ActeJuridique, format: str):
    """Exporte le document"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{acte.type_acte.value}_{timestamp}.{format.lower()}"
    
    if format == "TXT":
        # Export texte simple
        contenu = acte.contenu.replace('<h1', '\n\n').replace('</h1>', '\n')
        contenu = re.sub('<[^>]+>', '', contenu)  # Retirer les balises HTML
        
        st.download_button(
            "💾 Télécharger",
            contenu,
            filename,
            mime="text/plain"
        )
    
    elif format == "HTML":
        # Export HTML avec styles
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{acte.titre}</title>
    <style>
        body {{ font-family: Garamond, serif; line-height: 1.6; margin: 2cm; }}
        h1 {{ font-size: 14pt; font-weight: bold; text-decoration: underline; }}
        h2 {{ font-size: 12pt; font-weight: bold; }}
        .piece-ref {{ font-weight: bold; color: #0066cc; }}
    </style>
</head>
<body>
{acte.contenu}
</body>
</html>
"""
        st.download_button(
            "💾 Télécharger",
            html_content,
            filename,
            mime="text/html"
        )
    
    elif format in ["DOCX", "PDF"]:
        # Pour DOCX et PDF, on a besoin de librairies supplémentaires
        st.info(f"Export {format} : Fonctionnalité à implémenter avec python-docx/reportlab")
        
        # Fallback : export en HTML
        st.warning(f"Export {format} non disponible, téléchargement en HTML à la place")
        export_document(acte, "HTML")

# ========================= FONCTIONS UTILITAIRES =========================

def clean_text_for_display(text: str) -> str:
    """Nettoie le texte pour l'affichage"""
    # Retirer les doubles espaces
    text = re.sub(r'\s+', ' ', text)
    # Retirer les espaces avant ponctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    # Ajouter espace après ponctuation si manquant
    text = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', text)
    return text.strip()

# Pour l'import time
import time

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    # Afficher le résultat si un document a été généré
    if st.session_state.get('show_result', False):
        show_document_result()
    else:
        show_page()
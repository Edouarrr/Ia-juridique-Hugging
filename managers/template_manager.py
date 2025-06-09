# managers/template_manager.py
"""
Gestionnaire de templates pour documents juridiques
"""

import json
import os
from typing import Dict, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TemplateManager:
    """Gestionnaire centralisé des templates de documents juridiques"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates = self._load_default_templates()
        self._load_custom_templates()
    
    def _load_default_templates(self) -> Dict[str, str]:
        """Charge les templates par défaut"""
        return {
            "plainte": """
PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE

Monsieur le Doyen des Juges d'Instruction
Tribunal Judiciaire de {juridiction}

Le {date_jour}

POUR : {plaignant_nom}
       {plaignant_adresse}
       {plaignant_qualite}

CONTRE : {defendeur_nom}
         {defendeur_qualite}

OBJET : Plainte avec constitution de partie civile

Monsieur le Doyen,

J'ai l'honneur de porter plainte avec constitution de partie civile entre vos mains pour les faits suivants :

I. EXPOSÉ DES FAITS

{expose_faits}

II. QUALIFICATION JURIDIQUE

Les faits exposés ci-dessus sont constitutifs de :
{qualifications_juridiques}

III. PRÉJUDICE SUBI

{description_prejudice}

IV. DEMANDES

Par ces motifs, je vous prie de bien vouloir :
- Recevoir ma plainte avec constitution de partie civile
- Ordonner l'ouverture d'une information judiciaire
- Procéder à tous actes d'instruction utiles

Je verse la consignation fixée par vos soins.

Vous trouverez ci-joint les pièces justificatives.

Je vous prie d'agréer, Monsieur le Doyen, l'expression de ma haute considération.

{signature}

Pièces jointes :
{liste_pieces}
""",

            "conclusions": """
CONCLUSIONS

POUR : {client_nom}
       {client_qualite}
       {client_adresse}

CONTRE : {adversaire_nom}
         {adversaire_qualite}

DEVANT : {juridiction}
RG N° : {numero_rg}

Plaise au Tribunal,

I. RAPPEL DES FAITS ET DE LA PROCÉDURE

{rappel_faits}

{rappel_procedure}

II. DISCUSSION

{discussion_juridique}

III. SUR LES DEMANDES ADVERSES

{reponse_demandes_adverses}

IV. DISPOSITIF

PAR CES MOTIFS,

Il est demandé au Tribunal de :

{demandes}

Sous toutes réserves
Bordereau de pièces communiquées en annexe

{signature_avocat}
""",

            "assignation": """
ASSIGNATION DEVANT LE {type_tribunal}

L'AN {annee} ET LE {date_complete}

À LA REQUÊTE DE :
{demandeur_identite}

AYANT POUR AVOCAT :
{avocat_identite}

J'AI, HUISSIER DE JUSTICE SOUSSIGNÉ,

DONNÉ ASSIGNATION À :
{defendeur_identite}

À COMPARAÎTRE :
Devant le {tribunal_competent}
Siégeant : {adresse_tribunal}
À l'audience du : {date_audience}
À {heure_audience} heures

OBJET DE LA DEMANDE :
{objet_demande}

EXPOSÉ DES MOTIFS :
{expose_motifs}

DISCUSSION JURIDIQUE :
{discussion_juridique}

DISPOSITIF :
{dispositif}

PIÈCES COMMUNIQUÉES :
{liste_pieces}

Sous toutes réserves
""",

            "requete": """
REQUÊTE

À Monsieur le Président du {juridiction}

POUR : {requerant_identite}

OBJET : {objet_requete}

Monsieur le Président,

J'ai l'honneur de solliciter de votre bienveillance {demande_principale}.

I. EXPOSÉ DES FAITS
{expose_faits}

II. FONDEMENTS JURIDIQUES
{fondements_juridiques}

III. PIÈCES JUSTIFICATIVES
{pieces_justificatives}

PAR CES MOTIFS,

Je vous prie de bien vouloir :
{demandes}

Je vous prie d'agréer, Monsieur le Président, l'expression de ma haute considération.

{signature}
""",

            "courrier": """
{expediteur_nom}
{expediteur_adresse}
{expediteur_telephone}
{expediteur_email}

{destinataire_nom}
{destinataire_adresse}

{lieu}, le {date}

Objet : {objet_courrier}

{formule_appel},

{corps_courrier}

{formule_politesse}

{signature}

P.J. : {pieces_jointes}
"""
        }
    
    def _load_custom_templates(self):
        """Charge les templates personnalisés depuis le dossier templates"""
        if not self.templates_dir.exists():
            return
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    custom_templates = json.load(f)
                    self.templates.update(custom_templates)
                    logger.info(f"Templates personnalisés chargés depuis {template_file}")
            except Exception as e:
                logger.error(f"Erreur chargement template {template_file}: {e}")
    
    def get_template(self, template_name: str) -> Optional[str]:
        """Récupère un template par son nom"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """Liste tous les templates disponibles"""
        return list(self.templates.keys())
    
    def add_template(self, name: str, content: str):
        """Ajoute un nouveau template"""
        self.templates[name] = content
    
    def save_template(self, name: str, content: str, filename: Optional[str] = None):
        """Sauvegarde un template dans un fichier"""
        if not filename:
            filename = f"{name}_template.json"
        
        filepath = self.templates_dir / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({name: content}, f, ensure_ascii=False, indent=2)
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """Extrait les variables d'un template (format {variable})"""
        template = self.get_template(template_name)
        if not template:
            return []
        
        import re
        # Trouve toutes les variables entre accolades
        variables = re.findall(r'\{([^}]+)\}', template)
        return list(set(variables))  # Retirer les doublons
    
    def fill_template(self, template_name: str, context: Dict[str, str]) -> Optional[str]:
        """Remplit un template avec les valeurs du contexte"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        try:
            return template.format(**context)
        except KeyError as e:
            logger.error(f"Variable manquante dans le contexte: {e}")
            # Retourner le template avec les variables manquantes non remplacées
            for key, value in context.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
    
    def create_template_from_document(self, document: str, variables: List[str]) -> str:
        """
        Crée un template à partir d'un document en remplaçant 
        certaines parties par des variables
        """
        template = document
        for var in variables:
            # Ici on pourrait implémenter une logique plus sophistiquée
            # pour identifier et remplacer les parties du document
            pass
        return template
"""Module de génération pour documents juridiques longs (25-50+ pages)"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import time

# Import des configurations
from config.cahier_des_charges import (
    STRUCTURES_ACTES, 
    PROMPTS_GENERATION,
    INFRACTIONS_PENALES,
    FORMULES_JURIDIQUES
)

# Import du gestionnaire LLM
try:
    from managers.llm_manager import get_llm_manager
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# ========================= GÉNÉRATEUR DOCUMENTS LONGS =========================

class GenerateurDocumentsLongs:
    """Générateur spécialisé pour documents juridiques de 25-50+ pages"""
    
    def __init__(self):
        self.llm_manager = get_llm_manager() if LLM_AVAILABLE else None
        self.max_tokens_per_section = 4000  # Limite par section pour éviter les coupures
        
    async def generer_document_long(self, type_acte: str, params: Dict) -> Dict[str, Any]:
        """
        Génère un document long par sections pour atteindre 25-50+ pages
        
        Returns:
            Dict avec le document complet et les métadonnées
        """
        
        # Récupérer la structure et les cibles
        structure = STRUCTURES_ACTES.get(type_acte, {})
        longueur_cible = structure.get('longueur_cible', 20000)
        longueur_min = structure.get('longueur_min', 15000)
        longueur_max = structure.get('longueur_max', 30000)
        
        st.info(f"""
        📋 Génération d'un document complexe en cours...
        - Type : {type_acte.replace('_', ' ').title()}
        - Longueur cible : {longueur_cible:,} mots (~{longueur_cible//500} pages)
        - Plage : {longueur_min:,} à {longueur_max:,} mots
        """)
        
        # Initialiser le document
        document = {
            'type': type_acte,
            'sections': {},
            'contenu_complet': '',
            'metadata': {
                'longueur_mots': 0,
                'nb_pages_estimees': 0,
                'temps_generation': 0,
                'sections_generees': 0
            }
        }
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Timer
        start_time = time.time()
        
        # Générer section par section
        sections = structure.get('sections', [])
        total_sections = len(sections)
        
        for idx, section in enumerate(sections):
            status_text.text(f"⏳ Génération de la section : {section.replace('_', ' ').title()}...")
            
            # Calculer la longueur cible pour cette section
            section_weight = self._get_section_weight(section, type_acte)
            section_target = int(longueur_cible * section_weight)
            
            # Générer la section
            section_content = await self._generer_section_longue(
                section=section,
                type_acte=type_acte,
                params=params,
                target_length=section_target,
                context=document['sections']  # Passer les sections précédentes pour cohérence
            )
            
            # Stocker la section
            document['sections'][section] = section_content
            
            # Mettre à jour les métriques
            section_words = len(section_content.split())
            document['metadata']['longueur_mots'] += section_words
            document['metadata']['sections_generees'] += 1
            
            # Mettre à jour la progress bar
            progress = (idx + 1) / total_sections
            progress_bar.progress(progress)
            
            # Afficher les stats intermédiaires
            status_text.text(
                f"✅ Section '{section}' générée : {section_words:,} mots | "
                f"Total : {document['metadata']['longueur_mots']:,} mots"
            )
            
            # Pause pour éviter la surcharge
            await asyncio.sleep(0.5)
        
        # Assembler le document complet
        status_text.text("🔄 Assemblage du document final...")
        document['contenu_complet'] = self._assembler_document_long(
            sections=document['sections'],
            type_acte=type_acte,
            params=params
        )
        
        # Vérifier et ajuster la longueur si nécessaire
        mots_actuels = len(document['contenu_complet'].split())
        
        if mots_actuels < longueur_min:
            status_text.text("📝 Enrichissement du document pour atteindre la longueur minimale...")
            document = await self._enrichir_document(document, longueur_min, params)
        
        # Finaliser les métadonnées
        document['metadata']['longueur_mots'] = len(document['contenu_complet'].split())
        document['metadata']['nb_pages_estimees'] = document['metadata']['longueur_mots'] // 500
        document['metadata']['temps_generation'] = time.time() - start_time
        
        # Affichage final
        progress_bar.progress(1.0)
        status_text.text(
            f"✅ Document généré : {document['metadata']['longueur_mots']:,} mots "
            f"(~{document['metadata']['nb_pages_estimees']} pages) "
            f"en {document['metadata']['temps_generation']:.1f} secondes"
        )
        
        return document
    
    def _get_section_weight(self, section: str, type_acte: str) -> float:
        """Détermine le poids relatif d'une section dans le document"""
        
        # Poids par défaut selon le type de section
        weights = {
            # Sections majeures (40-50% du document)
            'faits': 0.35,
            'faits_detailles': 0.40,
            'faits_procedure': 0.35,
            'expose_faits': 0.35,
            
            # Discussion juridique (30-40% du document)
            'discussion': 0.30,
            'discussion_juridique': 0.35,
            'discussion_par_qualification': 0.35,
            'qualification_approfondie': 0.35,
            'critique_motifs_droit': 0.25,
            'critique_motifs_fait': 0.25,
            
            # Parties techniques (10-15%)
            'nullite_copj': 0.15,
            'application_espece': 0.10,
            'grief': 0.10,
            'evolution_accusations': 0.15,
            
            # Préjudices et demandes (10-15%)
            'prejudice_demandes': 0.15,
            'prejudices': 0.10,
            'volet_civil': 0.10,
            
            # Parties formelles (5-10%)
            'en_tete': 0.05,
            'identite_complete': 0.05,
            'parties': 0.05,
            'dispositif': 0.05,
            'par_ces_motifs': 0.05,
            'demandes': 0.05,
            
            # Autres
            'pieces': 0.03,
            'election_domicile': 0.02,
            'consignation': 0.02
        }
        
        # Ajustements selon le type d'acte
        if type_acte == 'plainte_cpc' and section == 'faits_detailles':
            return 0.45  # Les faits sont cruciaux dans une plainte
        elif type_acte == 'conclusions_fond' and section == 'discussion_par_qualification':
            return 0.40  # La discussion est centrale
        elif type_acte == 'conclusions_nullite' and section in ['nullite_copj', 'grief']:
            return 0.20  # Plus de poids sur les nullités
        
        return weights.get(section, 0.10)
    
    async def _generer_section_longue(self, section: str, type_acte: str, 
                                     params: Dict, target_length: int,
                                     context: Dict) -> str:
        """Génère une section longue et détaillée"""
        
        # Créer un prompt spécifique pour la section
        prompt = self._creer_prompt_section_longue(
            section, type_acte, params, target_length, context
        )
        
        if not self.llm_manager:
            # Fallback sans LLM
            return self._generer_section_template_longue(
                section, type_acte, params, target_length
            )
        
        # Pour les sections très longues, générer en plusieurs passes
        if target_length > 3000:
            return await self._generer_section_multi_passes(
                prompt, target_length, section
            )
        else:
            # Génération simple pour sections courtes
            response = self.llm_manager.query_single_llm(
                provider="anthropic",
                query=prompt,
                system_prompt=PROMPTS_GENERATION['style_instruction'],
                max_tokens=self.max_tokens_per_section
            )
            
            if response['success']:
                return response['response']
            else:
                return self._generer_section_template_longue(
                    section, type_acte, params, target_length
                )
    
    async def _generer_section_multi_passes(self, base_prompt: str, 
                                          target_length: int, 
                                          section_name: str) -> str:
        """Génère une section en plusieurs passes pour atteindre la longueur cible"""
        
        content_parts = []
        current_length = 0
        max_passes = 5  # Maximum 5 passes pour éviter les boucles infinies
        
        for pass_num in range(max_passes):
            remaining_words = target_length - current_length
            
            if remaining_words <= 0:
                break
            
            # Adapter le prompt pour la passe courante
            if pass_num == 0:
                prompt = base_prompt
            else:
                prompt = f"""{base_prompt}
IMPORTANT : Ceci est la SUITE de la section (partie {pass_num + 1}).
Reprends là où tu t'es arrêté et continue le développement.
Il reste environ {remaining_words} mots à générer pour cette section.
NE PAS répéter ce qui a déjà été dit, mais CONTINUER et APPROFONDIR."""
            
            # Générer
            response = self.llm_manager.query_single_llm(
                provider="anthropic",
                query=prompt,
                system_prompt=PROMPTS_GENERATION['style_instruction'],
                max_tokens=self.max_tokens_per_section
            )
            
            if response['success']:
                part_content = response['response']
                content_parts.append(part_content)
                current_length += len(part_content.split())
                
                # Progress pour cette section
                progress = min(current_length / target_length, 1.0)
                st.progress(progress, f"Section '{section_name}' : {current_length:,}/{target_length:,} mots")
            else:
                break
        
        # Assembler les parties
        return '\n\n'.join(content_parts)
    
    def _creer_prompt_section_longue(self, section: str, type_acte: str,
                                    params: Dict, target_length: int,
                                    context: Dict) -> str:
        """Crée un prompt détaillé pour générer une section longue"""
        
        parties = params.get('parties', {})
        infractions = params.get('infractions', [])
        contexte_affaire = params.get('contexte', '')
        
        # Prompts spécialisés par section
        prompts_sections = {
            'faits_detailles': f"""
Rédige un EXPOSÉ EXHAUSTIF DES FAITS pour une {type_acte}.
Longueur IMPÉRATIVE : {target_length} mots MINIMUM.
PARTIES CONCERNÉES :
- Demandeurs : {', '.join(parties.get('demandeurs', []))}
- Défendeurs : {', '.join(parties.get('defendeurs', []))}
CONTEXTE : {contexte_affaire}
STRUCTURE OBLIGATOIRE :
I. PRÉSENTATION GÉNÉRALE DE L'AFFAIRE (20% du texte)
   A. Les acteurs en présence
      - Présentation détaillée de chaque partie
      - Historique des relations
      - Contexte économique et social
   
   B. L'environnement de l'affaire
      - Secteur d'activité
      - Enjeux financiers
      - Contexte réglementaire
II. GENÈSE DES FAITS (25% du texte)
    A. Les origines du litige
       - Premiers contacts
       - Négociations initiales
       - Évolution des relations
    
    B. Les premiers signes de difficultés
       - Indices avant-coureurs
       - Premières irrégularités constatées
       - Réactions des parties
III. CHRONOLOGIE DÉTAILLÉE DES FAITS (35% du texte)
     Pour CHAQUE événement significatif :
     - Date précise
     - Acteurs impliqués
     - Description détaillée de l'événement
     - Documents associés (avec cote précise)
     - Conséquences immédiates
     - Analyse de la pertinence
IV. ANALYSE DES MÉCANISMES FRAUDULEUX (20% du texte)
    A. Schémas mis en place
       - Description technique
       - Acteurs et rôles
       - Flux financiers
    
    B. Modes opératoires
       - Techniques utilisées
       - Dissimulations
       - Complicités
CONSIGNES IMPÉRATIVES :
- NE JAMAIS résumer ou synthétiser
- Développer CHAQUE point en profondeur
- Utiliser des phrases longues et complexes
- Multiplier les détails factuels
- Citer systématiquement les pièces
- Inclure des verbatim de documents importants
- Analyser les motivations des acteurs
- Décrire l'ambiance, le contexte
- Utiliser un vocabulaire riche et varié
""",

            'discussion_par_qualification': f"""
Rédige une DISCUSSION JURIDIQUE EXHAUSTIVE pour une {type_acte}.
Longueur IMPÉRATIVE : {target_length} mots MINIMUM.
INFRACTIONS À ANALYSER : {', '.join(infractions)}
STRUCTURE PAR INFRACTION (répéter pour chaque) :
I. {infractions[0] if infractions else '[INFRACTION]'} (3000-4000 mots par infraction)
   
   A. CADRE LÉGAL EXHAUSTIF (1000+ mots)
      1. Textes d'incrimination
         - Citation intégrale des articles
         - Analyse grammaticale et sémantique
         - Portée de chaque terme
      
      2. Évolution législative
         - Historique des modifications
         - Travaux préparatoires
         - Intentions du législateur
      
      3. Doctrine autorisée
         - Principaux auteurs (citations longues)
         - Débats doctrinaux
         - Positions divergentes
   B. ÉLÉMENTS CONSTITUTIFS DÉTAILLÉS (1500+ mots)
      1. Élément matériel
         a) Comportement incriminé
            - Nature exacte de l'acte
            - Modalités de commission
            - Circonstances aggravantes
         
         b) Conditions préalables
            - Qualité de l'auteur
            - Contexte de commission
            - Éléments objectifs
         
         c) Résultat
            - Préjudice requis
            - Lien de causalité
            - Étendue du dommage
      
      2. Élément moral
         a) Intention générale
            - Conscience de l'illégalité
            - Volonté de l'acte
         
         b) Dol spécial (si requis)
            - Intention particulière
            - Mobile (pertinence)
         
         c) Preuves de l'intention
            - Indices matériels
            - Comportements révélateurs
            - Déclarations
   C. APPLICATION MINUTIEUSE AUX FAITS (1500+ mots)
      1. Correspondance avec l'élément matériel
         - Chaque acte reproché
         - Chaque condition vérifiée
         - Preuves documentaires (PIÈCES n°...)
      
      2. Démonstration de l'élément moral
         - Indices de l'intention
         - Faisceau de preuves
         - Réfutation des justifications
      
      3. Caractérisation complète
         - Synthèse probatoire
         - Force de la démonstration
   D. JURISPRUDENCE EXHAUSTIVE (1000+ mots)
      Pour CHAQUE arrêt cité (minimum 10 arrêts) :
      - Référence complète
      - Faits de l'espèce
      - Solution retenue
      - Principe dégagé
      - Application au cas présent
      - Distinction éventuelle
CONSIGNES :
- Développer CHAQUE point sans exception
- Ne JAMAIS dire "il convient de noter" mais développer
- Multiplier les citations de doctrine
- Analyser en profondeur chaque jurisprudence
- Anticiper TOUTES les objections
- Proposer des interprétations alternatives
- Conclure chaque partie par une synthèse partielle
""",

            'prejudice_demandes': f"""
Rédige une section PRÉJUDICES ET DEMANDES exhaustive.
Longueur IMPÉRATIVE : {target_length} mots MINIMUM.
STRUCTURE DÉTAILLÉE :
I. ANALYSE EXHAUSTIVE DES PRÉJUDICES (70% du texte)
   
   A. PRÉJUDICES PATRIMONIAUX DIRECTS
      1. Détournements et pertes sèches
         - Inventaire exhaustif
         - Montants précis avec calculs
         - Références aux pièces comptables
         - Méthodes d'évaluation
      
      2. Surcoûts et dépenses induites
         - Frais d'expertise
         - Honoraires supplémentaires
         - Coûts de restructuration
         - Mesures correctives
      
      3. Évaluation consolidée
         - Tableau récapitulatif détaillé
         - Actualisations et intérêts
         - Projections
   B. PRÉJUDICES PATRIMONIAUX INDIRECTS
      1. Pertes d'exploitation
         - Analyse sur 3-5 ans
         - Comparaison avec prévisions
         - Impact sur la trésorerie
         - Calculs détaillés
      
      2. Perte de chance et manque à gagner
         - Opportunités manquées
         - Contrats perdus
         - Développements avortés
         - Quantification argumentée
      
      3. Dépréciation d'actifs
         - Valeur de l'entreprise
         - Goodwill
         - Brevets et marques
   C. PRÉJUDICES EXTRA-PATRIMONIAUX
      1. Préjudice moral
         - Souffrance psychologique
         - Stress et anxiété
         - Impact sur la santé
         - Jurisprudence sur quantum
      
      2. Préjudice d'image et réputation
         - Analyse médiatique
         - Impact commercial
         - Perte de confiance
         - Coût de reconstruction
      
      3. Préjudice social
         - Relations professionnelles
         - Statut social
         - Carrière
II. DEMANDES CIRCONSTANCIÉES (30% du texte)
    
    A. DEMANDES PRINCIPALES
       1. Au pénal
          - Déclaration de culpabilité
          - Peines requises (argumentation)
          - Peines complémentaires
       
       2. Au civil
          - Dommages-intérêts (détail par poste)
          - Intérêts légaux
          - Capitalisation
          - Article 475-1 CPP
    
    B. DEMANDES SUBSIDIAIRES
       - Expertises complémentaires
       - Mesures d'instruction
       - Provisions
    
    C. DEMANDES ACCESSOIRES
       - Publication jugement
       - Exécution provisoire
       - Contrainte judiciaire
Développer CHAQUE poste de préjudice sur 200-300 mots minimum.
Justifier CHAQUE montant par des calculs détaillés.
Citer la jurisprudence sur l'évaluation des préjudices.
"""
        }
        
        # Prompt par défaut si section non définie
        default_prompt = f"""
Rédige la section '{section}' pour une {type_acte}.
Longueur IMPÉRATIVE : {target_length} mots MINIMUM.
Contexte de l'affaire : {contexte_affaire}
Parties : {parties}
Infractions : {infractions}
CONSIGNES ABSOLUES :
1. Développer de manière EXHAUSTIVE sans jamais résumer
2. Utiliser un style juridique élaboré avec phrases complexes
3. Multiplier les sous-parties et développements
4. Inclure de nombreuses références (doctrine, jurisprudence)
5. Analyser chaque point en profondeur
6. Ne JAMAIS utiliser de formules creuses ("il convient de", "force est de constater")
7. TOUJOURS développer, expliquer, analyser, approfondir
8. Minimum 30-40 lignes par paragraphe
9. Minimum 5-6 paragraphes par sous-partie
10. Utiliser un vocabulaire juridique riche et varié
Le texte doit être dense, technique et exhaustif.
"""
        
        return prompts_sections.get(section, default_prompt)
    
    def _generer_section_template_longue(self, section: str, type_acte: str,
                                       params: Dict, target_length: int) -> str:
        """Génère un template long pour une section (fallback)"""
        
        # Templates étendus pour chaque section
        # Ici on pourrait avoir des templates très détaillés
        # Pour l'instant, on génère un texte indicatif
        
        lines = [f"\n[SECTION : {section.upper().replace('_', ' ')}]\n"]
        lines.append(f"[Cette section doit contenir environ {target_length} mots]\n")
        
        # Générer des sous-sections selon le type
        if 'faits' in section:
            lines.extend([
                "I. CONTEXTE GÉNÉRAL DE L'AFFAIRE\n",
                "[Développement sur 500-800 mots : présentation des parties, historique...]\n",
                "II. CHRONOLOGIE DÉTAILLÉE DES FAITS\n",
                "[Développement sur 1500-2000 mots : chaque événement daté et détaillé...]\n",
                "III. ANALYSE DES MÉCANISMES MIS EN ŒUVRE\n",
                "[Développement sur 800-1000 mots : schémas frauduleux, montages...]\n"
            ])
        elif 'discussion' in section or 'qualification' in section:
            for inf in params.get('infractions', ['[INFRACTION]']):
                lines.extend([
                    f"\nI. SUR L'{inf.upper()}\n",
                    "A. Rappel du cadre légal\n[500-700 mots]\n",
                    "B. Éléments constitutifs\n[700-1000 mots]\n",
                    "C. Application aux faits\n[800-1000 mots]\n",
                    "D. Jurisprudence\n[500-700 mots]\n"
                ])
        
        lines.append(f"\n[Fin de section - Total visé : {target_length} mots]\n")
        
        return '\n'.join(lines)
    
    def _assembler_document_long(self, sections: Dict[str, str], 
                                type_acte: str, params: Dict) -> str:
        """Assemble toutes les sections en un document cohérent"""
        
        # En-tête du document
        document_parts = []
        
        # Titre et en-tête selon le type
        if type_acte == 'plainte_cpc':
            document_parts.append("""
PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE
À L'ATTENTION DE MONSIEUR LE DOYEN DES JUGES D'INSTRUCTION
TRIBUNAL JUDICIAIRE DE [VILLE]
""")
        elif 'conclusions' in type_acte:
            document_parts.append("""
CONCLUSIONS
POUR : [CLIENT]
CONTRE : [PARTIES ADVERSES]
""")
        
        # Ajouter chaque section avec sa numérotation
        section_number = 1
        for section_key, section_content in sections.items():
            # Titre de section
            section_title = section_key.upper().replace('_', ' ')
            
            # Numérotation romaine pour les grandes sections
            roman_num = self._to_roman(section_number)
            document_parts.append(f"\n\n{roman_num}. {section_title}\n\n")
            
            # Contenu de la section
            document_parts.append(section_content)
            
            section_number += 1
        
        # Conclusion et signature
        document_parts.append(self._generer_conclusion_longue(type_acte, params))
        
        return ''.join(document_parts)
    
    def _to_roman(self, num: int) -> str:
        """Convertit un nombre en chiffre romain"""
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
    
    def _generer_conclusion_longue(self, type_acte: str, params: Dict) -> str:
        """Génère une conclusion développée pour le document"""
        
        if type_acte == 'plainte_cpc':
            return """
PAR CES MOTIFS
Il est demandé à Monsieur le Doyen des Juges d'Instruction de bien vouloir :
- RECEVOIR la présente plainte avec constitution de partie civile ;
- CONSTATER la recevabilité et le bien-fondé de la constitution de partie civile ;
- ORDONNER l'ouverture d'une information judiciaire des chefs de :
  * [LISTE DES INFRACTIONS]
  
- PROCÉDER ou faire procéder à tous actes d'information utiles à la manifestation de la vérité ;
- ORDONNER toutes expertises nécessaires ;
- TRANSMETTRE le dossier au Parquet pour réquisitions ;
- RENVOYER les mis en cause devant la juridiction de jugement ;
Et en tout état de cause,
- CONDAMNER les responsables à réparer l'intégralité du préjudice subi ;
- DIRE que la présente décision sera exécutoire par provision ;
- CONDAMNER les défendeurs aux entiers dépens.
SOUS TOUTES RÉSERVES
Fait à [VILLE], le """ + datetime.now().strftime('%d/%m/%Y') + """
[SIGNATURE]
BORDEREAU DE PIÈCES COMMUNIQUÉES
[Liste des pièces]
"""
        else:
            return """
PAR CES MOTIFS
[DEMANDES SPÉCIFIQUES AU TYPE D'ACTE]
SOUS TOUTES RÉSERVES
[SIGNATURE ET DATE]
"""
    
    async def _enrichir_document(self, document: Dict, longueur_min: int, 
                               params: Dict) -> Dict:
        """Enrichit un document pour atteindre la longueur minimale"""
        
        mots_actuels = document['metadata']['longueur_mots']
        mots_manquants = longueur_min - mots_actuels
        
        if mots_manquants <= 0:
            return document
        
        # Identifier les sections à enrichir (les plus importantes)
        sections_a_enrichir = []
        for section, content in document['sections'].items():
            if 'faits' in section or 'discussion' in section:
                sections_a_enrichir.append(section)
        
        if not sections_a_enrichir:
            sections_a_enrichir = list(document['sections'].keys())
        
        # Répartir les mots manquants
        mots_par_section = mots_manquants // len(sections_a_enrichir)
        
        for section in sections_a_enrichir:
            # Générer du contenu supplémentaire
            prompt_enrichissement = f"""
La section '{section}' doit être ENRICHIE avec {mots_par_section} mots supplémentaires.
Contenu actuel à enrichir :
{document['sections'][section][-1000:]}  # Derniers 1000 caractères
CONSIGNES :
- Ajouter des développements complémentaires
- Approfondir l'analyse
- Ajouter des exemples jurisprudentiels
- Développer des arguments subsidiaires
- NE PAS répéter ce qui a déjà été dit
- CONTINUER et APPROFONDIR le raisonnement
"""
            
            if self.llm_manager:
                response = self.llm_manager.query_single_llm(
                    provider="anthropic",
                    query=prompt_enrichissement,
                    system_prompt=PROMPTS_GENERATION['style_instruction']
                )
                
                if response['success']:
                    # Ajouter le contenu enrichi
                    document['sections'][section] += "\n\n" + response['response']
        
        # Reconstruire le document complet
        document['contenu_complet'] = self._assembler_document_long(
            document['sections'],
            document['type'],
            params
        )
        
        # Mettre à jour les métadonnées
        document['metadata']['longueur_mots'] = len(document['contenu_complet'].split())
        document['metadata']['nb_pages_estimees'] = document['metadata']['longueur_mots'] // 500
        
        return document

# ========================= INTERFACE STREAMLIT =========================

def show_generation_longue_interface():
    """Interface pour la génération de documents longs"""
    
    st.header("📜 Génération de documents juridiques longs (25-50+ pages)")
    
    st.info("""
    🎯 **Module spécialisé pour documents complexes**
    
    Ce module génère des actes juridiques exhaustifs de 25 à 50+ pages, 
    adaptés aux dossiers complexes de droit pénal des affaires.
    
    **Caractéristiques :**
    - Développements approfondis de chaque point
    - Analyse exhaustive des faits et du droit
    - Citations doctrinales et jurisprudentielles nombreuses
    - Structure rigoureuse et hiérarchisée
    """)
    
    # Initialiser le générateur
    if 'generateur_long' not in st.session_state:
        st.session_state.generateur_long = GenerateurDocumentsLongs()
    
    generateur = st.session_state.generateur_long
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        type_acte = st.selectbox(
            "Type de document",
            [
                'plainte_cpc',
                'conclusions_fond',
                'conclusions_nullite',
                'conclusions_appel',
                'observations_175',
                'plainte_simple',
                'citation_directe'
            ],
            format_func=lambda x: {
                'plainte_cpc': 'Plainte avec CPC (50+ pages)',
                'conclusions_fond': 'Conclusions au fond (40-50 pages)',
                'conclusions_nullite': 'Conclusions de nullité (30-35 pages)',
                'conclusions_appel': 'Conclusions d\'appel (40-45 pages)',
                'observations_175': 'Observations art. 175 (40-45 pages)',
                'plainte_simple': 'Plainte simple (25-30 pages)',
                'citation_directe': 'Citation directe (20-25 pages)'
            }.get(x, x)
        )
    
    with col2:
        # Afficher la longueur cible
        structure = STRUCTURES_ACTES.get(type_acte, {})
        st.metric(
            "Longueur cible",
            f"{structure.get('longueur_cible', 20000):,} mots",
            f"~{structure.get('longueur_cible', 20000)//500} pages"
        )
    
    # Parties
    st.subheader("👥 Configuration des parties")
    
    col1, col2 = st.columns(2)
    
    with col1:
        demandeurs = st.text_area(
            "Demandeurs / Plaignants",
            height=100,
            placeholder="Un par ligne\nEx: SCI PATRIMOINE\nM. DUPONT Jean"
        )
    
    with col2:
        defendeurs = st.text_area(
            "Défendeurs / Mis en cause",
            height=100,
            placeholder="Un par ligne\nEx: SA CONSTRUCTION\nM. MARTIN Pierre"
        )
    
    # Infractions et contexte
    st.subheader("🚨 Infractions et contexte")
    
    infractions = st.multiselect(
        "Infractions",
        [
            "Abus de biens sociaux",
            "Corruption",
            "Escroquerie",
            "Abus de confiance",
            "Blanchiment",
            "Faux et usage de faux",
            "Détournement de fonds publics",
            "Favoritisme",
            "Prise illégale d'intérêts",
            "Trafic d'influence"
        ]
    )
    
    contexte = st.text_area(
        "Contexte détaillé de l'affaire",
        height=150,
        placeholder="Décrivez l'affaire, les montants en jeu, la période des faits..."
    )
    
    # Options avancées
    with st.expander("⚙️ Options avancées"):
        col1, col2 = st.columns(2)
        
        with col1:
            enrichissement_auto = st.checkbox(
                "Enrichissement automatique si trop court",
                value=True,
                help="Ajoute automatiquement du contenu si la longueur minimale n'est pas atteinte"
            )
        
        with col2:
            parallel_generation = st.checkbox(
                "Génération parallèle (plus rapide)",
                value=False,
                help="Génère plusieurs sections simultanément (expérimental)"
            )
    
    # Bouton de génération
    if st.button("🚀 Générer le document long", type="primary", use_container_width=True):
        
        # Validation
        if not (demandeurs.strip() or defendeurs.strip()):
            st.error("Veuillez renseigner au moins une partie")
            return
        
        if not infractions:
            st.error("Veuillez sélectionner au moins une infraction")
            return
        
        # Préparer les paramètres
        params = {
            'parties': {
                'demandeurs': [d.strip() for d in demandeurs.split('\n') if d.strip()],
                'defendeurs': [d.strip() for d in defendeurs.split('\n') if d.strip()]
            },
            'infractions': infractions,
            'contexte': contexte,
            'options': {
                'enrichissement_auto': enrichissement_auto,
                'parallel': parallel_generation
            }
        }
        
        # Générer
        asyncio.run(generer_document_interface(generateur, type_acte, params))

async def generer_document_interface(generateur, type_acte, params):
    """Interface de génération avec gestion asynchrone"""
    
    try:
        # Générer le document
        document = await generateur.generer_document_long(type_acte, params)
        
        # Stocker le résultat
        st.session_state.document_long_genere = document
        
        # Afficher les résultats
        st.success(f"""
        ✅ **Document généré avec succès !**
        
        - **Longueur :** {document['metadata']['longueur_mots']:,} mots
        - **Pages estimées :** ~{document['metadata']['nb_pages_estimees']} pages
        - **Temps de génération :** {document['metadata']['temps_generation']:.1f} secondes
        - **Sections générées :** {document['metadata']['sections_generees']}
        """)
        
        # Aperçu du document
        with st.expander("📄 Aperçu du document", expanded=True):
            # Afficher les premières lignes
            preview_lines = document['contenu_complet'].split('\n')[:50]
            st.text('\n'.join(preview_lines))
            st.info(f"... (document complet : {document['metadata']['longueur_mots']:,} mots)")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "📥 Télécharger (TXT)",
                document['contenu_complet'].encode('utf-8'),
                file_name=f"{type_acte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            if st.button("📊 Voir les statistiques détaillées"):
                show_document_statistics_detailed(document)
        
        with col3:
            if st.button("✏️ Éditer le document"):
                st.session_state.edit_mode = True
                st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération : {str(e)}")
        import traceback
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())

def show_document_statistics_detailed(document: Dict):
    """Affiche des statistiques détaillées sur le document généré"""
    
    with st.expander("📊 Statistiques détaillées", expanded=True):
        
        # Métriques générales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mots totaux", f"{document['metadata']['longueur_mots']:,}")
        with col2:
            st.metric("Pages", f"~{document['metadata']['nb_pages_estimees']}")
        with col3:
            st.metric("Sections", document['metadata']['sections_generees'])
        with col4:
            st.metric("Temps", f"{document['metadata']['temps_generation']:.1f}s")
        
        # Répartition par section
        st.subheader("📑 Répartition par section")
        
        section_stats = []
        for section, content in document['sections'].items():
            words = len(content.split())
            percentage = (words / document['metadata']['longueur_mots']) * 100
            section_stats.append({
                'Section': section.replace('_', ' ').title(),
                'Mots': words,
                'Pourcentage': f"{percentage:.1f}%",
                'Pages': f"~{words//500}"
            })
        
        import pandas as pd
        df = pd.DataFrame(section_stats)
        st.dataframe(df, use_container_width=True)
        
        # Graphique de répartition
        st.subheader("📊 Visualisation")
        chart_data = pd.DataFrame({
            'Section': [s['Section'] for s in section_stats],
            'Mots': [s['Mots'] for s in section_stats]
        })
        st.bar_chart(chart_data.set_index('Section'))

# ========================= INTÉGRATION =========================

def integrate_with_main_module():
    """Intègre ce module avec le module principal de génération"""
    
    # Cette fonction peut être appelée depuis generation_juridique.py
    # pour ajouter l'option de génération longue
    pass

if __name__ == "__main__":
    # Test du module
    st.set_page_config(page_title="Génération Documents Longs", page_icon="📜", layout="wide")
    show_generation_longue_interface()
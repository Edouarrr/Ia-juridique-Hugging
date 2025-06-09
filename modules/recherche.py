# modules/recherche.py
"""Module de recherche unifié avec toutes les fonctionnalités avancées intégrées"""

import streamlit as st
import asyncio
import re
import html
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from difflib import SequenceMatcher

# ========================= IMPORTS CENTRALISÉS =========================

# Import du service de recherche depuis les managers
try:
    from managers import UniversalSearchService, get_universal_search_service
    SEARCH_SERVICE_AVAILABLE = True
except ImportError:
    SEARCH_SERVICE_AVAILABLE = False

# Import des dataclasses et configurations
from modules.dataclasses import (
    Document, DocumentJuridique, Partie, TypePartie, PhaseProcedure,
    TypeDocument, TypeAnalyse, QueryAnalysis, InfractionAffaires,
    PieceSelectionnee, BordereauPieces, collect_available_documents,
    group_documents_by_category, determine_document_category,
    calculate_piece_relevance, create_bordereau, create_bordereau_document,
    InfractionIdentifiee, FactWithSource, SourceReference, ArgumentStructure,
    StyleLearningResult, StyleConfig, learn_document_style
)

from models.configurations import (
    DEFAULT_STYLE_CONFIGS, BUILTIN_DOCUMENT_TEMPLATES,
    DEFAULT_LETTERHEADS, FORMULES_JURIDIQUES,
    ARGUMENTATION_PATTERNS, ANALYSIS_CONFIGS
)

# ========================= MANAGERS AVANCÉS - IMPORT CONDITIONNEL =========================

MANAGERS = {
    'company_info': False,
    'jurisprudence_verifier': False,
    'style_analyzer': False,
    'dynamic_generators': False,
    'document_manager': False,
    'legal_search': False,
    'multi_llm': False
}

# Import des managers avec gestion d'erreur individuelle
try:
    from managers.company_info_manager import CompanyInfoManager
    MANAGERS['company_info'] = True
except ImportError as e:
    print(f"Import CompanyInfoManager failed: {e}")

try:
    from managers.jurisprudence_verifier import JurisprudenceVerifier
    MANAGERS['jurisprudence_verifier'] = True
except ImportError as e:
    print(f"Import JurisprudenceVerifier failed: {e}")

try:
    from managers.style_analyzer import StyleAnalyzer
    MANAGERS['style_analyzer'] = True
except ImportError as e:
    print(f"Import StyleAnalyzer failed: {e}")

try:
    from managers.dynamic_generators import generate_dynamic_search_prompts, generate_dynamic_templates
    MANAGERS['dynamic_generators'] = True
except ImportError as e:
    print(f"Import dynamic_generators functions failed: {e}")

try:
    from managers.document_manager import DocumentManager
    MANAGERS['document_manager'] = True
except ImportError as e:
    print(f"Import DocumentManager failed: {e}")

try:
    from managers.legal_search import LegalSearchManager
    MANAGERS['legal_search'] = True
except ImportError as e:
    print(f"Import LegalSearchManager failed: {e}")

try:
    from managers.multi_llm_manager import MultiLLMManager
    MANAGERS['multi_llm'] = True
except ImportError as e:
    print(f"Import MultiLLMManager failed: {e}")

# APIs - Import conditionnel
try:
    from utils.api_utils import get_available_models, call_llm_api
    HAS_API_UTILS = True
except ImportError:
    HAS_API_UTILS = False

# ========================= IMPORTS DES MODULES SPÉCIFIQUES =========================

MODULES_AVAILABLE = {}
MODULE_FUNCTIONS = {}

# Import conditionnel de tous les modules
modules_to_import = [
    ('analyse_ia', ['show_page']),
    ('bordereau', ['process_bordereau_request', 'create_bordereau']),
    ('comparison', ['process_comparison_request']),
    ('configuration', ['show_page']),
    ('email', ['process_email_request']),
    ('explorer', ['show_explorer_interface']),
    ('import_export', ['process_import_request', 'process_export_request']),
    ('jurisprudence', ['process_jurisprudence_request', 'show_jurisprudence_interface']),
    ('mapping', ['process_mapping_request']),
    ('plaidoirie', ['process_plaidoirie_request']),
    ('preparation_client', ['process_preparation_client_request']),
    ('redaction_unified', ['process_redaction_request']),
    ('selection_piece', ['show_page']),
    ('synthesis', ['process_synthesis_request']),
    ('templates', ['process_template_request']),
    ('timeline', ['process_timeline_request'])
]

for module_name, functions in modules_to_import:
    try:
        module = __import__(f'modules.{module_name}', fromlist=functions)
        MODULES_AVAILABLE[module_name] = True
        
        for func_name in functions:
            if hasattr(module, func_name):
                if func_name == 'show_page':
                    MODULE_FUNCTIONS[f'{module_name}_page'] = getattr(module, func_name)
                else:
                    MODULE_FUNCTIONS[func_name] = getattr(module, func_name)
    except ImportError:
        MODULES_AVAILABLE[module_name] = False

# ========================= GÉNÉRATION AVANCÉE DE PLAINTES =========================

async def generate_advanced_plainte(query: str):
    """Génère une plainte avancée avec toutes les fonctionnalités"""
    
    st.markdown("### 🚀 Génération avancée de plainte")
    
    # Analyser la requête
    analysis = analyze_plainte_request(query)
    
    # Vérifier si CPC
    is_cpc = check_if_cpc_required(query)
    
    if is_cpc:
        st.info("📋 Génération d'une plainte avec constitution de partie civile EXHAUSTIVE")
        await generate_exhaustive_cpc_plainte(analysis)
    else:
        await generate_standard_plainte(analysis)

def analyze_plainte_request(query: str) -> Dict[str, Any]:
    """Analyse la requête pour extraire les informations"""
    
    # Extraction des parties
    parties_pattern = r'contre\s+([A-Z][A-Za-z\s,&]+?)(?:\s+et\s+|,\s*|$)'
    parties = re.findall(parties_pattern, query, re.IGNORECASE)
    
    # Extraction des infractions
    infractions = []
    infractions_keywords = {
        'abus de biens sociaux': 'Abus de biens sociaux',
        'abs': 'Abus de biens sociaux',
        'corruption': 'Corruption',
        'escroquerie': 'Escroquerie',
        'abus de confiance': 'Abus de confiance',
        'blanchiment': 'Blanchiment'
    }
    
    query_lower = query.lower()
    for keyword, infraction in infractions_keywords.items():
        if keyword in query_lower:
            infractions.append(infraction)
    
    return {
        'parties': parties,
        'infractions': infractions or ['Abus de biens sociaux'],  # Par défaut
        'query': query
    }

def check_if_cpc_required(query: str) -> bool:
    """Vérifie si une CPC est requise"""
    cpc_indicators = [
        'constitution de partie civile',
        'cpc',
        'partie civile',
        'exhaustive',
        'complète'
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in cpc_indicators)

async def generate_exhaustive_cpc_plainte(analysis: Dict[str, Any]):
    """Génère une plainte CPC exhaustive de 8000+ mots"""
    
    with st.spinner("⏳ Génération d'une plainte exhaustive en cours... (cela peut prendre 2-3 minutes)"):
        
        # Options de génération
        col1, col2, col3 = st.columns(3)
        
        with col1:
            temperature = st.slider(
                "🌡️ Créativité",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Plus bas = plus factuel, Plus haut = plus créatif"
            )
        
        with col2:
            model = "claude-3-sonnet" 
            if HAS_API_UTILS:
                models = get_available_models()
                if models:
                    model = st.selectbox("🤖 Modèle", models, index=0)
        
        with col3:
            enrich_parties = st.checkbox(
                "🏢 Enrichir les parties",
                value=True,
                help="Rechercher des informations sur les sociétés"
            )
        
        # Enrichissement des parties si demandé
        enriched_parties = analysis['parties']
        if enrich_parties and MANAGERS['company_info']:
            enriched_parties = await enrich_parties_info(analysis['parties'])
        
        # Générer le prompt détaillé
        prompt = create_exhaustive_cpc_prompt(
            parties=enriched_parties,
            infractions=analysis['infractions']
        )
        
        # Appel à l'API
        try:
            if HAS_API_UTILS:
                response = await call_llm_api(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=8000
                )
                
                # Stocker le résultat
                st.session_state.generated_plainte = response
                st.session_state.search_results = {
                    'type': 'plainte_avancee',
                    'content': response,
                    'metadata': {
                        'parties': enriched_parties,
                        'infractions': analysis['infractions'],
                        'model': model,
                        'length': len(response.split())
                    }
                }
                
                # Afficher les statistiques
                show_plainte_statistics(response)
                
                # Vérifier les jurisprudences si disponible
                if MANAGERS['jurisprudence_verifier']:
                    verify_jurisprudences_in_plainte(response)
                
                # Suggestions d'amélioration
                show_improvement_suggestions(response)
                
            else:
                # Fallback sans API
                st.warning("API non disponible - Génération d'un modèle de plainte")
                generate_plainte_template(enriched_parties, analysis['infractions'])
                
        except Exception as e:
            st.error(f"Erreur lors de la génération : {str(e)}")

async def generate_standard_plainte(analysis: Dict[str, Any]):
    """Génère une plainte standard"""
    
    with st.spinner("⏳ Génération de la plainte..."):
        
        # Options simplifiées
        col1, col2 = st.columns(2)
        
        with col1:
            plainte_type = st.selectbox(
                "Type de plainte",
                ["Simple", "Avec constitution de partie civile"],
                index=1
            )
        
        with col2:
            include_jurisprudence = st.checkbox(
                "📚 Inclure jurisprudences",
                value=True
            )
        
        # Générer
        if HAS_API_UTILS:
            prompt = create_standard_plainte_prompt(
                parties=analysis['parties'],
                infractions=analysis['infractions'],
                plainte_type=plainte_type,
                include_jurisprudence=include_jurisprudence
            )
            
            try:
                response = await call_llm_api(
                    prompt=prompt,
                    model="claude-3-sonnet",
                    temperature=0.3
                )
                
                st.session_state.generated_plainte = response
                st.session_state.search_results = {
                    'type': 'plainte',
                    'content': response
                }
                
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
        else:
            generate_plainte_template(analysis['parties'], analysis['infractions'])

# ========================= ENRICHISSEMENT DES PARTIES =========================

async def enrich_parties_info(parties: List[str]) -> List[Dict[str, Any]]:
    """Enrichit les informations sur les parties"""
    
    if not MANAGERS['company_info']:
        return [{'name': p} for p in parties]
    
    enriched = []
    company_manager = CompanyInfoManager()
    
    for party in parties:
        with st.spinner(f"🔍 Recherche d'informations sur {party}..."):
            info = await company_manager.get_company_info(party)
            
            if info:
                enriched.append({
                    'name': party,
                    'siren': info.get('siren'),
                    'address': info.get('address'),
                    'legal_form': info.get('legal_form'),
                    'capital': info.get('capital'),
                    'executives': info.get('executives', [])
                })
            else:
                enriched.append({'name': party})
    
    return enriched

# ========================= CRÉATION DES PROMPTS =========================

def create_exhaustive_cpc_prompt(parties: List[Any], infractions: List[str]) -> str:
    """Crée un prompt pour une plainte CPC exhaustive"""
    
    parties_text = format_parties_for_prompt(parties)
    infractions_text = ', '.join(infractions)
    
    return f"""
Rédigez une plainte avec constitution de partie civile EXHAUSTIVE et DÉTAILLÉE d'au moins 8000 mots.
PARTIES MISES EN CAUSE :
{parties_text}
INFRACTIONS À DÉVELOPPER :
{infractions_text}
STRUCTURE IMPOSÉE :
1. EN-TÊTE COMPLET
   - Destinataire (Doyen des juges d'instruction)
   - Plaignant (à compléter)
   - Objet détaillé
2. EXPOSÉ EXHAUSTIF DES FAITS (3000+ mots)
   - Contexte détaillé de l'affaire
   - Chronologie précise et complète
   - Description minutieuse de chaque fait
   - Liens entre les protagonistes
   - Montants et préjudices détaillés
3. DISCUSSION JURIDIQUE APPROFONDIE (3000+ mots)
   Pour chaque infraction :
   - Rappel complet des textes
   - Analyse détaillée des éléments constitutifs
   - Application aux faits espèce par espèce
   - Jurisprudences pertinentes citées
   - Réfutation des arguments contraires
4. PRÉJUDICES DÉTAILLÉS (1000+ mots)
   - Préjudice financier chiffré
   - Préjudice moral développé
   - Préjudice d'image
   - Autres préjudices
5. DEMANDES ET CONCLUSION (1000+ mots)
   - Constitution de partie civile motivée
   - Demandes d'actes précises
   - Mesures conservatoires
   - Provision sur dommages-intérêts
CONSIGNES :
- Style juridique soutenu et précis
- Citations de jurisprudences récentes
- Argumentation implacable
- Aucune zone d'ombre
- Anticipation des contre-arguments
"""

def create_standard_plainte_prompt(parties: List[str], infractions: List[str], 
                                  plainte_type: str, include_jurisprudence: bool) -> str:
    """Crée un prompt pour une plainte standard"""
    
    parties_text = ', '.join(parties)
    infractions_text = ', '.join(infractions)
    
    jurisprudence_instruction = ""
    if include_jurisprudence:
        jurisprudence_instruction = "\n- Citez au moins 3 jurisprudences pertinentes"
    
    return f"""
Rédigez une {plainte_type} concernant :
- Parties : {parties_text}
- Infractions : {infractions_text}
Structure :
1. En-tête et qualités
2. Exposé des faits
3. Discussion juridique
4. Préjudices
5. Demandes
Consignes :
- Style juridique professionnel
- Argumentation structurée{jurisprudence_instruction}
- Environ 2000-3000 mots
"""

def format_parties_for_prompt(parties: List[Any]) -> str:
    """Formate les parties pour le prompt"""
    
    if not parties:
        return "À COMPLÉTER"
    
    formatted = []
    for party in parties:
        if isinstance(party, dict):
            text = f"- {party['name']}"
            if party.get('siren'):
                text += f" (SIREN: {party['siren']})"
            if party.get('address'):
                text += f"\n  Siège: {party['address']}"
            if party.get('executives'):
                text += f"\n  Dirigeants: {', '.join(party['executives'][:3])}"
            formatted.append(text)
        else:
            formatted.append(f"- {party}")
    
    return '\n'.join(formatted)

# ========================= VÉRIFICATION ET ANALYSE =========================

def verify_jurisprudences_in_plainte(content: str):
    """Vérifie les jurisprudences citées dans la plainte"""
    
    if not MANAGERS['jurisprudence_verifier']:
        return
    
    with st.expander("🔍 Vérification des jurisprudences"):
        verifier = JurisprudenceVerifier()
        
        # Extraire les références
        jurisprudence_pattern = r'(Cass\.\s+\w+\.?,?\s+\d{1,2}\s+\w+\s+\d{4}|C\.\s*cass\.\s*\w+\.?\s*\d{1,2}\s+\w+\s+\d{4})'
        references = re.findall(jurisprudence_pattern, content)
        
        if references:
            st.write(f"**{len(references)} références trouvées**")
            
            verified = 0
            for ref in references[:5]:  # Vérifier les 5 premières
                if verifier.verify_reference(ref):
                    st.success(f"✅ {ref}")
                    verified += 1
                else:
                    st.warning(f"⚠️ {ref} - Non vérifiée")
            
            reliability = (verified / len(references[:5])) * 100
            st.metric("Taux de fiabilité", f"{reliability:.0f}%")
        else:
            st.info("Aucune jurisprudence détectée")

def show_plainte_statistics(content: str):
    """Affiche les statistiques de la plainte"""
    
    with st.expander("📊 Statistiques du document"):
        words = content.split()
        sentences = content.split('.')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Mots", len(words))
        
        with col2:
            st.metric("Phrases", len(sentences))
        
        with col3:
            st.metric("Pages estimées", f"~{len(words) // 250}")
        
        # Analyse du style si disponible
        if MANAGERS['style_analyzer']:
            analyzer = StyleAnalyzer()
            style_score = analyzer.analyze_style(content)
            
            st.markdown("**Analyse du style :**")
            st.progress(style_score / 100)
            st.caption(f"Score de qualité : {style_score}/100")

def show_improvement_suggestions(content: str):
    """Suggère des améliorations pour la plainte"""
    
    with st.expander("💡 Suggestions d'amélioration"):
        suggestions = []
        
        # Vérifier la longueur
        word_count = len(content.split())
        if word_count < 2000:
            suggestions.append("📝 Développer davantage l'exposé des faits")
        
        # Vérifier les citations
        if content.count('"') < 4:
            suggestions.append("📚 Ajouter plus de citations de jurisprudence")
        
        # Vérifier les montants
        if not re.search(r'\d+\s*€|\d+\s*euros', content):
            suggestions.append("💰 Chiffrer précisément les préjudices")
        
        # Vérifier la structure
        required_sections = ['FAITS', 'DISCUSSION', 'PRÉJUDICE', 'DEMANDE']
        missing = [s for s in required_sections if s not in content.upper()]
        if missing:
            suggestions.append(f"📋 Ajouter sections : {', '.join(missing)}")
        
        if suggestions:
            for suggestion in suggestions:
                st.write(suggestion)
        else:
            st.success("✅ La plainte semble complète !")

# ========================= GÉNÉRATION DE PLAINTES =========================

def generate_plainte_simple(parties_defenderesses: List[str], infractions: List[str]) -> str:
    """Génère une plainte simple"""
    
    parties_text = '\n'.join([f"- {p}" for p in parties_defenderesses]) if parties_defenderesses else "- [À COMPLÉTER]"
    infractions_text = '\n'.join([f"- {i}" for i in infractions]) if infractions else "- [À COMPLÉTER]"
    
    return f"""PLAINTE SIMPLE
À l'attention de Monsieur le Procureur de la République
Tribunal Judiciaire de [VILLE]
[VILLE], le {datetime.now().strftime('%d/%m/%Y')}
OBJET : Plainte
Monsieur le Procureur,
Je soussigné(e) [NOM PRÉNOM]
Demeurant [ADRESSE]
Ai l'honneur de porter plainte contre :
{parties_text}
Pour les faits suivants :
[EXPOSÉ DES FAITS]
Ces faits sont susceptibles de recevoir les qualifications suivantes :
{infractions_text}
Je vous prie d'agréer, Monsieur le Procureur, l'expression de ma considération distinguée.
[SIGNATURE]
Pièces jointes :
- [LISTE DES PIÈCES]
"""

def generate_plainte_cpc(parties_defenderesses: List[str], infractions: List[str], 
                        demandeurs: List[str] = None, options: Dict = None) -> str:
    """Génère une plainte avec constitution de partie civile"""
    
    parties_text = format_parties_list([{'name': p} for p in parties_defenderesses])
    infractions_text = '\n'.join([f"- {i}" for i in infractions]) if infractions else "- [À COMPLÉTER]"
    
    return f"""PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE
Monsieur le Doyen des Juges d'Instruction
Tribunal Judiciaire de [VILLE]
[ADRESSE]
[VILLE], le {datetime.now().strftime('%d/%m/%Y')}
OBJET : Plainte avec constitution de partie civile
RÉFÉRENCES : [À COMPLÉTER]
Monsieur le Doyen,
Je soussigné(e) [NOM PRÉNOM]
Né(e) le [DATE] à [LIEU]
De nationalité française
Profession : [PROFESSION]
Demeurant : [ADRESSE COMPLÈTE]
Téléphone : [TÉLÉPHONE]
Email : [EMAIL]
Ayant pour conseil : [SI APPLICABLE]
Maître [NOM AVOCAT]
Avocat au Barreau de [VILLE]
[ADRESSE CABINET]
Ai l'honneur de déposer entre vos mains une plainte avec constitution de partie civile contre :
{parties_text}
Et toute autre personne que l'instruction révèlerait avoir participé aux faits ci-après exposés.
I. EXPOSÉ DÉTAILLÉ DES FAITS
[DÉVELOPPEMENT DÉTAILLÉ - À COMPLÉTER]
II. DISCUSSION JURIDIQUE
Les faits exposés ci-dessus caractérisent les infractions suivantes :
{infractions_text}
[ANALYSE JURIDIQUE DÉTAILLÉE - À COMPLÉTER]
III. PRÉJUDICES SUBIS
[DÉTAIL DES PRÉJUDICES - À COMPLÉTER]
IV. CONSTITUTION DE PARTIE CIVILE
Par les présents, je déclare me constituer partie civile et demander réparation intégrale de mon préjudice.
Je sollicite :
- La désignation d'un juge d'instruction
- L'ouverture d'une information judiciaire
- Tous actes d'instruction utiles à la manifestation de la vérité
- La mise en examen des personnes mises en cause
- Le renvoi devant la juridiction de jugement
- La condamnation des prévenus
- L'allocation de dommages-intérêts en réparation du préjudice subi
V. PIÈCES JUSTIFICATIVES
Vous trouverez ci-joint :
[LISTE DÉTAILLÉE DES PIÈCES]
Je verse la consignation fixée par vos soins.
Je vous prie d'agréer, Monsieur le Doyen, l'expression de ma considération distinguée.
Fait à [VILLE], le {datetime.now().strftime('%d/%m/%Y')}
[SIGNATURE]
"""

# ========================= TEMPLATES DE FALLBACK =========================

def generate_plainte_template(parties: List[Any], infractions: List[str]):
    """Génère un template de plainte sans API"""
    
    template = generate_plainte_cpc(
        parties_defenderesses=[p['name'] if isinstance(p, dict) else p for p in parties],
        infractions=infractions
    )
    
    st.session_state.generated_plainte = template
    st.session_state.search_results = {
        'type': 'plainte_template',
        'content': template
    }

def format_parties_list(parties: List[Any]) -> str:
    """Formate la liste des parties pour le template"""
    
    if not parties:
        return "- [NOM DE LA PARTIE]\n  [FORME JURIDIQUE]\n  [SIÈGE SOCIAL]\n  [SIREN]"
    
    formatted = []
    for party in parties:
        if isinstance(party, dict):
            formatted.append(f"- {party.get('name', '[NOM]')}")
            if party.get('legal_form'):
                formatted.append(f"  {party['legal_form']}")
            if party.get('address'):
                formatted.append(f"  {party['address']}")
            if party.get('siren'):
                formatted.append(f"  SIREN : {party['siren']}")
        else:
            formatted.append(f"- {party}")
            formatted.append("  [FORME JURIDIQUE]")
            formatted.append("  [SIÈGE SOCIAL]")
            formatted.append("  [SIREN]")
    
    return '\n'.join(formatted)

# ========================= COMPARAISON MULTI-IA =========================

async def compare_ai_generations(prompt: str, models: List[str] = None):
    """Compare les générations de plusieurs IA"""
    
    if not HAS_API_UTILS:
        st.warning("Comparaison multi-IA non disponible")
        return
    
    st.markdown("### 🤖 Comparaison Multi-IA")
    
    if not models:
        models = get_available_models()[:3]  # Top 3 modèles
    
    results = {}
    
    # Générer avec chaque modèle
    cols = st.columns(len(models))
    
    for idx, model in enumerate(models):
        with cols[idx]:
            with st.spinner(f"Génération {model}..."):
                try:
                    response = await call_llm_api(
                        prompt=prompt,
                        model=model,
                        temperature=0.3,
                        max_tokens=2000
                    )
                    results[model] = response
                    st.success(f"✅ {model}")
                except Exception as e:
                    st.error(f"❌ {model}: {str(e)}")
    
    # Afficher les résultats
    if results:
        st.markdown("#### Résultats")
        
        selected_model = st.radio(
            "Choisir le meilleur résultat",
            list(results.keys())
        )
        
        st.text_area(
            f"Résultat {selected_model}",
            results[selected_model],
            height=400
        )
        
        if st.button("✅ Utiliser ce résultat"):
            st.session_state.generated_plainte = results[selected_model]
            st.success("Résultat sélectionné !")

# ========================= RECHERCHE JURIDIQUE AVANCÉE =========================

async def perform_legal_search(query: str, options: Dict[str, Any] = None):
    """Effectue une recherche juridique avancée"""
    
    if not MANAGERS['legal_search']:
        st.warning("Module de recherche juridique non disponible")
        return None
    
    with st.spinner("🔍 Recherche juridique en cours..."):
        legal_search = LegalSearchManager()
        
        # Options de recherche
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_type = st.selectbox(
                "Type de recherche",
                ["Jurisprudence", "Doctrine", "Textes légaux", "Tout"],
                index=3
            )
        
        with col2:
            jurisdiction = st.selectbox(
                "Juridiction",
                ["Toutes", "Cour de cassation", "Cours d'appel", "Tribunaux"],
                index=0
            )
        
        with col3:
            date_filter = st.selectbox(
                "Période",
                ["Toutes", "1 an", "5 ans", "10 ans"],
                index=1
            )
        
        # Recherche
        try:
            results = await legal_search.search(
                query=query,
                search_type=search_type,
                jurisdiction=jurisdiction,
                date_filter=date_filter
            )
            
            # Afficher les résultats
            if results:
                st.success(f"✅ {len(results)} résultats trouvés")
                
                for idx, result in enumerate(results[:10], 1):
                    with st.expander(f"{idx}. {result.get('title', 'Sans titre')}"):
                        st.write(f"**Source:** {result.get('source', 'Non spécifiée')}")
                        st.write(f"**Date:** {result.get('date', 'Non datée')}")
                        st.write(f"**Juridiction:** {result.get('jurisdiction', 'Non spécifiée')}")
                        st.markdown("---")
                        st.write(result.get('content', 'Pas de contenu'))
                        
                        if result.get('reference'):
                            st.caption(f"Référence: {result['reference']}")
            else:
                st.info("Aucun résultat trouvé")
                
        except Exception as e:
            st.error(f"Erreur lors de la recherche : {str(e)}")

# ========================= GESTION AVANCÉE DES DOCUMENTS =========================

async def manage_documents_advanced(action: str, documents: List[Any] = None):
    """Gestion avancée des documents avec DocumentManager"""
    
    if not MANAGERS['document_manager']:
        st.warning("Module de gestion documentaire non disponible")
        return None
    
    doc_manager = DocumentManager()
    
    if action == "import":
        st.markdown("### 📥 Import avancé de documents")
        
        uploaded_files = st.file_uploader(
            "Choisir des fichiers",
            type=['pdf', 'docx', 'txt', 'rtf'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            with st.spinner(f"Import de {len(uploaded_files)} fichiers..."):
                imported = []
                
                for file in uploaded_files:
                    try:
                        # Traitement avec OCR si nécessaire
                        result = await doc_manager.import_document(
                            file,
                            ocr_enabled=st.checkbox(f"OCR pour {file.name}", value=True),
                            extract_metadata=True
                        )
                        imported.append(result)
                        st.success(f"✅ {file.name}")
                    except Exception as e:
                        st.error(f"❌ {file.name}: {str(e)}")
                
                return imported
    
    elif action == "analyze":
        st.markdown("### 📊 Analyse avancée de documents")
        
        if documents:
            analysis_type = st.multiselect(
                "Types d'analyse",
                ["Structure", "Entités", "Sentiment", "Thèmes", "Relations"],
                default=["Structure", "Entités"]
            )
            
            results = {}
            for doc in documents:
                with st.spinner(f"Analyse de {doc.get('name', 'document')}..."):
                    try:
                        analysis = await doc_manager.analyze_document(
                            doc,
                            analysis_types=analysis_type
                        )
                        results[doc['id']] = analysis
                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
            
            # Afficher les résultats d'analyse
            for doc_id, analysis in results.items():
                with st.expander(f"Analyse de {doc_id}"):
                    for analysis_type, data in analysis.items():
                        st.write(f"**{analysis_type}:**")
                        st.json(data)

# ========================= COMPARAISON MULTI-LLM AMÉLIORÉE =========================

async def enhanced_multi_llm_comparison(prompt: str, options: Dict[str, Any] = None):
    """Comparaison multi-LLM avec fonctionnalités avancées"""
    
    if not MANAGERS['multi_llm']:
        # Fallback vers la version simple
        return await compare_ai_generations(prompt)
    
    multi_llm = MultiLLMManager()
    
    st.markdown("### 🤖 Comparaison Multi-LLM Avancée")
    
    # Options de comparaison
    col1, col2, col3 = st.columns(3)
    
    with col1:
        models = st.multiselect(
            "Modèles à comparer",
            multi_llm.get_available_models(),
            default=multi_llm.get_available_models()[:3]
        )
    
    with col2:
        comparison_mode = st.selectbox(
            "Mode de comparaison",
            ["Parallèle", "Séquentiel", "Consensus"],
            help="Parallèle: tous en même temps | Séquentiel: un par un | Consensus: trouve le meilleur"
        )
    
    with col3:
        metrics = st.multiselect(
            "Métriques d'évaluation",
            ["Qualité", "Pertinence", "Créativité", "Cohérence"],
            default=["Qualité", "Pertinence"]
        )
    
    if st.button("🚀 Lancer la comparaison", type="primary"):
        results = {}
        
        if comparison_mode == "Parallèle":
            # Génération parallèle
            tasks = []
            for model in models:
                task = multi_llm.generate_async(prompt, model=model)
                tasks.append((model, task))
            
            # Attendre toutes les réponses
            progress = st.progress(0)
            for idx, (model, task) in enumerate(tasks):
                with st.spinner(f"Génération {model}..."):
                    try:
                        response = await task
                        results[model] = response
                        progress.progress((idx + 1) / len(tasks))
                    except Exception as e:
                        st.error(f"❌ {model}: {str(e)}")
        
        elif comparison_mode == "Séquentiel":
            # Génération séquentielle avec amélioration
            previous_response = None
            for model in models:
                with st.spinner(f"Génération {model}..."):
                    try:
                        if previous_response:
                            # Enrichir le prompt avec la réponse précédente
                            enriched_prompt = f"{prompt}\n\nAméliore cette réponse:\n{previous_response[:500]}..."
                            response = await multi_llm.generate(enriched_prompt, model=model)
                        else:
                            response = await multi_llm.generate(prompt, model=model)
                        
                        results[model] = response
                        previous_response = response
                    except Exception as e:
                        st.error(f"❌ {model}: {str(e)}")
        
        else:  # Consensus
            # Générer avec tous les modèles puis trouver le consensus
            with st.spinner("Recherche du consensus..."):
                consensus = await multi_llm.get_consensus(prompt, models=models)
                results['consensus'] = consensus
        
        # Évaluation et affichage
        if results:
            st.markdown("#### 📊 Résultats")
            
            # Évaluer selon les métriques
            if metrics and comparison_mode != "Consensus":
                evaluations = {}
                for model, response in results.items():
                    evaluations[model] = await multi_llm.evaluate_response(
                        response, 
                        metrics=metrics
                    )
                
                # Afficher les scores
                st.markdown("**Scores d'évaluation:**")
                df_scores = []
                for model, scores in evaluations.items():
                    row = {'Modèle': model}
                    row.update(scores)
                    df_scores.append(row)
                
                st.dataframe(df_scores)
                
                # Identifier le meilleur
                best_model = max(evaluations.items(), 
                               key=lambda x: sum(x[1].values()))[0]
                st.success(f"🏆 Meilleur modèle : {best_model}")
            
            # Afficher les réponses
            if comparison_mode == "Consensus":
                st.text_area("Consensus", results['consensus'], height=400)
            else:
                selected = st.selectbox(
                    "Voir la réponse de",
                    list(results.keys())
                )
                
                st.text_area(
                    f"Réponse {selected}",
                    results[selected],
                    height=400
                )
                
                # Actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📋 Copier"):
                        st.session_state.clipboard = results[selected]
                        st.success("Copié !")
                
                with col2:
                    if st.button("💾 Utiliser"):
                        st.session_state.generated_content = results[selected]
                        st.success("Contenu sélectionné !")
                
                with col3:
                    if st.button("🔄 Regénérer"):
                        st.rerun()

# ========================= GÉNÉRATEURS DYNAMIQUES =========================

async def use_dynamic_generators(content_type: str, context: Dict[str, Any]):
    """Utilise les générateurs dynamiques pour enrichir le contenu"""
    
    if not MANAGERS['dynamic_generators']:
        st.warning("Générateurs dynamiques non disponibles")
        return None
    
    st.markdown("### ✨ Génération dynamique")
    
    # Options selon le type de contenu
    if content_type == "plainte":
        # Génération de templates dynamiques
        if st.button("Générer des templates de plainte"):
            with st.spinner("Génération des templates..."):
                try:
                    templates = await generate_dynamic_templates('plainte', context)
                    
                    st.success("✅ Templates générés")
                    for name, template in templates.items():
                        with st.expander(name):
                            st.text_area("Contenu", value=template, height=300)
                            st.download_button(
                                "📥 Télécharger",
                                template,
                                file_name=f"{name.replace(' ', '_')}.txt"
                            )
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")
        
        # Génération de prompts de recherche
        if st.button("Générer des prompts de recherche"):
            with st.spinner("Génération des prompts..."):
                try:
                    prompts = await generate_dynamic_search_prompts(
                        context.get('query', 'plainte'),
                        context.get('context', '')
                    )
                    
                    st.success("✅ Prompts générés")
                    for category, subcategories in prompts.items():
                        with st.expander(category):
                            for subcat, prompts_list in subcategories.items():
                                st.subheader(subcat)
                                for prompt in prompts_list:
                                    st.write(f"• {prompt}")
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")

# ========================= GESTION DES PIÈCES =========================

def show_piece_selection_advanced(analysis: Any):
    """Interface avancée de sélection de pièces"""
    
    st.markdown("### 📁 Sélection avancée des pièces")
    
    # Collecter les documents disponibles
    documents = collect_available_documents(analysis)
    
    if not documents:
        st.warning("Aucun document disponible. Importez d'abord des documents.")
        return
    
    # Grouper par catégorie
    categories = group_documents_by_category(documents)
    
    # Options de filtrage
    col1, col2 = st.columns(2)
    with col1:
        selected_categories = st.multiselect(
            "Catégories",
            list(categories.keys()),
            default=list(categories.keys())
        )
    
    with col2:
        sort_by = st.selectbox(
            "Trier par",
            ["Pertinence", "Date", "Titre", "Catégorie"]
        )
    
    # Sélection des pièces
    selected_pieces = []
    
    for category in selected_categories:
        if category in categories:
            st.markdown(f"#### {category}")
            
            for doc in categories[category]:
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    selected = st.checkbox(
                        "",
                        key=f"select_{doc['id']}",
                        value=doc['id'] in st.session_state.get('selected_pieces_ids', [])
                    )
                
                with col2:
                    st.write(f"**{doc['title']}**")
                    if doc.get('metadata', {}).get('date'):
                        st.caption(f"Date: {doc['metadata']['date']}")
                
                with col3:
                    relevance = calculate_piece_relevance(doc, analysis)
                    st.progress(relevance)
                    st.caption(f"{relevance*100:.0f}% pertinent")
                
                if selected:
                    selected_pieces.append(doc)
    
    # Actions sur la sélection
    if selected_pieces:
        st.markdown("---")
        st.info(f"📋 {len(selected_pieces)} pièces sélectionnées")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Créer bordereau"):
                show_bordereau_interface_advanced(selected_pieces, analysis)
        
        with col2:
            if st.button("📄 Synthétiser"):
                asyncio.run(synthesize_selected_pieces(selected_pieces))
        
        with col3:
            if st.button("📥 Exporter liste"):
                export_piece_list(selected_pieces)
        
        with col4:
            if st.button("🗑️ Réinitialiser"):
                st.session_state.selected_pieces_ids = []
                st.rerun()
        
        # Stocker la sélection
        st.session_state.selected_pieces = selected_pieces
        st.session_state.selected_pieces_ids = [p['id'] for p in selected_pieces]

def show_bordereau_interface_advanced(documents: List[Dict], analysis: Any):
    """Interface avancée de création de bordereau"""
    
    st.markdown("### 📋 Création du bordereau")
    
    # Préparer les pièces pour le bordereau
    pieces = []
    for idx, doc in enumerate(documents, 1):
        piece = PieceSelectionnee(
            numero=idx,
            titre=doc.get('title', 'Sans titre'),
            description=doc.get('metadata', {}).get('description', ''),
            categorie=determine_document_category(doc),
            date=doc.get('metadata', {}).get('date'),
            pertinence=calculate_piece_relevance(doc, analysis)
        )
        pieces.append(piece)
    
    # Créer le bordereau
    bordereau = create_bordereau(pieces, analysis)
    
    # Afficher le bordereau
    st.text_area(
        "Aperçu du bordereau",
        value=bordereau.export_to_text()[:1000] + "...",
        height=300
    )
    
    # Options d'export
    col1, col2 = st.columns(2)
    
    with col1:
        format_export = st.selectbox(
            "Format d'export",
            ["Texte", "Markdown", "PDF", "Word"]
        )
    
    with col2:
        if st.button("📥 Télécharger le bordereau"):
            if format_export == "Texte":
                content = bordereau.export_to_text()
            elif format_export == "Markdown":
                content = bordereau.export_to_markdown_with_links()
            else:
                content = bordereau.export_to_text()  # Fallback
            
            st.download_button(
                "💾 Télécharger",
                content.encode('utf-8'),
                f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{'txt' if format_export == 'Texte' else 'md'}",
                "text/plain" if format_export == "Texte" else "text/markdown"
            )
    
    # Statistiques
    st.markdown("#### 📊 Statistiques")
    summary = bordereau.generate_summary()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total pièces", summary['total_pieces'])
    
    with col2:
        st.metric("Catégories", len(summary['pieces_by_category']))
    
    with col3:
        st.metric("Sources", summary['sources_count'])

def export_piece_list(pieces: List[Any]):
    """Exporte la liste des pièces"""
    content = "LISTE DES PIÈCES SÉLECTIONNÉES\n"
    content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    content += f"Nombre de pièces : {len(pieces)}\n\n"
    
    # Grouper par catégorie
    from collections import defaultdict
    by_category = defaultdict(list)
    for piece in pieces:
        category = piece.get('category', 'Non catégorisé')
        by_category[category].append(piece)
    
    for category, cat_pieces in by_category.items():
        content += f"\n{category.upper()} ({len(cat_pieces)} pièces)\n"
        content += "-" * 50 + "\n"
        
        for i, piece in enumerate(cat_pieces, 1):
            content += f"{i}. {piece.get('title', 'Sans titre')}\n"
            if piece.get('metadata', {}).get('date'):
                content += f"   Date: {piece['metadata']['date']}\n"
            content += "\n"
    
    # Proposer le téléchargement
    st.download_button(
        "💾 Télécharger la liste",
        content.encode('utf-8'),
        f"liste_pieces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain"
    )

async def synthesize_selected_pieces(pieces: List[Any]) -> Dict:
    """Synthétise les pièces sélectionnées"""
    
    if not MANAGERS['multi_llm']:
        return {'error': 'Module Multi-LLM non disponible'}
    
    try:
        from managers.multi_llm_manager import MultiLLMManager
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            return {'error': 'Aucune IA disponible'}
        
        # Construire le contexte
        context = "PIÈCES À SYNTHÉTISER:\n\n"
        
        for i, piece in enumerate(pieces[:20], 1):  # Limiter à 20 pièces
            context += f"Pièce {i}: {piece.get('title', 'Sans titre')}\n"
            if piece.get('category'):
                context += f"Catégorie: {piece['category']}\n"
            if piece.get('content'):
                context += f"Extrait: {piece['content'][:200]}...\n"
            context += "\n"
        
        # Prompt de synthèse
        synthesis_prompt = f"""{context}
Crée une synthèse structurée de ces pièces.
La synthèse doit inclure:
1. Vue d'ensemble des pièces
2. Points clés par catégorie
3. Chronologie si applicable
4. Points d'attention juridiques
5. Recommandations"""
        
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            synthesis_prompt,
            "Tu es un expert en analyse de documents juridiques."
        )
        
        if response['success']:
            synthesis_result = {
                'content': response['response'],
                'piece_count': len(pieces),
                'categories': list(set(p.get('category', 'Autre') for p in pieces)),
                'timestamp': datetime.now()
            }
            st.session_state.synthesis_result = synthesis_result
            return synthesis_result
        else:
            return {'error': 'Échec de la synthèse'}
            
    except Exception as e:
        return {'error': f'Erreur synthèse: {str(e)}'}

# ========================= STATISTIQUES ET UTILS =========================

def show_document_statistics(content: str):
    """Affiche les statistiques détaillées d'un document"""
    
    # Calculs de base
    words = content.split()
    sentences = content.split('.')
    paragraphs = content.split('\n\n')
    
    # Analyse avancée
    law_refs = len(re.findall(r'article\s+[LR]?\s*\d+', content, re.IGNORECASE))
    case_refs = len(re.findall(r'(Cass\.|C\.\s*cass\.|Crim\.|Civ\.)', content, re.IGNORECASE))
    
    # Affichage en colonnes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mots", f"{len(words):,}")
        st.metric("Phrases", f"{len(sentences):,}")
    
    with col2:
        st.metric("Paragraphes", len(paragraphs))
        st.metric("Mots/phrase", f"{len(words) / max(len(sentences), 1):.1f}")
    
    with col3:
        st.metric("Articles cités", law_refs)
        st.metric("Jurisprudences", case_refs)
    
    with col4:
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        st.metric("Long. moy.", f"{avg_word_length:.1f} car")
        st.metric("Pages est.", f"~{len(words) // 250}")
    
    # Analyse linguistique si StyleAnalyzer disponible
    if MANAGERS['style_analyzer']:
        with st.expander("📊 Analyse linguistique avancée"):
            try:
                analyzer = StyleAnalyzer()
                linguistic_analysis = analyzer.analyze_text_complexity(content)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Complexité lexicale:**")
                    st.progress(linguistic_analysis.get('lexical_diversity', 0.5))
                    
                with col2:
                    st.write("**Lisibilité:**")
                    readability_score = linguistic_analysis.get('readability_score', 50)
                    st.progress(readability_score / 100)
                    
            except Exception as e:
                st.error(f"Erreur analyse linguistique: {str(e)}")

def save_current_work() -> Dict:
    """Sauvegarde complète du travail actuel"""
    work_data = {
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'session_data': {},
        'results': {},
        'documents': {},
        'analysis': {}
    }
    
    # Sauvegarder l'état de session pertinent
    session_keys = [
        'universal_query', 'last_universal_query', 
        'redaction_result', 'ai_analysis_results',
        'search_results', 'selected_pieces',
        'synthesis_result', 'timeline_result',
        'generated_plainte'
    ]
    
    for key in session_keys:
        if key in st.session_state:
            value = st.session_state[key]
            # Sérialiser les objets complexes
            if hasattr(value, '__dict__'):
                work_data['session_data'][key] = value.__dict__
            else:
                work_data['session_data'][key] = value
    
    # Sauvegarder les documents
    if 'azure_documents' in st.session_state:
        for doc_id, doc in st.session_state.azure_documents.items():
            if hasattr(doc, '__dict__'):
                work_data['documents'][doc_id] = doc.__dict__
            else:
                work_data['documents'][doc_id] = doc
    
    # Créer le JSON
    import json
    
    def default_serializer(obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj)
    
    json_str = json.dumps(work_data, indent=2, ensure_ascii=False, default=default_serializer)
    
    # Proposer le téléchargement
    st.download_button(
        "💾 Sauvegarder le travail",
        json_str,
        f"sauvegarde_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json",
        key="save_work_btn"
    )
    
    return work_data

async def show_work_statistics():
    """Affiche des statistiques détaillées du travail"""
    st.markdown("### 📊 Statistiques du travail")
    
    # Statistiques de base
    stats = {
        'Documents Azure': len(st.session_state.get('azure_documents', {})),
        'Documents importés': len(st.session_state.get('imported_documents', {})),
        'Pièces sélectionnées': len(st.session_state.get('selected_pieces', [])),
        'Analyses effectuées': 1 if st.session_state.get('ai_analysis_results') else 0,
        'Rédactions': 1 if st.session_state.get('redaction_result') else 0
    }
    
    # Affichage en métriques
    cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(label, value)
    
    # Statistiques détaillées par type
    with st.expander("📈 Statistiques détaillées"):
        # Documents par catégorie
        if st.session_state.get('azure_documents'):
            all_docs = []
            for doc_id, doc in st.session_state.azure_documents.items():
                all_docs.append({
                    'id': doc_id,
                    'title': doc.title if hasattr(doc, 'title') else doc.get('title', ''),
                    'content': doc.content if hasattr(doc, 'content') else doc.get('content', ''),
                    'source': doc.source if hasattr(doc, 'source') else doc.get('source', '')
                })
            
            categories = group_documents_by_category(all_docs)
            
            st.write("**Documents par catégorie:**")
            for cat, docs in categories.items():
                st.write(f"• {cat}: {len(docs)} documents")
        
        # Historique des actions
        if 'action_history' in st.session_state:
            st.write("**Historique des actions:**")
            for action in st.session_state.action_history[-10:]:
                st.write(f"• {action['timestamp']}: {action['type']}")

# ========================= TRAITEMENT DES PLAINTES COMPLET =========================

async def process_plainte_request(query: str, analysis: QueryAnalysis):
    """Traite une demande de plainte avec toutes les options"""
    
    st.markdown("### 📋 Configuration de la plainte")
    
    # Déterminer le type de plainte
    query_lower = query.lower()
    is_partie_civile = any(term in query_lower for term in [
        'partie civile', 'constitution de partie civile', 'cpc', 
        'doyen', 'juge d\'instruction', 'instruction'
    ])
    
    # Extraire les parties et infractions
    parties_demanderesses = []
    parties_defenderesses = []
    infractions = []
    
    if hasattr(analysis, 'parties'):
        parties_demanderesses = analysis.parties.get('demandeurs', [])
        parties_defenderesses = analysis.parties.get('defendeurs', [])
    
    if hasattr(analysis, 'infractions'):
        infractions = analysis.infractions
    
    # Interface de configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏢 Demandeurs (victimes)**")
        demandeurs_text = st.text_area(
            "Un par ligne",
            value='\n'.join(parties_demanderesses),
            height=100,
            key="demandeurs_input"
        )
        parties_demanderesses = [p.strip() for p in demandeurs_text.split('\n') if p.strip()]
        
        st.markdown("**🎯 Infractions**")
        infractions_text = st.text_area(
            "Une par ligne",
            value='\n'.join(infractions),
            height=100,
            key="infractions_input"
        )
        infractions = [i.strip() for i in infractions_text.split('\n') if i.strip()]
    
    with col2:
        st.markdown("**⚖️ Défendeurs (mis en cause)**")
        defendeurs_text = st.text_area(
            "Un par ligne",
            value='\n'.join(parties_defenderesses),
            height=100,
            key="defendeurs_input"
        )
        parties_defenderesses = [p.strip() for p in defendeurs_text.split('\n') if p.strip()]
        
        st.markdown("**⚙️ Options**")
        type_plainte = st.radio(
            "Type de plainte",
            ["Plainte simple", "Plainte avec CPC"],
            index=1 if is_partie_civile else 0,
            key="type_plainte_radio"
        )
        is_partie_civile = (type_plainte == "Plainte avec CPC")
        
        include_chronologie = st.checkbox("Inclure chronologie détaillée", value=True)
        include_prejudices = st.checkbox("Détailler les préjudices", value=True)
        include_jurisprudence = st.checkbox("Citer jurisprudences", value=is_partie_civile)
    
    # Enrichissement des parties si CompanyInfoManager disponible
    if st.checkbox("🏢 Enrichir les informations des sociétés", value=True):
        if MANAGERS['company_info'] and (parties_demanderesses or parties_defenderesses):
            enriched_parties = await enrich_parties_info(
                parties_demanderesses + parties_defenderesses
            )
            
            if enriched_parties:
                with st.expander("📊 Informations enrichies", expanded=False):
                    for party in enriched_parties:
                        st.json(party)
    
    # Bouton de génération
    if st.button("🚀 Générer la plainte", type="primary", key="generate_plainte_btn"):
        # Préparer l'analyse enrichie
        analysis_dict = {
            'parties': {
                'demandeurs': parties_demanderesses,
                'defendeurs': parties_defenderesses
            },
            'infractions': infractions,
            'reference': analysis.reference if hasattr(analysis, 'reference') else None,
            'options': {
                'is_partie_civile': is_partie_civile,
                'include_chronologie': include_chronologie,
                'include_prejudices': include_prejudices,
                'include_jurisprudence': include_jurisprudence
            }
        }
        
        # Générer
        await generate_advanced_plainte(query)

# ========================= INTERFACE UTILISATEUR =========================

class SearchInterface:
    """Interface utilisateur pour le module de recherche"""
    
    def __init__(self):
        """Initialisation avec le service de recherche universelle"""
        if SEARCH_SERVICE_AVAILABLE:
            self.search_service = get_universal_search_service()
        else:
            self.search_service = None
        self.current_phase = PhaseProcedure.ENQUETE_PRELIMINAIRE
    
    async def process_universal_query(self, query: str):
        """Traite une requête en utilisant le service de recherche"""
        
        # Sauvegarder la requête
        st.session_state.last_universal_query = query
        
        # Analyser la requête avec le service
        if self.search_service:
            query_analysis = self.search_service.analyze_query_advanced(query)
        else:
            # Fallback simple si le service n'est pas disponible
            query_analysis = self._simple_query_analysis(query)
        
        # Router selon le type de commande détecté
        if query_analysis.command_type == 'redaction':
            return await self._process_redaction_request(query, query_analysis)
        elif query_analysis.command_type == 'plainte':
            return await process_plainte_request(query, query_analysis)
        elif query_analysis.command_type == 'plaidoirie':
            return await self._process_plaidoirie_request(query, query_analysis)
        elif query_analysis.command_type == 'preparation_client':
            return await self._process_preparation_client_request(query, query_analysis)
        elif query_analysis.command_type == 'import':
            return await self._process_import_request(query, query_analysis)
        elif query_analysis.command_type == 'export':
            return await self._process_export_request(query, query_analysis)
        elif query_analysis.command_type == 'email':
            return await self._process_email_request(query, query_analysis)
        elif query_analysis.command_type == 'analysis':
            return await self._process_analysis_request(query, query_analysis)
        elif query_analysis.command_type == 'piece_selection':
            return await self._process_piece_selection_request(query, query_analysis)
        elif query_analysis.command_type == 'bordereau':
            return await self._process_bordereau_request(query, query_analysis)
        elif query_analysis.command_type == 'synthesis':
            return await self._process_synthesis_request(query, query_analysis)
        elif query_analysis.command_type == 'template':
            return await self._process_template_request(query, query_analysis)
        elif query_analysis.command_type == 'jurisprudence':
            return await self._process_jurisprudence_request(query, query_analysis)
        elif query_analysis.command_type == 'timeline':
            return await self._process_timeline_request(query, query_analysis)
        elif query_analysis.command_type == 'mapping':
            return await self._process_mapping_request(query, query_analysis)
        elif query_analysis.command_type == 'comparison':
            return await self._process_comparison_request(query, query_analysis)
        else:
            # Recherche par défaut
            return await self._process_search_request(query, query_analysis)
    
    def _simple_query_analysis(self, query: str) -> QueryAnalysis:
        """Analyse simple de la requête si le service n'est pas disponible"""
        analysis = QueryAnalysis(
            original_query=query,
            query_lower=query.lower(),
            timestamp=datetime.now()
        )
        
        # Détection basique du type de commande
        query_lower = analysis.query_lower
        if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer']):
            analysis.command_type = 'redaction'
        else:
            analysis.command_type = 'search'
        
        # Extraction basique de la référence
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            analysis.reference = ref_match.group(1)
        
        return analysis
    
    # ===================== PROCESSEURS DE REQUÊTES =====================
    
    async def _process_redaction_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de rédaction"""
        st.info("📝 Détection d'une demande de rédaction...")
        
        if 'process_redaction_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_redaction_request'](query, query_analysis)
        else:
            st.warning("Module de rédaction non disponible")
    
    async def _process_analysis_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'analyse"""
        if 'analyse_ia_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['analyse_ia_page']()
        else:
            st.warning("Module d'analyse non disponible")
    
    async def _process_plaidoirie_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de plaidoirie"""
        if 'process_plaidoirie_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_plaidoirie_request'](query, query_analysis)
        else:
            st.warning("Module plaidoirie non disponible")
    
    async def _process_preparation_client_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de préparation client"""
        if 'process_preparation_client_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_preparation_client_request'](query, query_analysis)
        else:
            st.warning("Module préparation client non disponible")
    
    async def _process_import_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'import"""
        if 'process_import_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_import_request'](query, query_analysis)
        else:
            st.warning("Module import non disponible")
    
    async def _process_export_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'export"""
        if 'process_export_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_export_request'](query, query_analysis)
        else:
            st.warning("Module export non disponible")
    
    async def _process_email_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande d'email"""
        if 'process_email_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_email_request'](query, query_analysis)
        else:
            st.warning("Module email non disponible")
    
    async def _process_piece_selection_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de sélection de pièces"""
        if 'selection_piece_page' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['selection_piece_page']()
        else:
            show_piece_selection_advanced(query_analysis)
    
    async def _process_bordereau_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de bordereau"""
        if 'process_bordereau_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_bordereau_request'](query, query_analysis)
        else:
            docs = collect_available_documents(query_analysis)
            if docs:
                show_bordereau_interface_advanced(docs, query_analysis)
    
    async def _process_synthesis_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de synthèse"""
        if 'process_synthesis_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_synthesis_request'](query, query_analysis)
        elif st.session_state.get('selected_pieces'):
            return await synthesize_selected_pieces(st.session_state.selected_pieces)
        else:
            st.warning("Module synthèse non disponible ou aucune pièce sélectionnée")
    
    async def _process_template_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de template"""
        if 'process_template_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_template_request'](query, query_analysis)
        else:
            st.warning("Module templates non disponible")
    
    async def _process_jurisprudence_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de jurisprudence"""
        if 'process_jurisprudence_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_jurisprudence_request'](query, query_analysis)
        elif 'show_jurisprudence_interface' in MODULE_FUNCTIONS:
            MODULE_FUNCTIONS['show_jurisprudence_interface']()
        else:
            st.warning("Module jurisprudence non disponible")
    
    async def _process_timeline_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de timeline"""
        if 'process_timeline_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_timeline_request'](query, query_analysis)
        else:
            st.warning("Module timeline non disponible")
    
    async def _process_mapping_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de cartographie"""
        if 'process_mapping_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_mapping_request'](query, query_analysis)
        else:
            st.warning("Module cartographie non disponible")
    
    async def _process_comparison_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de comparaison"""
        if 'process_comparison_request' in MODULE_FUNCTIONS:
            return MODULE_FUNCTIONS['process_comparison_request'](query, query_analysis)
        else:
            st.warning("Module comparaison non disponible")
    
    async def _process_search_request(self, query: str, query_analysis: QueryAnalysis):
        """Traite une demande de recherche par défaut"""
        st.info("🔍 Recherche en cours...")
        
        if self.search_service:
            # Utiliser le service de recherche
            search_result = await self.search_service.search(query)
            
            # Stocker les résultats
            st.session_state.search_results = search_result.documents
            
            if not search_result.documents:
                st.warning("⚠️ Aucun résultat trouvé")
            else:
                st.success(f"✅ {len(search_result.documents)} résultats trouvés")
                
                # Afficher les facettes si disponibles
                if search_result.facets:
                    with st.expander("🔍 Filtres disponibles"):
                        for facet_name, facet_values in search_result.facets.items():
                            st.write(f"**{facet_name}**")
                            for value, count in facet_values.items():
                                st.write(f"- {value}: {count}")
                
                # Afficher les suggestions si disponibles
                if search_result.suggestions:
                    st.info("💡 Suggestions de recherche:")
                    cols = st.columns(min(len(search_result.suggestions), 3))
                    for i, suggestion in enumerate(search_result.suggestions):
                        with cols[i]:
                            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                                st.session_state.pending_query = suggestion
                                st.rerun()
            
            return search_result
        else:
            # Fallback simple
            st.warning("Service de recherche non disponible")
            return []

# ========================= FONCTIONS UTILITAIRES =========================

def get_reference_suggestions(query: str) -> List[str]:
    """Obtient des suggestions de références basées sur la requête"""
    
    suggestions = []
    
    if SEARCH_SERVICE_AVAILABLE:
        service = get_universal_search_service()
        
        # Extraire la partie après le dernier @
        if '@' in query:
            parts = query.split('@')
            partial_ref = parts[-1].strip().split()[0] if parts[-1].strip() else ''
            
            if partial_ref:
                suggestions = service.generate_reference_suggestions(partial_ref)
    
    return suggestions[:5]

def collect_all_references() -> List[str]:
    """Collecte toutes les références de dossiers disponibles"""
    
    if SEARCH_SERVICE_AVAILABLE:
        service = get_universal_search_service()
        return service.collect_all_references()
    
    # Fallback
    references = set()
    
    # Parcourir tous les documents
    all_docs = {}
    all_docs.update(st.session_state.get('azure_documents', {}))
    all_docs.update(st.session_state.get('imported_documents', {}))
    
    for doc in all_docs.values():
        title = doc.get('title', '')
        
        # Patterns simples pour extraire les références
        patterns = [
            r'affaire[_\s]+(\w+)',
            r'dossier[_\s]+(\w+)',
            r'projet[_\s]+(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, title, re.IGNORECASE)
            references.update(matches)
    
    return sorted(list(references))

def find_matching_documents(reference: str) -> List[Dict]:
    """Trouve les documents correspondant à une référence partielle"""
    
    matches = []
    ref_lower = reference.lower()
    
    # Parcourir tous les documents
    all_docs = {}
    all_docs.update(st.session_state.get('azure_documents', {}))
    all_docs.update(st.session_state.get('imported_documents', {}))
    
    for doc_id, doc in all_docs.items():
        title = doc.get('title', '')
        content = doc.get('content', '')[:200]  # Aperçu du contenu
        
        # Vérifier la correspondance
        if ref_lower in title.lower() or ref_lower in content.lower():
            # Extraire une référence propre du titre
            clean_ref = extract_clean_reference(title)
            
            matches.append({
                'id': doc_id,
                'title': title,
                'type': doc.get('type', 'Document'),
                'date': doc.get('date', doc.get('metadata', {}).get('date', 'Non daté')),
                'preview': content,
                'clean_ref': clean_ref or reference,
                'score': calculate_match_score(title, content, reference)
            })
    
    # Trier par score de pertinence
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def extract_clean_reference(title: str) -> str:
    """Extrait une référence propre du titre"""
    
    # Patterns pour extraire les références
    patterns = [
        r'affaire[_\s]+(\w+)',
        r'dossier[_\s]+(\w+)',
        r'projet[_\s]+(\w+)',
        r'^(\w+_\d{4})',
        r'^(\w+)[\s_]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Si pas de pattern, prendre le premier mot significatif
    words = title.split()
    for word in words:
        if len(word) > 3 and word.isalnum():
            return word
    
    return None

def calculate_match_score(title: str, content: str, reference: str) -> float:
    """Calcule un score de pertinence pour le tri"""
    
    score = 0
    ref_lower = reference.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Correspondance exacte dans le titre
    if ref_lower == title_lower:
        score += 100
    # Commence par la référence
    elif title_lower.startswith(ref_lower):
        score += 50
    # Contient la référence dans le titre
    elif ref_lower in title_lower:
        score += 30
    # Contient dans le contenu
    elif ref_lower in content_lower:
        score += 10
    
    # Bonus pour les références courtes (plus spécifiques)
    if len(reference) >= 5:
        score += 5
    
    return score

def highlight_match(text: str, match: str) -> str:
    """Surligne les correspondances dans le texte"""
    
    # Échapper les caractères HTML
    text = html.escape(text)
    match = html.escape(match)
    
    # Remplacer avec surbrillance (insensible à la casse)
    pattern = re.compile(re.escape(match), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<mark style="background-color: #ffeb3b; padding: 2px;">{m.group()}</mark>',
        text
    )
    
    return highlighted

def show_live_preview(reference: str, full_query: str):
    """Affiche une prévisualisation des dossiers correspondants"""
    
    with st.container():
        # Rechercher les correspondances
        matches = find_matching_documents(reference)
        
        if matches:
            st.markdown(f"### 📁 Aperçu des résultats pour **@{reference}**")
            
            # Limiter à 5 résultats
            for i, match in enumerate(matches[:5]):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    # Titre avec surbrillance
                    highlighted_title = highlight_match(match['title'], reference)
                    st.markdown(f"**{i+1}.** {highlighted_title}", unsafe_allow_html=True)
                
                with col2:
                    # Métadonnées
                    doc_type = match.get('type', 'Document')
                    date = match.get('date', 'Non daté')
                    st.caption(f"{doc_type} • {date}")
                
                with col3:
                    # Action rapide
                    if st.button("Utiliser", key=f"use_{match['id']}", use_container_width=True):
                        # Remplacer la référence partielle par la complète
                        new_query = full_query.replace(f"@{reference}", f"@{match['clean_ref']}")
                        st.session_state.pending_query = new_query
                        st.rerun()
            
            # Afficher le nombre total si plus de 5
            if len(matches) > 5:
                st.info(f"📊 {len(matches) - 5} autres résultats disponibles. Affinez votre recherche ou cliquez sur Rechercher.")
        else:
            st.info(f"🔍 Aucun dossier trouvé pour '@{reference}'. Essayez avec d'autres termes.")

def show_available_references():
    """Affiche toutes les références disponibles de manière organisée"""
    
    references = collect_all_references()
    
    if references:
        st.markdown("### 📚 Références disponibles")
        
        # Grouper par première lettre
        grouped = {}
        for ref in references:
            first_letter = ref[0].upper()
            if first_letter not in grouped:
                grouped[first_letter] = []
            grouped[first_letter].append(ref)
        
        # Afficher en colonnes
        cols = st.columns(4)
        col_idx = 0
        
        for letter in sorted(grouped.keys()):
            with cols[col_idx % 4]:
                st.markdown(f"**{letter}**")
                for ref in grouped[letter]:
                    if st.button(f"@{ref}", key=f"ref_{ref}", use_container_width=True):
                        st.session_state.pending_query = f"@{ref} "
                        st.rerun()
            col_idx += 1
    else:
        st.info("Aucune référence trouvée. Importez des documents pour commencer.")

# ========================= FONCTION PRINCIPALE =========================

def show_page():
    """Fonction principale de la page recherche universelle avec toutes les améliorations"""
    
    # Initialiser l'interface
    if 'search_interface' not in st.session_state:
        st.session_state.search_interface = SearchInterface()
    
    interface = st.session_state.search_interface
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # État des modules
    if st.checkbox("🔧 Voir l'état des modules"):
        show_modules_status()
    
    # Barre de recherche principale avec auto-complétion
    col1, col2 = st.columns([5, 1])
    
    with col1:
        default_value = ""
        if 'pending_query' in st.session_state:
            default_value = st.session_state.pending_query
            del st.session_state.pending_query
        elif 'universal_query' in st.session_state:
            default_value = st.session_state.universal_query
        
        query = st.text_input(
            "Entrez votre commande ou recherche",
            value=default_value,
            placeholder="Ex: rédiger conclusions @affaire_martin, analyser risques, importer documents...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique"
        )
        
        # Auto-complétion des références
        if query and '@' in query:
            suggestions = get_reference_suggestions(query)
            if suggestions:
                st.markdown("**Suggestions :**")
                cols = st.columns(min(len(suggestions), 5))
                for i, suggestion in enumerate(suggestions[:5]):
                    with cols[i]:
                        if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                            # Remplacer la partie après @ par la suggestion
                            parts = query.split('@')
                            if len(parts) > 1:
                                # Garder ce qui est avant @ et ajouter la suggestion
                                new_query = parts[0] + suggestion
                                st.session_state.pending_query = new_query
                                st.rerun()
    
    with col2:
        search_button = st.button("🔍 Rechercher", key="search_button", use_container_width=True)
    
    # Prévisualisation en temps réel
    if query and '@' in query:
        # Extraire la référence
        parts = query.split('@')
        if len(parts) > 1:
            ref_part = parts[-1].split()[0] if parts[-1].strip() else ''
            
            if ref_part and len(ref_part) >= 2:  # Au moins 2 caractères
                show_live_preview(ref_part, query)
    
    # Afficher les références disponibles
    if st.checkbox("📁 Voir toutes les références disponibles"):
        show_available_references()
    
    # Suggestions de commandes
    with st.expander("💡 Exemples de commandes", expanded=False):
        st.markdown("""
        **Recherche :**
        - `contrats société XYZ`
        - `@affaire_martin documents comptables`
        - `@mart` (trouvera martin, martinez, etc.)
        - `@2024` (tous les dossiers de 2024)
        
        **Analyse :**
        - `analyser les risques @dossier_pénal`
        - `identifier les infractions @affaire_corruption`
        
        **Rédaction :**
        - `rédiger conclusions défense @affaire_martin abus biens sociaux`
        - `créer plainte avec constitution partie civile escroquerie`
        - `rédiger plainte contre Vinci, SOGEPROM @projet_26_05_2025`
        
        **Synthèse :**
        - `synthétiser les pièces @dossier_fraude`
        - `résumer les auditions @affaire_martin`
        
        **Gestion :**
        - `sélectionner pièces @dossier catégorie procédure`
        - `créer bordereau @pièces_sélectionnées`
        - `importer documents PDF`
        - `exporter analyse format word`
        """)
    
    # Menu d'actions rapides
    show_quick_actions()
    
    # Traiter la requête
    if query and (search_button or st.session_state.get('process_query', False)):
        with st.spinner("🔄 Traitement en cours..."):
            # Utiliser une nouvelle boucle d'événements
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(interface.process_universal_query(query))
            finally:
                loop.close()
    
    # Afficher les résultats
    show_unified_results()
    
    # Réinitialiser le flag de traitement
    if 'process_query' in st.session_state:
        st.session_state.process_query = False
    
    # Footer avec actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder le travail", key="save_work"):
            save_current_work()
    
    with col2:
        if st.button("📊 Afficher les statistiques", key="show_stats"):
            if interface.search_service:
                # Afficher les statistiques du service de recherche
                stats = asyncio.run(interface.search_service.get_search_statistics())
                with st.expander("📊 Statistiques de recherche", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Recherches totales", stats['total_searches'])
                        st.metric("Résultats moyens", f"{stats['average_results']:.0f}")
                    with col2:
                        st.metric("Taille du cache", stats['cache_size'])
                    
                    if stats['popular_keywords']:
                        st.markdown("**Mots-clés populaires:**")
                        for keyword, count in list(stats['popular_keywords'].items())[:5]:
                            st.write(f"- {keyword}: {count} fois")
            else:
                asyncio.run(show_work_statistics())
    
    with col3:
        if st.button("🔗 Partager", key="share_work"):
            st.info("Fonctionnalité de partage à implémenter")

def show_modules_status():
    """Affiche l'état détaillé des modules"""
    with st.expander("🔧 État des modules et fonctions", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Modules disponibles", sum(1 for v in MODULES_AVAILABLE.values() if v))
            st.metric("Fonctions importées", len(MODULE_FUNCTIONS))
        
        with col2:
            st.metric("Managers avancés", sum(1 for v in MANAGERS.values() if v))
            st.metric("Service de recherche", "✅" if SEARCH_SERVICE_AVAILABLE else "❌")
        
        with col3:
            st.metric("Templates", len(BUILTIN_DOCUMENT_TEMPLATES))
            st.metric("Styles", len(DEFAULT_STYLE_CONFIGS))
        
        # Liste détaillée
        st.markdown("### 📋 Modules actifs")
        for module, available in MODULES_AVAILABLE.items():
            if available:
                st.success(f"✅ {module}")
            else:
                st.error(f"❌ {module}")

def show_quick_actions():
    """Affiche les actions rapides"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Nouvelle rédaction", key="quick_redaction"):
            st.session_state.pending_query = "rédiger "
            st.session_state.process_query = True
            st.rerun()
    
    with col2:
        if st.button("🤖 Analyser dossier", key="quick_analysis"):
            st.session_state.pending_query = "analyser "
            st.session_state.process_query = True
            st.rerun()
    
    with col3:
        if st.button("📥 Importer", key="quick_import"):
            st.session_state.pending_query = "importer documents"
            st.session_state.process_query = True
            st.rerun()
    
    with col4:
        if st.button("🔄 Réinitialiser", key="quick_reset"):
            clear_universal_state()

def show_unified_results():
    """Affiche tous les types de résultats de manière unifiée"""
    
    # Vérifier tous les types de résultats possibles
    results_found = False
    
    # Résultats de rédaction
    if st.session_state.get('redaction_result'):
        show_redaction_results()
        results_found = True
    
    # Plainte générée
    elif st.session_state.get('generated_plainte'):
        show_plainte_results()
        results_found = True
    
    # Résultats d'analyse
    elif st.session_state.get('ai_analysis_results'):
        show_analysis_results()
        results_found = True
    
    # Résultats de recherche
    elif st.session_state.get('search_results'):
        show_search_results()
        results_found = True
    
    # Résultats de synthèse
    elif st.session_state.get('synthesis_result'):
        show_synthesis_results()
        results_found = True
    
    # Autres résultats...
    elif st.session_state.get('timeline_result'):
        show_timeline_results()
        results_found = True
    
    elif st.session_state.get('bordereau_result'):
        show_bordereau_results()
        results_found = True
    
    elif st.session_state.get('jurisprudence_results'):
        show_jurisprudence_results()
        results_found = True
    
    if not results_found:
        st.info("💡 Utilisez la barre de recherche universelle pour commencer")

def show_redaction_results():
    """Affiche les résultats de rédaction"""
    result = st.session_state.redaction_result
    
    st.markdown("### 📝 Document juridique généré")
    
    # Contenu éditable
    edited_content = st.text_area(
        "Contenu du document",
        value=result.get('document', result.get('content', '')),
        height=600,
        key="edit_redaction"
    )
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "📥 Télécharger",
            edited_content.encode('utf-8'),
            f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("📧 Envoyer"):
            st.session_state.pending_email = {'content': edited_content}
    
    with col3:
        if st.button("🔄 Régénérer"):
            st.session_state.process_query = True
            st.rerun()

def show_plainte_results():
    """Affiche les résultats de génération de plainte"""
    content = st.session_state.generated_plainte
    
    st.markdown("### 📋 Plainte générée")
    
    # Options avancées si disponibles
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("✨ Version avancée", key="upgrade_plainte"):
            query = st.session_state.get('last_universal_query', '')
            asyncio.run(generate_advanced_plainte(query))
    
    # Contenu éditable
    edited_content = st.text_area(
        "Contenu de la plainte",
        value=content,
        height=600,
        key="edit_plainte"
    )
    
    # Actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.download_button(
            "📥 Télécharger",
            edited_content.encode('utf-8'),
            f"plainte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        if st.button("📊 Statistiques", key="stats_plainte"):
            show_plainte_statistics(edited_content)
    
    with col3:
        if st.button("✅ Vérifier", key="verify_plainte"):
            verify_jurisprudences_in_plainte(edited_content)
    
    with col4:
        if st.button("🔄 Régénérer", key="regen_plainte"):
            st.session_state.process_query = True
            st.rerun()

def show_analysis_results():
    """Affiche les résultats d'analyse"""
    results = st.session_state.ai_analysis_results
    
    st.markdown("### 🤖 Résultats de l'analyse")
    
    # Contenu
    st.text_area(
        "Analyse",
        value=results.get('content', ''),
        height=400,
        key="analysis_content"
    )
    
    # Métadonnées
    if results.get('document_count'):
        st.info(f"📄 Documents analysés : {results['document_count']}")

def show_search_results():
    """Affiche les résultats de recherche avec highlights"""
    results = st.session_state.search_results
    
    if isinstance(results, list) and results:
        st.markdown(f"### 🔍 Résultats de recherche ({len(results)} documents)")
        
        # Options de tri
        col1, col2 = st.columns([3, 1])
        with col2:
            sort_option = st.selectbox(
                "Trier par",
                ["Pertinence", "Date", "Type"],
                key="sort_results"
            )
        
        # Afficher les résultats
        for i, result in enumerate(results[:10], 1):
            # Si c'est un objet Document
            if hasattr(result, 'highlights'):
                with st.expander(f"{i}. {result.title}"):
                    # Afficher les highlights s'ils existent
                    if result.highlights:
                        st.markdown("**📌 Extraits pertinents:**")
                        for highlight in result.highlights:
                            st.info(f"...{highlight}...")
                    else:
                        st.write(result.content[:500] + '...')
                    
                    # Métadonnées
                    if hasattr(result, 'metadata') and result.metadata:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"📊 Score: {result.metadata.get('score', 0):.0f}")
                        with col2:
                            st.caption(f"📁 Source: {result.source}")
                        with col3:
                            match_type = result.metadata.get('match_type', 'standard')
                            if match_type == 'exact':
                                st.caption("✅ Correspondance exacte")
                            elif match_type == 'partial':
                                st.caption("📍 Correspondance partielle")
            else:
                # Format dictionnaire
                with st.expander(f"{i}. {result.get('title', 'Sans titre')}"):
                    st.write(result.get('content', '')[:500] + '...')
                    st.caption(f"Score: {result.get('score', 0):.0%}")
        
        # Pagination si plus de 10 résultats
        if len(results) > 10:
            st.info(f"📄 Affichage des 10 premiers résultats sur {len(results)}. Utilisez les filtres pour affiner.")

def show_synthesis_results():
    """Affiche les résultats de synthèse"""
    result = st.session_state.synthesis_result
    
    st.markdown("### 📝 Synthèse des documents")
    
    st.text_area(
        "Contenu de la synthèse",
        value=result.get('content', ''),
        height=400,
        key="synthesis_content"
    )
    
    if result.get('piece_count'):
        st.info(f"📄 Pièces analysées : {result['piece_count']}")

def show_timeline_results():
    """Affiche les résultats de timeline"""
    st.markdown("### ⏱️ Chronologie des événements")
    st.info("Timeline générée")

def show_bordereau_results():
    """Affiche les résultats de bordereau"""
    st.markdown("### 📊 Bordereau de communication")
    st.info("Bordereau généré")

def show_jurisprudence_results():
    """Affiche les résultats de jurisprudence"""
    st.markdown("### ⚖️ Jurisprudences trouvées")
    st.info("Résultats de jurisprudence")

def clear_universal_state():
    """Efface l'état de l'interface universelle"""
    keys_to_clear = [
        'universal_query', 'last_universal_query', 'current_analysis',
        'redaction_result', 'ai_analysis_results', 'search_results',
        'synthesis_result', 'selected_pieces', 'import_files',
        'generated_plainte', 'timeline_result', 'bordereau_result',
        'jurisprudence_results'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Effacer aussi le cache du service
    if hasattr(st.session_state, 'search_interface') and st.session_state.search_interface.search_service:
        st.session_state.search_interface.search_service.clear_cache()
    
    st.success("✅ Interface réinitialisée")
    st.rerun()

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    show_page()
# modules/advanced_features.py
"""Fonctionnalités avancées de l'assistant juridique - À préserver"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import re

# Managers avancés
try:
    from managers.jurisprudence_verifier import JurisprudenceVerifier, display_jurisprudence_verification
    from managers.company_info_manager import CompanyInfoManager
    from managers.style_analyzer import StyleAnalyzer
    from managers.dynamic_generators import DynamicGenerators
    ADVANCED_MANAGERS = True
except ImportError:
    ADVANCED_MANAGERS = False

# ========================= GÉNÉRATION AVANCÉE DE PLAINTES =========================

def generate_advanced_plainte(
    query: str,
    parties_demanderesses: List[str],
    parties_defenderesses: List[str],
    infractions: List[str],
    is_partie_civile: bool,
    reference: Optional[str] = None,
    modele: Optional[str] = None,
    llm_manager = None
) -> Dict[str, Any]:
    """
    Génère une plainte avancée avec toutes les fonctionnalités
    
    Fonctionnalités :
    - Plainte CPC exhaustive (8000+ mots)
    - Enrichissement des parties
    - Vérification des jurisprudences
    - Suggestions d'amélioration
    """
    
    # 1. ENRICHIR LES INFORMATIONS DES PARTIES
    if ADVANCED_MANAGERS and CompanyInfoManager:
        enriched_parties = enrich_parties_information(
            parties_demanderesses + parties_defenderesses
        )
    else:
        enriched_parties = {}
    
    # 2. GÉNÉRER LE PROMPT AVANCÉ
    if is_partie_civile:
        prompt = generate_cpc_exhaustive_prompt(
            parties_demanderesses,
            parties_defenderesses,
            infractions,
            reference,
            enriched_parties
        )
    else:
        prompt = generate_simple_plainte_prompt(
            parties_demanderesses,
            parties_defenderesses,
            infractions,
            reference
        )
    
    # 3. AMÉLIORER LE PROMPT AVEC DYNAMIC GENERATORS
    if ADVANCED_MANAGERS and DynamicGenerators:
        try:
            dynamic_gen = DynamicGenerators()
            prompt = dynamic_gen.enhance_prompt(
                prompt,
                doc_type='plainte_avec_cpc' if is_partie_civile else 'plainte_simple',
                context={'parties': enriched_parties}
            )
        except:
            pass
    
    # 4. GÉNÉRER AVEC OPTIONS AVANCÉES
    generation_result = generate_with_advanced_options(
        prompt,
        llm_manager,
        is_partie_civile
    )
    
    # 5. POST-TRAITEMENT ET AMÉLIORATIONS
    if generation_result['success']:
        # Améliorer le style si disponible
        if ADVANCED_MANAGERS and StyleAnalyzer:
            generation_result['document'] = improve_document_style(
                generation_result['document'],
                'formel' if is_partie_civile else 'persuasif'
            )
        
        # Vérifier les jurisprudences citées
        if ADVANCED_MANAGERS:
            generation_result['jurisprudence_verification'] = verify_document_jurisprudences(
                generation_result['document']
            )
        
        # Ajouter les suggestions d'amélioration
        generation_result['improvement_suggestions'] = generate_improvement_suggestions(
            generation_result['document'],
            is_partie_civile,
            enriched_parties
        )
    
    return generation_result

def enrich_parties_information(parties: List[str]) -> Dict[str, Any]:
    """Enrichit les informations des parties avec CompanyInfoManager"""
    
    enriched = {}
    
    if not ADVANCED_MANAGERS or not CompanyInfoManager:
        return enriched
    
    try:
        company_manager = CompanyInfoManager()
        
        for partie in parties:
            info = company_manager.get_company_info(partie)
            if info:
                enriched[partie] = info
                st.info(f"✅ Informations enrichies pour {partie}")
    except Exception as e:
        st.warning(f"⚠️ Impossible d'enrichir les informations : {e}")
    
    return enriched

def generate_cpc_exhaustive_prompt(
    demandeurs: List[str],
    defendeurs: List[str],
    infractions: List[str],
    reference: Optional[str],
    enriched_parties: Dict[str, Any]
) -> str:
    """Génère le prompt pour une plainte CPC exhaustive"""
    
    # Enrichir les informations des parties
    demandeurs_detail = []
    for d in demandeurs:
        if d in enriched_parties:
            info = enriched_parties[d]
            demandeurs_detail.append(
                f"{d}, société {info.get('forme_juridique', '[À PRÉCISER]')}, "
                f"capital {info.get('capital', '[À PRÉCISER]')} €, "
                f"RCS {info.get('ville_rcs', '[VILLE]')} {info.get('numero_rcs', '[NUMÉRO]')}, "
                f"siège {info.get('adresse', '[ADRESSE]')}"
            )
        else:
            demandeurs_detail.append(f"{d} [INFORMATIONS À COMPLÉTER]")
    
    prompt = f"""Tu es Maître Jean-Michel DURAND, avocat pénaliste réputé avec 25 ans d'expérience.
    
MISSION : Rédiger une plainte avec constitution de partie civile EXHAUSTIVE et PERCUTANTE.

CONTEXTE :
- Référence : {reference or 'Dossier de criminalité économique complexe'}
- Demandeurs : {', '.join(demandeurs)}
- Défendeurs : {', '.join(defendeurs)}
- Infractions : {', '.join(infractions)}

INFORMATIONS ENRICHIES DES PARTIES :
{chr(10).join(demandeurs_detail)}

EXIGENCES SPÉCIFIQUES :
1. Document EXHAUSTIF (minimum 8000 mots)
2. Argumentation IMPLACABLE avec jurisprudences
3. Évaluation PRÉCISE des préjudices
4. Demandes d'actes d'instruction DÉTAILLÉES
5. Style PERCUTANT mais juridiquement irréprochable

[STRUCTURE DÉTAILLÉE DE LA PLAINTE CPC - 10 SECTIONS]
[Reprendre la structure complète du prompt original]

IMPORTANT : Cette plainte doit être un modèle du genre, exhaustive et percutante."""
    
    return prompt

def generate_simple_plainte_prompt(
    demandeurs: List[str],
    defendeurs: List[str],
    infractions: List[str],
    reference: Optional[str]
) -> str:
    """Génère le prompt pour une plainte simple"""
    
    return f"""Rédige une plainte simple mais complète et professionnelle.

PARTIES :
- Plaignants : {', '.join(demandeurs)}
- Mis en cause : {', '.join(defendeurs)}
- Infractions : {', '.join(infractions)}

Document professionnel de 3000 mots minimum avec structure complète."""

def generate_with_advanced_options(
    prompt: str,
    llm_manager,
    is_partie_civile: bool
) -> Dict[str, Any]:
    """Génère avec options avancées (température, longueur, etc.)"""
    
    # Options par défaut optimisées
    options = {
        'temperature': 0.3 if is_partie_civile else 0.5,
        'max_tokens': 8000 if is_partie_civile else 4000,
        'system_prompt': (
            "Tu es un avocat pénaliste expert avec 25 ans d'expérience, "
            "spécialisé en criminalité économique et financière. "
            "Tu rédiges des documents juridiques parfaits."
        )
    }
    
    # Interface pour modifier les options
    with st.expander("⚙️ Options avancées de génération", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            options['temperature'] = st.slider(
                "Créativité",
                0.0, 1.0, options['temperature'], 0.1,
                help="Plus bas = plus factuel"
            )
        
        with col2:
            options['max_tokens'] = st.number_input(
                "Longueur max",
                2000, 10000, options['max_tokens'], 1000
            )
    
    # Générer
    if llm_manager and llm_manager.clients:
        provider = select_best_provider(llm_manager, is_partie_civile)
        
        with st.spinner(f"⚖️ Génération via {provider}..."):
            response = llm_manager.query_single_llm(
                provider,
                prompt,
                options['system_prompt'],
                temperature=options['temperature'],
                max_tokens=options['max_tokens']
            )
            
            return {
                'success': response['success'],
                'document': response.get('response', ''),
                'provider': provider,
                'generation_time': response.get('elapsed_time', 0),
                'options': options
            }
    
    return {'success': False, 'error': 'Aucun LLM disponible'}

def select_best_provider(llm_manager, is_partie_civile: bool) -> str:
    """Sélectionne le meilleur provider selon le type de document"""
    
    available = [p for p in llm_manager.clients.keys()]
    
    # Préférences selon le type
    if is_partie_civile:
        # Pour CPC : préférer les modèles puissants
        preferences = ['anthropic', 'openai', 'google', 'mistral', 'groq']
    else:
        # Pour plainte simple : plus flexible
        preferences = ['openai', 'anthropic', 'google', 'groq', 'mistral']
    
    # Sélectionner selon les préférences
    for pref in preferences:
        if pref in available:
            return pref
    
    # Sinon prendre le premier disponible
    return available[0] if available else None

# ========================= VÉRIFICATION DES JURISPRUDENCES =========================

def verify_document_jurisprudences(content: str) -> Dict[str, Any]:
    """Vérifie toutes les jurisprudences citées dans un document"""
    
    if not ADVANCED_MANAGERS:
        return {'available': False}
    
    try:
        verifier = JurisprudenceVerifier()
        
        # Extraire les références
        references = verifier.extract_references(content)
        
        # Vérifier chaque référence
        results = []
        for ref in references:
            result = verifier.verify_reference(ref)
            results.append({
                'reference': ref,
                'valid': result.is_valid,
                'confidence': result.confidence,
                'source': result.source_verified
            })
        
        # Calculer les statistiques
        valid_count = sum(1 for r in results if r['valid'])
        total_count = len(results)
        
        return {
            'available': True,
            'results': results,
            'statistics': {
                'total': total_count,
                'verified': valid_count,
                'confidence': (valid_count / total_count * 100) if total_count > 0 else 0
            }
        }
        
    except Exception as e:
        return {'available': False, 'error': str(e)}

def verify_jurisprudences_in_analysis(content: str):
    """Interface Streamlit pour vérifier les jurisprudences"""
    
    st.markdown("### 🔍 Vérification des jurisprudences citées")
    
    if not ADVANCED_MANAGERS:
        st.warning("⚠️ Module de vérification non disponible")
        return
    
    try:
        verifier = JurisprudenceVerifier()
        verification_results = display_jurisprudence_verification(content, verifier)
        
        if verification_results:
            # Statistiques
            verified_count = sum(1 for r in verification_results if r.status == 'verified')
            total_count = len(verification_results)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Jurisprudences vérifiées", f"{verified_count}/{total_count}")
            
            with col2:
                confidence = (verified_count / total_count * 100) if total_count > 0 else 0
                st.metric("Fiabilité des sources", f"{confidence:.0f}%")
            
            return verification_results
            
    except Exception as e:
        st.error(f"Erreur vérification : {e}")
        return []

# ========================= AMÉLIORATION DE STYLE =========================

def improve_document_style(content: str, target_style: str) -> str:
    """Améliore le style d'un document avec StyleAnalyzer"""
    
    if not ADVANCED_MANAGERS or not StyleAnalyzer:
        return content
    
    try:
        analyzer = StyleAnalyzer()
        
        if hasattr(analyzer, 'analyze_and_improve'):
            improved = analyzer.analyze_and_improve(
                content,
                target_style=target_style,
                document_type='legal'
            )
            
            if improved and improved != content:
                st.success("✨ Document amélioré avec l'analyseur de style")
                return improved
                
    except Exception as e:
        st.warning(f"⚠️ Amélioration de style non disponible : {e}")
    
    return content

# ========================= SUGGESTIONS D'AMÉLIORATION =========================

def generate_improvement_suggestions(
    document: str,
    is_partie_civile: bool,
    enriched_parties: Dict[str, Any]
) -> List[str]:
    """Génère des suggestions pour améliorer le document"""
    
    suggestions = []
    
    # Analyser le document
    word_count = len(document.split())
    has_juridictions = bool(re.search(r'Cass\.|CA |CE ', document))
    has_amounts = bool(re.search(r'\d+\s*€|euros?', document))
    has_dates = bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', document))
    
    # Suggestions selon l'analyse
    if word_count < (5000 if is_partie_civile else 2000):
        suggestions.append("📝 Développer davantage les faits et circonstances")
    
    if not has_juridictions:
        suggestions.append("⚖️ Ajouter des jurisprudences pour renforcer l'argumentation")
    
    if not has_amounts and is_partie_civile:
        suggestions.append("💰 Préciser les montants des préjudices")
    
    if not has_dates:
        suggestions.append("📅 Ajouter une chronologie précise des faits")
    
    # Suggestions selon les parties enrichies
    for partie, info in enriched_parties.items():
        if info and 'missing_info' in info:
            suggestions.append(f"🏢 Compléter les informations manquantes pour {partie}")
    
    # Suggestions spécifiques CPC
    if is_partie_civile:
        required_sections = [
            "DEMANDES D'ACTES D'INSTRUCTION",
            "ÉVALUATION DÉTAILLÉE DES PRÉJUDICES",
            "CONSTITUTION DE PARTIE CIVILE"
        ]
        
        for section in required_sections:
            if section not in document.upper():
                suggestions.append(f"➕ Ajouter la section : {section}")
    
    return suggestions

# ========================= COMPARAISON MULTI-IA =========================

def compare_all_providers(prompt: str, llm_manager) -> Dict[str, Any]:
    """Compare les résultats de tous les providers disponibles"""
    
    if not llm_manager or not llm_manager.clients:
        return {'error': 'Aucun provider disponible'}
    
    results = {}
    
    st.markdown("### 🤖 Comparaison multi-IA")
    
    # Générer avec chaque provider
    for provider in llm_manager.clients.keys():
        with st.spinner(f"Génération avec {provider}..."):
            response = llm_manager.query_single_llm(
                provider,
                prompt,
                "Tu es un expert juridique.",
                temperature=0.3,
                max_tokens=2000  # Limiter pour la comparaison
            )
            
            if response['success']:
                results[provider] = {
                    'content': response['response'],
                    'time': response.get('elapsed_time', 0),
                    'word_count': len(response['response'].split())
                }
                st.success(f"✅ {provider} - {results[provider]['word_count']} mots en {results[provider]['time']:.1f}s")
            else:
                st.error(f"❌ {provider} - Erreur")
    
    # Afficher les résultats
    if results:
        for provider, result in results.items():
            with st.expander(f"{provider} ({result['word_count']} mots)"):
                st.text_area("", result['content'][:1000] + "...", height=200)
    
    return results

# ========================= EXPORT DES FONCTIONNALITÉS =========================

# Exporter toutes les fonctionnalités avancées
__all__ = [
    'generate_advanced_plainte',
    'enrich_parties_information',
    'verify_document_jurisprudences',
    'verify_jurisprudences_in_analysis',
    'improve_document_style',
    'generate_improvement_suggestions',
    'compare_all_providers'
]
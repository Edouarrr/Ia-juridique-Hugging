# modules/comparison.py
"""Module de comparaison de documents juridiques"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from managers.multi_llm_manager import MultiLLMManager
from utils.helpers import extract_entities, clean_key

def process_comparison_request(query: str, analysis: dict):
    """Traite une demande de comparaison"""
    
    st.markdown("### 🔄 Comparaison de documents")
    
    # Collecter les documents à comparer
    documents = collect_documents_for_comparison(analysis)
    
    if len(documents) < 2:
        st.warning("⚠️ Au moins 2 documents sont nécessaires pour une comparaison")
        return
    
    # Configuration
    config = display_comparison_config_interface(documents, analysis)
    
    if st.button("🚀 Lancer la comparaison", key="start_comparison", type="primary"):
        with st.spinner("🔄 Comparaison en cours..."):
            comparison_result = generate_comparison(documents, config, analysis)
            
            if comparison_result:
                st.session_state.comparison_result = comparison_result
                display_comparison_results(comparison_result)

def collect_documents_for_comparison(analysis: dict) -> List[Dict[str, Any]]:
    """Collecte les documents pour la comparaison"""
    documents = []
    
    # Documents locaux
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        documents.append({
            'id': doc_id,
            'title': doc.title,
            'content': doc.content,
            'source': doc.source,
            'metadata': doc.metadata
        })
    
    # Filtrer selon le contexte
    if analysis.get('reference'):
        ref_lower = analysis['reference'].lower()
        documents = [d for d in documents if ref_lower in d['title'].lower() or ref_lower in d.get('source', '').lower()]
    
    return documents

def display_comparison_config_interface(documents: List[Dict[str, Any]], analysis: dict) -> dict:
    """Interface de configuration pour la comparaison"""
    
    config = {}
    
    # Type de comparaison
    config['comparison_type'] = st.selectbox(
        "🔍 Type de comparaison",
        ["auditions", "expertises", "contrats", "versions", "declarations", "documents_generique"],
        format_func=lambda x: {
            "auditions": "📋 Comparaison d'auditions/témoignages",
            "expertises": "🔬 Comparaison d'expertises",
            "contrats": "📄 Comparaison de contrats",
            "versions": "📑 Comparaison de versions",
            "declarations": "💬 Comparaison de déclarations",
            "documents_generique": "📄 Comparaison générique"
        }.get(x, x.title()),
        key="comparison_type_select"
    )
    
    # Options de comparaison
    col1, col2 = st.columns(2)
    
    with col1:
        config['detail_level'] = st.select_slider(
            "Niveau de détail",
            options=["Résumé", "Standard", "Détaillé", "Très détaillé"],
            value="Détaillé",
            key="comparison_detail"
        )
        
        config['focus_differences'] = st.checkbox(
            "Focus sur les différences",
            value=True,
            key="focus_differences"
        )
    
    with col2:
        config['chronological'] = st.checkbox(
            "Analyse chronologique",
            value=config['comparison_type'] in ['auditions', 'declarations'],
            key="chronological_analysis"
        )
        
        config['highlight_contradictions'] = st.checkbox(
            "Mettre en évidence les contradictions",
            value=True,
            key="highlight_contradictions"
        )
    
    # Sélection des documents
    with st.expander("📄 Documents à comparer", expanded=True):
        st.info("Sélectionnez au moins 2 documents")
        
        selected_docs = []
        for i, doc in enumerate(documents):
            is_selected = st.checkbox(
                f"📄 {doc['title']}",
                value=i < 2,  # Sélectionner les 2 premiers par défaut
                key=f"select_doc_compare_{i}"
            )
            if is_selected:
                selected_docs.append(doc)
        
        config['selected_documents'] = selected_docs
    
    # Options avancées
    with st.expander("⚙️ Options avancées", expanded=False):
        config['similarity_threshold'] = st.slider(
            "Seuil de similarité",
            0.0, 1.0, 0.7,
            help="Pour détecter les passages similaires",
            key="similarity_threshold"
        )
        
        config['min_change_length'] = st.number_input(
            "Longueur minimale des changements",
            min_value=10,
            max_value=200,
            value=50,
            help="En caractères",
            key="min_change_length"
        )
        
        config['include_metadata'] = st.checkbox(
            "Inclure les métadonnées",
            value=True,
            key="include_metadata_compare"
        )
    
    return config

def generate_comparison(documents: List[Dict[str, Any]], config: dict, analysis: dict) -> Dict[str, Any]:
    """Génère la comparaison des documents"""
    
    # Analyse basique
    basic_comparison = perform_basic_comparison(documents, config)
    
    # Analyse IA si disponible
    if len(documents) <= 5:  # Limiter pour l'IA
        ai_comparison = perform_ai_comparison(documents, config, analysis)
        if ai_comparison:
            basic_comparison = merge_comparisons(basic_comparison, ai_comparison)
    
    # Créer les visualisations
    visualizations = create_comparison_visualizations(basic_comparison, config)
    
    return {
        'type': config['comparison_type'],
        'document_count': len(documents),
        'documents': [{'id': d['id'], 'title': d['title']} for d in documents],
        'comparison': basic_comparison,
        'visualizations': visualizations,
        'config': config,
        'timestamp': datetime.now()
    }

def perform_basic_comparison(documents: List[Dict[str, Any]], config: dict) -> Dict[str, Any]:
    """Effectue une comparaison basique des documents"""
    
    comparison = {
        'convergences': [],
        'divergences': [],
        'evolutions': [],
        'statistics': {},
        'entities_comparison': {},
        'timeline': []
    }
    
    # Extraire les entités de chaque document
    doc_entities = {}
    for doc in documents:
        entities = extract_entities(doc['content'])
        doc_entities[doc['id']] = entities
    
    # Comparer les entités
    comparison['entities_comparison'] = compare_entities(doc_entities)
    
    # Analyse du contenu
    if config['comparison_type'] == 'auditions':
        comparison.update(compare_testimonies(documents, config))
    elif config['comparison_type'] == 'contrats':
        comparison.update(compare_contracts(documents, config))
    elif config['comparison_type'] == 'expertises':
        comparison.update(compare_expertises(documents, config))
    else:
        comparison.update(generic_comparison(documents, config))
    
    # Statistiques globales
    comparison['statistics'] = calculate_comparison_statistics(comparison, documents)
    
    return comparison

def compare_entities(doc_entities: Dict[str, Dict]) -> Dict[str, Any]:
    """Compare les entités entre documents"""
    
    all_persons = set()
    all_organizations = set()
    all_locations = set()
    all_dates = set()
    
    # Collecter toutes les entités
    for entities in doc_entities.values():
        all_persons.update(entities.get('persons', []))
        all_organizations.update(entities.get('organizations', []))
        all_locations.update(entities.get('locations', []))
        all_dates.update(entities.get('dates', []))
    
    # Analyser la présence dans chaque document
    entity_presence = {
        'persons': {},
        'organizations': {},
        'locations': {},
        'dates': {}
    }
    
    for person in all_persons:
        entity_presence['persons'][person] = []
        for doc_id, entities in doc_entities.items():
            if person in entities.get('persons', []):
                entity_presence['persons'][person].append(doc_id)
    
    # Même logique pour les autres types
    for org in all_organizations:
        entity_presence['organizations'][org] = []
        for doc_id, entities in doc_entities.items():
            if org in entities.get('organizations', []):
                entity_presence['organizations'][org].append(doc_id)
    
    return {
        'all_entities': {
            'persons': list(all_persons),
            'organizations': list(all_organizations),
            'locations': list(all_locations),
            'dates': list(all_dates)
        },
        'presence_matrix': entity_presence,
        'common_entities': {
            'persons': [p for p, docs in entity_presence['persons'].items() if len(docs) > 1],
            'organizations': [o for o, docs in entity_presence['organizations'].items() if len(docs) > 1]
        }
    }

def compare_testimonies(documents: List[Dict[str, Any]], config: dict) -> Dict[str, Any]:
    """Compare spécifiquement des témoignages/auditions"""
    
    comparison = {
        'convergences': [],
        'divergences': [],
        'evolutions': []
    }
    
    # Points clés à comparer dans les témoignages
    key_aspects = [
        'chronologie', 'acteurs', 'lieux', 'actions', 
        'motivations', 'contradictions'
    ]
    
    # Analyser chaque aspect
    for aspect in key_aspects:
        aspect_data = extract_testimony_aspect(documents, aspect)
        
        # Identifier convergences et divergences
        if all_similar(aspect_data.values()):
            comparison['convergences'].append({
                'aspect': aspect,
                'point': f"Accord sur {aspect}",
                'details': summarize_aspect(aspect_data),
                'documents': list(aspect_data.keys())
            })
        else:
            comparison['divergences'].append({
                'aspect': aspect,
                'point': f"Divergence sur {aspect}",
                'details': explain_differences(aspect_data),
                'documents': list(aspect_data.keys())
            })
    
    # Détecter les évolutions (si chronologique)
    if config.get('chronological'):
        comparison['evolutions'] = detect_testimony_evolution(documents)
    
    return comparison

def compare_contracts(documents: List[Dict[str, Any]], config: dict) -> Dict[str, Any]:
    """Compare spécifiquement des contrats"""
    
    comparison = {
        'convergences': [],
        'divergences': [],
        'clauses_comparison': {}
    }
    
    # Éléments contractuels à comparer
    contract_elements = [
        'parties', 'objet', 'durée', 'montant', 'conditions',
        'obligations', 'pénalités', 'résiliation'
    ]
    
    for element in contract_elements:
        element_data = {}
        
        for doc in documents:
            # Extraire l'élément du contrat
            extracted = extract_contract_element(doc['content'], element)
            element_data[doc['id']] = extracted
        
        # Comparer
        if all_similar(element_data.values()):
            comparison['convergences'].append({
                'element': element,
                'point': f"{element.capitalize()} identique",
                'details': element_data[documents[0]['id']],
                'documents': list(element_data.keys())
            })
        else:
            comparison['divergences'].append({
                'element': element,
                'point': f"{element.capitalize()} différent",
                'details': element_data,
                'documents': list(element_data.keys())
            })
    
    # Analyse des clauses
    comparison['clauses_comparison'] = compare_contract_clauses(documents)
    
    return comparison

def compare_expertises(documents: List[Dict[str, Any]], config: dict) -> Dict[str, Any]:
    """Compare spécifiquement des expertises"""
    
    comparison = {
        'convergences': [],
        'divergences': [],
        'methodologies': {},
        'conclusions': {}
    }
    
    # Éléments d'expertise à comparer
    expertise_elements = [
        'méthodologie', 'observations', 'analyses', 'conclusions',
        'recommandations', 'réserves'
    ]
    
    for element in expertise_elements:
        element_data = {}
        
        for doc in documents:
            extracted = extract_expertise_element(doc['content'], element)
            element_data[doc['title']] = extracted
        
        # Analyser les similarités/différences
        if element == 'conclusions':
            comparison['conclusions'] = element_data
            
            # Vérifier si les conclusions convergent
            if conclusions_agree(element_data.values()):
                comparison['convergences'].append({
                    'point': "Conclusions convergentes",
                    'details': "Les experts arrivent aux mêmes conclusions",
                    'data': element_data
                })
            else:
                comparison['divergences'].append({
                    'point': "Conclusions divergentes",
                    'details': "Les experts ont des conclusions différentes",
                    'data': element_data
                })
        
        elif element == 'méthodologie':
            comparison['methodologies'] = element_data
    
    return comparison

def generic_comparison(documents: List[Dict[str, Any]], config: dict) -> Dict[str, Any]:
    """Comparaison générique de documents"""
    
    comparison = {
        'convergences': [],
        'divergences': [],
        'similarity_matrix': {}
    }
    
    # Calcul de similarité entre tous les documents
    for i, doc1 in enumerate(documents):
        for j, doc2 in enumerate(documents[i+1:], i+1):
            similarity = calculate_text_similarity(doc1['content'], doc2['content'])
            
            key = f"{doc1['title']} vs {doc2['title']}"
            comparison['similarity_matrix'][key] = {
                'score': similarity,
                'similar_passages': find_similar_passages(
                    doc1['content'], 
                    doc2['content'],
                    config['similarity_threshold']
                ),
                'different_passages': find_different_passages(
                    doc1['content'],
                    doc2['content'],
                    config['similarity_threshold']
                )
            }
    
    # Identifier les points de convergence et divergence
    for key, data in comparison['similarity_matrix'].items():
        # Convergences
        for passage in data['similar_passages'][:5]:  # Top 5
            comparison['convergences'].append({
                'documents': key,
                'point': "Passage similaire",
                'details': passage['text'][:200] + "...",
                'similarity': passage['score']
            })
        
        # Divergences
        for passage in data['different_passages'][:5]:  # Top 5
            comparison['divergences'].append({
                'documents': key,
                'point': "Passage différent",
                'details': {
                    'doc1': passage['text1'][:200] + "...",
                    'doc2': passage['text2'][:200] + "..."
                }
            })
    
    return comparison

def perform_ai_comparison(documents: List[Dict[str, Any]], config: dict, analysis: dict) -> Optional[Dict[str, Any]]:
    """Effectue une comparaison enrichie par l'IA"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return None
    
    # Construire le prompt selon le type
    if config['comparison_type'] == 'auditions':
        prompt = build_testimony_comparison_prompt(documents, config)
    elif config['comparison_type'] == 'expertises':
        prompt = build_expertise_comparison_prompt(documents, config)
    else:
        prompt = build_generic_comparison_prompt(documents, config)
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            prompt,
            "Tu es un expert en analyse comparative de documents juridiques.",
            temperature=0.3
        )
        
        if response['success']:
            return parse_ai_comparison_response(response['response'], config)
            
    except Exception as e:
        st.error(f"Erreur IA: {str(e)}")
    
    return None

def build_testimony_comparison_prompt(documents: List[Dict[str, Any]], config: dict) -> str:
    """Construit le prompt pour comparer des témoignages"""
    
    prompt = """Compare ces témoignages/auditions en identifiant :

1. CONVERGENCES
   - Points sur lesquels les témoins s'accordent
   - Éléments factuels confirmés
   - Chronologie commune

2. DIVERGENCES
   - Contradictions flagrantes
   - Versions différentes des faits
   - Incohérences temporelles

3. ÉVOLUTIONS
   - Changements dans les déclarations
   - Nouveaux éléments apparus
   - Rétractations ou modifications

4. CRÉDIBILITÉ
   - Cohérence interne de chaque témoignage
   - Éléments vérifiables
   - Indices de sincérité/mensonge

TÉMOIGNAGES À COMPARER:
"""
    
    for doc in documents:
        prompt += f"\n\n--- {doc['title']} ---\n{doc['content'][:2000]}..."
    
    prompt += "\n\nFournis une analyse structurée et objective."
    
    return prompt

def build_expertise_comparison_prompt(documents: List[Dict[str, Any]], config: dict) -> str:
    """Construit le prompt pour comparer des expertises"""
    
    prompt = """Compare ces expertises en analysant :

1. MÉTHODOLOGIES
   - Approches utilisées
   - Protocoles suivis
   - Outils et techniques

2. OBSERVATIONS
   - Constats communs
   - Observations divergentes
   - Données collectées

3. ANALYSES
   - Interprétations convergentes
   - Points de désaccord
   - Raisonnements différents

4. CONCLUSIONS
   - Conclusions identiques
   - Conclusions opposées
   - Nuances et réserves

EXPERTISES À COMPARER:
"""
    
    for doc in documents:
        prompt += f"\n\n--- {doc['title']} ---\n{doc['content'][:2000]}..."
    
    return prompt

def build_generic_comparison_prompt(documents: List[Dict[str, Any]], config: dict) -> str:
    """Construit un prompt de comparaison générique"""
    
    detail_instruction = {
        "Résumé": "Fournis un résumé concis des principales similarités et différences.",
        "Standard": "Fournis une analyse équilibrée des points communs et divergents.",
        "Détaillé": "Fournis une analyse approfondie avec exemples précis.",
        "Très détaillé": "Fournis une analyse exhaustive avec citations et références."
    }
    
    prompt = f"""Compare ces documents en suivant ces instructions :

NIVEAU DE DÉTAIL : {detail_instruction.get(config['detail_level'], 'Standard')}

Identifie :
1. Points de convergence (éléments similaires ou identiques)
2. Points de divergence (différences notables)
3. Éléments présents dans certains documents mais pas dans d'autres
4. Évolution ou progression si applicable

DOCUMENTS À COMPARER:
"""
    
    for doc in documents:
        prompt += f"\n\n--- {doc['title']} ---\n{doc['content'][:2000]}..."
    
    if config.get('focus_differences'):
        prompt += "\n\nACCORDE UNE ATTENTION PARTICULIÈRE AUX DIFFÉRENCES ET CONTRADICTIONS."
    
    return prompt

def parse_ai_comparison_response(response: str, config: dict) -> Dict[str, Any]:
    """Parse la réponse de l'IA pour extraire la comparaison"""
    
    comparison = {
        'convergences': [],
        'divergences': [],
        'analysis': response,
        'ai_insights': []
    }
    
    # Extraire les sections
    sections = response.split('\n\n')
    current_section = None
    
    for section in sections:
        section_lower = section.lower()
        
        if 'convergence' in section_lower or 'accord' in section_lower:
            current_section = 'convergences'
        elif 'divergence' in section_lower or 'contradiction' in section_lower:
            current_section = 'divergences'
        elif current_section:
            # Parser les points
            points = extract_comparison_points(section)
            
            if current_section == 'convergences':
                comparison['convergences'].extend(points)
            elif current_section == 'divergences':
                comparison['divergences'].extend(points)
    
    # Extraire les insights
    if 'crédibilité' in response.lower() or 'conclusion' in response.lower():
        insights = extract_ai_insights(response)
        comparison['ai_insights'] = insights
    
    return comparison

def merge_comparisons(basic: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
    """Fusionne les comparaisons basique et IA"""
    
    merged = basic.copy()
    
    # Ajouter les éléments de l'IA
    if ai:
        # Fusionner les convergences
        existing_conv = {c['point'] for c in merged['convergences']}
        for conv in ai.get('convergences', []):
            if conv.get('point') not in existing_conv:
                merged['convergences'].append(conv)
        
        # Fusionner les divergences
        existing_div = {d['point'] for d in merged['divergences']}
        for div in ai.get('divergences', []):
            if div.get('point') not in existing_div:
                merged['divergences'].append(div)
        
        # Ajouter l'analyse IA
        merged['ai_analysis'] = ai.get('analysis', '')
        merged['ai_insights'] = ai.get('ai_insights', [])
    
    return merged

def create_comparison_visualizations(comparison: Dict[str, Any], config: dict) -> Dict[str, Any]:
    """Crée les visualisations pour la comparaison"""
    
    visualizations = {}
    
    if not PLOTLY_AVAILABLE:
        return visualizations
    
    # Graphique des convergences/divergences
    if comparison.get('convergences') or comparison.get('divergences'):
        fig = create_convergence_divergence_chart(comparison)
        visualizations['conv_div_chart'] = fig
    
    # Matrice de similarité
    if comparison.get('similarity_matrix'):
        fig = create_similarity_heatmap(comparison['similarity_matrix'])
        visualizations['similarity_heatmap'] = fig
    
    # Timeline si applicable
    if comparison.get('timeline'):
        fig = create_comparison_timeline(comparison['timeline'])
        visualizations['timeline'] = fig
    
    # Graphique des entités
    if comparison.get('entities_comparison'):
        fig = create_entities_comparison_chart(comparison['entities_comparison'])
        visualizations['entities_chart'] = fig
    
    return visualizations

def calculate_comparison_statistics(comparison: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcule les statistiques de la comparaison"""
    
    stats = {
        'total_convergences': len(comparison.get('convergences', [])),
        'total_divergences': len(comparison.get('divergences', [])),
        'total_evolutions': len(comparison.get('evolutions', [])),
        'document_count': len(documents),
        'total_words': sum(len(doc['content'].split()) for doc in documents),
        'avg_document_length': sum(len(doc['content']) for doc in documents) / len(documents),
        'reliability_score': 0
    }
    
    # Calculer un score de fiabilité
    if stats['total_convergences'] + stats['total_divergences'] > 0:
        stats['reliability_score'] = stats['total_convergences'] / (stats['total_convergences'] + stats['total_divergences'])
    
    # Statistiques des entités
    if comparison.get('entities_comparison'):
        entities = comparison['entities_comparison'].get('all_entities', {})
        stats['total_persons'] = len(entities.get('persons', []))
        stats['total_organizations'] = len(entities.get('organizations', []))
        stats['common_entities'] = len(comparison['entities_comparison'].get('common_entities', {}).get('persons', []))
    
    return stats

def display_comparison_results(comparison_result: Dict[str, Any]):
    """Affiche les résultats de la comparaison"""
    
    # Déjà implémenté dans le module principal
    # Cette fonction est appelée depuis là-bas
    pass

# Fonctions utilitaires

def extract_testimony_aspect(documents: List[Dict[str, Any]], aspect: str) -> Dict[str, Any]:
    """Extrait un aspect spécifique des témoignages"""
    
    aspect_data = {}
    
    for doc in documents:
        content = doc['content'].lower()
        
        if aspect == 'chronologie':
            # Extraire les dates et heures
            dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', content)
            times = re.findall(r'\d{1,2}h\d{0,2}', content)
            aspect_data[doc['id']] = {'dates': dates, 'times': times}
            
        elif aspect == 'acteurs':
            # Utiliser extract_entities
            entities = extract_entities(doc['content'])
            aspect_data[doc['id']] = entities.get('persons', [])
            
        elif aspect == 'lieux':
            entities = extract_entities(doc['content'])
            aspect_data[doc['id']] = entities.get('locations', [])
            
        # Autres aspects...
    
    return aspect_data

def all_similar(values) -> bool:
    """Vérifie si toutes les valeurs sont similaires"""
    
    values_list = list(values)
    if not values_list:
        return True
    
    first = values_list[0]
    
    # Comparaison basique
    return all(v == first for v in values_list)

def summarize_aspect(aspect_data: Dict[str, Any]) -> str:
    """Résume un aspect convergent"""
    
    # Prendre la première valeur comme référence
    values = list(aspect_data.values())
    if not values:
        return "Aucune donnée"
    
    first = values[0]
    
    if isinstance(first, list):
        return f"Éléments communs : {', '.join(str(v) for v in first[:5])}"
    else:
        return str(first)

def explain_differences(aspect_data: Dict[str, Any]) -> str:
    """Explique les différences trouvées"""
    
    differences = []
    
    items = list(aspect_data.items())
    for i, (doc1, data1) in enumerate(items):
        for doc2, data2 in items[i+1:]:
            if data1 != data2:
                differences.append(f"{doc1}: {data1} vs {doc2}: {data2}")
    
    return " | ".join(differences[:3])  # Limiter à 3

def detect_testimony_evolution(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Détecte l'évolution dans les témoignages"""
    
    evolutions = []
    
    # Trier par date si possible
    sorted_docs = sorted(documents, key=lambda d: d.get('metadata', {}).get('date', ''))
    
    # Comparer séquentiellement
    for i in range(len(sorted_docs) - 1):
        doc1 = sorted_docs[i]
        doc2 = sorted_docs[i + 1]
        
        # Chercher les changements
        changes = find_changes(doc1['content'], doc2['content'])
        
        if changes:
            evolutions.append({
                'from': doc1['title'],
                'to': doc2['title'],
                'changes': changes[:5]  # Top 5 changements
            })
    
    return evolutions

def extract_contract_element(content: str, element: str) -> str:
    """Extrait un élément spécifique d'un contrat"""
    
    content_lower = content.lower()
    
    patterns = {
        'parties': r'entre[:\s]+([^,]+),.*?et[:\s]+([^,]+)',
        'objet': r'objet[:\s]+([^\n]+)',
        'durée': r'durée[:\s]+([^\n]+)',
        'montant': r'montant[:\s]+([^\n]+)|prix[:\s]+([^\n]+)',
        'conditions': r'conditions[:\s]+([^\n]+)',
        'obligations': r'obligations[:\s]+([^\n]+)',
        'pénalités': r'pénalités[:\s]+([^\n]+)',
        'résiliation': r'résiliation[:\s]+([^\n]+)'
    }
    
    pattern = patterns.get(element, '')
    if pattern:
        match = re.search(pattern, content_lower)
        if match:
            return match.group(0)
    
    return "Non trouvé"

def compare_contract_clauses(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare les clauses entre contrats"""
    
    clauses_comparison = {}
    
    # Identifier les clauses dans chaque document
    for doc in documents:
        clauses = extract_contract_clauses(doc['content'])
        clauses_comparison[doc['title']] = clauses
    
    return clauses_comparison

def extract_contract_clauses(content: str) -> List[str]:
    """Extrait les clauses d'un contrat"""
    
    # Pattern pour les clauses numérotées
    clause_pattern = r'(?:article|clause)\s*\d+[:\s-]+([^\n]+(?:\n(?!\s*(?:article|clause)\s*\d+)[^\n]+)*)'
    
    clauses = re.findall(clause_pattern, content, re.IGNORECASE | re.MULTILINE)
    
    return [c.strip() for c in clauses]

def extract_expertise_element(content: str, element: str) -> str:
    """Extrait un élément d'expertise"""
    
    content_lower = content.lower()
    
    # Chercher la section
    section_start = content_lower.find(element)
    if section_start == -1:
        return "Section non trouvée"
    
    # Trouver la fin de la section (prochain titre)
    next_sections = ['méthodologie', 'observations', 'analyses', 'conclusions', 'recommandations']
    section_end = len(content)
    
    for next_element in next_sections:
        if next_element != element:
            pos = content_lower.find(next_element, section_start + len(element))
            if pos != -1 and pos < section_end:
                section_end = pos
    
    return content[section_start:section_end].strip()

def conclusions_agree(conclusions: list) -> bool:
    """Vérifie si les conclusions s'accordent"""
    
    # Analyse sémantique simple
    positive_words = ['confirme', 'valide', 'établi', 'prouvé', 'certain']
    negative_words = ['infirme', 'invalide', 'réfute', 'impossible', 'exclu']
    
    sentiments = []
    
    for conclusion in conclusions:
        conclusion_lower = str(conclusion).lower()
        
        positive_count = sum(1 for word in positive_words if word in conclusion_lower)
        negative_count = sum(1 for word in negative_words if word in conclusion_lower)
        
        if positive_count > negative_count:
            sentiments.append('positive')
        elif negative_count > positive_count:
            sentiments.append('negative')
        else:
            sentiments.append('neutral')
    
    # Vérifier si tous les sentiments sont alignés
    return len(set(sentiments)) == 1

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calcule la similarité entre deux textes"""
    
    # Utiliser SequenceMatcher pour une similarité basique
    return SequenceMatcher(None, text1, text2).ratio()

def find_similar_passages(text1: str, text2: str, threshold: float) -> List[Dict[str, Any]]:
    """Trouve les passages similaires entre deux textes"""
    
    similar_passages = []
    
    # Diviser en phrases
    sentences1 = text1.split('.')
    sentences2 = text2.split('.')
    
    for s1 in sentences1:
        if len(s1.strip()) < 20:
            continue
            
        for s2 in sentences2:
            if len(s2.strip()) < 20:
                continue
                
            similarity = SequenceMatcher(None, s1, s2).ratio()
            
            if similarity >= threshold:
                similar_passages.append({
                    'text': s1.strip(),
                    'score': similarity
                })
                break
    
    return sorted(similar_passages, key=lambda x: x['score'], reverse=True)

def find_different_passages(text1: str, text2: str, threshold: float) -> List[Dict[str, Any]]:
    """Trouve les passages différents entre deux textes"""
    
    different_passages = []
    
    # Diviser en paragraphes
    paragraphs1 = text1.split('\n\n')
    paragraphs2 = text2.split('\n\n')
    
    # Passages uniques au document 1
    for p1 in paragraphs1:
        if len(p1.strip()) < 50:
            continue
            
        max_similarity = 0
        for p2 in paragraphs2:
            similarity = SequenceMatcher(None, p1, p2).ratio()
            max_similarity = max(max_similarity, similarity)
        
        if max_similarity < (1 - threshold):
            different_passages.append({
                'text1': p1.strip(),
                'text2': '[Absent]'
            })
    
    return different_passages[:10]  # Limiter

def find_changes(text1: str, text2: str) -> List[str]:
    """Trouve les changements entre deux textes"""
    
    changes = []
    
    # Utiliser difflib pour trouver les changements
    import difflib
    
    lines1 = text1.split('\n')
    lines2 = text2.split('\n')
    
    differ = difflib.unified_diff(lines1, lines2, lineterm='')
    
    for line in differ:
        if line.startswith('+') and not line.startswith('+++'):
            changes.append(f"Ajouté: {line[1:]}")
        elif line.startswith('-') and not line.startswith('---'):
            changes.append(f"Supprimé: {line[1:]}")
    
    return changes

def extract_comparison_points(section: str) -> List[Dict[str, str]]:
    """Extrait les points de comparaison d'une section"""
    
    points = []
    
    # Chercher les points listés
    lines = section.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('-') or line.startswith('•') or re.match(r'^\d+\.', line):
            # Nettoyer et ajouter
            point_text = re.sub(r'^[-•\d.]+\s*', '', line)
            
            points.append({
                'point': point_text[:100],  # Titre court
                'details': point_text
            })
    
    return points

def extract_ai_insights(response: str) -> List[str]:
    """Extrait les insights de l'analyse IA"""
    
    insights = []
    
    # Patterns pour les insights
    insight_patterns = [
        r'[Ii]l apparaît que[:\s]+([^\n]+)',
        r'[Oo]n peut conclure[:\s]+([^\n]+)',
        r'[Ll]\'analyse révèle[:\s]+([^\n]+)',
        r'[Ii]l est notable que[:\s]+([^\n]+)'
    ]
    
    for pattern in insight_patterns:
        matches = re.findall(pattern, response)
        insights.extend(matches)
    
    return insights

# Fonctions de visualisation

def create_convergence_divergence_chart(comparison: Dict[str, Any]) -> go.Figure:
    """Crée un graphique des convergences/divergences"""
    
    labels = ['Convergences', 'Divergences', 'Évolutions']
    values = [
        len(comparison.get('convergences', [])),
        len(comparison.get('divergences', [])),
        len(comparison.get('evolutions', []))
    ]
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    
    fig.update_layout(
        title="Répartition de l'analyse comparative",
        height=400
    )
    
    return fig

def create_similarity_heatmap(similarity_matrix: Dict[str, Dict]) -> go.Figure:
    """Crée une heatmap de similarité"""
    
    # Extraire les données
    comparisons = list(similarity_matrix.keys())
    scores = [data['score'] for data in similarity_matrix.values()]
    
    # Créer la matrice pour la heatmap
    # Pour simplifier, on affiche juste les scores
    fig = go.Figure(data=go.Bar(
        x=comparisons,
        y=scores,
        text=[f"{s:.0%}" for s in scores],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Scores de similarité entre documents",
        xaxis_title="Comparaisons",
        yaxis_title="Similarité",
        yaxis_range=[0, 1],
        height=400
    )
    
    return fig

def create_comparison_timeline(timeline_data: List[Dict]) -> go.Figure:
    """Crée une timeline de comparaison"""
    
    # Implémenter selon les données de timeline
    # Pour l'instant, retourner un graphique vide
    fig = go.Figure()
    fig.update_layout(title="Timeline comparative")
    
    return fig

def create_entities_comparison_chart(entities_data: Dict[str, Any]) -> go.Figure:
    """Crée un graphique de comparaison des entités"""
    
    # Données pour le graphique
    entity_types = ['Personnes', 'Organisations', 'Lieux']
    counts = [
        len(entities_data.get('all_entities', {}).get('persons', [])),
        len(entities_data.get('all_entities', {}).get('organizations', [])),
        len(entities_data.get('all_entities', {}).get('locations', []))
    ]
    
    common_counts = [
        len(entities_data.get('common_entities', {}).get('persons', [])),
        len(entities_data.get('common_entities', {}).get('organizations', [])),
        0  # Pas de lieux communs calculés pour l'instant
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Total',
        x=entity_types,
        y=counts
    ))
    
    fig.add_trace(go.Bar(
        name='Communs',
        x=entity_types,
        y=common_counts
    ))
    
    fig.update_layout(
        title="Entités dans les documents",
        xaxis_title="Type d'entité",
        yaxis_title="Nombre",
        barmode='group',
        height=400
    )
    
    return fig
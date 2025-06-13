# modules/mapping.py
"""Module de cartographie des relations et entités juridiques"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
import re
from collections import defaultdict, Counter

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    st.warning("⚠️ NetworkX non installé - Fonctionnalités d'analyse réseau limitées")

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from modules.dataclasses import Entity, Relationship, Document
from utils.helpers import extract_entities, clean_key
from managers.multi_llm_manager import MultiLLMManager

def process_mapping_request(query: str, analysis: dict):
    """Traite une demande de cartographie des relations"""
    
    st.markdown("### 🗺️ Cartographie des relations")
    
    # Collecter les documents
    documents = collect_documents_for_mapping(analysis)
    
    if not documents:
        st.warning("⚠️ Aucun document disponible pour la cartographie")
        return
    
    # Configuration
    config = display_mapping_config_interface(documents, analysis)
    
    if st.button("🚀 Générer la cartographie", key="generate_mapping", type="primary"):
        with st.spinner("🔄 Analyse des relations en cours..."):
            mapping_result = generate_relationship_mapping(documents, config, analysis)
            
            if mapping_result:
                st.session_state.mapping_result = mapping_result
                display_mapping_results(mapping_result)

def collect_documents_for_mapping(analysis: dict) -> List[Dict[str, Any]]:
    """Collecte les documents pour la cartographie"""
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
    
    # Filtrer si référence spécifique
    if analysis.get('reference'):
        ref_lower = analysis['reference'].lower()
        documents = [d for d in documents if ref_lower in d['title'].lower() or ref_lower in d.get('source', '').lower()]
    
    return documents

def display_mapping_config_interface(documents: List[Dict[str, Any]], analysis: dict) -> dict:
    """Interface de configuration pour la cartographie"""
    
    config = {}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Type de cartographie
        config['mapping_type'] = st.selectbox(
            "🗺️ Type de cartographie",
            ["complete", "personnes", "societes", "flux_financiers", "hierarchique"],
            format_func=lambda x: {
                "complete": "🌐 Cartographie complète",
                "personnes": "👥 Relations entre personnes",
                "societes": "🏢 Structure sociétaire",
                "flux_financiers": "💰 Flux financiers",
                "hierarchique": "📊 Relations hiérarchiques"
            }.get(x, x.title()),
            key="mapping_type_select"
        )
        
        # Profondeur d'analyse
        config['depth'] = st.slider(
            "🔍 Profondeur d'analyse",
            1, 3, 2,
            help="1: Relations directes | 2: +indirectes | 3: Réseau complet",
            key="analysis_depth"
        )
    
    with col2:
        # Seuil de relation
        config['min_strength'] = st.slider(
            "💪 Force minimale des relations",
            0.0, 1.0, 0.3,
            help="Filtrer les relations faibles",
            key="min_strength_slider"
        )
        
        # Layout
        config['layout'] = st.selectbox(
            "📐 Disposition",
            ["spring", "circular", "hierarchical", "kamada_kawai"],
            format_func=lambda x: {
                "spring": "🌸 Spring (organique)",
                "circular": "⭕ Circulaire",
                "hierarchical": "📊 Hiérarchique",
                "kamada_kawai": "🎯 Kamada-Kawai"
            }.get(x, x.title()),
            key="layout_select"
        )
    
    with col3:
        # Options d'affichage
        config['show_labels'] = st.checkbox(
            "🏷️ Afficher les labels",
            value=True,
            key="show_labels_check"
        )
        
        config['show_weights'] = st.checkbox(
            "📊 Afficher les poids",
            value=False,
            key="show_weights_check"
        )
        
        config['color_by'] = st.selectbox(
            "🎨 Colorer par",
            ["type", "centrality", "community"],
            format_func=lambda x: {
                "type": "Type d'entité",
                "centrality": "Centralité",
                "community": "Communauté"
            }.get(x, x.title()),
            key="color_by_select"
        )
    
    # Sélection des documents
    with st.expander("📄 Documents à analyser", expanded=True):
        select_all = st.checkbox("Tout sélectionner", value=True, key="select_all_mapping")
        
        selected_docs = []
        for i, doc in enumerate(documents):
            is_selected = st.checkbox(
                f"📄 {doc['title']}",
                value=select_all,
                key=f"select_doc_mapping_{i}"
            )
            if is_selected:
                selected_docs.append(doc)
        
        config['selected_documents'] = selected_docs
    
    # Filtres d'entités
    with st.expander("🔍 Filtres d'entités", expanded=False):
        config['entity_types'] = st.multiselect(
            "Types d'entités",
            ["personne", "société", "organisation", "lieu"],
            default=["personne", "société"],
            key="entity_types_select"
        )
        
        config['exclude_entities'] = st.text_area(
            "Entités à exclure (une par ligne)",
            placeholder="Ex:\nFrance\nParis",
            height=100,
            key="exclude_entities"
        )
        
        config['focus_entities'] = st.text_input(
            "Focus sur ces entités",
            placeholder="Ex: Jean Dupont, Société XYZ",
            key="focus_entities"
        )
    
    return config

def generate_relationship_mapping(documents: List[Dict[str, Any]], config: dict, analysis: dict) -> Dict[str, Any]:
    """Génère la cartographie des relations"""
    
    # Extraire les entités et relations
    entities, relationships = extract_entities_and_relationships(documents, config)
    
    if not entities:
        st.warning("⚠️ Aucune entité trouvée dans les documents")
        return None
    
    # Enrichir avec l'IA si nécessaire
    if len(relationships) < 10 and config.get('depth', 1) > 1:
        entities, relationships = enrich_with_ai_analysis(documents, entities, relationships, config)
    
    # Filtrer selon la configuration
    filtered_entities, filtered_relationships = filter_mapping_data(entities, relationships, config)
    
    # Analyser le réseau
    network_analysis = None
    if NETWORKX_AVAILABLE:
        network_analysis = analyze_network(filtered_entities, filtered_relationships)
    
    # Créer la visualisation
    visualization = None
    if PLOTLY_AVAILABLE:
        visualization = create_network_visualization(filtered_entities, filtered_relationships, config, network_analysis)
    
    return {
        'type': config['mapping_type'],
        'entities': filtered_entities,
        'relationships': filtered_relationships,
        'analysis': network_analysis or basic_network_analysis(filtered_entities, filtered_relationships),
        'visualization': visualization,
        'document_count': len(config['selected_documents']),
        'config': config,
        'timestamp': datetime.now()
    }

def extract_entities_and_relationships(documents: List[Dict[str, Any]], config: dict) -> Tuple[List[Entity], List[Relationship]]:
    """Extrait les entités et relations des documents"""
    
    all_entities = {}  # nom -> Entity
    all_relationships = []
    
    for doc in documents:
        # Extraire les entités du document
        doc_entities = extract_document_entities(doc, config)
        
        # Fusionner avec les entités existantes
        for entity in doc_entities:
            if entity.name in all_entities:
                # Fusionner les informations
                existing = all_entities[entity.name]
                existing.mentions_count += entity.mentions_count
                existing.aliases.extend(entity.aliases)
                existing.aliases = list(set(existing.aliases))
            else:
                all_entities[entity.name] = entity
        
        # Extraire les relations
        doc_relationships = extract_document_relationships(doc, doc_entities, config)
        all_relationships.extend(doc_relationships)
    
    # Consolider les relations
    consolidated_relationships = consolidate_relationships(all_relationships)
    
    return list(all_entities.values()), consolidated_relationships

def extract_document_entities(doc: Dict[str, Any], config: dict) -> List[Entity]:
    """Extrait les entités d'un document"""
    
    content = doc['content']
    entities = []
    
    # Utiliser la fonction helper pour extraire les entités de base
    basic_entities = extract_entities(content)
    
    # Convertir en objets Entity selon le type de mapping
    if config['mapping_type'] in ['personnes', 'complete']:
        for person in basic_entities.get('persons', []):
            entity = Entity(
                name=person,
                type='person',
                mentions_count=content.count(person),
                first_mention=doc.get('title', 'Document')
            )
            entities.append(entity)
    
    if config['mapping_type'] in ['societes', 'complete', 'flux_financiers']:
        for org in basic_entities.get('organizations', []):
            entity = Entity(
                name=org,
                type='company',
                mentions_count=content.count(org),
                first_mention=doc.get('title', 'Document')
            )
            entities.append(entity)
    
    # Extraction spécifique selon le type
    if config['mapping_type'] == 'flux_financiers':
        # Extraire les comptes bancaires
        account_pattern = r'\b(?:compte|IBAN|RIB)\s*:?\s*([A-Z0-9]+)'
        accounts = re.findall(account_pattern, content)
        for account in accounts:
            entity = Entity(
                name=f"Compte {account[:8]}...",
                type='account',
                mentions_count=1,
                first_mention=doc.get('title', 'Document')
            )
            entities.append(entity)
    
    return entities

def extract_document_relationships(doc: Dict[str, Any], entities: List[Entity], config: dict) -> List[Relationship]:
    """Extrait les relations d'un document"""
    
    content = doc['content']
    relationships = []
    
    # Créer un mapping nom -> entité
    entity_map = {e.name.lower(): e for e in entities}
    
    # Patterns de relations selon le type
    relation_patterns = get_relation_patterns(config['mapping_type'])
    
    for pattern_info in relation_patterns:
        pattern = pattern_info['pattern']
        rel_type = pattern_info['type']
        
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            # Extraire les entités de la relation
            source_entity, target_entity = extract_entities_from_match(match, entity_map, entities)
            
            if source_entity and target_entity:
                relationship = Relationship(
                    source=source_entity.name,
                    target=target_entity.name,
                    type=rel_type,
                    strength=calculate_relationship_strength(match.group(0), doc),
                    evidence=[doc.get('title', 'Document')]
                )
                relationships.append(relationship)
    
    # Relations de proximité
    proximity_relationships = extract_proximity_relationships(content, entities, config)
    relationships.extend(proximity_relationships)
    
    return relationships

def get_relation_patterns(mapping_type: str) -> List[Dict[str, Any]]:
    """Retourne les patterns de relations selon le type de mapping"""
    
    patterns = {
        'complete': [
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:est|était)\s+(?:le|la|l\')\s+(\w+)\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'hierarchical'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+et\s+(\w+(?:\s+\w+)*)\s+ont\s+(?:signé|conclu)',
                'type': 'contractual'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:verse|transfère|paie)\s+.*\s+à\s+(\w+(?:\s+\w+)*)',
                'type': 'financial'
            }
        ],
        'personnes': [
            {
                'pattern': r'(\w+\s+\w+)\s+(?:époux|épouse|conjoint|marié)',
                'type': 'familial'
            },
            {
                'pattern': r'(\w+\s+\w+)\s+(?:fils|fille|enfant|parent)\s+de\s+(\w+\s+\w+)',
                'type': 'familial'
            },
            {
                'pattern': r'(\w+\s+\w+)\s+(?:associé|partenaire)\s+(?:de|avec)\s+(\w+\s+\w+)',
                'type': 'business'
            }
        ],
        'societes': [
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:filiale|succursale)\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'subsidiary'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:détient|possède|contrôle)\s+.*\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'ownership'
            },
            {
                'pattern': r'fusion\s+(?:entre|de)\s+(\w+(?:\s+\w+)*)\s+et\s+(\w+(?:\s+\w+)*)',
                'type': 'merger'
            }
        ],
        'flux_financiers': [
            {
                'pattern': r'virement\s+de\s+([0-9,.\s]+)\s*€?\s+(?:de|depuis)\s+(\w+(?:\s+\w+)*)\s+(?:à|vers)\s+(\w+(?:\s+\w+)*)',
                'type': 'transfer'
            },
            {
                'pattern': r'(\w+(?:\s+\w+)*)\s+(?:doit|verse|paie)\s+([0-9,.\s]+)\s*€?\s+à\s+(\w+(?:\s+\w+)*)',
                'type': 'payment'
            }
        ],
        'hierarchique': [
            {
                'pattern': r'(\w+\s+\w+)\s+(?:directeur|président|gérant)\s+de\s+(\w+(?:\s+\w+)*)',
                'type': 'manages'
            },
            {
                'pattern': r'(\w+\s+\w+)\s+(?:employé|salarié|travaille)\s+(?:chez|pour)\s+(\w+(?:\s+\w+)*)',
                'type': 'employed_by'
            }
        ]
    }
    
    return patterns.get(mapping_type, patterns['complete'])

def extract_entities_from_match(match, entity_map: Dict[str, Entity], all_entities: List[Entity]) -> Tuple[Optional[Entity], Optional[Entity]]:
    """Extrait les entités source et cible d'un match de pattern"""
    
    groups = match.groups()
    if len(groups) < 2:
        return None, None
    
    # Chercher les entités dans les groupes
    source_text = groups[0].lower() if groups[0] else ""
    target_text = groups[-1].lower() if groups[-1] else ""
    
    source_entity = None
    target_entity = None
    
    # Recherche exacte d'abord
    source_entity = entity_map.get(source_text)
    target_entity = entity_map.get(target_text)
    
    # Si pas trouvé, recherche partielle
    if not source_entity:
        for entity in all_entities:
            if source_text in entity.name.lower() or entity.name.lower() in source_text:
                source_entity = entity
                break
    
    if not target_entity:
        for entity in all_entities:
            if target_text in entity.name.lower() or entity.name.lower() in target_text:
                target_entity = entity
                break
    
    return source_entity, target_entity

def extract_proximity_relationships(content: str, entities: List[Entity], config: dict) -> List[Relationship]:
    """Extrait les relations basées sur la proximité dans le texte"""
    
    relationships = []
    
    # Paramètres de proximité
    window_size = 100  # caractères
    min_occurrences = 2  # minimum d'occurrences proches
    
    # Trouver les positions de chaque entité
    entity_positions = {}
    for entity in entities:
        positions = []
        for match in re.finditer(re.escape(entity.name), content, re.IGNORECASE):
            positions.append(match.start())
        entity_positions[entity.name] = positions
    
    # Analyser les proximités
    for i, entity1 in enumerate(entities):
        for entity2 in entities[i+1:]:
            if entity1.name == entity2.name:
                continue
            
            # Compter les occurrences proches
            close_occurrences = 0
            
            for pos1 in entity_positions[entity1.name]:
                for pos2 in entity_positions[entity2.name]:
                    if abs(pos1 - pos2) <= window_size:
                        close_occurrences += 1
            
            if close_occurrences >= min_occurrences:
                relationship = Relationship(
                    source=entity1.name,
                    target=entity2.name,
                    type='proximity',
                    strength=min(close_occurrences / 10, 1.0),
                    evidence=[f"Proximité textuelle ({close_occurrences} occurrences)"]
                )
                relationships.append(relationship)
    
    return relationships

def calculate_relationship_strength(context: str, doc: Dict[str, Any]) -> float:
    """Calcule la force d'une relation"""
    
    strength = 0.5  # Base
    
    # Mots renforçant la relation
    strong_words = ['principal', 'majoritaire', 'exclusif', 'unique', 'total', 'complet']
    weak_words = ['possible', 'éventuel', 'partiel', 'minoritaire', 'accessoire']
    
    context_lower = context.lower()
    
    for word in strong_words:
        if word in context_lower:
            strength += 0.1
    
    for word in weak_words:
        if word in context_lower:
            strength -= 0.1
    
    # Montants élevés renforcent les relations financières
    amounts = re.findall(r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*€', context)
    if amounts:
        for amount_str in amounts:
            try:
                amount = float(amount_str.replace('.', '').replace(',', '.'))
                if amount > 100000:
                    strength += 0.2
            except:
                pass
    
    return max(0.1, min(1.0, strength))

def consolidate_relationships(relationships: List[Relationship]) -> List[Relationship]:
    """Consolide les relations dupliquées"""
    
    # Grouper les relations identiques
    rel_groups = defaultdict(list)
    
    for rel in relationships:
        # Clé normalisée (ignorer la direction pour certains types)
        if rel.type in ['contractual', 'business', 'proximity']:
            key = tuple(sorted([rel.source, rel.target])) + (rel.type,)
        else:
            key = (rel.source, rel.target, rel.type)
        
        rel_groups[key].append(rel)
    
    # Consolider
    consolidated = []
    
    for key, group in rel_groups.items():
        if len(group) == 1:
            consolidated.append(group[0])
        else:
            # Fusionner les relations
            merged = Relationship(
                source=group[0].source,
                target=group[0].target,
                type=group[0].type,
                strength=sum(r.strength for r in group) / len(group),
                direction=group[0].direction,
                evidence=list(set(sum([r.evidence for r in group], [])))
            )
            consolidated.append(merged)
    
    return consolidated

def enrich_with_ai_analysis(documents: List[Dict[str, Any]], entities: List[Entity], 
                           relationships: List[Relationship], config: dict) -> Tuple[List[Entity], List[Relationship]]:
    """Enrichit l'analyse avec l'IA"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return entities, relationships
    
    # Construire le prompt
    prompt = f"""Analyse ces documents pour identifier TOUTES les entités et relations de type {config['mapping_type']}.

DOCUMENTS:
"""
    
    for doc in documents[:5]:  # Limiter
        prompt += f"\n--- {doc['title']} ---\n{doc['content'][:1500]}...\n"
    
    prompt += f"""
Identifie:
1. ENTITÉS (personnes, sociétés, organisations)
   - Nom complet
   - Type
   - Rôle/fonction
   - Attributs importants

2. RELATIONS
   - Entité source -> Entité cible
   - Type de relation
   - Description
   - Force (0-1)

Focus sur les relations de type : {config['mapping_type']}
"""
    
    # Interroger l'IA
    provider = list(llm_manager.clients.keys())[0]
    response = llm_manager.query_single_llm(
        provider,
        prompt,
        "Tu es un expert en analyse de réseaux et relations dans les documents juridiques.",
        temperature=0.3
    )
    
    if response['success']:
        # Parser la réponse
        new_entities, new_relationships = parse_ai_mapping_response(response['response'])
        
        # Fusionner avec l'existant
        all_entities = merge_entities(entities, new_entities)
        all_relationships = relationships + new_relationships
        
        return all_entities, consolidate_relationships(all_relationships)
    
    return entities, relationships

def parse_ai_mapping_response(response: str) -> Tuple[List[Entity], List[Relationship]]:
    """Parse la réponse de l'IA pour extraire entités et relations"""
    
    entities = []
    relationships = []
    
    lines = response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if 'ENTITÉ' in line.upper():
            current_section = 'entities'
        elif 'RELATION' in line.upper():
            current_section = 'relationships'
        elif current_section == 'entities' and line.startswith('-'):
            # Parser une entité
            entity_match = re.match(r'-\s*([^:]+):\s*(.+)', line)
            if entity_match:
                name = entity_match.group(1).strip()
                details = entity_match.group(2).strip()
                
                # Déterminer le type
                entity_type = 'person' if any(word in details.lower() for word in ['directeur', 'président', 'gérant']) else 'company'
                
                entities.append(Entity(
                    name=name,
                    type=entity_type,
                    attributes={'details': details}
                ))
        
        elif current_section == 'relationships' and '->' in line:
            # Parser une relation
            rel_match = re.match(r'([^->]+)\s*->\s*([^:]+):\s*(.+)', line)
            if rel_match:
                source = rel_match.group(1).strip()
                target = rel_match.group(2).strip()
                rel_type = rel_match.group(3).strip()
                
                relationships.append(Relationship(
                    source=source,
                    target=target,
                    type=rel_type,
                    strength=0.7
                ))
    
    return entities, relationships

def merge_entities(existing: List[Entity], new: List[Entity]) -> List[Entity]:
    """Fusionne les listes d'entités"""
    
    entity_map = {e.name.lower(): e for e in existing}
    
    for new_entity in new:
        key = new_entity.name.lower()
        if key in entity_map:
            # Fusionner les attributs
            entity_map[key].attributes.update(new_entity.attributes)
        else:
            entity_map[key] = new_entity
    
    return list(entity_map.values())

def filter_mapping_data(entities: List[Entity], relationships: List[Relationship], 
                       config: dict) -> Tuple[List[Entity], List[Relationship]]:
    """Filtre les données selon la configuration"""
    
    # Filtrer les entités
    filtered_entities = entities
    
    # Par type
    if config.get('entity_types'):
        filtered_entities = [e for e in filtered_entities if e.type in config['entity_types']]
    
    # Exclure certaines entités
    if config.get('exclude_entities'):
        exclude_list = [e.strip().lower() for e in config['exclude_entities'].split('\n') if e.strip()]
        filtered_entities = [e for e in filtered_entities if e.name.lower() not in exclude_list]
    
    # Focus sur certaines entités
    if config.get('focus_entities'):
        focus_list = [e.strip().lower() for e in config['focus_entities'].split(',') if e.strip()]
        if focus_list:
            # Garder les entités focus et leurs voisins directs
            focus_entities = {e.name for e in filtered_entities if e.name.lower() in focus_list}
            
            # Ajouter les voisins
            for rel in relationships:
                if rel.source in focus_entities:
                    focus_entities.add(rel.target)
                if rel.target in focus_entities:
                    focus_entities.add(rel.source)
            
            filtered_entities = [e for e in filtered_entities if e.name in focus_entities]
    
    # Filtrer les relations
    entity_names = {e.name for e in filtered_entities}
    filtered_relationships = [
        r for r in relationships 
        if r.source in entity_names and r.target in entity_names
        and r.strength >= config.get('min_strength', 0)
    ]
    
    return filtered_entities, filtered_relationships

def analyze_network(entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
    """Analyse le réseau avec NetworkX"""
    
    if not NETWORKX_AVAILABLE:
        return basic_network_analysis(entities, relationships)
    
    # Créer le graphe
    G = nx.Graph() if any(r.direction == 'bidirectional' for r in relationships) else nx.DiGraph()
    
    # Ajouter les nœuds
    for entity in entities:
        G.add_node(entity.name, **entity.attributes, type=entity.type)
    
    # Ajouter les arêtes
    for rel in relationships:
        if rel.direction == 'bidirectional' or isinstance(G, nx.Graph):
            G.add_edge(rel.source, rel.target, weight=rel.strength, type=rel.type)
        else:
            G.add_edge(rel.source, rel.target, weight=rel.strength, type=rel.type)
    
    # Analyses
    analysis = {
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'density': nx.density(G),
        'components': list(nx.connected_components(G.to_undirected())) if isinstance(G, nx.DiGraph) else list(nx.connected_components(G)),
        'is_connected': nx.is_connected(G.to_undirected()) if isinstance(G, nx.DiGraph) else nx.is_connected(G)
    }
    
    # Centralités
    try:
        analysis['degree_centrality'] = nx.degree_centrality(G)
        analysis['betweenness_centrality'] = nx.betweenness_centrality(G)
        
        if isinstance(G, nx.DiGraph):
            analysis['in_degree_centrality'] = nx.in_degree_centrality(G)
            analysis['out_degree_centrality'] = nx.out_degree_centrality(G)
    except:
        pass
    
    # Acteurs clés (top 5 par centralité)
    if 'degree_centrality' in analysis:
        sorted_centrality = sorted(analysis['degree_centrality'].items(), key=lambda x: x[1], reverse=True)
        analysis['key_players'] = [node for node, _ in sorted_centrality[:5]]
    
    # Communautés
    try:
        if isinstance(G, nx.Graph):
            communities = nx.community.greedy_modularity_communities(G)
            analysis['communities'] = [list(c) for c in communities]
            analysis['modularity'] = nx.community.modularity(G, communities)
    except:
        pass
    
    # Chemins
    if G.number_of_nodes() > 1:
        try:
            if nx.is_connected(G.to_undirected() if isinstance(G, nx.DiGraph) else G):
                analysis['average_shortest_path'] = nx.average_shortest_path_length(G)
                analysis['diameter'] = nx.diameter(G.to_undirected() if isinstance(G, nx.DiGraph) else G)
        except:
            pass
    
    return analysis

def basic_network_analysis(entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
    """Analyse basique du réseau sans NetworkX"""
    
    # Compter les connexions par entité
    connections = defaultdict(int)
    for rel in relationships:
        connections[rel.source] += 1
        connections[rel.target] += 1
    
    # Acteurs clés (plus de connexions)
    sorted_connections = sorted(connections.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'node_count': len(entities),
        'edge_count': len(relationships),
        'density': len(relationships) / (len(entities) * (len(entities) - 1) / 2) if len(entities) > 1 else 0,
        'key_players': [node for node, _ in sorted_connections[:5]],
        'components': [],  # Non calculé sans NetworkX
        'is_connected': None
    }

def create_network_visualization(entities: List[Entity], relationships: List[Relationship], 
                                config: dict, analysis: Dict[str, Any]) -> go.Figure:
    """Crée la visualisation du réseau avec Plotly"""
    
    if not PLOTLY_AVAILABLE:
        return None
    
    # Calculer les positions des nœuds
    pos = calculate_node_positions(entities, relationships, config['layout'])
    
    # Préparer les données pour Plotly
    edge_trace = create_edge_trace(relationships, pos)
    node_trace = create_node_trace(entities, pos, config, analysis)
    
    # Créer la figure
    fig = go.Figure(data=[edge_trace, node_trace])
    
    # Mise en forme
    fig.update_layout(
        title=f"Cartographie {config['mapping_type'].replace('_', ' ').title()}",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    # Ajouter les labels si demandé
    if config.get('show_labels'):
        for entity, (x, y) in pos.items():
            fig.add_annotation(
                x=x, y=y,
                text=entity,
                showarrow=False,
                font=dict(size=10)
            )
    
    return fig

def calculate_node_positions(entities: List[Entity], relationships: List[Relationship], layout: str) -> Dict[str, Tuple[float, float]]:
    """Calcule les positions des nœuds selon le layout"""
    
    if NETWORKX_AVAILABLE:
        # Créer un graphe NetworkX temporaire
        G = nx.Graph()
        G.add_nodes_from([e.name for e in entities])
        G.add_edges_from([(r.source, r.target) for r in relationships])
        
        # Calculer les positions selon le layout
        if layout == 'spring':
            pos = nx.spring_layout(G, k=1, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'hierarchical':
            try:
                pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
            except:
                pos = nx.spring_layout(G)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G)
    else:
        # Layout simple sans NetworkX
        n = len(entities)
        if layout == 'circular':
            # Disposition circulaire
            import math
            pos = {}
            for i, entity in enumerate(entities):
                angle = 2 * math.pi * i / n
                pos[entity.name] = (math.cos(angle), math.sin(angle))
        else:
            # Grille simple
            import math
            cols = int(math.sqrt(n)) + 1
            pos = {}
            for i, entity in enumerate(entities):
                row = i // cols
                col = i % cols
                pos[entity.name] = (col, -row)
    
    return pos

def create_edge_trace(relationships: List[Relationship], pos: Dict[str, Tuple[float, float]]) -> go.Scatter:
    """Crée le trace des arêtes pour Plotly"""
    
    edge_x = []
    edge_y = []
    
    for rel in relationships:
        if rel.source in pos and rel.target in pos:
            x0, y0 = pos[rel.source]
            x1, y1 = pos[rel.target]
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    return edge_trace

def create_node_trace(entities: List[Entity], pos: Dict[str, Tuple[float, float]], 
                     config: dict, analysis: Dict[str, Any]) -> go.Scatter:
    """Crée le trace des nœuds pour Plotly"""
    
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    
    # Couleurs par défaut
    type_colors = {
        'person': '#FF6B6B',
        'company': '#4ECDC4',
        'organization': '#45B7D1',
        'account': '#96CEB4',
        'other': '#DDA0DD'
    }
    
    for entity in entities:
        if entity.name in pos:
            x, y = pos[entity.name]
            node_x.append(x)
            node_y.append(y)
            
            # Texte du hover
            text = f"<b>{entity.name}</b><br>"
            text += f"Type: {entity.type}<br>"
            text += f"Mentions: {entity.mentions_count}"
            node_text.append(text)
            
            # Couleur selon la configuration
            if config['color_by'] == 'type':
                color = type_colors.get(entity.type, '#DDA0DD')
            elif config['color_by'] == 'centrality' and 'degree_centrality' in analysis:
                # Gradient selon la centralité
                centrality = analysis['degree_centrality'].get(entity.name, 0)
                color = centrality * 100  # Pour la colorscale
            else:
                color = '#1f77b4'
            
            node_color.append(color)
            
            # Taille selon les mentions ou la centralité
            if 'degree_centrality' in analysis:
                size = 10 + analysis['degree_centrality'].get(entity.name, 0) * 50
            else:
                size = 10 + min(entity.mentions_count, 20) * 2
            
            node_size.append(size)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=config['color_by'] == 'centrality',
            colorscale='Viridis',
            size=node_size,
            color=node_color,
            line_width=2,
            colorbar=dict(
                thickness=15,
                title='Centralité',
                xanchor='left',
                titleside='right'
            ) if config['color_by'] == 'centrality' else None
        )
    )
    
    return node_trace

def display_mapping_results(mapping_result: Dict[str, Any]):
    """Affiche les résultats de la cartographie"""
    
    st.success(f"✅ Cartographie générée : {mapping_result['analysis']['node_count']} entités, {mapping_result['analysis']['edge_count']} relations")
    
    # Métadonnées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type", mapping_result['type'].replace('_', ' ').title())
    
    with col2:
        st.metric("Entités", mapping_result['analysis']['node_count'])
    
    with col3:
        st.metric("Relations", mapping_result['analysis']['edge_count'])
    
    with col4:
        density_pct = mapping_result['analysis']['density'] * 100
        st.metric("Densité", f"{density_pct:.1f}%")
    
    # Visualisation
    if mapping_result.get('visualization'):
        st.plotly_chart(mapping_result['visualization'], use_container_width=True)
    else:
        st.info("Visualisation non disponible - Installez plotly pour les graphiques")
    
    # Analyse du réseau
    with st.expander("📊 Analyse du réseau", expanded=True):
        display_network_analysis(mapping_result['analysis'])
    
    # Liste des entités et relations
    tabs = st.tabs(["👥 Entités", "🔗 Relations", "📊 Statistiques"])
    
    with tabs[0]:
        display_entities_list(mapping_result['entities'], mapping_result['analysis'])
    
    with tabs[1]:
        display_relationships_list(mapping_result['relationships'])
    
    with tabs[2]:
        display_mapping_statistics(mapping_result)
    
    # Actions
    st.markdown("### 💾 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Exporter rapport", key="export_mapping_report"):
            report = generate_mapping_report(mapping_result)
            st.download_button(
                "💾 Télécharger rapport",
                report.encode('utf-8'),
                f"rapport_cartographie_{mapping_result['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                key="download_mapping_report"
            )
    
    with col2:
        if st.button("📊 Exporter données", key="export_mapping_data"):
            if PANDAS_AVAILABLE:
                excel_data = export_mapping_to_excel(mapping_result)
                st.download_button(
                    "💾 Télécharger Excel",
                    excel_data,
                    f"cartographie_{mapping_result['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_mapping_excel"
                )
    
    with col3:
        if st.button("🖼️ Exporter image", key="export_mapping_image"):
            if mapping_result.get('visualization'):
                # Exporter en PNG
                img_bytes = mapping_result['visualization'].to_image(format="png")
                st.download_button(
                    "💾 Télécharger PNG",
                    img_bytes,
                    f"cartographie_{mapping_result['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    "image/png",
                    key="download_mapping_png"
                )
    
    with col4:
        if NETWORKX_AVAILABLE:
            if st.button("🔍 Analyse avancée", key="advanced_network_analysis"):
                show_advanced_network_analysis(mapping_result)

def display_network_analysis(analysis: Dict[str, Any]):
    """Affiche l'analyse du réseau"""
    
    # Acteurs clés
    if 'key_players' in analysis and analysis['key_players']:
        st.markdown("#### 🎯 Acteurs principaux")
        for i, player in enumerate(analysis['key_players'], 1):
            centrality = analysis.get('degree_centrality', {}).get(player, 0)
            st.write(f"{i}. **{player}** (centralité: {centrality:.3f})")
    
    # Composantes
    if 'components' in analysis and analysis['components']:
        st.markdown("#### 🔗 Composantes connexes")
        st.write(f"Nombre de composantes : {len(analysis['components'])}")
        
        if len(analysis['components']) > 1:
            st.warning("⚠️ Le réseau n'est pas entièrement connecté")
            
            for i, component in enumerate(analysis['components'][:5], 1):
                if len(component) > 1:
                    st.write(f"Composante {i} : {len(component)} entités")
                    st.caption(f"Membres : {', '.join(list(component)[:5])}...")
    
    # Métriques globales
    if any(key in analysis for key in ['average_shortest_path', 'diameter', 'modularity']):
        st.markdown("#### 📏 Métriques globales")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'average_shortest_path' in analysis:
                st.metric("Chemin moyen", f"{analysis['average_shortest_path']:.2f}")
        
        with col2:
            if 'diameter' in analysis:
                st.metric("Diamètre", analysis['diameter'])
        
        with col3:
            if 'modularity' in analysis:
                st.metric("Modularité", f"{analysis['modularity']:.3f}")

def display_entities_list(entities: List[Entity], analysis: Dict[str, Any]):
    """Affiche la liste des entités"""
    
    # Options de tri
    sort_by = st.selectbox(
        "Trier par",
        ["Nom", "Type", "Mentions", "Centralité"],
        key="sort_entities"
    )
    
    # Trier
    if sort_by == "Nom":
        sorted_entities = sorted(entities, key=lambda e: e.name)
    elif sort_by == "Type":
        sorted_entities = sorted(entities, key=lambda e: (e.type, e.name))
    elif sort_by == "Mentions":
        sorted_entities = sorted(entities, key=lambda e: e.mentions_count, reverse=True)
    else:  # Centralité
        centrality = analysis.get('degree_centrality', {})
        sorted_entities = sorted(entities, key=lambda e: centrality.get(e.name, 0), reverse=True)
    
    # Afficher
    for entity in sorted_entities:
        with st.expander(f"{entity.name} ({entity.type})", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Type :** {entity.type}")
                st.write(f"**Mentions :** {entity.mentions_count}")
            
            with col2:
                if 'degree_centrality' in analysis:
                    centrality = analysis['degree_centrality'].get(entity.name, 0)
                    st.write(f"**Centralité :** {centrality:.3f}")
                
                if entity.first_mention:
                    st.write(f"**Première mention :** {entity.first_mention}")
            
            with col3:
                if entity.aliases:
                    st.write(f"**Alias :** {', '.join(entity.aliases)}")
                
                if entity.attributes:
                    st.write("**Attributs :**")
                    for key, value in entity.attributes.items():
                        st.caption(f"{key}: {value}")

def display_relationships_list(relationships: List[Relationship]):
    """Affiche la liste des relations"""
    
    # Grouper par type
    rel_by_type = defaultdict(list)
    for rel in relationships:
        rel_by_type[rel.type].append(rel)
    
    # Afficher par type
    for rel_type, type_relationships in rel_by_type.items():
        st.markdown(f"#### {rel_type.replace('_', ' ').title()} ({len(type_relationships)})")
        
        # Trier par force
        sorted_rels = sorted(type_relationships, key=lambda r: r.strength, reverse=True)
        
        for rel in sorted_rels[:20]:  # Limiter à 20 par type
            strength_bar = "🟩" * int(rel.strength * 5) + "⬜" * (5 - int(rel.strength * 5))
            
            st.write(f"**{rel.source}** → **{rel.target}** {strength_bar}")
            
            if rel.evidence:
                st.caption(f"Sources : {', '.join(rel.evidence[:3])}")

def display_mapping_statistics(mapping_result: Dict[str, Any]):
    """Affiche les statistiques détaillées de la cartographie"""
    
    entities = mapping_result['entities']
    relationships = mapping_result['relationships']
    analysis = mapping_result['analysis']
    
    # Statistiques des entités
    st.markdown("#### 👥 Statistiques des entités")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Types d'entités
        type_counts = Counter(e.type for e in entities)
        st.write("**Répartition par type :**")
        for entity_type, count in type_counts.most_common():
            st.write(f"- {entity_type} : {count}")
    
    with col2:
        # Top mentions
        st.write("**Plus mentionnées :**")
        top_mentioned = sorted(entities, key=lambda e: e.mentions_count, reverse=True)[:5]
        for entity in top_mentioned:
            st.write(f"- {entity.name} : {entity.mentions_count} mentions")
    
    with col3:
        # Distribution des connexions
        if 'degree_centrality' in analysis:
            centralities = list(analysis['degree_centrality'].values())
            avg_centrality = sum(centralities) / len(centralities) if centralities else 0
            st.metric("Centralité moyenne", f"{avg_centrality:.3f}")
            
            high_centrality = sum(1 for c in centralities if c > avg_centrality * 1.5)
            st.metric("Nœuds très connectés", high_centrality)
    
    # Statistiques des relations
    st.markdown("#### 🔗 Statistiques des relations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Types de relations
        rel_type_counts = Counter(r.type for r in relationships)
        st.write("**Types de relations :**")
        for rel_type, count in rel_type_counts.most_common():
            st.write(f"- {rel_type} : {count}")
    
    with col2:
        # Force des relations
        avg_strength = sum(r.strength for r in relationships) / len(relationships) if relationships else 0
        st.metric("Force moyenne", f"{avg_strength:.2f}")
        
        strong_rels = sum(1 for r in relationships if r.strength >= 0.7)
        st.metric("Relations fortes", strong_rels)
    
    with col3:
        # Direction
        bidirectional = sum(1 for r in relationships if r.direction == 'bidirectional')
        st.metric("Relations bidirectionnelles", bidirectional)
        
        unidirectional = len(relationships) - bidirectional
        st.metric("Relations unidirectionnelles", unidirectional)

def generate_mapping_report(mapping_result: Dict[str, Any]) -> str:
    """Génère un rapport textuel de la cartographie"""
    
    report = f"RAPPORT DE CARTOGRAPHIE - {mapping_result['type'].upper()}\n"
    report += "=" * 60 + "\n\n"
    
    report += f"Généré le : {mapping_result['timestamp'].strftime('%d/%m/%Y à %H:%M')}\n"
    report += f"Documents analysés : {mapping_result['document_count']}\n\n"
    
    # Résumé
    analysis = mapping_result['analysis']
    report += "RÉSUMÉ DU RÉSEAU\n"
    report += "-" * 30 + "\n"
    report += f"Nombre d'entités : {analysis['node_count']}\n"
    report += f"Nombre de relations : {analysis['edge_count']}\n"
    report += f"Densité du réseau : {analysis['density']:.2%}\n"
    report += f"Réseau connecté : {'Oui' if analysis.get('is_connected') else 'Non (fragmenté)'}\n\n"
    
    # Acteurs clés
    if 'key_players' in analysis:
        report += "ACTEURS PRINCIPAUX\n"
        report += "-" * 30 + "\n"
        for i, player in enumerate(analysis['key_players'], 1):
            report += f"{i}. {player}\n"
        report += "\n"
    
    # Entités par type
    type_counts = Counter(e.type for e in mapping_result['entities'])
    report += "RÉPARTITION DES ENTITÉS\n"
    report += "-" * 30 + "\n"
    for entity_type, count in type_counts.items():
        report += f"{entity_type.title()} : {count}\n"
    report += "\n"
    
    # Relations par type
    rel_type_counts = Counter(r.type for r in mapping_result['relationships'])
    report += "TYPES DE RELATIONS\n"
    report += "-" * 30 + "\n"
    for rel_type, count in rel_type_counts.items():
        report += f"{rel_type.replace('_', ' ').title()} : {count}\n"
    report += "\n"
    
    # Communautés détectées
    if 'communities' in analysis and analysis['communities']:
        report += "COMMUNAUTÉS DÉTECTÉES\n"
        report += "-" * 30 + "\n"
        for i, community in enumerate(analysis['communities'], 1):
            report += f"Communauté {i} : {len(community)} membres\n"
            report += f"Membres : {', '.join(list(community)[:5])}"
            if len(community) > 5:
                report += "..."
            report += "\n\n"
    
    return report

def export_mapping_to_excel(mapping_result: Dict[str, Any]) -> bytes:
    """Exporte la cartographie vers Excel"""
    
    if not PANDAS_AVAILABLE:
        return b""
    
    import io
    
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Feuille des entités
        entities_data = []
        for entity in mapping_result['entities']:
            entities_data.append({
                'Nom': entity.name,
                'Type': entity.type,
                'Mentions': entity.mentions_count,
                'Première mention': entity.first_mention or '',
                'Centralité': mapping_result['analysis'].get('degree_centrality', {}).get(entity.name, 0)
            })
        
        df_entities = pd.DataFrame(entities_data)
        df_entities.to_excel(writer, sheet_name='Entités', index=False)
        
        # Feuille des relations
        relations_data = []
        for rel in mapping_result['relationships']:
            relations_data.append({
                'Source': rel.source,
                'Cible': rel.target,
                'Type': rel.type,
                'Force': rel.strength,
                'Direction': rel.direction,
                'Sources': ', '.join(rel.evidence) if rel.evidence else ''
            })
        
        df_relations = pd.DataFrame(relations_data)
        df_relations.to_excel(writer, sheet_name='Relations', index=False)
        
        # Feuille d'analyse
        analysis_data = []
        for key, value in mapping_result['analysis'].items():
            if isinstance(value, (int, float, str)):
                analysis_data.append({'Métrique': key, 'Valeur': value})
        
        if analysis_data:
            df_analysis = pd.DataFrame(analysis_data)
            df_analysis.to_excel(writer, sheet_name='Analyse', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def show_advanced_network_analysis(mapping_result: Dict[str, Any]):
    """Affiche l'analyse réseau avancée"""
    
    st.markdown("### 🔬 Analyse réseau avancée")
    
    if not NETWORKX_AVAILABLE:
        st.error("NetworkX requis pour l'analyse avancée")
        return
    
    # Recréer le graphe
    G = nx.Graph()
    for entity in mapping_result['entities']:
        G.add_node(entity.name, **entity.attributes)
    
    for rel in mapping_result['relationships']:
        G.add_edge(rel.source, rel.target, weight=rel.strength, type=rel.type)
    
    # Analyses supplémentaires
    tabs = st.tabs(["🎯 Centralités", "🌐 Communautés", "🛤️ Chemins", "📊 Propriétés"])
    
    with tabs[0]:
        # Différentes mesures de centralité
        st.markdown("#### Mesures de centralité")
        
        centrality_measures = {
            'Degré': nx.degree_centrality(G),
            'Intermédiarité': nx.betweenness_centrality(G),
            'Proximité': nx.closeness_centrality(G),
            'Vecteur propre': nx.eigenvector_centrality(G, max_iter=1000) if G.number_of_nodes() > 1 else {}
        }
        
        # Afficher le top 5 pour chaque mesure
        for measure_name, centrality_dict in centrality_measures.items():
            if centrality_dict:
                st.write(f"**{measure_name} :**")
                top_nodes = sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)[:5]
                for node, score in top_nodes:
                    st.write(f"- {node}: {score:.3f}")
    
    with tabs[1]:
        # Détection de communautés
        st.markdown("#### Détection de communautés")
        
        if G.number_of_nodes() > 2:
            try:
                # Différents algorithmes
                communities_greedy = nx.community.greedy_modularity_communities(G)
                
                st.write(f"**Algorithme Greedy Modularity :**")
                st.write(f"Nombre de communautés : {len(communities_greedy)}")
                st.write(f"Modularité : {nx.community.modularity(G, communities_greedy):.3f}")
                
                # Afficher les communautés
                for i, community in enumerate(communities_greedy, 1):
                    with st.expander(f"Communauté {i} ({len(community)} membres)"):
                        st.write(", ".join(sorted(community)))
            except:
                st.info("Impossible de détecter des communautés dans ce réseau")
    
    with tabs[2]:
        # Analyse des chemins
        st.markdown("#### Analyse des chemins")
        
        if nx.is_connected(G):
            # Sélectionner deux nœuds
            nodes = list(G.nodes())
            
            col1, col2 = st.columns(2)
            with col1:
                source = st.selectbox("Nœud source", nodes, key="path_source")
            with col2:
                target = st.selectbox("Nœud cible", nodes, key="path_target")
            
            if source != target:
                try:
                    # Plus court chemin
                    shortest_path = nx.shortest_path(G, source, target)
                    path_length = nx.shortest_path_length(G, source, target)
                    
                    st.write(f"**Plus court chemin ({path_length} étapes) :**")
                    st.write(" → ".join(shortest_path))
                    
                    # Tous les chemins simples (limité)
                    all_paths = list(nx.all_simple_paths(G, source, target, cutoff=5))
                    if len(all_paths) > 1:
                        st.write(f"**Nombre de chemins alternatifs (≤5 étapes) :** {len(all_paths)}")
                except:
                    st.info("Pas de chemin entre ces nœuds")
        else:
            st.warning("Le réseau n'est pas connecté - Analyse des chemins limitée")
    
    with tabs[3]:
        # Propriétés du graphe
        st.markdown("#### Propriétés structurelles")
        
        properties = {
            "Nombre de nœuds": G.number_of_nodes(),
            "Nombre d'arêtes": G.number_of_edges(),
            "Densité": nx.density(G),
            "Degré moyen": sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
            "Coefficient de clustering moyen": nx.average_clustering(G),
            "Transitivité": nx.transitivity(G)
        }
        
        for prop, value in properties.items():
            if isinstance(value, float):
                st.metric(prop, f"{value:.3f}")
            else:
                st.metric(prop, value)
        
        # Distribution des degrés
        if PLOTLY_AVAILABLE:
            degrees = [d for n, d in G.degree()]
            fig = go.Figure(data=[go.Histogram(x=degrees)])
            fig.update_layout(
                title="Distribution des degrés",
                xaxis_title="Degré",
                yaxis_title="Nombre de nœuds"
            )
            st.plotly_chart(fig, use_container_width=True)
# modules/recherche.py (EXTENSION POUR ANALYSES AVANCÉES)

# Ajouter ces imports en haut du fichier
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import networkx as nx
from collections import defaultdict, Counter
import json

# Modifier la fonction analyze_universal_query pour détecter ces nouvelles demandes
def analyze_universal_query(query: str) -> dict:
    """Analyse la requête pour déterminer l'intention (VERSION ÉTENDUE)"""
    analysis = {
        'intent': 'search',  # search, analysis, redaction, timeline, mapping, comparison
        'type': 'simple',
        'has_reference': False,
        'reference': None,
        'action': None,
        'document_type': None,
        'subject_matter': None,
        'confidence': 0.0,
        'details': {}
    }
    
    query_lower = query.lower()
    
    # Détecter les références
    if '@' in query:
        analysis['has_reference'] = True
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            analysis['reference'] = ref_match.group(1)
    
    # NOUVELLES DÉTECTIONS D'ANALYSE AVANCÉE
    
    # Chronologie
    timeline_keywords = ['chronologie', 'timeline', 'calendrier', 'séquence', 'déroulement', 'historique']
    if any(kw in query_lower for kw in timeline_keywords):
        analysis['intent'] = 'timeline'
        analysis['confidence'] = 0.9
        
        # Type de chronologie
        if any(kw in query_lower for kw in ['fait', 'événement', 'action']):
            analysis['details']['timeline_type'] = 'facts'
        elif any(kw in query_lower for kw in ['procédure', 'procédural', 'juridique', 'instance']):
            analysis['details']['timeline_type'] = 'procedure'
        else:
            analysis['details']['timeline_type'] = 'general'
    
    # Cartographie/Mapping
    mapping_keywords = ['cartographie', 'mapping', 'carte', 'réseau', 'liens', 'relations', 'connexions']
    if any(kw in query_lower for kw in mapping_keywords):
        analysis['intent'] = 'mapping'
        analysis['confidence'] = 0.9
        
        # Type d'entités
        if any(kw in query_lower for kw in ['personne', 'individu', 'acteur']):
            analysis['details']['entity_type'] = 'persons'
        elif any(kw in query_lower for kw in ['société', 'entreprise', 'entité']):
            analysis['details']['entity_type'] = 'companies'
        else:
            analysis['details']['entity_type'] = 'all'
    
    # Comparaison
    comparison_keywords = ['comparer', 'comparaison', 'différence', 'convergence', 'évolution', 'contradiction']
    if any(kw in query_lower for kw in comparison_keywords):
        analysis['intent'] = 'comparison'
        analysis['confidence'] = 0.9
        
        # Type de comparaison
        if any(kw in query_lower for kw in ['audition', 'déclaration', 'témoignage']):
            analysis['details']['comparison_type'] = 'auditions'
        elif any(kw in query_lower for kw in ['version', 'récit']):
            analysis['details']['comparison_type'] = 'versions'
        else:
            analysis['details']['comparison_type'] = 'general'
    
    # Garder les détections précédentes (rédaction, etc.)
    # [Code existant pour détecter rédaction...]
    
    return analysis

# Modifier process_universal_query pour traiter ces nouvelles intentions
def process_universal_query(query: str):
    """Traite la requête universelle (VERSION ÉTENDUE)"""
    analysis = analyze_universal_query(query)
    st.session_state.query_analysis = analysis
    
    with st.spinner("🔄 Traitement de votre demande..."):
        
        # NOUVEAUX TYPES DE TRAITEMENT
        if analysis['intent'] == 'timeline':
            process_timeline_request(query, analysis)
            
        elif analysis['intent'] == 'mapping':
            process_mapping_request(query, analysis)
            
        elif analysis['intent'] == 'comparison':
            process_comparison_request(query, analysis)
            
        # Traitements existants
        elif analysis['intent'] == 'redaction':
            process_redaction_request(query, analysis)
            
        elif analysis['intent'] == 'analysis':
            process_analysis_request(query, analysis)
            
        else:  # search
            process_search_request(query, analysis)

# NOUVELLES FONCTIONS D'ANALYSE AVANCÉE

def process_timeline_request(query: str, analysis: dict):
    """Traite une demande de chronologie"""
    
    # 1. Collecter les documents pertinents
    documents = collect_timeline_documents(analysis)
    
    if not documents:
        st.warning("⚠️ Aucun document trouvé pour créer la chronologie")
        return
    
    # 2. Extraire les événements avec l'IA
    timeline_type = analysis['details'].get('timeline_type', 'general')
    events = extract_timeline_events(documents, timeline_type)
    
    # 3. Créer la visualisation
    timeline_viz = create_timeline_visualization(events, timeline_type)
    
    # 4. Stocker les résultats
    st.session_state.timeline_result = {
        'events': events,
        'visualization': timeline_viz,
        'type': timeline_type,
        'document_count': len(documents),
        'timestamp': datetime.now()
    }

def collect_timeline_documents(analysis: dict) -> list:
    """Collecte les documents pour la chronologie"""
    documents = []
    
    # Si référence spécifique
    if analysis['reference']:
        ref_results = search_by_reference(f"@{analysis['reference']}")
        documents.extend(ref_results)
    
    # Sinon chercher tous les documents avec dates
    else:
        # Rechercher dans les documents locaux
        for doc_id, doc in st.session_state.get('azure_documents', {}).items():
            # Vérifier si le document contient des dates
            if has_temporal_information(doc.content):
                documents.append({
                    'id': doc_id,
                    'title': doc.title,
                    'content': doc.content,
                    'source': doc.source
                })
    
    return documents

def has_temporal_information(content: str) -> bool:
    """Vérifie si le contenu contient des informations temporelles"""
    # Patterns de dates
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # 01/01/2024
        r'\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{2,4}',
        r'(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)',
        r'(hier|aujourd\'hui|demain)',
        r'(semaine|mois|année)\s+(dernier|dernière|prochain|prochaine)'
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    return False

def extract_timeline_events(documents: list, timeline_type: str) -> list:
    """Extrait les événements de la chronologie avec l'IA"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return []
    
    # Prompt spécialisé selon le type
    prompts = {
        'facts': """Extrais TOUS les faits et événements datés de ces documents.
Pour chaque fait, indique :
- Date exacte ou période
- Description précise du fait
- Personnes/entités impliquées
- Source/document d'origine
- Importance (1-5)

Format JSON : {"date": "YYYY-MM-DD", "description": "...", "actors": [...], "source": "...", "importance": N}""",
        
        'procedure': """Extrais TOUS les actes de procédure et étapes juridiques datés.
Pour chaque acte :
- Date exacte
- Type d'acte (plainte, audition, perquisition, mise en examen, etc.)
- Autorité concernée
- Personnes visées
- Résultat/décision

Format JSON : {"date": "YYYY-MM-DD", "type": "...", "description": "...", "authority": "...", "targets": [...]}""",
        
        'general': """Extrais TOUS les événements importants avec leurs dates.
Format JSON : {"date": "YYYY-MM-DD", "description": "...", "category": "..."}"""
    }
    
    prompt = prompts.get(timeline_type, prompts['general'])
    
    # Traiter par batch de documents
    all_events = []
    
    for i in range(0, len(documents), 5):  # Batch de 5 documents
        batch = documents[i:i+5]
        
        # Construire le contexte
        context = "\n\n".join([
            f"=== DOCUMENT: {doc['title']} ===\n{doc['content'][:2000]}"
            for doc in batch
        ])
        
        # Requête à l'IA
        full_prompt = f"{prompt}\n\nDocuments à analyser :\n{context}\n\nExtrais les événements au format JSON demandé."
        
        try:
            # Utiliser une seule IA pour la cohérence
            provider = list(llm_manager.clients.keys())[0]
            response = llm_manager.query_single_llm(
                provider,
                full_prompt,
                "Tu es un expert en analyse temporelle de documents juridiques."
            )
            
            if response['success']:
                # Parser la réponse JSON
                events = parse_timeline_events(response['response'], batch)
                all_events.extend(events)
                
        except Exception as e:
            st.warning(f"⚠️ Erreur extraction événements : {str(e)}")
    
    # Trier par date
    all_events.sort(key=lambda x: x.get('date', ''))
    
    return all_events

def parse_timeline_events(ai_response: str, source_docs: list) -> list:
    """Parse les événements extraits par l'IA"""
    events = []
    
    try:
        # Extraire les objets JSON de la réponse
        json_matches = re.findall(r'\{[^}]+\}', ai_response)
        
        for match in json_matches:
            try:
                event = json.loads(match)
                
                # Normaliser la date
                if 'date' in event:
                    event['date'] = normalize_date(event['date'])
                
                # Ajouter la source si non présente
                if 'source' not in event and source_docs:
                    event['source'] = source_docs[0]['title']
                
                events.append(event)
                
            except json.JSONDecodeError:
                continue
                
    except Exception as e:
        print(f"Erreur parsing événements : {e}")
    
    return events

def normalize_date(date_str: str) -> str:
    """Normalise une date au format YYYY-MM-DD"""
    # Essayer différents formats
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d %B %Y',
        '%d %b %Y'
    ]
    
    for fmt in formats:
        try:
            date = datetime.strptime(date_str, fmt)
            return date.strftime('%Y-%m-%d')
        except:
            continue
    
    # Si échec, retourner la date originale
    return date_str

def create_timeline_visualization(events: list, timeline_type: str):
    """Crée la visualisation de la chronologie"""
    
    if not events:
        return None
    
    # Créer un DataFrame
    df = pd.DataFrame(events)
    
    # S'assurer que les dates sont au bon format
    try:
        df['date'] = pd.to_datetime(df['date'])
    except:
        pass
    
    # Créer la figure Plotly
    fig = go.Figure()
    
    # Grouper par catégorie/type si disponible
    categories = df.get('category', df.get('type', ['Événement'] * len(df))).unique()
    colors = px.colors.qualitative.Set3[:len(categories)]
    
    for i, category in enumerate(categories):
        cat_events = df[df.get('category', df.get('type', 'Événement')) == category]
        
        # Ajouter les points
        fig.add_trace(go.Scatter(
            x=cat_events['date'],
            y=[i] * len(cat_events),
            mode='markers+text',
            name=category,
            marker=dict(size=12, color=colors[i % len(colors)]),
            text=cat_events['description'].apply(lambda x: x[:50] + '...' if len(x) > 50 else x),
            textposition='top center',
            hovertemplate='<b>%{text}</b><br>Date: %{x}<br><extra></extra>'
        ))
    
    # Mise en forme
    fig.update_layout(
        title=f"Chronologie des {timeline_type}",
        xaxis_title="Date",
        yaxis_title="Catégorie",
        height=600,
        hovermode='closest',
        showlegend=True
    )
    
    # Masquer l'axe Y si une seule catégorie
    if len(categories) == 1:
        fig.update_yaxes(visible=False)
    
    return fig

def process_mapping_request(query: str, analysis: dict):
    """Traite une demande de cartographie des relations"""
    
    # 1. Collecter les documents
    documents = collect_mapping_documents(analysis)
    
    if not documents:
        st.warning("⚠️ Aucun document trouvé pour créer la cartographie")
        return
    
    # 2. Extraire les entités et relations
    entity_type = analysis['details'].get('entity_type', 'all')
    entities, relations = extract_entities_and_relations(documents, entity_type)
    
    # 3. Créer le graphe
    graph = create_network_graph(entities, relations)
    
    # 4. Analyser le réseau
    network_analysis = analyze_network(graph)
    
    # 5. Créer la visualisation
    visualization = create_network_visualization(graph, network_analysis)
    
    # 6. Stocker les résultats
    st.session_state.mapping_result = {
        'entities': entities,
        'relations': relations,
        'graph': graph,
        'analysis': network_analysis,
        'visualization': visualization,
        'type': entity_type,
        'timestamp': datetime.now()
    }

def extract_entities_and_relations(documents: list, entity_type: str) -> tuple:
    """Extrait les entités et leurs relations avec l'IA"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return [], []
    
    # Prompt spécialisé
    prompts = {
        'persons': """Identifie TOUTES les personnes physiques et leurs relations.
Pour chaque personne : nom, rôle, fonction
Pour chaque relation : personne1, personne2, type de relation, description

Format JSON :
Entités : {"name": "...", "role": "...", "type": "person"}
Relations : {"source": "...", "target": "...", "type": "...", "description": "..."}""",
        
        'companies': """Identifie TOUTES les sociétés/entités morales et leurs relations.
Pour chaque société : nom, forme juridique, rôle
Pour chaque relation : société1, société2, type (filiale, actionnaire, client, etc.)

Format JSON :
Entités : {"name": "...", "legal_form": "...", "type": "company"}
Relations : {"source": "...", "target": "...", "type": "...", "stake": "..."}""",
        
        'all': """Identifie TOUTES les entités (personnes ET sociétés) et leurs relations.
Distingue bien personnes physiques et morales.
Indique tous les liens : hiérarchiques, capitalistiques, contractuels, familiaux.

Format JSON comme ci-dessus."""
    }
    
    prompt = prompts.get(entity_type, prompts['all'])
    
    all_entities = {}
    all_relations = []
    
    # Traiter les documents
    for doc in documents[:20]:  # Limiter
        context = f"=== DOCUMENT: {doc['title']} ===\n{doc['content'][:3000]}"
        
        full_prompt = f"{prompt}\n\nDocument à analyser :\n{context}"
        
        try:
            provider = list(llm_manager.clients.keys())[0]
            response = llm_manager.query_single_llm(
                provider,
                full_prompt,
                "Tu es un expert en analyse de réseaux et relations d'affaires."
            )
            
            if response['success']:
                entities, relations = parse_entities_relations(response['response'])
                
                # Fusionner les entités (éviter doublons)
                for entity in entities:
                    key = entity['name'].lower()
                    if key not in all_entities:
                        all_entities[key] = entity
                    else:
                        # Enrichir l'entité existante
                        all_entities[key].update(entity)
                
                all_relations.extend(relations)
                
        except Exception as e:
            print(f"Erreur extraction entités : {e}")
    
    return list(all_entities.values()), all_relations

def parse_entities_relations(ai_response: str) -> tuple:
    """Parse les entités et relations extraites par l'IA"""
    entities = []
    relations = []
    
    try:
        # Chercher les sections Entités et Relations
        entities_section = re.search(r'Entités?\s*:?\s*\n(.*?)(?=Relations?|$)', ai_response, re.DOTALL | re.IGNORECASE)
        relations_section = re.search(r'Relations?\s*:?\s*\n(.*?)$', ai_response, re.DOTALL | re.IGNORECASE)
        
        # Parser les entités
        if entities_section:
            json_matches = re.findall(r'\{[^}]+\}', entities_section.group(1))
            for match in json_matches:
                try:
                    entity = json.loads(match)
                    entities.append(entity)
                except:
                    continue
        
        # Parser les relations
        if relations_section:
            json_matches = re.findall(r'\{[^}]+\}', relations_section.group(1))
            for match in json_matches:
                try:
                    relation = json.loads(match)
                    relations.append(relation)
                except:
                    continue
                    
    except Exception as e:
        print(f"Erreur parsing entités/relations : {e}")
    
    return entities, relations

def create_network_graph(entities: list, relations: list) -> nx.Graph:
    """Crée le graphe NetworkX"""
    G = nx.Graph()
    
    # Ajouter les nœuds
    for entity in entities:
        G.add_node(
            entity['name'],
            **entity  # Ajouter tous les attributs
        )
    
    # Ajouter les arêtes
    for relation in relations:
        if relation['source'] in G and relation['target'] in G:
            G.add_edge(
                relation['source'],
                relation['target'],
                **relation  # Ajouter tous les attributs
            )
    
    return G

def analyze_network(G: nx.Graph) -> dict:
    """Analyse le réseau (centralité, clusters, etc.)"""
    analysis = {
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'density': nx.density(G),
        'components': list(nx.connected_components(G)),
        'centrality': {},
        'key_players': []
    }
    
    if G.number_of_nodes() > 0:
        # Centralité
        analysis['centrality'] = {
            'degree': nx.degree_centrality(G),
            'betweenness': nx.betweenness_centrality(G) if G.number_of_nodes() > 2 else {},
            'closeness': nx.closeness_centrality(G) if nx.is_connected(G) else {}
        }
        
        # Identifier les acteurs clés (top 5 par centralité)
        degree_sorted = sorted(analysis['centrality']['degree'].items(), key=lambda x: x[1], reverse=True)
        analysis['key_players'] = [node for node, _ in degree_sorted[:5]]
    
    return analysis

def create_network_visualization(G: nx.Graph, analysis: dict):
    """Crée la visualisation du réseau avec Plotly"""
    
    # Positions des nœuds
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Créer les traces pour les arêtes
    edge_trace = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        edge_trace.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=0.5, color='#888'),
            hoverinfo='none'
        ))
    
    # Créer la trace pour les nœuds
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Texte du hover
        node_data = G.nodes[node]
        hover_text = f"<b>{node}</b><br>"
        hover_text += f"Type: {node_data.get('type', 'Unknown')}<br>"
        hover_text += f"Rôle: {node_data.get('role', 'N/A')}<br>"
        hover_text += f"Connexions: {G.degree(node)}"
        node_text.append(hover_text)
        
        # Taille selon le degré
        node_size.append(10 + G.degree(node) * 5)
        
        # Couleur selon le type
        if node_data.get('type') == 'person':
            node_color.append('lightblue')
        elif node_data.get('type') == 'company':
            node_color.append('lightgreen')
        else:
            node_color.append('lightgray')
    
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[node for node in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=node_size,
            color=node_color,
            line_width=2
        )
    )
    
    # Créer la figure
    fig = go.Figure(data=edge_trace + [node_trace])
    
    fig.update_layout(
        title="Cartographie des relations",
        titlefont_size=16,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=700
    )
    
    return fig

def process_comparison_request(query: str, analysis: dict):
    """Traite une demande de comparaison"""
    
    # 1. Collecter les documents à comparer
    documents = collect_comparison_documents(analysis)
    
    if not documents or len(documents) < 2:
        st.warning("⚠️ Au moins 2 documents nécessaires pour la comparaison")
        return
    
    # 2. Type de comparaison
    comparison_type = analysis['details'].get('comparison_type', 'general')
    
    # 3. Extraire et comparer
    if comparison_type == 'auditions':
        comparison_result = compare_auditions(documents)
    else:
        comparison_result = compare_documents_general(documents)
    
    # 4. Créer les visualisations
    visualizations = create_comparison_visualizations(comparison_result)
    
    # 5. Stocker les résultats
    st.session_state.comparison_result = {
        'comparison': comparison_result,
        'visualizations': visualizations,
        'type': comparison_type,
        'document_count': len(documents),
        'timestamp': datetime.now()
    }

def compare_auditions(documents: list) -> dict:
    """Compare spécifiquement des auditions"""
    
    llm_manager = MultiLLMManager()
    if not llm_manager.clients:
        return {}
    
    # Prompt spécialisé pour comparaison d'auditions
    prompt = """Compare ces auditions/déclarations en détail.

Identifie pour chaque point abordé :
1. CONVERGENCES : Points sur lesquels toutes les versions concordent
2. DIVERGENCES : Points de désaccord ou contradictions
3. ÉVOLUTIONS : Changements de version d'une même personne
4. OMISSIONS : Points mentionnés par certains mais pas d'autres
5. DÉTAILS SUSPECTS : Incohérences, impossibilités factuelles

Pour chaque point, cite précisément les déclarations.

Format structuré :
### CONVERGENCES
- Point 1 : [description]
  - Personne A : "citation exacte"
  - Personne B : "citation exacte"

### DIVERGENCES
- Point 1 : [description de la divergence]
  - Version A : "citation"
  - Version B : "citation contradictoire"

### ÉVOLUTIONS
- Personne X :
  - Première version : "citation"
  - Version ultérieure : "citation modifiée"

### ANALYSE
- Fiabilité globale
- Points nécessitant vérification
- Recommandations pour l'enquête"""
    
    # Préparer le contexte
    context = "\n\n".join([
        f"=== AUDITION/DOCUMENT: {doc['title']} ===\n{doc['content'][:3000]}"
        for doc in documents[:10]  # Limiter
    ])
    
    full_prompt = f"{prompt}\n\nDocuments à comparer :\n{context}"
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            full_prompt,
            "Tu es un expert en analyse comparative de témoignages et procédures judiciaires."
        )
        
        if response['success']:
            # Parser la réponse structurée
            comparison = parse_comparison_response(response['response'])
            
            # Ajouter une analyse quantitative
            comparison['statistics'] = calculate_comparison_statistics(comparison)
            
            return comparison
            
    except Exception as e:
        st.error(f"Erreur comparaison : {e}")
        return {}

def parse_comparison_response(response: str) -> dict:
    """Parse la réponse de comparaison structurée"""
    comparison = {
        'convergences': [],
        'divergences': [],
        'evolutions': [],
        'omissions': [],
        'suspicious_details': [],
        'analysis': ''
    }
    
    # Extraire chaque section
    sections = {
        'convergences': r'###?\s*CONVERGENCES?\s*\n(.*?)(?=###|$)',
        'divergences': r'###?\s*DIVERGENCES?\s*\n(.*?)(?=###|$)',
        'evolutions': r'###?\s*[ÉE]VOLUTIONS?\s*\n(.*?)(?=###|$)',
        'analysis': r'###?\s*ANALYSE\s*\n(.*?)$'
    }
    
    for key, pattern in sections.items():
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1)
            
            if key == 'analysis':
                comparison[key] = content.strip()
            else:
                # Extraire les points
                points = re.findall(r'-\s*([^:]+):\s*([^\n]+(?:\n\s+[^\n]+)*)', content)
                comparison[key] = [{'point': p[0].strip(), 'details': p[1].strip()} for p in points]
    
    return comparison

def calculate_comparison_statistics(comparison: dict) -> dict:
    """Calcule des statistiques sur la comparaison"""
    return {
        'convergence_rate': len(comparison['convergences']) / max(
            len(comparison['convergences']) + len(comparison['divergences']), 1
        ),
        'total_points': len(comparison['convergences']) + len(comparison['divergences']),
        'evolution_count': len(comparison['evolutions']),
        'reliability_score': calculate_reliability_score(comparison)
    }

def calculate_reliability_score(comparison: dict) -> float:
    """Calcule un score de fiabilité basé sur la comparaison"""
    score = 0.5  # Base
    
    # Plus de convergences = plus fiable
    convergence_rate = len(comparison['convergences']) / max(
        len(comparison['convergences']) + len(comparison['divergences']), 1
    )
    score += convergence_rate * 0.3
    
    # Évolutions = moins fiable
    if len(comparison['evolutions']) > 0:
        score -= min(len(comparison['evolutions']) * 0.1, 0.3)
    
    # Détails suspects = moins fiable
    if len(comparison.get('suspicious_details', [])) > 0:
        score -= min(len(comparison['suspicious_details']) * 0.05, 0.2)
    
    return max(0, min(1, score))

def create_comparison_visualizations(comparison_result: dict):
    """Crée les visualisations pour la comparaison"""
    visualizations = {}
    
    # 1. Graphique en radar des convergences/divergences
    if 'statistics' in comparison_result:
        stats = comparison_result['statistics']
        
        categories = ['Convergences', 'Divergences', 'Évolutions', 'Fiabilité']
        values = [
            len(comparison_result.get('convergences', [])),
            len(comparison_result.get('divergences', [])),
            len(comparison_result.get('evolutions', [])),
            stats.get('reliability_score', 0) * 10  # Mettre à l'échelle
        ]
        
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Analyse comparative'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2]
                )
            ),
            showlegend=False,
            title="Vue d'ensemble de la comparaison"
        )
        
        visualizations['radar'] = fig_radar
    
    # 2. Timeline des évolutions si applicable
    if comparison_result.get('evolutions'):
        # Créer une timeline des changements de version
        # (Simplifiée ici, pourrait être plus sophistiquée)
        visualizations['evolution_timeline'] = create_evolution_timeline(comparison_result['evolutions'])
    
    # 3. Heatmap des points de comparaison
    visualizations['heatmap'] = create_comparison_heatmap(comparison_result)
    
    return visualizations

def create_evolution_timeline(evolutions: list):
    """Crée une timeline des évolutions de déclarations"""
    # Implémentation simplifiée
    fig = go.Figure()
    
    for i, evolution in enumerate(evolutions):
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[i, i],
            mode='lines+markers+text',
            name=f"Évolution {i+1}",
            text=['Version initiale', 'Version modifiée'],
            textposition='top center'
        ))
    
    fig.update_layout(
        title="Évolutions des déclarations",
        xaxis_title="Versions",
        yaxis_title="Points modifiés",
        height=400
    )
    
    return fig

def create_comparison_heatmap(comparison_result: dict):
    """Crée une heatmap des points de comparaison"""
    # Construire une matrice simple
    points = []
    categories = []
    
    for conv in comparison_result.get('convergences', []):
        points.append(conv['point'])
        categories.append('Convergence')
    
    for div in comparison_result.get('divergences', []):
        points.append(div['point'])
        categories.append('Divergence')
    
    for evo in comparison_result.get('evolutions', []):
        points.append(evo.get('point', 'Évolution'))
        categories.append('Évolution')
    
    # Créer une matrice binaire simple
    matrix = []
    for i, cat in enumerate(categories):
        row = [0] * len(set(categories))
        row[list(set(categories)).index(cat)] = 1
        matrix.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=list(set(categories)),
        y=points,
        colorscale='RdYlGn',
        showscale=False
    ))
    
    fig.update_layout(
        title="Répartition des points de comparaison",
        xaxis_title="Type",
        yaxis_title="Points analysés",
        height=max(400, len(points) * 30)
    )
    
    return fig

# Modifier show_unified_results_tab pour afficher ces nouveaux résultats
def show_unified_results_tab():
    """Affiche les résultats unifiés (VERSION ÉTENDUE)"""
    
    # Résultats de chronologie
    if 'timeline_result' in st.session_state:
        show_timeline_results()
    
    # Résultats de cartographie
    elif 'mapping_result' in st.session_state:
        show_mapping_results()
    
    # Résultats de comparaison
    elif 'comparison_result' in st.session_state:
        show_comparison_results()
    
    # Résultats existants (rédaction, analyse, recherche)
    elif 'redaction_result' in st.session_state:
        show_redaction_results()
    
    elif 'ai_analysis_results' in st.session_state and st.session_state.ai_analysis_results:
        show_ai_analysis_results()
    
    elif 'search_results' in st.session_state and st.session_state.search_results:
        show_search_results_unified()
    
    else:
        st.info("🔍 Utilisez la barre de recherche universelle pour commencer")
        show_extended_examples()

def show_timeline_results():
    """Affiche les résultats de chronologie"""
    result = st.session_state.timeline_result
    
    st.markdown("### ⏱️ Chronologie")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Événements", len(result['events']))
    
    with col2:
        timeline_types = {
            'facts': '📅 Faits',
            'procedure': '⚖️ Procédure',
            'general': '📊 Générale'
        }
        st.metric("Type", timeline_types.get(result['type'], result['type']))
    
    with col3:
        st.metric("Documents analysés", result['document_count'])
    
    # Visualisation principale
    if result['visualization']:
        st.plotly_chart(result['visualization'], use_container_width=True)
    
    # Liste détaillée des événements
    with st.expander("📋 Détail des événements", expanded=False):
        for event in result['events']:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.write(f"**{event.get('date', 'N/A')}**")
            
            with col2:
                st.write(event.get('description', ''))
                if 'actors' in event:
                    st.caption(f"Acteurs : {', '.join(event['actors'])}")
                if 'source' in event:
                    st.caption(f"Source : {event['source']}")
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Exporter chronologie", key="export_timeline"):
            export_timeline(result)
    
    with col2:
        if st.button("📊 Analyser périodes", key="analyze_periods"):
            analyze_timeline_periods(result)
    
    with col3:
        if st.button("🔍 Zoomer période", key="zoom_period"):
            zoom_timeline_period(result)

def show_mapping_results():
    """Affiche les résultats de cartographie"""
    result = st.session_state.mapping_result
    
    st.markdown("### 🗺️ Cartographie des relations")
    
    # Métadonnées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Entités", result['analysis']['node_count'])
    
    with col2:
        st.metric("Relations", result['analysis']['edge_count'])
    
    with col3:
        st.metric("Densité", f"{result['analysis']['density']:.2f}")
    
    with col4:
        entity_types = {
            'persons': '👤 Personnes',
            'companies': '🏢 Sociétés',
            'all': '🔍 Toutes'
        }
        st.metric("Type", entity_types.get(result['type'], result['type']))
    
    # Visualisation du réseau
    if result['visualization']:
        st.plotly_chart(result['visualization'], use_container_width=True)
    
    # Acteurs clés
    if result['analysis']['key_players']:
        st.markdown("### 🎯 Acteurs clés")
        
        cols = st.columns(len(result['analysis']['key_players'][:5]))
        for i, (col, player) in enumerate(zip(cols, result['analysis']['key_players'][:5])):
            with col:
                st.metric(
                    f"#{i+1}",
                    player,
                    f"Centralité: {result['analysis']['centrality']['degree'].get(player, 0):.2f}"
                )
    
    # Analyse détaillée
    with st.expander("📊 Analyse du réseau", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Composantes connexes**")
            for i, component in enumerate(result['analysis']['components']):
                st.write(f"Groupe {i+1}: {len(component)} entités")
        
        with col2:
            st.markdown("**Métriques de centralité**")
            top_central = sorted(
                result['analysis']['centrality']['degree'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for entity, centrality in top_central:
                st.write(f"• {entity}: {centrality:.3f}")
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Exporter réseau", key="export_network"):
            export_network(result)
    
    with col2:
        if st.button("🔍 Analyser clusters", key="analyze_clusters"):
            analyze_network_clusters(result)
    
    with col3:
        if st.button("📊 Matrice relations", key="relation_matrix"):
            show_relation_matrix(result)

def show_comparison_results():
    """Affiche les résultats de comparaison"""
    result = st.session_state.comparison_result
    
    st.markdown("### 🔄 Comparaison de documents")
    
    # Métadonnées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", result['document_count'])
    
    with col2:
        comp_types = {
            'auditions': '🎤 Auditions',
            'versions': '📄 Versions',
            'general': '📊 Général'
        }
        st.metric("Type", comp_types.get(result['type'], result['type']))
    
    with col3:
        if 'statistics' in result['comparison']:
            st.metric(
                "Convergence",
                f"{result['comparison']['statistics']['convergence_rate']:.0%}"
            )
    
    with col4:
        if 'statistics' in result['comparison']:
            st.metric(
                "Fiabilité",
                f"{result['comparison']['statistics']['reliability_score']:.0%}"
            )
    
    # Visualisations
    if 'visualizations' in result:
        # Vue radar
        if 'radar' in result['visualizations']:
            st.plotly_chart(result['visualizations']['radar'], use_container_width=True)
        
        # Tabs pour les détails
        tabs = st.tabs(['✅ Convergences', '❌ Divergences', '🔄 Évolutions', '📊 Analyse'])
        
        with tabs[0]:
            show_convergences(result['comparison'])
        
        with tabs[1]:
            show_divergences(result['comparison'])
        
        with tabs[2]:
            show_evolutions(result['comparison'])
        
        with tabs[3]:
            show_comparison_analysis(result['comparison'])
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Exporter comparaison", key="export_comparison"):
            export_comparison(result)
    
    with col2:
        if st.button("📝 Générer rapport", key="generate_comparison_report"):
            generate_comparison_report(result)
    
    with col3:
        if st.button("🔍 Approfondir", key="deepen_comparison"):
            deepen_comparison_analysis(result)

def show_convergences(comparison: dict):
    """Affiche les points de convergence"""
    convergences = comparison.get('convergences', [])
    
    if not convergences:
        st.info("Aucune convergence identifiée")
        return
    
    for i, conv in enumerate(convergences):
        with st.container():
            st.markdown(f"**{i+1}. {conv['point']}**")
            st.write(conv['details'])

def show_divergences(comparison: dict):
    """Affiche les points de divergence"""
    divergences = comparison.get('divergences', [])
    
    if not divergences:
        st.info("Aucune divergence identifiée")
        return
    
    for i, div in enumerate(divergences):
        with st.container():
            st.markdown(f"**{i+1}. {div['point']}**")
            st.write(div['details'])
            
            # Alerte si divergence importante
            if 'critique' in div.get('details', '').lower():
                st.warning("⚠️ Divergence critique détectée")

def show_evolutions(comparison: dict):
    """Affiche les évolutions de déclarations"""
    evolutions = comparison.get('evolutions', [])
    
    if not evolutions:
        st.info("Aucune évolution identifiée")
        return
    
    for i, evo in enumerate(evolutions):
        with st.container():
            st.markdown(f"**{i+1}. {evo.get('point', 'Évolution')}**")
            st.write(evo.get('details', ''))

def show_comparison_analysis(comparison: dict):
    """Affiche l'analyse globale de la comparaison"""
    if 'analysis' in comparison:
        st.markdown(comparison['analysis'])
    
    if 'statistics' in comparison:
        st.markdown("### 📊 Statistiques")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Points analysés", comparison['statistics']['total_points'])
            st.metric("Évolutions détectées", comparison['statistics']['evolution_count'])
        
        with col2:
            reliability = comparison['statistics']['reliability_score']
            color = "🟢" if reliability > 0.7 else "🟡" if reliability > 0.4 else "🔴"
            st.metric("Score de fiabilité", f"{color} {reliability:.0%}")

def show_extended_examples():
    """Affiche des exemples étendus incluant les nouvelles fonctionnalités"""
    
    st.markdown("### 💡 Exemples d'utilisation avancée")
    
    advanced_examples = [
        {
            'category': '⏱️ Chronologies',
            'examples': [
                {
                    'title': 'Chronologie des faits',
                    'query': 'chronologie des faits @affaire_martin',
                    'desc': 'Génère une timeline de tous les événements'
                },
                {
                    'title': 'Chronologie procédurale',
                    'query': 'chronologie de la procédure @dossier_xyz',
                    'desc': 'Timeline des actes de procédure uniquement'
                }
            ]
        },
        {
            'category': '🗺️ Cartographies',
            'examples': [
                {
                    'title': 'Réseau de personnes',
                    'query': 'cartographie des personnes @affaire_corruption',
                    'desc': 'Visualise les liens entre individus'
                },
                {
                    'title': 'Relations sociétés',
                    'query': 'mapping des sociétés et leurs liens @groupe_abc',
                    'desc': 'Carte des relations capitalistiques'
                }
            ]
        },
        {
            'category': '🔄 Comparaisons',
            'examples': [
                {
                    'title': 'Comparer auditions',
                    'query': 'comparer les auditions @affaire_martin',
                    'desc': 'Analyse convergences et contradictions'
                },
                {
                    'title': 'Évolution déclarations',
                    'query': 'comparer évolution des versions @témoin_principal',
                    'desc': 'Détecte les changements de version'
                }
            ]
        }
    ]
    
    for category in advanced_examples:
        st.markdown(f"**{category['category']}**")
        
        cols = st.columns(len(category['examples']))
        for col, example in zip(cols, category['examples']):
            with col:
                with st.container():
                    st.markdown(f"**{example['title']}**")
                    st.caption(example['desc'])
                    st.code(example['query'])
                    
                    if st.button("Utiliser", key=f"use_{example['query']}"):
                        st.session_state.universal_query = example['query']
                        st.rerun()

# Fonctions d'export et d'actions supplémentaires
def export_timeline(result: dict):
    """Exporte la chronologie"""
    # Format CSV
    events_df = pd.DataFrame(result['events'])
    csv = events_df.to_csv(index=False)
    
    st.download_button(
        "💾 Télécharger CSV",
        csv,
        f"chronologie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        key="download_timeline_csv"
    )

def export_network(result: dict):
    """Exporte le réseau"""
    # Format GraphML
    import io
    buffer = io.BytesIO()
    nx.write_graphml(result['graph'], buffer)
    
    st.download_button(
        "💾 Télécharger GraphML",
        buffer.getvalue(),
        f"reseau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.graphml",
        "application/xml",
        key="download_network_graphml"
    )

def export_comparison(result: dict):
    """Exporte la comparaison"""
    # Format structuré
    comparison_text = format_comparison_for_export(result['comparison'])
    
    st.download_button(
        "💾 Télécharger rapport",
        comparison_text,
        f"comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain",
        key="download_comparison_txt"
    )

def format_comparison_for_export(comparison: dict) -> str:
    """Formate la comparaison pour l'export"""
    output = "RAPPORT DE COMPARAISON\n" + "=" * 50 + "\n\n"
    
    output += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if 'statistics' in comparison:
        output += f"Taux de convergence : {comparison['statistics']['convergence_rate']:.0%}\n"
        output += f"Score de fiabilité : {comparison['statistics']['reliability_score']:.0%}\n\n"
    
    output += "CONVERGENCES\n" + "-" * 30 + "\n"
    for conv in comparison.get('convergences', []):
        output += f"• {conv['point']}\n  {conv['details']}\n\n"
    
    output += "DIVERGENCES\n" + "-" * 30 + "\n"
    for div in comparison.get('divergences', []):
        output += f"• {div['point']}\n  {div['details']}\n\n"
    
    if comparison.get('analysis'):
        output += "ANALYSE\n" + "-" * 30 + "\n"
        output += comparison['analysis']
    
    return output

# Fonctions helper pour les documents
def collect_mapping_documents(analysis: dict) -> list:
    """Collecte les documents pour la cartographie"""
    # Réutiliser la logique de collect_timeline_documents
    return collect_timeline_documents(analysis)

def collect_comparison_documents(analysis: dict) -> list:
    """Collecte les documents pour la comparaison"""
    documents = []
    
    # Si référence spécifique
    if analysis['reference']:
        ref_results = search_by_reference(f"@{analysis['reference']}")
        
        # Filtrer par type si spécifié
        if analysis['details'].get('comparison_type') == 'auditions':
            # Chercher spécifiquement les auditions
            audition_keywords = ['audition', 'interrogatoire', 'déclaration', 'témoignage']
            documents = [
                doc for doc in ref_results
                if any(kw in doc.get('title', '').lower() or kw in doc.get('content', '').lower()
                      for kw in audition_keywords)
            ]
        else:
            documents = ref_results
    
    return documents

def compare_documents_general(documents: list) -> dict:
    """Comparaison générale de documents"""
    # Réutiliser la logique de compare_auditions avec un prompt plus général
    return compare_auditions(documents)

# Fonctions d'analyse supplémentaires (placeholder)
def analyze_timeline_periods(result: dict):
    """Analyse les périodes de la chronologie"""
    st.info("🔄 Analyse des périodes à implémenter")

def zoom_timeline_period(result: dict):
    """Zoom sur une période spécifique"""
    st.info("🔍 Zoom temporel à implémenter")

def analyze_network_clusters(result: dict):
    """Analyse les clusters du réseau"""
    st.info("🔍 Analyse de clusters à implémenter")

def show_relation_matrix(result: dict):
    """Affiche la matrice des relations"""
    st.info("📊 Matrice de relations à implémenter")

def generate_comparison_report(result: dict):
    """Génère un rapport de comparaison détaillé"""
    st.info("📝 Génération de rapport à implémenter")

def deepen_comparison_analysis(result: dict):
    """Approfondit l'analyse comparative"""
    st.info("🔬 Analyse approfondie à implémenter")
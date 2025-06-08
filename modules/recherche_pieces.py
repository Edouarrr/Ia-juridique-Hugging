"""Module de gestion des pièces et bordereaux"""

import streamlit as st
from datetime import datetime
from collections import defaultdict
from models.dataclasses import PieceSelectionnee
from utils.helpers import clean_key

def process_piece_selection_request(query: str, analysis: dict):
    """Traite une demande de sélection de pièces"""
    
    st.markdown("### 📋 Sélection de pièces")
    
    # Collecter les documents disponibles
    available_docs = collect_available_documents(analysis)
    
    if not available_docs:
        st.warning("⚠️ Aucun document disponible")
        return
    
    # Grouper par catégorie
    categories = group_documents_by_category(available_docs)
    
    # Interface de sélection
    selected_pieces = []
    
    for category, docs in categories.items():
        with st.expander(f"📁 {category} ({len(docs)} documents)", expanded=True):
            select_all = st.checkbox(f"Tout sélectionner - {category}", key=f"select_all_{category}")
            
            for doc in docs:
                is_selected = st.checkbox(
                    f"📄 {doc['title']}",
                    value=select_all,
                    key=f"select_doc_{doc['id']}",
                    help=f"Source: {doc.get('source', 'N/A')}"
                )
                
                if is_selected:
                    selected_pieces.append(PieceSelectionnee(
                        numero=len(selected_pieces) + 1,
                        titre=doc['title'],
                        description=doc.get('description', ''),
                        categorie=category,
                        date=doc.get('date'),
                        source=doc.get('source', ''),
                        pertinence=calculate_piece_relevance(doc, analysis)
                    ))
    
    # Sauvegarder la sélection
    st.session_state.selected_pieces = selected_pieces
    
    # Actions
    if selected_pieces:
        st.success(f"✅ {len(selected_pieces)} pièces sélectionnées")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Créer bordereau", key="create_bordereau_from_selection"):
                process_bordereau_request(query, analysis)
        
        with col2:
            if st.button("📄 Synthétiser", key="synthesize_selection"):
                synthesize_selected_pieces(selected_pieces)
        
        with col3:
            if st.button("📤 Exporter liste", key="export_piece_list"):
                export_piece_list(selected_pieces)

def process_bordereau_request(query: str, analysis: dict):
    """Traite une demande de création de bordereau"""
    
    pieces = st.session_state.get('selected_pieces', [])
    
    if not pieces:
        st.warning("⚠️ Aucune pièce sélectionnée pour le bordereau")
        return
    
    # Créer le bordereau
    bordereau = create_bordereau(pieces, analysis)
    
    # Afficher
    st.markdown("### 📊 Bordereau de communication de pièces")
    
    # En-tête
    st.text_area(
        "En-tête du bordereau",
        value=bordereau['header'],
        height=150,
        key="bordereau_header"
    )
    
    # Table des pièces
    try:
        import pandas as pd
        df = pd.DataFrame([
            {
                'N°': p.numero,
                'Titre': p.titre,
                'Description': p.description,
                'Catégorie': p.categorie,
                'Date': p.date.strftime('%d/%m/%Y') if p.date else 'N/A'
            }
            for p in pieces
        ])
        
        st.dataframe(df, use_container_width=True)
    except ImportError:
        # Affichage sans pandas
        for piece in pieces:
            st.write(f"**{piece.numero}.** {piece.titre}")
            if piece.description:
                st.caption(piece.description)
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "💾 Télécharger bordereau",
            create_bordereau_document(bordereau),
            f"bordereau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    with col2:
        if st.button("📧 Envoyer bordereau", key="send_bordereau"):
            st.session_state.pending_email = {
                'content': create_bordereau_document(bordereau),
                'type': 'bordereau'
            }

def process_synthesis_request(query: str, analysis: dict):
    """Traite une demande de synthèse"""
    
    # Déterminer la source
    if st.session_state.get('selected_pieces'):
        content_to_synthesize = synthesize_selected_pieces(st.session_state.selected_pieces)
    elif analysis.get('reference'):
        docs = search_by_reference(f"@{analysis['reference']}")
        content_to_synthesize = synthesize_documents(docs)
    else:
        st.warning("⚠️ Aucun contenu à synthétiser")
        return
    
    # Stocker le résultat
    st.session_state.synthesis_result = content_to_synthesize

def synthesize_selected_pieces(pieces: list) -> dict:
    """Synthétise les pièces sélectionnées"""
    
    try:
        from managers.multi_llm_manager import MultiLLMManager
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            return {'error': 'Aucune IA disponible'}
        
        # Construire le contexte
        context = "PIÈCES À SYNTHÉTISER:\n\n"
        
        for piece in pieces[:20]:  # Limiter
            context += f"Pièce {piece.numero}: {piece.titre}\n"
            context += f"Catégorie: {piece.categorie}\n"
            if piece.description:
                context += f"Description: {piece.description}\n"
            context += "\n"
        
        # Prompt
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
            return {
                'content': response['response'],
                'piece_count': len(pieces),
                'categories': list(set(p.categorie for p in pieces)),
                'timestamp': datetime.now()
            }
        else:
            return {'error': 'Échec de la synthèse'}
            
    except Exception as e:
        return {'error': f'Erreur synthèse: {str(e)}'}

def collect_available_documents(analysis: dict) -> list:
    """Collecte tous les documents disponibles"""
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
    
    return documents

def group_documents_by_category(documents: list) -> dict:
    """Groupe les documents par catégorie"""
    categories = defaultdict(list)
    
    for doc in documents:
        category = determine_document_category(doc)
        categories[category].append(doc)
    
    return dict(categories)

def determine_document_category(doc: dict) -> str:
    """Détermine la catégorie d'un document"""
    title_lower = doc.get('title', '').lower()
    content_lower = doc.get('content', '')[:500].lower()
    
    category_patterns = {
        'Procédure': ['plainte', 'procès-verbal', 'audition'],
        'Expertise': ['expertise', 'expert', 'rapport technique'],
        'Comptabilité': ['bilan', 'compte', 'facture'],
        'Contrats': ['contrat', 'convention', 'accord'],
        'Correspondance': ['courrier', 'email', 'lettre']
    }
    
    for category, keywords in category_patterns.items():
        if any(kw in title_lower or kw in content_lower for kw in keywords):
            return category
    
    return 'Autres'

def calculate_piece_relevance(doc: dict, analysis: dict) -> float:
    """Calcule la pertinence d'une pièce"""
    score = 0.5
    
    if analysis.get('subject_matter'):
        if analysis['subject_matter'] in doc.get('content', '').lower():
            score += 0.3
    
    if analysis.get('reference'):
        if analysis['reference'] in doc.get('title', '').lower():
            score += 0.2
    
    return min(score, 1.0)

def create_bordereau(pieces: list, analysis: dict) -> dict:
    """Crée un bordereau structuré"""
    
    bordereau = {
        'header': f"""BORDEREAU DE COMMUNICATION DE PIÈCES
AFFAIRE : {analysis.get('reference', 'N/A').upper()}
DATE : {datetime.now().strftime('%d/%m/%Y')}
NOMBRE DE PIÈCES : {len(pieces)}""",
        'pieces': pieces,
        'footer': f"""Je certifie que les pièces communiquées sont conformes aux originaux.
Fait le {datetime.now().strftime('%d/%m/%Y')}""",
        'metadata': {
            'created_at': datetime.now(),
            'piece_count': len(pieces),
            'reference': analysis.get('reference')
        }
    }
    
    return bordereau

def create_bordereau_document(bordereau: dict) -> bytes:
    """Crée le document du bordereau"""
    content = bordereau['header'] + '\n\n'
    
    for piece in bordereau['pieces']:
        content += f"{piece.numero}. {piece.titre}\n"
        if piece.description:
            content += f"   {piece.description}\n"
        content += f"   Catégorie: {piece.categorie}\n"
        if piece.date:
            content += f"   Date: {piece.date.strftime('%d/%m/%Y')}\n"
        content += "\n"
    
    content += bordereau['footer']
    
    return content.encode('utf-8')

def export_piece_list(pieces: list):
    """Exporte la liste des pièces"""
    content = "LISTE DES PIÈCES SÉLECTIONNÉES\n"
    content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    content += f"Nombre de pièces : {len(pieces)}\n\n"
    
    # Grouper par catégorie
    by_category = defaultdict(list)
    for piece in pieces:
        by_category[piece.categorie].append(piece)
    
    for category, cat_pieces in by_category.items():
        content += f"\n{category.upper()} ({len(cat_pieces)} pièces)\n"
        content += "-" * 50 + "\n"
        
        for piece in cat_pieces:
            content += f"{piece.numero}. {piece.titre}\n"
            if piece.description:
                content += f"   {piece.description}\n"
            content += "\n"
    
    # Télécharger
    st.download_button(
        "💾 Télécharger la liste",
        content.encode('utf-8'),
        f"liste_pieces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain"
    )

def search_by_reference(reference: str) -> list:
    """Recherche par référence @"""
    results = []
    ref_clean = reference.replace('@', '').strip().lower()
    
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if ref_clean in doc.title.lower() or ref_clean in doc.source.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source
            })
    
    return results

def synthesize_documents(documents: list) -> dict:
    """Synthétise une liste de documents"""
    pieces = []
    
    for i, doc in enumerate(documents):
        pieces.append(PieceSelectionnee(
            numero=i + 1,
            titre=doc.get('title', 'Sans titre'),
            description=doc.get('content', '')[:200] + '...' if doc.get('content') else '',
            categorie=determine_document_category(doc),
            source=doc.get('source', '')
        ))
    
    return synthesize_selected_pieces(pieces)
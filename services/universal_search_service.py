# Ajouts à intégrer dans services/universal_search_service.py

# Ajouter ces imports en haut du fichier
from services.company_info_service import get_company_info_service
from services.style_learning_service import StyleLearningService
from models.dataclasses import (
    PhaseProcedure, StatutProcedural, create_partie_from_name_with_lookup,
    format_partie_designation_by_phase, PieceSelectionnee, format_piece_with_source_and_footnote
)

# Ajouter cette méthode à la classe UniversalSearchService

async def enrich_parties_with_company_info(self, parties: List[Partie]) -> List[Partie]:
    """Enrichit les informations des parties avec les données entreprises"""
    company_service = get_company_info_service()
    
    for partie in parties:
        if partie.type_personne == "morale" and not partie.info_entreprise:
            try:
                # Rechercher les informations de l'entreprise
                info = await company_service.get_company_info(partie.nom)
                if info:
                    partie.update_from_entreprise_info(info)
                    st.success(f"✓ Informations trouvées pour {partie.nom}")
                else:
                    st.warning(f"⚠️ Aucune information trouvée pour {partie.nom}")
            except Exception as e:
                st.error(f"Erreur lors de la recherche pour {partie.nom}: {e}")
    
    return parties

async def create_parties_from_query_with_enrichment(self, query_analysis: QueryAnalysis, 
                                                   phase: PhaseProcedure = PhaseProcedure.ENQUETE_PRELIMINAIRE) -> Dict[str, List[Partie]]:
    """Crée les parties depuis l'analyse de requête avec enrichissement automatique"""
    parties_dict = extract_parties_from_query(query_analysis.original_query)
    
    all_parties = {
        'demandeurs': [],
        'defendeurs': []
    }
    
    # Créer les parties demanderesses
    for nom in parties_dict.get('demandeurs', []):
        partie = create_partie_from_name_with_lookup(
            nom=nom,
            type_partie=TypePartie.DEMANDEUR,
            is_personne_morale=True,
            phase=phase,
            fetch_entreprise_info=False  # On le fera après
        )
        all_parties['demandeurs'].append(partie)
    
    # Créer les parties défenderesses
    for nom in parties_dict.get('defendeurs', []):
        # Déterminer le type selon la phase
        if phase in [PhaseProcedure.ENQUETE_PRELIMINAIRE, PhaseProcedure.ENQUETE_FLAGRANCE]:
            type_partie = TypePartie.MIS_EN_CAUSE
        else:
            type_partie = TypePartie.DEFENDEUR
        
        partie = create_partie_from_name_with_lookup(
            nom=nom,
            type_partie=type_partie,
            is_personne_morale=not nom.startswith(('M.', 'Mme')),
            phase=phase,
            fetch_entreprise_info=False
        )
        all_parties['defendeurs'].append(partie)
    
    # Enrichir avec les informations entreprises
    with st.spinner("Recherche des informations légales des entreprises..."):
        for key in all_parties:
            all_parties[key] = await self.enrich_parties_with_company_info(all_parties[key])
    
    return all_parties

def format_pieces_with_links_and_footnotes(self, pieces: List[PieceSelectionnee], 
                                         source_tracker: Optional[SourceTracker] = None) -> str:
    """Formate les pièces avec liens sources et footnotes"""
    formatted_pieces = []
    footnotes = []
    
    for piece in pieces:
        # Enrichir la pièce si possible
        if source_tracker:
            # Chercher le document source
            source_docs = source_tracker.find_documents_by_reference(piece.source)
            if source_docs:
                piece = format_piece_with_source_and_footnote(piece, source_docs[0])
        
        # Ajouter la référence formatée
        formatted_pieces.append(piece.get_formatted_reference())
        
        # Collecter la footnote
        footnotes.append(piece.get_footnote())
    
    # Assembler le tout
    content = "\n".join(formatted_pieces)
    if footnotes:
        content += "\n\n---\n\n" + "\n".join(footnotes)
    
    return content

def adapt_terminology_by_phase(self, text: str, phase: PhaseProcedure) -> str:
    """Adapte la terminologie selon la phase procédurale"""
    replacements = {
        PhaseProcedure.ENQUETE_PRELIMINAIRE: {
            'mis en examen': 'mis en cause',
            'prévenu': 'suspect',
            'témoin assisté': 'témoin',
            'le prévenu': 'le mis en cause',
            'les prévenus': 'les mis en cause'
        },
        PhaseProcedure.INSTRUCTION: {
            'prévenu': 'mis en examen',
            'suspect': 'mis en examen',
            'mis en cause': 'mis en examen',
            'le prévenu': 'le mis en examen',
            'les prévenus': 'les mis en examen'
        },
        PhaseProcedure.JUGEMENT: {
            'mis en examen': 'prévenu',
            'mis en cause': 'prévenu',
            'suspect': 'prévenu',
            'le mis en examen': 'le prévenu',
            'les mis en examen': 'les prévenus'
        }
    }
    
    if phase in replacements:
        for old_term, new_term in replacements[phase].items():
            text = text.replace(old_term, new_term)
            # Aussi avec majuscule
            text = text.replace(old_term.capitalize(), new_term.capitalize())
    
    return text

async def apply_learned_style_to_document(self, document: str, style_name: str) -> str:
    """Applique un style appris à un document"""
    style_service = StyleLearningService()
    
    # Récupérer le style appris
    if style_name in style_service.learned_styles:
        style = style_service.learned_styles[style_name]
        return style_service.apply_style_to_text(document, style)
    else:
        st.warning(f"Style '{style_name}' non trouvé")
        return document

# Modifier la méthode process_query existante pour intégrer ces fonctionnalités
async def process_query_enhanced(self, query: str, documents: List[Document]) -> Dict[str, Any]:
    """Version améliorée du traitement de requête avec toutes les nouvelles fonctionnalités"""
    
    # Analyse de base
    query_analysis = QueryAnalysis(original_query=query)
    
    # Détecter la phase procédurale
    phase = self._detect_procedural_phase(query)
    
    # Résultats de base
    results = await self.process_query(query, documents)
    
    # Enrichissement des parties si c'est une demande de rédaction
    if query_analysis.is_redaction_request():
        # Créer et enrichir les parties
        parties = await self.create_parties_from_query_with_enrichment(query_analysis, phase)
        results['parties_enrichies'] = parties
        results['phase_procedurale'] = phase
        
        # Si c'est une plainte, adapter la terminologie
        if 'plainte' in query.lower():
            if 'document' in results:
                results['document'] = self.adapt_terminology_by_phase(
                    results['document'], 
                    phase
                )
    
    # Si des pièces sont mentionnées, les formater avec liens
    if 'pieces' in results:
        results['pieces_formatees'] = self.format_pieces_with_links_and_footnotes(
            results['pieces'],
            self.source_tracker if hasattr(self, 'source_tracker') else None
        )
    
    return results

def _detect_procedural_phase(self, query: str) -> PhaseProcedure:
    """Détecte la phase procédurale depuis la requête"""
    query_lower = query.lower()
    
    if any(term in query_lower for term in ['enquête', 'plainte', 'signalement']):
        return PhaseProcedure.ENQUETE_PRELIMINAIRE
    elif any(term in query_lower for term in ['instruction', 'juge d\'instruction', 'mis en examen']):
        return PhaseProcedure.INSTRUCTION
    elif any(term in query_lower for term in ['audience', 'tribunal', 'jugement', 'plaidoirie']):
        return PhaseProcedure.JUGEMENT
    elif any(term in query_lower for term in ['appel', 'cour d\'appel']):
        return PhaseProcedure.APPEL
    else:
        return PhaseProcedure.ENQUETE_PRELIMINAIRE  # Par défaut
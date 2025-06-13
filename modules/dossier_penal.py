"""
Module de gestion des dossiers pénaux
"""

import streamlit as st
from datetime import datetime
import json
from typing import Dict, List, Optional
import uuid

# Import des modèles avec gestion d'erreur
try:
    from modules.dataclasses import DossierPenal, PieceProcedure, EvenementTimeline
except ImportError:
    # Définitions de secours si l'import échoue
    from dataclasses import dataclass, field
    from typing import Dict, List, Optional
    from datetime import datetime
    
    @dataclass
    class DossierPenal:
        id: str
        numero_dossier: str
        titre: str
        date_ouverture: datetime
        date_cloture: Optional[datetime] = None
        juridiction: str
        juge_instruction: Optional[str] = None
        procureur: Optional[str] = None
        parties: Dict[str, List[str]] = field(default_factory=dict)
        faits: Optional[str] = None
        qualification_juridique: List[str] = field(default_factory=list)
        pieces: List[str] = field(default_factory=list)
        evenements: List[str] = field(default_factory=list)
        statut: str = "en_cours"

class DossierPenalManager:
    """Gestionnaire des dossiers pénaux"""
    
    def __init__(self):
        """Initialise le gestionnaire"""
        if 'dossiers_penaux' not in st.session_state:
            st.session_state.dossiers_penaux = {}
        if 'current_dossier_id' not in st.session_state:
            st.session_state.current_dossier_id = None
    
    def create_dossier(self, numero: str, titre: str, juridiction: str) -> DossierPenal:
        """Crée un nouveau dossier pénal"""
        dossier_id = str(uuid.uuid4())
        dossier = DossierPenal(
            id=dossier_id,
            numero_dossier=numero,
            titre=titre,
            date_ouverture=datetime.now(),
            juridiction=juridiction,
            parties={"demandeurs": [], "defendeurs": []},
            statut="en_cours"
        )
        
        st.session_state.dossiers_penaux[dossier_id] = dossier
        return dossier
    
    def get_dossier(self, dossier_id: str) -> Optional[DossierPenal]:
        """Récupère un dossier par son ID"""
        return st.session_state.dossiers_penaux.get(dossier_id)
    
    def update_dossier(self, dossier_id: str, **kwargs):
        """Met à jour un dossier"""
        if dossier_id in st.session_state.dossiers_penaux:
            dossier = st.session_state.dossiers_penaux[dossier_id]
            for key, value in kwargs.items():
                if hasattr(dossier, key):
                    setattr(dossier, key, value)
    
    def list_dossiers(self) -> List[DossierPenal]:
        """Liste tous les dossiers"""
        return list(st.session_state.dossiers_penaux.values())
    
    def delete_dossier(self, dossier_id: str):
        """Supprime un dossier"""
        if dossier_id in st.session_state.dossiers_penaux:
            del st.session_state.dossiers_penaux[dossier_id]
            if st.session_state.current_dossier_id == dossier_id:
                st.session_state.current_dossier_id = None

def display_dossier_penal_interface():
    """Interface principale de gestion des dossiers pénaux"""
    st.title("📁 Gestion des Dossiers Pénaux")
    
    manager = DossierPenalManager()
    
    # Sidebar pour la navigation
    with st.sidebar:
        st.subheader("Navigation")
        
        # Bouton nouveau dossier
        if st.button("➕ Nouveau dossier", use_container_width=True):
            st.session_state.show_new_dossier = True
        
        # Liste des dossiers existants
        st.markdown("### Dossiers existants")
        dossiers = manager.list_dossiers()
        
        if dossiers:
            for dossier in sorted(dossiers, key=lambda d: d.date_ouverture, reverse=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        f"📋 {dossier.numero_dossier}",
                        key=f"select_{dossier.id}",
                        use_container_width=True
                    ):
                        st.session_state.current_dossier_id = dossier.id
                        st.session_state.show_new_dossier = False
                with col2:
                    if dossier.statut == "en_cours":
                        st.success("🟢", help="En cours")
                    elif dossier.statut == "clos":
                        st.info("🔵", help="Clos")
                    else:
                        st.warning("🟡", help=dossier.statut)
        else:
            st.info("Aucun dossier créé")
    
    # Zone principale
    if getattr(st.session_state, 'show_new_dossier', False):
        display_new_dossier_form(manager)
    elif st.session_state.current_dossier_id:
        display_dossier_detail(manager, st.session_state.current_dossier_id)
    else:
        display_dashboard(manager)

def display_new_dossier_form(manager: DossierPenalManager):
    """Formulaire de création d'un nouveau dossier"""
    st.subheader("📝 Nouveau dossier pénal")
    
    with st.form("new_dossier_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            numero = st.text_input("Numéro de dossier*", placeholder="2024/001")
            juridiction = st.text_input("Juridiction*", placeholder="TGI Paris")
            juge = st.text_input("Juge d'instruction", placeholder="M. Dupont")
        
        with col2:
            titre = st.text_input("Titre du dossier*", placeholder="Affaire X c/ Y")
            procureur = st.text_input("Procureur", placeholder="Mme Martin")
            date_ouverture = st.date_input("Date d'ouverture", value=datetime.now())
        
        faits = st.text_area("Résumé des faits", height=100)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            submitted = st.form_submit_button("✅ Créer le dossier", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Annuler", use_container_width=True)
        
        if submitted and numero and titre and juridiction:
            dossier = manager.create_dossier(numero, titre, juridiction)
            dossier.juge_instruction = juge
            dossier.procureur = procureur
            dossier.faits = faits
            dossier.date_ouverture = datetime.combine(date_ouverture, datetime.min.time())
            
            st.success(f"✅ Dossier {numero} créé avec succès!")
            st.session_state.current_dossier_id = dossier.id
            st.session_state.show_new_dossier = False
            st.rerun()
        
        if cancel:
            st.session_state.show_new_dossier = False
            st.rerun()

def display_dossier_detail(manager: DossierPenalManager, dossier_id: str):
    """Affiche le détail d'un dossier"""
    dossier = manager.get_dossier(dossier_id)
    
    if not dossier:
        st.error("Dossier introuvable")
        return
    
    # En-tête du dossier
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title(f"📁 {dossier.numero_dossier} - {dossier.titre}")
    with col2:
        if st.button("✏️ Modifier", use_container_width=True):
            st.session_state.edit_mode = True
    with col3:
        if st.button("🗑️ Supprimer", use_container_width=True):
            st.session_state.confirm_delete = dossier_id
    
    # Confirmation de suppression
    if getattr(st.session_state, 'confirm_delete', None) == dossier_id:
        st.warning("⚠️ Êtes-vous sûr de vouloir supprimer ce dossier ?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmer la suppression"):
                manager.delete_dossier(dossier_id)
                st.success("Dossier supprimé")
                st.session_state.current_dossier_id = None
                st.session_state.confirm_delete = None
                st.rerun()
        with col2:
            if st.button("❌ Annuler"):
                st.session_state.confirm_delete = None
                st.rerun()
    
    # Onglets
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Informations générales",
        "👥 Parties",
        "📎 Pièces",
        "📅 Chronologie",
        "📊 Analyse"
    ])
    
    with tab1:
        display_general_info(dossier, manager)
    
    with tab2:
        display_parties(dossier, manager)
    
    with tab3:
        display_pieces(dossier, manager)
    
    with tab4:
        display_chronologie(dossier, manager)
    
    with tab5:
        display_analyse(dossier, manager)

def display_general_info(dossier: DossierPenal, manager: DossierPenalManager):
    """Affiche les informations générales du dossier"""
    if getattr(st.session_state, 'edit_mode', False):
        # Mode édition
        with st.form("edit_general_info"):
            col1, col2 = st.columns(2)
            
            with col1:
                juridiction = st.text_input("Juridiction", value=dossier.juridiction)
                juge = st.text_input("Juge d'instruction", value=dossier.juge_instruction or "")
                statut = st.selectbox(
                    "Statut",
                    ["en_cours", "clos", "suspendu", "archive"],
                    index=["en_cours", "clos", "suspendu", "archive"].index(dossier.statut)
                )
            
            with col2:
                procureur = st.text_input("Procureur", value=dossier.procureur or "")
                date_cloture = st.date_input(
                    "Date de clôture",
                    value=dossier.date_cloture.date() if dossier.date_cloture else None
                )
            
            faits = st.text_area("Résumé des faits", value=dossier.faits or "", height=150)
            
            # Qualifications juridiques
            st.subheader("Qualifications juridiques")
            qualifications = st.text_area(
                "Une qualification par ligne",
                value="\n".join(dossier.qualification_juridique),
                height=100
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                    manager.update_dossier(
                        dossier.id,
                        juridiction=juridiction,
                        juge_instruction=juge,
                        procureur=procureur,
                        statut=statut,
                        faits=faits,
                        date_cloture=datetime.combine(date_cloture, datetime.min.time()) if date_cloture else None,
                        qualification_juridique=[q.strip() for q in qualifications.split("\n") if q.strip()]
                    )
                    st.success("✅ Modifications enregistrées")
                    st.session_state.edit_mode = False
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Annuler", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
    else:
        # Mode lecture
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Juridiction :** {dossier.juridiction}")
            st.markdown(f"**Juge d'instruction :** {dossier.juge_instruction or 'Non désigné'}")
            st.markdown(f"**Date d'ouverture :** {dossier.date_ouverture.strftime('%d/%m/%Y')}")
        
        with col2:
            st.markdown(f"**Procureur :** {dossier.procureur or 'Non désigné'}")
            st.markdown(f"**Statut :** {dossier.statut}")
            if dossier.date_cloture:
                st.markdown(f"**Date de clôture :** {dossier.date_cloture.strftime('%d/%m/%Y')}")
        
        if dossier.faits:
            st.markdown("### Résumé des faits")
            st.info(dossier.faits)
        
        if dossier.qualification_juridique:
            st.markdown("### Qualifications juridiques")
            for qual in dossier.qualification_juridique:
                st.markdown(f"- {qual}")

def display_parties(dossier: DossierPenal, manager: DossierPenalManager):
    """Affiche et gère les parties du dossier"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Demandeurs")
        
        # Formulaire d'ajout
        with st.expander("➕ Ajouter un demandeur"):
            nom = st.text_input("Nom", key="new_demandeur")
            if st.button("Ajouter", key="add_demandeur"):
                if nom:
                    if "demandeurs" not in dossier.parties:
                        dossier.parties["demandeurs"] = []
                    dossier.parties["demandeurs"].append(nom)
                    manager.update_dossier(dossier.id, parties=dossier.parties)
                    st.success(f"✅ {nom} ajouté")
                    st.rerun()
        
        # Liste des demandeurs
        if dossier.parties.get("demandeurs"):
            for i, partie in enumerate(dossier.parties["demandeurs"]):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"• {partie}")
                with col_b:
                    if st.button("🗑️", key=f"del_dem_{i}"):
                        dossier.parties["demandeurs"].pop(i)
                        manager.update_dossier(dossier.id, parties=dossier.parties)
                        st.rerun()
        else:
            st.info("Aucun demandeur")
    
    with col2:
        st.subheader("⚖️ Défendeurs")
        
        # Formulaire d'ajout
        with st.expander("➕ Ajouter un défendeur"):
            nom = st.text_input("Nom", key="new_defendeur")
            if st.button("Ajouter", key="add_defendeur"):
                if nom:
                    if "defendeurs" not in dossier.parties:
                        dossier.parties["defendeurs"] = []
                    dossier.parties["defendeurs"].append(nom)
                    manager.update_dossier(dossier.id, parties=dossier.parties)
                    st.success(f"✅ {nom} ajouté")
                    st.rerun()
        
        # Liste des défendeurs
        if dossier.parties.get("defendeurs"):
            for i, partie in enumerate(dossier.parties["defendeurs"]):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"• {partie}")
                with col_b:
                    if st.button("🗑️", key=f"del_def_{i}"):
                        dossier.parties["defendeurs"].pop(i)
                        manager.update_dossier(dossier.id, parties=dossier.parties)
                        st.rerun()
        else:
            st.info("Aucun défendeur")

def display_pieces(dossier: DossierPenal, manager: DossierPenalManager):
    """Affiche et gère les pièces du dossier"""
    st.subheader("📎 Pièces du dossier")
    
    # Interface d'ajout de pièces
    with st.expander("➕ Ajouter une pièce"):
        col1, col2 = st.columns(2)
        with col1:
            nom_piece = st.text_input("Nom de la pièce")
            type_piece = st.selectbox(
                "Type de pièce",
                ["Procès-verbal", "Rapport d'expertise", "Témoignage", "Document", "Photo", "Vidéo", "Audio", "Autre"]
            )
        with col2:
            numero_ordre = st.number_input("Numéro d'ordre", min_value=1, value=len(dossier.pieces) + 1)
            description = st.text_area("Description", height=100)
        
        if st.button("➕ Ajouter la pièce", use_container_width=True):
            if nom_piece:
                # Simuler l'ajout d'une pièce (ID fictif)
                piece_id = f"piece_{uuid.uuid4().hex[:8]}"
                dossier.pieces.append(piece_id)
                manager.update_dossier(dossier.id, pieces=dossier.pieces)
                st.success(f"✅ Pièce '{nom_piece}' ajoutée")
                st.rerun()
    
    # Liste des pièces
    if dossier.pieces:
        st.markdown("### Liste des pièces")
        for i, piece_id in enumerate(dossier.pieces):
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                st.write(f"#{i+1}")
            with col2:
                st.write(f"Pièce {piece_id}")
            with col3:
                if st.button("🗑️", key=f"del_piece_{i}"):
                    dossier.pieces.pop(i)
                    manager.update_dossier(dossier.id, pieces=dossier.pieces)
                    st.rerun()
    else:
        st.info("Aucune pièce dans ce dossier")

def display_chronologie(dossier: DossierPenal, manager: DossierPenalManager):
    """Affiche la chronologie du dossier"""
    st.subheader("📅 Chronologie des événements")
    
    # Interface d'ajout d'événements
    with st.expander("➕ Ajouter un événement"):
        col1, col2 = st.columns(2)
        with col1:
            titre_event = st.text_input("Titre de l'événement")
            date_event = st.date_input("Date", value=datetime.now())
            type_event = st.selectbox(
                "Type d'événement",
                ["Audience", "Dépôt de pièce", "Expertise", "Audition", "Décision", "Autre"]
            )
        with col2:
            importance = st.selectbox("Importance", ["normale", "importante", "critique"])
            description_event = st.text_area("Description", height=100)
        
        if st.button("➕ Ajouter l'événement", use_container_width=True):
            if titre_event:
                # Simuler l'ajout d'un événement
                event_id = f"event_{uuid.uuid4().hex[:8]}"
                dossier.evenements.append(event_id)
                manager.update_dossier(dossier.id, evenements=dossier.evenements)
                st.success(f"✅ Événement '{titre_event}' ajouté")
                st.rerun()
    
    # Affichage de la timeline
    if dossier.evenements:
        st.markdown("### Timeline")
        # Créer une timeline simple
        for i, event_id in enumerate(dossier.evenements):
            col1, col2 = st.columns([1, 5])
            with col1:
                st.write(f"📍 {datetime.now().strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**Événement** : {event_id}")
                if st.button("🗑️", key=f"del_event_{i}"):
                    dossier.evenements.pop(i)
                    manager.update_dossier(dossier.id, evenements=dossier.evenements)
                    st.rerun()
    else:
        st.info("Aucun événement enregistré")

def display_analyse(dossier: DossierPenal, manager: DossierPenalManager):
    """Affiche l'analyse du dossier"""
    st.subheader("📊 Analyse du dossier")
    
    # Statistiques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nombre de pièces", len(dossier.pieces))
    with col2:
        st.metric("Événements", len(dossier.evenements))
    with col3:
        nb_parties = len(dossier.parties.get("demandeurs", [])) + len(dossier.parties.get("defendeurs", []))
        st.metric("Parties", nb_parties)
    with col4:
        duree = (datetime.now() - dossier.date_ouverture).days
        st.metric("Durée (jours)", duree)
    
    # Résumé
    st.markdown("### Résumé du dossier")
    
    # Synthèse automatique
    synthese = f"""
    **Dossier** : {dossier.numero_dossier} - {dossier.titre}
    
    **Juridiction** : {dossier.juridiction}
    
    **Ouvert le** : {dossier.date_ouverture.strftime('%d/%m/%Y')}
    
    **Statut actuel** : {dossier.statut}
    
    **Parties impliquées** :
    - Demandeurs : {', '.join(dossier.parties.get('demandeurs', [])) or 'Aucun'}
    - Défendeurs : {', '.join(dossier.parties.get('defendeurs', [])) or 'Aucun'}
    
    **Qualifications juridiques** :
    {chr(10).join(['- ' + q for q in dossier.qualification_juridique]) if dossier.qualification_juridique else 'Aucune qualification'}
    """
    
    st.info(synthese)
    
    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Générer un rapport", use_container_width=True):
            st.info("Fonction de génération de rapport à implémenter")
    with col2:
        if st.button("📧 Exporter", use_container_width=True):
            st.info("Fonction d'export à implémenter")
    with col3:
        if st.button("🖨️ Imprimer", use_container_width=True):
            st.info("Fonction d'impression à implémenter")

def display_dashboard(manager: DossierPenalManager):
    """Affiche le tableau de bord des dossiers"""
    st.subheader("📊 Tableau de bord")
    
    dossiers = manager.list_dossiers()
    
    if not dossiers:
        st.info("Aucun dossier créé. Cliquez sur '➕ Nouveau dossier' pour commencer.")
        return
    
    # Statistiques globales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total dossiers", len(dossiers))
    with col2:
        en_cours = len([d for d in dossiers if d.statut == "en_cours"])
        st.metric("En cours", en_cours)
    with col3:
        clos = len([d for d in dossiers if d.statut == "clos"])
        st.metric("Clos", clos)
    with col4:
        autres = len([d for d in dossiers if d.statut not in ["en_cours", "clos"]])
        st.metric("Autres", autres)
    
    # Tableau des dossiers
    st.markdown("### Liste des dossiers")
    
    # Créer un tableau simple
    data = []
    for dossier in sorted(dossiers, key=lambda d: d.date_ouverture, reverse=True):
        data.append({
            "Numéro": dossier.numero_dossier,
            "Titre": dossier.titre,
            "Juridiction": dossier.juridiction,
            "Date ouverture": dossier.date_ouverture.strftime('%d/%m/%Y'),
            "Statut": dossier.statut,
            "Nb pièces": len(dossier.pieces)
        })
    
    if data:
        st.dataframe(data, use_container_width=True)
    
    # Graphiques
    st.markdown("### Visualisations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Répartition par statut
        st.markdown("#### Répartition par statut")
        statuts = {}
        for dossier in dossiers:
            statuts[dossier.statut] = statuts.get(dossier.statut, 0) + 1
        
        for statut, count in statuts.items():
            st.write(f"- {statut}: {count} dossiers")
    
    with col2:
        # Répartition par juridiction
        st.markdown("#### Répartition par juridiction")
        juridictions = {}
        for dossier in dossiers:
            juridictions[dossier.juridiction] = juridictions.get(dossier.juridiction, 0) + 1
        
        for juridiction, count in juridictions.items():
            st.write(f"- {juridiction}: {count} dossiers")

# Point d'entrée principal
if __name__ == "__main__":
    display_dossier_penal_interface()
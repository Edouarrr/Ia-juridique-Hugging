"""
Module de gestion des risques juridiques
"""

import streamlit as st
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import uuid
import pandas as pd

# Import des modèles avec gestion d'erreur
try:
    from models.dataclasses import Risque, RiskLevel
except ImportError:
    # Définitions de secours si l'import échoue
    from dataclasses import dataclass, field
    from typing import Dict, List, Optional, Any
    from datetime import datetime
    from enum import Enum
    
    class RiskLevel(Enum):
        FAIBLE = "faible"
        MOYEN = "moyen"
        ELEVE = "eleve"
        CRITIQUE = "critique"
    
    @dataclass
    class Risque:
        id: str
        titre: str
        description: str
        niveau: RiskLevel
        probabilite: float
        impact: float
        date_identification: datetime = field(default_factory=datetime.now)
        date_echeance: Optional[datetime] = None
        mesures_mitigation: List[str] = field(default_factory=list)
        responsable: Optional[str] = None
        statut: str = "actif"
        
        @property
        def score_risque(self) -> float:
            return self.probabilite * self.impact

class RisqueManager:
    """Gestionnaire des risques juridiques"""
    
    # Catégories de risques prédéfinies
    CATEGORIES_RISQUES = [
        "Contentieux",
        "Réglementaire",
        "Contractuel",
        "Fiscal",
        "Pénal",
        "Social",
        "Propriété intellectuelle",
        "Données personnelles",
        "Environnemental",
        "Réputation",
        "Autre"
    ]
    
    # Statuts possibles
    STATUTS_RISQUES = [
        "actif",
        "en_cours_traitement",
        "mitige",
        "accepte",
        "transfere",
        "clos"
    ]
    
    def __init__(self):
        """Initialise le gestionnaire"""
        if 'risques' not in st.session_state:
            st.session_state.risques = {}
        if 'risques_historique' not in st.session_state:
            st.session_state.risques_historique = []
    
    def create_risque(self, titre: str, description: str, niveau: str, 
                     probabilite: float, impact: float, **kwargs) -> Risque:
        """Crée un nouveau risque"""
        risque = Risque(
            id=str(uuid.uuid4()),
            titre=titre,
            description=description,
            niveau=RiskLevel(niveau),
            probabilite=probabilite,
            impact=impact,
            **kwargs
        )
        
        st.session_state.risques[risque.id] = risque
        self._add_to_history("creation", risque.id, {"titre": titre})
        return risque
    
    def get_risque(self, risque_id: str) -> Optional[Risque]:
        """Récupère un risque par son ID"""
        return st.session_state.risques.get(risque_id)
    
    def update_risque(self, risque_id: str, **kwargs):
        """Met à jour un risque"""
        if risque_id in st.session_state.risques:
            risque = st.session_state.risques[risque_id]
            
            # Sauvegarder l'état précédent pour l'historique
            old_state = {
                'niveau': risque.niveau.value,
                'statut': risque.statut,
                'score': risque.score_risque
            }
            
            for key, value in kwargs.items():
                if hasattr(risque, key):
                    if key == 'niveau' and isinstance(value, str):
                        value = RiskLevel(value)
                    setattr(risque, key, value)
            
            # Enregistrer dans l'historique
            self._add_to_history("modification", risque_id, {
                'old_state': old_state,
                'new_state': {
                    'niveau': risque.niveau.value,
                    'statut': risque.statut,
                    'score': risque.score_risque
                }
            })
    
    def delete_risque(self, risque_id: str):
        """Supprime un risque"""
        if risque_id in st.session_state.risques:
            risque = st.session_state.risques[risque_id]
            self._add_to_history("suppression", risque_id, {"titre": risque.titre})
            del st.session_state.risques[risque_id]
    
    def list_risques(self, filters: Dict[str, Any] = None) -> List[Risque]:
        """Liste les risques avec filtres optionnels"""
        risques = list(st.session_state.risques.values())
        
        if filters:
            if filters.get('statut'):
                risques = [r for r in risques if r.statut == filters['statut']]
            if filters.get('niveau'):
                risques = [r for r in risques if r.niveau.value == filters['niveau']]
            if filters.get('responsable'):
                risques = [r for r in risques if r.responsable == filters['responsable']]
            if filters.get('score_min') is not None:
                risques = [r for r in risques if r.score_risque >= filters['score_min']]
        
        return risques
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calcule les statistiques sur les risques"""
        risques = list(st.session_state.risques.values())
        
        if not risques:
            return {
                'total': 0,
                'par_niveau': {},
                'par_statut': {},
                'score_moyen': 0,
                'risques_critiques': []
            }
        
        # Statistiques de base
        par_niveau = {}
        par_statut = {}
        scores = []
        
        for risque in risques:
            # Par niveau
            niveau = risque.niveau.value
            par_niveau[niveau] = par_niveau.get(niveau, 0) + 1
            
            # Par statut
            par_statut[risque.statut] = par_statut.get(risque.statut, 0) + 1
            
            # Scores
            scores.append(risque.score_risque)
        
        # Risques critiques (score > 0.7 ou niveau critique)
        risques_critiques = [
            r for r in risques 
            if r.niveau == RiskLevel.CRITIQUE or r.score_risque > 0.7
        ]
        
        # Risques imminents (échéance < 30 jours)
        risques_imminents = []
        for r in risques:
            if r.date_echeance and r.statut == "actif":
                jours_restants = (r.date_echeance - datetime.now()).days
                if jours_restants <= 30:
                    risques_imminents.append((r, jours_restants))
        
        return {
            'total': len(risques),
            'par_niveau': par_niveau,
            'par_statut': par_statut,
            'score_moyen': sum(scores) / len(scores),
            'score_max': max(scores) if scores else 0,
            'risques_critiques': risques_critiques,
            'risques_imminents': sorted(risques_imminents, key=lambda x: x[1])
        }
    
    def _add_to_history(self, action: str, risque_id: str, details: Dict[str, Any]):
        """Ajoute une action à l'historique"""
        st.session_state.risques_historique.append({
            'timestamp': datetime.now(),
            'action': action,
            'risque_id': risque_id,
            'details': details,
            'user': st.session_state.get('user_name', 'Utilisateur')
        })
    
    @staticmethod
    def calculate_risk_matrix() -> pd.DataFrame:
        """Calcule la matrice des risques"""
        # Créer une matrice 5x5
        matrix = pd.DataFrame(
            index=['Très faible', 'Faible', 'Moyen', 'Élevé', 'Très élevé'],
            columns=['Très faible', 'Faible', 'Moyen', 'Élevé', 'Très élevé']
        )
        
        # Remplir avec les scores
        for i in range(5):
            for j in range(5):
                matrix.iloc[i, j] = (i + 1) * (j + 1) / 25
        
        return matrix

def display_risques_interface():
    """Interface principale de gestion des risques"""
    st.title("⚠️ Gestion des Risques Juridiques")
    
    manager = RisqueManager()
    
    # Onglets principaux
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Vue d'ensemble",
        "➕ Nouveau risque",
        "📋 Liste des risques",
        "📊 Matrice des risques",
        "📜 Historique"
    ])
    
    with tab1:
        display_dashboard(manager)
    
    with tab2:
        display_new_risque(manager)
    
    with tab3:
        display_risques_list(manager)
    
    with tab4:
        display_risk_matrix(manager)
    
    with tab5:
        display_history(manager)

def display_dashboard(manager: RisqueManager):
    """Tableau de bord des risques"""
    st.subheader("🎯 Vue d'ensemble des risques")
    
    stats = manager.get_statistics()
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total des risques",
            stats['total'],
            delta=None
        )
    with col2:
        st.metric(
            "Score moyen",
            f"{stats['score_moyen']:.2f}",
            delta=None,
            help="Score sur 1.0"
        )
    with col3:
        st.metric(
            "Risques critiques",
            len(stats['risques_critiques']),
            delta=None
        )
    with col4:
        st.metric(
            "Risques imminents",
            len(stats['risques_imminents']),
            delta=None,
            help="Échéance < 30 jours"
        )
    
    # Alertes
    if stats['risques_critiques']:
        st.error(f"⚠️ **{len(stats['risques_critiques'])} risque(s) critique(s) nécessitent une attention immédiate!**")
        
        with st.expander("Voir les risques critiques"):
            for risque in stats['risques_critiques']:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{risque.titre}**")
                    st.caption(risque.description[:100] + "..." if len(risque.description) > 100 else risque.description)
                with col2:
                    st.metric("Score", f"{risque.score_risque:.2f}")
                with col3:
                    if st.button("Gérer", key=f"manage_crit_{risque.id}"):
                        st.session_state.current_risque_id = risque.id
    
    if stats['risques_imminents']:
        st.warning(f"📅 **{len(stats['risques_imminents'])} risque(s) avec échéance proche**")
        
        with st.expander("Voir les risques imminents"):
            for risque, jours in stats['risques_imminents']:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{risque.titre}**")
                with col2:
                    if jours < 0:
                        st.error(f"En retard de {-jours} jours!")
                    elif jours == 0:
                        st.error("Échéance aujourd'hui!")
                    else:
                        st.warning(f"{jours} jours restants")
                with col3:
                    if st.button("Gérer", key=f"manage_imm_{risque.id}"):
                        st.session_state.current_risque_id = risque.id
    
    # Graphiques
    if stats['total'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Répartition par niveau")
            for niveau, count in stats['par_niveau'].items():
                # Couleur selon le niveau
                if niveau == "critique":
                    color = "🔴"
                elif niveau == "eleve":
                    color = "🟠"
                elif niveau == "moyen":
                    color = "🟡"
                else:
                    color = "🟢"
                
                st.write(f"{color} **{niveau.upper()}** : {count} risques")
                st.progress(count / stats['total'])
        
        with col2:
            st.markdown("### 📈 Répartition par statut")
            for statut, count in stats['par_statut'].items():
                st.write(f"**{statut}** : {count} risques")
                st.progress(count / stats['total'])

def display_new_risque(manager: RisqueManager):
    """Formulaire de création d'un nouveau risque"""
    st.subheader("➕ Créer un nouveau risque")
    
    with st.form("new_risque_form"):
        # Informations de base
        st.markdown("### 📋 Informations générales")
        
        col1, col2 = st.columns(2)
        with col1:
            titre = st.text_input("Titre du risque*", placeholder="Ex: Non-conformité RGPD")
            categorie = st.selectbox("Catégorie", manager.CATEGORIES_RISQUES)
            responsable = st.text_input("Responsable", placeholder="Nom du responsable")
        
        with col2:
            niveau = st.selectbox(
                "Niveau de risque*",
                options=[n.value for n in RiskLevel],
                format_func=lambda x: x.upper()
            )
            date_echeance = st.date_input("Date d'échéance", value=None)
        
        description = st.text_area(
            "Description détaillée*",
            placeholder="Décrivez le risque, ses causes et ses conséquences potentielles...",
            height=100
        )
        
        # Évaluation du risque
        st.markdown("### 📊 Évaluation du risque")
        
        col1, col2 = st.columns(2)
        with col1:
            probabilite = st.slider(
                "Probabilité d'occurrence",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="0 = Très improbable, 1 = Certain"
            )
            
            # Aide à l'évaluation
            if probabilite <= 0.2:
                st.caption("Très improbable (< 20%)")
            elif probabilite <= 0.4:
                st.caption("Peu probable (20-40%)")
            elif probabilite <= 0.6:
                st.caption("Possible (40-60%)")
            elif probabilite <= 0.8:
                st.caption("Probable (60-80%)")
            else:
                st.caption("Très probable (> 80%)")
        
        with col2:
            impact = st.slider(
                "Impact potentiel",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="0 = Négligeable, 1 = Catastrophique"
            )
            
            # Aide à l'évaluation
            if impact <= 0.2:
                st.caption("Impact négligeable")
            elif impact <= 0.4:
                st.caption("Impact faible")
            elif impact <= 0.6:
                st.caption("Impact modéré")
            elif impact <= 0.8:
                st.caption("Impact important")
            else:
                st.caption("Impact catastrophique")
        
        # Score de risque calculé
        score = probabilite * impact
        col1, col2, col3 = st.columns(3)
        with col2:
            if score <= 0.25:
                st.success(f"**Score de risque : {score:.2f}** (Faible)")
            elif score <= 0.5:
                st.warning(f"**Score de risque : {score:.2f}** (Moyen)")
            elif score <= 0.75:
                st.error(f"**Score de risque : {score:.2f}** (Élevé)")
            else:
                st.error(f"**Score de risque : {score:.2f}** (Critique)")
        
        # Mesures de mitigation
        st.markdown("### 🛡️ Mesures de mitigation")
        
        mesures = st.text_area(
            "Mesures de mitigation (une par ligne)",
            placeholder="- Mettre en place un audit\n- Former le personnel\n- Réviser les procédures",
            height=100
        )
        
        # Validation
        submitted = st.form_submit_button("✅ Créer le risque", use_container_width=True)
        
        if submitted and titre and description:
            # Créer le risque
            risque = manager.create_risque(
                titre=titre,
                description=description,
                niveau=niveau,
                probabilite=probabilite,
                impact=impact,
                date_echeance=datetime.combine(date_echeance, datetime.min.time()) if date_echeance else None,
                mesures_mitigation=[m.strip() for m in mesures.split('\n') if m.strip()] if mesures else [],
                responsable=responsable if responsable else None
            )
            
            # Ajouter la catégorie dans les métadonnées (si on avait un champ metadata)
            st.success(f"✅ Risque '{titre}' créé avec succès!")
            st.balloons()
            
            # Proposer des actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("➕ Créer un autre risque"):
                    st.rerun()
            with col2:
                if st.button("📋 Voir la liste"):
                    st.session_state.show_list = True
            with col3:
                if st.button("📊 Voir la matrice"):
                    st.session_state.show_matrix = True

def display_risques_list(manager: RisqueManager):
    """Liste des risques avec filtres"""
    st.subheader("📋 Liste des risques")
    
    # Filtres
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filtre_statut = st.selectbox(
            "Statut",
            ["Tous"] + manager.STATUTS_RISQUES
        )
    
    with col2:
        filtre_niveau = st.selectbox(
            "Niveau",
            ["Tous"] + [n.value for n in RiskLevel]
        )
    
    with col3:
        filtre_score = st.slider(
            "Score minimum",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1
        )
    
    with col4:
        tri = st.selectbox(
            "Trier par",
            ["Score (décroissant)", "Date création", "Date échéance", "Nom"]
        )
    
    # Récupérer les risques filtrés
    filters = {}
    if filtre_statut != "Tous":
        filters['statut'] = filtre_statut
    if filtre_niveau != "Tous":
        filters['niveau'] = filtre_niveau
    if filtre_score > 0:
        filters['score_min'] = filtre_score
    
    risques = manager.list_risques(filters)
    
    # Trier
    if tri == "Score (décroissant)":
        risques.sort(key=lambda r: r.score_risque, reverse=True)
    elif tri == "Date création":
        risques.sort(key=lambda r: r.date_identification, reverse=True)
    elif tri == "Date échéance":
        risques.sort(key=lambda r: r.date_echeance or datetime.max)
    else:
        risques.sort(key=lambda r: r.titre.lower())
    
    if not risques:
        st.info("Aucun risque trouvé avec ces critères")
        return
    
    # Affichage
    for risque in risques:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                # Indicateur de niveau
                if risque.niveau == RiskLevel.CRITIQUE:
                    st.markdown(f"🔴 **{risque.titre}**")
                elif risque.niveau == RiskLevel.ELEVE:
                    st.markdown(f"🟠 **{risque.titre}**")
                elif risque.niveau == RiskLevel.MOYEN:
                    st.markdown(f"🟡 **{risque.titre}**")
                else:
                    st.markdown(f"🟢 **{risque.titre}**")
                
                st.caption(risque.description[:150] + "..." if len(risque.description) > 150 else risque.description)
            
            with col2:
                st.metric("Score", f"{risque.score_risque:.2f}")
            
            with col3:
                st.write(f"**Statut**")
                st.caption(risque.statut)
            
            with col4:
                if risque.date_echeance:
                    jours = (risque.date_echeance - datetime.now()).days
                    if jours < 0:
                        st.error(f"En retard!")
                    elif jours <= 7:
                        st.warning(f"{jours}j")
                    else:
                        st.info(f"{jours}j")
                else:
                    st.caption("Pas d'échéance")
            
            with col5:
                if st.button("Gérer", key=f"manage_{risque.id}"):
                    st.session_state.current_risque_id = risque.id
                    st.session_state.show_risque_detail = True
            
            st.divider()
    
    # Détail du risque si sélectionné
    if getattr(st.session_state, 'show_risque_detail', False) and st.session_state.current_risque_id:
        display_risque_detail(manager, st.session_state.current_risque_id)

def display_risque_detail(manager: RisqueManager, risque_id: str):
    """Affiche et permet de gérer un risque spécifique"""
    risque = manager.get_risque(risque_id)
    
    if not risque:
        st.error("Risque introuvable")
        return
    
    # Modal simulée
    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if risque.niveau == RiskLevel.CRITIQUE:
                st.markdown(f"## 🔴 {risque.titre}")
            elif risque.niveau == RiskLevel.ELEVE:
                st.markdown(f"## 🟠 {risque.titre}")
            elif risque.niveau == RiskLevel.MOYEN:
                st.markdown(f"## 🟡 {risque.titre}")
            else:
                st.markdown(f"## 🟢 {risque.titre}")
        
        with col2:
            if st.button("❌ Fermer"):
                st.session_state.show_risque_detail = False
                st.rerun()
        
        # Onglets pour le détail
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Informations",
            "🛡️ Mitigation",
            "📊 Évaluation",
            "📝 Actions"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Niveau :** {risque.niveau.value.upper()}")
                st.write(f"**Statut :** {risque.statut}")
                st.write(f"**Responsable :** {risque.responsable or 'Non assigné'}")
                st.write(f"**Date d'identification :** {risque.date_identification.strftime('%d/%m/%Y')}")
            
            with col2:
                st.write(f"**Score de risque :** {risque.score_risque:.2f}")
                st.write(f"**Probabilité :** {risque.probabilite:.1f}")
                st.write(f"**Impact :** {risque.impact:.1f}")
                if risque.date_echeance:
                    jours = (risque.date_echeance - datetime.now()).days
                    st.write(f"**Échéance :** {risque.date_echeance.strftime('%d/%m/%Y')} ({jours} jours)")
            
            st.markdown("### Description")
            st.info(risque.description)
        
        with tab2:
            st.markdown("### 🛡️ Mesures de mitigation")
            
            if risque.mesures_mitigation:
                for i, mesure in enumerate(risque.mesures_mitigation):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(f"• {mesure}")
                    with col2:
                        if st.button("🗑️", key=f"del_mesure_{i}"):
                            risque.mesures_mitigation.pop(i)
                            manager.update_risque(risque_id, mesures_mitigation=risque.mesures_mitigation)
                            st.rerun()
            else:
                st.info("Aucune mesure de mitigation définie")
            
            # Ajouter une mesure
            with st.expander("➕ Ajouter une mesure"):
                nouvelle_mesure = st.text_input("Nouvelle mesure")
                if st.button("Ajouter"):
                    if nouvelle_mesure:
                        risque.mesures_mitigation.append(nouvelle_mesure)
                        manager.update_risque(risque_id, mesures_mitigation=risque.mesures_mitigation)
                        st.success("Mesure ajoutée")
                        st.rerun()
        
        with tab3:
            st.markdown("### 📊 Réévaluation du risque")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_probabilite = st.slider(
                    "Nouvelle probabilité",
                    min_value=0.0,
                    max_value=1.0,
                    value=risque.probabilite,
                    step=0.1
                )
            
            with col2:
                new_impact = st.slider(
                    "Nouvel impact",
                    min_value=0.0,
                    max_value=1.0,
                    value=risque.impact,
                    step=0.1
                )
            
            new_score = new_probabilite * new_impact
            
            # Comparaison
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score actuel", f"{risque.score_risque:.2f}")
            with col2:
                st.metric(
                    "Nouveau score",
                    f"{new_score:.2f}",
                    delta=f"{new_score - risque.score_risque:.2f}"
                )
            with col3:
                if st.button("💾 Appliquer", use_container_width=True):
                    manager.update_risque(
                        risque_id,
                        probabilite=new_probabilite,
                        impact=new_impact
                    )
                    st.success("Évaluation mise à jour")
                    st.rerun()
        
        with tab4:
            st.markdown("### 📝 Actions sur le risque")
            
            # Changer le statut
            col1, col2 = st.columns(2)
            
            with col1:
                new_statut = st.selectbox(
                    "Nouveau statut",
                    manager.STATUTS_RISQUES,
                    index=manager.STATUTS_RISQUES.index(risque.statut)
                )
                
                if st.button("Changer le statut", use_container_width=True):
                    manager.update_risque(risque_id, statut=new_statut)
                    st.success(f"Statut changé en '{new_statut}'")
                    st.rerun()
            
            with col2:
                new_responsable = st.text_input("Assigner à", value=risque.responsable or "")
                
                if st.button("Assigner", use_container_width=True):
                    manager.update_risque(risque_id, responsable=new_responsable)
                    st.success(f"Assigné à {new_responsable}")
                    st.rerun()
            
            # Actions dangereuses
            st.markdown("### ⚠️ Zone dangereuse")
            
            if st.button("🗑️ Supprimer ce risque", use_container_width=True, type="secondary"):
                if st.button("⚠️ Confirmer la suppression", use_container_width=True):
                    manager.delete_risque(risque_id)
                    st.success("Risque supprimé")
                    st.session_state.show_risque_detail = False
                    st.rerun()

def display_risk_matrix(manager: RisqueManager):
    """Affiche la matrice des risques"""
    st.subheader("📊 Matrice des risques")
    
    risques = manager.list_risques()
    
    if not risques:
        st.info("Aucun risque à afficher dans la matrice")
        return
    
    # Créer la matrice
    st.markdown("### Positionnement des risques")
    
    # Axes
    st.write("**↑ Impact** | **Probabilité →**")
    
    # Créer une grille 5x5
    grid = [[[] for _ in range(5)] for _ in range(5)]
    
    # Placer les risques dans la grille
    for risque in risques:
        # Convertir probabilité et impact en indices (0-4)
        prob_idx = min(int(risque.probabilite * 5), 4)
        impact_idx = min(int(risque.impact * 5), 4)
        
        # La matrice est inversée verticalement (impact élevé en haut)
        grid[4 - impact_idx][prob_idx].append(risque)
    
    # Afficher la matrice
    for i in range(5):
        cols = st.columns(5)
        for j in range(5):
            with cols[j]:
                # Calculer le niveau de risque de la cellule
                prob = (j + 0.5) / 5
                impact = (4 - i + 0.5) / 5
                score = prob * impact
                
                # Couleur de fond selon le score
                if score <= 0.25:
                    color = "🟢"
                elif score <= 0.5:
                    color = "🟡"
                elif score <= 0.75:
                    color = "🟠"
                else:
                    color = "🔴"
                
                # Afficher la cellule
                st.markdown(f"**{color}**")
                
                # Afficher les risques dans cette cellule
                for risque in grid[i][j]:
                    if st.button(
                        risque.titre[:15] + "...",
                        key=f"matrix_{risque.id}",
                        help=f"{risque.titre}\nScore: {risque.score_risque:.2f}"
                    ):
                        st.session_state.current_risque_id = risque.id
                        st.session_state.show_risque_detail = True
    
    # Légende
    st.markdown("### Légende")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.success("🟢 Risque faible (< 0.25)")
    with col2:
        st.warning("🟡 Risque moyen (0.25-0.5)")
    with col3:
        st.error("🟠 Risque élevé (0.5-0.75)")
    with col4:
        st.error("🔴 Risque critique (> 0.75)")
    
    # Statistiques de la matrice
    st.markdown("### 📊 Analyse de la matrice")
    
    col1, col2, col3, col4 = st.columns(4)
    
    risques_faibles = len([r for r in risques if r.score_risque <= 0.25])
    risques_moyens = len([r for r in risques if 0.25 < r.score_risque <= 0.5])
    risques_eleves = len([r for r in risques if 0.5 < r.score_risque <= 0.75])
    risques_critiques = len([r for r in risques if r.score_risque > 0.75])
    
    with col1:
        st.metric("Faibles", risques_faibles, help="Score ≤ 0.25")
    with col2:
        st.metric("Moyens", risques_moyens, help="0.25 < Score ≤ 0.5")
    with col3:
        st.metric("Élevés", risques_eleves, help="0.5 < Score ≤ 0.75")
    with col4:
        st.metric("Critiques", risques_critiques, help="Score > 0.75")

def display_history(manager: RisqueManager):
    """Affiche l'historique des actions sur les risques"""
    st.subheader("📜 Historique des actions")
    
    historique = st.session_state.risques_historique
    
    if not historique:
        st.info("Aucune action enregistrée")
        return
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtre_action = st.selectbox(
            "Type d'action",
            ["Toutes", "creation", "modification", "suppression"]
        )
    
    with col2:
        filtre_periode = st.selectbox(
            "Période",
            ["Tout", "Aujourd'hui", "7 derniers jours", "30 derniers jours"]
        )
    
    # Filtrer l'historique
    historique_filtre = historique.copy()
    
    if filtre_action != "Toutes":
        historique_filtre = [h for h in historique_filtre if h['action'] == filtre_action]
    
    if filtre_periode != "Tout":
        now = datetime.now()
        if filtre_periode == "Aujourd'hui":
            date_limite = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filtre_periode == "7 derniers jours":
            date_limite = now - timedelta(days=7)
        else:  # 30 derniers jours
            date_limite = now - timedelta(days=30)
        
        historique_filtre = [h for h in historique_filtre if h['timestamp'] >= date_limite]
    
    # Trier par date décroissante
    historique_filtre.sort(key=lambda h: h['timestamp'], reverse=True)
    
    # Afficher l'historique
    for entry in historique_filtre[:50]:  # Limiter à 50 entrées
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            st.write(f"**{entry['timestamp'].strftime('%d/%m/%Y %H:%M')}**")
            st.caption(f"Par : {entry['user']}")
        
        with col2:
            # Icône selon l'action
            if entry['action'] == 'creation':
                icon = "➕"
                color = "green"
            elif entry['action'] == 'modification':
                icon = "✏️"
                color = "blue"
            else:  # suppression
                icon = "🗑️"
                color = "red"
            
            st.markdown(f":{color}[{icon} {entry['action'].capitalize()}]")
            
            # Détails selon l'action
            if entry['action'] == 'creation':
                st.write(f"Risque créé : **{entry['details'].get('titre', 'N/A')}**")
            elif entry['action'] == 'modification':
                if 'old_state' in entry['details'] and 'new_state' in entry['details']:
                    old = entry['details']['old_state']
                    new = entry['details']['new_state']
                    changes = []
                    if old['niveau'] != new['niveau']:
                        changes.append(f"Niveau: {old['niveau']} → {new['niveau']}")
                    if old['statut'] != new['statut']:
                        changes.append(f"Statut: {old['statut']} → {new['statut']}")
                    if abs(old['score'] - new['score']) > 0.01:
                        changes.append(f"Score: {old['score']:.2f} → {new['score']:.2f}")
                    
                    if changes:
                        st.caption(" | ".join(changes))
            else:  # suppression
                st.write(f"Risque supprimé : **{entry['details'].get('titre', 'N/A')}**")
        
        with col3:
            # Lien vers le risque (s'il existe encore)
            if entry['action'] != 'suppression':
                risque = manager.get_risque(entry['risque_id'])
                if risque:
                    if st.button("Voir", key=f"hist_{entry['timestamp'].timestamp()}"):
                        st.session_state.current_risque_id = entry['risque_id']
                        st.session_state.show_risque_detail = True
        
        st.divider()
    
    # Export de l'historique
    if st.button("📥 Exporter l'historique complet"):
        export_data = []
        for entry in historique:
            export_data.append({
                'timestamp': entry['timestamp'].isoformat(),
                'action': entry['action'],
                'risque_id': entry['risque_id'],
                'user': entry['user'],
                'details': entry['details']
            })
        
        st.download_button(
            "Télécharger",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"historique_risques_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Point d'entrée principal
if __name__ == "__main__":
    display_risques_interface()
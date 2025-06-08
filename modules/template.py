# modules/templates.py
"""Module de gestion des templates de documents juridiques"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import re

from models.dataclasses import Template
from utils.helpers import clean_key

# Templates prédéfinis
BUILTIN_TEMPLATES = {
    'conclusions_defense': Template(
        id='conclusions_defense',
        name='Conclusions en défense',
        type='conclusions',
        structure=[
            'POUR : [Partie défenderesse]',
            '',
            'CONTRE : [Partie demanderesse]',
            '',
            'PLAISE AU TRIBUNAL',
            '',
            'I. FAITS ET PROCÉDURE',
            '   A. Rappel des faits',
            '   B. Procédure',
            '',
            'II. DISCUSSION',
            '   A. Sur la recevabilité',
            '      1. [Point de recevabilité]',
            '   B. Sur le fond',
            '      1. Sur [premier moyen]',
            '      2. Sur [deuxième moyen]',
            '',
            'III. SUR LES DEMANDES',
            '   A. Sur les demandes principales',
            '   B. Sur les demandes accessoires',
            '',
            'PAR CES MOTIFS',
            '',
            'REJETER l\'ensemble des demandes',
            'CONDAMNER [partie adverse] aux entiers dépens'
        ],
        style='formel',
        category='Procédure civile',
        description='Template standard pour des conclusions en défense',
        is_builtin=True
    ),
    
    'plainte_simple': Template(
        id='plainte_simple',
        name='Plainte simple',
        type='plainte',
        structure=[
            'Madame, Monsieur le Procureur de la République',
            'Tribunal judiciaire de [Ville]',
            '',
            'PLAINTE',
            '',
            'Je soussigné(e) [Nom, Prénom]',
            'Né(e) le [Date] à [Lieu]',
            'Demeurant [Adresse]',
            'Profession : [Profession]',
            '',
            'Ai l\'honneur de porter plainte contre :',
            '[Identité du mis en cause ou X]',
            '',
            'POUR LES FAITS SUIVANTS :',
            '',
            '[Exposé détaillé des faits]',
            '',
            'Ces faits sont susceptibles de constituer :',
            '- [Qualification juridique 1]',
            '- [Qualification juridique 2]',
            '',
            'PRÉJUDICES SUBIS :',
            '[Description des préjudices]',
            '',
            'PIÈCES JOINTES :',
            '1. [Pièce 1]',
            '2. [Pièce 2]',
            '',
            'Je me tiens à votre disposition pour tout complément.',
            '',
            'Fait à [Ville], le [Date]',
            'Signature'
        ],
        style='formel',
        category='Pénal',
        description='Template pour une plainte simple',
        is_builtin=True
    ),
    
    'constitution_partie_civile': Template(
        id='constitution_partie_civile',
        name='Constitution de partie civile',
        type='constitution_pc',
        structure=[
            'Madame, Monsieur le Doyen des juges d\'instruction',
            'Tribunal judiciaire de [Ville]',
            '',
            'PLAINTE AVEC CONSTITUTION DE PARTIE CIVILE',
            '',
            'POUR :',
            '[Identité complète du plaignant]',
            'Ayant pour conseil [Me XXX]',
            '',
            'CONTRE :',
            '[Identité du mis en cause ou X]',
            '',
            'EXPOSÉ DES FAITS :',
            '',
            'I. CONTEXTE',
            '[Contexte détaillé]',
            '',
            'II. FAITS DÉLICTUEUX',
            '[Description précise et chronologique]',
            '',
            'III. QUALIFICATION JURIDIQUE',
            '[Analyse juridique des faits]',
            '',
            'IV. PRÉJUDICES',
            '   A. Préjudice matériel',
            '      [Détail et évaluation]',
            '   B. Préjudice moral',
            '      [Description]',
            '',
            'V. CONSTITUTION DE PARTIE CIVILE',
            'Le plaignant se constitue partie civile et sollicite :',
            '- La mise en examen de [X]',
            '- Tous actes d\'instruction utiles',
            '- La condamnation aux dommages-intérêts',
            '',
            'VI. CONSIGNATION',
            'Le plaignant verse la consignation fixée.',
            '',
            'PIÈCES COMMUNIQUÉES :',
            '[Liste numérotée]',
            '',
            'Fait à [Ville], le [Date]'
        ],
        style='formel',
        category='Pénal',
        description='Template pour une constitution de partie civile',
        is_builtin=True
    ),
    
    'assignation': Template(
        id='assignation',
        name='Assignation',
        type='assignation',
        structure=[
            'ASSIGNATION DEVANT LE TRIBUNAL JUDICIAIRE DE [VILLE]',
            '',
            'L\'AN [ANNÉE]',
            'ET LE [DATE]',
            '',
            'À LA REQUÊTE DE :',
            '[Identité complète du demandeur]',
            'Ayant pour avocat [Me XXX]',
            '',
            'J\'AI, HUISSIER DE JUSTICE SOUSSIGNÉ,',
            '',
            'DONNÉ ASSIGNATION À :',
            '[Identité complète du défendeur]',
            '',
            'À COMPARAÎTRE :',
            'Devant le Tribunal judiciaire de [Ville]',
            'À l\'audience du [Date] à [Heure]',
            '',
            'POUR :',
            '',
            'EXPOSÉ DES FAITS :',
            '[Exposé détaillé]',
            '',
            'DISCUSSION :',
            '   I. SUR LA COMPÉTENCE',
            '   II. SUR LA RECEVABILITÉ',
            '   III. AU FOND',
            '',
            'PAR CES MOTIFS',
            '',
            'DIRE ET JUGER que [demandes]',
            '',
            'CONDAMNER [défendeur] à payer :',
            '- [Montant] € à titre de [...]',
            '- [Article 700]',
            '- Aux entiers dépens',
            '',
            'SOUS TOUTES RÉSERVES'
        ],
        style='formel',
        category='Procédure civile',
        description='Template pour une assignation en justice',
        is_builtin=True
    ),
    
    'memoire_defense': Template(
        id='memoire_defense',
        name='Mémoire en défense',
        type='memoire',
        structure=[
            'MÉMOIRE EN DÉFENSE',
            '',
            'POUR : [Défendeur]',
            'CONTRE : [Demandeur]',
            '',
            'Procédure n° [Numéro]',
            '',
            'I. RAPPEL DES FAITS ET DE LA PROCÉDURE',
            '   A. Les faits',
            '   B. La procédure',
            '',
            'II. DISCUSSION',
            '   A. Sur la procédure',
            '      1. [Moyen de procédure]',
            '   B. Sur le fond',
            '      1. [Premier moyen]',
            '         a) En droit',
            '         b) En fait',
            '      2. [Deuxième moyen]',
            '',
            'III. SUR LES PRÉTENTIONS ADVERSES',
            '   A. Sur le principal',
            '   B. Sur les dommages-intérêts',
            '',
            'PAR CES MOTIFS',
            '',
            '- DÉBOUTER [demandeur] de l\'ensemble de ses demandes',
            '- SUBSIDIAIREMENT, [demandes subsidiaires]',
            '- CONDAMNER [demandeur] à payer [montant] € au titre de l\'article 700',
            '- CONDAMNER [demandeur] aux entiers dépens'
        ],
        style='formel',
        category='Procédure',
        description='Template pour un mémoire en défense',
        is_builtin=True
    ),
    
    'requete': Template(
        id='requete',
        name='Requête',
        type='requete',
        structure=[
            'REQUÊTE',
            '',
            'À Madame, Monsieur le Président',
            'Du Tribunal judiciaire de [Ville]',
            '',
            'REQUÉRANT :',
            '[Identité complète]',
            'Ayant pour conseil [Me XXX]',
            '',
            'A l\'honneur de vous exposer :',
            '',
            'I. FAITS',
            '[Exposé des faits]',
            '',
            'II. PROCÉDURE',
            '[Le cas échéant]',
            '',
            'III. DISCUSSION',
            '   A. Sur la compétence',
            '   B. Sur le bien-fondé',
            '',
            'IV. PIÈCES JUSTIFICATIVES',
            '[Liste des pièces]',
            '',
            'PAR CES MOTIFS',
            '',
            'PLAISE AU TRIBUNAL',
            '',
            '- ORDONNER [mesure sollicitée]',
            '- DIRE que [modalités]',
            '',
            'SOUS TOUTES RÉSERVES',
            '',
            'Fait à [Ville], le [Date]'
        ],
        style='formel',
        category='Procédure civile',
        description='Template pour une requête',
        is_builtin=True
    ),
    
    'note_plaidoirie': Template(
        id='note_plaidoirie',
        name='Note de plaidoirie',
        type='note',
        structure=[
            'NOTE DE PLAIDOIRIE',
            '',
            'Audience du [Date]',
            'Affaire : [Parties]',
            'RG n° [Numéro]',
            '',
            'Pour : [Client]',
            '',
            'I. RAPPEL DE LA PROCÉDURE',
            '[Points essentiels]',
            '',
            'II. FAITS ESSENTIELS',
            '[Résumé des faits marquants]',
            '',
            'III. MOYENS',
            '   A. [Premier moyen]',
            '      • [Argument 1]',
            '      • [Argument 2]',
            '   B. [Deuxième moyen]',
            '',
            'IV. DEMANDES',
            '- [Demande principale]',
            '- [Demande subsidiaire]',
            '',
            'V. PIÈCES ESSENTIELLES',
            '- Pièce n°[X] : [Description]',
            '',
            '[Signature]'
        ],
        style='synthétique',
        category='Plaidoirie',
        description='Template pour une note de plaidoirie',
        is_builtin=True
    )
}

def process_template_request(query: str, analysis: dict):
    """Traite une demande liée aux templates"""
    
    action = detect_template_action(query, analysis)
    
    if action == 'create':
        show_create_template_interface()
    
    elif action == 'edit':
        show_edit_template_interface()
    
    elif action == 'apply':
        show_apply_template_interface()
    
    elif action == 'list':
        show_templates_list()
    
    else:
        # Interface par défaut
        show_templates_interface()

def detect_template_action(query: str, analysis: dict) -> str:
    """Détecte l'action demandée sur les templates"""
    
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['créer', 'nouveau', 'ajouter']):
        return 'create'
    elif any(word in query_lower for word in ['modifier', 'éditer', 'changer']):
        return 'edit'
    elif any(word in query_lower for word in ['utiliser', 'appliquer', 'générer']):
        return 'apply'
    elif any(word in query_lower for word in ['liste', 'voir', 'afficher']):
        return 'list'
    
    return 'default'

def show_templates_interface():
    """Interface principale des templates"""
    
    st.markdown("### 📄 Gestion des templates")
    
    tabs = st.tabs([
        "📚 Bibliothèque",
        "➕ Créer",
        "✏️ Modifier",
        "🎯 Appliquer",
        "⚙️ Configuration"
    ])
    
    with tabs[0]:
        show_templates_library()
    
    with tabs[1]:
        show_create_template_interface()
    
    with tabs[2]:
        show_edit_template_interface()
    
    with tabs[3]:
        show_apply_template_interface()
    
    with tabs[4]:
        show_templates_configuration()

def show_templates_library():
    """Affiche la bibliothèque de templates"""
    
    st.markdown("#### 📚 Bibliothèque de templates")
    
    # Récupérer tous les templates
    all_templates = get_all_templates()
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input(
            "🔍 Rechercher",
            placeholder="Nom, type, catégorie...",
            key="template_search"
        )
    
    with col2:
        categories = ["Toutes"] + get_template_categories(all_templates)
        selected_category = st.selectbox(
            "Catégorie",
            categories,
            key="template_category_filter"
        )
    
    with col3:
        types = ["Tous"] + get_template_types(all_templates)
        selected_type = st.selectbox(
            "Type",
            types,
            key="template_type_filter"
        )
    
    # Filtrer les templates
    filtered_templates = filter_templates(all_templates, search_query, selected_category, selected_type)
    
    # Statistiques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total templates", len(all_templates))
    
    with col2:
        custom_count = sum(1 for t in all_templates.values() if not t.is_builtin)
        st.metric("Templates personnalisés", custom_count)
    
    with col3:
        recent_count = sum(
            1 for t in all_templates.values()
            if (datetime.now() - t.created_at).days < 30
        )
        st.metric("Créés récemment", recent_count)
    
    # Affichage des templates
    if not filtered_templates:
        st.info("Aucun template trouvé")
    else:
        for template_id, template in filtered_templates.items():
            show_template_card(template_id, template)

def get_all_templates() -> Dict[str, Template]:
    """Récupère tous les templates disponibles"""
    
    # Templates intégrés
    all_templates = BUILTIN_TEMPLATES.copy()
    
    # Templates personnalisés
    custom_templates = st.session_state.get('custom_templates', {})
    all_templates.update(custom_templates)
    
    return all_templates

def get_template_categories(templates: Dict[str, Template]) -> List[str]:
    """Récupère les catégories uniques"""
    
    categories = set()
    for template in templates.values():
        categories.add(template.category)
    
    return sorted(list(categories))

def get_template_types(templates: Dict[str, Template]) -> List[str]:
    """Récupère les types uniques"""
    
    types = set()
    for template in templates.values():
        types.add(template.type)
    
    return sorted(list(types))

def filter_templates(
    templates: Dict[str, Template],
    search_query: str,
    category: str,
    template_type: str
) -> Dict[str, Template]:
    """Filtre les templates"""
    
    filtered = {}
    search_lower = search_query.lower()
    
    for template_id, template in templates.items():
        # Filtre recherche
        if search_query:
            searchable = f"{template.name} {template.type} {template.category} {template.description}".lower()
            if search_lower not in searchable:
                continue
        
        # Filtre catégorie
        if category != "Toutes" and template.category != category:
            continue
        
        # Filtre type
        if template_type != "Tous" and template.type != template_type:
            continue
        
        filtered[template_id] = template
    
    return filtered

def show_template_card(template_id: str, template: Template):
    """Affiche une carte de template"""
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Titre et description
            icon = "🔒" if template.is_builtin else "✏️"
            st.markdown(f"### {icon} {template.name}")
            
            if template.description:
                st.caption(template.description)
            
            # Métadonnées
            meta_parts = [
                f"📁 {template.category}",
                f"🏷️ {template.type}",
                f"📝 {len(template.structure)} lignes"
            ]
            
            if template.variables:
                meta_parts.append(f"🔤 {len(template.variables)} variables")
            
            st.caption(" • ".join(meta_parts))
        
        with col2:
            # Statistiques d'usage
            st.metric("Utilisations", template.usage_count)
            
            # Date
            if not template.is_builtin:
                st.caption(f"Créé le {template.created_at.strftime('%d/%m/%Y')}")
        
        with col3:
            # Actions
            if st.button("👁️", key=f"preview_template_{template_id}", help="Aperçu"):
                show_template_preview(template)
            
            if st.button("🎯", key=f"use_template_{template_id}", help="Utiliser"):
                apply_template(template)
            
            if not template.is_builtin:
                if st.button("✏️", key=f"edit_template_{template_id}", help="Modifier"):
                    st.session_state.editing_template = template_id
                
                if st.button("🗑️", key=f"delete_template_{template_id}", help="Supprimer"):
                    if confirm_delete_template(template_id):
                        delete_template(template_id)
        
        st.divider()

def show_template_preview(template: Template):
    """Affiche un aperçu du template"""
    
    with st.expander(f"👁️ Aperçu : {template.name}", expanded=True):
        # Structure
        st.markdown("**Structure :**")
        
        structure_text = "\n".join(template.structure)
        
        # Surligner les variables
        for var in template.variables:
            structure_text = structure_text.replace(f"[{var}]", f"**[{var}]**")
        
        st.text_area(
            "Contenu du template",
            value=structure_text,
            height=400,
            disabled=True,
            key=f"preview_content_{template.id}"
        )
        
        # Variables détectées
        if template.variables:
            st.markdown("**Variables détectées :**")
            
            cols = st.columns(3)
            for i, var in enumerate(template.variables):
                with cols[i % 3]:
                    st.caption(f"• [{var}]")

def show_create_template_interface():
    """Interface de création de template"""
    
    st.markdown("#### ➕ Créer un nouveau template")
    
    # Base de départ
    base_options = ["Vide"] + [t.name for t in BUILTIN_TEMPLATES.values()]
    base_template = st.selectbox(
        "Partir de",
        base_options,
        key="create_base_template"
    )
    
    # Si partir d'un template existant
    if base_template != "Vide":
        base = next(t for t in BUILTIN_TEMPLATES.values() if t.name == base_template)
        initial_structure = "\n".join(base.structure)
        initial_type = base.type
        initial_category = base.category
        initial_style = base.style
    else:
        initial_structure = ""
        initial_type = "autre"
        initial_category = "Autre"
        initial_style = "formel"
    
    # Formulaire
    with st.form("create_template_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Nom du template *",
                placeholder="Ex: Conclusions complexes",
                key="create_template_name"
            )
            
            template_type = st.selectbox(
                "Type *",
                ["conclusions", "plainte", "assignation", "requete", "memoire", "courrier", "autre"],
                index=["conclusions", "plainte", "assignation", "requete", "memoire", "courrier", "autre"].index(initial_type),
                key="create_template_type"
            )
            
            category = st.text_input(
                "Catégorie",
                value=initial_category,
                placeholder="Ex: Procédure civile",
                key="create_template_category"
            )
        
        with col2:
            style = st.selectbox(
                "Style",
                ["formel", "persuasif", "technique", "synthétique", "pédagogique"],
                index=["formel", "persuasif", "technique", "synthétique", "pédagogique"].index(initial_style),
                key="create_template_style"
            )
            
            description = st.text_area(
                "Description",
                placeholder="Description du template et de son usage",
                height=100,
                key="create_template_description"
            )
        
        # Structure
        st.markdown("**Structure du template**")
        st.info("""
        💡 Utilisez [NomVariable] pour créer des variables.
        Une variable par ligne pour une meilleure lisibilité.
        """)
        
        structure = st.text_area(
            "Contenu",
            value=initial_structure,
            height=400,
            placeholder="Entrez la structure du template...",
            key="create_template_structure"
        )
        
        # Validation et soumission
        col1, col2 = st.columns(2)
        
        with col1:
            preview = st.form_submit_button("👁️ Aperçu", type="secondary")
        
        with col2:
            submit = st.form_submit_button("💾 Créer le template", type="primary")
    
    # Aperçu
    if preview:
        show_template_creation_preview(name, structure, template_type, category, style, description)
    
    # Création
    if submit:
        if not name:
            st.error("❌ Le nom est requis")
        elif not structure:
            st.error("❌ La structure est requise")
        else:
            create_new_template(name, structure, template_type, category, style, description)

def show_template_creation_preview(
    name: str,
    structure: str,
    template_type: str,
    category: str,
    style: str,
    description: str
):
    """Aperçu du template en création"""
    
    # Créer un template temporaire
    temp_template = Template(
        id=f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=name or "Sans nom",
        type=template_type,
        structure=structure.split('\n'),
        style=style,
        category=category,
        description=description,
        is_builtin=False
    )
    
    # Extraire les variables
    temp_template.extract_variables()
    
    # Afficher l'aperçu
    show_template_preview(temp_template)

def create_new_template(
    name: str,
    structure: str,
    template_type: str,
    category: str,
    style: str,
    description: str
):
    """Crée un nouveau template"""
    
    # Générer l'ID
    template_id = clean_key(name)
    
    # Vérifier l'unicité
    if 'custom_templates' not in st.session_state:
        st.session_state.custom_templates = {}
    
    if template_id in st.session_state.custom_templates:
        # Ajouter un timestamp pour l'unicité
        template_id = f"{template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Créer le template
    new_template = Template(
        id=template_id,
        name=name,
        type=template_type,
        structure=structure.split('\n'),
        style=style,
        category=category,
        description=description,
        is_builtin=False,
        created_at=datetime.now()
    )
    
    # Extraire les variables
    new_template.extract_variables()
    
    # Sauvegarder
    st.session_state.custom_templates[template_id] = new_template
    
    # Persister (optionnel)
    save_templates_to_storage()
    
    st.success(f"✅ Template '{name}' créé avec succès")
    
    # Proposer de l'utiliser
    if st.button("🎯 Utiliser ce template maintenant"):
        apply_template(new_template)

def show_edit_template_interface():
    """Interface d'édition de template"""
    
    st.markdown("#### ✏️ Modifier un template")
    
    # Sélection du template
    custom_templates = st.session_state.get('custom_templates', {})
    
    if not custom_templates:
        st.info("Aucun template personnalisé à modifier")
        st.write("Les templates intégrés ne peuvent pas être modifiés directement.")
        return
    
    # Template à éditer
    if st.session_state.get('editing_template'):
        template_id = st.session_state.editing_template
    else:
        template_id = st.selectbox(
            "Template à modifier",
            options=list(custom_templates.keys()),
            format_func=lambda x: custom_templates[x].name,
            key="select_template_to_edit"
        )
    
    if not template_id:
        return
    
    template = custom_templates[template_id]
    
    # Formulaire d'édition
    with st.form("edit_template_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Nom",
                value=template.name,
                key="edit_template_name"
            )
            
            template_type = st.selectbox(
                "Type",
                ["conclusions", "plainte", "assignation", "requete", "memoire", "courrier", "autre"],
                index=["conclusions", "plainte", "assignation", "requete", "memoire", "courrier", "autre"].index(template.type),
                key="edit_template_type"
            )
            
            category = st.text_input(
                "Catégorie",
                value=template.category,
                key="edit_template_category"
            )
        
        with col2:
            style = st.selectbox(
                "Style",
                ["formel", "persuasif", "technique", "synthétique", "pédagogique"],
                index=["formel", "persuasif", "technique", "synthétique", "pédagogique"].index(template.style),
                key="edit_template_style"
            )
            
            description = st.text_area(
                "Description",
                value=template.description,
                height=100,
                key="edit_template_description"
            )
        
        # Structure
        st.markdown("**Structure**")
        
        structure = st.text_area(
            "Contenu",
            value="\n".join(template.structure),
            height=400,
            key="edit_template_structure"
        )
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            preview = st.form_submit_button("👁️ Aperçu")
        
        with col2:
            save = st.form_submit_button("💾 Sauvegarder", type="primary")
        
        with col3:
            cancel = st.form_submit_button("❌ Annuler")
    
    # Aperçu
    if preview:
        show_template_creation_preview(name, structure, template_type, category, style, description)
    
    # Sauvegarde
    if save:
        update_template(template_id, name, structure, template_type, category, style, description)
    
    # Annulation
    if cancel:
        st.session_state.editing_template = None
        st.rerun()

def update_template(
    template_id: str,
    name: str,
    structure: str,
    template_type: str,
    category: str,
    style: str,
    description: str
):
    """Met à jour un template existant"""
    
    if template_id not in st.session_state.custom_templates:
        st.error("❌ Template introuvable")
        return
    
    # Mettre à jour
    template = st.session_state.custom_templates[template_id]
    
    template.name = name
    template.type = template_type
    template.structure = structure.split('\n')
    template.style = style
    template.category = category
    template.description = description
    template.updated_at = datetime.now()
    
    # Recalculer les variables
    template.extract_variables()
    
    # Sauvegarder
    save_templates_to_storage()
    
    st.success(f"✅ Template '{name}' mis à jour")
    
    # Nettoyer l'état
    st.session_state.editing_template = None
    st.rerun()

def show_apply_template_interface():
    """Interface d'application de template"""
    
    st.markdown("#### 🎯 Appliquer un template")
    
    # Sélection du template
    all_templates = get_all_templates()
    
    if not all_templates:
        st.info("Aucun template disponible")
        return
    
    template_id = st.selectbox(
        "Choisir un template",
        options=list(all_templates.keys()),
        format_func=lambda x: f"{all_templates[x].name} ({all_templates[x].category})",
        key="select_template_to_apply"
    )
    
    if not template_id:
        return
    
    template = all_templates[template_id]
    
    # Afficher les informations du template
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Type", template.type)
    
    with col2:
        st.metric("Style", template.style)
    
    with col3:
        st.metric("Variables", len(template.variables))
    
    # Remplir les variables
    if template.variables:
        st.markdown("##### 📝 Remplir les variables")
        
        variable_values = {}
        
        # Organiser en colonnes
        cols = st.columns(2)
        
        for i, var in enumerate(template.variables):
            with cols[i % 2]:
                # Valeur par défaut depuis le contexte
                default_value = get_variable_default_value(var)
                
                value = st.text_input(
                    f"[{var}]",
                    value=default_value,
                    key=f"var_{template_id}_{var}"
                )
                
                variable_values[var] = value
    else:
        variable_values = {}
    
    # Options de génération
    with st.expander("⚙️ Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            use_ai = st.checkbox(
                "Enrichir avec l'IA",
                value=True,
                help="L'IA complètera le template avec du contenu pertinent",
                key="template_use_ai"
            )
            
            if use_ai:
                ai_style = st.selectbox(
                    "Style IA",
                    ["Identique au template", "Formel", "Persuasif", "Technique"],
                    key="template_ai_style"
                )
        
        with col2:
            add_jurisprudence = st.checkbox(
                "Ajouter jurisprudence",
                value=False,
                help="Rechercher et intégrer la jurisprudence pertinente",
                key="template_add_juris"
            )
            
            create_docx = st.checkbox(
                "Générer Word",
                value=True,
                help="Créer directement un document Word formaté",
                key="template_create_docx"
            )
    
    # Bouton de génération
    if st.button("🚀 Générer le document", type="primary", key="generate_from_template"):
        generate_document_from_template(
            template,
            variable_values,
            use_ai,
            ai_style if use_ai else template.style,
            add_jurisprudence,
            create_docx
        )

def get_variable_default_value(variable: str) -> str:
    """Obtient une valeur par défaut pour une variable"""
    
    # Valeurs depuis le contexte
    context_values = {
        'Date': datetime.now().strftime('%d/%m/%Y'),
        'Ville': 'Paris',
        'Année': str(datetime.now().year)
    }
    
    # Depuis la session
    if st.session_state.get('current_case_info'):
        case_info = st.session_state.current_case_info
        context_values.update({
            'Partie défenderesse': case_info.get('defendant', ''),
            'Partie demanderesse': case_info.get('plaintiff', ''),
            'Numéro': case_info.get('case_number', ''),
            'Référence': case_info.get('reference', '')
        })
    
    return context_values.get(variable, '')

def generate_document_from_template(
    template: Template,
    variable_values: Dict[str, str],
    use_ai: bool,
    ai_style: str,
    add_jurisprudence: bool,
    create_docx: bool
):
    """Génère un document depuis un template"""
    
    with st.spinner("🔄 Génération du document..."):
        # Remplacer les variables
        content = "\n".join(template.structure)
        
        for var, value in variable_values.items():
            content = content.replace(f"[{var}]", value)
        
        # Enrichissement IA si demandé
        if use_ai:
            content = enrich_with_ai(content, template, ai_style)
        
        # Ajout jurisprudence si demandé
        if add_jurisprudence:
            content = add_relevant_jurisprudence(content, template)
        
        # Incrémenter le compteur d'usage
        template.usage_count += 1
        
        # Sauvegarder le résultat
        result = {
            'type': template.type,
            'document': content,
            'template_used': template.name,
            'timestamp': datetime.now(),
            'style': ai_style if use_ai else template.style,
            'variables': variable_values
        }
        
        st.session_state.redaction_result = result
        
        # Générer Word si demandé
        if create_docx:
            from modules.import_export import export_to_docx
            
            docx_data = export_to_docx(content, {'document_type': template.type})
            
            st.download_button(
                "📄 Télécharger Word",
                docx_data,
                f"{template.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_generated_docx"
            )
        
        st.success("✅ Document généré avec succès")
        
        # Proposer de voir le résultat
        if st.button("📊 Voir le résultat"):
            st.session_state.current_page = 'recherche'
            st.rerun()

def enrich_with_ai(content: str, template: Template, ai_style: str) -> str:
    """Enrichit le contenu avec l'IA"""
    
    from managers.multi_llm_manager import MultiLLMManager
    
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        return content
    
    # Prompt d'enrichissement
    prompt = f"""Enrichis ce document juridique en conservant sa structure.

Type de document : {template.type}
Style demandé : {ai_style}

DOCUMENT :
{content}

INSTRUCTIONS :
1. Conserve EXACTEMENT la structure et les titres
2. Complète les sections vides avec du contenu pertinent
3. Développe les points qui ne sont que des titres
4. Utilise le style {ai_style}
5. Reste cohérent avec le type de document ({template.type})
6. N'ajoute PAS de nouvelles sections

Retourne le document enrichi."""
    
    try:
        provider = list(llm_manager.clients.keys())[0]
        response = llm_manager.query_single_llm(
            provider,
            prompt,
            f"Tu es un expert en rédaction juridique, spécialisé en {template.category}."
        )
        
        if response['success']:
            return response['response']
        
    except Exception as e:
        st.warning(f"⚠️ Enrichissement IA échoué : {str(e)}")
    
    return content

def add_relevant_jurisprudence(content: str, template: Template) -> str:
    """Ajoute la jurisprudence pertinente au document"""
    
    from modules.jurisprudence import get_jurisprudence_for_document, format_jurisprudence_citation
    
    # Extraire les mots-clés du contenu
    keywords = extract_legal_keywords(content)
    
    # Rechercher la jurisprudence
    jurisprudence_refs = get_jurisprudence_for_document(template.type, keywords, limit=5)
    
    if not jurisprudence_refs:
        return content
    
    # Insérer la jurisprudence selon le type de document
    if template.type in ['conclusions', 'memoire']:
        # Ajouter dans la section discussion
        discussion_pattern = r'(II\.\s*DISCUSSION.*?)(\n\s*III\.|\n\s*PAR CES MOTIFS)'
        
        juris_section = "\n\n   C. Jurisprudence applicable\n"
        
        for ref in jurisprudence_refs:
            juris_section += f"\n      - {format_jurisprudence_citation(ref)}"
            if ref.resume:
                juris_section += f"\n        {ref.resume}\n"
        
        content = re.sub(
            discussion_pattern,
            r'\1' + juris_section + r'\2',
            content,
            flags=re.DOTALL
        )
    
    elif template.type == 'plainte':
        # Ajouter après la qualification juridique
        qual_pattern = r'(QUALIFICATION JURIDIQUE.*?)(\n\s*PRÉJUDICES)'
        
        juris_section = "\n\nJurisprudence pertinente :\n"
        
        for ref in jurisprudence_refs:
            juris_section += f"- {format_jurisprudence_citation(ref)}\n"
        
        content = re.sub(
            qual_pattern,
            r'\1' + juris_section + r'\2',
            content,
            flags=re.DOTALL
        )
    
    return content

def extract_legal_keywords(content: str) -> List[str]:
    """Extrait les mots-clés juridiques d'un contenu"""
    
    # Mots-clés juridiques courants
    legal_terms = [
        'responsabilité', 'préjudice', 'dommages', 'faute', 'causalité',
        'contrat', 'obligation', 'nullité', 'prescription', 'compétence',
        'recevabilité', 'procédure', 'preuve', 'bonne foi', 'abus'
    ]
    
    keywords = []
    content_lower = content.lower()
    
    for term in legal_terms:
        if term in content_lower:
            keywords.append(term)
    
    # Ajouter les infractions mentionnées
    infractions = re.findall(r'(?:délit|crime|infraction) (?:de |d\')([^,\.\n]+)', content_lower)
    keywords.extend(infractions)
    
    return keywords[:10]  # Limiter à 10

def show_templates_configuration():
    """Configuration des templates"""
    
    st.markdown("#### ⚙️ Configuration des templates")
    
    # Import/Export
    st.markdown("##### 📦 Import/Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Exporter tous les templates"):
            export_all_templates()
    
    with col2:
        uploaded_file = st.file_uploader(
            "📥 Importer des templates",
            type=['json'],
            key="import_templates_file"
        )
        
        if uploaded_file:
            import_templates(uploaded_file)
    
    # Gestion des templates
    st.markdown("##### 🗃️ Gestion")
    
    custom_templates = st.session_state.get('custom_templates', {})
    
    if custom_templates:
        st.write(f"**{len(custom_templates)} templates personnalisés**")
        
        # Actions groupées
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Supprimer tous les customs"):
                if st.checkbox("Confirmer suppression", key="confirm_delete_all_templates"):
                    st.session_state.custom_templates = {}
                    save_templates_to_storage()
                    st.success("✅ Templates supprimés")
                    st.rerun()
        
        with col2:
            if st.button("📊 Réinitialiser les stats"):
                for template in custom_templates.values():
                    template.usage_count = 0
                save_templates_to_storage()
                st.success("✅ Statistiques réinitialisées")
        
        with col3:
            if st.button("🔄 Recharger"):
                load_templates_from_storage()
                st.rerun()
    
    # Préférences
    st.markdown("##### 🎨 Préférences")
    
    default_ai_enrichment = st.checkbox(
        "Enrichissement IA par défaut",
        value=st.session_state.get('template_default_ai', True),
        key="config_template_ai"
    )
    st.session_state.template_default_ai = default_ai_enrichment
    
    default_juris = st.checkbox(
        "Ajout jurisprudence par défaut",
        value=st.session_state.get('template_default_juris', False),
        key="config_template_juris"
    )
    st.session_state.template_default_juris = default_juris
    
    default_docx = st.checkbox(
        "Génération Word par défaut",
        value=st.session_state.get('template_default_docx', True),
        key="config_template_docx"
    )
    st.session_state.template_default_docx = default_docx

def confirm_delete_template(template_id: str) -> bool:
    """Demande confirmation pour supprimer un template"""
    
    return st.checkbox(
        f"Confirmer la suppression",
        key=f"confirm_delete_{template_id}"
    )

def delete_template(template_id: str):
    """Supprime un template"""
    
    if template_id in st.session_state.custom_templates:
        del st.session_state.custom_templates[template_id]
        save_templates_to_storage()
        st.success("✅ Template supprimé")
        st.rerun()

def save_templates_to_storage():
    """Sauvegarde les templates (dans la session pour l'instant)"""
    
    # Pour une vraie persistence, sauvegarder dans un fichier ou base de données
    pass

def load_templates_from_storage():
    """Charge les templates depuis le stockage"""
    
    # Pour l'instant, les templates sont dans la session
    # Dans une vraie app, charger depuis un fichier ou base de données
    pass

def export_all_templates():
    """Exporte tous les templates"""
    
    all_templates = get_all_templates()
    
    export_data = {
        'builtin': {},
        'custom': {}
    }
    
    for template_id, template in all_templates.items():
        template_dict = {
            'name': template.name,
            'type': template.type,
            'structure': template.structure,
            'style': template.style,
            'category': template.category,
            'description': template.description,
            'variables': template.variables,
            'created_at': template.created_at.isoformat(),
            'updated_at': template.updated_at.isoformat(),
            'usage_count': template.usage_count
        }
        
        if template.is_builtin:
            export_data['builtin'][template_id] = template_dict
        else:
            export_data['custom'][template_id] = template_dict
    
    # JSON
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        "💾 Télécharger templates.json",
        json_str,
        f"templates_export_{datetime.now().strftime('%Y%m%d')}.json",
        "application/json",
        key="download_all_templates"
    )

def import_templates(uploaded_file):
    """Importe des templates depuis un fichier"""
    
    try:
        data = json.load(uploaded_file)
        
        if 'custom_templates' not in st.session_state:
            st.session_state.custom_templates = {}
        
        imported_count = 0
        
        # Importer les templates custom
        if 'custom' in data:
            for template_id, template_data in data['custom'].items():
                # Créer le template
                template = Template(
                    id=template_id,
                    name=template_data['name'],
                    type=template_data['type'],
                    structure=template_data['structure'],
                    style=template_data.get('style', 'formel'),
                    category=template_data.get('category', 'Autre'),
                    description=template_data.get('description', ''),
                    is_builtin=False
                )
                
                # Restaurer les stats
                if 'usage_count' in template_data:
                    template.usage_count = template_data['usage_count']
                
                if 'created_at' in template_data:
                    template.created_at = datetime.fromisoformat(template_data['created_at'])
                
                # Extraire les variables
                template.extract_variables()
                
                st.session_state.custom_templates[template_id] = template
                imported_count += 1
        
        save_templates_to_storage()
        st.success(f"✅ {imported_count} templates importés")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erreur import : {str(e)}")

def apply_template(template: Template):
    """Applique un template sélectionné"""
    
    st.session_state.selected_template = template
    st.session_state.current_page = 'recherche'
    st.session_state.universal_query = f"appliquer template {template.name}"
    st.rerun()

# Fonctions pour intégration avec d'autres modules

def get_template_by_type(doc_type: str) -> Optional[Template]:
    """Récupère un template par type de document"""
    
    all_templates = get_all_templates()
    
    for template in all_templates.values():
        if template.type == doc_type:
            return template
    
    return None

def get_template_structure(template_name: str) -> List[str]:
    """Récupère la structure d'un template par nom"""
    
    all_templates = get_all_templates()
    
    for template in all_templates.values():
        if template.name == template_name:
            return template.structure
    
    return []

def create_template_from_document(document: str, name: str, doc_type: str) -> Template:
    """Crée un template à partir d'un document existant"""
    
    # Analyser la structure
    lines = document.split('\n')
    
    # Identifier les variables potentielles (mots entre crochets ou à remplacer)
    structure = []
    
    for line in lines:
        # Remplacer les données spécifiques par des variables
        # Dates
        line = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '[Date]', line)
        
        # Montants
        line = re.sub(r'\d+(?:\.\d{3})*(?:,\d{2})?\s*€', '[Montant] €', line)
        
        # Noms propres (heuristique simple)
        line = re.sub(r'\b(?:M\.|Mme|Me)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '[Nom]', line)
        
        structure.append(line)
    
    # Créer le template
    template = Template(
        id=clean_key(name),
        name=name,
        type=doc_type,
        structure=structure,
        style='formel',
        category='Importé',
        description=f"Template créé à partir d'un document {doc_type}",
        is_builtin=False
    )
    
    template.extract_variables()
    
    return template
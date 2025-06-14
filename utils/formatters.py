# utils/formatters_extended.py
"""
Fonctions de formatage avancées pour documents juridiques
À ajouter au fichier formatters.py existant
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import re

def create_letterhead_from_template(template_name: str, data: Dict[str, Any]) -> str:
    """
    Crée un en-tête de lettre à partir d'un template
    
    Args:
        template_name: Nom du template
        data: Données pour remplir le template
        
    Returns:
        En-tête formaté
    """
    # Templates prédéfinis
    templates = {
        'cabinet': """
{cabinet_name}
{address_line1}
{address_line2}
{phone} - {email}
{bar_info}

{date}

{recipient_name}
{recipient_address1}
{recipient_address2}
""",
        'simple': """
{sender_name}
{sender_address}

Le {date}

{recipient_name}
{recipient_address}
"""
    }
    
    template = templates.get(template_name, templates['simple'])
    
    # Remplacer les placeholders
    for key, value in data.items():
        placeholder = f"{{{key}}}"
        if placeholder in template:
            template = template.replace(placeholder, str(value))
    
    # Nettoyer les placeholders non remplacés
    template = re.sub(r'\{[^}]+\}', '', template)
    
    # Nettoyer les lignes vides multiples
    template = re.sub(r'\n{3,}', '\n\n', template)
    
    return template.strip()

def create_formatted_docx(content: str, style: str = "formal") -> Dict[str, Any]:
    """
    Crée une structure de document DOCX formaté (métadonnées seulement)
    
    Args:
        content: Contenu du document
        style: Style de formatage
        
    Returns:
        Structure du document
    """
    styles = {
        'formal': {
            'font': 'Times New Roman',
            'size': 12,
            'line_spacing': 1.5,
            'margins': {'top': 2.5, 'bottom': 2.5, 'left': 2.5, 'right': 2.5}
        },
        'modern': {
            'font': 'Arial',
            'size': 11,
            'line_spacing': 1.15,
            'margins': {'top': 2, 'bottom': 2, 'left': 2, 'right': 2}
        }
    }
    
    doc_style = styles.get(style, styles['formal'])
    
    return {
        'content': content,
        'style': doc_style,
        'metadata': {
            'created': datetime.now().isoformat(),
            'format': 'docx',
            'style_name': style
        }
    }

def format_party_designation(party: Dict[str, Any], format_type: str = "full") -> str:
    """
    Formate la désignation d'une partie
    
    Args:
        party: Informations de la partie
        format_type: Type de format (full, short, legal)
        
    Returns:
        Désignation formatée
    """
    if format_type == "short":
        if party.get('type') == 'personne_morale':
            return f"{party.get('denomination', 'Société')} ({party.get('forme_juridique', 'SA')})"
        else:
            return f"{party.get('civilite', '')} {party.get('nom', '')}".strip()
    
    elif format_type == "legal":
        lines = []
        
        if party.get('type') == 'personne_morale':
            lines.append(f"{party.get('denomination', '')}")
            lines.append(f"{party.get('forme_juridique', '')} au capital de {party.get('capital', 'XXX')} €")
            lines.append(f"Immatriculée au RCS de {party.get('rcs_ville', 'XXX')} sous le n° {party.get('siren', 'XXX XXX XXX')}")
            lines.append(f"Siège social : {party.get('siege_social', 'XXX')}")
        else:
            lines.append(f"{party.get('civilite', '')} {party.get('prenom', '')} {party.get('nom', '')}")
            lines.append(f"Né(e) le {party.get('date_naissance', 'XXX')} à {party.get('lieu_naissance', 'XXX')}")
            lines.append(f"Domicilié(e) : {party.get('adresse', 'XXX')}")
        
        return '\n'.join(lines)
    
    else:  # full
        return format_party_designation(party, "legal")

def apply_legal_numbering(sections: List[str], style: str = "decimal") -> List[str]:
    """
    Applique une numérotation juridique aux sections
    
    Args:
        sections: Liste des sections
        style: Style de numérotation (decimal, roman, letter)
        
    Returns:
        Sections numérotées
    """
    numbered = []
    
    for i, section in enumerate(sections, 1):
        if style == "roman":
            number = _to_roman(i)
        elif style == "letter":
            number = chr(ord('A') + i - 1) if i <= 26 else f"A{chr(ord('A') + (i - 27))}"
        else:  # decimal
            number = str(i)
        
        numbered.append(f"{number} - {section}")
    
    return numbered

def _to_roman(num: int) -> str:
    """Convertit un nombre en chiffres romains"""
    values = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    
    result = ''
    for value, letter in values:
        count = num // value
        if count:
            result += letter * count
            num -= value * count
    return result

def create_document_header(title: str, doc_type: str, reference: str = None) -> str:
    """
    Crée un en-tête de document juridique
    """
    header = f"{doc_type.upper()}\n"
    header += "=" * len(doc_type) + "\n\n"
    
    if reference:
        header += f"Référence : {reference}\n\n"
    
    header += f"{title}\n"
    header += "-" * len(title) + "\n\n"
    
    return header

def create_table_of_contents(sections: List[Dict[str, Any]]) -> str:
    """
    Crée une table des matières
    
    Args:
        sections: Liste des sections avec titre et niveau
        
    Returns:
        Table des matières formatée
    """
    toc = "TABLE DES MATIÈRES\n"
    toc += "=" * 20 + "\n\n"
    
    for section in sections:
        indent = "  " * section.get('level', 0)
        title = section.get('title', '')
        page = section.get('page', '...')
        
        # Calculer le nombre de points
        line_length = 80
        dots_length = line_length - len(indent) - len(title) - len(str(page)) - 2
        dots = '.' * max(dots_length, 3)
        
        toc += f"{indent}{title} {dots} {page}\n"
    
    return toc

def split_into_pages(content: str, lines_per_page: int = 50) -> List[str]:
    """
    Divise un contenu en pages
    """
    lines = content.split('\n')
    pages = []
    
    for i in range(0, len(lines), lines_per_page):
        page_lines = lines[i:i + lines_per_page]
        pages.append('\n'.join(page_lines))
    
    return pages

def add_page_numbers(pages: List[str], start_number: int = 1) -> List[str]:
    """
    Ajoute des numéros de page
    """
    numbered_pages = []
    
    for i, page in enumerate(pages, start_number):
        # Ajouter le numéro en bas de page
        footer = f"\n\n{'-' * 80}\nPage {i} / {len(pages) + start_number - 1}"
        numbered_pages.append(page + footer)
    
    return numbered_pages

def format_legal_list(items: List[str], style: str = "dash", indent_level: int = 0) -> str:
    """
    Formate une liste selon les conventions juridiques
    
    Args:
        items: Éléments de la liste
        style: Style de liste (dash, number, letter, roman)
        indent_level: Niveau d'indentation
        
    Returns:
        Liste formatée
    """
    formatted_items = []
    indent = "  " * indent_level
    
    for i, item in enumerate(items, 1):
        if style == "dash":
            prefix = "-"
        elif style == "number":
            prefix = f"{i}."
        elif style == "letter":
            prefix = f"{chr(ord('a') + i - 1)})"
        elif style == "roman":
            prefix = f"{_to_roman(i).lower()})"
        else:
            prefix = "•"
        
        formatted_items.append(f"{indent}{prefix} {item}")
    
    return '\n'.join(formatted_items)

def format_signature_block(signatories: List[Dict[str, str]], location: str = None) -> str:
    """
    Formate un bloc de signatures
    
    Args:
        signatories: Liste des signataires avec nom et titre
        location: Lieu de signature
        
    Returns:
        Bloc de signatures formaté
    """
    block = "\n\n"
    
    if location:
        block += f"Fait à {location}, le {format_date_long(datetime.now())}\n\n"
    
    # Créer les emplacements de signature
    signature_width = 40
    signatures_per_line = 2
    
    for i in range(0, len(signatories), signatures_per_line):
        line_signatories = signatories[i:i + signatures_per_line]
        
        # Ligne des signatures
        sig_line = ""
        for sig in line_signatories:
            sig_line += "_" * 30 + " " * 20
        block += sig_line.rstrip() + "\n"
        
        # Ligne des noms
        name_line = ""
        for sig in line_signatories:
            name = sig.get('name', '')
            name_line += name.ljust(signature_width + 10)
        block += name_line.rstrip() + "\n"
        
        # Ligne des titres
        title_line = ""
        for sig in line_signatories:
            title = sig.get('title', '')
            title_line += title.ljust(signature_width + 10)
        block += title_line.rstrip() + "\n\n"
    
    return block

def format_annex_reference(annex_number: int, title: str) -> str:
    """
    Formate une référence d'annexe
    """
    return f"ANNEXE {annex_number} - {title.upper()}"

def create_document_footer(doc_type: str, page_number: int = None, total_pages: int = None) -> str:
    """
    Crée un pied de page de document
    """
    footer = "\n" + "-" * 80 + "\n"
    
    elements = []
    
    # Type de document
    elements.append(doc_type)
    
    # Date
    elements.append(datetime.now().strftime("%d/%m/%Y"))
    
    # Pagination
    if page_number and total_pages:
        elements.append(f"Page {page_number}/{total_pages}")
    
    footer += " | ".join(elements)
    
    return footer
# utils/formatters.py
"""
Utilitaires pour le formatage de documents juridiques
"""

import re
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

# Import des types nécessaires avec gestion d'erreur
try:
    from models.dataclasses import (
        LetterheadTemplate,
        DocumentJuridique,
        Partie
    )
except ImportError:
    try:
        from modules.dataclasses import (
            LetterheadTemplate,
            DocumentJuridique,
            Partie
        )
    except ImportError:
        # Classes fallback minimales
        class LetterheadTemplate:
            def __init__(self, **kwargs):
                self.cabinet_name = kwargs.get('cabinet_name', '')
                self.lawyers = kwargs.get('lawyers', [])
                self.address = kwargs.get('address', '')
                self.phone = kwargs.get('phone', '')
                self.fax = kwargs.get('fax', '')
                self.email = kwargs.get('email', '')
                self.bar_mentions = kwargs.get('bar_mentions', [])
                self.logo_path = kwargs.get('logo_path', '')
        
        class DocumentJuridique:
            def __init__(self, **kwargs):
                self.numero_reference = kwargs.get('numero_reference', '')
                self.type_document = kwargs.get('type_document', '')
                self.date_document = kwargs.get('date_document')
                self.juridiction = kwargs.get('juridiction', '')
        
        class Partie:
            def __init__(self, **kwargs):
                self.nom = kwargs.get('nom', '')
                self.type = kwargs.get('type', '')
                self.forme_juridique = kwargs.get('forme_juridique', '')
                self.numero_immatriculation = kwargs.get('numero_immatriculation', '')
                self.adresse = kwargs.get('adresse', '')
                self.representant = kwargs.get('representant', '')
                self.avocat = kwargs.get('avocat', '')


def create_letterhead_from_template(template: LetterheadTemplate) -> str:
    """Crée un en-tête de lettre à partir d'un template"""
    lines = []
    
    # Nom du cabinet
    if template.cabinet_name:
        lines.append(template.cabinet_name.upper())
        lines.append("")
    
    # Avocats
    if template.lawyers:
        for lawyer in template.lawyers:
            lines.append(lawyer)
        lines.append("")
    
    # Adresse
    if template.address:
        lines.append(template.address)
    
    # Contact
    contact_parts = []
    if template.phone:
        contact_parts.append(f"Tél: {template.phone}")
    if template.fax:
        contact_parts.append(f"Fax: {template.fax}")
    if template.email:
        contact_parts.append(f"Email: {template.email}")
    
    if contact_parts:
        lines.append(" - ".join(contact_parts))
    
    # Barreaux et mentions
    if template.bar_mentions:
        lines.append("")
        for mention in template.bar_mentions:
            lines.append(mention)
    
    # Logo (placeholder)
    if template.logo_path:
        lines.append("")
        lines.append(f"[LOGO: {template.logo_path}]")
    
    return "\n".join(lines)


def create_formatted_docx(content: str, style_config: Dict[str, Any]) -> bytes:
    """
    Crée un document Word formaté
    Note: En production, utiliserait python-docx
    """
    # Configuration par défaut
    default_config = {
        'font': 'Times New Roman',
        'font_size': 12,
        'line_spacing': 1.5,
        'margins': {
            'top': 2.5,
            'bottom': 2.5,
            'left': 2.5,
            'right': 2.5
        },
        'alignment': 'justify'
    }
    
    # Fusionner avec la configuration fournie
    config = {**default_config, **style_config}
    
    # Simuler la création d'un document Word
    formatted_content = f"""
DOCUMENT WORD
=============

Configuration appliquée:
- Police: {config['font']} {config['font_size']}pt
- Interligne: {config['line_spacing']}
- Alignement: {config['alignment']}
- Marges: {config['margins']['top']}cm (haut), {config['margins']['bottom']}cm (bas), {config['margins']['left']}cm (gauche), {config['margins']['right']}cm (droite)

-------------------

{content}

-------------------

[Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}]
"""
    
    return formatted_content.encode('utf-8')


def format_party_designation(partie: Partie, phase: str = "instruction") -> str:
    """Formate la désignation d'une partie selon la phase procédurale"""
    designation_parts = []
    
    # Nom principal
    if partie.type == "personne_morale" and partie.forme_juridique:
        designation_parts.append(f"{partie.forme_juridique} {partie.nom}")
    else:
        designation_parts.append(partie.nom)
    
    # Numéro d'immatriculation
    if partie.numero_immatriculation:
        designation_parts.append(f"immatriculée au RCS sous le n° {partie.numero_immatriculation}")
    
    # Adresse
    if partie.adresse:
        designation_parts.append(partie.adresse)
    
    # Représentation (selon la phase)
    if phase == "instruction" and partie.representant:
        designation_parts.append(f"représentée par {partie.representant}")
    
    # Avocat
    if partie.avocat:
        if phase == "jugement":
            designation_parts.append(f"comparant par Me {partie.avocat}, avocat")
        else:
            designation_parts.append(f"ayant pour avocat Me {partie.avocat}")
    
    return ", ".join(designation_parts)


def apply_legal_numbering(sections: List[str], style: str = "roman") -> List[str]:
    """Applique une numérotation juridique aux sections"""
    numbered_sections = []
    
    for i, section in enumerate(sections, 1):
        if style == "roman":
            number = _to_roman(i)
        elif style == "letter":
            number = _to_letter(i)
        elif style == "decimal":
            number = f"{i}."
        else:  # numeric
            number = str(i)
        
        numbered_sections.append(f"{number} {section}")
    
    return numbered_sections


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


def _to_letter(num: int) -> str:
    """Convertit un nombre en lettre (A, B, C...)"""
    if num <= 26:
        return chr(ord('A') + num - 1)
    else:
        # Pour les nombres > 26: AA, AB, AC...
        first = (num - 1) // 26
        second = (num - 1) % 26
        return chr(ord('A') + first - 1) + chr(ord('A') + second)


def create_document_header(doc: DocumentJuridique) -> str:
    """Crée l'en-tête d'un document juridique"""
    header_lines = []
    
    # Numéro de référence
    if doc.numero_reference:
        header_lines.append(f"N° {doc.numero_reference}")
        header_lines.append("")
    
    # Type de document
    header_lines.append(doc.type_document.upper())
    header_lines.append("")
    
    # Date
    if doc.date_document:
        from .date_time import format_legal_date
        header_lines.append(format_legal_date(doc.date_document))
        header_lines.append("")
    
    # Juridiction
    if doc.juridiction:
        header_lines.append(doc.juridiction)
        header_lines.append("")
    
    return "\n".join(header_lines)


def create_table_of_contents(sections: List[Dict[str, Any]]) -> str:
    """Crée une table des matières"""
    toc_lines = ["TABLE DES MATIÈRES", "=" * 50, ""]
    
    for i, section in enumerate(sections, 1):
        # Indentation selon le niveau
        indent = "  " * (section.get('level', 1) - 1)
        
        # Numérotation selon le niveau
        if section.get('level', 1) == 1:
            number = _to_roman(i) + "."
        else:
            number = f"{i}."
        
        # Titre
        line = f"{indent}{number} {section['title']}"
        
        # Numéro de page si disponible
        if 'page' in section:
            # Calculer les points de suite
            line_length = len(line)
            dots_count = max(1, 60 - line_length - len(str(section['page'])))
            dots = "." * dots_count
            line += f" {dots} {section['page']}"
        
        toc_lines.append(line)
    
    return "\n".join(toc_lines)


def split_into_pages(text: str, lines_per_page: int = 50) -> List[str]:
    """Divise un texte en pages"""
    lines = text.split('\n')
    pages = []
    
    current_page = []
    current_line_count = 0
    
    for line in lines:
        # Compter les lignes en tenant compte du retour à la ligne
        line_count = 1 + (len(line) // 80)  # Environ 80 caractères par ligne
        
        if current_line_count + line_count > lines_per_page and current_page:
            # Nouvelle page
            pages.append('\n'.join(current_page))
            current_page = [line]
            current_line_count = line_count
        else:
            current_page.append(line)
            current_line_count += line_count
    
    # Ajouter la dernière page
    if current_page:
        pages.append('\n'.join(current_page))
    
    return pages


def add_page_numbers(pages: List[str], start_number: int = 1, position: str = "bottom") -> List[str]:
    """Ajoute des numéros de page"""
    numbered_pages = []
    total_pages = len(pages)
    
    for i, page in enumerate(pages, start_number):
        if position == "top":
            header = f"Page {i} / {total_pages}\n{'-' * 50}\n\n"
            numbered_page = header + page
        else:  # bottom
            footer = f"\n\n{'-' * 50}\nPage {i} / {total_pages}"
            numbered_page = page + footer
        
        numbered_pages.append(numbered_page)
    
    return numbered_pages


def format_legal_list(items: List[str], style: str = "dash", indent: int = 0) -> str:
    """Formate une liste selon les conventions juridiques"""
    formatted_items = []
    indent_str = "  " * indent
    
    for i, item in enumerate(items, 1):
        if style == "dash":
            prefix = "- "
        elif style == "bullet":
            prefix = "• "
        elif style == "number":
            prefix = f"{i}. "
        elif style == "letter":
            prefix = f"{_to_letter(i)}. "
        elif style == "roman":
            prefix = f"{_to_roman(i).lower()}. "
        else:
            prefix = ""
        
        formatted_items.append(f"{indent_str}{prefix}{item}")
    
    return "\n".join(formatted_items)


def format_signature_block(
    signatories: List[Dict[str, str]], 
    date_location: str = None,
    include_date: bool = True
) -> str:
    """Crée un bloc de signatures"""
    lines = []
    
    # Date et lieu
    if include_date:
        from .date_time import format_legal_date
        date_str = format_legal_date(datetime.now())
        if date_location:
            lines.append(f"Fait à {date_location}, {date_str}")
        else:
            lines.append(f"Fait {date_str}")
        lines.append("")
    
    # Signatures
    if len(signatories) == 1:
        # Une seule signature centrée
        lines.append("")
        lines.append("")
        lines.append("_" * 30)
        lines.append(signatories[0].get('name', ''))
        if signatories[0].get('title'):
            lines.append(signatories[0]['title'])
    else:
        # Plusieurs signatures en colonnes
        lines.append("")
        lines.append("")
        
        # Ligne de signatures
        sig_line = "    ".join(["_" * 25 for _ in signatories])
        lines.append(sig_line)
        
        # Noms
        names = []
        for sig in signatories:
            name = sig.get('name', '')
            # Centrer le nom sous la ligne
            name = name.center(25)
            names.append(name)
        lines.append("    ".join(names))
        
        # Titres si présents
        if any(sig.get('title') for sig in signatories):
            titles = []
            for sig in signatories:
                title = sig.get('title', '')
                title = title.center(25)
                titles.append(title)
            lines.append("    ".join(titles))
    
    return "\n".join(lines)


def format_annex_reference(annex_number: int, title: str) -> str:
    """Formate une référence d'annexe"""
    return f"ANNEXE {annex_number} : {title}"


def create_document_footer(
    doc_type: str,
    page_current: int = None,
    page_total: int = None,
    reference: str = None
) -> str:
    """Crée un pied de page pour un document"""
    footer_parts = []
    
    if reference:
        footer_parts.append(f"Réf: {reference}")
    
    footer_parts.append(doc_type)
    
    if page_current and page_total:
        footer_parts.append(f"Page {page_current}/{page_total}")
    
    return " - ".join(footer_parts)
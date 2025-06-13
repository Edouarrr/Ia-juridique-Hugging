# utils/document_formatter.py
"""Utilitaires pour le formatage de documents juridiques"""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import streamlit as st

from modules.dataclasses import (
    LetterheadTemplate,
    DocumentJuridique,
    Partie
)

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
    Pour la démo, retourne le contenu en bytes
    """
    
    # Simuler la création d'un document Word
    # En production, ceci utiliserait python-docx pour créer un vrai .docx
    
    formatted_content = f"""
    DOCUMENT WORD SIMULÉ
    ====================
    
    Police: {style_config.get('font', 'Times New Roman')}
    Taille: {style_config.get('font_size', 12)}pt
    Interligne: {style_config.get('line_spacing', '1.5')}
    
    -------------------
    
    {content}
    
    -------------------
    
    [Ce serait un vrai document Word en production]
    """
    
    return formatted_content.encode('utf-8')

def format_legal_citations(text: str) -> str:
    """Formate les citations juridiques selon les conventions"""
    
    # Formater les références de jurisprudence
    patterns = [
        # Cour de cassation
        (r'\bCass\.?\s*', 'Cass. '),
        (r'\b(civ|crim|com|soc)\.?\s*(\d)', r'\1. \2'),
        
        # Conseil d'État
        (r'\bCE\b', 'CE'),
        (r'\bConseil d\'Etat\b', 'Conseil d\'État'),
        
        # Articles
        (r'\bart\.?\s*', 'art. '),
        (r'\barticles?\s+', 'art. '),
        
        # Autres
        (r'\bc\.\s*', 'c. '),  # contre
        (r'\bp\.\s*', 'p. '),  # page
        (r'\bn°\s*', 'n° '),  # numéro
    ]
    
    formatted_text = text
    for pattern, replacement in patterns:
        formatted_text = re.sub(pattern, replacement, formatted_text, flags=re.IGNORECASE)
    
    return formatted_text

def apply_legal_numbering(sections: List[str], style: str = "roman") -> List[str]:
    """Applique une numérotation juridique aux sections"""
    
    numbered_sections = []
    
    for i, section in enumerate(sections, 1):
        if style == "roman":
            number = _to_roman(i)
        elif style == "letter":
            number = chr(ord('A') + i - 1) if i <= 26 else f"A{chr(ord('A') + (i - 27))}"
        else:  # numeric
            number = str(i)
        
        numbered_sections.append(f"{number}. {section}")
    
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

def format_party_designation(partie: Partie, phase: str = "instruction") -> str:
    """Formate la désignation d'une partie selon la phase procédurale"""
    
    designation = partie.nom
    
    if partie.type == "personne_morale":
        # Ajouter la forme juridique
        if partie.forme_juridique:
            designation = f"{partie.forme_juridique} {designation}"
        
        # Ajouter le numéro d'immatriculation
        if partie.numero_immatriculation:
            designation += f", immatriculée au RCS sous le n° {partie.numero_immatriculation}"
    
    # Ajouter l'adresse
    if partie.adresse:
        designation += f", {partie.adresse}"
    
    # Ajouter la représentation
    if partie.representant:
        designation += f", représentée par {partie.representant}"
    
    # Ajouter l'avocat
    if partie.avocat:
        designation += f", ayant pour avocat {partie.avocat}"
    
    return designation

def format_date_juridique(date: datetime, include_day_name: bool = False) -> str:
    """Formate une date au format juridique français"""
    
    mois_fr = [
        '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
    ]
    
    jours_fr = [
        'lundi', 'mardi', 'mercredi', 'jeudi', 
        'vendredi', 'samedi', 'dimanche'
    ]
    
    if include_day_name:
        jour_semaine = jours_fr[date.weekday()]
        return f"le {jour_semaine} {date.day} {mois_fr[date.month]} {date.year}"
    else:
        return f"le {date.day} {mois_fr[date.month]} {date.year}"

def create_document_header(doc: DocumentJuridique) -> str:
    """Crée l'en-tête d'un document juridique"""
    
    header_lines = []
    
    # Numéro de référence
    if doc.numero_reference:
        header_lines.append(f"N° {doc.numero_reference}")
    
    # Type de document
    header_lines.append(doc.type_document.upper())
    
    # Date
    if doc.date_document:
        header_lines.append(format_date_juridique(doc.date_document))
    
    # Juridiction
    if doc.juridiction:
        header_lines.append(doc.juridiction)
    
    return "\n".join(header_lines)

def format_legal_amount(amount: float, currency: str = "€") -> str:
    """Formate un montant selon les conventions juridiques"""
    
    # Formater avec espaces comme séparateurs de milliers
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    
    # Ajouter la devise
    if currency == "€":
        return f"{formatted} euros"
    else:
        return f"{formatted} {currency}"

def clean_legal_text(text: str) -> str:
    """Nettoie un texte juridique en préservant la mise en forme"""
    
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    # Corriger la ponctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])(\w)', r'\1 \2', text)
    
    # Corriger les guillemets
    text = re.sub(r'"\s*([^"]+)\s*"', r'« \1 »', text)
    
    # Préserver les sauts de paragraphe
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def highlight_legal_terms(text: str, terms: List[str]) -> str:
    """Surligne les termes juridiques importants"""
    
    highlighted = text
    
    for term in terms:
        # Créer un pattern case-insensitive avec limites de mots
        pattern = rf'\b{re.escape(term)}\b'
        
        # Remplacer avec mise en évidence
        highlighted = re.sub(
            pattern,
            f'**{term}**',
            highlighted,
            flags=re.IGNORECASE
        )
    
    return highlighted

def create_table_of_contents(sections: List[Dict[str, Any]]) -> str:
    """Crée une table des matières"""
    
    toc_lines = ["TABLE DES MATIÈRES", "=" * 30, ""]
    
    for i, section in enumerate(sections, 1):
        # Numéro et titre
        indent = "  " * (section.get('level', 1) - 1)
        number = _to_roman(i) if section.get('level', 1) == 1 else str(i)
        
        line = f"{indent}{number}. {section['title']}"
        
        # Ajouter le numéro de page si disponible
        if 'page' in section:
            # Calculer les points de suite
            dots = "." * (50 - len(line))
            line += f" {dots} {section['page']}"
        
        toc_lines.append(line)
    
    return "\n".join(toc_lines)

def split_into_pages(text: str, lines_per_page: int = 50) -> List[str]:
    """Divise un texte en pages"""
    
    lines = text.split('\n')
    pages = []
    
    for i in range(0, len(lines), lines_per_page):
        page_lines = lines[i:i + lines_per_page]
        pages.append('\n'.join(page_lines))
    
    return pages

def add_page_numbers(pages: List[str], start_number: int = 1) -> List[str]:
    """Ajoute des numéros de page"""
    
    numbered_pages = []
    
    for i, page in enumerate(pages, start_number):
        # Ajouter le numéro en bas de page
        numbered_page = page + f"\n\n{'-' * 50}\nPage {i}"
        numbered_pages.append(numbered_page)
    
    return numbered_pages
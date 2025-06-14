# utils/formatters.py
"""
Fonctions de formatage pour l'application juridique
"""
import locale
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

# Essayer de définir la locale française
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    except:
        # Si la locale française n'est pas disponible, on continue avec la locale par défaut
        pass

def format_date(date_obj: Union[datetime, date, str], format_str: str = "%d/%m/%Y") -> str:
    """
    Formate une date selon le format spécifié.
    
    Args:
        date_obj: L'objet date à formater (datetime, date ou string)
        format_str: Le format de sortie (par défaut JJ/MM/AAAA)
        
    Returns:
        La date formatée en string
    """
    if not date_obj:
        return ""
    
    # Si c'est déjà une string, essayer de la parser
    if isinstance(date_obj, str):
        try:
            # Essayer différents formats courants
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                try:
                    date_obj = datetime.strptime(date_obj, fmt)
                    break
                except ValueError:
                    continue
            else:
                # Si aucun format ne marche, retourner la string originale
                return date_obj
        except:
            return date_obj
    
    # Formater la date
    try:
        return date_obj.strftime(format_str)
    except:
        return str(date_obj)

def format_date_long(date_obj: Union[datetime, date, str]) -> str:
    """
    Formate une date en format long (ex: 15 janvier 2024).
    
    Args:
        date_obj: L'objet date à formater
        
    Returns:
        La date en format long
    """
    if not date_obj:
        return ""
    
    # Convertir en datetime si nécessaire
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
    elif isinstance(date_obj, date) and not isinstance(date_obj, datetime):
        date_obj = datetime.combine(date_obj, datetime.min.time())
    
    # Noms des mois en français
    mois_fr = [
        "", "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ]
    
    try:
        jour = date_obj.day
        mois = mois_fr[date_obj.month]
        annee = date_obj.year
        return f"{jour} {mois} {annee}"
    except:
        return format_date(date_obj)

def format_datetime(dt_obj: Union[datetime, str], 
                   include_seconds: bool = False) -> str:
    """
    Formate une date et heure.
    
    Args:
        dt_obj: L'objet datetime à formater
        include_seconds: Inclure les secondes ou non
        
    Returns:
        La date et heure formatées
    """
    if not dt_obj:
        return ""
    
    if include_seconds:
        format_str = "%d/%m/%Y %H:%M:%S"
    else:
        format_str = "%d/%m/%Y %H:%M"
    
    return format_date(dt_obj, format_str)

def format_currency(amount: Union[float, int, str], 
                   currency: str = "EUR",
                   decimal_places: int = 2) -> str:
    """
    Formate un montant monétaire.
    
    Args:
        amount: Le montant à formater
        currency: La devise (EUR par défaut)
        decimal_places: Nombre de décimales
        
    Returns:
        Le montant formaté
    """
    if amount is None:
        return ""
    
    # Convertir en float si nécessaire
    try:
        if isinstance(amount, str):
            # Nettoyer la string (enlever espaces, remplacer virgule par point)
            amount = amount.strip().replace(',', '.').replace(' ', '')
        amount = float(amount)
    except (ValueError, TypeError):
        return str(amount)
    
    # Formater avec le bon nombre de décimales
    formatted = f"{amount:,.{decimal_places}f}"
    
    # Remplacer les séparateurs pour le format français
    formatted = formatted.replace(',', ' ').replace('.', ',')
    
    # Ajouter le symbole de devise
    if currency == "EUR":
        return f"{formatted} €"
    elif currency == "USD":
        return f"${formatted}"
    else:
        return f"{formatted} {currency}"

def format_percentage(value: Union[float, int, str], 
                     decimal_places: int = 2) -> str:
    """
    Formate un pourcentage.
    
    Args:
        value: La valeur à formater (entre 0 et 100)
        decimal_places: Nombre de décimales
        
    Returns:
        Le pourcentage formaté
    """
    if value is None:
        return ""
    
    try:
        value = float(value)
        return f"{value:.{decimal_places}f} %"
    except (ValueError, TypeError):
        return str(value)

def format_phone(phone: str, country: str = "FR") -> str:
    """
    Formate un numéro de téléphone.
    
    Args:
        phone: Le numéro à formater
        country: Le code pays (FR par défaut)
        
    Returns:
        Le numéro formaté
    """
    if not phone:
        return ""
    
    # Nettoyer le numéro (garder seulement les chiffres)
    phone_digits = re.sub(r'\D', '', phone)
    
    if country == "FR":
        # Format français
        if len(phone_digits) == 10:
            # Format: 01 23 45 67 89
            return ' '.join([phone_digits[i:i+2] for i in range(0, 10, 2)])
        elif len(phone_digits) == 11 and phone_digits.startswith('33'):
            # Format international: +33 1 23 45 67 89
            return f"+33 {phone_digits[2]} " + ' '.join([phone_digits[i:i+2] for i in range(3, 11, 2)])
    
    # Si le format n'est pas reconnu, retourner tel quel
    return phone

def format_case_number(number: str) -> str:
    """
    Formate un numéro de dossier juridique.
    
    Args:
        number: Le numéro à formater
        
    Returns:
        Le numéro formaté
    """
    if not number:
        return ""
    
    # Nettoyer le numéro
    number = str(number).strip()
    
    # Détecter le format et formater en conséquence
    # Format RG : 20/12345
    if '/' in number and len(number.split('/')) == 2:
        parts = number.split('/')
        return f"RG {parts[0]}/{parts[1]}"
    
    return number

def format_name(first_name: str = "", last_name: str = "", 
                title: str = "", format_type: str = "full") -> str:
    """
    Formate un nom de personne.
    
    Args:
        first_name: Prénom
        last_name: Nom de famille
        title: Titre (M., Mme, Me, etc.)
        format_type: Type de format ("full", "initials", "last_only")
        
    Returns:
        Le nom formaté
    """
    parts = []
    
    if title:
        parts.append(title)
    
    if format_type == "full":
        if first_name:
            parts.append(first_name.strip().title())
        if last_name:
            parts.append(last_name.strip().upper())
    elif format_type == "initials":
        if first_name:
            parts.append(f"{first_name[0].upper()}.")
        if last_name:
            parts.append(last_name.strip().upper())
    elif format_type == "last_only":
        if last_name:
            parts.append(last_name.strip().upper())
    
    return " ".join(parts)

def format_address(street: str = "", postal_code: str = "", 
                  city: str = "", country: str = "") -> str:
    """
    Formate une adresse postale.
    
    Args:
        street: Rue et numéro
        postal_code: Code postal
        city: Ville
        country: Pays
        
    Returns:
        L'adresse formatée sur plusieurs lignes
    """
    lines = []
    
    if street:
        lines.append(street.strip())
    
    city_line = []
    if postal_code:
        city_line.append(postal_code.strip())
    if city:
        city_line.append(city.strip().upper())
    
    if city_line:
        lines.append(" ".join(city_line))
    
    if country and country.upper() != "FRANCE":
        lines.append(country.strip().upper())
    
    return "\n".join(lines)

def format_duration(minutes: int) -> str:
    """
    Formate une durée en heures et minutes.
    
    Args:
        minutes: Nombre de minutes
        
    Returns:
        La durée formatée
    """
    if not minutes or minutes < 0:
        return "0 min"
    
    hours = minutes // 60
    mins = minutes % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if mins > 0 or hours == 0:
        parts.append(f"{mins}min")
    
    return " ".join(parts)

def format_file_path(path: str, max_length: int = 50) -> str:
    """
    Formate un chemin de fichier pour l'affichage.
    
    Args:
        path: Le chemin complet
        max_length: Longueur maximale
        
    Returns:
        Le chemin formaté (tronqué si nécessaire)
    """
    if not path:
        return ""
    
    if len(path) <= max_length:
        return path
    
    # Garder le début et la fin
    parts = path.split('/')
    if len(parts) > 2:
        return f"{parts[0]}/.../{parts[-1]}"
    else:
        # Tronquer au milieu
        start = path[:max_length//2 - 2]
        end = path[-(max_length//2 - 2):]
        return f"{start}...{end}"

def format_list_items(items: list, separator: str = ", ", 
                     last_separator: str = " et ") -> str:
    """
    Formate une liste d'éléments en texte.
    
    Args:
        items: Liste d'éléments
        separator: Séparateur entre éléments
        last_separator: Séparateur avant le dernier élément
        
    Returns:
        La liste formatée en texte
    """
    if not items:
        return ""
    
    items = [str(item) for item in items if item]
    
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]}{last_separator}{items[1]}"
    else:
        return separator.join(items[:-1]) + last_separator + items[-1]

def format_legal_reference(type_ref: str, number: str, 
                          date_ref: Optional[Union[datetime, date, str]] = None) -> str:
    """
    Formate une référence juridique.
    
    Args:
        type_ref: Type de référence (Cass., CA, TGI, etc.)
        number: Numéro de la décision
        date_ref: Date de la décision
        
    Returns:
        La référence formatée
    """
    parts = [type_ref]
    
    if date_ref:
        parts.append(format_date(date_ref))
    
    if number:
        parts.append(f"n° {number}")
    
    return ", ".join(parts)

# ========== FONCTIONS ÉTENDUES ==========

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
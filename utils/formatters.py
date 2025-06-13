# utils/formatters.py
"""
Fonctions de formatage pour l'application juridique
"""
from datetime import datetime, date
from typing import Union, Optional, Any
import locale
import re

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
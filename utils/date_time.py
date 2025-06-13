# utils/date_time.py
"""
Fonctions de gestion des dates et du temps
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union, Optional


# Mois français
MOIS_FR = [
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
]

JOURS_FR = [
    'lundi', 'mardi', 'mercredi', 'jeudi', 
    'vendredi', 'samedi', 'dimanche'
]

MONTHS_FR = {
    'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
    'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
    'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
}


def format_date(date: Union[datetime, str], format: str = "%d/%m/%Y") -> str:
    """Formate une date de manière cohérente"""
    if isinstance(date, str):
        # Essayer de parser la date
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                date = datetime.strptime(date, fmt)
                break
            except:
                continue
        else:
            return date  # Retourner tel quel si parsing échoue
    
    if isinstance(date, datetime):
        return date.strftime(format)
    
    return str(date)


def format_legal_date(date: Union[datetime, str], include_day_name: bool = False) -> str:
    """Formate une date au format juridique français"""
    if isinstance(date, str):
        # Essayer de parser la date
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                date = datetime.strptime(date, fmt)
                break
            except:
                continue
        else:
            return date
    
    if isinstance(date, datetime):
        if include_day_name:
            day_name = JOURS_FR[date.weekday()]
            return f"{day_name} {date.day} {MOIS_FR[date.month - 1]} {date.year}"
        else:
            return f"{date.day} {MOIS_FR[date.month - 1]} {date.year}"
    
    return str(date)


def format_date_juridique(date: datetime, include_day_name: bool = False) -> str:
    """Formate une date au format juridique français (alias)"""
    return format_legal_date(date, include_day_name)


def format_duration(seconds: int) -> str:
    """Formate une durée en format lisible"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"


def extract_dates(text: str) -> List[Dict[str, Any]]:
    """Extrait les dates d'un texte avec leur contexte"""
    dates = []
    
    # Patterns pour différents formats
    date_patterns = [
        # Format JJ/MM/AAAA ou JJ-MM-AAAA
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', 'dmy'),
        # Format AAAA/MM/JJ ou AAAA-MM-JJ
        (r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b', 'ymd'),
        # Format JJ mois AAAA
        (r'\b(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})\b', 'dmy_text'),
        # Format mois AAAA
        (r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})\b', 'my_text')
    ]
    
    for pattern, format_type in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                if format_type == 'dmy':
                    day, month, year = match.groups()
                    date_obj = datetime(int(year), int(month), int(day))
                
                elif format_type == 'ymd':
                    year, month, day = match.groups()
                    date_obj = datetime(int(year), int(month), int(day))
                
                elif format_type == 'dmy_text':
                    day, month_text, year = match.groups()
                    month = MONTHS_FR.get(month_text.lower(), 1)
                    date_obj = datetime(int(year), month, int(day))
                
                elif format_type == 'my_text':
                    month_text, year = match.groups()
                    month = MONTHS_FR.get(month_text.lower(), 1)
                    date_obj = datetime(int(year), month, 1)
                
                # Extraire le contexte
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                dates.append({
                    'date': date_obj,
                    'text': match.group(0),
                    'context': context,
                    'position': match.start()
                })
                
            except (ValueError, KeyError):
                continue
    
    # Trier par date
    dates.sort(key=lambda x: x['date'])
    
    return dates


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse une date depuis une chaîne"""
    # Formats à essayer
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d %B %Y',
        '%B %Y'
    ]
    
    # Remplacer les mois français
    for fr_month, month_num in MONTHS_FR.items():
        date_str = date_str.replace(fr_month, str(month_num))
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None


def get_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """Retourne une liste de dates entre deux dates"""
    dates = []
    current = start_date
    
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates


def is_business_day(date: datetime) -> bool:
    """Vérifie si une date est un jour ouvré"""
    # 0 = Lundi, 6 = Dimanche
    return date.weekday() < 5


def get_next_business_day(date: datetime) -> datetime:
    """Retourne le prochain jour ouvré"""
    next_day = date + timedelta(days=1)
    
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    
    return next_day


def calculate_business_days(start_date: datetime, end_date: datetime) -> int:
    """Calcule le nombre de jours ouvrés entre deux dates"""
    days = 0
    current = start_date
    
    while current <= end_date:
        if is_business_day(current):
            days += 1
        current += timedelta(days=1)
    
    return days


def add_business_days(date: datetime, days: int) -> datetime:
    """Ajoute un nombre de jours ouvrés à une date"""
    current = date
    remaining_days = days
    
    while remaining_days > 0:
        current += timedelta(days=1)
        if is_business_day(current):
            remaining_days -= 1
    
    return current


def format_relative_date(date: datetime) -> str:
    """Formate une date de manière relative (il y a X jours, etc.)"""
    now = datetime.now()
    delta = now - date
    
    if delta.days == 0:
        if delta.seconds < 3600:
            minutes = delta.seconds // 60
            return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            hours = delta.seconds // 3600
            return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    elif delta.days == 1:
        return "hier"
    elif delta.days < 7:
        return f"il y a {delta.days} jours"
    elif delta.days < 30:
        weeks = delta.days // 7
        return f"il y a {weeks} semaine{'s' if weeks > 1 else ''}"
    elif delta.days < 365:
        months = delta.days // 30
        return f"il y a {months} mois"
    else:
        years = delta.days // 365
        return f"il y a {years} an{'s' if years > 1 else ''}"


def get_quarter(date: datetime) -> str:
    """Retourne le trimestre d'une date"""
    quarter = (date.month - 1) // 3 + 1
    return f"T{quarter} {date.year}"


def get_week_number(date: datetime) -> int:
    """Retourne le numéro de semaine d'une date"""
    return date.isocalendar()[1]
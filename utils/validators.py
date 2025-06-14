# utils/validators.py
"""
Validateurs et fonctions de vérification
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def validate_siren(siren: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un numéro SIREN (9 chiffres)
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Nettoyer le SIREN
    siren = re.sub(r'[^0-9]', '', siren)
    
    if len(siren) != 9:
        return False, "Le SIREN doit contenir exactement 9 chiffres"
    
    if not siren.isdigit():
        return False, "Le SIREN ne doit contenir que des chiffres"
    
    # Validation par l'algorithme de Luhn
    total = 0
    for i, digit in enumerate(siren):
        if i % 2 == 0:  # Position paire (en partant de 0)
            value = int(digit) * 2
            if value > 9:
                value = value - 9
            total += value
        else:
            total += int(digit)
    
    if total % 10 != 0:
        return False, "Le SIREN n'est pas valide (échec du contrôle de Luhn)"
    
    return True, None


def validate_siret(siret: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un numéro SIRET (14 chiffres)
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Nettoyer le SIRET
    siret = re.sub(r'[^0-9]', '', siret)
    
    if len(siret) != 14:
        return False, "Le SIRET doit contenir exactement 14 chiffres"
    
    # Vérifier le SIREN (9 premiers chiffres)
    siren = siret[:9]
    is_valid_siren, siren_error = validate_siren(siren)
    if not is_valid_siren:
        return False, f"SIREN invalide: {siren_error}"
    
    # Validation par l'algorithme de Luhn sur tout le SIRET
    total = 0
    for i, digit in enumerate(siret):
        if i % 2 == 1:  # Position impaire (en partant de 0)
            value = int(digit) * 2
            if value > 9:
                value = value - 9
            total += value
        else:
            total += int(digit)
    
    if total % 10 != 0:
        return False, "Le SIRET n'est pas valide (échec du contrôle de Luhn)"
    
    return True, None


def validate_iban(iban: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un IBAN français
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Nettoyer l'IBAN
    iban = re.sub(r'[^A-Z0-9]', '', iban.upper())
    
    # Vérifier le format français
    if not iban.startswith('FR'):
        return False, "L'IBAN doit commencer par FR pour un compte français"
    
    if len(iban) != 27:
        return False, "L'IBAN français doit contenir 27 caractères"
    
    # Vérifier que les caractères 3-4 sont des chiffres
    if not iban[2:4].isdigit():
        return False, "Les caractères de contrôle doivent être des chiffres"
    
    # Validation du modulo 97
    # Déplacer les 4 premiers caractères à la fin
    rearranged = iban[4:] + iban[:4]
    
    # Convertir les lettres en chiffres (A=10, B=11, ..., Z=35)
    numeric_iban = ''
    for char in rearranged:
        if char.isdigit():
            numeric_iban += char
        else:
            numeric_iban += str(ord(char) - ord('A') + 10)
    
    # Calculer le modulo 97
    if int(numeric_iban) % 97 != 1:
        return False, "L'IBAN n'est pas valide (échec du contrôle modulo 97)"
    
    return True, None


def validate_phone_number(phone: str, country: str = 'FR') -> Tuple[bool, Optional[str]]:
    """
    Valide un numéro de téléphone
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Nettoyer le numéro
    phone = re.sub(r'[^0-9+]', '', phone)
    
    if country == 'FR':
        # Formats acceptés: 
        # 0123456789
        # +33123456789
        # 0033123456789
        
        if phone.startswith('+33'):
            phone = '0' + phone[3:]
        elif phone.startswith('0033'):
            phone = '0' + phone[4:]
        
        if not re.match(r'^0[1-9][0-9]{8}$', phone):
            return False, "Le numéro de téléphone français doit contenir 10 chiffres et commencer par 0"
        
        return True, None
    
    return False, f"Validation non implémentée pour le pays {country}"


def validate_postal_code(postal_code: str, country: str = 'FR') -> Tuple[bool, Optional[str]]:
    """
    Valide un code postal
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if country == 'FR':
        # Code postal français: 5 chiffres
        if not re.match(r'^[0-9]{5}$', postal_code):
            return False, "Le code postal français doit contenir exactement 5 chiffres"
        
        # Vérifier que le département existe (01-95, 2A, 2B, 971-976)
        dept = postal_code[:2]
        if dept == '20':
            return True, None  # Corse
        
        dept_num = int(dept)
        if not (1 <= dept_num <= 95 or dept_num in [97]):
            return False, f"Le département {dept} n'existe pas"
        
        return True, None
    
    return False, f"Validation non implémentée pour le pays {country}"


def validate_legal_form(forme_juridique: str) -> Tuple[bool, Optional[str]]:
    """
    Valide une forme juridique d'entreprise
    
    Returns:
        Tuple (is_valid, error_message)
    """
    formes_valides = [
        'SA', 'SAS', 'SASU', 'SARL', 'EURL', 'SNC', 'SCS', 'SCA',
        'GIE', 'GEIE', 'SEL', 'SELARL', 'SELAFA', 'SELAS', 'SELCA',
        'SCI', 'SCPI', 'SCP', 'SCM', 'GAEC', 'EARL', 'EIRL',
        'Auto-entrepreneur', 'Micro-entreprise', 'EI', 'Association'
    ]
    
    forme_upper = forme_juridique.upper().strip()
    
    if forme_upper not in [f.upper() for f in formes_valides]:
        return False, f"Forme juridique '{forme_juridique}' non reconnue"
    
    return True, None


def validate_case_number(numero: str, juridiction: str = "") -> Tuple[bool, Optional[str]]:
    """
    Valide un numéro de dossier/affaire
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Formats courants:
    # RG 20/12345
    # N° 2020/123
    # 20-12.345
    
    # Nettoyer le numéro
    numero = numero.strip()
    
    if not numero:
        return False, "Le numéro de dossier ne peut pas être vide"
    
    # Pattern général: doit contenir au moins des chiffres
    if not re.search(r'\d', numero):
        return False, "Le numéro de dossier doit contenir au moins des chiffres"
    
    # Patterns spécifiques selon la juridiction
    if juridiction:
        juridiction_upper = juridiction.upper()
        
        if 'RG' in juridiction_upper or 'RG' in numero.upper():
            # Format RG: RG 20/12345 ou 20/12345
            if not re.match(r'^(RG\s+)?\d{2,4}/\d+$', numero, re.IGNORECASE):
                return False, "Format RG invalide (attendu: RG AA/NNNNN)"
        
        elif 'PARQUET' in juridiction_upper:
            # Format parquet: P.20.123.456789
            if not re.match(r'^P\.\d{2}\.\d{3}\.\d+$', numero):
                return False, "Format parquet invalide (attendu: P.AA.NNN.NNNNNN)"
    
    return True, None


def validate_infraction_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un code d'infraction
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Codes du Code pénal: ex. 311-1, 432-11
    if re.match(r'^\d{3}-\d{1,2}$', code):
        return True, None
    
    # Codes avec lettres: ex. L.123-4, R.625-1
    if re.match(r'^[LRD]\.\d{3}-\d{1,2}$', code, re.IGNORECASE):
        return True, None
    
    # Codes NATINF (7 chiffres)
    if re.match(r'^\d{7}$', code):
        return True, None
    
    return False, "Format de code d'infraction non reconnu"


def validate_lawyer_bar_number(numero: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un numéro d'avocat au barreau
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Format: lettres suivies de chiffres (ex: P1234, A567)
    if not re.match(r'^[A-Z]{1,3}\d{3,6}$', numero.upper()):
        return False, "Le numéro de barreau doit commencer par 1-3 lettres suivies de 3-6 chiffres"
    
    return True, None


def validate_document_reference(reference: str) -> Tuple[bool, Optional[str]]:
    """
    Valide une référence de document juridique
    
    Returns:
        Tuple (is_valid, error_message)
    """
    # Ne doit pas être vide
    if not reference or not reference.strip():
        return False, "La référence ne peut pas être vide"
    
    # Longueur maximale
    if len(reference) > 100:
        return False, "La référence est trop longue (maximum 100 caractères)"
    
    # Caractères autorisés: lettres, chiffres, tirets, underscores, slashes, points
    if not re.match(r'^[a-zA-Z0-9_\-/\.\s]+$', reference):
        return False, "La référence contient des caractères non autorisés"
    
    return True, None


def validate_date_range(start_date: datetime, end_date: datetime) -> Tuple[bool, Optional[str]]:
    """
    Valide une plage de dates
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if start_date > end_date:
        return False, "La date de début doit être antérieure à la date de fin"
    
    # Vérifier que les dates ne sont pas trop éloignées (ex: 50 ans)
    diff = end_date - start_date
    if diff.days > 365 * 50:
        return False, "La plage de dates ne peut pas dépasser 50 ans"
    
    return True, None


def validate_amount(amount: float, min_amount: float = 0, max_amount: float = None) -> Tuple[bool, Optional[str]]:
    """
    Valide un montant monétaire
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if amount < min_amount:
        return False, f"Le montant doit être supérieur ou égal à {min_amount}"
    
    if max_amount and amount > max_amount:
        return False, f"Le montant doit être inférieur ou égal à {max_amount}"
    
    # Vérifier le nombre de décimales (max 2 pour les euros)
    if round(amount, 2) != amount:
        return False, "Le montant ne peut avoir plus de 2 décimales"
    
    return True, None


def validate_percentage(value: float) -> Tuple[bool, Optional[str]]:
    """
    Valide un pourcentage
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not 0 <= value <= 100:
        return False, "Le pourcentage doit être entre 0 et 100"
    
    return True, None


def validate_juridiction_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Valide le nom d'une juridiction
    
    Returns:
        Tuple (is_valid, error_message)
    """
    juridictions_valides = [
        'Tribunal judiciaire', 'Tribunal de commerce', 'Conseil de prud\'hommes',
        'Tribunal correctionnel', 'Tribunal de police', 'Cour d\'appel',
        'Cour de cassation', 'Conseil d\'État', 'Tribunal administratif',
        'Cour administrative d\'appel', 'Cour d\'assises', 'Juge d\'instruction',
        'Juge des libertés et de la détention', 'Parquet'
    ]
    
    # Normaliser pour la comparaison
    name_normalized = name.strip().lower()
    
    for juridiction in juridictions_valides:
        if juridiction.lower() in name_normalized:
            return True, None
    
    return False, f"Juridiction '{name}' non reconnue"


# Fonction utilitaire pour valider plusieurs champs
def validate_fields(fields: Dict[str, Any], validators: Dict[str, callable]) -> Dict[str, str]:
    """
    Valide plusieurs champs avec leurs validateurs respectifs
    
    Args:
        fields: Dict des champs à valider {nom: valeur}
        validators: Dict des validateurs {nom: fonction_validation}
    
    Returns:
        Dict des erreurs {nom: message_erreur}
    """
    errors = {}
    
    for field_name, field_value in fields.items():
        if field_name in validators:
            is_valid, error_msg = validators[field_name](field_value)
            if not is_valid:
                errors[field_name] = error_msg
    
    return errors
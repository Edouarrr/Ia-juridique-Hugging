# utils/constants.py
"""
Constantes utilisées dans l'application juridique
"""

# ========== TYPES DE DOCUMENTS ==========
DOCUMENT_TYPES = {
    'conclusions': 'Conclusions',
    'plainte': 'Plainte',
    'assignation': 'Assignation',
    'requete': 'Requête',
    'memoire': 'Mémoire',
    'ordonnance': 'Ordonnance',
    'jugement': 'Jugement',
    'arret': 'Arrêt',
    'citation': 'Citation',
    'pv': 'Procès-verbal',
    'expertise': 'Rapport d\'expertise',
    'courrier': 'Courrier',
    'contrat': 'Contrat',
    'convention': 'Convention',
    'protocole': 'Protocole d\'accord'
}

# ========== PHASES PROCÉDURALES ==========
PHASES_PROCEDURE = {
    'pre_contentieux': 'Pré-contentieux',
    'mise_en_etat': 'Mise en état',
    'instruction': 'Instruction',
    'jugement': 'Jugement',
    'appel': 'Appel',
    'cassation': 'Cassation',
    'execution': 'Exécution'
}

# ========== JURIDICTIONS ==========
JURIDICTIONS = {
    # Ordre judiciaire civil
    'tj': 'Tribunal judiciaire',
    'tc': 'Tribunal de commerce',
    'cph': 'Conseil de prud\'hommes',
    'tgi': 'Tribunal de grande instance (ancien)',
    
    # Ordre judiciaire pénal
    'tp': 'Tribunal de police',
    'tcorr': 'Tribunal correctionnel',
    'ca_corr': 'Cour d\'assises',
    'ji': 'Juge d\'instruction',
    'jld': 'Juge des libertés et de la détention',
    
    # Cours d'appel
    'ca': 'Cour d\'appel',
    
    # Cour de cassation
    'ccass': 'Cour de cassation',
    'ccass_civ': 'Cour de cassation - Chambre civile',
    'ccass_com': 'Cour de cassation - Chambre commerciale',
    'ccass_soc': 'Cour de cassation - Chambre sociale',
    'ccass_crim': 'Cour de cassation - Chambre criminelle',
    
    # Ordre administratif
    'ta': 'Tribunal administratif',
    'caa': 'Cour administrative d\'appel',
    'ce': 'Conseil d\'État',
    
    # Autres
    'cc': 'Conseil constitutionnel',
    'cjue': 'Cour de justice de l\'Union européenne',
    'cedh': 'Cour européenne des droits de l\'homme'
}

# ========== INFRACTIONS PRINCIPALES ==========
INFRACTIONS_COURANTES = {
    # Atteintes aux biens
    '311-1': 'Vol',
    '313-1': 'Escroquerie',
    '314-1': 'Abus de confiance',
    '321-1': 'Recel',
    '322-1': 'Destruction de biens',
    
    # Atteintes aux personnes
    '221-1': 'Meurtre',
    '222-1': 'Tortures et actes de barbarie',
    '222-7': 'Violences',
    '222-33': 'Harcèlement',
    '226-1': 'Atteinte à la vie privée',
    
    # Infractions économiques
    '432-11': 'Corruption passive',
    '433-1': 'Corruption active',
    '441-1': 'Faux et usage de faux',
    'L241-3': 'Abus de biens sociaux',
    'L242-6': 'Distribution de dividendes fictifs',
    
    # Blanchiment
    '324-1': 'Blanchiment',
    '324-2': 'Blanchiment aggravé'
}

# ========== FORMES JURIDIQUES ==========
FORMES_JURIDIQUES = {
    # Sociétés commerciales
    'SA': 'Société Anonyme',
    'SAS': 'Société par Actions Simplifiée',
    'SASU': 'Société par Actions Simplifiée Unipersonnelle',
    'SARL': 'Société à Responsabilité Limitée',
    'EURL': 'Entreprise Unipersonnelle à Responsabilité Limitée',
    'SNC': 'Société en Nom Collectif',
    'SCS': 'Société en Commandite Simple',
    'SCA': 'Société en Commandite par Actions',
    
    # Sociétés civiles
    'SCI': 'Société Civile Immobilière',
    'SCP': 'Société Civile Professionnelle',
    'SCM': 'Société Civile de Moyens',
    'SCPI': 'Société Civile de Placement Immobilier',
    
    # Sociétés d'exercice libéral
    'SEL': 'Société d\'Exercice Libéral',
    'SELARL': 'Société d\'Exercice Libéral à Responsabilité Limitée',
    'SELAFA': 'Société d\'Exercice Libéral à Forme Anonyme',
    'SELAS': 'Société d\'Exercice Libéral par Actions Simplifiée',
    
    # Autres
    'GIE': 'Groupement d\'Intérêt Économique',
    'GEIE': 'Groupement Européen d\'Intérêt Économique',
    'Association': 'Association loi 1901',
    'Fondation': 'Fondation',
    'EI': 'Entreprise Individuelle',
    'EIRL': 'Entreprise Individuelle à Responsabilité Limitée'
}

# ========== QUALITÉS DES PARTIES ==========
QUALITES_PARTIES = {
    'demandeur': 'Demandeur',
    'defendeur': 'Défendeur',
    'partie_civile': 'Partie civile',
    'prevenu': 'Prévenu',
    'accuse': 'Accusé',
    'temoin': 'Témoin',
    'expert': 'Expert',
    'intervenant': 'Intervenant volontaire',
    'appele_en_garantie': 'Appelé en garantie',
    'tiers': 'Tiers'
}

# ========== BARREAUX FRANÇAIS PRINCIPAUX ==========
BARREAUX = {
    'paris': 'Barreau de Paris',
    'marseille': 'Barreau de Marseille',
    'lyon': 'Barreau de Lyon',
    'toulouse': 'Barreau de Toulouse',
    'nice': 'Barreau de Nice',
    'nantes': 'Barreau de Nantes',
    'strasbourg': 'Barreau de Strasbourg',
    'montpellier': 'Barreau de Montpellier',
    'bordeaux': 'Barreau de Bordeaux',
    'lille': 'Barreau de Lille',
    'rennes': 'Barreau de Rennes',
    'versailles': 'Barreau de Versailles'
}

# ========== DEVISES ==========
CURRENCIES = {
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'USD': {'symbol': '$', 'name': 'Dollar américain'},
    'GBP': {'symbol': '£', 'name': 'Livre sterling'},
    'CHF': {'symbol': 'CHF', 'name': 'Franc suisse'},
    'JPY': {'symbol': '¥', 'name': 'Yen japonais'}
}

# ========== LIMITES ET SEUILS ==========
LIMITS = {
    'max_file_size_mb': 50,
    'max_document_length': 1000000,  # caractères
    'max_search_results': 100,
    'max_timeline_events': 500,
    'max_parties': 50,
    'cache_duration_hours': 24,
    'session_timeout_minutes': 120
}

# ========== FORMATS DE FICHIERS ACCEPTÉS ==========
ACCEPTED_FILE_TYPES = {
    'documents': ['.pdf', '.doc', '.docx', '.odt', '.rtf', '.txt'],
    'spreadsheets': ['.xls', '.xlsx', '.ods', '.csv'],
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
    'emails': ['.eml', '.msg'],
    'archives': ['.zip', '.rar', '.7z']
}

# ========== MESSAGES D'ERREUR STANDARDS ==========
ERROR_MESSAGES = {
    'file_too_large': "Le fichier est trop volumineux (limite: {limit} MB)",
    'invalid_format': "Format de fichier non supporté",
    'missing_field': "Le champ '{field}' est obligatoire",
    'invalid_date': "Date invalide",
    'invalid_reference': "Référence invalide",
    'connection_error': "Erreur de connexion au service",
    'permission_denied': "Accès refusé",
    'not_found': "Élément introuvable",
    'generic_error': "Une erreur inattendue s'est produite"
}

# ========== PATTERNS REGEX ==========
REGEX_PATTERNS = {
    'case_number': r'^(RG\s+)?\d{2,4}/\d+$',
    'siren': r'^\d{9}$',
    'siret': r'^\d{14}$',
    'phone_fr': r'^0[1-9][0-9]{8}$',
    'postal_code_fr': r'^[0-9]{5}$',
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'iban_fr': r'^FR\d{2}[A-Z0-9]{23}$',
    'article_code': r'^\d{3}-\d{1,2}$',
    'law_reference': r'loi\s+n°\s*\d{4}-\d+\s+du\s+\d{1,2}\s+\w+\s+\d{4}'
}

# ========== ICÔNES ==========
ICONS = {
    'document': '📄',
    'folder': '📁',
    'search': '🔍',
    'calendar': '📅',
    'person': '👤',
    'company': '🏢',
    'law': '⚖️',
    'court': '🏛️',
    'warning': '⚠️',
    'success': '✅',
    'error': '❌',
    'info': 'ℹ️',
    'email': '📧',
    'phone': '📞',
    'location': '📍',
    'money': '💰',
    'time': '⏰',
    'edit': '✏️',
    'delete': '🗑️',
    'download': '⬇️',
    'upload': '⬆️',
    'print': '🖨️',
    'save': '💾'
}

# ========== COULEURS THÈME ==========
COLORS = {
    'primary': '#1a237e',
    'secondary': '#283593',
    'success': '#2e7d32',
    'warning': '#f57c00',
    'error': '#c62828',
    'info': '#0288d1',
    'light': '#f5f5f5',
    'dark': '#212121'
}

# ========== DÉPARTEMENTS FRANÇAIS ==========
DEPARTEMENTS = {
    '01': 'Ain', '02': 'Aisne', '03': 'Allier', '04': 'Alpes-de-Haute-Provence',
    '05': 'Hautes-Alpes', '06': 'Alpes-Maritimes', '07': 'Ardèche', '08': 'Ardennes',
    '09': 'Ariège', '10': 'Aube', '11': 'Aude', '12': 'Aveyron',
    '13': 'Bouches-du-Rhône', '14': 'Calvados', '15': 'Cantal', '16': 'Charente',
    '17': 'Charente-Maritime', '18': 'Cher', '19': 'Corrèze', '2A': 'Corse-du-Sud',
    '2B': 'Haute-Corse', '21': 'Côte-d\'Or', '22': 'Côtes-d\'Armor', '23': 'Creuse',
    '24': 'Dordogne', '25': 'Doubs', '26': 'Drôme', '27': 'Eure',
    '28': 'Eure-et-Loir', '29': 'Finistère', '30': 'Gard', '31': 'Haute-Garonne',
    '32': 'Gers', '33': 'Gironde', '34': 'Hérault', '35': 'Ille-et-Vilaine',
    '36': 'Indre', '37': 'Indre-et-Loire', '38': 'Isère', '39': 'Jura',
    '40': 'Landes', '41': 'Loir-et-Cher', '42': 'Loire', '43': 'Haute-Loire',
    '44': 'Loire-Atlantique', '45': 'Loiret', '46': 'Lot', '47': 'Lot-et-Garonne',
    '48': 'Lozère', '49': 'Maine-et-Loire', '50': 'Manche', '51': 'Marne',
    '52': 'Haute-Marne', '53': 'Mayenne', '54': 'Meurthe-et-Moselle', '55': 'Meuse',
    '56': 'Morbihan', '57': 'Moselle', '58': 'Nièvre', '59': 'Nord',
    '60': 'Oise', '61': 'Orne', '62': 'Pas-de-Calais', '63': 'Puy-de-Dôme',
    '64': 'Pyrénées-Atlantiques', '65': 'Hautes-Pyrénées', '66': 'Pyrénées-Orientales',
    '67': 'Bas-Rhin', '68': 'Haut-Rhin', '69': 'Rhône', '70': 'Haute-Saône',
    '71': 'Saône-et-Loire', '72': 'Sarthe', '73': 'Savoie', '74': 'Haute-Savoie',
    '75': 'Paris', '76': 'Seine-Maritime', '77': 'Seine-et-Marne', '78': 'Yvelines',
    '79': 'Deux-Sèvres', '80': 'Somme', '81': 'Tarn', '82': 'Tarn-et-Garonne',
    '83': 'Var', '84': 'Vaucluse', '85': 'Vendée', '86': 'Vienne',
    '87': 'Haute-Vienne', '88': 'Vosges', '89': 'Yonne', '90': 'Territoire de Belfort',
    '91': 'Essonne', '92': 'Hauts-de-Seine', '93': 'Seine-Saint-Denis', '94': 'Val-de-Marne',
    '95': 'Val-d\'Oise', '971': 'Guadeloupe', '972': 'Martinique', '973': 'Guyane',
    '974': 'La Réunion', '976': 'Mayotte'
}

# ========== SUGGESTIONS LÉGALES ==========

LEGAL_SUGGESTIONS = [
    'Plainte pour abus de biens sociaux',
    'Assignation en référé',
    'Contrat de bail commercial',
    'Consultation jurisprudence récente',
    'Procédure de CJIP',
    "Qualification juridique des faits",
    "Éléments constitutifs de l'infraction",
    "Responsabilité pénale",
    "Responsabilité civile",
    "Nullités de procédure",
    "Circonstances aggravantes",
    "Prescription applicable",
    "Jurisprudence pertinente",
    "Sanctions encourues",
    "Moyens de défense"
]


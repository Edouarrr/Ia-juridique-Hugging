# Module Utils - Documentation

## Vue d'ensemble

Le module `utils` contient l'ensemble des fonctions utilitaires pour l'application juridique. Il est organisé en plusieurs sous-modules spécialisés pour une meilleure maintenabilité.

Toutes les fonctions sont exportées directement via `utils/__init__.py`. L'ancien fichier `exports.py` a été supprimé.

## Structure du module

```
utils/
├── __init__.py          # Point d'entrée du module
├── session.py           # Gestion de la session Streamlit
├── text_processing.py   # Traitement et analyse de texte
├── date_time.py         # Gestion des dates et du temps
├── document_utils.py    # Utilitaires pour les documents
├── legal_utils.py       # Fonctions spécifiques au juridique
├── file_utils.py        # Gestion des fichiers
├── cache_manager.py     # Système de cache performant
├── formatters.py        # Formatage de documents juridiques
├── styles.py            # Styles CSS pour Streamlit
├── validators.py        # Validateurs de données
├── constants.py         # Constantes de l'application
├── test_utils.py        # Tests unitaires simples
└── README.md            # Cette documentation
```

> **Note** : toutes les fonctions exportées sont désormais accessibles
> directement via `utils`. L'ancien fichier `utils/exports.py` a été
> supprimé.

## Utilisation

### Import simple

```python
# Import des fonctions les plus courantes
from utils import (
    initialize_session_state,
    clean_key,
    format_legal_date,
    get_cache,
    load_custom_css
)
```

### Import par module

```python
# Import de modules spécifiques
from utils.text_processing import extract_entities, calculate_text_similarity
from utils import format_duration, is_business_day
from utils.legal_utils import extract_legal_references, analyze_query_intent
from utils.validators import validate_siren, validate_iban
```

## Modules détaillés

### 1. session.py - Gestion de session
Gère l'état de la session Streamlit.

**Fonctions principales :**
- `initialize_session_state()` : Initialise toutes les variables de session
- `get_session_value(key, default)` : Récupère une valeur de session
- `set_session_value(key, value)` : Définit une valeur de session
- `add_to_history(action, details)` : Ajoute une action à l'historique
- `toggle_favorite(item_id, item_type)` : Gère les favoris

### 2. text_processing.py - Traitement de texte
Fonctions pour analyser et traiter le texte.

**Fonctions principales :**
- `clean_key(text)` : Nettoie une chaîne pour l'utiliser comme clé
- `extract_entities(text)` : Extrait personnes, organisations, lieux
- `calculate_text_similarity(text1, text2)` : Calcule la similarité (0-1)
- `chunk_text(text, size, overlap)` : Divise un texte en chunks
- `highlight_text(text, keywords)` : Surligne des mots-clés (HTML)

### 3. date_time.py - Dates et temps
Gestion complète des dates en français.

**Fonctions principales :**
- `format_legal_date(date, include_day_name)` : Format juridique français
- `extract_dates(text)` : Extrait toutes les dates d'un texte
- `is_business_day(date)` : Vérifie si jour ouvré
- `calculate_business_days(start, end)` : Calcule les jours ouvrés
- `format_relative_date(date)` : Format relatif ("il y a 2 jours")

### 4. document_utils.py - Documents
Utilitaires pour la gestion des documents.

**Fonctions principales :**
- `generate_document_id(title, source)` : Génère un ID unique
- `merge_documents(docs)` : Fusionne plusieurs documents
- `extract_document_metadata(content)` : Extrait les métadonnées
- `create_document_index(docs)` : Crée un index de documents
- `compare_documents(doc1, doc2)` : Compare deux documents

### 5. legal_utils.py - Juridique
Fonctions spécialisées pour le domaine juridique.

**Fonctions principales :**
- `extract_legal_references(text)` : Extrait articles, jurisprudences, lois
- `analyze_query_intent(query)` : Analyse l'intention d'une requête
- `categorize_legal_document(content)` : Catégorise un document
- `extract_parties(text)` : Extrait demandeurs/défendeurs
- `format_legal_amount(amount)` : Formate un montant (1 234,56 euros)

### 6. file_utils.py - Fichiers
Gestion sécurisée des fichiers.

**Fonctions principales :**
- `sanitize_filename(filename)` : Nettoie un nom de fichier
- `format_file_size(bytes)` : Formate une taille (1.5 MB)
- `get_file_icon(filename)` : Retourne l'icône appropriée
- `is_valid_email(email)` : Valide une adresse email
- `organize_files_by_type(files)` : Organise par type

### 7. cache_manager.py - Cache
Système de cache performant avec TTL.

**Classes principales :**
- `CacheJuridique` : Gestionnaire de cache principal
- `CacheActesJuridiques` : Cache spécialisé pour les actes

**Décorateurs :**
- `@cache_result(cache_type, key_generator)` : Met en cache les résultats
- `@cache_streamlit(cache_type, show_spinner)` : Cache avec spinner Streamlit

**Configuration des durées :**
```python
CACHE_DURATION = {
    'acte_genere': timedelta(hours=24),
    'analyse_requete': timedelta(hours=1),
    'enrichissement': timedelta(days=7),
    'jurisprudence': timedelta(days=30),
    'template': timedelta(days=90)
}
```

### 8. formatters.py - Formatage
Formatage de documents juridiques.

**Fonctions principales :**
- `create_letterhead_from_template(template)` : Crée un en-tête
- `apply_legal_numbering(sections, style)` : Numérotation (I, II, III...)
- `format_party_designation(partie, phase)` : Formate une partie
- `create_table_of_contents(sections)` : Crée une table des matières
- `format_signature_block(signatories)` : Bloc de signatures

### 9. validators.py - Validation
Validateurs pour données françaises.

**Validateurs disponibles :**
- `validate_siren(siren)` : Valide un SIREN (algo Luhn)
- `validate_siret(siret)` : Valide un SIRET
- `validate_iban(iban)` : Valide un IBAN français
- `validate_phone_number(phone)` : Valide un téléphone
- `validate_postal_code(code)` : Valide un code postal
- `validate_case_number(numero)` : Valide un numéro d'affaire

### 10. styles.py - Styles CSS
Styles CSS personnalisés pour Streamlit.

**Utilisation :**
```python
from utils import load_custom_css

# Dans votre app Streamlit
load_custom_css()
```

**Fonctions de création HTML :**
- `create_card(title, content, icon, type)` : Crée une carte
- `create_timeline_item(date, title, desc)` : Élément de timeline
- `create_search_result(title, content, source, score)` : Résultat de recherche
- `create_alert(message, type, icon)` : Message d'alerte

### 11. constants.py - Constantes
Toutes les constantes de l'application.

**Constantes disponibles :**
- `DOCUMENT_TYPES` : Types de documents juridiques
- `JURIDICTIONS` : Liste des juridictions
- `INFRACTIONS_COURANTES` : Codes d'infractions
- `FORMES_JURIDIQUES` : Formes juridiques d'entreprises
- `REGEX_PATTERNS` : Patterns de validation
- `ICONS` : Mapping des icônes
- `ERROR_MESSAGES` : Messages d'erreur standard

## Tests

Pour lancer les tests :

```bash
python utils/test_utils.py
```

Les tests couvrent :
- Traitement de texte
- Gestion des dates
- Fonctions juridiques
- Gestion des fichiers
- Validateurs
- Système de cache
- Formatters

## Exemples d'utilisation

### Exemple 1 : Analyser une requête utilisat
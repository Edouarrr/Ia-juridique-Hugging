# modules/redaction.py
"""
Fichier de redirection pour maintenir la compatibilité
avec les imports existants qui utilisent modules.redaction
"""

# Réexporter tout depuis modules.redaction_unified
from modules.redaction_unified import *

# Note: Ce fichier permet de maintenir la compatibilité avec le code existant
# qui utilise "from modules.redaction import ..."
# tout en ayant le fichier principal dans modules/redaction_unified.py
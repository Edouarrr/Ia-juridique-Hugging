# models/dataclasses.py
"""
Fichier de redirection pour maintenir la compatibilité
avec les imports existants qui utilisent models.dataclasses
"""

# Réexporter tout depuis modules.dataclasses
from modules.dataclasses import *

# Note: Ce fichier permet de maintenir la compatibilité avec le code existant
# qui utilise "from models.dataclasses import ..." 
# tout en ayant le fichier principal dans modules/dataclasses.py
"""
Modules métier pour SPIC 2.0
Fonctionnalités principales de suivi d'opérations MOA
"""

from .suivi_operations import *
from .gestion_journal import *
from .suivi_financier import *
from .gestion_risques import *
from .exports import *

__version__ = "2.0.0"
__modules__ = [
    "suivi_operations",
    "gestion_journal", 
    "suivi_financier",
    "gestion_risques",
    "exports"
]
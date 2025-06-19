# -*- coding: utf-8 -*-
"""
Configuration centralisée pour SPIC 2.0 - VERSION REFACTORISÉE
Gestion des opérations immobilières avec 113 phases exactes
Compatible OPCOPILOT pour connexion future
"""

from typing import Dict, List, Any
import datetime

# ============================================================================
# TYPES D'OPÉRATIONS
# ============================================================================

TYPES_OPERATIONS = [
    "OPP",      # Opérations Propres - 45 phases
    "VEFA",     # Vente en État Futur d'Achèvement - 22 phases
    "AMO",      # Assistance à Maîtrise d'Ouvrage - 22 phases
    "MANDAT"    # Opérations en Mandat - 24 phases
]

# ============================================================================
# PHASES EXACTES PAR TYPE D'OPÉRATION (113 PHASES TOTALES)
# ============================================================================

PHASES_PAR_TYPE = {
    "OPP": [
        # Phase Études et Faisabilité (1-8)
        {"id": 1, "nom": "Études préalables", "ordre": 1, "duree_min": 15, "duree_max": 30, "principale": True},
        {"id": 2, "nom": "Faisabilité technique", "ordre": 2, "duree_min": 10, "duree_max": 21, "principale": False},
        {"id": 3, "nom": "Faisabilité financière", "ordre": 3, "duree_min": 7, "duree_max": 14, "principale": False},
        {"id": 4, "nom": "Études de sol", "ordre": 4, "duree_min": 21, "duree_max": 45, "principale": True},
        {"id": 5, "nom": "Levés topographiques", "ordre": 5, "duree_min": 10, "duree_max": 15, "principale": False},
        {"id": 6, "nom": "Diagnostic technique", "ordre": 6, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 7, "nom": "Programme architectural", "ordre": 7, "duree_min": 30, "duree_max": 45, "principale": True},
        {"id": 8, "nom": "Validation programme", "ordre": 8, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Conception (9-16)
        {"id": 9, "nom": "Esquisse (ESQ)", "ordre": 9, "duree_min": 21, "duree_max": 30, "principale": True},
        {"id": 10, "nom": "Avant-projet sommaire (APS)", "ordre": 10, "duree_min": 30, "duree_max": 45, "principale": True},
        {"id": 11, "nom": "Avant-projet définitif (APD)", "ordre": 11, "duree_min": 45, "duree_max": 60, "principale": True},
        {"id": 12, "nom": "Projet (PRO)", "ordre": 12, "duree_min": 60, "duree_max": 90, "principale": True},
        {"id": 13, "nom": "Dossier de consultation (DCE)", "ordre": 13, "duree_min": 30, "duree_max": 45, "principale": True},
        {"id": 14, "nom": "Études d'exécution (EXE)", "ordre": 14, "duree_min": 45, "duree_max": 75, "principale": False},
        {"id": 15, "nom": "Visa plans", "ordre": 15, "duree_min": 7, "duree_max": 14, "principale": False},
        {"id": 16, "nom": "Plans conformes", "ordre": 16, "duree_min": 14, "duree_max": 21, "principale": False},
        
        # Phase Administrative (17-24)
        {"id": 17, "nom": "Dépôt permis de construire", "ordre": 17, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 18, "nom": "Instruction permis", "ordre": 18, "duree_min": 60, "duree_max": 120, "principale": True},
        {"id": 19, "nom": "Purge recours permis", "ordre": 19, "duree_min": 60, "duree_max": 90, "principale": True},
        {"id": 20, "nom": "Déclaration ouverture chantier", "ordre": 20, "duree_min": 1, "duree_max": 7, "principale": False},
        {"id": 21, "nom": "Autorisations voirie", "ordre": 21, "duree_min": 30, "duree_max": 60, "principale": False},
        {"id": 22, "nom": "Raccordements réseaux", "ordre": 22, "duree_min": 45, "duree_max": 90, "principale": False},
        {"id": 23, "nom": "Assurances chantier", "ordre": 23, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 24, "nom": "Validation administrative", "ordre": 24, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Consultation (25-32)
        {"id": 25, "nom": "Consultation entreprises", "ordre": 25, "duree_min": 45, "duree_max": 60, "principale": True},
        {"id": 26, "nom": "Analyse offres", "ordre": 26, "duree_min": 15, "duree_max": 30, "principale": True},
        {"id": 27, "nom": "Négociation", "ordre": 27, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 28, "nom": "Attribution marchés", "ordre": 28, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 29, "nom": "Signature marchés", "ordre": 29, "duree_min": 15, "duree_max": 30, "principale": True},
        {"id": 30, "nom": "Ordres de service", "ordre": 30, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 31, "nom": "Planning travaux", "ordre": 31, "duree_min": 14, "duree_max": 21, "principale": False},
        {"id": 32, "nom": "Préparation chantier", "ordre": 32, "duree_min": 21, "duree_max": 30, "principale": False},
        
        # Phase Travaux (33-40)
        {"id": 33, "nom": "Installation chantier", "ordre": 33, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 34, "nom": "Gros œuvre", "ordre": 34, "duree_min": 120, "duree_max": 240, "principale": True},
        {"id": 35, "nom": "Second œuvre", "ordre": 35, "duree_min": 90, "duree_max": 180, "principale": True},
        {"id": 36, "nom": "Corps d'état techniques", "ordre": 36, "duree_min": 60, "duree_max": 120, "principale": True},
        {"id": 37, "nom": "Finitions", "ordre": 37, "duree_min": 45, "duree_max": 90, "principale": True},
        {"id": 38, "nom": "VRD", "ordre": 38, "duree_min": 30, "duree_max": 60, "principale": False},
        {"id": 39, "nom": "Espaces verts", "ordre": 39, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 40, "nom": "Nettoyage chantier", "ordre": 40, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Réception (41-45)
        {"id": 41, "nom": "Réception provisoire", "ordre": 41, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 42, "nom": "Levée réserves", "ordre": 42, "duree_min": 30, "duree_max": 90, "principale": True},
        {"id": 43, "nom": "Réception définitive", "ordre": 43, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 44, "nom": "Garanties", "ordre": 44, "duree_min": 365, "duree_max": 3650, "principale": False},
        {"id": 45, "nom": "Clôture opération", "ordre": 45, "duree_min": 15, "duree_max": 30, "principale": False}
    ],
    
    "VEFA": [
        # Phase Recherche (1-4)
        {"id": 46, "nom": "Recherche programme", "ordre": 1, "duree_min": 30, "duree_max": 90, "principale": True},
        {"id": 47, "nom": "Visite commerciale", "ordre": 2, "duree_min": 1, "duree_max": 7, "principale": False},
        {"id": 48, "nom": "Négociation prix", "ordre": 3, "duree_min": 7, "duree_max": 30, "principale": False},
        {"id": 49, "nom": "Validation choix", "ordre": 4, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Réservation (5-8)
        {"id": 50, "nom": "Contrat réservation", "ordre": 5, "duree_min": 1, "duree_max": 7, "principale": True},
        {"id": 51, "nom": "Versement réservation", "ordre": 6, "duree_min": 1, "duree_max": 3, "principale": True},
        {"id": 52, "nom": "Délai rétractation", "ordre": 7, "duree_min": 10, "duree_max": 10, "principale": True},
        {"id": 53, "nom": "Confirmation réservation", "ordre": 8, "duree_min": 1, "duree_max": 7, "principale": False},
        
        # Phase Financement (9-12)
        {"id": 54, "nom": "Montage financement", "ordre": 9, "duree_min": 30, "duree_max": 60, "principale": True},
        {"id": 55, "nom": "Accord banque", "ordre": 10, "duree_min": 15, "duree_max": 45, "principale": True},
        {"id": 56, "nom": "Conditions suspensives", "ordre": 11, "duree_min": 45, "duree_max": 90, "principale": True},
        {"id": 57, "nom": "Validation financement", "ordre": 12, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Contractuelle (13-16)
        {"id": 58, "nom": "Signature acte authentique", "ordre": 13, "duree_min": 1, "duree_max": 7, "principale": True},
        {"id": 59, "nom": "Appel fonds démarrage", "ordre": 14, "duree_min": 30, "duree_max": 60, "principale": True},
        {"id": 60, "nom": "Suivi avancement", "ordre": 15, "duree_min": 180, "duree_max": 365, "principale": True},
        {"id": 61, "nom": "Appels fonds périodiques", "ordre": 16, "duree_min": 30, "duree_max": 60, "principale": False},
        
        # Phase Livraison (17-22)
        {"id": 62, "nom": "Pré-livraison", "ordre": 17, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 63, "nom": "Réserves pré-livraison", "ordre": 18, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 64, "nom": "Livraison", "ordre": 19, "duree_min": 1, "duree_max": 7, "principale": True},
        {"id": 65, "nom": "Remise clés", "ordre": 20, "duree_min": 1, "duree_max": 1, "principale": True},
        {"id": 66, "nom": "Levée réserves", "ordre": 21, "duree_min": 30, "duree_max": 90, "principale": True},
        {"id": 67, "nom": "Garanties", "ordre": 22, "duree_min": 365, "duree_max": 3650, "principale": False}
    ],
    
    "AMO": [
        # Phase Mission (1-4)
        {"id": 68, "nom": "Définition mission", "ordre": 1, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 69, "nom": "Signature contrat AMO", "ordre": 2, "duree_min": 7, "duree_max": 21, "principale": True},
        {"id": 70, "nom": "Lancement mission", "ordre": 3, "duree_min": 1, "duree_max": 7, "principale": False},
        {"id": 71, "nom": "Équipe projet", "ordre": 4, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Diagnostic (5-8)
        {"id": 72, "nom": "Diagnostic existant", "ordre": 5, "duree_min": 15, "duree_max": 30, "principale": True},
        {"id": 73, "nom": "Analyse besoins", "ordre": 6, "duree_min": 15, "duree_max": 21, "principale": True},
        {"id": 74, "nom": "Étude faisabilité", "ordre": 7, "duree_min": 21, "duree_max": 30, "principale": True},
        {"id": 75, "nom": "Rapport diagnostic", "ordre": 8, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Programme (9-12)
        {"id": 76, "nom": "Élaboration programme", "ordre": 9, "duree_min": 30, "duree_max": 45, "principale": True},
        {"id": 77, "nom": "Validation programme", "ordre": 10, "duree_min": 14, "duree_max": 30, "principale": True},
        {"id": 78, "nom": "Enveloppe financière", "ordre": 11, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 79, "nom": "Planning prévisionnel", "ordre": 12, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Conception (13-16)
        {"id": 80, "nom": "Assistance conception", "ordre": 13, "duree_min": 60, "duree_max": 120, "principale": True},
        {"id": 81, "nom": "Validation études", "ordre": 14, "duree_min": 15, "duree_max": 30, "principale": True},
        {"id": 82, "nom": "Contrôle coûts", "ordre": 15, "duree_min": 30, "duree_max": 60, "principale": True},
        {"id": 83, "nom": "Optimisation projet", "ordre": 16, "duree_min": 15, "duree_max": 30, "principale": False},
        
        # Phase Consultation (17-20)
        {"id": 84, "nom": "Assistance consultation", "ordre": 17, "duree_min": 45, "duree_max": 60, "principale": True},
        {"id": 85, "nom": "Analyse offres", "ordre": 18, "duree_min": 15, "duree_max": 30, "principale": True},
        {"id": 86, "nom": "Négociation", "ordre": 19, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 87, "nom": "Attribution", "ordre": 20, "duree_min": 7, "duree_max": 14, "principale": True},
        
        # Phase Réalisation (21-22)
        {"id": 88, "nom": "Suivi travaux", "ordre": 21, "duree_min": 180, "duree_max": 730, "principale": True},
        {"id": 89, "nom": "Réception assistance", "ordre": 22, "duree_min": 15, "duree_max": 30, "principale": True}
    ],
    
    "MANDAT": [
        # Phase Mandat (1-4)
        {"id": 90, "nom": "Prospection mandat", "ordre": 1, "duree_min": 30, "duree_max": 90, "principale": True},
        {"id": 91, "nom": "Évaluation bien", "ordre": 2, "duree_min": 7, "duree_max": 14, "principale": True},
        {"id": 92, "nom": "Signature mandat", "ordre": 3, "duree_min": 1, "duree_max": 7, "principale": True},
        {"id": 93, "nom": "Enregistrement mandat", "ordre": 4, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Marketing (5-8)
        {"id": 94, "nom": "Photos/visite virtuelle", "ordre": 5, "duree_min": 1, "duree_max": 7, "principale": False},
        {"id": 95, "nom": "Annonces diffusion", "ordre": 6, "duree_min": 1, "duree_max": 3, "principale": True},
        {"id": 96, "nom": "Plaquette commerciale", "ordre": 7, "duree_min": 3, "duree_max": 7, "principale": False},
        {"id": 97, "nom": "Lancement commercial", "ordre": 8, "duree_min": 1, "duree_max": 1, "principale": False},
        
        # Phase Commercialisation (9-16)
        {"id": 98, "nom": "Visites prospects", "ordre": 9, "duree_min": 30, "duree_max": 180, "principale": True},
        {"id": 99, "nom": "Négociation prix", "ordre": 10, "duree_min": 7, "duree_max": 30, "principale": True},
        {"id": 100, "nom": "Accord verbal", "ordre": 11, "duree_min": 1, "duree_max": 7, "principale": True},
        {"id": 101, "nom": "Signature compromis", "ordre": 12, "duree_min": 7, "duree_max": 21, "principale": True},
        {"id": 102, "nom": "Conditions suspensives", "ordre": 13, "duree_min": 45, "duree_max": 90, "principale": True},
        {"id": 103, "nom": "Financement acquéreur", "ordre": 14, "duree_min": 45, "duree_max": 60, "principale": False},
        {"id": 104, "nom": "Diagnostics techniques", "ordre": 15, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 105, "nom": "Levée conditions", "ordre": 16, "duree_min": 7, "duree_max": 14, "principale": False},
        
        # Phase Finalisation (17-24)
        {"id": 106, "nom": "Préparation acte", "ordre": 17, "duree_min": 21, "duree_max": 45, "principale": True},
        {"id": 107, "nom": "Signature acte authentique", "ordre": 18, "duree_min": 1, "duree_max": 1, "principale": True},
        {"id": 108, "nom": "Remise clés", "ordre": 19, "duree_min": 1, "duree_max": 1, "principale": True},
        {"id": 109, "nom": "Commission mandataire", "ordre": 20, "duree_min": 1, "duree_max": 7, "principale": False},
        {"id": 110, "nom": "Régularisations", "ordre": 21, "duree_min": 15, "duree_max": 30, "principale": False},
        {"id": 111, "nom": "Suivi post-vente", "ordre": 22, "duree_min": 30, "duree_max": 90, "principale": False},
        {"id": 112, "nom": "Archivage dossier", "ordre": 23, "duree_min": 7, "duree_max": 14, "principale": False},
        {"id": 113, "nom": "Clôture mandat", "ordre": 24, "duree_min": 1, "duree_max": 7, "principale": False}
    ]
}

# ============================================================================
# STATUTS GLOBAUX DYNAMIQUES
# ============================================================================

STATUTS_OPERATIONS = {
    "EN_PREPARATION": {
        "libelle": "En préparation",
        "couleur": "#FFA500",
        "couleur_bg": "#FFF3E0",
        "icone": "🔄",
        "ordre": 1,
        "description": "Opération en cours de préparation",
        "css_class": "status-preparation"
    },
    "EN_COURS": {
        "libelle": "En cours",
        "couleur": "#4CAF50", 
        "couleur_bg": "#E8F5E8",
        "icone": "🚀",
        "ordre": 2,
        "description": "Opération active",
        "css_class": "status-active"
    },
    "EN_ATTENTE": {
        "libelle": "En attente",
        "couleur": "#FF9800",
        "couleur_bg": "#FFF3E0",
        "icone": "⏸️",
        "ordre": 3,
        "description": "Opération en pause",
        "css_class": "status-waiting"
    },
    "BLOQUE": {
        "libelle": "Bloqué",
        "couleur": "#F44336",
        "couleur_bg": "#FFEBEE",
        "icone": "🔒",
        "ordre": 4,
        "description": "Opération bloquée",
        "css_class": "status-blocked"
    },
    "TERMINE": {
        "libelle": "Terminé",
        "couleur": "#2196F3",
        "couleur_bg": "#E3F2FD",
        "icone": "✅",
        "ordre": 5,
        "description": "Opération terminée",
        "css_class": "status-completed"
    },
    "ANNULE": {
        "libelle": "Annulé",
        "couleur": "#9E9E9E",
        "couleur_bg": "#F5F5F5",
        "icone": "❌",
        "ordre": 6,
        "description": "Opération annulée",
        "css_class": "status-cancelled"
    }
}

# ============================================================================
# STATUTS DE PHASES
# ============================================================================

STATUTS_PHASES = {
    "NON_COMMENCE": {
        "libelle": "Non commencé", 
        "couleur": "#E0E0E0", 
        "couleur_bg": "#FAFAFA",
        "icone": "⭕",
        "progression": 0,
        "css_class": "phase-not-started"
    },
    "EN_COURS": {
        "libelle": "En cours", 
        "couleur": "#2196F3", 
        "couleur_bg": "#E3F2FD",
        "icone": "🔄",
        "progression": 50,
        "css_class": "phase-in-progress"
    },
    "TERMINE": {
        "libelle": "Terminé", 
        "couleur": "#4CAF50", 
        "couleur_bg": "#E8F5E8",
        "icone": "✅",
        "progression": 100,
        "css_class": "phase-completed"
    },
    "EN_RETARD": {
        "libelle": "En retard", 
        "couleur": "#FF5722", 
        "couleur_bg": "#FFF3E0",
        "icone": "⚠️",
        "progression": 25,
        "css_class": "phase-delayed"
    },
    "BLOQUE": {
        "libelle": "Bloqué", 
        "couleur": "#F44336", 
        "couleur_bg": "#FFEBEE",
        "icone": "🔒",
        "progression": 0,
        "css_class": "phase-blocked"
    }
}

# ============================================================================
# NIVEAUX DE RISQUE ET ALERTES
# ============================================================================

NIVEAUX_RISQUE = {
    "FAIBLE": {
        "libelle": "Faible", 
        "couleur": "#4CAF50", 
        "couleur_bg": "#E8F5E8",
        "icone": "🟢", 
        "score_min": 0,
        "score_max": 25,
        "css_class": "risk-low"
    },
    "MOYEN": {
        "libelle": "Moyen", 
        "couleur": "#FF9800", 
        "couleur_bg": "#FFF3E0",
        "icone": "🟡", 
        "score_min": 26,
        "score_max": 50,
        "css_class": "risk-medium"
    },
    "ELEVE": {
        "libelle": "Élevé", 
        "couleur": "#F44336", 
        "couleur_bg": "#FFEBEE",
        "icone": "🔴", 
        "score_min": 51,
        "score_max": 75,
        "css_class": "risk-high"
    },
    "CRITIQUE": {
        "libelle": "Critique", 
        "couleur": "#9C27B0", 
        "couleur_bg": "#F3E5F5",
        "icone": "🟣", 
        "score_min": 76,
        "score_max": 100,
        "css_class": "risk-critical"
    }
}

# ============================================================================
# TYPES D'ALERTES
# ============================================================================

TYPES_ALERTES = {
    "RETARD": {
        "libelle": "Retard", 
        "couleur": "#FF5722", 
        "couleur_bg": "#FFF3E0",
        "icone": "⏰",
        "priorite": 3,
        "css_class": "alert-delay"
    },
    "BUDGET": {
        "libelle": "Budget", 
        "couleur": "#F44336", 
        "couleur_bg": "#FFEBEE",
        "icone": "💰",
        "priorite": 4,
        "css_class": "alert-budget"
    },
    "TECHNIQUE": {
        "libelle": "Technique", 
        "couleur": "#FF9800", 
        "couleur_bg": "#FFF3E0",
        "icone": "⚙️",
        "priorite": 2,
        "css_class": "alert-technical"
    },
    "ADMINISTRATIF": {
        "libelle": "Administratif", 
        "couleur": "#9C27B0", 
        "couleur_bg": "#F3E5F5",
        "icone": "📋",
        "priorite": 2,
        "css_class": "alert-admin"
    },
    "COMMERCIAL": {
        "libelle": "Commercial", 
        "couleur": "#2196F3", 
        "couleur_bg": "#E3F2FD",
        "icone": "🏢",
        "priorite": 1,
        "css_class": "alert-commercial"
    },
    "JURIDIQUE": {
        "libelle": "Juridique", 
        "couleur": "#795548", 
        "couleur_bg": "#EFEBE9",
        "icone": "⚖️",
        "priorite": 4,
        "css_class": "alert-legal"
    }
}

# ============================================================================
# CONFIGURATION INTERFACE ET DESIGN
# ============================================================================

COULEURS_THEME = {
    "primary": "#1E88E5",
    "primary_light": "#64B5F6", 
    "primary_dark": "#1565C0",
    "secondary": "#26A69A",
    "secondary_light": "#80CBC4",
    "secondary_dark": "#00695C",
    "success": "#4CAF50",
    "success_light": "#81C784",
    "warning": "#FF9800",
    "warning_light": "#FFB74D",
    "error": "#F44336",
    "error_light": "#E57373",
    "info": "#2196F3",
    "info_light": "#64B5F6",
    "light": "#F5F5F5",
    "light_grey": "#EEEEEE",
    "dark": "#212121",
    "dark_grey": "#424242",
    "white": "#FFFFFF",
    "black": "#000000"
}

# Couleurs Timeline (progression type PowerPoint)
COULEURS_TIMELINE = [
    "#3498db",  # Bleu
    "#2ecc71",  # Vert  
    "#f39c12",  # Orange
    "#e74c3c",  # Rouge
    "#9b59b6",  # Violet
    "#1abc9c",  # Turquoise
    "#34495e",  # Gris foncé
    "#f1c40f"   # Jaune
]

# Configuration Layout Streamlit
LAYOUT_CONFIG = {
    "page_title": "SPIC 2.0 - Suivi Opérations MOA",
    "page_icon": "🏗️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        'Get Help': None,
        'Report a bug': None,
        'About': "SPIC 2.0 - Outil de suivi d'opérations MOA"
    }
}

# ============================================================================
# PARAMÈTRES MÉTIER ET SEUILS
# ============================================================================

SEUILS_ALERTES = {
    "retard_jours": 7,              # Alerte si retard > 7 jours
    "retard_critique_jours": 21,    # Critique si retard > 21 jours
    "budget_depassement_pct": 10,   # Alerte si dépassement > 10%
    "budget_critique_pct": 20,      # Critique si dépassement > 20%
    "phase_bloquee_jours": 14,      # Alerte si phase bloquée > 14 jours
    "score_risque_moyen": 50,       # Score risque moyen à partir de 50
    "score_risque_eleve": 70,       # Score risque élevé à partir de 70
    "score_risque_critique": 85,    # Score risque critique à partir de 85
    "rem_seuil_alerte": 15,         # Alerte REM si > 15% du budget
    "rem_seuil_critique": 25        # Critique REM si > 25% du budget
}

# Durées de cache Streamlit
DUREES_CACHE = {
    "courte": 300,      # 5 minutes - données fréquemment modifiées
    "moyenne": 900,     # 15 minutes - calculs intermédiaires
    "longue": 3600,     # 1 heure - données statiques
    "journaliere": 86400 # 24 heures - référentiels
}

# ============================================================================
# DOMAINES ET SECTEURS
# ============================================================================

DOMAINES_ACTIVITE = [
    "Logement social",
    "Logement libre", 
    "Résidentiel senior",
    "Équipements publics",
    "Tertiaire privé",
    "Tertiaire public",
    "Commercial",
    "Industriel",
    "Rénovation urbaine",
    "Aménagement"
]

# Secteur géographique = CHAMP LIBRE (pas de liste prédéfinie)
SECTEUR_GEOGRAPHIQUE_LIBRE = True  # Permet saisie libre dans l'interface


# ============================================================================
# FORMATS D'EXPORT ET TEMPLATES
# ============================================================================

FORMATS_EXPORT = {
    "excel": {
        "extension": ".xlsx", 
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "icone": "📊"
    },
    "word": {
        "extension": ".docx", 
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "icone": "📄"
    },
    "pdf": {
        "extension": ".pdf", 
        "mime": "application/pdf",
        "icone": "📑"
    },
    "csv": {
        "extension": ".csv", 
        "mime": "text/csv",
        "icone": "📋"
    }
}

TEMPLATES_EXPORT = {
    "rapport_operation": "templates/rapport_operation.docx",
    "tableau_bord": "templates/tableau_bord.xlsx", 
    "synthese_phases": "templates/synthese_phases.docx",
    "suivi_budget": "templates/suivi_budget.xlsx",
    "rapport_rem": "templates/rapport_rem.docx"
}

# ============================================================================
# CONFIGURATION BASE DE DONNÉES (COMPATIBLE OPCOPILOT)
# ============================================================================

DB_CONFIG = {
    "db_path": "data/spic_operations.db",
    "timeout": 30.0,
    "check_same_thread": False,
    "backup_enabled": True,
    "backup_interval_hours": 24,
    "max_connections": 10,
    "journal_mode": "WAL",  # Write-Ahead Logging pour performance
    "synchronous": "NORMAL"
}

# Tables partagées avec OPCOPILOT futur
TABLES_PARTAGEES_OPCOPILOT = [
    "operations",
    "phases_operations", 
    "journal_modifications",
    "alertes",
    "budgets",
    "intervenants"
]

# API Endpoints pour connexion future OPCOPILOT
API_ENDPOINTS = {
    "base_url": "http://localhost:8501/api/v1",
    "operations": "/operations",
    "phases": "/phases", 
    "journal": "/journal",
    "alertes": "/alertes",
    "sync": "/sync",
    "webhook": "/webhook"
}

# ============================================================================
# RÔLES ET PERMISSIONS UTILISATEURS
# ============================================================================

ROLES_UTILISATEURS = {
    "ADMIN": {
        "libelle": "Administrateur",
        "permissions": ["CREATE", "READ", "UPDATE", "DELETE", "EXPORT", "CONFIG"],
        "couleur": "#9C27B0"
    },
    "MANAGER": {
        "libelle": "Manager",
        "permissions": ["CREATE", "READ", "UPDATE", "EXPORT"],
        "couleur": "#2196F3"
    },
    "CHARGE_OPERATION": {
        "libelle": "Chargé d'opération", 
        "permissions": ["READ", "UPDATE", "EXPORT"],
        "couleur": "#4CAF50"
    },
    "CONSULTANT": {
        "libelle": "Consultant",
        "permissions": ["READ", "EXPORT"],
        "couleur": "#FF9800"
    }
}

# ============================================================================
# CONFIGURATION REM (RÉSULTAT EXCEPTIONNEL DE MISSION)
# ============================================================================

REM_CONFIG = {
    "periodes": ["Trimestriel", "Semestriel", "Annuel"],
    "seuils_pct": {
        "alerte": 15,       # 15% du budget
        "critique": 25      # 25% du budget  
    },
    "types_rem": [
        "Économies réalisées",
        "Plus-values foncières",
        "Optimisations techniques", 
        "Négociations commerciales",
        "Subventions obtenues",
        "Autres"
    ]
}

# ============================================================================
# CONFIGURATION TIMELINE ET VISUALISATIONS
# ============================================================================

TIMELINE_CONFIG = {
    "hauteur": 400,
    "couleurs_progression": COULEURS_TIMELINE,
    "afficher_alertes": True,
    "afficher_jalons": True,
    "style": "roadmap",  # roadmap, gantt, simple
    "animation": True,
    "responsive": True
}

GRAPHIQUES_CONFIG = {
    "theme": "plotly_white",
    "couleurs": COULEURS_TIMELINE,
    "police": "Arial",
    "taille_police": 12,
    "responsive": True,
    "toolbar": True
}

# ============================================================================
# MESSAGES ET LABELS INTERFACE
# ============================================================================

MESSAGES_UI = {
    "titre_app": "SPIC 2.0 - Suivi Professionnel d'Opérations de Construction",
    "sous_titre": "Outil de pilotage MOA intelligent et collaboratif",
    "menu_principal": "Navigation principale",
    "aucune_donnee": "Aucune donnée disponible",
    "chargement": "Chargement en cours...",
    "erreur_db": "Erreur de connexion à la base de données",
    "succes_sauvegarde": "Données sauvegardées avec succès",
    "erreur_sauvegarde": "Erreur lors de la sauvegarde",
    "confirmation_suppression": "Êtes-vous sûr de vouloir supprimer cet élément ?",
    "export_reussi": "Export généré avec succès",
    "calcul_en_cours": "Calcul des métriques en cours..."
}

# ============================================================================
# CRITÈRES CALCUL SCORE DE RISQUE
# ============================================================================

CRITERES_RISQUE = {
    "retard_phases": {
        "poids": 25,
        "seuils": {
            "faible": 0,     # 0-7 jours
            "moyen": 7,      # 7-21 jours  
            "eleve": 21,     # 21-45 jours
            "critique": 45   # > 45 jours
        }
    },
    "depassement_budget": {
        "poids": 30,
        "seuils": {
            "faible": 0,     # 0-5%
            "moyen": 5,      # 5-15%
            "eleve": 15,     # 15-25%
            "critique": 25   # > 25%
        }
    },
    "alertes_actives": {
        "poids": 20,
        "seuils": {
            "faible": 0,     # 0-2 alertes
            "moyen": 2,      # 2-5 alertes
            "eleve": 5,      # 5-10 alertes
            "critique": 10   # > 10 alertes
        }
    },
    "phases_bloquees": {
        "poids": 15,
        "seuils": {
            "faible": 0,     # 0 phase
            "moyen": 1,      # 1 phase
            "eleve": 2,      # 2 phases
            "critique": 3    # > 3 phases
        }
    },
    "avancement_global": {
        "poids": 10,
        "seuils": {
            "faible": 80,    # > 80% d'avancement
            "moyen": 60,     # 60-80%
            "eleve": 40,     # 40-60%
            "critique": 20   # < 40%
        }
    }
}

# ============================================================================
# CONFIGURATION NOTIFICATIONS
# ============================================================================

NOTIFICATIONS_CONFIG = {
    "enabled": True,
    "types": ["email", "interface"],
    "frequence": "quotidienne",  # quotidienne, hebdomadaire
    "seuils": {
        "alertes_critiques": True,
        "retards_importants": True, 
        "depassements_budget": True,
        "phases_bloquees": True
    }
}

# ============================================================================
# VERSION ET MÉTADONNÉES
# ============================================================================

APP_METADATA = {
    "version": "2.0.0",
    "date_version": "2024-12-18",
    "auteur": "SPIC Development Team",
    "description": "Outil de suivi professionnel d'opérations de construction MOA",
    "compatibilite_opcopilot": True,
    "base_donnees": "SQLite 3.x",
    "framework": "Streamlit 1.28+",
    "python_version": "3.8+"
}
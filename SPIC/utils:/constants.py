"""
Constantes métier spécialisées pour SPIC 2.0
Messages, formats, paramètres d'affichage
"""

# Messages interface utilisateur
UI_MESSAGES = {
    'loading': '⏳ Chargement en cours...',
    'no_data': '📋 Aucune donnée disponible',
    'success_save': '✅ Sauvegarde réussie',
    'error_save': '❌ Erreur lors de la sauvegarde',
    'confirm_delete': '⚠️ Confirmer la suppression ?',
    'export_success': '📥 Export généré avec succès',
    'calculation_progress': '🧮 Calcul en cours...',
    'access_denied': '🔒 Accès non autorisé',
    'invalid_data': '⚠️ Données invalides',
    'connection_error': '🔌 Erreur de connexion'
}

# Formats d'affichage
DISPLAY_FORMATS = {
    'currency': '€{:,.0f}',
    'percentage': '{:.1f}%',
    'duration_days': '{} jour(s)',
    'date_short': '%d/%m/%Y',
    'date_long': '%d %B %Y',
    'datetime': '%d/%m/%Y %H:%M'
}

# Paramètres graphiques Timeline
TIMELINE_PARAMS = {
    'height': 400,
    'margin': {'t': 50, 'b': 100, 'l': 100, 'r': 50},
    'font_size': 12,
    'marker_size': 15,
    'line_width': 6,
    'hover_template': '<b>%{text}</b><br>%{customdata}<extra></extra>'
}

# Seuils visuels
VISUAL_THRESHOLDS = {
    'progress_low': 30,
    'progress_medium': 70,
    'score_risk_medium': 50,
    'score_risk_high': 75,
    'budget_alert': 10,
    'budget_critical': 20
}

# Mappings statuts vers icônes
STATUS_ICONS = {
    'EN_PREPARATION': '🔄',
    'EN_COURS': '🚀', 
    'EN_ATTENTE': '⏸️',
    'BLOQUE': '🔒',
    'TERMINE': '✅',
    'ANNULE': '❌',
    'NON_COMMENCE': '⭕',
    'EN_RETARD': '⚠️'
}

# Configuration cache par type de données
CACHE_CONFIG = {
    'static_data': 3600,      # 1 heure - données statiques
    'operations': 900,        # 15 min - données opérations  
    'calculations': 300,      # 5 min - calculs
    'dashboard': 600,         # 10 min - métriques dashboard
    'timeline': 300,          # 5 min - données timeline
    'reports': 1800          # 30 min - rapports
}

# Limites et pagination
PAGINATION_LIMITS = {
    'operations_per_page': 20,
    'journal_entries': 50,
    'alerts_per_page': 25,
    'export_max_rows': 10000
}
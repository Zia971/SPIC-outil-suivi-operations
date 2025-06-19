"""
Utilitaires spécifiques base de données pour SPIC 2.0
Connexions optimisées, requêtes fréquentes, cache
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging
from .constants import CACHE_CONFIG, PAGINATION_LIMITS
import config

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Utilitaires pour optimiser les interactions avec la base de données"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    @st.cache_data(ttl=CACHE_CONFIG['operations'])
    def get_operations_for_selectbox(_self, user_id: str = None) -> Dict[str, str]:
        """Récupérer opérations pour selectbox (format {id: nom})"""
        try:
            operations = _self.db.get_all_operations(user_id)
            return {op['id']: f"{op['nom']} ({op['type_operation']})" 
                   for op in operations}
        except Exception as e:
            logger.error(f"Erreur récupération opérations selectbox: {e}")
            return {}
    
    @st.cache_data(ttl=CACHE_CONFIG['static_data'])
    def get_users_for_selectbox(_self) -> Dict[str, str]:
        """Récupérer utilisateurs pour selectbox"""
        try:
            with _self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, nom, prenom, role 
                    FROM utilisateurs_spic 
                    WHERE actif = 1 
                    ORDER BY nom, prenom
                """)
                users = cursor.fetchall()
                
            return {user['id']: f"{user['nom']} {user['prenom']} ({user['role']})" 
                   for user in users}
        except Exception as e:
            logger.error(f"Erreur récupération utilisateurs: {e}")
            return {}
    
    @st.cache_data(ttl=CACHE_CONFIG['operations'])
    def get_operations_dataframe(_self, user_id: str = None, 
                                filters: Dict = None) -> pd.DataFrame:
        """Récupérer opérations formatées pour affichage DataFrame"""
        try:
            operations = _self.db.get_all_operations(user_id)
            
            if not operations:
                return pd.DataFrame()
            
            # Convertir en DataFrame
            df = pd.DataFrame(operations)
            
            # Formatage colonnes
            if 'budget_initial' in df.columns:
                df['budget_initial'] = df['budget_initial'].fillna(0).astype(float)
                df['budget_initial_format'] = df['budget_initial'].apply(
                    lambda x: f"€{x:,.0f}" if x > 0 else "Non défini"
                )
            
            if 'date_debut' in df.columns:
                df['date_debut'] = pd.to_datetime(df['date_debut'], errors='coerce')
                df['date_debut_format'] = df['date_debut'].dt.strftime('%d/%m/%Y')
            
            # Appliquer filtres
            if filters:
                if filters.get('type_operation'):
                    df = df[df['type_operation'].isin(filters['type_operation'])]
                
                if filters.get('statut_global'):
                    df = df[df['statut_global'].isin(filters['statut_global'])]
                
                if filters.get('score_risque_min'):
                    df = df[df['score_risque'] >= filters['score_risque_min']]
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur création DataFrame opérations: {e}")
            return pd.DataFrame()
    
    def get_phases_dataframe(self, operation_id: str) -> pd.DataFrame:
        """Récupérer phases formatées pour affichage"""
        try:
            phases = self.db.get_phases_by_operation(operation_id)
            
            if not phases:
                return pd.DataFrame()
            
            df = pd.DataFrame(phases)
            
            # Formatage dates
            for col in ['date_debut_prevue', 'date_fin_prevue', 'date_debut_reelle', 'date_fin_reelle']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df[f"{col}_format"] = df[col].dt.strftime('%d/%m/%Y')
            
            # Calcul retards
            if 'date_fin_prevue' in df.columns:
                today = pd.Timestamp.now()
                df['en_retard'] = (
                    (df['date_fin_prevue'] < today) & 
                    (df['statut_phase'] != 'TERMINE')
                )
                df['jours_retard'] = (today - df['date_fin_prevue']).dt.days
                df['jours_retard'] = df['jours_retard'].where(df['en_retard'], 0)
            
            # Icônes statuts
            df['icone_statut'] = df['statut_phase'].map(
                lambda x: config.STATUTS_PHASES.get(x, {}).get('icone', '⭕')
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur DataFrame phases: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=CACHE_CONFIG['dashboard'])
    def get_dashboard_metrics(_self) -> Dict:
        """Métriques formatées pour dashboard"""
        try:
            metrics = _self.db.get_operations_dashboard()
            
            # Formatage pour affichage Streamlit
            formatted = {
                'total_operations': {
                    'value': metrics['statistiques']['total_operations'],
                    'label': 'Opérations Total'
                },
                'operations_actives': {
                    'value': metrics['statistiques']['operations_actives'],
                    'label': 'En Cours',
                    'delta': None
                },
                'score_risque_moyen': {
                    'value': round(metrics['statistiques']['score_risque_moyen'] or 0),
                    'label': 'Score Risque Moyen',
                    'delta': None
                },
                'budget_total': {
                    'value': f"€{(metrics['statistiques']['budget_total_actuel'] or 0):,.0f}",
                    'label': 'Budget Total Portefeuille'
                }
            }
            
            # Calcul variations budget
            budget_initial = metrics['statistiques']['budget_total_initial'] or 0
            budget_actuel = metrics['statistiques']['budget_total_actuel'] or 0
            
            if budget_initial > 0:
                variation_pct = ((budget_actuel - budget_initial) / budget_initial) * 100
                formatted['variation_budget'] = {
                    'value': f"{variation_pct:+.1f}%",
                    'label': 'Variation Budget',
                    'delta': variation_pct
                }
            
            return formatted
            
        except Exception as e:
            logger.error(f"Erreur métriques dashboard: {e}")
            return {}
    
    def paginate_results(self, data: List[Dict], page: int = 1, 
                        per_page: int = None) -> Dict:
        """Paginer les résultats"""
        per_page = per_page or PAGINATION_LIMITS['operations_per_page']
        total = len(data)
        total_pages = (total + per_page - 1) // per_page
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return {
            'data': data[start_idx:end_idx],
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_items': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        }
    
    def search_operations(self, query: str, user_id: str = None) -> List[Dict]:
        """Recherche textuelle dans les opérations"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Recherche sur nom, adresse, secteur
                search_query = f"%{query.lower()}%"
                
                if user_id:
                    cursor.execute("""
                        SELECT DISTINCT o.* FROM operations o
                        LEFT JOIN droits_operations d ON o.id = d.operation_id
                        WHERE (
                            LOWER(o.nom) LIKE ? OR
                            LOWER(o.adresse) LIKE ? OR  
                            LOWER(o.secteur_geographique) LIKE ?
                        ) AND (
                            d.utilisateur_id = ? AND d.actif = 1
                            OR o.created_by = ?
                        )
                        ORDER BY o.created_at DESC
                    """, (search_query, search_query, search_query, user_id, user_id))
                else:
                    cursor.execute("""
                        SELECT * FROM operations
                        WHERE LOWER(nom) LIKE ? OR
                              LOWER(adresse) LIKE ? OR
                              LOWER(secteur_geographique) LIKE ?
                        ORDER BY created_at DESC
                    """, (search_query, search_query, search_query))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Erreur recherche opérations: {e}")
            return []
    
    def get_operation_summary(self, operation_id: str) -> Dict:
        """Résumé complet d'une opération pour affichage"""
        try:
            # Données opération
            operation = self.db.get_operation(operation_id)
            if not operation:
                return {}
            
            # Phases avec statistiques
            phases = self.db.get_phases_by_operation(operation_id)
            phases_stats = self._calculate_phases_stats(phases)
            
            # Alertes actives
            alertes = self.db.get_active_alerts(operation_id)
            
            # Évolution budgétaire
            budgets = self.db.get_budget_evolution(operation_id)
            
            # Dernières modifications
            journal = self.db.get_journal_entries(operation_id, 5)
            
            return {
                'operation': operation,
                'phases_stats': phases_stats,
                'alertes_actives': len([a for a in alertes if a.get('actif')]),
                'alertes_critiques': len([a for a in alertes 
                                        if a.get('niveau_severite') == 'CRITIQUE']),
                'budget_evolution': budgets,
                'dernieres_modifications': journal,
                'resume_genere': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur résumé opération: {e}")
            return {}
    
    def _calculate_phases_stats(self, phases: List[Dict]) -> Dict:
        """Calculer statistiques des phases"""
        if not phases:
            return {
                'total': 0, 'terminees': 0, 'en_cours': 0, 
                'non_commencees': 0, 'bloquees': 0, 'en_retard': 0,
                'progression_moyenne': 0
            }
        
        stats = {
            'total': len(phases),
            'terminees': 0,
            'en_cours': 0, 
            'non_commencees': 0,
            'bloquees': 0,
            'en_retard': 0
        }
        
        progressions = []
        today = date.today()
        
        for phase in phases:
            statut = phase.get('statut_phase', '')
            progression = phase.get('progression_pct', 0)
            progressions.append(progression)
            
            if statut == 'TERMINE':
                stats['terminees'] += 1
            elif statut == 'EN_COURS':
                stats['en_cours'] += 1
            elif statut == 'BLOQUE':
                stats['bloquees'] += 1
            else:
                stats['non_commencees'] += 1
            
            # Vérifier retards
            if (phase.get('date_fin_prevue') and statut != 'TERMINE'):
                date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                if date_fin < today:
                    stats['en_retard'] += 1
        
        stats['progression_moyenne'] = sum(progressions) / len(progressions) if progressions else 0
        
        return stats
    
    def export_to_dataframe(self, table_name: str, operation_id: str = None) -> pd.DataFrame:
        """Exporter une table vers DataFrame pour export Excel/CSV"""
        try:
            with self.db.get_connection() as conn:
                if table_name == 'operations':
                    if operation_id:
                        query = "SELECT * FROM operations WHERE id = ?"
                        df = pd.read_sql_query(query, conn, params=[operation_id])
                    else:
                        df = pd.read_sql_query("SELECT * FROM operations", conn)
                
                elif table_name == 'phases_operations' and operation_id:
                    query = "SELECT * FROM phases_operations WHERE operation_id = ?"
                    df = pd.read_sql_query(query, conn, params=[operation_id])
                
                elif table_name == 'journal_modifications' and operation_id:
                    query = """
                        SELECT j.*, u.nom, u.prenom 
                        FROM journal_modifications j
                        LEFT JOIN utilisateurs_spic u ON j.utilisateur_id = u.id
                        WHERE j.operation_id = ?
                        ORDER BY j.timestamp DESC
                    """
                    df = pd.read_sql_query(query, conn, params=[operation_id])
                
                else:
                    df = pd.DataFrame()
                
                return df
                
        except Exception as e:
            logger.error(f"Erreur export DataFrame {table_name}: {e}")
            return pd.DataFrame()

# Fonction utilitaire pour format des montants
def format_currency(amount: float) -> str:
    """Formater un montant en euros"""
    if pd.isna(amount) or amount == 0:
        return "Non défini"
    return f"€{amount:,.0f}".replace(',', ' ')

def format_percentage(value: float) -> str:
    """Formater un pourcentage"""
    if pd.isna(value):
        return "N/A"
    return f"{value:.1f}%"

def format_duration(days: int) -> str:
    """Formater une durée en jours"""
    if pd.isna(days) or days == 0:
        return "N/A"
    return f"{days} jour{'s' if days > 1 else ''}"

def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Division sécurisée"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default
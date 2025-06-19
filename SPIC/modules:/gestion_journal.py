"""
Module de gestion du journal et historique SPIC 2.0
Affichage dynamique, filtres, recherche, statistiques
Cohérent avec l'architecture refactorisée
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging

import config
from utils import *
from utils.form_utils import FormComponents
from utils.db_utils import DatabaseUtils
from utils.constants import UI_MESSAGES, CACHE_CONFIG

logger = logging.getLogger(__name__)

def show_gestion_journal(db_manager, user_session: Dict):
    """Interface principale de gestion du journal"""
    
    st.header("📚 Gestion du Journal")
    
    # Navigation par onglets (cohérent avec suivi_operations.py)
    tab1, tab2, tab3 = st.tabs([
        "📖 Journal Global",
        "🔍 Recherche Avancée", 
        "📊 Statistiques"
    ])
    
    db_utils = DatabaseUtils(db_manager)
    
    with tab1:
        show_global_journal(db_manager, db_utils, user_session)
    
    with tab2:
        show_advanced_search(db_manager, db_utils, user_session)
    
    with tab3:
        show_journal_statistics(db_manager, db_utils, user_session)

def show_global_journal(db_manager, db_utils, user_session: Dict):
    """Affichage du journal global avec filtres"""
    
    st.subheader("📖 Journal des Modifications")
    
    # Filtres en sidebar (cohérent avec portfolio)
    with st.sidebar:
        st.header("🔍 Filtres Journal")
        
        # Filtre par opération
        operations_options = db_utils.get_operations_for_selectbox(user_session.get('user_id'))
        selected_operation = st.selectbox(
            "Opération",
            options=[''] + list(operations_options.keys()),
            format_func=lambda x: 'Toutes les opérations' if x == '' else operations_options.get(x, x),
            key="journal_operation_filter"
        )
        
        # Filtre par utilisateur
        users_options = db_utils.get_users_for_selectbox()
        selected_user = st.selectbox(
            "Utilisateur",
            options=[''] + list(users_options.keys()),
            format_func=lambda x: 'Tous les utilisateurs' if x == '' else users_options.get(x, x),
            key="journal_user_filter"
        )
        
        # Filtre par action
        actions_available = ['CREATE', 'UPDATE', 'DELETE']
        selected_actions = st.multiselect(
            "Actions",
            options=actions_available,
            default=actions_available,
            key="journal_actions_filter"
        )
        
        # Filtre par période
        date_range = st.date_input(
            "Période",
            value=[date.today() - timedelta(days=30), date.today()],
            key="journal_date_filter"
        )
        
        # Filtre par table
        tables_available = ['operations', 'phases_operations', 'budgets_globaux', 'rem_operations']
        selected_tables = st.multiselect(
            "Tables concernées",
            options=tables_available,
            default=tables_available,
            key="journal_tables_filter"
        )
        
        # Bouton reset
        if st.button("🔄 Réinitialiser filtres"):
            for key in ['journal_operation_filter', 'journal_user_filter', 'journal_actions_filter', 
                       'journal_date_filter', 'journal_tables_filter']:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()
    
    # Contrôles principaux
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        entries_limit = st.selectbox(
            "Nombre d'entrées",
            options=[50, 100, 200, 500],
            index=1,
            key="journal_limit"
        )
    
    with col2:
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    with col3:
        if st.button("📥 Exporter Journal"):
            st.session_state['export_request'] = 'journal'
            st.info("👉 Rendez-vous dans l'onglet Exports")
    
    try:
        # Récupérer entrées du journal avec filtres
        journal_entries = get_filtered_journal_entries(
            db_manager, selected_operation, selected_user, 
            selected_actions, date_range, selected_tables, entries_limit
        )
        
        if not journal_entries:
            st.info("📋 Aucune entrée de journal trouvée")
            return
        
        # Métriques rapides (cohérent avec vue manager)
        show_journal_metrics(journal_entries)
        
        # Affichage du journal
        display_journal_entries(journal_entries)
        
    except Exception as e:
        logger.error(f"Erreur chargement journal: {e}")
        FormComponents.alert_message(f"Erreur chargement journal: {e}", "error")

def show_advanced_search(db_manager, db_utils, user_session: Dict):
    """Recherche avancée dans le journal"""
    
    st.subheader("🔍 Recherche Avancée")
    
    # Formulaire de recherche
    with st.form("advanced_search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Recherche textuelle
            search_text = st.text_input(
                "Recherche textuelle",
                help="Recherche dans les valeurs anciennes et nouvelles"
            )
            
            # Recherche par champ modifié
            field_search = st.text_input(
                "Champ modifié",
                help="Nom du champ modifié (ex: statut_global, budget_initial)"
            )
        
        with col2:
            # Recherche par IP
            ip_search = st.text_input(
                "Adresse IP",
                help="Adresse IP de l'utilisateur"
            )
            
            # Période spécifique
            specific_date = st.date_input(
                "Date spécifique",
                help="Rechercher les modifications d'une date précise"
            )
        
        # Options avancées
        st.markdown("#### Options Avancées")
        
        col3, col4 = st.columns(2)
        
        with col3:
            include_system = st.checkbox(
                "Inclure modifications système",
                help="Inclure les modifications automatiques"
            )
        
        with col4:
            sort_order = st.selectbox(
                "Ordre de tri",
                options=['DESC', 'ASC'],
                format_func=lambda x: 'Plus récent d\'abord' if x == 'DESC' else 'Plus ancien d\'abord'
            )
        
        submitted = st.form_submit_button("🔍 Rechercher", type="primary")
    
    if submitted:
        try:
            # Construire requête de recherche avancée
            search_results = perform_advanced_journal_search(
                db_manager, search_text, field_search, ip_search, 
                specific_date, include_system, sort_order
            )
            
            if search_results:
                st.success(f"✅ {len(search_results)} résultat(s) trouvé(s)")
                display_journal_entries(search_results)
            else:
                st.info("📋 Aucun résultat trouvé")
                
        except Exception as e:
            logger.error(f"Erreur recherche avancée: {e}")
            FormComponents.alert_message(f"Erreur lors de la recherche: {e}", "error")

def show_journal_statistics(db_manager, db_utils, user_session: Dict):
    """Statistiques d'activité du journal"""
    
    st.subheader("📊 Statistiques d'Activité")
    
    try:
        # Période d'analyse
        col1, col2 = st.columns(2)
        
        with col1:
            period_start = st.date_input(
                "Début de période",
                value=date.today() - timedelta(days=30)
            )
        
        with col2:
            period_end = st.date_input(
                "Fin de période",
                value=date.today()
            )
        
        # Récupérer statistiques
        stats_data = calculate_journal_statistics(db_manager, period_start, period_end)
        
        if not stats_data:
            st.warning("Aucune donnée disponible pour cette période")
            return
        
        # Métriques principales (cohérent avec dashboard)
        st.markdown("### 📈 Métriques de la Période")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card(
                "Total Modifications",
                stats_data.get('total_modifications', 0),
                help_text="Nombre total de modifications"
            )
        
        with col2:
            create_metric_card(
                "Utilisateurs Actifs",
                stats_data.get('utilisateurs_actifs', 0),
                help_text="Nombre d'utilisateurs ayant fait des modifications"
            )
        
        with col3:
            create_metric_card(
                "Opérations Modifiées",
                stats_data.get('operations_modifiees', 0),
                help_text="Nombre d'opérations ayant subi des modifications"
            )
        
        with col4:
            avg_per_day = stats_data.get('moyenne_par_jour', 0)
            create_metric_card(
                "Moyenne/Jour",
                f"{avg_per_day:.1f}",
                help_text="Nombre moyen de modifications par jour"
            )
        
        # Graphiques de répartition
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition par action
            if stats_data.get('repartition_actions'):
                fig_actions = create_actions_distribution_chart(stats_data['repartition_actions'])
                st.plotly_chart(fig_actions, use_container_width=True)
        
        with col2:
            # Répartition par utilisateur
            if stats_data.get('repartition_utilisateurs'):
                fig_users = create_users_activity_chart(stats_data['repartition_utilisateurs'])
                st.plotly_chart(fig_users, use_container_width=True)
        
        # Timeline d'activité
        if stats_data.get('activite_quotidienne'):
            st.markdown("### 📅 Activité Quotidienne")
            fig_timeline = create_daily_activity_chart(stats_data['activite_quotidienne'])
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Top des modifications
        if stats_data.get('top_modifications'):
            st.markdown("### 🔝 Top des Champs Modifiés")
            
            for i, modif in enumerate(stats_data['top_modifications'][:10], 1):
                with st.expander(f"#{i} - {modif['champ']} ({modif['count']} modifications)"):
                    st.write(f"**Table:** {modif['table']}")
                    st.write(f"**Dernière modification:** {modif['derniere_modif']}")
                    if modif.get('utilisateurs'):
                        st.write(f"**Utilisateurs:** {', '.join(modif['utilisateurs'])}")
        
    except Exception as e:
        logger.error(f"Erreur statistiques journal: {e}")
        FormComponents.alert_message(f"Erreur calcul statistiques: {e}", "error")

# Fonctions utilitaires cohérentes avec l'architecture

@st.cache_data(ttl=CACHE_CONFIG['journal'])
def get_filtered_journal_entries(db_manager, operation_id: str, user_id: str, 
                                actions: List[str], date_range: List, 
                                tables: List[str], limit: int) -> List[Dict]:
    """Récupérer entrées journal avec filtres appliqués"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construire requête dynamique
            where_conditions = ["1=1"]
            params = []
            
            if operation_id:
                where_conditions.append("j.operation_id = ?")
                params.append(operation_id)
            
            if user_id:
                where_conditions.append("j.utilisateur_id = ?")
                params.append(user_id)
            
            if actions:
                placeholders = ','.join('?' for _ in actions)
                where_conditions.append(f"j.action IN ({placeholders})")
                params.extend(actions)
            
            if tables:
                placeholders = ','.join('?' for _ in tables)
                where_conditions.append(f"j.table_concernee IN ({placeholders})")
                params.extend(tables)
            
            if date_range and len(date_range) == 2:
                where_conditions.append("DATE(j.timestamp) BETWEEN ? AND ?")
                params.extend([str(date_range[0]), str(date_range[1])])
            
            query = f"""
                SELECT j.*, u.nom, u.prenom, o.nom as operation_nom
                FROM journal_modifications j
                LEFT JOIN utilisateurs_spic u ON j.utilisateur_id = u.id
                LEFT JOIN operations o ON j.operation_id = o.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY j.timestamp DESC
                LIMIT ?
            """
            
            params.append(limit)
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur récupération journal filtré: {e}")
        return []

def show_journal_metrics(journal_entries: List[Dict]):
    """Afficher métriques rapides du journal (cohérent avec autres vues)"""
    
    if not journal_entries:
        return
    
    df = pd.DataFrame(journal_entries)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Entrées Affichées",
            len(df),
            help_text="Nombre d'entrées dans la vue actuelle"
        )
    
    with col2:
        unique_users = df['utilisateur_id'].nunique()
        create_metric_card(
            "Utilisateurs Uniques",
            unique_users,
            help_text="Nombre d'utilisateurs différents"
        )
    
    with col3:
        unique_operations = df['operation_id'].nunique()
        create_metric_card(
            "Opérations Concernées", 
            unique_operations,
            help_text="Nombre d'opérations différentes"
        )
    
    with col4:
        actions_counts = df['action'].value_counts()
        most_common_action = actions_counts.index[0] if not actions_counts.empty else "N/A"
        create_metric_card(
            "Action la + Fréquente",
            most_common_action,
            help_text="Action la plus représentée"
        )

def display_journal_entries(journal_entries: List[Dict]):
    """Afficher les entrées du journal avec formatage"""
    
    if not journal_entries:
        st.info("📋 Aucune entrée à afficher")
        return
    
    # Préparer DataFrame pour affichage
    df = pd.DataFrame(journal_entries)
    
    # Formatage des colonnes
    df['timestamp_format'] = pd.to_datetime(df['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
    df['utilisateur_format'] = df.apply(
        lambda row: f"{row.get('nom', '')} {row.get('prenom', '')}".strip() or 'Utilisateur inconnu',
        axis=1
    )
    df['operation_format'] = df['operation_nom'].fillna('Opération supprimée')
    
    # Action avec icône
    action_icons = {'CREATE': '➕', 'UPDATE': '✏️', 'DELETE': '🗑️'}
    df['action_format'] = df['action'].map(
        lambda x: f"{action_icons.get(x, '📝')} {x}"
    )
    
    # Colonnes à afficher
    display_columns = [
        'timestamp_format', 'action_format', 'utilisateur_format',
        'operation_format', 'table_concernee', 'champ_modifie', 
        'ancienne_valeur', 'nouvelle_valeur'
    ]
    
    display_df = df[display_columns].copy()
    
    # Configuration colonnes
    column_config = {
        "timestamp_format": st.column_config.TextColumn("Date/Heure", width="medium"),
        "action_format": st.column_config.TextColumn("Action", width="small"),
        "utilisateur_format": st.column_config.TextColumn("Utilisateur", width="medium"),
        "operation_format": st.column_config.TextColumn("Opération", width="medium"),
        "table_concernee": st.column_config.TextColumn("Table", width="small"),
        "champ_modifie": st.column_config.TextColumn("Champ", width="small"),
        "ancienne_valeur": st.column_config.TextColumn("Ancienne Valeur", width="medium"),
        "nouvelle_valeur": st.column_config.TextColumn("Nouvelle Valeur", width="medium")
    }
    
    # Affichage avec data_editor (cohérent avec autres modules)
    st.dataframe(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        key="journal_display"
    )

def perform_advanced_journal_search(db_manager, search_text: str, field_search: str,
                                   ip_search: str, specific_date: date, 
                                   include_system: bool, sort_order: str) -> List[Dict]:
    """Effectuer recherche avancée dans le journal"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["1=1"]
            params = []
            
            if search_text:
                where_conditions.append("""
                    (j.ancienne_valeur LIKE ? OR j.nouvelle_valeur LIKE ? OR 
                     o.nom LIKE ? OR u.nom LIKE ? OR u.prenom LIKE ?)
                """)
                search_pattern = f"%{search_text}%"
                params.extend([search_pattern] * 5)
            
            if field_search:
                where_conditions.append("j.champ_modifie LIKE ?")
                params.append(f"%{field_search}%")
            
            if ip_search:
                where_conditions.append("j.ip_address LIKE ?")
                params.append(f"%{ip_search}%")
            
            if specific_date:
                where_conditions.append("DATE(j.timestamp) = ?")
                params.append(str(specific_date))
            
            if not include_system:
                # Exclure modifications automatiques (ex: recalculs)
                where_conditions.append("j.champ_modifie NOT LIKE '%auto%'")
            
            order_clause = f"ORDER BY j.timestamp {sort_order}"
            
            query = f"""
                SELECT j.*, u.nom, u.prenom, o.nom as operation_nom
                FROM journal_modifications j
                LEFT JOIN utilisateurs_spic u ON j.utilisateur_id = u.id
                LEFT JOIN operations o ON j.operation_id = o.id
                WHERE {' AND '.join(where_conditions)}
                {order_clause}
                LIMIT 500
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur recherche avancée journal: {e}")
        return []

@st.cache_data(ttl=CACHE_CONFIG['dashboard'])
def calculate_journal_statistics(db_manager, start_date: date, end_date: date) -> Dict:
    """Calculer statistiques du journal pour une période"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Statistiques principales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_modifications,
                    COUNT(DISTINCT utilisateur_id) as utilisateurs_actifs,
                    COUNT(DISTINCT operation_id) as operations_modifiees
                FROM journal_modifications
                WHERE DATE(timestamp) BETWEEN ? AND ?
            """, (str(start_date), str(end_date)))
            
            main_stats = dict(cursor.fetchone())
            
            # Moyenne par jour
            days_diff = (end_date - start_date).days + 1
            main_stats['moyenne_par_jour'] = main_stats['total_modifications'] / days_diff if days_diff > 0 else 0
            
            # Répartition par action
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM journal_modifications
                WHERE DATE(timestamp) BETWEEN ? AND ?
                GROUP BY action
                ORDER BY count DESC
            """, (str(start_date), str(end_date)))
            
            repartition_actions = [dict(row) for row in cursor.fetchall()]
            
            # Répartition par utilisateur
            cursor.execute("""
                SELECT u.nom, u.prenom, COUNT(*) as count
                FROM journal_modifications j
                LEFT JOIN utilisateurs_spic u ON j.utilisateur_id = u.id
                WHERE DATE(j.timestamp) BETWEEN ? AND ?
                GROUP BY j.utilisateur_id, u.nom, u.prenom
                ORDER BY count DESC
                LIMIT 10
            """, (str(start_date), str(end_date)))
            
            repartition_utilisateurs = [dict(row) for row in cursor.fetchall()]
            
            # Activité quotidienne
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM journal_modifications
                WHERE DATE(timestamp) BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (str(start_date), str(end_date)))
            
            activite_quotidienne = [dict(row) for row in cursor.fetchall()]
            
            # Top des champs modifiés
            cursor.execute("""
                SELECT 
                    champ_modifie as champ,
                    table_concernee as table,
                    COUNT(*) as count,
                    MAX(timestamp) as derniere_modif
                FROM journal_modifications
                WHERE DATE(timestamp) BETWEEN ? AND ? 
                AND champ_modifie IS NOT NULL
                GROUP BY champ_modifie, table_concernee
                ORDER BY count DESC
                LIMIT 15
            """, (str(start_date), str(end_date)))
            
            top_modifications = [dict(row) for row in cursor.fetchall()]
            
            return {
                **main_stats,
                'repartition_actions': repartition_actions,
                'repartition_utilisateurs': repartition_utilisateurs,
                'activite_quotidienne': activite_quotidienne,
                'top_modifications': top_modifications
            }
            
    except Exception as e:
        logger.error(f"Erreur calcul statistiques journal: {e}")
        return {}

# Fonctions de création des graphiques (cohérentes avec utils/)

def create_actions_distribution_chart(actions_data: List[Dict]):
    """Graphique répartition des actions"""
    if not actions_data:
        return go.Figure()
    
    df = pd.DataFrame(actions_data)
    
    fig = px.pie(
        df, 
        values='count', 
        names='action',
        title="Répartition des Actions",
        color_discrete_map={
            'CREATE': '#4CAF50',
            'UPDATE': '#2196F3', 
            'DELETE': '#F44336'
        }
    )
    
    fig.update_layout(height=300)
    return fig

def create_users_activity_chart(users_data: List[Dict]):
    """Graphique activité utilisateurs"""
    if not users_data:
        return go.Figure()
    
    df = pd.DataFrame(users_data)
    df['utilisateur'] = df.apply(lambda row: f"{row.get('nom', '')} {row.get('prenom', '')}".strip(), axis=1)
    
    fig = px.bar(
        df.head(10), 
        x='count', 
        y='utilisateur',
        orientation='h',
        title="Top 10 Utilisateurs Actifs",
        color='count',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(height=400)
    return fig

def create_daily_activity_chart(activity_data: List[Dict]):
    """Graphique activité quotidienne"""
    if not activity_data:
        return go.Figure()
    
    df = pd.DataFrame(activity_data)
    df['date'] = pd.to_datetime(df['date'])
    
    fig = px.line(
        df, 
        x='date', 
        y='count',
        title="Évolution de l'Activité Quotidienne",
        markers=True
    )
    
    fig.update_layout(height=300)
    return fig
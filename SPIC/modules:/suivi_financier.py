"""
Module de suivi financier et REM SPIC 2.0
Gestion budgets, évolution, REM par période, complémentarité Gespro
Cohérent avec l'architecture refactorisée
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging

import config
from utils import *
from utils.form_utils import FormComponents
from utils.db_utils import DatabaseUtils
from utils.constants import UI_MESSAGES, CACHE_CONFIG

logger = logging.getLogger(__name__)

def show_suivi_financier(db_manager, user_session: Dict):
    """Interface principale de suivi financier"""
    
    st.header("💰 Suivi Financier")
    
    # Navigation par onglets (cohérent avec autres modules)
    tab1, tab2, tab3, tab4 = st.tabs([
        "💵 Budgets Opérations",
        "📈 REM",
        "📊 Vue Portefeuille", 
        "⚠️ Alertes Budget"
    ])
    
    db_utils = DatabaseUtils(db_manager)
    
    with tab1:
        show_budgets_operations(db_manager, db_utils, user_session)
    
    with tab2:
        show_rem_management(db_manager, db_utils, user_session)
    
    with tab3:
        show_portfolio_financial_view(db_manager, db_utils, user_session)
    
    with tab4:
        show_budget_alerts(db_manager, db_utils, user_session)

def show_budgets_operations(db_manager, db_utils, user_session: Dict):
    """Gestion des budgets par opération"""
    
    st.subheader("💵 Gestion des Budgets")
    
    # Sélection opération
    operations_options = db_utils.get_operations_for_selectbox(user_session.get('user_id'))
    
    if not operations_options:
        st.warning("Aucune opération disponible")
        return
    
    selected_op_id = st.selectbox(
        "Sélectionner une opération",
        options=list(operations_options.keys()),
        format_func=lambda x: operations_options[x],
        key="budget_operation_select"
    )
    
    if not selected_op_id:
        return
    
    # Informations opération (cohérent avec timeline_view)
    operation = db_manager.get_operation(selected_op_id)
    
    if operation:
        with st.expander("ℹ️ Informations Opération", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Nom:** {operation['nom']}")
                st.write(f"**Type:** {operation['type_operation']}")
            
            with col2:
                st.write(f"**Statut:** {operation['statut_global']}")
                if operation.get('surface_m2'):
                    st.write(f"**Surface:** {format_number_french(operation['surface_m2'])} m²")
            
            with col3:
                st.write(f"**Score Risque:** {operation.get('score_risque', 0)}/100")
                if operation.get('nb_logements'):
                    st.write(f"**Logements:** {operation['nb_logements']}")
    
    # Actions budgétaires
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💰 Évolution Budgétaire")
    
    with col2:
        if st.button("➕ Nouveau Budget"):
            st.session_state['show_budget_form'] = True
    
    try:
        # Récupérer évolution budgétaire
        budget_evolution = db_manager.get_budget_evolution(selected_op_id)
        
        if budget_evolution:
            # Graphique évolution (cohérent avec utils/)
            budget_fig = create_budget_evolution_chart(budget_evolution)
            st.plotly_chart(budget_fig, use_container_width=True)
            
            # Métriques budgétaires (cohérent avec autres vues)
            show_budget_metrics(budget_evolution, operation)
            
            # Table détaillée des budgets
            show_budget_details_table(budget_evolution)
        else:
            st.info("📋 Aucun historique budgétaire disponible")
        
        # Formulaire nouveau budget
        if st.session_state.get('show_budget_form', False):
            show_budget_form(db_manager, selected_op_id, user_session)
    
    except Exception as e:
        logger.error(f"Erreur suivi budgets: {e}")
        FormComponents.alert_message(f"Erreur chargement budgets: {e}", "error")

def show_rem_management(db_manager, db_utils, user_session: Dict):
    """Gestion REM par opération et globale"""
    
    st.subheader("📈 Gestion REM")
    
    # Vue par onglets REM
    rem_tab1, rem_tab2, rem_tab3 = st.tabs([
        "🎯 REM par Opération",
        "🌐 REM Globale",
        "➕ Nouvelle REM"
    ])
    
    with rem_tab1:
        show_rem_per_operation(db_manager, db_utils, user_session)
    
    with rem_tab2:
        show_global_rem_view(db_manager, db_utils, user_session)
    
    with rem_tab3:
        show_rem_form(db_manager, db_utils, user_session)

def show_rem_per_operation(db_manager, db_utils, user_session: Dict):
    """REM par opération spécifique"""
    
    # Sélection opération
    operations_options = db_utils.get_operations_for_selectbox(user_session.get('user_id'))
    
    if not operations_options:
        st.warning("Aucune opération disponible")
        return
    
    selected_op_id = st.selectbox(
        "Opération pour REM",
        options=list(operations_options.keys()),
        format_func=lambda x: operations_options[x],
        key="rem_operation_select"
    )
    
    if not selected_op_id:
        return
    
    try:
        # Récupérer REM de l'opération
        rem_data = db_manager.get_rem_by_operation(selected_op_id)
        operation = db_manager.get_operation(selected_op_id)
        
        if rem_data:
            # Métriques REM (cohérent avec autres métriques)
            show_rem_metrics(rem_data, operation)
            
            # Graphique évolution REM
            rem_fig = create_rem_evolution_chart(rem_data)
            if rem_fig:
                st.plotly_chart(rem_fig, use_container_width=True)
            
            # Table REM
            show_rem_table(rem_data)
        else:
            st.info(f"📋 Aucune REM saisie pour cette opération")
            
            if operation and operation.get('budget_initial'):
                st.info(f"💡 Budget initial: {format_number_french(operation['budget_initial'])}€")
    
    except Exception as e:
        logger.error(f"Erreur REM par opération: {e}")
        FormComponents.alert_message(f"Erreur chargement REM: {e}", "error")

def show_global_rem_view(db_manager, db_utils, user_session: Dict):
    """Vue globale REM portefeuille"""
    
    st.markdown("#### 🌐 REM Globale du Portefeuille")
    
    # Filtres période
    col1, col2, col3 = st.columns(3)
    
    with col1:
        annee_filter = st.selectbox(
            "Année",
            options=list(range(datetime.now().year - 2, datetime.now().year + 2)),
            index=2,  # Année actuelle
            key="rem_global_year"
        )
    
    with col2:
        periode_filter = st.selectbox(
            "Période",
            options=['Toutes', 'TRIMESTRE', 'SEMESTRE'],
            key="rem_global_period"
        )
    
    with col3:
        if st.button("🔄 Actualiser REM"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    try:
        # Récupérer REM globale
        global_rem_data = get_global_rem_data(
            db_manager, annee_filter, periode_filter, user_session.get('user_id')
        )
        
        if not global_rem_data:
            st.info("📋 Aucune REM trouvée pour les critères sélectionnés")
            return
        
        # Métriques globales
        show_global_rem_metrics(global_rem_data)
        
        # Graphiques REM globale
        col1, col2 = st.columns(2)
        
        with col1:
            # REM par opération
            fig_ops = create_rem_by_operation_chart(global_rem_data)
            if fig_ops:
                st.plotly_chart(fig_ops, use_container_width=True)
        
        with col2:
            # REM par période
            fig_periods = create_rem_by_period_chart(global_rem_data)
            if fig_periods:
                st.plotly_chart(fig_periods, use_container_width=True)
        
        # Table récapitulative
        st.markdown("#### 📊 Récapitulatif REM")
        
        rem_summary = prepare_rem_summary_table(global_rem_data)
        if not rem_summary.empty:
            st.dataframe(
                rem_summary,
                column_config={
                    "operation_nom": "Opération",
                    "total_rem": st.column_config.NumberColumn("Total REM", format="€%.0f"),
                    "pourcentage_moyen": st.column_config.NumberColumn("% Moyen", format="%.1f%%"),
                    "nb_saisies": "Nb Saisies",
                    "derniere_saisie": "Dernière Saisie"
                },
                hide_index=True,
                use_container_width=True
            )
    
    except Exception as e:
        logger.error(f"Erreur REM globale: {e}")
        FormComponents.alert_message(f"Erreur chargement REM globale: {e}", "error")

def show_rem_form(db_manager, db_utils, user_session: Dict):
    """Formulaire de saisie REM"""
    
    st.markdown("#### ➕ Nouvelle Saisie REM")
    
    # Sélection opération
    operations_options = db_utils.get_operations_for_selectbox(user_session.get('user_id'))
    
    if not operations_options:
        st.warning("Aucune opération disponible")
        return
    
    selected_op_id = st.selectbox(
        "Opération",
        options=list(operations_options.keys()),
        format_func=lambda x: operations_options[x],
        key="rem_form_operation_select"
    )
    
    if selected_op_id:
        # Afficher budget de référence
        operation = db_manager.get_operation(selected_op_id)
        if operation and operation.get('budget_initial'):
            st.info(f"💰 Budget initial: {format_number_french(operation['budget_initial'])}€")
        
        # Formulaire REM (cohérent avec form_utils)
        rem_data = FormComponents.rem_form(selected_op_id)
        
        if rem_data:
            try:
                rem_id = db_manager.add_rem(
                    selected_op_id,
                    rem_data['periode'],
                    rem_data['annee'],
                    rem_data['montant_rem'],
                    rem_data.get('trimestre'),
                    rem_data.get('semestre'),
                    rem_data.get('type_rem'),
                    rem_data.get('commentaire'),
                    user_session['user_id']
                )
                
                if rem_id:
                    FormComponents.alert_message(
                        f"REM de {format_number_french(rem_data['montant_rem'])}€ ajoutée avec succès !",
                        "success"
                    )
                    
                    # Actualiser cache
                    st.cache_data.clear()
                    
                    # Recalculer alertes budgétaires
                    db_manager.generate_alerts(selected_op_id)
                else:
                    FormComponents.alert_message("Erreur lors de l'ajout de la REM", "error")
            
            except Exception as e:
                logger.error(f"Erreur ajout REM: {e}")
                FormComponents.alert_message(f"Erreur ajout REM: {e}", "error")

def show_portfolio_financial_view(db_manager, db_utils, user_session: Dict):
    """Vue financière globale du portefeuille"""
    
    st.subheader("📊 Vue Financière Portefeuille")
    
    try:
        # Métriques portefeuille (cohérent avec dashboard)
        dashboard_data = db_utils.get_dashboard_metrics()
        
        if dashboard_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                budget_info = dashboard_data.get('budget_total', {})
                create_metric_card(
                    "Budget Total",
                    budget_info.get('value', '€0'),
                    help_text="Budget total du portefeuille"
                )
            
            with col2:
                variation_info = dashboard_data.get('variation_budget', {})
                if variation_info:
                    create_metric_card(
                        "Variation Budget",
                        variation_info.get('value', '0%'),
                        delta=variation_info.get('delta'),
                        help_text="Évolution vs budget initial"
                    )
            
            with col3:
                # Calculer total REM
                total_rem = calculate_total_rem_portfolio(db_manager, user_session.get('user_id'))
                create_metric_card(
                    "Total REM",
                    f"{format_number_french(total_rem)}€",
                    help_text="REM cumulée du portefeuille"
                )
            
            with col4:
                # Ratio REM/Budget
                if dashboard_data.get('statistiques', {}).get('budget_total_actuel', 0) > 0:
                    ratio_rem = (total_rem / dashboard_data['statistiques']['budget_total_actuel']) * 100
                    create_metric_card(
                        "Ratio REM/Budget",
                        f"{ratio_rem:.1f}%",
                        help_text="REM en % du budget total"
                    )
        
        # Graphiques portefeuille
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition budgets par type d'opération
            budget_by_type = get_budget_by_operation_type(db_manager, user_session.get('user_id'))
            if budget_by_type:
                fig_budget_type = create_budget_by_type_chart(budget_by_type)
                st.plotly_chart(fig_budget_type, use_container_width=True)
        
        with col2:
            # Évolution budgétaire globale
            global_budget_evolution = db_utils.get_budget_evolution_global()
            if global_budget_evolution and global_budget_evolution.get('evolution_mensuelle'):
                fig_evolution = create_budget_evolution_chart(global_budget_evolution['evolution_mensuelle'])
                st.plotly_chart(fig_evolution, use_container_width=True)
        
        # Top opérations par budget
        st.markdown("### 🏆 Top Opérations par Budget")
        
        top_operations = get_top_operations_by_budget(db_manager, user_session.get('user_id'))
        
        if top_operations:
            for i, op in enumerate(top_operations[:5], 1):
                with st.expander(f"#{i} - {op['nom']} ({format_number_french(op.get('budget_actuel', 0))}€)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {op['type_operation']}")
                        st.write(f"**Budget initial:** {format_number_french(op.get('budget_initial', 0))}€")
                    
                    with col2:
                        if op.get('budget_initial', 0) > 0:
                            variation = ((op.get('budget_actuel', 0) - op['budget_initial']) / op['budget_initial']) * 100
                            st.write(f"**Variation:** {variation:+.1f}%")
                        st.write(f"**Statut:** {op['statut_global']}")
    
    except Exception as e:
        logger.error(f"Erreur vue portefeuille financier: {e}")
        FormComponents.alert_message(f"Erreur chargement vue portefeuille: {e}", "error")

def show_budget_alerts(db_manager, db_utils, user_session: Dict):
    """Alertes et dépassements budgétaires"""
    
    st.subheader("⚠️ Alertes Budgétaires")
    
    try:
        # Générer alertes budgétaires
        if st.button("🔄 Actualiser les alertes budgétaires"):
            with st.spinner("Génération des alertes en cours..."):
                db_manager.generate_alerts()
                st.success("✅ Alertes budgétaires mises à jour")
        
        # Récupérer alertes budgétaires actives
        budget_alerts = get_budget_alerts(db_manager, user_session.get('user_id'))
        
        if not budget_alerts:
            st.success("✅ Aucune alerte budgétaire active")
            return
        
        # Métriques alertes
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_metric_card(
                "Alertes Actives",
                len(budget_alerts),
                help_text="Nombre d'alertes budgétaires actives"
            )
        
        with col2:
            critiques = len([a for a in budget_alerts if a.get('niveau_severite') == 'CRITIQUE'])
            create_metric_card(
                "Alertes Critiques",
                critiques,
                help_text="Alertes de niveau critique"
            )
        
        with col3:
            operations_concernees = len(set([a['operation_id'] for a in budget_alerts]))
            create_metric_card(
                "Opérations Concernées",
                operations_concernees,
                help_text="Nombre d'opérations avec alertes budget"
            )
        
        # Affichage des alertes
        st.markdown("### 🚨 Détail des Alertes")
        
        for alerte in budget_alerts:
            severity_color = {
                'CRITIQUE': '#F44336',
                'ELEVE': '#FF9800',
                'MOYEN': '#FFD54F'
            }.get(alerte.get('niveau_severite', 'MOYEN'), '#FFD54F')
            
            with st.expander(f"⚠️ {alerte.get('titre', 'Alerte budget')} - {alerte.get('operation_nom', 'Opération')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Niveau:** {alerte.get('niveau_severite', 'MOYEN')}")
                    st.write(f"**Description:** {alerte.get('description', '')}")
                    st.write(f"**Date création:** {alerte.get('date_creation', '')}")
                
                with col2:
                    # Bouton résolution
                    if st.button(f"✅ Résoudre", key=f"resolve_{alerte['id']}"):
                        if db_manager.resolve_alert(alerte['id'], user_session['user_id']):
                            st.success("Alerte résolue")
                            st.experimental_rerun()
                    
                    # Paramètres alerte si disponibles
                    if alerte.get('parametres'):
                        try:
                            import json
                            params = json.loads(alerte['parametres'])
                            for key, value in params.items():
                                st.write(f"**{key}:** {value}")
                        except:
                            pass
    
    except Exception as e:
        logger.error(f"Erreur alertes budgétaires: {e}")
        FormComponents.alert_message(f"Erreur chargement alertes: {e}", "error")

# Fonctions utilitaires cohérentes avec l'architecture

def show_budget_form(db_manager, operation_id: str, user_session: Dict):
    """Afficher formulaire budget (cohérent avec form_utils)"""
    
    st.markdown("#### ➕ Nouveau Budget")
    
    budget_data = FormComponents.budget_form(operation_id)
    
    if budget_data:
        try:
            budget_id = db_manager.add_budget(
                operation_id,
                budget_data['type_budget'],
                budget_data['montant'],
                budget_data['date_budget'],
                budget_data['justification'],
                user_session['user_id']
            )
            
            if budget_id:
                FormComponents.alert_message(
                    f"Budget {budget_data['type_budget']} ajouté avec succès !",
                    "success"
                )
                
                # Actualiser cache et recalculer alertes
                st.cache_data.clear()
                db_manager.generate_alerts(operation_id)
                
                # Masquer le formulaire
                st.session_state['show_budget_form'] = False
                st.experimental_rerun()
            else:
                FormComponents.alert_message("Erreur lors de l'ajout du budget", "error")
        
        except Exception as e:
            logger.error(f"Erreur ajout budget: {e}")
            FormComponents.alert_message(f"Erreur ajout budget: {e}", "error")
    
    # Bouton annuler
    if st.button("❌ Annuler"):
        st.session_state['show_budget_form'] = False
        st.experimental_rerun()

def show_budget_metrics(budget_evolution: List[Dict], operation: Dict):
    """Afficher métriques budgétaires (cohérent avec autres métriques)"""
    
    if not budget_evolution:
        return
    
    # Calculer métriques
    budget_initial = next((b['montant'] for b in budget_evolution if b['type_budget'] == 'INITIAL'), 0)
    budget_final = next((b['montant'] for b in budget_evolution if b['type_budget'] == 'FINAL'), None)
    budget_revise = next((b['montant'] for b in budget_evolution if b['type_budget'] == 'REVISE'), None)
    
    budget_actuel = budget_final or budget_revise or budget_initial
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Budget Initial",
            f"{format_number_french(budget_initial)}€",
            help_text="Budget initial de l'opération"
        )
    
    with col2:
        create_metric_card(
            "Budget Actuel",
            f"{format_number_french(budget_actuel)}€",
            help_text="Dernier budget validé"
        )
    
    with col3:
        if budget_initial > 0:
            variation = budget_actuel - budget_initial
            variation_pct = (variation / budget_initial) * 100
            create_metric_card(
                "Variation",
                f"{variation_pct:+.1f}%",
                delta=f"{format_number_french(variation)}€",
                help_text="Évolution vs budget initial"
            )
    
    with col4:
        nb_revisions = len([b for b in budget_evolution if b['type_budget'] in ['REVISE', 'FINAL']])
        create_metric_card(
            "Nb Révisions",
            nb_revisions,
            help_text="Nombre de révisions budgétaires"
        )

def show_budget_details_table(budget_evolution: List[Dict]):
    """Table détaillée des budgets"""
    
    df = pd.DataFrame(budget_evolution)
    df['date_budget'] = pd.to_datetime(df['date_budget']).dt.strftime('%d/%m/%Y')
    df['montant_format'] = df['montant'].apply(lambda x: f"{format_number_french(x)}€")
    
    # Type avec icône
    type_icons = {'INITIAL': '🏁', 'REVISE': '📝', 'FINAL': '✅'}
    df['type_display'] = df['type_budget'].map(lambda x: f"{type_icons.get(x, '💰')} {x}")
    
    display_cols = ['date_budget', 'type_display', 'montant_format', 'justification']
    
    st.dataframe(
        df[display_cols],
        column_config={
            "date_budget": "Date",
            "type_display": "Type",
            "montant_format": "Montant",
            "justification": "Justification"
        },
        hide_index=True,
        use_container_width=True
    )

def show_rem_metrics(rem_data: List[Dict], operation: Dict):
    """Métriques REM pour une opération"""
    
    if not rem_data:
        return
    
    total_rem = sum(r.get('montant_rem', 0) for r in rem_data)
    budget_initial = operation.get('budget_initial', 0) if operation else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Total REM",
            f"{format_number_french(total_rem)}€",
            help_text="REM cumulée de l'opération"
        )
    
    with col2:
        create_metric_card(
            "Nb Saisies",
            len(rem_data),
            help_text="Nombre de saisies REM"
        )
    
    with col3:
        if budget_initial > 0:
            ratio_rem = (total_rem / budget_initial) * 100
            create_metric_card(
                "% du Budget",
                f"{ratio_rem:.1f}%",
                help_text="REM en % du budget initial"
            )
    
    with col4:
        derniere_rem = max(rem_data, key=lambda x: x.get('date_saisie', ''))
        derniere_date = derniere_rem.get('date_saisie', '')[:10] if derniere_rem else ''
        create_metric_card(
            "Dernière REM",
            derniere_date,
            help_text="Date de la dernière saisie"
        )

def show_rem_table(rem_data: List[Dict]):
    """Table des REM"""
    
    df = pd.DataFrame(rem_data)
    df['date_saisie'] = pd.to_datetime(df['date_saisie']).dt.strftime('%d/%m/%Y')
    df['montant_format'] = df['montant_rem'].apply(lambda x: f"{format_number_french(x)}€")
    df['pourcentage_format'] = df['pourcentage_budget'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    
    # Période formatée
    def format_periode(row):
        if row['periode'] == 'TRIMESTRE':
            return f"T{row.get('trimestre', '')} {row['annee']}"
        else:
            return f"S{row.get('semestre', '')} {row['annee']}"
    
    df['periode_format'] = df.apply(format_periode, axis=1)
    
    display_cols = ['periode_format', 'montant_format', 'pourcentage_format', 'type_rem', 'date_saisie']
    
    st.dataframe(
        df[display_cols],
        column_config={
            "periode_format": "Période",
            "montant_format": "Montant REM",
            "pourcentage_format": "% Budget",
            "type_rem": "Type REM",
            "date_saisie": "Date Saisie"
        },
        hide_index=True,
        use_container_width=True
    )

# Fonctions de récupération des données

@st.cache_data(ttl=CACHE_CONFIG['dashboard'])
def get_global_rem_data(db_manager, annee: int, periode: str, user_id: str) -> List[Dict]:
    """Récupérer données REM globales"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["r.annee = ?"]
            params = [annee]
            
            if periode != 'Toutes':
                where_conditions.append("r.periode = ?")
                params.append(periode)
            
            # Filtrer par droits utilisateur si nécessaire
            if user_id:
                where_conditions.append("""
                    (o.created_by = ? OR EXISTS (
                        SELECT 1 FROM droits_operations d 
                        WHERE d.operation_id = o.id AND d.utilisateur_id = ? AND d.actif = 1
                    ))
                """)
                params.extend([user_id, user_id])
            
            query = f"""
                SELECT r.*, o.nom as operation_nom, o.budget_initial
                FROM rem_operations r
                LEFT JOIN operations o ON r.operation_id = o.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY r.annee DESC, r.trimestre DESC, r.semestre DESC
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur récupération REM globale: {e}")
        return []

@st.cache_data(ttl=CACHE_CONFIG['operations'])
def calculate_total_rem_portfolio(db_manager, user_id: str) -> float:
    """Calculer total REM du portefeuille"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["1=1"]
            params = []
            
            if user_id:
                where_conditions.append("""
                    (o.created_by = ? OR EXISTS (
                        SELECT 1 FROM droits_operations d 
                        WHERE d.operation_id = o.id AND d.utilisateur_id = ? AND d.actif = 1
                    ))
                """)
                params.extend([user_id, user_id])
            
            query = f"""
                SELECT SUM(r.montant_rem) as total_rem
                FROM rem_operations r
                LEFT JOIN operations o ON r.operation_id = o.id
                WHERE {' AND '.join(where_conditions)}
            """
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['total_rem'] if result and result['total_rem'] else 0.0
            
    except Exception as e:
        logger.error(f"Erreur calcul total REM: {e}")
        return 0.0

@st.cache_data(ttl=CACHE_CONFIG['operations'])
def get_budget_by_operation_type(db_manager, user_id: str) -> List[Dict]:
    """Répartition budgets par type d'opération"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["1=1"]
            params = []
            
            if user_id:
                where_conditions.append("""
                    (created_by = ? OR EXISTS (
                        SELECT 1 FROM droits_operations d 
                        WHERE d.operation_id = o.id AND d.utilisateur_id = ? AND d.actif = 1
                    ))
                """)
                params.extend([user_id, user_id])
            
            query = f"""
                SELECT 
                    type_operation,
                    SUM(budget_initial) as budget_initial_total,
                    SUM(COALESCE(budget_final, budget_revise, budget_initial)) as budget_actuel_total,
                    COUNT(*) as nb_operations
                FROM operations o
                WHERE {' AND '.join(where_conditions)}
                GROUP BY type_operation
                ORDER BY budget_actuel_total DESC
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur budget par type: {e}")
        return []

@st.cache_data(ttl=CACHE_CONFIG['operations'])
def get_top_operations_by_budget(db_manager, user_id: str, limit: int = 10) -> List[Dict]:
    """Top opérations par budget"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["1=1"]
            params = []
            
            if user_id:
                where_conditions.append("""
                    (created_by = ? OR EXISTS (
                        SELECT 1 FROM droits_operations d 
                        WHERE d.operation_id = o.id AND d.utilisateur_id = ? AND d.actif = 1
                    ))
                """)
                params.extend([user_id, user_id])
            
            query = f"""
                SELECT 
                    *,
                    COALESCE(budget_final, budget_revise, budget_initial) as budget_actuel
                FROM operations o
                WHERE {' AND '.join(where_conditions)}
                ORDER BY budget_actuel DESC
                LIMIT ?
            """
            
            params.append(limit)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur top opérations budget: {e}")
        return []

@st.cache_data(ttl=CACHE_CONFIG['alerts'])
def get_budget_alerts(db_manager, user_id: str) -> List[Dict]:
    """Récupérer alertes budgétaires actives"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["a.actif = 1", "a.type_alerte = 'BUDGET'"]
            params = []
            
            if user_id:
                where_conditions.append("""
                    (o.created_by = ? OR EXISTS (
                        SELECT 1 FROM droits_operations d 
                        WHERE d.operation_id = o.id AND d.utilisateur_id = ? AND d.actif = 1
                    ))
                """)
                params.extend([user_id, user_id])
            
            query = f"""
                SELECT a.*, o.nom as operation_nom
                FROM alertes a
                LEFT JOIN operations o ON a.operation_id = o.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY a.niveau_severite DESC, a.date_creation DESC
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur alertes budget: {e}")
        return []

def show_global_rem_metrics(global_rem_data: List[Dict]):
    """Métriques REM globales"""
    
    if not global_rem_data:
        return
    
    total_rem = sum(r.get('montant_rem', 0) for r in global_rem_data)
    nb_operations = len(set(r['operation_id'] for r in global_rem_data))
    nb_saisies = len(global_rem_data)
    
    # Calculer moyenne par opération
    moyenne_par_op = total_rem / nb_operations if nb_operations > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Total REM Global",
            f"{format_number_french(total_rem)}€",
            help_text="REM totale du portefeuille"
        )
    
    with col2:
        create_metric_card(
            "Opérations REM",
            nb_operations,
            help_text="Nombre d'opérations avec REM"
        )
    
    with col3:
        create_metric_card(
            "Total Saisies",
            nb_saisies,
            help_text="Nombre total de saisies REM"
        )
    
    with col4:
        create_metric_card(
            "Moyenne/Opération",
            f"{format_number_french(moyenne_par_op)}€",
            help_text="REM moyenne par opération"
        )

def prepare_rem_summary_table(global_rem_data: List[Dict]) -> pd.DataFrame:
    """Préparer table récapitulative REM"""
    
    if not global_rem_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(global_rem_data)
    
    # Grouper par opération
    summary = df.groupby(['operation_id', 'operation_nom']).agg({
        'montant_rem': 'sum',
        'pourcentage_budget': 'mean',
        'date_saisie': ['count', 'max']
    }).round(1)
    
    summary.columns = ['total_rem', 'pourcentage_moyen', 'nb_saisies', 'derniere_saisie']
    summary = summary.reset_index()
    
    # Formater dernière saisie
    summary['derniere_saisie'] = pd.to_datetime(summary['derniere_saisie']).dt.strftime('%d/%m/%Y')
    
    return summary

# Fonctions de création des graphiques (cohérentes avec utils/)

def create_rem_evolution_chart(rem_data: List[Dict]):
    """Graphique évolution REM"""
    
    if not rem_data:
        return None
    
    df = pd.DataFrame(rem_data)
    df['date_saisie'] = pd.to_datetime(df['date_saisie'])
    df = df.sort_values('date_saisie')
    
    # Créer période lisible
    def format_periode(row):
        if row['periode'] == 'TRIMESTRE':
            return f"T{row.get('trimestre', '')} {row['annee']}"
        else:
            return f"S{row.get('semestre', '')} {row['annee']}"
    
    df['periode_format'] = df.apply(format_periode, axis=1)
    
    fig = px.line(
        df, 
        x='periode_format', 
        y='montant_rem',
        title="Évolution REM par Période",
        markers=True,
        hover_data=['pourcentage_budget', 'type_rem']
    )
    
    fig.update_layout(
        xaxis_title="Période",
        yaxis_title="Montant REM (€)",
        height=400
    )
    
    return fig

def create_rem_by_operation_chart(global_rem_data: List[Dict]):
    """Graphique REM par opération"""
    
    if not global_rem_data:
        return None
    
    df = pd.DataFrame(global_rem_data)
    
    # Grouper par opération
    rem_by_op = df.groupby(['operation_id', 'operation_nom'])['montant_rem'].sum().reset_index()
    rem_by_op = rem_by_op.sort_values('montant_rem', ascending=True).tail(10)
    
    fig = px.bar(
        rem_by_op,
        x='montant_rem',
        y='operation_nom',
        orientation='h',
        title="Top 10 REM par Opération",
        color='montant_rem',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_title="Montant REM (€)",
        yaxis_title="Opération",
        height=400
    )
    
    return fig

def create_rem_by_period_chart(global_rem_data: List[Dict]):
    """Graphique REM par période"""
    
    if not global_rem_data:
        return None
    
    df = pd.DataFrame(global_rem_data)
    
    # Créer clé période
    def create_period_key(row):
        if row['periode'] == 'TRIMESTRE':
            return f"{row['annee']}-T{row.get('trimestre', '')}"
        else:
            return f"{row['annee']}-S{row.get('semestre', '')}"
    
    df['periode_key'] = df.apply(create_period_key, axis=1)
    
    # Grouper par période
    rem_by_period = df.groupby('periode_key')['montant_rem'].sum().reset_index()
    rem_by_period = rem_by_period.sort_values('periode_key')
    
    fig = px.bar(
        rem_by_period,
        x='periode_key',
        y='montant_rem',
        title="REM par Période",
        color='montant_rem',
        color_continuous_scale='Greens'
    )
    
    fig.update_layout(
        xaxis_title="Période",
        yaxis_title="Montant REM (€)",
        height=400
    )
    
    return fig

def create_budget_by_type_chart(budget_data: List[Dict]):
    """Graphique budget par type d'opération"""
    
    if not budget_data:
        return None
    
    df = pd.DataFrame(budget_data)
    
    fig = px.pie(
        df,
        values='budget_actuel_total',
        names='type_operation',
        title="Répartition Budget par Type d'Opération",
        color_discrete_map={
            'OPP': config.COULEURS_TIMELINE[0],
            'VEFA': config.COULEURS_TIMELINE[1],
            'AMO': config.COULEURS_TIMELINE[2],
            'MANDAT': config.COULEURS_TIMELINE[3]
        }
    )
    
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig
"""
Module principal de suivi des opérations SPIC 2.0
Vue portefeuille, timeline, vue manager, CRUD opérations
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging

import config
import database
from utils import *
from utils.form_utils import FormComponents
from utils.db_utils import DatabaseUtils
from utils.constants import UI_MESSAGES

logger = logging.getLogger(__name__)

def show_suivi_operations(db_manager, user_session: Dict):
    """Interface principale de suivi des opérations"""
    
    st.header("🏗️ Suivi des Opérations")
    
    # Navigation par onglets
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Portefeuille", 
        "📊 Vue Manager", 
        "🎯 Timeline", 
        "➕ Nouvelle Opération"
    ])
    
    # Utilitaires DB
    db_utils = DatabaseUtils(db_manager)
    
    with tab1:
        show_portfolio_view(db_manager, db_utils, user_session)
    
    with tab2:
        show_manager_view(db_manager, db_utils, user_session)
    
    with tab3:
        show_timeline_view(db_manager, db_utils, user_session)
    
    with tab4:
        show_new_operation_form(db_manager, db_utils, user_session)

def show_portfolio_view(db_manager, db_utils, user_session: Dict):
    """Vue portefeuille avec filtres et recherche"""
    
    st.subheader("📋 Portefeuille d'Opérations")
    
    # Barre de recherche
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = FormComponents.search_bar("Rechercher par nom, adresse, secteur...")
    
    with col2:
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    # Récupérer les opérations
    user_id = user_session.get('user_id')
    
    try:
        if search_query:
            operations = db_utils.search_operations(search_query, user_id)
        else:
            operations = db_manager.get_all_operations(user_id)
        
        operations_df = pd.DataFrame(operations) if operations else pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erreur chargement opérations: {e}")
        operations_df = pd.DataFrame()
    
    if operations_df.empty:
        st.info("📋 Aucune opération trouvée")
        return
    
    # Filtres sidebar
    with st.sidebar:
        st.header("🔍 Filtres")
        filters = FormComponents.filters_sidebar(operations_df)
    
    # Appliquer filtres
    filtered_df = apply_portfolio_filters(operations_df, filters)
    
    # Métriques résumé
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Total Opérations", 
            len(filtered_df),
            help_text="Nombre total d'opérations"
        )
    
    with col2:
        actives = len(filtered_df[filtered_df['statut_global'] == 'EN_COURS'])
        create_metric_card(
            "En Cours", 
            actives,
            help_text="Opérations actives"
        )
    
    with col3:
        if 'budget_initial' in filtered_df.columns:
            budget_total = filtered_df['budget_initial'].fillna(0).sum()
            create_metric_card(
                "Budget Total", 
                format_number_french(budget_total) + "€",
                help_text="Budget total portefeuille"
            )
    
    with col4:
        if 'score_risque' in filtered_df.columns:
            score_moyen = filtered_df['score_risque'].fillna(0).mean()
            create_metric_card(
                "Score Risque Moyen", 
                f"{score_moyen:.0f}/100",
                help_text="Score de risque moyen"
            )
    
    # Table des opérations
    st.subheader("📊 Liste des Opérations")
    
    # Préparer colonnes d'affichage
    display_columns = prepare_operations_display(filtered_df)
    
    # Configuration de l'éditeur
    column_config = {
        "nom": st.column_config.TextColumn("Nom", width="medium"),
        "type_operation": st.column_config.TextColumn("Type", width="small"),
        "statut_display": st.column_config.TextColumn("Statut", width="medium"),
        "budget_display": st.column_config.TextColumn("Budget", width="medium"),
        "score_risque": st.column_config.ProgressColumn(
            "Score Risque", 
            min_value=0, 
            max_value=100,
            format="%d%%"
        ),
        "responsable_nom": st.column_config.TextColumn("Responsable", width="medium"),
        "actions": st.column_config.TextColumn("Actions", width="small")
    }
    
    # Affichage avec éditeur
    if not display_columns.empty:
        
        # Sélection d'opération pour actions
        selected_operations = st.data_editor(
            display_columns,
            column_config=column_config,
            disabled=list(display_columns.columns),
            hide_index=True,
            use_container_width=True,
            key="operations_table"
        )
        
        # Actions sur les opérations sélectionnées
        show_operations_actions(db_manager, filtered_df, user_session)

def show_manager_view(db_manager, db_utils, user_session: Dict):
    """Vue manager avec KPI et métriques"""
    
    st.subheader("📊 Vue Manager")
    
    try:
        # Récupérer métriques dashboard
        dashboard_data = db_utils.get_dashboard_metrics()
        
        if not dashboard_data:
            st.warning("Aucune donnée disponible pour le dashboard")
            return
        
        # KPI principaux
        st.markdown("### 📈 Indicateurs Clés")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Opérations Totales",
                dashboard_data.get('total_operations', {}).get('value', 0),
                help="Nombre total d'opérations en portefeuille"
            )
        
        with col2:
            st.metric(
                "En Cours",
                dashboard_data.get('operations_actives', {}).get('value', 0),
                help="Opérations actuellement en cours"
            )
        
        with col3:
            st.metric(
                "Score Risque Moyen",
                f"{dashboard_data.get('score_risque_moyen', {}).get('value', 0)}/100",
                help="Score de risque moyen du portefeuille"
            )
        
        with col4:
            budget_info = dashboard_data.get('budget_total', {})
            st.metric(
                "Budget Total",
                budget_info.get('value', '€0'),
                help="Budget total du portefeuille"
            )
        
        # Graphiques dashboard
        st.markdown("### 📊 Analyses Visuelles")
        
        # Récupérer données complètes pour graphiques
        metrics_data = db_manager.get_operations_dashboard()
        
        if metrics_data:
            # Graphique dashboard principal
            dashboard_fig = create_dashboard_metrics(metrics_data)
            st.plotly_chart(dashboard_fig, use_container_width=True)
        
        # TOP 3 des risques
        st.markdown("### 🚨 TOP 3 des Opérations à Risque")
        
        top_risks = db_manager.get_top_risks(3)
        
        if top_risks:
            for i, risk_op in enumerate(top_risks, 1):
                with st.expander(f"#{i} - {risk_op['nom']} (Score: {risk_op['score_risque']}/100)"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {risk_op['type_operation']}")
                        st.write(f"**Statut:** {risk_op['statut_global']}")
                        st.write(f"**Responsable:** {risk_op.get('responsable_nom', 'Non assigné')}")
                    
                    with col2:
                        st.write(f"**Budget:** {format_number_french(risk_op.get('budget_initial', 0))}€")
                        st.write(f"**Alertes actives:** {risk_op.get('nb_alertes_actives', 0)}")
                        
                        # Badge score de risque
                        st.markdown(
                            FormComponents.risk_score_badge(risk_op['score_risque']),
                            unsafe_allow_html=True
                        )
        else:
            st.info("Aucune opération à risque identifiée")
        
        # Évolution budgétaire globale
        st.markdown("### 💰 Évolution Budgétaire Globale")
        
        budget_evolution = db_utils.get_budget_evolution_global()
        
        if budget_evolution and budget_evolution.get('evolution_mensuelle'):
            budget_fig = create_budget_evolution_chart(budget_evolution['evolution_mensuelle'])
            st.plotly_chart(budget_fig, use_container_width=True)
        else:
            st.info("Aucune donnée d'évolution budgétaire disponible")
    
    except Exception as e:
        logger.error(f"Erreur vue manager: {e}")
        st.error(f"Erreur lors du chargement de la vue manager: {e}")

def show_timeline_view(db_manager, db_utils, user_session: Dict):
    """Vue timeline avec opération sélectionnable"""
    
    st.subheader("🎯 Timeline des Opérations")
    
    # Sélection d'opération
    operations_options = db_utils.get_operations_for_selectbox(user_session.get('user_id'))
    
    if not operations_options:
        st.warning("Aucune opération disponible")
        return
    
    selected_op_id = st.selectbox(
        "Sélectionner une opération",
        options=list(operations_options.keys()),
        format_func=lambda x: operations_options[x],
        key="timeline_operation_select"
    )
    
    if not selected_op_id:
        return
    
    try:
        # Récupérer données timeline
        timeline_data = db_manager.get_timeline_data(selected_op_id)
        
        if not timeline_data:
            st.warning("Aucune donnée timeline disponible")
            return
        
        # Informations opération
        operation = db_manager.get_operation(selected_op_id)
        
        if operation:
            with st.expander("ℹ️ Informations Opération", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Nom:** {operation['nom']}")
                    st.write(f"**Type:** {operation['type_operation']}")
                
                with col2:
                    st.write(f"**Statut:** {operation['statut_global']}")
                    st.write(f"**Budget:** {format_number_french(operation.get('budget_initial', 0))}€")
                
                with col3:
                    st.write(f"**Score Risque:** {operation.get('score_risque', 0)}/100")
                    if operation.get('responsable_id'):
                        # Récupérer nom responsable
                        st.write(f"**Responsable:** [Responsable]")
        
        # Timeline interactive
        if timeline_data.get('phases'):
            timeline_fig = generate_timeline(
                timeline_data['phases'],
                timeline_data.get('alertes', []),
                timeline_data.get('journal', [])
            )
            
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        # Détails phases
        st.markdown("### 📋 Détail des Phases")
        
        phases_df = db_utils.get_phases_dataframe(selected_op_id)
        
        if not phases_df.empty:
            # Colonnes d'affichage
            display_cols = ['nom_phase', 'statut_phase', 'progression_pct', 
                          'date_debut_prevue', 'date_fin_prevue', 'principale']
            
            phases_display = phases_df[display_cols].copy()
            phases_display['statut_badge'] = phases_df['statut_phase'].apply(
                lambda x: FormComponents.status_badge(x, 'small')
            )
            
            st.dataframe(
                phases_display,
                column_config={
                    "nom_phase": "Phase",
                    "statut_badge": st.column_config.TextColumn("Statut"),
                    "progression_pct": st.column_config.ProgressColumn("Progression", min_value=0, max_value=100),
                    "date_debut_prevue": "Début Prévu",
                    "date_fin_prevue": "Fin Prévue",
                    "principale": st.column_config.CheckboxColumn("Principale")
                },
                hide_index=True,
                use_container_width=True
            )
        
        # Alertes actives sur cette opération
        alertes_actives = timeline_data.get('alertes', [])
        
        if alertes_actives:
            st.markdown("### 🚨 Alertes Actives")
            
            for alerte in alertes_actives:
                alert_level = alerte.get('niveau_severite', 'MOYEN')
                alert_color = config.TYPES_ALERTES.get(alerte.get('type_alerte', 'TECHNIQUE'), {}).get('couleur', '#666666')
                
                st.markdown(f"""
                <div style="
                    border-left: 4px solid {alert_color};
                    background-color: #f8f9fa;
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 4px;
                ">
                    <strong>{alerte.get('titre', 'Alerte')}</strong> 
                    <span style="color: {alert_color}; font-weight: bold;">({alert_level})</span><br>
                    <small>{alerte.get('description', '')}</small><br>
                    <small style="color: #666;">Créée le: {alerte.get('date_creation', '')}</small>
                </div>
                """, unsafe_allow_html=True)
    
    except Exception as e:
        logger.error(f"Erreur timeline: {e}")
        st.error(f"Erreur lors du chargement de la timeline: {e}")

def show_new_operation_form(db_manager, db_utils, user_session: Dict):
    """Formulaire de création d'une nouvelle opération"""
    
    st.subheader("➕ Nouvelle Opération")
    
    # Options pour le formulaire
    user_options = db_utils.get_users_for_selectbox()
    
    # Formulaire principal
    operation_data = FormComponents.operation_form(
        operation_data=None,
        user_options=user_options
    )
    
    if operation_data:
        try:
            # Créer l'opération
            operation_id = db_manager.create_operation(
                operation_data, 
                user_session['user_id']
            )
            
            if operation_id:
                FormComponents.alert_message(
                    f"Opération '{operation_data['nom']}' créée avec succès !",
                    "success"
                )
                
                # Calculer score de risque initial
                db_manager.calculate_risk_score(operation_id)
                
                # Actualiser cache
                st.cache_data.clear()
                
                # Proposer d'aller à la timeline
                if st.button("🎯 Voir la Timeline de cette opération"):
                    st.session_state['selected_operation'] = operation_id
                    st.experimental_rerun()
            else:
                FormComponents.alert_message(
                    "Erreur lors de la création de l'opération",
                    "error"
                )
        
        except Exception as e:
            logger.error(f"Erreur création opération: {e}")
            FormComponents.alert_message(
                f"Erreur lors de la création: {e}",
                "error"
            )

# Fonctions utilitaires

def apply_portfolio_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """Appliquer les filtres au portefeuille d'opérations"""
    
    filtered_df = df.copy()
    
    # Filtre type d'opération
    if filters.get('type_operation'):
        filtered_df = filtered_df[filtered_df['type_operation'].isin(filters['type_operation'])]
    
    # Filtre statut
    if filters.get('statut_global'):
        filtered_df = filtered_df[filtered_df['statut_global'].isin(filters['statut_global'])]
    
    # Filtre score de risque
    if filters.get('score_risque_min', 0) > 0:
        filtered_df = filtered_df[filtered_df['score_risque'] >= filters['score_risque_min']]
    
    # Filtre budget
    if filters.get('budget_min') is not None and filters.get('budget_max') is not None:
        filtered_df = filtered_df[
            (filtered_df['budget_initial'] >= filters['budget_min']) &
            (filtered_df['budget_initial'] <= filters['budget_max'])
        ]
    
    return filtered_df

def prepare_operations_display(df: pd.DataFrame) -> pd.DataFrame:
    """Préparer les colonnes d'affichage pour la table des opérations"""
    
    if df.empty:
        return df
    
    display_df = df.copy()
    
    # Formater statut avec badge
    display_df['statut_display'] = df['statut_global'].apply(
        lambda x: FormComponents.status_badge(x, 'small')
    )
    
    # Formater budget
    display_df['budget_display'] = df['budget_initial'].apply(
        lambda x: format_number_french(x) + "€" if pd.notna(x) and x > 0 else "Non défini"
    )
    
    # Colonnes à afficher
    columns_to_show = [
        'nom', 'type_operation', 'statut_display', 
        'budget_display', 'score_risque', 'secteur_geographique'
    ]
    
    # Ajouter responsable si disponible
    if 'responsable_id' in df.columns:
        # Simplification : afficher l'ID pour l'instant
        display_df['responsable_nom'] = df['responsable_id'].fillna('Non assigné')
        columns_to_show.append('responsable_nom')
    
    return display_df[columns_to_show]

def show_operations_actions(db_manager, operations_df: pd.DataFrame, user_session: Dict):
    """Afficher les actions possibles sur les opérations"""
    
    st.markdown("### ⚡ Actions Rapides")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Recalculer tous les scores de risque"):
            with st.spinner("Recalcul en cours..."):
                count = db_manager.recalculate_all_scores()
                st.success(f"✅ {count} scores recalculés")
                st.cache_data.clear()
    
    with col2:
        if st.button("📊 Mettre à jour tous les statuts"):
            with st.spinner("Mise à jour en cours..."):
                count = db_manager.update_all_statuses()
                st.success(f"✅ {count} statuts mis à jour")
                st.cache_data.clear()
    
    with col3:
        if st.button("🚨 Générer toutes les alertes"):
            with st.spinner("Génération des alertes..."):
                db_manager.generate_alerts()
                st.success("✅ Alertes générées")
                st.cache_data.clear()
    
    with col4:
        if st.button("📥 Exporter le portefeuille"):
            # Redirection vers module exports
            st.session_state['export_request'] = 'portfolio'
            st.info("👉 Rendez-vous dans l'onglet Exports")
"""
Module de gestion des risques et alertes SPIC 2.0
Score automatique, TOP 3 risques, alertes intelligentes
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
from utils.risk_score import calculate_risk_score, get_risk_trend
from utils.constants import UI_MESSAGES, CACHE_CONFIG

logger = logging.getLogger(__name__)

def show_gestion_risques(db_manager, user_session: Dict):
    """Interface principale de gestion des risques"""
    
    st.header("🚨 Gestion des Risques")
    
    # Navigation par onglets (cohérent avec autres modules)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard Risques",
        "🏆 TOP Risques", 
        "🚨 Alertes Actives",
        "📈 Analyse Détaillée"
    ])
    
    db_utils = DatabaseUtils(db_manager)
    
    with tab1:
        show_risk_dashboard(db_manager, db_utils, user_session)
    
    with tab2:
        show_top_risks(db_manager, db_utils, user_session)
    
    with tab3:
        show_active_alerts(db_manager, db_utils, user_session)
    
    with tab4:
        show_detailed_risk_analysis(db_manager, db_utils, user_session)

def show_risk_dashboard(db_manager, db_utils, user_session: Dict):
    """Dashboard principal des risques"""
    
    st.subheader("📊 Dashboard des Risques")
    
    try:
        # Actions rapides
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Recalculer tous les scores"):
                with st.spinner("Recalcul en cours..."):
                    count = db_manager.recalculate_all_scores()
                    st.success(f"✅ {count} scores recalculés")
                    st.cache_data.clear()
        
        with col2:
            if st.button("🚨 Générer toutes les alertes"):
                with st.spinner("Génération des alertes..."):
                    db_manager.generate_alerts()
                    st.success("✅ Alertes générées")
                    st.cache_data.clear()
        
        with col3:
            if st.button("📥 Exporter analyse risques"):
                st.session_state['export_request'] = 'risks'
                st.info("👉 Rendez-vous dans l'onglet Exports")
        
        # Métriques globales des risques
        risk_metrics = get_global_risk_metrics(db_manager, user_session.get('user_id'))
        
        if risk_metrics:
            st.markdown("### 📈 Métriques Globales")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                create_metric_card(
                    "Score Moyen",
                    f"{risk_metrics['score_moyen']:.0f}/100",
                    delta=risk_metrics.get('evolution_score'),
                    help_text="Score de risque moyen du portefeuille"
                )
            
            with col2:
                create_metric_card(
                    "Opérations Critiques",
                    risk_metrics['operations_critiques'],
                    help_text="Opérations avec score ≥ 75"
                )
            
            with col3:
                create_metric_card(
                    "Alertes Actives",
                    risk_metrics['alertes_actives'],
                    help_text="Nombre d'alertes actives"
                )
            
            with col4:
                create_metric_card(
                    "Alertes Critiques",
                    risk_metrics['alertes_critiques'],
                    help_text="Alertes de niveau critique"
                )
        
        # Graphiques dashboard
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des scores de risque
            risk_distribution = get_risk_distribution(db_manager, user_session.get('user_id'))
            if risk_distribution:
                fig_distribution = create_risk_distribution_chart(risk_distribution)
                st.plotly_chart(fig_distribution, use_container_width=True)
        
        with col2:
            # Répartition des alertes par type
            alerts_by_type = get_alerts_by_type(db_manager, user_session.get('user_id'))
            if alerts_by_type:
                fig_alerts = create_alerts_by_type_chart(alerts_by_type)
                st.plotly_chart(fig_alerts, use_container_width=True)
        
        # Évolution temporelle des risques
        risk_evolution = get_risk_evolution_data(db_manager, user_session.get('user_id'))
        if risk_evolution:
            st.markdown("### 📅 Évolution des Risques dans le Temps")
            fig_evolution = create_risk_evolution_chart(risk_evolution)
            st.plotly_chart(fig_evolution, use_container_width=True)
        
        # Matrice risques par type d'opération
        risk_matrix = get_risk_by_operation_type(db_manager, user_session.get('user_id'))
        if risk_matrix:
            st.markdown("### 🎯 Risques par Type d'Opération")
            
            for op_type, data in risk_matrix.items():
                with st.expander(f"📋 {op_type} - Score moyen: {data['score_moyen']:.0f}/100"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Opérations:** {data['nb_operations']}")
                        st.write(f"**Score minimum:** {data['score_min']}/100")
                        st.write(f"**Score maximum:** {data['score_max']}/100")
                    
                    with col2:
                        st.write(f"**Opérations à risque élevé:** {data['nb_risque_eleve']}")
                        st.write(f"**Opérations critiques:** {data['nb_critiques']}")
                        
                        # Badge niveau de risque moyen
                        st.markdown(
                            FormComponents.risk_score_badge(int(data['score_moyen'])),
                            unsafe_allow_html=True
                        )
    
    except Exception as e:
        logger.error(f"Erreur dashboard risques: {e}")
        FormComponents.alert_message(f"Erreur chargement dashboard: {e}", "error")

def show_top_risks(db_manager, db_utils, user_session: Dict):
    """TOP des opérations à risque"""
    
    st.subheader("🏆 TOP des Opérations à Risque")
    
    # Contrôles
    col1, col2 = st.columns([3, 1])
    
    with col1:
        limit = st.selectbox(
            "Nombre d'opérations à afficher",
            options=[5, 10, 15, 20],
            index=1,
            key="top_risks_limit"
        )
    
    with col2:
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    try:
        # Récupérer TOP risques
        top_risks = db_manager.get_top_risks(limit)
        
        if not top_risks:
            st.success("✅ Aucune opération à risque élevé identifiée")
            return
        
        # Affichage du TOP
        st.markdown("### 🚨 Classement par Score de Risque")
        
        for i, risk_op in enumerate(top_risks, 1):
            # Couleur selon niveau de risque
            score = risk_op.get('score_risque', 0)
            
            if score >= 75:
                border_color = "#F44336"  # Rouge critique
            elif score >= 50:
                border_color = "#FF9800"  # Orange élevé
            else:
                border_color = "#FFD54F"  # Jaune moyen
            
            with st.expander(f"#{i} - {risk_op['nom']} - Score: {score}/100", expanded=i <= 3):
                
                # En-tête avec badge
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(
                        FormComponents.risk_score_badge(score),
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        FormComponents.status_badge(risk_op.get('statut_global', 'EN_COURS')),
                        unsafe_allow_html=True
                    )
                
                with col2:
                    if st.button(f"🎯 Voir Timeline", key=f"timeline_{risk_op['id']}"):
                        st.session_state['selected_operation'] = risk_op['id']
                        st.session_state['redirect_to'] = 'timeline'
                        st.info("👉 Redirection vers Timeline")
                
                with col3:
                    if st.button(f"📊 Analyse Détaillée", key=f"analysis_{risk_op['id']}"):
                        st.session_state['detailed_analysis_op'] = risk_op['id']
                
                # Informations détaillées
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {risk_op['type_operation']}")
                    st.write(f"**Budget:** {format_number_french(risk_op.get('budget_initial', 0))}€")
                    st.write(f"**Responsable:** {risk_op.get('responsable_nom', 'Non assigné')} {risk_op.get('responsable_prenom', '')}")
                
                with col2:
                    st.write(f"**Alertes actives:** {risk_op.get('nb_alertes_actives', 0)}")
                    st.write(f"**Secteur:** {risk_op.get('secteur_geographique', 'Non défini')}")
                    st.write(f"**Dernière MAJ:** {risk_op.get('updated_at', '')[:10] if risk_op.get('updated_at') else 'N/A'}")
                
                # Analyse rapide du risque
                if score >= 50:  # Seulement pour risques significatifs
                    show_quick_risk_analysis(db_manager, risk_op['id'])
    
    except Exception as e:
        logger.error(f"Erreur TOP risques: {e}")
        FormComponents.alert_message(f"Erreur chargement TOP risques: {e}", "error")

def show_active_alerts(db_manager, db_utils, user_session: Dict):
    """Gestion des alertes actives"""
    
    st.subheader("🚨 Alertes Actives")
    
    # Filtres alertes
    with st.sidebar:
        st.header("🔍 Filtres Alertes")
        
        # Filtre par niveau
        severity_levels = list(config.NIVEAUX_RISQUE.keys())
        selected_severity = st.multiselect(
            "Niveau de sévérité",
            options=severity_levels,
            default=severity_levels,
            key="alerts_severity_filter"
        )
        
        # Filtre par type
        alert_types = list(config.TYPES_ALERTES.keys())
        selected_types = st.multiselect(
            "Type d'alerte",
            options=alert_types,
            default=alert_types,
            key="alerts_type_filter"
        )
        
        # Filtre par opération
        operations_options = db_utils.get_operations_for_selectbox(user_session.get('user_id'))
        selected_operation = st.selectbox(
            "Opération",
            options=[''] + list(operations_options.keys()),
            format_func=lambda x: 'Toutes les opérations' if x == '' else operations_options.get(x, x),
            key="alerts_operation_filter"
        )
    
    # Actions sur les alertes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Actualiser alertes"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    with col2:
        if st.button("✅ Résoudre toutes les alertes faibles"):
            if FormComponents.confirmation_dialog(
                "Résoudre toutes les alertes de niveau FAIBLE ?", 
                "resolve_low_alerts"
            ):
                count = resolve_alerts_by_level(db_manager, 'FAIBLE', user_session['user_id'])
                st.success(f"✅ {count} alertes résolues")
                st.cache_data.clear()
    
    with col3:
        if st.button("📥 Exporter alertes"):
            st.session_state['export_request'] = 'alerts'
            st.info("👉 Rendez-vous dans l'onglet Exports")
    
    try:
        # Récupérer alertes filtrées
        filtered_alerts = get_filtered_alerts(
            db_manager, selected_severity, selected_types, 
            selected_operation, user_session.get('user_id')
        )
        
        if not filtered_alerts:
            st.success("✅ Aucune alerte active correspondant aux critères")
            return
        
        # Métriques alertes
        show_alerts_metrics(filtered_alerts)
        
        # Affichage des alertes par niveau de priorité
        alerts_by_priority = group_alerts_by_priority(filtered_alerts)
        
        for priority, alerts in alerts_by_priority.items():
            if not alerts:
                continue
            
            priority_config = {
                'CRITIQUE': {'color': '#F44336', 'icon': '🔴'},
                'ELEVE': {'color': '#FF9800', 'icon': '🟠'},
                'MOYEN': {'color': '#FFD54F', 'icon': '🟡'},
                'FAIBLE': {'color': '#4CAF50', 'icon': '🟢'}
            }.get(priority, {'color': '#666666', 'icon': '⭕'})
            
            st.markdown(f"### {priority_config['icon']} Alertes {priority} ({len(alerts)})")
            
            for alerte in alerts:
                with st.expander(f"{alerte.get('titre', 'Alerte')} - {alerte.get('operation_nom', 'Opération')}"):
                    show_alert_detail(db_manager, alerte, user_session)
    
    except Exception as e:
        logger.error(f"Erreur alertes actives: {e}")
        FormComponents.alert_message(f"Erreur chargement alertes: {e}", "error")

def show_detailed_risk_analysis(db_manager, db_utils, user_session: Dict):
    """Analyse détaillée des risques pour une opération"""
    
    st.subheader("📈 Analyse Détaillée des Risques")
    
    # Sélection opération pour analyse
    operations_options = db_utils.get_operations_for_selectbox(user_session.get('user_id'))
    
    # Vérifier si une opération est présélectionnée
    default_op = st.session_state.get('detailed_analysis_op')
    default_index = 0
    
    if default_op and default_op in operations_options:
        default_index = list(operations_options.keys()).index(default_op)
    
    selected_op_id = st.selectbox(
        "Sélectionner une opération pour analyse détaillée",
        options=list(operations_options.keys()),
        format_func=lambda x: operations_options[x],
        index=default_index,
        key="detailed_analysis_operation_select"
    )
    
    if not selected_op_id:
        return
    
    try:
        # Récupérer données complètes pour analyse
        operation = db_manager.get_operation(selected_op_id)
        phases = db_manager.get_phases_by_operation(selected_op_id)
        alerts = db_manager.get_active_alerts(selected_op_id)
        
        if not operation:
            st.error("Opération non trouvée")
            return
        
        # Calculer score de risque détaillé
        risk_analysis = calculate_risk_score(operation, phases, alerts)
        
        # En-tête avec informations opération
        with st.expander("ℹ️ Informations Opération", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Nom:** {operation['nom']}")
                st.write(f"**Type:** {operation['type_operation']}")
                st.write(f"**Statut:** {operation['statut_global']}")
            
            with col2:
                st.write(f"**Budget:** {format_number_french(operation.get('budget_initial', 0))}€")
                st.write(f"**Score Actuel:** {operation.get('score_risque', 0)}/100")
                if operation.get('surface_m2'):
                    st.write(f"**Surface:** {format_number_french(operation['surface_m2'])} m²")
            
            with col3:
                st.write(f"**Secteur:** {operation.get('secteur_geographique', 'Non défini')}")
                st.write(f"**Dernière MAJ:** {operation.get('updated_at', '')[:10] if operation.get('updated_at') else 'N/A'}")
                
                # Badge score avec couleur
                st.markdown(
                    FormComponents.risk_score_badge(operation.get('score_risque', 0)),
                    unsafe_allow_html=True
                )
        
        # Analyse détaillée du risque
        if risk_analysis:
            st.markdown("### 🔍 Analyse Détaillée du Score de Risque")
            
            # Score global et niveau
            col1, col2 = st.columns(2)
            
            with col1:
                # Gauge du score total
                fig_gauge = create_risk_gauge(risk_analysis['score_total'])
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col2:
                # Métriques détaillées
                create_metric_card(
                    "Score Total",
                    f"{risk_analysis['score_total']}/100",
                    help_text=f"Niveau: {risk_analysis['niveau_risque']}"
                )
                
                create_metric_card(
                    "Dernière Évaluation",
                    risk_analysis['calcul_date'][:10],
                    help_text="Date du dernier calcul"
                )
            
            # Détail des composantes du score
            st.markdown("#### 📊 Composantes du Score")
            
            scores_detail = risk_analysis.get('scores_detail', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                create_metric_card(
                    "Retards",
                    f"{scores_detail.get('retard', 0)}/100",
                    help_text="Impact des retards (25%)"
                )
                
                create_metric_card(
                    "Alertes",
                    f"{scores_detail.get('alertes', 0)}/100", 
                    help_text="Impact des alertes (20%)"
                )
            
            with col2:
                create_metric_card(
                    "Budget",
                    f"{scores_detail.get('budget', 0)}/100",
                    help_text="Impact budgétaire (30%)"
                )
                
                create_metric_card(
                    "Blocages",
                    f"{scores_detail.get('blocages', 0)}/100",
                    help_text="Phases bloquées (15%)"
                )
            
            with col3:
                create_metric_card(
                    "Avancement",
                    f"{scores_detail.get('avancement', 0)}/100",
                    help_text="Retard d'avancement (10%)"
                )
            
            # Graphique radar des composantes
            if scores_detail:
                fig_radar = create_risk_components_radar(scores_detail)
                st.plotly_chart(fig_radar, use_container_width=True)
            
            # Explications détaillées
            st.markdown("#### 📋 Explications Détaillées")
            
            explications = risk_analysis.get('explications', {})
            
            for component, details in explications.items():
                component_names = {
                    'retard': '⏰ Retards',
                    'budget': '💰 Budget', 
                    'alertes': '🚨 Alertes',
                    'blocages': '🔒 Blocages',
                    'avancement': '📈 Avancement'
                }
                
                component_name = component_names.get(component, component)
                
                with st.expander(f"{component_name} - Score: {scores_detail.get(component, 0)}/100"):
                    for key, value in details.items():
                        if isinstance(value, list):
                            if value:  # Si la liste n'est pas vide
                                st.write(f"**{key.replace('_', ' ').title()}:**")
                                for item in value:
                                    if isinstance(item, dict):
                                        st.write(f"- {item.get('nom', '')} ({item.get('retard_jours', 0)} jours)")
                                    else:
                                        st.write(f"- {item}")
                        else:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            
            # Recommandations
            recommandations = risk_analysis.get('recommandations', [])
            
            if recommandations:
                st.markdown("#### 💡 Recommandations")
                
                for i, reco in enumerate(recommandations, 1):
                    st.markdown(f"{i}. {reco}")
            
            # Historique des scores (si disponible)
            historical_scores = get_risk_score_history(db_manager, selected_op_id)
            
            if historical_scores and len(historical_scores) > 1:
                st.markdown("#### 📈 Évolution du Score de Risque")
                
                fig_history = create_risk_history_chart(historical_scores)
                st.plotly_chart(fig_history, use_container_width=True)
                
                # Tendance
                trend = get_risk_trend(historical_scores)
                
                trend_messages = {
                    'amelioration': "📉 Tendance à l'amélioration",
                    'degradation': "📈 Tendance à la dégradation", 
                    'stable': "➡️ Tendance stable"
                }
                
                trend_colors = {
                    'amelioration': 'success',
                    'degradation': 'error',
                    'stable': 'info'
                }
                
                FormComponents.alert_message(
                    f"{trend_messages.get(trend['trend'], 'Tendance inconnue')} ({trend['evolution']:+.0f} points)",
                    trend_colors.get(trend['trend'], 'info')
                )
        
        # Actions recommandées
        st.markdown("### ⚡ Actions Recommandées")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Recalculer le score", key="recalc_score"):
                new_score = db_manager.calculate_risk_score(selected_op_id)
                st.success(f"✅ Score recalculé: {new_score}/100")
                st.cache_data.clear()
                st.experimental_rerun()
        
        with col2:
            if st.button("🚨 Générer alertes", key="gen_alerts"):
                db_manager.generate_alerts(selected_op_id)
                st.success("✅ Alertes générées")
                st.cache_data.clear()
        
        with col3:
            if st.button("🎯 Voir Timeline", key="view_timeline"):
                st.session_state['selected_operation'] = selected_op_id
                st.session_state['redirect_to'] = 'timeline'
                st.info("👉 Redirection vers Timeline")
    
    except Exception as e:
        logger.error(f"Erreur analyse détaillée: {e}")
        FormComponents.alert_message(f"Erreur analyse détaillée: {e}", "error")

# Fonctions utilitaires cohérentes avec l'architecture

def show_quick_risk_analysis(db_manager, operation_id: str):
    """Analyse rapide du risque pour une opération"""
    
    try:
        operation = db_manager.get_operation(operation_id)
        phases = db_manager.get_phases_by_operation(operation_id)
        alerts = db_manager.get_active_alerts(operation_id)
        
        if operation and phases:
            risk_analysis = calculate_risk_score(operation, phases, alerts)
            
            if risk_analysis:
                st.markdown("**🔍 Analyse Rapide:**")
                
                # Principales causes de risque
                scores = risk_analysis.get('scores_detail', {})
                max_score_component = max(scores.items(), key=lambda x: x[1]) if scores else None
                
                if max_score_component:
                    component_names = {
                        'retard': 'retards de planning',
                        'budget': 'dépassements budgétaires',
                        'alertes': 'alertes actives',
                        'blocages': 'phases bloquées',
                        'avancement': 'retard d\'avancement'
                    }
                    
                    main_cause = component_names.get(max_score_component[0], max_score_component[0])
                    st.write(f"🎯 **Cause principale:** {main_cause} (score: {max_score_component[1]}/100)")
                
                # Première recommandation
                recommandations = risk_analysis.get('recommandations', [])
                if recommandations:
                    st.write(f"💡 **Action prioritaire:** {recommandations[0]}")
    
    except Exception as e:
        logger.error(f"Erreur analyse rapide: {e}")

def show_alert_detail(db_manager, alerte: Dict, user_session: Dict):
    """Afficher détail d'une alerte avec actions"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"**Type:** {alerte.get('type_alerte', 'TECHNIQUE')}")
        st.write(f"**Description:** {alerte.get('description', '')}")
        st.write(f"**Créée le:** {alerte.get('date_creation', '')}")
        
        # Paramètres de l'alerte si disponibles
        if alerte.get('parametres'):
            try:
                import json
                params = json.loads(alerte['parametres'])
                st.write("**Paramètres:**")
                for key, value in params.items():
                    st.write(f"- {key}: {value}")
            except:
                pass
    
    with col2:
        # Actions sur l'alerte
        if st.button(f"✅ Résoudre", key=f"resolve_alert_{alerte['id']}"):
            if db_manager.resolve_alert(alerte['id'], user_session['user_id']):
                st.success("✅ Alerte résolue")
                st.cache_data.clear()
                st.experimental_rerun()
            else:
                st.error("❌ Erreur lors de la résolution")
        
        if alerte.get('operation_id'):
            if st.button(f"🎯 Voir Opération", key=f"view_op_{alerte['id']}"):
                st.session_state['selected_operation'] = alerte['operation_id']
                st.session_state['redirect_to'] = 'timeline'
                st.info("👉 Redirection vers Timeline")

def show_alerts_metrics(alerts: List[Dict]):
    """Métriques des alertes (cohérent avec autres métriques)"""
    
    if not alerts:
        return
    
    # Compter par niveau
    severity_counts = {}
    for alert in alerts:
        level = alert.get('niveau_severite', 'MOYEN')
        severity_counts[level] = severity_counts.get(level, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Total Alertes",
            len(alerts),
            help_text="Nombre total d'alertes actives"
        )
    
    with col2:
        create_metric_card(
            "Critiques",
            severity_counts.get('CRITIQUE', 0),
            help_text="Alertes de niveau critique"
        )
    
    with col3:
        create_metric_card(
            "Élevées",
            severity_counts.get('ELEVE', 0),
            help_text="Alertes de niveau élevé"
        )
    
    with col4:
        operations_avec_alertes = len(set(a['operation_id'] for a in alerts if a.get('operation_id')))
        create_metric_card(
            "Opérations Concernées",
            operations_avec_alertes,
            help_text="Nombre d'opérations avec alertes"
        )

# Fonctions de récupération des données (cohérentes avec cache)

@st.cache_data(ttl=CACHE_CONFIG['dashboard'])
def get_global_risk_metrics(db_manager, user_id: str) -> Dict:
    """Métriques globales des risques"""
    
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
            
            # Métriques de base
            query = f"""
                SELECT 
                    AVG(score_risque) as score_moyen,
                    SUM(CASE WHEN score_risque >= 75 THEN 1 ELSE 0 END) as operations_critiques,
                    COUNT(*) as total_operations
                FROM operations o
                WHERE {' AND '.join(where_conditions)}
            """
            
            cursor.execute(query, params)
            metrics = dict(cursor.fetchone())
            
            # Compter alertes actives
            cursor.execute("""
                SELECT 
                    COUNT(*) as alertes_actives,
                    SUM(CASE WHEN niveau_severite = 'CRITIQUE' THEN 1 ELSE 0 END) as alertes_critiques
                FROM alertes a
                LEFT JOIN operations o ON a.operation_id = o.id
                WHERE a.actif = 1
            """)
            
            alert_metrics = dict(cursor.fetchone())
            
            return {
                **metrics,
                **alert_metrics,
                'score_moyen': metrics.get('score_moyen', 0) or 0
            }
            
    except Exception as e:
        logger.error(f"Erreur métriques globales risques: {e}")
        return {}

@st.cache_data(ttl=CACHE_CONFIG['dashboard'])
def get_risk_distribution(db_manager, user_id: str) -> List[Dict]:
    """Distribution des scores de risque"""
    
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
                    CASE 
                        WHEN score_risque >= 75 THEN 'CRITIQUE'
                        WHEN score_risque >= 50 THEN 'ELEVE'
                        WHEN score_risque >= 25 THEN 'MOYEN'
                        ELSE 'FAIBLE'
                    END as niveau_risque,
                    COUNT(*) as count
                FROM operations o
                WHERE {' AND '.join(where_conditions)}
                GROUP BY niveau_risque
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur distribution risques: {e}")
        return []

@st.cache_data(ttl=CACHE_CONFIG['alerts'])
def get_alerts_by_type(db_manager, user_id: str) -> List[Dict]:
    """Répartition des alertes par type"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["a.actif = 1"]
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
                SELECT type_alerte, COUNT(*) as count
                FROM alertes a
                LEFT JOIN operations o ON a.operation_id = o.id
                WHERE {' AND '.join(where_conditions)}
                GROUP BY type_alerte
                ORDER BY count DESC
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur alertes par type: {e}")
        return []

@st.cache_data(ttl=CACHE_CONFIG['dashboard'])
def get_risk_by_operation_type(db_manager, user_id: str) -> Dict:
    """Risques par type d'opération"""
    
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
                    COUNT(*) as nb_operations,
                    AVG(score_risque) as score_moyen,
                    MIN(score_risque) as score_min,
                    MAX(score_risque) as score_max,
                    SUM(CASE WHEN score_risque >= 50 THEN 1 ELSE 0 END) as nb_risque_eleve,
                    SUM(CASE WHEN score_risque >= 75 THEN 1 ELSE 0 END) as nb_critiques
                FROM operations o
                WHERE {' AND '.join(where_conditions)}
                GROUP BY type_operation
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return {row['type_operation']: dict(row) for row in rows}
            
    except Exception as e:
        logger.error(f"Erreur risques par type: {e}")
        return {}

def get_filtered_alerts(db_manager, severity_levels: List[str], alert_types: List[str], 
                       operation_id: str, user_id: str) -> List[Dict]:
    """Récupérer alertes filtrées"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            where_conditions = ["a.actif = 1"]
            params = []
            
            if severity_levels:
                placeholders = ','.join('?' for _ in severity_levels)
                where_conditions.append(f"a.niveau_severite IN ({placeholders})")
                params.extend(severity_levels)
            
            if alert_types:
                placeholders = ','.join('?' for _ in alert_types)
                where_conditions.append(f"a.type_alerte IN ({placeholders})")
                params.extend(alert_types)
            
            if operation_id:
                where_conditions.append("a.operation_id = ?")
                params.append(operation_id)
            
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
                ORDER BY 
                    CASE a.niveau_severite 
                        WHEN 'CRITIQUE' THEN 1 
                        WHEN 'ELEVE' THEN 2 
                        WHEN 'MOYEN' THEN 3 
                        ELSE 4 
                    END,
                    a.date_creation DESC
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur alertes filtrées: {e}")
        return []

def group_alerts_by_priority(alerts: List[Dict]) -> Dict[str, List[Dict]]:
    """Grouper alertes par niveau de priorité"""
    
    grouped = {'CRITIQUE': [], 'ELEVE': [], 'MOYEN': [], 'FAIBLE': []}
    
    for alert in alerts:
        level = alert.get('niveau_severite', 'MOYEN')
        if level in grouped:
            grouped[level].append(alert)
    
    return grouped

def resolve_alerts_by_level(db_manager, level: str, user_id: str) -> int:
    """Résoudre toutes les alertes d'un niveau donné"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE alertes 
                SET statut = 'RESOLVED', date_resolution = CURRENT_TIMESTAMP, 
                    resolu_par = ?, actif = 0
                WHERE niveau_severite = ? AND actif = 1
            """, (user_id, level))
            
            conn.commit()
            return cursor.rowcount
            
    except Exception as e:
        logger.error(f"Erreur résolution alertes niveau {level}: {e}")
        return 0

@st.cache_data(ttl=CACHE_CONFIG['operations'])
def get_risk_score_history(db_manager, operation_id: str) -> List[Dict]:
    """Historique des scores de risque pour une opération"""
    
    try:
        # Pour l'instant, simuler un historique simple
        # Dans une version future, on pourrait avoir une table d'historique
        operation = db_manager.get_operation(operation_id)
        
        if not operation:
            return []
        
        current_score = operation.get('score_risque', 0)
        
        # Simuler historique basé sur dates de modification
        return [
            {
                'date': operation.get('updated_at', datetime.now().isoformat())[:10],
                'score_total': current_score
            }
        ]
        
    except Exception as e:
        logger.error(f"Erreur historique scores: {e}")
        return []

def get_risk_evolution_data(db_manager, user_id: str) -> List[Dict]:
    """Données d'évolution des risques dans le temps"""
    
    try:
        # Version simplifiée - à améliorer avec table d'historique
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
                    DATE(updated_at) as date,
                    AVG(score_risque) as score_moyen,
                    COUNT(*) as nb_operations
                FROM operations o
                WHERE {' AND '.join(where_conditions)}
                GROUP BY DATE(updated_at)
                ORDER BY date DESC
                LIMIT 30
            """
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Erreur évolution risques: {e}")
        return []

# Fonctions de création des graphiques (cohérentes avec utils/)

def create_risk_distribution_chart(distribution_data: List[Dict]):
    """Graphique distribution des risques"""
    
    if not distribution_data:
        return go.Figure()
    
    df = pd.DataFrame(distribution_data)
    
    colors = {
        'CRITIQUE': '#F44336',
        'ELEVE': '#FF9800',
        'MOYEN': '#FFD54F',
        'FAIBLE': '#4CAF50'
    }
    
    df['color'] = df['niveau_risque'].map(colors)
    
    fig = px.pie(
        df,
        values='count',
        names='niveau_risque',
        title="Distribution des Niveaux de Risque",
        color='niveau_risque',
        color_discrete_map=colors
    )
    
    fig.update_traces(textinfo='percent+label+value')
    fig.update_layout(height=400)
    
    return fig

def create_alerts_by_type_chart(alerts_data: List[Dict]):
    """Graphique alertes par type"""
    
    if not alerts_data:
        return go.Figure()
    
    df = pd.DataFrame(alerts_data)
    
    # Couleurs selon config
    colors = [config.TYPES_ALERTES.get(alert_type, {}).get('couleur', '#666666') 
             for alert_type in df['type_alerte']]
    
    fig = px.bar(
        df,
        x='type_alerte',
        y='count',
        title="Répartition des Alertes par Type",
        color='count',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        xaxis_title="Type d'Alerte",
        yaxis_title="Nombre d'Alertes",
        height=400
    )
    
    return fig

def create_risk_gauge(score: int):
    """Gauge pour score de risque"""
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Score de Risque"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': calculate_score_color(score)},
            'steps': [
                {'range': [0, 25], 'color': "#E8F5E8"},
                {'range': [25, 50], 'color': "#FFF3E0"},
                {'range': [50, 75], 'color': "#FFE0B2"},
                {'range': [75, 100], 'color': "#FFEBEE"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_risk_components_radar(scores_detail: Dict):
    """Graphique radar des composantes du risque"""
    
    categories = ['Retards', 'Budget', 'Alertes', 'Blocages', 'Avancement']
    values = [
        scores_detail.get('retard', 0),
        scores_detail.get('budget', 0),
        scores_detail.get('alertes', 0),
        scores_detail.get('blocages', 0),
        scores_detail.get('avancement', 0)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Score de Risque',
        line_color='rgb(255, 100, 100)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title="Composantes du Score de Risque",
        height=400
    )
    
    return fig

def create_risk_history_chart(history_data: List[Dict]):
    """Graphique historique des scores"""
    
    if not history_data:
        return go.Figure()
    
    df = pd.DataFrame(history_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = px.line(
        df,
        x='date',
        y='score_total',
        title="Évolution du Score de Risque",
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Score de Risque",
        height=300
    )
    
    return fig

def create_risk_evolution_chart(evolution_data: List[Dict]):
    """Graphique évolution des risques globaux"""
    
    if not evolution_data:
        return go.Figure()
    
    df = pd.DataFrame(evolution_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = px.line(
        df,
        x='date',
        y='score_moyen',
        title="Évolution du Score de Risque Moyen",
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Score Moyen",
        height=400
    )
    
    return fig
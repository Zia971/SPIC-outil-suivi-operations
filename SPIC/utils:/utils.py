"""
Fonctions utilitaires générales pour SPIC 2.0
Timeline, calculs, visualisations, helpers interface
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
import config
from .constants import TIMELINE_PARAMS, CACHE_CONFIG, UI_MESSAGES
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TIMELINE COLORÉE DYNAMIQUE
# ============================================================================

@st.cache_data(ttl=CACHE_CONFIG['timeline'])
def generate_timeline(phases_data: List[Dict], alertes_data: List[Dict] = None, 
                     journal_data: List[Dict] = None) -> go.Figure:
    """Générer timeline colorée style PowerPoint avec alertes intégrées"""
    
    if not phases_data:
        return go.Figure().add_annotation(
            text="Aucune phase disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Préparer les données
    phases_df = pd.DataFrame(phases_data)
    phases_df = phases_df.sort_values('ordre')
    
    # Calculer positions et dates
    phases_df['date_debut_calc'] = pd.to_datetime(
        phases_df['date_debut_reelle'].fillna(phases_df['date_debut_prevue']), 
        errors='coerce'
    )
    phases_df['date_fin_calc'] = pd.to_datetime(
        phases_df['date_fin_reelle'].fillna(phases_df['date_fin_prevue']), 
        errors='coerce'
    )
    
    # Couleurs selon statut
    colors_map = {
        'NON_COMMENCE': '#E0E0E0',
        'EN_COURS': '#2196F3', 
        'TERMINE': '#4CAF50',
        'EN_RETARD': '#FF5722',
        'BLOQUE': '#F44336'
    }
    
    phases_df['color'] = phases_df['statut_phase'].map(colors_map).fillna('#E0E0E0')
    
    # Créer la figure
    fig = go.Figure()
    
    # Ligne principale de timeline
    min_date = phases_df['date_debut_calc'].min()
    max_date = phases_df['date_fin_calc'].max()
    
    if pd.isna(min_date) or pd.isna(max_date):
        min_date = datetime.now() - timedelta(days=30)
        max_date = datetime.now() + timedelta(days=365)
    
    # Ligne de base
    fig.add_shape(
        type="line",
        x0=min_date, x1=max_date,
        y0=0, y1=0,
        line=dict(color=config.COULEURS_THEME['primary'], width=6),
    )
    
    # Ajouter les phases
    for idx, phase in phases_df.iterrows():
        if pd.isna(phase['date_debut_calc']) or pd.isna(phase['date_fin_calc']):
            continue
        
        y_pos = 0.5 if phase['principale'] else -0.5
        
        # Barre de phase
        fig.add_shape(
            type="rect",
            x0=phase['date_debut_calc'], x1=phase['date_fin_calc'],
            y0=y_pos-0.2, y1=y_pos+0.2,
            fillcolor=phase['color'],
            opacity=0.8,
            line_width=0
        )
        
        # Marker de début
        fig.add_trace(go.Scatter(
            x=[phase['date_debut_calc']],
            y=[y_pos],
            mode='markers+text',
            marker=dict(
                size=TIMELINE_PARAMS['marker_size'],
                color=phase['color'],
                line=dict(width=2, color='white')
            ),
            text=[f"📌 {phase['nom_phase']}"],
            textposition="top center" if phase['principale'] else "bottom center",
            textfont=dict(size=TIMELINE_PARAMS['font_size']),
            hovertemplate=f"""
            <b>{phase['nom_phase']}</b><br>
            Statut: {config.STATUTS_PHASES.get(phase['statut_phase'], {}).get('libelle', phase['statut_phase'])}<br>
            Progression: {phase.get('progression_pct', 0)}%<br>
            Ordre: {phase['ordre']}<br>
            <extra></extra>
            """,
            showlegend=False,
            name=phase['nom_phase']
        ))
    
    # Ajouter alertes sur timeline
    if alertes_data:
        alertes_df = pd.DataFrame(alertes_data)
        alertes_actives = alertes_df[alertes_df.get('actif', True) == True]
        
        for idx, alerte in alertes_actives.iterrows():
            alerte_date = pd.to_datetime(alerte.get('date_creation', datetime.now()))
            
            color_alerte = '#F44336' if alerte.get('niveau_severite') == 'CRITIQUE' else '#FF9800'
            
            fig.add_trace(go.Scatter(
                x=[alerte_date],
                y=[1],
                mode='markers+text',
                marker=dict(
                    size=12,
                    color=color_alerte,
                    symbol='triangle-up'
                ),
                text=['🚨'],
                textposition="top center",
                hovertemplate=f"""
                <b>Alerte: {alerte.get('titre', 'Alerte')}</b><br>
                Niveau: {alerte.get('niveau_severite', 'MOYEN')}<br>
                Description: {alerte.get('description', '')}<br>
                <extra></extra>
                """,
                showlegend=False,
                name="Alerte"
            ))
    
    # Ajouter événements journal importants
    if journal_data:
        journal_df = pd.DataFrame(journal_data)
        evenements_importants = journal_df[
            journal_df['action'].isin(['CREATE', 'DELETE']) |
            journal_df['table_concernee'].isin(['operations', 'phases_operations'])
        ].head(5)  # Derniers 5 événements importants
        
        for idx, event in evenements_importants.iterrows():
            event_date = pd.to_datetime(event.get('timestamp', datetime.now()))
            
            fig.add_trace(go.Scatter(
                x=[event_date],
                y=[-1],
                mode='markers',
                marker=dict(
                    size=8,
                    color=config.COULEURS_THEME['info'],
                    symbol='circle'
                ),
                hovertemplate=f"""
                <b>Événement: {event.get('action', '')}</b><br>
                Table: {event.get('table_concernee', '')}<br>
                Utilisateur: {event.get('nom', '')} {event.get('prenom', '')}<br>
                Date: {event_date.strftime('%d/%m/%Y %H:%M')}<br>
                <extra></extra>
                """,
                showlegend=False,
                name="Événement"
            ))
    
    # Ligne du temps actuel
    fig.add_shape(
        type="line",
        x0=datetime.now(), x1=datetime.now(),
        y0=-1.5, y1=1.5,
        line=dict(color='red', width=2, dash="dot"),
    )
    
    # Configuration du layout
    fig.update_layout(
        title={
            'text': "Timeline Opération",
            'x': 0.5,
            'font': {'size': 16, 'family': 'Arial'}
        },
        xaxis=dict(
            title="Période",
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            type='date'
        ),
        yaxis=dict(
            range=[-1.8, 1.8],
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        height=TIMELINE_PARAMS['height'],
        margin=TIMELINE_PARAMS['margin'],
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='white'
    )
    
    return fig

# ============================================================================
# CALCULS D'AVANCEMENT ET PROGRESSIONS
# ============================================================================

@st.cache_data(ttl=CACHE_CONFIG['calculations'])
def calculate_global_progress(phases_data: List[Dict]) -> Dict:
    """Calculer la progression globale d'une opération"""
    
    if not phases_data:
        return {
            'progression_globale': 0,
            'phases_terminees': 0,
            'phases_total': 0,
            'phases_en_cours': 0,
            'phases_retard': 0,
            'duree_prevue_total': 0,
            'duree_reelle_total': 0
        }
    
    phases_df = pd.DataFrame(phases_data)
    
    # Statistiques de base
    total_phases = len(phases_df)
    phases_terminees = len(phases_df[phases_df['statut_phase'] == 'TERMINE'])
    phases_en_cours = len(phases_df[phases_df['statut_phase'] == 'EN_COURS'])
    
    # Calcul retards
    today = pd.Timestamp.now()
    phases_df['date_fin_prevue_dt'] = pd.to_datetime(phases_df['date_fin_prevue'], errors='coerce')
    
    phases_retard = len(phases_df[
        (phases_df['date_fin_prevue_dt'] < today) & 
        (phases_df['statut_phase'] != 'TERMINE')
    ])
    
    # Progression pondérée par importance des phases
    progressions = phases_df['progression_pct'].fillna(0)
    
    # Pondération phases principales
    poids = phases_df['principale'].map({True: 1.5, False: 1.0})
    progression_ponderee = (progressions * poids).sum() / poids.sum()
    
    # Durées
    duree_prevue_total = phases_df['duree_prevue'].fillna(0).sum()
    duree_reelle_total = phases_df['duree_reelle'].fillna(0).sum()
    
    return {
        'progression_globale': round(progression_ponderee, 1),
        'phases_terminees': phases_terminees,
        'phases_total': total_phases,
        'phases_en_cours': phases_en_cours,
        'phases_retard': phases_retard,
        'duree_prevue_total': duree_prevue_total,
        'duree_reelle_total': duree_reelle_total,
        'efficacite_planning': round((duree_prevue_total / duree_reelle_total * 100), 1) 
                              if duree_reelle_total > 0 else 100
    }

def calculate_phase_efficiency(phase_data: Dict) -> Dict:
    """Calculer l'efficacité d'une phase"""
    
    duree_prevue = phase_data.get('duree_prevue', 0)
    duree_reelle = phase_data.get('duree_reelle', 0)
    progression = phase_data.get('progression_pct', 0)
    
    if duree_prevue == 0:
        return {'efficacite': 100, 'message': 'Durée prévue non définie'}
    
    if duree_reelle == 0:
        efficacite = progression  # Basé sur progression uniquement
        message = 'En cours'
    else:
        efficacite = (duree_prevue / duree_reelle) * (progression / 100) * 100
        message = 'Terminé' if progression == 100 else 'En cours'
    
    return {
        'efficacite': round(efficacite, 1),
        'message': message,
        'retard_jours': max(0, duree_reelle - duree_prevue) if duree_reelle > 0 else 0
    }

# ============================================================================
# VISUALISATIONS PLOTLY
# ============================================================================

@st.cache_data(ttl=CACHE_CONFIG['dashboard'])
def create_dashboard_metrics(metrics_data: Dict) -> go.Figure:
    """Créer graphique des métriques dashboard"""
    
    # Graphique en gauge pour score de risque moyen
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Score Risque Moyen', 'Répartition Statuts', 
                       'Évolution Budget', 'Phases par Type'),
        specs=[[{"type": "indicator"}, {"type": "pie"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # 1. Gauge score de risque
    score_moyen = metrics_data.get('statistiques', {}).get('score_risque_moyen', 0)
    
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=score_moyen,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Score Risque"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "lightgreen"},
                {'range': [25, 50], 'color': "yellow"},
                {'range': [50, 75], 'color': "orange"},
                {'range': [75, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ), row=1, col=1)
    
    # 2. Pie chart répartition statuts
    repartition_statut = metrics_data.get('repartition_statut', {})
    if repartition_statut:
        labels = list(repartition_statut.keys())
        values = list(repartition_statut.values())
        colors = [config.STATUTS_OPERATIONS.get(label, {}).get('couleur', '#666666') 
                 for label in labels]
        
        fig.add_trace(go.Pie(
            labels=[config.STATUTS_OPERATIONS.get(label, {}).get('libelle', label) 
                   for label in labels],
            values=values,
            marker=dict(colors=colors),
            name="Statuts"
        ), row=1, col=2)
    
    # 3. Bar chart répartition types
    repartition_type = metrics_data.get('repartition_type', {})
    if repartition_type:
        fig.add_trace(go.Bar(
            x=list(repartition_type.keys()),
            y=list(repartition_type.values()),
            marker_color=config.COULEURS_TIMELINE[:len(repartition_type)],
            name="Types"
        ), row=2, col=1)
    
    # 4. Alertes par niveau
    alertes_niveau = metrics_data.get('alertes_par_niveau', {})
    if alertes_niveau:
        colors_alertes = [config.TYPES_ALERTES.get(niveau, {}).get('couleur', '#666666')
                         for niveau in alertes_niveau.keys()]
        
        fig.add_trace(go.Bar(
            x=list(alertes_niveau.keys()),
            y=list(alertes_niveau.values()),
            marker_color=colors_alertes,
            name="Alertes"
        ), row=2, col=2)
    
    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="Dashboard Métriques",
        title_x=0.5
    )
    
    return fig

def create_budget_evolution_chart(budget_data: List[Dict]) -> go.Figure:
    """Graphique évolution budgétaire"""
    
    if not budget_data:
        return go.Figure().add_annotation(
            text="Aucune donnée budgétaire",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
    
    df = pd.DataFrame(budget_data)
    df['date_budget'] = pd.to_datetime(df['date_budget'])
    df = df.sort_values('date_budget')
    
    fig = go.Figure()
    
    # Ligne par type de budget
    for type_budget in df['type_budget'].unique():
        data_type = df[df['type_budget'] == type_budget]
        
        fig.add_trace(go.Scatter(
            x=data_type['date_budget'],
            y=data_type['montant'],
            mode='lines+markers',
            name=type_budget,
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Date: %{x}<br>' +
                         'Montant: €%{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title="Évolution Budgétaire",
        xaxis_title="Date",
        yaxis_title="Montant (€)",
        hovermode='closest',
        height=400
    )
    
    return fig

def create_gantt_chart(phases_data: List[Dict]) -> go.Figure:
    """Créer un diagramme de Gantt des phases"""
    
    if not phases_data:
        return go.Figure().add_annotation(
            text="Aucune phase disponible",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
    
    df = pd.DataFrame(phases_data)
    df = df.sort_values('ordre')
    
    # Préparer les dates
    df['Start'] = pd.to_datetime(df['date_debut_prevue'], errors='coerce')
    df['Finish'] = pd.to_datetime(df['date_fin_prevue'], errors='coerce')
    df['Start_Real'] = pd.to_datetime(df['date_debut_reelle'], errors='coerce')
    df['Finish_Real'] = pd.to_datetime(df['date_fin_reelle'], errors='coerce')
    
    fig = go.Figure()
    
                # Barres prévues
    for idx, phase in df.iterrows():
        if pd.notna(phase['Start']) and pd.notna(phase['Finish']):
            fig.add_trace(go.Bar(
                x=[phase['Finish'] - phase['Start']],
                y=[phase['nom_phase']],
                orientation='h',
                base=phase['Start'],
                marker=dict(
                    color=config.STATUTS_PHASES.get(phase['statut_phase'], {}).get('couleur', '#E0E0E0'),
                    opacity=0.6
                ),
                name=f"Prévu - {phase['nom_phase']}",
                showlegend=False,
                hovertemplate=f"""
                <b>{phase['nom_phase']}</b><br>
                Début prévu: {phase['Start'].strftime('%d/%m/%Y') if pd.notna(phase['Start']) else 'N/A'}<br>
                Fin prévue: {phase['Finish'].strftime('%d/%m/%Y') if pd.notna(phase['Finish']) else 'N/A'}<br>
                Statut: {config.STATUTS_PHASES.get(phase['statut_phase'], {}).get('libelle', phase['statut_phase'])}<br>
                Progression: {phase.get('progression_pct', 0)}%<br>
                <extra></extra>
                """
            ))
        
        # Barres réelles (si disponibles)
        if pd.notna(phase['Start_Real']) and pd.notna(phase['Finish_Real']):
            fig.add_trace(go.Bar(
                x=[phase['Finish_Real'] - phase['Start_Real']],
                y=[phase['nom_phase']],
                orientation='h',
                base=phase['Start_Real'],
                marker=dict(
                    color=config.STATUTS_PHASES.get(phase['statut_phase'], {}).get('couleur', '#E0E0E0'),
                    opacity=1.0,
                    line=dict(width=2, color='black')
                ),
                name=f"Réel - {phase['nom_phase']}",
                showlegend=False,
                hovertemplate=f"""
                <b>{phase['nom_phase']} - RÉEL</b><br>
                Début réel: {phase['Start_Real'].strftime('%d/%m/%Y') if pd.notna(phase['Start_Real']) else 'N/A'}<br>
                Fin réelle: {phase['Finish_Real'].strftime('%d/%m/%Y') if pd.notna(phase['Finish_Real']) else 'N/A'}<br>
                Durée réelle: {phase.get('duree_reelle', 'N/A')} jours<br>
                <extra></extra>
                """
            ))
    
    # Ligne date actuelle
    fig.add_vline(
        x=datetime.now(),
        line_dash="dash",
        line_color="red",
        annotation_text="Aujourd'hui"
    )
    
    fig.update_layout(
        title="Diagramme de Gantt - Phases",
        xaxis_title="Période",
        yaxis_title="Phases",
        height=max(400, len(df) * 40),
        showlegend=False,
        barmode='overlay'
    )
    
    return fig

# ============================================================================
# FORMATAGE DATES ET DURÉES
# ============================================================================

def format_date_french(date_obj: Any) -> str:
    """Formater une date en français"""
    if pd.isna(date_obj) or date_obj is None:
        return "Non définie"
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except:
            return date_obj
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    months_fr = {
        1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
        5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
        9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
    }
    
    return f"{date_obj.day} {months_fr[date_obj.month]} {date_obj.year}"

def format_duration_smart(days: int) -> str:
    """Formater une durée intelligemment"""
    if pd.isna(days) or days == 0:
        return "Non définie"
    
    if days < 0:
        return f"En avance de {abs(days)} jour{'s' if abs(days) > 1 else ''}"
    
    if days < 7:
        return f"{days} jour{'s' if days > 1 else ''}"
    elif days < 30:
        weeks = days // 7
        remaining_days = days % 7
        result = f"{weeks} semaine{'s' if weeks > 1 else ''}"
        if remaining_days > 0:
            result += f" et {remaining_days} jour{'s' if remaining_days > 1 else ''}"
        return result
    elif days < 365:
        months = days // 30
        remaining_days = days % 30
        result = f"{months} mois"
        if remaining_days > 0:
            result += f" et {remaining_days} jour{'s' if remaining_days > 1 else ''}"
        return result
    else:
        years = days // 365
        remaining_days = days % 365
        result = f"{years} an{'s' if years > 1 else ''}"
        if remaining_days > 0:
            result += f" et {remaining_days} jour{'s' if remaining_days > 1 else ''}"
        return result

def calculate_working_days(start_date: date, end_date: date) -> int:
    """Calculer le nombre de jours ouvrés entre deux dates"""
    if start_date >= end_date:
        return 0
    
    # Calcul simple : exclure weekends
    total_days = (end_date - start_date).days
    weeks = total_days // 7
    remaining_days = total_days % 7
    
    # Compter jours ouvrés dans la semaine restante
    working_days_remainder = 0
    current_date = start_date + timedelta(days=weeks * 7)
    
    for i in range(remaining_days):
        if current_date.weekday() < 5:  # Lundi=0, Vendredi=4
            working_days_remainder += 1
        current_date += timedelta(days=1)
    
    return weeks * 5 + working_days_remainder

# ============================================================================
# HELPERS INTERFACE STREAMLIT
# ============================================================================

def show_loading_spinner(message: str = None):
    """Afficher un spinner de chargement"""
    message = message or UI_MESSAGES['loading']
    return st.spinner(message)

def show_success_message(message: str, auto_dismiss: bool = True):
    """Afficher un message de succès"""
    st.success(f"✅ {message}")
    if auto_dismiss:
        time.sleep(2)

def show_error_message(message: str, details: str = None):
    """Afficher un message d'erreur avec détails optionnels"""
    st.error(f"❌ {message}")
    if details:
        with st.expander("Détails de l'erreur"):
            st.code(details)

def create_metric_card(title: str, value: Any, delta: Any = None, 
                      help_text: str = None, color: str = None) -> None:
    """Créer une carte métrique stylisée"""
    
    # Déterminer couleur selon valeur
    if color is None:
        if isinstance(value, (int, float)):
            if value > 75:
                color = "red"
            elif value > 50:
                color = "orange" 
            else:
                color = "green"
        else:
            color = "blue"
    
    # Formater delta
    if delta is not None:
        if isinstance(delta, (int, float)):
            delta_formatted = f"{delta:+.1f}" if delta != 0 else "0"
        else:
            delta_formatted = str(delta)
    else:
        delta_formatted = None
    
    st.metric(
        label=title,
        value=value,
        delta=delta_formatted,
        help=help_text
    )

def create_progress_indicator(current: int, total: int, 
                            label: str = "Progression") -> None:
    """Créer un indicateur de progression"""
    if total == 0:
        percentage = 0
    else:
        percentage = min(100, (current / total) * 100)
    
    st.progress(percentage / 100, text=f"{label}: {current}/{total} ({percentage:.1f}%)")

def create_status_indicator(status: str, size: str = "normal") -> None:
    """Créer un indicateur de statut coloré"""
    status_config = config.STATUTS_OPERATIONS.get(status, {
        'icone': '❓', 
        'libelle': status, 
        'couleur': '#666666'
    })
    
    icon_size = "2em" if size == "large" else "1.2em"
    
    st.markdown(f"""
    <div style="
        display: flex; 
        align-items: center; 
        gap: 8px;
        padding: 8px;
        border-radius: 8px;
        background-color: {status_config.get('couleur_bg', '#f0f0f0')};
        border: 1px solid {status_config['couleur']};
    ">
        <span style="font-size: {icon_size};">{status_config['icone']}</span>
        <span style="
            color: {status_config['couleur']};
            font-weight: 600;
        ">{status_config['libelle']}</span>
    </div>
    """, unsafe_allow_html=True)

def format_number_french(number: float, decimals: int = 0) -> str:
    """Formater un nombre selon les conventions françaises"""
    if pd.isna(number):
        return "N/A"
    
    if decimals == 0:
        return f"{number:,.0f}".replace(',', ' ')
    else:
        return f"{number:,.{decimals}f}".replace(',', ' ').replace('.', ',')

def create_download_button(data: Any, filename: str, 
                          mime_type: str = "text/csv") -> None:
    """Créer un bouton de téléchargement stylisé"""
    
    if isinstance(data, pd.DataFrame):
        if mime_type == "text/csv":
            data_bytes = data.to_csv(index=False).encode('utf-8')
        else:
            data_bytes = data.to_excel(index=False).encode('utf-8') 
    else:
        data_bytes = str(data).encode('utf-8')
    
    st.download_button(
        label=f"📥 Télécharger {filename}",
        data=data_bytes,
        file_name=filename,
        mime=mime_type,
        type="secondary"
    )

# ============================================================================
# CACHE ET PERFORMANCE
# ============================================================================

def clear_cache_by_pattern(pattern: str = None):
    """Nettoyer le cache selon un pattern"""
    if pattern:
        # Cache spécifique
        st.cache_data.clear()
    else:
        # Tout le cache
        st.cache_data.clear()

def get_cache_stats() -> Dict:
    """Obtenir les statistiques du cache"""
    # Placeholder pour stats cache Streamlit
    return {
        'cache_enabled': True,
        'entries_count': 'N/A',
        'memory_usage': 'N/A'
    }

# ============================================================================
# UTILITAIRES DIVERS
# ============================================================================

def generate_operation_code(type_operation: str, sequence: int) -> str:
    """Générer un code d'opération automatique"""
    year = datetime.now().year
    return f"{type_operation}-{year}-{sequence:04d}"

def calculate_score_color(score: int) -> str:
    """Retourner la couleur selon le score"""
    if score >= 75:
        return "#F44336"  # Rouge
    elif score >= 50:
        return "#FF9800"  # Orange  
    elif score >= 25:
        return "#FFEB3B"  # Jaune
    else:
        return "#4CAF50"  # Vert

def truncate_text(text: str, max_length: int = 50) -> str:
    """Tronquer un texte avec ellipse"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Récupération sécurisée dans un dictionnaire"""
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default

def validate_date_range(start_date: date, end_date: date) -> bool:
    """Valider une plage de dates"""
    return start_date <= end_date

def get_next_business_day(input_date: date) -> date:
    """Obtenir le prochain jour ouvré"""
    next_day = input_date + timedelta(days=1)
    
    # Si samedi (5) ou dimanche (6), aller au lundi
    while next_day.weekday() > 4:
        next_day += timedelta(days=1)
    
    return next_day

# Fonction de debug pour développement
def debug_print(message: str, data: Any = None):
    """Affichage debug en développement"""
    if st.session_state.get('debug_mode', False):
        st.write(f"🐛 DEBUG: {message}")
        if data is not None:
            st.json(data)

# Export de toutes les fonctions principales
__all__ = [
    'generate_timeline',
    'calculate_global_progress', 
    'calculate_phase_efficiency',
    'create_dashboard_metrics',
    'create_budget_evolution_chart',
    'create_gantt_chart',
    'format_date_french',
    'format_duration_smart',
    'calculate_working_days',
    'show_loading_spinner',
    'show_success_message', 
    'show_error_message',
    'create_metric_card',
    'create_progress_indicator',
    'create_status_indicator',
    'format_number_french',
    'create_download_button',
    'clear_cache_by_pattern',
    'generate_operation_code',
    'calculate_score_color',
    'truncate_text',
    'safe_get',
    'validate_date_range',
    'get_next_business_day'
]
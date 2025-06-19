"""
Utilitaires pour formulaires Streamlit SPIC 2.0
Composants réutilisables, validation, messages
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import config
from .constants import UI_MESSAGES, DISPLAY_FORMATS

class FormComponents:
    """Composants de formulaires réutilisables"""
    
    @staticmethod
    def operation_form(operation_data: Dict = None, user_options: Dict = None) -> Dict:
        """Formulaire complet de création/édition d'opération"""
        
        with st.form("operation_form"):
            st.subheader("📋 Informations Opération")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input(
                    "Nom de l'opération *",
                    value=operation_data.get('nom', '') if operation_data else '',
                    help="Nom descriptif de l'opération"
                )
                
                type_operation = st.selectbox(
                    "Type d'opération *",
                    options=config.TYPES_OPERATIONS,
                    index=config.TYPES_OPERATIONS.index(operation_data.get('type_operation', 'OPP')) 
                          if operation_data and operation_data.get('type_operation') in config.TYPES_OPERATIONS 
                          else 0,
                    help="Type d'opération selon référentiel MOA"
                )
                
                domaine_activite = st.selectbox(
                    "Domaine d'activité",
                    options=[''] + config.DOMAINES_ACTIVITE,
                    index=config.DOMAINES_ACTIVITE.index(operation_data.get('domaine_activite', '')) + 1
                          if operation_data and operation_data.get('domaine_activite') in config.DOMAINES_ACTIVITE
                          else 0
                )
                
                secteur_geographique = st.text_input(
                    "Secteur géographique",
                    value=operation_data.get('secteur_geographique', '') if operation_data else '',
                    help="Champ libre pour localisation (ex: Paris 15ème, Métropole lilloise...)"
                )
            
            with col2:
                adresse = st.text_area(
                    "Adresse",
                    value=operation_data.get('adresse', '') if operation_data else '',
                    height=100
                )
                
                budget_initial = st.number_input(
                    "Budget initial (€)",
                    min_value=0.0,
                    value=float(operation_data.get('budget_initial', 0)) if operation_data else 0.0,
                    step=1000.0,
                    format="%.0f"
                )
                
                if user_options:
                    responsable_id = st.selectbox(
                        "Responsable",
                        options=[''] + list(user_options.keys()),
                        format_func=lambda x: user_options.get(x, 'Non assigné') if x else 'Non assigné',
                        index=list(user_options.keys()).index(operation_data.get('responsable_id', '')) + 1
                              if operation_data and operation_data.get('responsable_id') in user_options
                              else 0
                    )
                else:
                    responsable_id = None
            
            st.subheader("📅 Planning")
            col3, col4 = st.columns(2)
            
            with col3:
                date_debut = st.date_input(
                    "Date de début",
                    value=datetime.strptime(operation_data.get('date_debut', str(date.today())), '%Y-%m-%d').date()
                          if operation_data and operation_data.get('date_debut') 
                          else date.today()
                )
            
            with col4:
                date_fin_prevue = st.date_input(
                    "Date de fin prévue",
                    value=datetime.strptime(operation_data.get('date_fin_prevue', str(date.today() + timedelta(days=365))), '%Y-%m-%d').date()
                          if operation_data and operation_data.get('date_fin_prevue')
                          else date.today() + timedelta(days=365),
                    min_value=date_debut
                )
            
            st.subheader("📊 Détails Techniques")
            col5, col6 = st.columns(2)
            
            with col5:
                surface_m2 = st.number_input(
                    "Surface (m²)",
                    min_value=0.0,
                    value=float(operation_data.get('surface_m2', 0)) if operation_data else 0.0,
                    step=1.0
                )
            
            with col6:
                nb_logements = st.number_input(
                    "Nombre de logements",
                    min_value=0,
                    value=int(operation_data.get('nb_logements', 0)) if operation_data else 0,
                    step=1
                )
            
            description = st.text_area(
                "Description",
                value=operation_data.get('description', '') if operation_data else '',
                help="Description détaillée de l'opération"
            )
            
            submitted = st.form_submit_button("💾 Enregistrer", type="primary")
            
            if submitted:
                # Validation
                errors = FormComponents.validate_operation_form(
                    nom, type_operation, date_debut, date_fin_prevue
                )
                
                if errors:
                    for error in errors:
                        st.error(error)
                    return None
                
                return {
                    'nom': nom,
                    'type_operation': type_operation,
                    'domaine_activite': domaine_activite if domaine_activite else None,
                    'secteur_geographique': secteur_geographique,
                    'adresse': adresse,
                    'budget_initial': budget_initial if budget_initial > 0 else None,
                    'responsable_id': responsable_id if responsable_id else None,
                    'date_debut': str(date_debut),
                    'date_fin_prevue': str(date_fin_prevue),
                    'surface_m2': surface_m2 if surface_m2 > 0 else None,
                    'nb_logements': nb_logements if nb_logements > 0 else None,
                    'description': description
                }
        
        return None
    
    @staticmethod
    def validate_operation_form(nom: str, type_operation: str, 
                               date_debut: date, date_fin_prevue: date) -> List[str]:
        """Valider le formulaire d'opération"""
        errors = []
        
        if not nom or len(nom.strip()) < 3:
            errors.append("Le nom de l'opération doit contenir au moins 3 caractères")
        
        if not type_operation:
            errors.append("Le type d'opération est obligatoire")
        
        if date_fin_prevue <= date_debut:
            errors.append("La date de fin doit être postérieure à la date de début")
        
        return errors
    
    @staticmethod
    def phase_status_form(phase_data: Dict) -> Optional[Dict]:
        """Formulaire de mise à jour du statut d'une phase"""
        
        with st.form(f"phase_status_{phase_data.get('id', '')}"):
            st.write(f"**{phase_data.get('nom_phase', 'Phase')}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nouveau_statut = st.selectbox(
                    "Nouveau statut",
                    options=list(config.STATUTS_PHASES.keys()),
                    index=list(config.STATUTS_PHASES.keys()).index(phase_data.get('statut_phase', 'NON_COMMENCE')),
                    format_func=lambda x: f"{config.STATUTS_PHASES[x]['icone']} {config.STATUTS_PHASES[x]['libelle']}"
                )
                
                progression = st.slider(
                    "Progression (%)",
                    min_value=0,
                    max_value=100,
                    value=int(phase_data.get('progression_pct', 0)),
                    step=5
                )
            
            with col2:
                date_debut_reelle = st.date_input(
                    "Date début réelle",
                    value=datetime.strptime(phase_data.get('date_debut_reelle', str(date.today())), '%Y-%m-%d').date()
                          if phase_data.get('date_debut_reelle')
                          else None
                )
                
                date_fin_reelle = st.date_input(
                    "Date fin réelle",
                    value=datetime.strptime(phase_data.get('date_fin_reelle', str(date.today())), '%Y-%m-%d').date()
                          if phase_data.get('date_fin_reelle')
                          else None
                ) if nouveau_statut == 'TERMINE' else None
            
            commentaire = st.text_area(
                "Commentaire",
                value=phase_data.get('commentaire', ''),
                help="Observations sur l'avancement de cette phase"
            )
            
            submitted = st.form_submit_button("✅ Mettre à jour")
            
            if submitted:
                return {
                    'statut_phase': nouveau_statut,
                    'progression_pct': progression,
                    'date_debut_reelle': str(date_debut_reelle) if date_debut_reelle else None,
                    'date_fin_reelle': str(date_fin_reelle) if date_fin_reelle else None,
                    'commentaire': commentaire
                }
        
        return None
    
    @staticmethod
    def budget_form(operation_id: str, budget_data: Dict = None) -> Optional[Dict]:
        """Formulaire de saisie budget"""
        
        with st.form("budget_form"):
            st.subheader("💰 Saisie Budget")
            
            col1, col2 = st.columns(2)
            
            with col1:
                type_budget = st.selectbox(
                    "Type de budget",
                    options=['INITIAL', 'REVISE', 'FINAL'],
                    index=['INITIAL', 'REVISE', 'FINAL'].index(budget_data.get('type_budget', 'INITIAL'))
                          if budget_data else 0,
                    format_func=lambda x: {
                        'INITIAL': '🏁 Budget initial',
                        'REVISE': '📝 Budget révisé', 
                        'FINAL': '✅ Budget final'
                    }[x]
                )
                
                montant = st.number_input(
                    "Montant (€)",
                    min_value=0.0,
                    value=float(budget_data.get('montant', 0)) if budget_data else 0.0,
                    step=1000.0,
                    format="%.0f"
                )
            
            with col2:
                date_budget = st.date_input(
                    "Date du budget",
                    value=datetime.strptime(budget_data.get('date_budget', str(date.today())), '%Y-%m-%d').date()
                          if budget_data and budget_data.get('date_budget')
                          else date.today()
                )
            
            justification = st.text_area(
                "Justification",
                value=budget_data.get('justification', '') if budget_data else '',
                help="Motif de révision ou détails sur ce budget"
            )
            
            submitted = st.form_submit_button("💾 Enregistrer Budget")
            
            if submitted:
                if montant <= 0:
                    st.error("Le montant doit être supérieur à 0")
                    return None
                
                return {
                    'type_budget': type_budget,
                    'montant': montant,
                    'date_budget': str(date_budget),
                    'justification': justification
                }
        
        return None
    
    @staticmethod
    def rem_form(operation_id: str) -> Optional[Dict]:
        """Formulaire de saisie REM"""
        
        with st.form("rem_form"):
            st.subheader("📈 Saisie REM")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                periode = st.selectbox(
                    "Période",
                    options=['TRIMESTRE', 'SEMESTRE'],
                    format_func=lambda x: 'Trimestrielle' if x == 'TRIMESTRE' else 'Semestrielle'
                )
                
                annee = st.number_input(
                    "Année",
                    min_value=2020,
                    max_value=2030,
                    value=datetime.now().year,
                    step=1
                )
            
            with col2:
                if periode == 'TRIMESTRE':
                    trimestre = st.selectbox(
                        "Trimestre",
                        options=[1, 2, 3, 4],
                        format_func=lambda x: f"T{x}"
                    )
                    semestre = None
                else:
                    semestre = st.selectbox(
                        "Semestre", 
                        options=[1, 2],
                        format_func=lambda x: f"S{x}"
                    )
                    trimestre = None
                
                montant_rem = st.number_input(
                    "Montant REM (€)",
                    min_value=0.0,
                    step=1000.0,
                    format="%.0f"
                )
            
            with col3:
                type_rem = st.selectbox(
                    "Type de REM",
                    options=config.REM_CONFIG['types_rem']
                )
            
            commentaire = st.text_area(
                "Commentaire",
                help="Détails sur cette REM"
            )
            
            submitted = st.form_submit_button("📊 Enregistrer REM")
            
            if submitted:
                if montant_rem <= 0:
                    st.error("Le montant REM doit être supérieur à 0")
                    return None
                
                return {
                    'periode': periode,
                    'annee': annee,
                    'trimestre': trimestre,
                    'semestre': semestre,
                    'montant_rem': montant_rem,
                    'type_rem': type_rem,
                    'commentaire': commentaire
                }
        
        return None
    
    @staticmethod
    def filters_sidebar(operations_df) -> Dict:
        """Barre latérale de filtres"""
        st.sidebar.header("🔍 Filtres")
        
        filters = {}
        
        # Filtre type d'opération
        if not operations_df.empty and 'type_operation' in operations_df.columns:
            types_disponibles = operations_df['type_operation'].unique().tolist()
            filters['type_operation'] = st.sidebar.multiselect(
                "Type d'opération",
                options=types_disponibles,
                default=types_disponibles
            )
        
                # Filtre statut
        if not operations_df.empty and 'statut_global' in operations_df.columns:
            statuts_disponibles = operations_df['statut_global'].unique().tolist()
            filters['statut_global'] = st.sidebar.multiselect(
                "Statut global",
                options=statuts_disponibles,
                default=statuts_disponibles,
                format_func=lambda x: f"{config.STATUTS_OPERATIONS.get(x, {}).get('icone', '')} {config.STATUTS_OPERATIONS.get(x, {}).get('libelle', x)}"
            )
        
        # Filtre score de risque
        filters['score_risque_min'] = st.sidebar.slider(
            "Score de risque minimum",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            help="Afficher seulement les opérations avec un score ≥ à cette valeur"
        )
        
        # Filtre budget
        if not operations_df.empty and 'budget_initial' in operations_df.columns:
            budget_max = operations_df['budget_initial'].max()
            if budget_max > 0:
                budget_range = st.sidebar.slider(
                    "Fourchette budget (€)",
                    min_value=0.0,
                    max_value=float(budget_max),
                    value=(0.0, float(budget_max)),
                    step=10000.0,
                    format="€%.0f"
                )
                filters['budget_min'] = budget_range[0]
                filters['budget_max'] = budget_range[1]
        
        # Filtre responsable
        if not operations_df.empty and 'responsable_id' in operations_df.columns:
            responsables = operations_df['responsable_id'].dropna().unique().tolist()
            if responsables:
                filters['responsable_id'] = st.sidebar.multiselect(
                    "Responsable",
                    options=responsables,
                    default=responsables
                )
        
        # Filtre par domaine
        if not operations_df.empty and 'domaine_activite' in operations_df.columns:
            domaines = operations_df['domaine_activite'].dropna().unique().tolist()
            if domaines:
                filters['domaine_activite'] = st.sidebar.multiselect(
                    "Domaine d'activité",
                    options=domaines,
                    default=domaines
                )
        
        # Bouton reset filtres
        if st.sidebar.button("🔄 Réinitialiser les filtres"):
            st.experimental_rerun()
        
        return filters
    
    @staticmethod
    def search_bar(placeholder: str = "Rechercher une opération...") -> str:
        """Barre de recherche"""
        return st.text_input(
            "🔍 Recherche",
            placeholder=placeholder,
            help="Recherche dans le nom, adresse, secteur géographique"
        )
    
    @staticmethod
    def status_badge(statut: str, size: str = "normal") -> str:
        """Générer un badge HTML pour un statut"""
        config_statut = config.STATUTS_OPERATIONS.get(statut, {})
        couleur = config_statut.get('couleur', '#666666')
        couleur_bg = config_statut.get('couleur_bg', '#f0f0f0')
        icone = config_statut.get('icone', '⭕')
        libelle = config_statut.get('libelle', statut)
        
        font_size = "0.8em" if size == "small" else "0.9em"
        padding = "2px 6px" if size == "small" else "4px 8px"
        
        return f"""
        <span style="
            background-color: {couleur_bg};
            color: {couleur};
            border: 1px solid {couleur};
            border-radius: 12px;
            padding: {padding};
            font-size: {font_size};
            font-weight: 500;
            display: inline-block;
            margin: 2px;
        ">
            {icone} {libelle}
        </span>
        """
    
    @staticmethod
    def risk_score_badge(score: int) -> str:
        """Badge pour score de risque"""
        niveau = 'FAIBLE'
        for niv, config_niv in config.NIVEAUX_RISQUE.items():
            if config_niv['score_min'] <= score <= config_niv['score_max']:
                niveau = niv
                break
        
        config_niveau = config.NIVEAUX_RISQUE[niveau]
        couleur = config_niveau['couleur']
        couleur_bg = config_niveau['couleur_bg']
        icone = config_niveau['icone']
        
        return f"""
        <span style="
            background-color: {couleur_bg};
            color: {couleur};
            border: 1px solid {couleur};
            border-radius: 12px;
            padding: 4px 8px;
            font-size: 0.9em;
            font-weight: 600;
            display: inline-block;
        ">
            {icone} {score}/100
        </span>
        """
    
    @staticmethod
    def progress_bar(progression: int, hauteur: int = 20) -> str:
        """Barre de progression HTML"""
        couleur = '#4CAF50' if progression >= 80 else '#FF9800' if progression >= 50 else '#F44336'
        
        return f"""
        <div style="
            width: 100%;
            background-color: #e0e0e0;
            border-radius: {hauteur//2}px;
            height: {hauteur}px;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                width: {progression}%;
                background-color: {couleur};
                height: 100%;
                border-radius: {hauteur//2}px;
                transition: width 0.3s ease;
            "></div>
            <span style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: {hauteur-6}px;
                font-weight: 600;
                color: white;
                text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
            ">
                {progression}%
            </span>
        </div>
        """
    
    @staticmethod
    def alert_message(message: str, type_alert: str = "info", 
                     dismissible: bool = False) -> None:
        """Afficher un message d'alerte stylisé"""
        
        alert_configs = {
            'success': {'color': '#4CAF50', 'bg': '#E8F5E8', 'icon': '✅'},
            'error': {'color': '#F44336', 'bg': '#FFEBEE', 'icon': '❌'}, 
            'warning': {'color': '#FF9800', 'bg': '#FFF3E0', 'icon': '⚠️'},
            'info': {'color': '#2196F3', 'bg': '#E3F2FD', 'icon': 'ℹ️'}
        }
        
        config_alert = alert_configs.get(type_alert, alert_configs['info'])
        
        if type_alert == 'success':
            st.success(f"{config_alert['icon']} {message}")
        elif type_alert == 'error':
            st.error(f"{config_alert['icon']} {message}")
        elif type_alert == 'warning':
            st.warning(f"{config_alert['icon']} {message}")
        else:
            st.info(f"{config_alert['icon']} {message}")
    
    @staticmethod
    def confirmation_dialog(message: str, key: str) -> bool:
        """Dialog de confirmation"""
        if f"confirm_{key}" not in st.session_state:
            st.session_state[f"confirm_{key}"] = False
        
        if not st.session_state[f"confirm_{key}"]:
            st.warning(f"⚠️ {message}")
            col1, col2, col3 = st.columns([1, 1, 3])
            
            with col1:
                if st.button("✅ Confirmer", key=f"yes_{key}"):
                    st.session_state[f"confirm_{key}"] = True
                    st.experimental_rerun()
            
            with col2:
                if st.button("❌ Annuler", key=f"no_{key}"):
                    return False
            
            return False
        else:
            # Reset après confirmation
            st.session_state[f"confirm_{key}"] = False
            return True
    
    @staticmethod
    def data_editor_enhanced(df, key: str, disabled_columns: List[str] = None) -> Any:
        """Éditeur de données amélioré avec validation"""
        
        if df.empty:
            st.info("Aucune donnée à afficher")
            return df
        
        # Configuration colonnes
        column_config = {}
        disabled_columns = disabled_columns or []
        
        for col in df.columns:
            if col in disabled_columns:
                column_config[col] = st.column_config.Column(disabled=True)
            elif 'date' in col.lower():
                column_config[col] = st.column_config.DateColumn(format="DD/MM/YYYY")
            elif 'budget' in col.lower() or 'montant' in col.lower():
                column_config[col] = st.column_config.NumberColumn(format="€%.0f")
            elif 'pct' in col.lower() or 'pourcentage' in col.lower():
                column_config[col] = st.column_config.NumberColumn(format="%.1f%%")
        
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            key=key
        )
        
        return edited_df

# Fonctions utilitaires pour les formulaires
def validate_email(email: str) -> bool:
    """Valider format email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Valider format téléphone français"""
    import re
    # Format français 10 chiffres
    pattern = r'^(?:(?:\+33|0)\d{9})$'
    return re.match(pattern, phone.replace(' ', '').replace('.', '').replace('-', '')) is not None

def sanitize_input(text: str) -> str:
    """Nettoyer une saisie utilisateur"""
    if not text:
        return ""
    
    # Supprimer caractères dangereux
    import re
    text = re.sub(r'[<>"\']', '', text)
    text = text.strip()
    
    return text

def format_file_size(size_bytes: int) -> str:
    """Formater taille de fichier"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"
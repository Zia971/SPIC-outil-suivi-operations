"""
Application Streamlit SPIC 2.0 - VERSION REFACTORISÉE
Point d'entrée minimal avec dispatch vers modules spécialisés
Gestion session, navigation, authentification
"""

import streamlit as st
import logging
from datetime import datetime
import sys
import os

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules SPIC
try:
    import config
    import database
    from utils.constants import UI_MESSAGES
    from utils.form_utils import FormComponents
    
    # Import modules métier
    from modules.suivi_operations import show_suivi_operations
    from modules.gestion_journal import show_gestion_journal  
    from modules.suivi_financier import show_suivi_financier
    from modules.gestion_risques import show_gestion_risques
    from modules.exports import show_exports
    
except ImportError as e:
    st.error(f"Erreur d'import des modules SPIC: {e}")
    st.stop()

# ============================================================================
# CONFIGURATION STREAMLIT
# ============================================================================

def configure_streamlit():
    """Configuration globale de Streamlit"""
    
    st.set_page_config(
        page_title=config.LAYOUT_CONFIG["page_title"],
        page_icon=config.LAYOUT_CONFIG["page_icon"], 
        layout=config.LAYOUT_CONFIG["layout"],
        initial_sidebar_state=config.LAYOUT_CONFIG["initial_sidebar_state"],
        menu_items=config.LAYOUT_CONFIG.get("menu_items", {})
    )
    
    # CSS personnalisé (sera chargé depuis assets/css/style.css en production)
    st.markdown("""
    <style>
        .main > div {
            padding-top: 2rem;
        }
        .stSidebar > div {
            padding-top: 2rem;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# GESTION SESSION UTILISATEUR
# ============================================================================

def init_session_state():
    """Initialiser les variables de session"""
    
    # Variables session
    session_vars = {
        'authenticated': False,
        'user_id': None,
        'user_data': None,
        'current_module': 'suivi_operations',
        'db_manager': None,
        'notifications': [],
        'redirect_to': None,
        'selected_operation': None,
        'debug_mode': False
    }
    
    for var, default_value in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

def show_login_form():
    """Formulaire de connexion"""
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🏗️ SPIC 2.0</h1>
        <h3>Suivi Professionnel d'Opérations de Construction</h3>
        <p>Outil de pilotage MOA intelligent et collaboratif</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.subheader("🔐 Connexion")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            email = st.text_input(
                "Email",
                placeholder="exemple@moa.fr",
                help="Utilisez un email de démonstration"
            )
            
            password = st.text_input(
                "Mot de passe", 
                type="password",
                placeholder="Votre mot de passe",
                help="Utilisez un mot de passe de démonstration"
            )
            
            submitted = st.form_submit_button("🚀 Se connecter", type="primary", use_container_width=True)
        
        # Comptes de démonstration
        with st.expander("👤 Comptes de Démonstration"):
            demo_accounts = [
                {"email": "sophie.martin@moa.fr", "password": "admin123", "role": "ADMIN"},
                {"email": "pierre.dubois@moa.fr", "password": "manager123", "role": "MANAGER"},
                {"email": "marie.bernard@moa.fr", "password": "charge123", "role": "CHARGE_OPERATION"}
            ]
            
            for account in demo_accounts:
                st.write(f"**{account['role']}** - {account['email']} / {account['password']}")
    
    if submitted and email and password:
        try:
            # Vérifier authentification
            db_manager = get_database_manager()
            user = db_manager.verify_user_password(email, password)
            
            if user:
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = user['id']
                st.session_state['user_data'] = user
                st.session_state['db_manager'] = db_manager
                
                FormComponents.alert_message(
                    f"Connexion réussie ! Bienvenue {user['prenom']} {user['nom']}",
                    "success"
                )
                
                st.experimental_rerun()
            else:
                FormComponents.alert_message(
                    "Email ou mot de passe incorrect",
                    "error"
                )
        
        except Exception as e:
            logger.error(f"Erreur authentification: {e}")
            FormComponents.alert_message(f"Erreur de connexion: {e}", "error")

def show_logout():
    """Déconnexion utilisateur"""
    
    if st.sidebar.button("🚪 Déconnexion"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

# ============================================================================
# NAVIGATION ET MENU
# ============================================================================

def show_sidebar_menu():
    """Menu de navigation principal"""
    
    user_data = st.session_state.get('user_data', {})
    
    # En-tête utilisateur
    st.sidebar.markdown(f"""
    <div style="padding: 1rem; background-color: #f0f0f0; border-radius: 0.5rem; margin-bottom: 1rem;">
        <strong>👤 {user_data.get('prenom', '')} {user_data.get('nom', '')}</strong><br>
        <small>{config.ROLES_UTILISATEURS.get(user_data.get('role', ''), {}).get('libelle', '')}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu principal
    st.sidebar.markdown("### 🧭 Navigation")
    
    # Définition des modules selon rôles
    modules_config = {
        'suivi_operations': {
            'name': '🏗️ Suivi Opérations',
            'description': 'Portefeuille, timeline, vue manager',
            'roles': ['ADMIN', 'MANAGER', 'CHARGE_OPERATION', 'CONSULTANT']
        },
        'gestion_journal': {
            'name': '📚 Journal',
            'description': 'Historique et modifications',
            'roles': ['ADMIN', 'MANAGER', 'CHARGE_OPERATION']
        },
        'suivi_financier': {
            'name': '💰 Suivi Financier',
            'description': 'Budgets, REM, évolution',
            'roles': ['ADMIN', 'MANAGER', 'CHARGE_OPERATION']
        },
        'gestion_risques': {
            'name': '🚨 Gestion Risques',
            'description': 'Scores, alertes, TOP 3',
            'roles': ['ADMIN', 'MANAGER', 'CHARGE_OPERATION']
        },
        'exports': {
            'name': '📥 Exports',
            'description': 'Word, Excel, rapports',
            'roles': ['ADMIN', 'MANAGER', 'CHARGE_OPERATION', 'CONSULTANT']
        }
    }
    
    user_role = user_data.get('role', 'CONSULTANT')
    current_module = st.session_state.get('current_module', 'suivi_operations')
    
    # Afficher modules selon droits
    for module_id, module_config in modules_config.items():
        if user_role in module_config['roles']:
            
            # Style bouton selon sélection
            if module_id == current_module:
                button_type = "primary"
            else:
                button_type = "secondary"
            
            if st.sidebar.button(
                module_config['name'],
                key=f"nav_{module_id}",
                help=module_config['description'],
                type=button_type,
                use_container_width=True
            ):
                st.session_state['current_module'] = module_id
                st.experimental_rerun()
    
    # Section outils
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Outils")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🔄 Cache", help="Vider le cache"):
            st.cache_data.clear()
            FormComponents.alert_message("Cache vidé", "success")
    
    with col2:
        if st.button("📊 Stats", help="Statistiques BDD"):
            show_database_stats()
    
    # Debug mode (admin seulement)
    if user_role == 'ADMIN':
        st.sidebar.markdown("---")
        debug_mode = st.sidebar.checkbox(
            "🐛 Mode Debug",
            value=st.session_state.get('debug_mode', False)
        )
        st.session_state['debug_mode'] = debug_mode
    
    # Déconnexion
    st.sidebar.markdown("---")
    show_logout()

def handle_redirections():
    """Gérer les redirections entre modules"""
    
    redirect_to = st.session_state.get('redirect_to')
    
    if redirect_to:
        if redirect_to == 'timeline' and st.session_state.get('selected_operation'):
            st.session_state['current_module'] = 'suivi_operations'
            st.info("👉 Redirection vers la timeline de l'opération sélectionnée")
        
        elif redirect_to in ['exports', 'risks', 'journal']:
            st.session_state['current_module'] = redirect_to
            st.info(f"👉 Redirection vers {redirect_to}")
        
        # Reset redirection
        st.session_state['redirect_to'] = None
        st.experimental_rerun()

def show_notifications():
    """Afficher notifications globales"""
    
    notifications = st.session_state.get('notifications', [])
    
    if notifications:
        for notification in notifications:
            if notification['type'] == 'success':
                st.success(notification['message'])
            elif notification['type'] == 'error':
                st.error(notification['message'])
            elif notification['type'] == 'warning':
                st.warning(notification['message'])
            else:
                st.info(notification['message'])
        
        # Vider notifications après affichage
        st.session_state['notifications'] = []

# ============================================================================
# DISPATCH VERS MODULES
# ============================================================================

def dispatch_to_module():
    """Dispatcher vers le module sélectionné"""
    
    current_module = st.session_state.get('current_module', 'suivi_operations')
    db_manager = st.session_state['db_manager']
    user_session = {
        'user_id': st.session_state['user_id'],
        'user_data': st.session_state['user_data'],
        'role': st.session_state['user_data']['role']
    }
    
    try:
        if current_module == 'suivi_operations':
            show_suivi_operations(db_manager, user_session)
        
        elif current_module == 'gestion_journal':
            show_gestion_journal(db_manager, user_session)
        
        elif current_module == 'suivi_financier':
            show_suivi_financier(db_manager, user_session)
        
        elif current_module == 'gestion_risques':
            show_gestion_risques(db_manager, user_session)
        
        elif current_module == 'exports':
            show_exports(db_manager, user_session)
        
        else:
            st.error(f"Module '{current_module}' non reconnu")
    
    except Exception as e:
        logger.error(f"Erreur module {current_module}: {e}")
        st.error(f"Erreur lors du chargement du module: {e}")
        
        if st.session_state.get('debug_mode'):
            st.exception(e)

# ============================================================================
# UTILITAIRES
# ============================================================================

@st.cache_resource
def get_database_manager():
    """Récupérer instance DatabaseManager (cached)"""
    
    try:
        # Créer dossier data s'il n'existe pas
        os.makedirs('data', exist_ok=True)
        
        # Initialiser DatabaseManager
        db_manager = database.DatabaseManager()
        logger.info("DatabaseManager initialisé avec succès")
        
        return db_manager
    
    except Exception as e:
        logger.error(f"Erreur initialisation DatabaseManager: {e}")
        st.error(f"Erreur initialisation base de données: {e}")
        st.stop()

def show_database_stats():
    """Afficher statistiques de la base de données"""
    
    try:
        db_manager = st.session_state['db_manager']
        stats = db_manager.get_database_stats()
        
        st.sidebar.markdown("**📊 Stats BDD:**")
        for key, value in stats.items():
            if 'nb_' in key:
                table_name = key.replace('nb_', '').replace('_', ' ').title()
                st.sidebar.write(f"• {table_name}: {value}")
    
    except Exception as e:
        logger.error(f"Erreur stats BDD: {e}")
        st.sidebar.error("Erreur stats BDD")

def show_app_info():
    """Informations sur l'application"""
    
    if st.session_state.get('debug_mode'):
        with st.expander("ℹ️ Informations Application"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Version:**", config.APP_METADATA["version"])
                st.write("**Date:**", config.APP_METADATA["date_version"])
                st.write("**Python:**", f"{sys.version_info.major}.{sys.version_info.minor}")
            
            with col2:
                st.write("**Framework:**", config.APP_METADATA["framework"])
                st.write("**Base de données:**", config.APP_METADATA["base_donnees"])
                st.write("**OPCOPILOT:**", "✅" if config.APP_METADATA["compatibilite_opcopilot"] else "❌")

# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main():
    """Fonction principale de l'application"""
    
    try:
        # Configuration Streamlit
        configure_streamlit()
        
        # Initialisation session
        init_session_state()
        
        # Vérification authentification
        if not st.session_state.get('authenticated'):
            show_login_form()
            return
        
        # Interface authentifiée
        show_sidebar_menu()
        handle_redirections()
        show_notifications()
        
        # Dispatch vers module
        dispatch_to_module()
        
        # Informations debug
        show_app_info()
    
    except Exception as e:
        logger.error(f"Erreur application principale: {e}")
        st.error(f"Erreur critique de l'application: {e}")
        
        if st.button("🔄 Redémarrer l'application"):
            st.experimental_rerun()

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()
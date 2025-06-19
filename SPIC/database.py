# -*- coding: utf-8 -*-
"""
Module de gestion de la base de données SQLite pour SPIC 2.0
Gestionnaire BDD avec gestion collaborative, automatisations intelligentes
et compatibilité future OPCOPILOT
"""

import sqlite3
import json
import uuid
import hashlib
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
import logging
from contextlib import contextmanager
import config

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire de base de données SQLite pour SPIC 2.0"""
    
    def __init__(self, db_path: str = None):
        """Initialise la connexion à la base de données"""
        self.db_path = db_path or config.DB_CONFIG["db_path"]
        self.timeout = config.DB_CONFIG["timeout"]
        self.init_database()
        
    @contextmanager
    def get_connection(self):
        """Gestionnaire de contexte pour les connexions"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=self.timeout,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            # Optimisations SQLite
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erreur base de données: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_database(self):
        """Initialise la structure de la base de données"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table UTILISATEURS_SPIC (Intervenants internes MOA)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS utilisateurs_spic (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    mot_de_passe_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'MANAGER', 'CHARGE_OPERATION', 'CONSULTANT')),
                    actif BOOLEAN DEFAULT 1,
                    derniere_connexion DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table OPERATIONS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    nom TEXT NOT NULL,
                    adresse TEXT,
                    secteur_geographique TEXT,
                    type_operation TEXT NOT NULL CHECK (type_operation IN ('OPP', 'VEFA', 'AMO', 'MANDAT')),
                    domaine_activite TEXT,
                    budget_initial REAL,
                    budget_revise REAL,
                    budget_final REAL,
                    date_debut DATE,
                    date_fin_prevue DATE,
                    date_fin_reelle DATE,
                    statut_global TEXT DEFAULT 'EN_PREPARATION',
                    score_risque INTEGER DEFAULT 0,
                    responsable_id TEXT,
                    description TEXT,
                    surface_m2 REAL,
                    nb_logements INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (responsable_id) REFERENCES utilisateurs_spic(id),
                    FOREIGN KEY (created_by) REFERENCES utilisateurs_spic(id)
                )
            """)
            
            # Table PHASES_OPERATIONS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phases_operations (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    operation_id TEXT NOT NULL,
                    phase_id INTEGER NOT NULL,
                    nom_phase TEXT NOT NULL,
                    ordre INTEGER NOT NULL,
                    type_operation TEXT NOT NULL,
                    date_debut_prevue DATE,
                    date_fin_prevue DATE,
                    duree_prevue INTEGER,
                    date_debut_reelle DATE,
                    date_fin_reelle DATE,
                    duree_reelle INTEGER,
                    statut_phase TEXT DEFAULT 'NON_COMMENCE',
                    progression_pct INTEGER DEFAULT 0,
                    principale BOOLEAN DEFAULT 0,
                    commentaire TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    FOREIGN KEY (operation_id) REFERENCES operations(id) ON DELETE CASCADE,
                    FOREIGN KEY (updated_by) REFERENCES utilisateurs_spic(id)
                )
            """)
            
            # Table DROITS_OPERATIONS (Gestion collaborative)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS droits_operations (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    utilisateur_id TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    permissions TEXT NOT NULL,  -- JSON
                    date_attribution DATETIME DEFAULT CURRENT_TIMESTAMP,
                    attribue_par TEXT,
                    actif BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs_spic(id),
                    FOREIGN KEY (operation_id) REFERENCES operations(id) ON DELETE CASCADE,
                    FOREIGN KEY (attribue_par) REFERENCES utilisateurs_spic(id),
                    UNIQUE(utilisateur_id, operation_id)
                )
            """)
            
            # Table JOURNAL_MODIFICATIONS (Traçabilité)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_modifications (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    utilisateur_id TEXT NOT NULL,
                    operation_id TEXT,
                    phase_id TEXT,
                    action TEXT NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),
                    table_concernee TEXT NOT NULL,
                    champ_modifie TEXT,
                    ancienne_valeur TEXT,
                    nouvelle_valeur TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs_spic(id),
                    FOREIGN KEY (operation_id) REFERENCES operations(id),
                    FOREIGN KEY (phase_id) REFERENCES phases_operations(id)
                )
            """)
            
            # Table ALERTES
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alertes (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    operation_id TEXT NOT NULL,
                    phase_id TEXT,
                    type_alerte TEXT NOT NULL,
                    niveau_severite TEXT NOT NULL,
                    titre TEXT NOT NULL,
                    description TEXT,
                    statut TEXT DEFAULT 'ACTIVE',
                    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date_resolution DATETIME,
                    resolu_par TEXT,
                    parametres TEXT,  -- JSON
                    actif BOOLEAN DEFAULT 1,
                    FOREIGN KEY (operation_id) REFERENCES operations(id) ON DELETE CASCADE,
                    FOREIGN KEY (phase_id) REFERENCES phases_operations(id),
                    FOREIGN KEY (resolu_par) REFERENCES utilisateurs_spic(id)
                )
            """)
            
            # Table BUDGETS_GLOBAUX (Vision macro)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets_globaux (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    operation_id TEXT NOT NULL,
                    type_budget TEXT NOT NULL CHECK (type_budget IN ('INITIAL', 'REVISE', 'FINAL')),
                    montant REAL NOT NULL,
                    date_budget DATE NOT NULL,
                    justification TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (operation_id) REFERENCES operations(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES utilisateurs_spic(id)
                )
            """)
            
            # Table REM_OPERATIONS (Simple en attendant OPCOPILOT)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rem_operations (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    operation_id TEXT NOT NULL,
                    periode TEXT NOT NULL CHECK (periode IN ('TRIMESTRE', 'SEMESTRE')),
                    annee INTEGER NOT NULL,
                    trimestre INTEGER CHECK (trimestre BETWEEN 1 AND 4),
                    semestre INTEGER CHECK (semestre BETWEEN 1 AND 2),
                    montant_rem REAL NOT NULL,
                    pourcentage_budget REAL,
                    type_rem TEXT,
                    commentaire TEXT,
                    valide BOOLEAN DEFAULT 0,
                    date_saisie DATETIME DEFAULT CURRENT_TIMESTAMP,
                    saisi_par TEXT,
                    FOREIGN KEY (operation_id) REFERENCES operations(id) ON DELETE CASCADE,
                    FOREIGN KEY (saisi_par) REFERENCES utilisateurs_spic(id)
                )
            """)
            
            # Index pour optimisation
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(type_operation)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_statut ON operations(statut_global)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_phases_operation ON phases_operations(operation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_phases_statut ON phases_operations(statut_phase)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_timestamp ON journal_modifications(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alertes_active ON alertes(actif, niveau_severite)")
            
            conn.commit()
            logger.info("Base de données initialisée avec succès")
            
            # Créer données démo si tables vides
            self._create_demo_data()

    def _create_demo_data(self):
        """Créer des données de démonstration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si données existent déjà
            cursor.execute("SELECT COUNT(*) FROM utilisateurs_spic")
            if cursor.fetchone()[0] > 0:
                return
            
            # Utilisateurs démo
            users_demo = [
                {
                    'id': str(uuid.uuid4()),
                    'nom': 'MARTIN',
                    'prenom': 'Sophie',
                    'email': 'sophie.martin@moa.fr',
                    'role': 'ADMIN',
                    'mot_de_passe_hash': hashlib.sha256('admin123'.encode()).hexdigest()
                },
                {
                    'id': str(uuid.uuid4()),
                    'nom': 'DUBOIS',
                    'prenom': 'Pierre',
                    'email': 'pierre.dubois@moa.fr',
                    'role': 'MANAGER',
                    'mot_de_passe_hash': hashlib.sha256('manager123'.encode()).hexdigest()
                },
                {
                    'id': str(uuid.uuid4()),
                    'nom': 'BERNARD',
                    'prenom': 'Marie',
                    'email': 'marie.bernard@moa.fr',
                    'role': 'CHARGE_OPERATION',
                    'mot_de_passe_hash': hashlib.sha256('charge123'.encode()).hexdigest()
                }
            ]
            
            for user in users_demo:
                cursor.execute("""
                    INSERT INTO utilisateurs_spic (id, nom, prenom, email, mot_de_passe_hash, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user['id'], user['nom'], user['prenom'], user['email'], 
                     user['mot_de_passe_hash'], user['role']))
            
            # Opérations démo
            operations_demo = [
                {
                    'id': str(uuid.uuid4()),
                    'nom': 'Résidence Les Jardins',
                    'adresse': '123 Avenue de la République, 75011 Paris',
                    'secteur_geographique': 'Île-de-France Est',
                    'type_operation': 'OPP',
                    'domaine_activite': 'Logement social',
                    'budget_initial': 2500000,
                    'date_debut': '2024-01-15',
                    'date_fin_prevue': '2025-12-31',
                    'statut_global': 'EN_COURS',
                    'responsable_id': users_demo[1]['id'],
                    'surface_m2': 1200,
                    'nb_logements': 24
                },
                {
                    'id': str(uuid.uuid4()),
                    'nom': 'Acquisition T3 Belleville',
                    'adresse': '45 Rue de Belleville, 75020 Paris',
                    'secteur_geographique': 'Paris 20ème',
                    'type_operation': 'VEFA',
                    'domaine_activite': 'Logement libre',
                    'budget_initial': 450000,
                    'date_debut': '2024-03-01',
                    'date_fin_prevue': '2025-06-30',
                    'statut_global': 'EN_COURS',
                    'responsable_id': users_demo[2]['id'],
                    'surface_m2': 75,
                    'nb_logements': 1
                }
            ]
            
            for op in operations_demo:
                cursor.execute("""
                    INSERT INTO operations (id, nom, adresse, secteur_geographique, type_operation,
                                          domaine_activite, budget_initial, date_debut, date_fin_prevue,
                                          statut_global, responsable_id, surface_m2, nb_logements, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (op['id'], op['nom'], op['adresse'], op['secteur_geographique'], 
                     op['type_operation'], op['domaine_activite'], op['budget_initial'],
                     op['date_debut'], op['date_fin_prevue'], op['statut_global'],
                     op['responsable_id'], op['surface_m2'], op['nb_logements'], users_demo[0]['id']))
            
            # Phases démo pour première opération
            phases_opp = config.PHASES_PAR_TYPE['OPP'][:10]  # Première 10 phases
            for i, phase_config in enumerate(phases_opp):
                cursor.execute("""
                    INSERT INTO phases_operations (operation_id, phase_id, nom_phase, ordre, type_operation,
                                                 duree_prevue, statut_phase, progression_pct, principale)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (operations_demo[0]['id'], phase_config['id'], phase_config['nom'],
                     phase_config['ordre'], 'OPP', phase_config['duree_max'],
                     'TERMINE' if i < 3 else ('EN_COURS' if i == 3 else 'NON_COMMENCE'),
                     100 if i < 3 else (50 if i == 3 else 0),
                     phase_config['principale']))
            
            conn.commit()
            logger.info("Données de démonstration créées")

    # =============================================================================
    # CRUD OPERATIONS
    # =============================================================================
    
    def create_operation(self, operation_data: Dict, user_id: str) -> str:
        """Créer une nouvelle opération"""
        operation_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insérer opération
            cursor.execute("""
                INSERT INTO operations (id, nom, adresse, secteur_geographique, type_operation,
                                      domaine_activite, budget_initial, date_debut, date_fin_prevue,
                                      responsable_id, surface_m2, nb_logements, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (operation_id, operation_data['nom'], operation_data.get('adresse'),
                 operation_data.get('secteur_geographique'), operation_data['type_operation'],
                 operation_data.get('domaine_activite'), operation_data.get('budget_initial'),
                 operation_data.get('date_debut'), operation_data.get('date_fin_prevue'),
                 operation_data.get('responsable_id'), operation_data.get('surface_m2'),
                 operation_data.get('nb_logements'), user_id))
            
            # Créer phases automatiquement selon type
            self._create_phases_for_operation(operation_id, operation_data['type_operation'], user_id)
            
            # Journaliser
            self.log_modification(user_id, operation_id, None, 'CREATE', 'operations', 
                                'opération', None, operation_data['nom'])
            
            conn.commit()
            return operation_id

    def _create_phases_for_operation(self, operation_id: str, type_operation: str, user_id: str):
        """Créer les phases pour une opération selon son type"""
        phases = config.PHASES_PAR_TYPE.get(type_operation, [])
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for phase in phases:
                cursor.execute("""
                    INSERT INTO phases_operations (operation_id, phase_id, nom_phase, ordre, 
                                                 type_operation, duree_prevue, principale, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (operation_id, phase['id'], phase['nom'], phase['ordre'],
                     type_operation, phase['duree_max'], phase['principale'], user_id))

    def get_operation(self, operation_id: str) -> Optional[Dict]:
        """Récupérer une opération par ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM operations WHERE id = ?", (operation_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_operations(self, user_id: str = None) -> List[Dict]:
        """Récupérer toutes les opérations (avec droits utilisateur)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                # Filtrer selon droits utilisateur
                cursor.execute("""
                    SELECT DISTINCT o.* FROM operations o
                    LEFT JOIN droits_operations d ON o.id = d.operation_id
                    WHERE d.utilisateur_id = ? AND d.actif = 1
                    OR o.created_by = ?
                    ORDER BY o.created_at DESC
                """, (user_id, user_id))
            else:
                cursor.execute("SELECT * FROM operations ORDER BY created_at DESC")
            
            return [dict(row) for row in cursor.fetchall()]

    def update_operation(self, operation_id: str, updates: Dict, user_id: str) -> bool:
        """Mettre à jour une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Récupérer anciennes valeurs pour journal
            old_data = self.get_operation(operation_id)
            if not old_data:
                return False
            
            # Construire requête UPDATE dynamique
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in ['nom', 'adresse', 'secteur_geographique', 'domaine_activite',
                           'budget_initial', 'budget_revise', 'budget_final', 'date_debut',
                           'date_fin_prevue', 'date_fin_reelle', 'statut_global', 'responsable_id',
                           'surface_m2', 'nb_logements']:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(operation_id)
            
            cursor.execute(f"""
                UPDATE operations 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            # Journaliser les modifications
            for field, new_value in updates.items():
                old_value = old_data.get(field)
                if old_value != new_value:
                    self.log_modification(user_id, operation_id, None, 'UPDATE', 'operations',
                                        field, str(old_value), str(new_value))
            
            conn.commit()
            return cursor.rowcount > 0

    def delete_operation(self, operation_id: str, user_id: str) -> bool:
        """Supprimer une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Récupérer nom pour journal
            operation = self.get_operation(operation_id)
            if not operation:
                return False
            
            cursor.execute("DELETE FROM operations WHERE id = ?", (operation_id,))
            
            # Journaliser
            self.log_modification(user_id, None, None, 'DELETE', 'operations',
                                'opération', operation['nom'], None)
            
            conn.commit()
            return cursor.rowcount > 0

    # =============================================================================
    # CRUD PHASES
    # =============================================================================
    
    def get_phases_by_operation(self, operation_id: str) -> List[Dict]:
        """Récupérer les phases d'une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM phases_operations 
                WHERE operation_id = ? 
                ORDER BY ordre
            """, (operation_id,))
            return [dict(row) for row in cursor.fetchall()]

    def update_phase_status(self, phase_id: str, statut: str, progression: int, 
                           user_id: str, date_debut: str = None, date_fin: str = None) -> bool:
        """Mettre à jour le statut d'une phase"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Récupérer ancienne données
            cursor.execute("SELECT * FROM phases_operations WHERE id = ?", (phase_id,))
            old_phase = dict(cursor.fetchone())
            
            updates = {
                'statut_phase': statut,
                'progression_pct': progression,
                'updated_by': user_id
            }
            
            if date_debut:
                updates['date_debut_reelle'] = date_debut
            if date_fin:
                updates['date_fin_reelle'] = date_fin
                if old_phase.get('date_debut_reelle'):
                    # Calculer durée réelle
                    debut = datetime.strptime(date_debut or old_phase['date_debut_reelle'], '%Y-%m-%d')
                    fin = datetime.strptime(date_fin, '%Y-%m-%d')
                    updates['duree_reelle'] = (fin - debut).days
            
            # Construire requête UPDATE
            set_clauses = [f"{k} = ?" for k in updates.keys()]
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values = list(updates.values()) + [phase_id]
            
            cursor.execute(f"""
                UPDATE phases_operations 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            # Journaliser
            self.log_modification(user_id, old_phase['operation_id'], phase_id, 'UPDATE', 
                                'phases_operations', 'statut_phase', 
                                old_phase['statut_phase'], statut)
            
            # Recalculer statut opération
            self.calculate_operation_status(old_phase['operation_id'])
            
            conn.commit()
            return cursor.rowcount > 0

    def get_phase(self, phase_id: str) -> Optional[Dict]:
        """Récupérer une phase par ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM phases_operations WHERE id = ?", (phase_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # =============================================================================
    # CRUD UTILISATEURS ET DROITS
    # =============================================================================
    
    def create_user(self, user_data: Dict) -> str:
        """Créer un utilisateur"""
        user_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Hash du mot de passe
            password_hash = hashlib.sha256(user_data['mot_de_passe'].encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO utilisateurs_spic (id, nom, prenom, email, mot_de_passe_hash, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, user_data['nom'], user_data['prenom'], user_data['email'],
                 password_hash, user_data['role']))
            
            conn.commit()
            return user_id

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Récupérer utilisateur par email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM utilisateurs_spic WHERE email = ? AND actif = 1", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def verify_user_password(self, email: str, password: str) -> Optional[Dict]:
        """Vérifier mot de passe utilisateur"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['mot_de_passe_hash'] == password_hash:
            # Mettre à jour dernière connexion
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE utilisateurs_spic 
                    SET derniere_connexion = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user['id'],))
                conn.commit()
            return user
        return None

    def grant_operation_access(self, user_id: str, operation_id: str, permissions: Dict, 
                              granted_by: str) -> bool:
        """Accorder des droits sur une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO droits_operations 
                (utilisateur_id, operation_id, permissions, attribue_par)
                VALUES (?, ?, ?, ?)
            """, (user_id, operation_id, json.dumps(permissions), granted_by))
            
            conn.commit()
            return cursor.rowcount > 0

    def check_user_permission(self, user_id: str, operation_id: str, permission: str) -> bool:
        """Vérifier si utilisateur a une permission sur une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Admin a tous les droits
            cursor.execute("SELECT role FROM utilisateurs_spic WHERE id = ?", (user_id,))
            user_role = cursor.fetchone()
            if user_role and user_role['role'] == 'ADMIN':
                return True
            
            # Créateur a tous les droits
            cursor.execute("SELECT created_by FROM operations WHERE id = ?", (operation_id,))
            creator = cursor.fetchone()
            if creator and creator['created_by'] == user_id:
                return True
            
            # Vérifier droits explicites
            cursor.execute("""
                SELECT permissions FROM droits_operations 
                WHERE utilisateur_id = ? AND operation_id = ? AND actif = 1
            """, (user_id, operation_id))
            
            row = cursor.fetchone()
            if row:
                permissions = json.loads(row['permissions'])
                return permissions.get(permission, False)
            
            return False

    # =============================================================================
    # GESTION JOURNAL ET ALERTES
    # =============================================================================
    
    def log_modification(self, user_id: str, operation_id: str, phase_id: str, 
                        action: str, table: str, field: str = None, 
                        old_value: str = None, new_value: str = None):
        """Enregistrer une modification dans le journal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO journal_modifications 
                (utilisateur_id, operation_id, phase_id, action, table_concernee, 
                 champ_modifie, ancienne_valeur, nouvelle_valeur)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, operation_id, phase_id, action, table, 
                 field, old_value, new_value))
            
            conn.commit()

    def get_journal_entries(self, operation_id: str = None, limit: int = 100) -> List[Dict]:
        """Récupérer les entrées du journal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if operation_id:
                cursor.execute("""
                    SELECT j.*, u.nom, u.prenom, o.nom as operation_nom
                    FROM journal_modifications j
                    LEFT JOIN utilisateurs_spic u ON j.utilisateur_id = u.id
                    LEFT JOIN operations o ON j.operation_id = o.id
                    WHERE j.operation_id = ?
                    ORDER BY j.timestamp DESC
                    LIMIT ?
                """, (operation_id, limit))
            else:
                cursor.execute("""
                    SELECT j.*, u.nom, u.prenom, o.nom as operation_nom
                    FROM journal_modifications j
                    LEFT JOIN utilisateurs_spic u ON j.utilisateur_id = u.id
                    LEFT JOIN operations o ON j.operation_id = o.id
                    ORDER BY j.timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]

    def create_alert(self, operation_id: str, phase_id: str, type_alerte: str,
                    niveau: str, titre: str, description: str, parametres: Dict = None) -> str:
        """Créer une alerte"""
        alert_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alertes (id, operation_id, phase_id, type_alerte, niveau_severite,
                                   titre, description, parametres)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (alert_id, operation_id, phase_id, type_alerte, niveau,
                 titre, description, json.dumps(parametres) if parametres else None))
            
            conn.commit()
            return alert_id

    def get_active_alerts(self, operation_id: str = None) -> List[Dict]:
        """Récupérer les alertes actives"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if operation_id:
                cursor.execute("""
                    SELECT a.*, o.nom as operation_nom, p.nom_phase
                    FROM alertes a
                    LEFT JOIN operations o ON a.operation_id = o.id
                    LEFT JOIN phases_operations p ON a.phase_id = p.id
                    WHERE a.operation_id = ? AND a.actif = 1
                    ORDER BY a.niveau_severite DESC, a.date_creation DESC
                """, (operation_id,))
            else:
                cursor.execute("""
                    SELECT a.*, o.nom as operation_nom, p.nom_phase
                    FROM alertes a
                    LEFT JOIN operations o ON a.operation_id = o.id
                    LEFT JOIN phases_operations p ON a.phase_id = p.id
                    WHERE a.actif = 1
                    ORDER BY a.niveau_severite DESC, a.date_creation DESC
                """, ())
            
            return [dict(row) for row in cursor.fetchall()]

    def resolve_alert(self, alert_id: str, user_id: str) -> bool:
        """Résoudre une alerte"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE alertes 
                SET statut = 'RESOLVED', date_resolution = CURRENT_TIMESTAMP, 
                    resolu_par = ?, actif = 0
                WHERE id = ?
            """, (user_id, alert_id))
            
            conn.commit()
            return cursor.rowcount > 0

    # =============================================================================
    # GESTION BUDGETS ET REM
    # =============================================================================
    
    def add_budget(self, operation_id: str, type_budget: str, montant: float,
                  date_budget: str, justification: str, user_id: str) -> str:
        """Ajouter un budget"""
        budget_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO budgets_globaux (id, operation_id, type_budget, montant,
                                           date_budget, justification, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (budget_id, operation_id, type_budget, montant, 
                 date_budget, justification, user_id))
            
            # Mettre à jour l'opération
            field_map = {
                'INITIAL': 'budget_initial',
                'REVISE': 'budget_revise', 
                'FINAL': 'budget_final'
            }
            
            if type_budget in field_map:
                cursor.execute(f"""
                    UPDATE operations 
                    SET {field_map[type_budget]} = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (montant, operation_id))
            
            conn.commit()
            return budget_id

    def get_budget_evolution(self, operation_id: str) -> List[Dict]:
        """Récupérer l'évolution budgétaire"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM budgets_globaux 
                WHERE operation_id = ? 
                ORDER BY date_budget
            """, (operation_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_rem(self, operation_id: str, periode: str, annee: int, montant: float,
               trimestre: int = None, semestre: int = None, type_rem: str = None,
               commentaire: str = None, user_id: str = None) -> str:
        """Ajouter une REM"""
        rem_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculer pourcentage du budget
            cursor.execute("SELECT budget_initial FROM operations WHERE id = ?", (operation_id,))
            budget = cursor.fetchone()
            pourcentage = (montant / budget['budget_initial'] * 100) if budget and budget['budget_initial'] else 0
            
            cursor.execute("""
                INSERT INTO rem_operations (id, operation_id, periode, annee, trimestre, semestre,
                                          montant_rem, pourcentage_budget, type_rem, commentaire, saisi_par)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rem_id, operation_id, periode, annee, trimestre, semestre,
                 montant, pourcentage, type_rem, commentaire, user_id))
            
            conn.commit()
            return rem_id

    def get_rem_by_operation(self, operation_id: str) -> List[Dict]:
        """Récupérer les REM d'une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rem_operations 
                WHERE operation_id = ? 
                ORDER BY annee DESC, trimestre DESC, semestre DESC
            """, (operation_id,))
            return [dict(row) for row in cursor.fetchall()]

    # =============================================================================
    # AUTOMATISATIONS INTELLIGENTES
    # =============================================================================
    
    def calculate_operation_status(self, operation_id: str) -> str:
        """Calculer le statut automatique d'une opération selon ses phases"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Récupérer statistiques des phases
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_phases,
                    SUM(CASE WHEN statut_phase = 'TERMINE' THEN 1 ELSE 0 END) as phases_terminees,
                    SUM(CASE WHEN statut_phase = 'EN_COURS' THEN 1 ELSE 0 END) as phases_en_cours,
                    SUM(CASE WHEN statut_phase = 'BLOQUE' THEN 1 ELSE 0 END) as phases_bloquees,
                    AVG(progression_pct) as progression_moyenne
                FROM phases_operations
                WHERE operation_id = ?
            """, (operation_id,))
            
            stats = dict(cursor.fetchone())
            
            # Logique de calcul du statut
            if stats['phases_bloquees'] > 0:
                nouveau_statut = 'BLOQUE'
            elif stats['phases_terminees'] == stats['total_phases']:
                nouveau_statut = 'TERMINE'
            elif stats['phases_en_cours'] > 0 or stats['phases_terminees'] > 0:
                nouveau_statut = 'EN_COURS'
            else:
                nouveau_statut = 'EN_PREPARATION'
            
            # Mettre à jour le statut
            cursor.execute("""
                UPDATE operations 
                SET statut_global = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (nouveau_statut, operation_id))
            
            conn.commit()
            return nouveau_statut

    def calculate_risk_score(self, operation_id: str) -> int:
        """Calculer le score de risque d'une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            score_total = 0
            criteres = config.CRITERES_RISQUE
            
            # 1. Retard phases (25%)
            cursor.execute("""
                SELECT COUNT(*) as phases_retard,
                       AVG(CASE WHEN date_fin_prevue < date('now') AND statut_phase != 'TERMINE' 
                           THEN julianday('now') - julianday(date_fin_prevue) 
                           ELSE 0 END) as retard_moyen
                FROM phases_operations
                WHERE operation_id = ?
            """, (operation_id,))
            
            retard_data = dict(cursor.fetchone())
            retard_moyen = retard_data['retard_moyen'] or 0
            
            if retard_moyen > criteres['retard_phases']['seuils']['critique']:
                score_retard = 100
            elif retard_moyen > criteres['retard_phases']['seuils']['eleve']:
                score_retard = 75
            elif retard_moyen > criteres['retard_phases']['seuils']['moyen']:
                score_retard = 50
            else:
                score_retard = 25
                
            score_total += score_retard * criteres['retard_phases']['poids'] / 100
            
            # 2. Dépassement budget (30%)
            cursor.execute("""
                SELECT budget_initial, budget_revise, budget_final
                FROM operations WHERE id = ?
            """, (operation_id,))
            
            budget_data = dict(cursor.fetchone())
            budget_initial = budget_data['budget_initial'] or 0
            budget_actuel = budget_data['budget_final'] or budget_data['budget_revise'] or budget_initial
            
            if budget_initial > 0:
                depassement_pct = ((budget_actuel - budget_initial) / budget_initial) * 100
                
                if depassement_pct > criteres['depassement_budget']['seuils']['critique']:
                    score_budget = 100
                elif depassement_pct > criteres['depassement_budget']['seuils']['eleve']:
                    score_budget = 75
                elif depassement_pct > criteres['depassement_budget']['seuils']['moyen']:
                    score_budget = 50
                else:
                    score_budget = 25
            else:
                score_budget = 0
                
            score_total += score_budget * criteres['depassement_budget']['poids'] / 100
            
            # 3. Alertes actives (20%)
            cursor.execute("""
                SELECT COUNT(*) as nb_alertes
                FROM alertes
                WHERE operation_id = ? AND actif = 1
            """, (operation_id,))
            
            nb_alertes = cursor.fetchone()['nb_alertes']
            
            if nb_alertes > criteres['alertes_actives']['seuils']['critique']:
                score_alertes = 100
            elif nb_alertes > criteres['alertes_actives']['seuils']['eleve']:
                score_alertes = 75
            elif nb_alertes > criteres['alertes_actives']['seuils']['moyen']:
                score_alertes = 50
            else:
                score_alertes = 25
                
            score_total += score_alertes * criteres['alertes_actives']['poids'] / 100
            
            # 4. Phases bloquées (15%)
            cursor.execute("""
                SELECT COUNT(*) as phases_bloquees
                FROM phases_operations
                WHERE operation_id = ? AND statut_phase = 'BLOQUE'
            """, (operation_id,))
            
            phases_bloquees = cursor.fetchone()['phases_bloquees']
            
            if phases_bloquees > criteres['phases_bloquees']['seuils']['critique']:
                score_blocage = 100
            elif phases_bloquees > criteres['phases_bloquees']['seuils']['eleve']:
                score_blocage = 75
            elif phases_bloquees > criteres['phases_bloquees']['seuils']['moyen']:
                score_blocage = 50
            else:
                score_blocage = 25
                
            score_total += score_blocage * criteres['phases_bloquees']['poids'] / 100
            
            # 5. Avancement global (10%)
            cursor.execute("""
                SELECT AVG(progression_pct) as avancement_moyen
                FROM phases_operations
                WHERE operation_id = ?
            """, (operation_id,))
            
            avancement = cursor.fetchone()['avancement_moyen'] or 0
            
            if avancement < criteres['avancement_global']['seuils']['critique']:
                score_avancement = 100
            elif avancement < criteres['avancement_global']['seuils']['eleve']:
                score_avancement = 75
            elif avancement < criteres['avancement_global']['seuils']['moyen']:
                score_avancement = 50
            else:
                score_avancement = 25
                
            score_total += score_avancement * criteres['avancement_global']['poids'] / 100
            
            # Arrondir le score final
            score_final = min(100, max(0, round(score_total)))
            
            # Mettre à jour le score dans la BDD
            cursor.execute("""
                UPDATE operations 
                SET score_risque = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (score_final, operation_id))
            
            conn.commit()
            return score_final

    def generate_alerts(self, operation_id: str = None):
        """Générer des alertes automatiques selon les seuils"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Requête pour toutes les opérations ou une spécifique
            where_clause = "WHERE o.id = ?" if operation_id else ""
            params = [operation_id] if operation_id else []
            
            cursor.execute(f"""
                SELECT o.id, o.nom, o.budget_initial, o.budget_revise, o.budget_final,
                       COUNT(p.id) as total_phases,
                       SUM(CASE WHEN p.statut_phase = 'BLOQUE' THEN 1 ELSE 0 END) as phases_bloquees,
                       SUM(CASE WHEN p.date_fin_prevue < date('now') AND p.statut_phase != 'TERMINE' 
                           THEN 1 ELSE 0 END) as phases_retard
                FROM operations o
                LEFT JOIN phases_operations p ON o.id = p.operation_id
                {where_clause}
                GROUP BY o.id
            """, params)
            
            operations = cursor.fetchall()
            
            for op in operations:
                operation_dict = dict(op)
                
                # Alerte retards
                if operation_dict['phases_retard'] > 0:
                    niveau = 'CRITIQUE' if operation_dict['phases_retard'] > 3 else 'ELEVE'
                    
                    # Vérifier si alerte existe déjà
                    cursor.execute("""
                        SELECT id FROM alertes 
                        WHERE operation_id = ? AND type_alerte = 'RETARD' AND actif = 1
                    """, (operation_dict['id'],))
                    
                    if not cursor.fetchone():
                        self.create_alert(
                            operation_dict['id'], None, 'RETARD', niveau,
                            f"Retards détectés - {operation_dict['nom']}",
                            f"{operation_dict['phases_retard']} phase(s) en retard"
                        )
                
                # Alerte budget
                budget_initial = operation_dict['budget_initial'] or 0
                budget_actuel = (operation_dict['budget_final'] or 
                               operation_dict['budget_revise'] or budget_initial)
                
                if budget_initial > 0:
                    depassement_pct = ((budget_actuel - budget_initial) / budget_initial) * 100
                    seuil_critique = config.SEUILS_ALERTES['budget_critique_pct']
                    seuil_alerte = config.SEUILS_ALERTES['budget_depassement_pct']
                    
                    if depassement_pct > seuil_alerte:
                        niveau = 'CRITIQUE' if depassement_pct > seuil_critique else 'ELEVE'
                        
                        cursor.execute("""
                            SELECT id FROM alertes 
                            WHERE operation_id = ? AND type_alerte = 'BUDGET' AND actif = 1
                        """, (operation_dict['id'],))
                        
                        if not cursor.fetchone():
                            self.create_alert(
                                operation_dict['id'], None, 'BUDGET', niveau,
                                f"Dépassement budgétaire - {operation_dict['nom']}",
                                f"Dépassement de {depassement_pct:.1f}%"
                            )
                
                # Alerte phases bloquées
                if operation_dict['phases_bloquees'] > 0:
                    niveau = 'CRITIQUE' if operation_dict['phases_bloquees'] > 2 else 'ELEVE'
                    
                    cursor.execute("""
                        SELECT id FROM alertes 
                        WHERE operation_id = ? AND type_alerte = 'TECHNIQUE' AND actif = 1
                    """, (operation_dict['id'],))
                    
                    if not cursor.fetchone():
                        self.create_alert(
                            operation_dict['id'], None, 'TECHNIQUE', niveau,
                            f"Phases bloquées - {operation_dict['nom']}",
                            f"{operation_dict['phases_bloquees']} phase(s) bloquée(s)"
                        )
            
            conn.commit()

    # =============================================================================
    # REQUÊTES MÉTIER ET DASHBOARD
    # =============================================================================
    
    def get_operations_dashboard(self) -> Dict:
        """Récupérer les métriques pour le dashboard manager"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_operations,
                    SUM(CASE WHEN statut_global = 'EN_COURS' THEN 1 ELSE 0 END) as operations_actives,
                    SUM(CASE WHEN statut_global = 'TERMINE' THEN 1 ELSE 0 END) as operations_terminees,
                    SUM(CASE WHEN statut_global = 'BLOQUE' THEN 1 ELSE 0 END) as operations_bloquees,
                    AVG(score_risque) as score_risque_moyen,
                    SUM(budget_initial) as budget_total_initial,
                    SUM(COALESCE(budget_final, budget_revise, budget_initial)) as budget_total_actuel
                FROM operations
            """)
            
            stats = dict(cursor.fetchone())
            
            # Répartition par type
            cursor.execute("""
                SELECT type_operation, COUNT(*) as count
                FROM operations
                GROUP BY type_operation
            """)
            
            repartition_type = {row['type_operation']: row['count'] for row in cursor.fetchall()}
            
            # Répartition par statut
            cursor.execute("""
                SELECT statut_global, COUNT(*) as count
                FROM operations
                GROUP BY statut_global
            """)
            
            repartition_statut = {row['statut_global']: row['count'] for row in cursor.fetchall()}
            
            # TOP 3 des risques
            cursor.execute("""
                SELECT nom, score_risque, statut_global
                FROM operations
                ORDER BY score_risque DESC
                LIMIT 3
            """)
            
            top_risques = [dict(row) for row in cursor.fetchall()]
            
            # Alertes actives par niveau
            cursor.execute("""
                SELECT niveau_severite, COUNT(*) as count
                FROM alertes
                WHERE actif = 1
                GROUP BY niveau_severite
            """)
            
            alertes_par_niveau = {row['niveau_severite']: row['count'] for row in cursor.fetchall()}
            
            return {
                'statistiques': stats,
                'repartition_type': repartition_type,
                'repartition_statut': repartition_statut,
                'top_risques': top_risques,
                'alertes_par_niveau': alertes_par_niveau
            }

    def get_timeline_data(self, operation_id: str) -> Dict:
        """Récupérer les données pour la timeline colorée"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Phases avec leurs données
            cursor.execute("""
                SELECT p.*, 
                       CASE 
                           WHEN p.date_fin_prevue < date('now') AND p.statut_phase != 'TERMINE' 
                           THEN 1 ELSE 0 
                       END as en_retard
                FROM phases_operations p
                WHERE p.operation_id = ?
                ORDER BY p.ordre
            """, (operation_id,))
            
            phases = [dict(row) for row in cursor.fetchall()]
            
            # Alertes liées aux phases
            cursor.execute("""
                SELECT a.*, p.nom_phase
                FROM alertes a
                LEFT JOIN phases_operations p ON a.phase_id = p.id
                WHERE a.operation_id = ? AND a.actif = 1
                ORDER BY a.date_creation
            """, (operation_id,))
            
            alertes = [dict(row) for row in cursor.fetchall()]
            
            # Événements du journal pour cette opération
            cursor.execute("""
                SELECT j.*, u.nom, u.prenom, p.nom_phase
                FROM journal_modifications j
                LEFT JOIN utilisateurs_spic u ON j.utilisateur_id = u.id
                LEFT JOIN phases_operations p ON j.phase_id = p.id
                WHERE j.operation_id = ?
                ORDER BY j.timestamp DESC
                LIMIT 20
            """, (operation_id,))
            
            journal = [dict(row) for row in cursor.fetchall()]
            
            return {
                'phases': phases,
                'alertes': alertes,
                'journal': journal
            }

    def get_top_risks(self, limit: int = 10) -> List[Dict]:
        """Récupérer le TOP des opérations à risque"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT o.*, u.nom as responsable_nom, u.prenom as responsable_prenom,
                       COUNT(a.id) as nb_alertes_actives
                FROM operations o
                LEFT JOIN utilisateurs_spic u ON o.responsable_id = u.id
                LEFT JOIN alertes a ON o.id = a.operation_id AND a.actif = 1
                GROUP BY o.id
                ORDER BY o.score_risque DESC, nb_alertes_actives DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_budget_evolution_global(self) -> Dict:
        """Récupérer l'évolution budgétaire globale du portefeuille"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Évolution par mois
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', b.date_budget) as mois,
                    b.type_budget,
                    SUM(b.montant) as montant_total
                FROM budgets_globaux b
                GROUP BY strftime('%Y-%m', b.date_budget), b.type_budget
                ORDER BY mois
            """)
            
            evolution_mensuelle = [dict(row) for row in cursor.fetchall()]
            
            # Répartition par type d'opération
            cursor.execute("""
                SELECT 
                    o.type_operation,
                    SUM(o.budget_initial) as budget_initial_total,
                    SUM(COALESCE(o.budget_final, o.budget_revise, o.budget_initial)) as budget_actuel_total,
                    COUNT(*) as nb_operations
                FROM operations o
                GROUP BY o.type_operation
            """)
            
            repartition_type = [dict(row) for row in cursor.fetchall()]
            
            return {
                'evolution_mensuelle': evolution_mensuelle,
                'repartition_type': repartition_type
            }

    # =============================================================================
    # EXPORTS ET RAPPORTS
    # =============================================================================
    
    def export_operation_data(self, operation_id: str) -> Dict:
        """Exporter toutes les données d'une opération"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Données opération
            operation = self.get_operation(operation_id)
            if not operation:
                return {}
            
            # Phases
            phases = self.get_phases_by_operation(operation_id)
            
            # Budget
            budgets = self.get_budget_evolution(operation_id)
            
            # REM
            rem = self.get_rem_by_operation(operation_id)
            
            # Alertes
            alertes = self.get_active_alerts(operation_id)
            
            # Journal
            journal = self.get_journal_entries(operation_id, 50)
            
            return {
                'operation': operation,
                'phases': phases,
                'budgets': budgets,
                'rem': rem,
                'alertes': alertes,
                'journal': journal,
                'export_date': datetime.now().isoformat()
            }

    def get_operations_summary(self) -> List[Dict]:
        """Récupérer un résumé de toutes les opérations pour export"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    o.*,
                    u.nom as responsable_nom,
                    u.prenom as responsable_prenom,
                    COUNT(p.id) as nb_phases_total,
                    SUM(CASE WHEN p.statut_phase = 'TERMINE' THEN 1 ELSE 0 END) as nb_phases_terminees,
                    AVG(p.progression_pct) as progression_moyenne,
                    COUNT(a.id) as nb_alertes_actives
                FROM operations o
                LEFT JOIN utilisateurs_spic u ON o.responsable_id = u.id
                LEFT JOIN phases_operations p ON o.id = p.operation_id
                LEFT JOIN alertes a ON o.id = a.operation_id AND a.actif = 1
                GROUP BY o.id
                ORDER BY o.created_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]

    # =============================================================================
    # COMPATIBILITÉ FUTURE OPCOPILOT
    # =============================================================================
    
    def prepare_sync_data(self, operation_id: str = None) -> Dict:
        """Préparer les données pour synchronisation future avec OPCOPILOT"""
        sync_data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'source': 'SPIC',
            'tables': {}
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tables à synchroniser avec OPCOPILOT
            tables_partagees = config.TABLES_PARTAGEES_OPCOPILOT
            
            for table in tables_partagees:
                if operation_id and table in ['operations', 'phases_operations', 'budgets']:
                    # Filtrer par opération
                    if table == 'operations':
                        cursor.execute("SELECT * FROM operations WHERE id = ?", (operation_id,))
                    elif table == 'phases_operations':
                        cursor.execute("SELECT * FROM phases_operations WHERE operation_id = ?", (operation_id,))
                    elif table == 'budgets':
                        cursor.execute("SELECT * FROM budgets_globaux WHERE operation_id = ?", (operation_id,))
                else:
                    # Toutes les données
                    cursor.execute(f"SELECT * FROM {table}")
                
                rows = cursor.fetchall()
                sync_data['tables'][table] = [dict(row) for row in rows]
        
        return sync_data

    def import_sync_data(self, sync_data: Dict, user_id: str) -> bool:
        """Importer des données de synchronisation (future utilisation OPCOPILOT)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Exemple d'import (à adapter selon besoins OPCOPILOT)
                if 'operations' in sync_data.get('tables', {}):
                    for op_data in sync_data['tables']['operations']:
                        # Vérifier si opération existe
                        cursor.execute("SELECT id FROM operations WHERE id = ?", (op_data['id'],))
                        if cursor.fetchone():
                            # Mettre à jour
                            self.update_operation(op_data['id'], op_data, user_id)
                        else:
                            # Créer nouvelle
                            self.create_operation(op_data, user_id)
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erreur import sync: {e}")
            return False

    # =============================================================================
    # UTILITAIRES ET MAINTENANCE
    # =============================================================================
    
    def cleanup_old_journal_entries(self, days_to_keep: int = 365):
        """Nettoyer les anciennes entrées du journal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM journal_modifications 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Nettoyage journal: {deleted_count} entrées supprimées")
            return deleted_count

    def cleanup_resolved_alerts(self, days_to_keep: int = 90):
        """Nettoyer les alertes résolues anciennes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM alertes 
                WHERE statut = 'RESOLVED' 
                AND date_resolution < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Nettoyage alertes: {deleted_count} alertes supprimées")
            return deleted_count

    def backup_database(self, backup_path: str = None) -> str:
        """Créer une sauvegarde de la base de données"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backup_spic_{timestamp}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        logger.info(f"Sauvegarde créée: {backup_path}")
        return backup_path

    def get_database_stats(self) -> Dict:
        """Récupérer les statistiques de la base de données"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Nombre d'enregistrements par table
            tables = ['operations', 'phases_operations', 'utilisateurs_spic', 
                     'droits_operations', 'journal_modifications', 'alertes',
                     'budgets_globaux', 'rem_operations']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"nb_{table}"] = cursor.fetchone()['count']
            
            # Taille de la base
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            stats['taille_db_bytes'] = cursor.fetchone()['size']
            
            # Dernière modification
            cursor.execute("""
                SELECT MAX(timestamp) as derniere_modification 
                FROM journal_modifications
            """)
            
            result = cursor.fetchone()
            stats['derniere_modification'] = result['derniere_modification'] if result else None
            
            return stats

    def validate_data_integrity(self) -> Dict:
        """Valider l'intégrité des données"""
        issues = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier orphelins phases
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM phases_operations p
                LEFT JOIN operations o ON p.operation_id = o.id
                WHERE o.id IS NULL
            """)
            
            orphan_phases = cursor.fetchone()['count']
            if orphan_phases > 0:
                issues.append(f"{orphan_phases} phases orphelines détectées")
            
            # Vérifier droits orphelins
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM droits_operations d
                LEFT JOIN operations o ON d.operation_id = o.id
                LEFT JOIN utilisateurs_spic u ON d.utilisateur_id = u.id
                WHERE o.id IS NULL OR u.id IS NULL
            """)
            
            orphan_rights = cursor.fetchone()['count']
            if orphan_rights > 0:
                issues.append(f"{orphan_rights} droits orphelins détectés")
            
            # Vérifier alertes orphelines
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM alertes a
                LEFT JOIN operations o ON a.operation_id = o.id
                WHERE o.id IS NULL
            """)
            
            orphan_alerts = cursor.fetchone()['count']
            if orphan_alerts > 0:
                issues.append(f"{orphan_alerts} alertes orphelines détectées")
        
        return {
            'valide': len(issues) == 0,
            'problemes': issues,
            'verifiction_date': datetime.now().isoformat()
        }

    def recalculate_all_scores(self) -> int:
        """Recalculer tous les scores de risque"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM operations")
            operation_ids = [row['id'] for row in cursor.fetchall()]
        
        count = 0
        for operation_id in operation_ids:
            self.calculate_risk_score(operation_id)
            count += 1
        
        logger.info(f"Scores de risque recalculés pour {count} opérations")
        return count

    def update_all_statuses(self) -> int:
        """Mettre à jour tous les statuts d'opérations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM operations")
            operation_ids = [row['id'] for row in cursor.fetchall()]
        
        count = 0
        for operation_id in operation_ids:
            self.calculate_operation_status(operation_id)
            count += 1
        
        logger.info(f"Statuts mis à jour pour {count} opérations")
        return count

    def close(self):
        """Fermer les connexions (si nécessaire)"""
        # Avec le gestionnaire de contexte, pas besoin de fermeture explicite
        logger.info("Gestionnaire de base de données fermé")

# =============================================================================
# FONCTIONS UTILITAIRES GLOBALES
# =============================================================================

def get_db_manager(db_path: str = None) -> DatabaseManager:
    """Factory pour créer une instance du gestionnaire de BDD"""
    return DatabaseManager(db_path)

def init_demo_database(db_path: str = "data/spic_demo.db") -> DatabaseManager:
    """Initialiser une base de données de démonstration"""
    import os
    
    # Créer le dossier data s'il n'existe pas
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Supprimer ancienne BDD si elle existe
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Créer nouvelle BDD avec données démo
    db = DatabaseManager(db_path)
    logger.info(f"Base de données de démonstration créée: {db_path}")
    
    return db

# =============================================================================
# TESTS INTÉGRITÉ (OPTIONNEL)
# =============================================================================

def test_database_operations():
    """Tests basiques des opérations BDD"""
    try:
        # Utiliser BDD temporaire pour tests
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            test_db_path = tmp.name
        
        db = DatabaseManager(test_db_path)
        
        # Test création utilisateur
        user_data = {
            'nom': 'TEST',
            'prenom': 'User',
            'email': 'test@test.com',
            'mot_de_passe': 'test123',
            'role': 'ADMIN'
        }
        user_id = db.create_user(user_data)
        assert user_id is not None
        
        # Test création opération
        op_data = {
            'nom': 'Test Operation',
            'type_operation': 'OPP',
            'budget_initial': 100000
        }
        op_id = db.create_operation(op_data, user_id)
        assert op_id is not None
        
        # Test récupération
        operation = db.get_operation(op_id)
        assert operation['nom'] == 'Test Operation'
        
        # Test calcul score
        score = db.calculate_risk_score(op_id)
        assert isinstance(score, int)
        
        # Nettoyer
        os.unlink(test_db_path)
        
        logger.info("Tests base de données: OK")
        return True
        
    except Exception as e:
        logger.error(f"Tests base de données échoués: {e}")
        return False

if __name__ == "__main__":
    # Exécuter tests si lancé directement
    test_database_operations()
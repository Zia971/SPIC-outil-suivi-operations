# 🏗️ SPIC 2.0 - Suivi Professionnel d'Opérations de Construction

> Outil de pilotage MOA intelligent et collaboratif pour le suivi d'opérations immobilières

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-Proprietary-yellow)]()

## 📋 Table des Matières

- [🎯 Présentation](#-présentation)
- [✨ Fonctionnalités](#-fonctionnalités)
- [🏗️ Architecture](#️-architecture)
- [⚡ Installation](#-installation)
- [🚀 Utilisation](#-utilisation)
- [👥 Gestion des Utilisateurs](#-gestion-des-utilisateurs)
- [🔮 Compatibilité OPCOPILOT](#-compatibilité-opcopilot)
- [🛠️ Développement](#️-développement)
- [📞 Support](#-support)

## 🎯 Présentation

**SPIC 2.0** est un outil professionnel de suivi d'opérations de construction destiné aux Maîtres d'Ouvrage (MOA). Il offre une vision stratégique et managériale complète du portefeuille d'opérations immobilières.

### Objectifs Principaux

- **Suivi en temps réel** des opérations (OPP, VEFA, AMO, MANDAT)
- **Gestion des 113 phases** selon référentiel métier normé
- **Analyse intelligente des risques** avec scoring automatique
- **Timeline dynamique** avec alertes intégrées
- **Suivi budgétaire** complémentaire aux outils existants
- **Interface collaborative** multi-utilisateurs avec gestion des droits

## ✨ Fonctionnalités

### 🏗️ Suivi des Opérations
- **Portefeuille complet** avec filtres avancés
- **Vue manager** avec KPI et métriques en temps réel
- **Timeline colorée** style PowerPoint avec jalons visuels
- **Gestion CRUD** complète des opérations
- **113 phases exactes** par type d'opération :
  - **OPP** : 45 phases (Opérations Propres)
  - **VEFA** : 22 phases (Vente en État Futur d'Achèvement)
  - **AMO** : 22 phases (Assistance à Maîtrise d'Ouvrage)
  - **MANDAT** : 24 phases (Opérations en Mandat)

### 📚 Gestion du Journal
- **Historique complet** des modifications avec horodatage
- **Recherche avancée** par utilisateur, période, action
- **Statistiques d'activité** et métriques d'usage
- **Traçabilité** de toutes les actions utilisateur

### 💰 Suivi Financier
- **Gestion budgétaire** (initial/révisé/final)
- **Évolution budgétaire** avec graphiques interactifs
- **Module REM** simple par trimestre/semestre
- **Alertes dépassements** configurables
- **Complémentarité** avec outils existants (Gespro)

### 🚨 Gestion des Risques
- **Score de risque automatique** basé sur 5 critères pondérés
- **TOP 3 des opérations** à risque avec recommandations
- **Alertes intelligentes** multi-niveaux (FAIBLE/MOYEN/ÉLEVÉ/CRITIQUE)
- **Dashboard risques** avec analyses visuelles

### 📥 Exports et Rapports
- **Export Word** avec templates personnalisables
- **Export Excel** multi-feuilles avec données structurées
- **Export PDF** via conversion automatique
- **Rapports personnalisés** avec filtres avancés
- **Exports graphiques** (PNG, SVG, HTML interactif)

## 🏗️ Architecture

### Structure du Projet
SPIC/
│
├── app.py
├── config.py  
├── database.py
├── requirements.txt
├── README.md
│
├── utils/
│   ├── __init__.py
│   ├── constants.py
│   ├── risk_score.py
│   ├── db_utils.py
│   ├── form_utils.py
│   └── utils.py
│
├── modules/
│   ├── __init__.py
│   ├── suivi_operations.py
│   ├── gestion_journal.py
│   ├── suivi_financier.py
│   ├── gestion_risques.py
│   └── exports.py
│
├── data/
│   └── (vide au début - la BDD se crée automatiquement)
│
└── assets/
    └── css/
        └── style.css

### Principes Architecturaux

- **Modularité** : Séparation claire des responsabilités
- **Réutilisabilité** : Composants utils/ partagés
- **Évolutivité** : Architecture prête pour extensions
- **Performance** : Cache Streamlit optimisé
- **Sécurité** : Gestion des droits utilisateur

## ⚡ Installation

### Prérequis

- **Python 3.8+** installé sur votre système
- **Git** pour cloner le projet (optionnel)
- **Navigateur web** moderne (Chrome, Firefox, Safari, Edge)

### Installation Pas à Pas

1. **Télécharger le projet**
   ```bash
   # Option 1: Via Git
   git clone <repository_url>
   cd SPIC
   
   # Option 2: Télécharger et extraire l'archive ZIP
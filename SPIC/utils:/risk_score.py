"""
Calcul spécialisé du score de risque pour SPIC 2.0
Algorithmes basés sur les critères métier
"""

import config
from typing import Dict, List, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class RiskScoreCalculator:
    """Calculateur de score de risque intelligent"""
    
    def __init__(self):
        self.criteria = config.CRITERES_RISQUE
        self.thresholds = config.SEUILS_ALERTES
    
    def calculate_comprehensive_score(self, operation_data: Dict, 
                                    phases_data: List[Dict], 
                                    alerts_data: List[Dict]) -> Dict:
        """Calcul complet du score de risque avec détails"""
        
        scores = {}
        details = {}
        
        # 1. Score retards (25%)
        scores['retard'], details['retard'] = self._calculate_delay_score(phases_data)
        
        # 2. Score budget (30%) 
        scores['budget'], details['budget'] = self._calculate_budget_score(operation_data)
        
        # 3. Score alertes (20%)
        scores['alertes'], details['alertes'] = self._calculate_alerts_score(alerts_data)
        
        # 4. Score blocages (15%)
        scores['blocages'], details['blocages'] = self._calculate_blocking_score(phases_data)
        
        # 5. Score avancement (10%)
        scores['avancement'], details['avancement'] = self._calculate_progress_score(phases_data)
        
        # Score final pondéré
        final_score = (
            scores['retard'] * self.criteria['retard_phases']['poids'] / 100 +
            scores['budget'] * self.criteria['depassement_budget']['poids'] / 100 +
            scores['alertes'] * self.criteria['alertes_actives']['poids'] / 100 +
            scores['blocages'] * self.criteria['phases_bloquees']['poids'] / 100 +
            scores['avancement'] * self.criteria['avancement_global']['poids'] / 100
        )
        
        final_score = min(100, max(0, round(final_score)))
        
        return {
            'score_total': final_score,
            'niveau_risque': self._get_risk_level(final_score),
            'scores_detail': scores,
            'explications': details,
            'recommandations': self._generate_recommendations(scores, details),
            'calcul_date': datetime.now().isoformat()
        }
    
    def _calculate_delay_score(self, phases_data: List[Dict]) -> Tuple[int, Dict]:
        """Calculer le score des retards"""
        if not phases_data:
            return 0, {'phases_retard': 0, 'retard_moyen': 0}
        
        phases_en_retard = []
        retards_jours = []
        
        today = date.today()
        
        for phase in phases_data:
            if (phase.get('date_fin_prevue') and 
                phase.get('statut_phase') != 'TERMINE'):
                
                date_fin = datetime.strptime(phase['date_fin_prevue'], '%Y-%m-%d').date()
                
                if date_fin < today:
                    retard_jours = (today - date_fin).days
                    phases_en_retard.append({
                        'nom': phase.get('nom_phase', ''),
                        'retard_jours': retard_jours
                    })
                    retards_jours.append(retard_jours)
        
        if not retards_jours:
            return 0, {'phases_retard': 0, 'retard_moyen': 0}
        
        retard_moyen = sum(retards_jours) / len(retards_jours)
        seuils = self.criteria['retard_phases']['seuils']
        
        if retard_moyen > seuils['critique']:
            score = 100
        elif retard_moyen > seuils['eleve']:
            score = 75
        elif retard_moyen > seuils['moyen']:
            score = 50
        else:
            score = 25
        
        return score, {
            'phases_retard': len(phases_en_retard),
            'retard_moyen': round(retard_moyen, 1),
            'detail_phases': phases_en_retard
        }
    
    def _calculate_budget_score(self, operation_data: Dict) -> Tuple[int, Dict]:
        """Calculer le score budgétaire"""
        budget_initial = operation_data.get('budget_initial', 0)
        budget_final = operation_data.get('budget_final')
        budget_revise = operation_data.get('budget_revise')
        
        if budget_initial <= 0:
            return 0, {'depassement_pct': 0, 'message': 'Budget initial non défini'}
        
        budget_actuel = budget_final or budget_revise or budget_initial
        depassement_pct = ((budget_actuel - budget_initial) / budget_initial) * 100
        
        seuils = self.criteria['depassement_budget']['seuils']
        
        if depassement_pct > seuils['critique']:
            score = 100
        elif depassement_pct > seuils['eleve']:
            score = 75
        elif depassement_pct > seuils['moyen']:
            score = 50
        else:
            score = 0 if depassement_pct <= 0 else 25
        
        return score, {
            'depassement_pct': round(depassement_pct, 1),
            'budget_initial': budget_initial,
            'budget_actuel': budget_actuel,
            'ecart_montant': budget_actuel - budget_initial
        }
    
    def _calculate_alerts_score(self, alerts_data: List[Dict]) -> Tuple[int, Dict]:
        """Calculer le score des alertes"""
        alertes_actives = [a for a in alerts_data if a.get('actif', True)]
        nb_alertes = len(alertes_actives)
        
        # Pondération par niveau de sévérité
        score_alerte = 0
        repartition = {'FAIBLE': 0, 'MOYEN': 0, 'ELEVE': 0, 'CRITIQUE': 0}
        
        for alerte in alertes_actives:
            niveau = alerte.get('niveau_severite', 'MOYEN')
            repartition[niveau] = repartition.get(niveau, 0) + 1
            
            if niveau == 'CRITIQUE':
                score_alerte += 25
            elif niveau == 'ELEVE':
                score_alerte += 15
            elif niveau == 'MOYEN':
                score_alerte += 10
            else:
                score_alerte += 5
        
        score_final = min(100, score_alerte)
        
        return score_final, {
            'nb_alertes_total': nb_alertes,
            'repartition_niveaux': repartition,
            'score_pondere': score_alerte
        }
    
    def _calculate_blocking_score(self, phases_data: List[Dict]) -> Tuple[int, Dict]:
        """Calculer le score des blocages"""
        phases_bloquees = [p for p in phases_data if p.get('statut_phase') == 'BLOQUE']
        nb_bloquees = len(phases_bloquees)
        
        seuils = self.criteria['phases_bloquees']['seuils']
        
        if nb_bloquees > seuils['critique']:
            score = 100
        elif nb_bloquees > seuils['eleve']:
            score = 75
        elif nb_bloquees > seuils['moyen']:
            score = 50
        elif nb_bloquees > 0:
            score = 25
        else:
            score = 0
        
        detail_phases = [{'nom': p.get('nom_phase', ''), 
                         'ordre': p.get('ordre', 0)} for p in phases_bloquees]
        
        return score, {
            'nb_phases_bloquees': nb_bloquees,
            'detail_phases': detail_phases
        }
    
    def _calculate_progress_score(self, phases_data: List[Dict]) -> Tuple[int, Dict]:
        """Calculer le score d'avancement"""
        if not phases_data:
            return 0, {'avancement_moyen': 0}
        
        progressions = [p.get('progression_pct', 0) for p in phases_data]
        avancement_moyen = sum(progressions) / len(progressions)
        
        seuils = self.criteria['avancement_global']['seuils']
        
        if avancement_moyen < seuils['critique']:
            score = 100
        elif avancement_moyen < seuils['eleve']:
            score = 75
        elif avancement_moyen < seuils['moyen']:
            score = 50
        else:
            score = 0
        
        return score, {
            'avancement_moyen': round(avancement_moyen, 1),
            'nb_phases_total': len(phases_data),
            'phases_terminees': len([p for p in phases_data if p.get('statut_phase') == 'TERMINE'])
        }
    
    def _get_risk_level(self, score: int) -> str:
        """Déterminer le niveau de risque selon le score"""
        for niveau, config_niveau in config.NIVEAUX_RISQUE.items():
            if config_niveau['score_min'] <= score <= config_niveau['score_max']:
                return niveau
        return 'FAIBLE'
    
    def _generate_recommendations(self, scores: Dict, details: Dict) -> List[str]:
        """Générer des recommandations selon les scores"""
        recommendations = []
        
        # Recommandations retards
        if scores['retard'] >= 75:
            recommendations.append("🚨 Reprioriser les phases en retard et renforcer les équipes")
        elif scores['retard'] >= 50:
            recommendations.append("⚠️ Analyser les causes de retard et ajuster le planning")
        
        # Recommandations budget
        if scores['budget'] >= 75:
            recommendations.append("💰 Révision budgétaire urgente et contrôle des coûts")
        elif scores['budget'] >= 50:
            recommendations.append("📊 Surveiller l'évolution budgétaire de près")
        
        # Recommandations alertes
        if scores['alertes'] >= 75:
            recommendations.append("🔔 Traiter les alertes critiques en priorité")
        
        # Recommandations blocages
        if scores['blocages'] >= 75:
            recommendations.append("🔓 Débloquer les phases critiques immédiatement")
        
        # Recommandations avancement
        if scores['avancement'] >= 75:
            recommendations.append("⚡ Accélérer la réalisation des phases")
        
        if not recommendations:
            recommendations.append("✅ Opération sous contrôle, maintenir la surveillance")
        
        return recommendations

# Instance globale
risk_calculator = RiskScoreCalculator()

def calculate_risk_score(operation_data: Dict, phases_data: List[Dict], 
                        alerts_data: List[Dict]) -> Dict:
    """Interface principale de calcul du score de risque"""
    return risk_calculator.calculate_comprehensive_score(
        operation_data, phases_data, alerts_data
    )

def get_risk_trend(historical_scores: List[Dict]) -> Dict:
    """Analyser la tendance d'évolution du risque"""
    if len(historical_scores) < 2:
        return {'trend': 'stable', 'evolution': 0}
    
    scores = [s['score_total'] for s in historical_scores[-5:]]  # 5 derniers
    
    if len(scores) < 2:
        return {'trend': 'stable', 'evolution': 0}
    
    evolution = scores[-1] - scores[0]
    
    if evolution > 10:
        trend = 'degradation'
    elif evolution < -10:
        trend = 'amelioration'
    else:
        trend = 'stable'
    
    return {
        'trend': trend,
        'evolution': evolution,
        'scores_historique': scores
    }
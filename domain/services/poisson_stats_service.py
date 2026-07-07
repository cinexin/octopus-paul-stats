import math

from domain.models.constants import (
    PRIOR_WEIGHT, LEAGUE_AVG_GOALS, H2H_RAW_WEIGHT, H2H_DATA_WEIGHT,
    MAX_GOALS_POISSON, DRAW_TO_ET_WIN_PROB, DRAW_TO_PENALTIES_PROB,
    PENALTIES_WIN_PROB_T1, PENALTIES_WIN_PROB_T2,
)
from domain.models.probability_result import ProbabilityResult
from domain.models.team_stats import TeamStats
from domain.services.stats_computation_service import StatsComputationService


class PoissonStatsService(StatsComputationService):

    @staticmethod
    def _poisson_prob(k, lam):
        return (math.e ** -lam) * (lam ** k) / math.factorial(k)

    @staticmethod
    def _expected_goals(attack_avg, defend_avg, league_avg, n_matches):
        attack_weighted = (attack_avg * n_matches + league_avg * PRIOR_WEIGHT) / (n_matches + PRIOR_WEIGHT)
        defend_weighted = (defend_avg * n_matches + league_avg * PRIOR_WEIGHT) / (n_matches + PRIOR_WEIGHT)
        return (attack_weighted + defend_weighted) / 2

    def calculate_probabilities(self, team1_stats: TeamStats, team2_stats: TeamStats) -> ProbabilityResult:
        t1_exp_raw = self._expected_goals(
            team1_stats.avg_goals, team2_stats.avg_conceded, LEAGUE_AVG_GOALS, team1_stats.n_matches
        )
        t2_exp_raw = self._expected_goals(
            team2_stats.avg_goals, team1_stats.avg_conceded, LEAGUE_AVG_GOALS, team2_stats.n_matches
        )

        if team1_stats.h2h_avg_goals is not None and team2_stats.h2h_avg_goals is not None:
            exp_t1 = H2H_RAW_WEIGHT * t1_exp_raw + H2H_DATA_WEIGHT * team1_stats.h2h_avg_goals
            exp_t2 = H2H_RAW_WEIGHT * t2_exp_raw + H2H_DATA_WEIGHT * team2_stats.h2h_avg_goals
        else:
            exp_t1 = t1_exp_raw
            exp_t2 = t2_exp_raw

        probs = {}
        total_prob = 0.0

        for g1 in range(MAX_GOALS_POISSON + 1):
            for g2 in range(MAX_GOALS_POISSON + 1):
                p = self._poisson_prob(g1, exp_t1) * self._poisson_prob(g2, exp_t2)
                if g1 > g2:
                    key = 'team1_win'
                elif g2 > g1:
                    key = 'team2_win'
                else:
                    key = 'draw'
                probs[key] = probs.get(key, 0.0) + p
                total_prob += p

        for k in probs:
            probs[k] /= total_prob

        draw_prob = probs['draw']
        prob_et_t1 = draw_prob * DRAW_TO_ET_WIN_PROB
        prob_et_t2 = draw_prob * DRAW_TO_ET_WIN_PROB
        prob_penalties = draw_prob * DRAW_TO_PENALTIES_PROB
        prob_pen_t1 = prob_penalties * PENALTIES_WIN_PROB_T1
        prob_pen_t2 = prob_penalties * PENALTIES_WIN_PROB_T2

        return ProbabilityResult(
            team1_win_90=probs['team1_win'],
            team2_win_90=probs['team2_win'],
            draw_90=draw_prob,
            team1_win_et=prob_et_t1,
            team2_win_et=prob_et_t2,
            team1_win_pen=prob_pen_t1,
            team2_win_pen=prob_pen_t2,
            team1_total=probs['team1_win'] + prob_et_t1 + prob_pen_t1,
            team2_total=probs['team2_win'] + prob_et_t2 + prob_pen_t2,
            exp_t1=exp_t1,
            exp_t2=exp_t2,
        )

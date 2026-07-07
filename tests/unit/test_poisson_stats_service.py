import math

from domain.models.team_stats import TeamStats
from domain.services.poisson_stats_service import PoissonStatsService


class TestPoissonStatsService:
    def setup_method(self):
        self.service = PoissonStatsService()

    def test_poisson_prob_zero_goals(self):
        prob = self.service._poisson_prob(0, 1.0)
        expected = math.exp(-1.0)
        assert abs(prob - expected) < 1e-10

    def test_poisson_prob_one_goal(self):
        prob = self.service._poisson_prob(1, 1.0)
        expected = math.exp(-1.0) * 1.0
        assert abs(prob - expected) < 1e-10

    def test_poisson_prob_two_goals(self):
        prob = self.service._poisson_prob(2, 2.0)
        expected = math.exp(-2.0) * (2.0 ** 2) / 2
        assert abs(prob - expected) < 1e-10

    def test_poisson_prob_zero_lambda(self):
        prob = self.service._poisson_prob(5, 0.0)
        assert prob == 0.0

    def test_expected_goals_with_prior(self):
        # attack_avg=2.0, defend_avg=1.0, league_avg=1.25, n_matches=5
        result = self.service._expected_goals(2.0, 1.0, 1.25, 5)
        attack_w = (2.0 * 5 + 1.25 * 3) / (5 + 3)
        defend_w = (1.0 * 5 + 1.25 * 3) / (5 + 3)
        expected = (attack_w + defend_w) / 2
        assert abs(result - expected) < 1e-10

    def test_expected_goals_zero_matches(self):
        result = self.service._expected_goals(0, 0, 1.25, 0)
        attack_w = (0 + 1.25 * 3) / 3
        defend_w = (0 + 1.25 * 3) / 3
        expected = (attack_w + defend_w) / 2
        assert abs(result - expected) < 1e-10

    def test_calculate_probabilities_with_h2h(self):
        t1 = TeamStats(avg_goals=2.0, avg_conceded=1.0, n_matches=5, h2h_avg_goals=1.5)
        t2 = TeamStats(avg_goals=1.2, avg_conceded=1.8, n_matches=5, h2h_avg_goals=1.0)

        result = self.service.calculate_probabilities(t1, t2)

        assert 0 < result.team1_win_90 < 1
        assert 0 < result.draw_90 < 1
        assert 0 < result.team2_win_90 < 1
        assert abs(result.team1_win_90 + result.draw_90 + result.team2_win_90 - 1.0) < 0.01

        assert result.team1_win_90 > result.team2_win_90
        assert result.team1_total > result.team2_total
        assert result.exp_t1 > result.exp_t2

    def test_calculate_probabilities_without_h2h(self):
        t1 = TeamStats(avg_goals=2.0, avg_conceded=1.0, n_matches=5)
        t2 = TeamStats(avg_goals=1.2, avg_conceded=1.8, n_matches=5)

        result = self.service.calculate_probabilities(t1, t2)

        assert 0 < result.team1_win_90 < 1
        assert result.team1_win_90 > result.team2_win_90

    def test_calculate_probabilities_balanced_teams(self):
        t1 = TeamStats(avg_goals=1.25, avg_conceded=1.25, n_matches=10)
        t2 = TeamStats(avg_goals=1.25, avg_conceded=1.25, n_matches=10)

        result = self.service.calculate_probabilities(t1, t2)

        assert abs(result.team1_win_90 - result.team2_win_90) < 0.05
        assert abs(result.exp_t1 - result.exp_t2) < 0.05

    def test_probabilities_sum_to_one(self):
        t1 = TeamStats(avg_goals=1.8, avg_conceded=1.2, n_matches=8, h2h_avg_goals=1.3)
        t2 = TeamStats(avg_goals=1.5, avg_conceded=1.5, n_matches=8, h2h_avg_goals=1.1)

        result = self.service.calculate_probabilities(t1, t2)

        total_90 = result.team1_win_90 + result.draw_90 + result.team2_win_90
        assert abs(total_90 - 1.0) < 0.001

    def test_et_and_penalties_derived_from_draw(self):
        t1 = TeamStats(avg_goals=1.5, avg_conceded=1.5, n_matches=6)
        t2 = TeamStats(avg_goals=1.5, avg_conceded=1.5, n_matches=6)

        result = self.service.calculate_probabilities(t1, t2)

        from domain.models.constants import DRAW_TO_ET_WIN_PROB, DRAW_TO_PENALTIES_PROB

        expected_et = result.draw_90 * DRAW_TO_ET_WIN_PROB
        assert abs(result.team1_win_et - expected_et) < 0.001
        assert abs(result.team2_win_et - expected_et) < 0.001

        expected_pen_total = result.draw_90 * DRAW_TO_PENALTIES_PROB
        assert abs(result.team1_win_pen + result.team2_win_pen - expected_pen_total) < 0.001

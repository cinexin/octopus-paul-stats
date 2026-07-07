from unittest.mock import Mock, patch

from domain.models.team_stats import TeamStats
from domain.services.bet_explorer_team_stats_service import BetExplorerTeamStatsService
from domain.services.poisson_stats_service import PoissonStatsService
from infrastructure.betexplorer_repository import BetExplorerRepository


class TestFullStatsFlow:
    def setup_method(self):
        self.repo = BetExplorerRepository()
        self.team_service = BetExplorerTeamStatsService(self.repo)
        self.stats_service = PoissonStatsService()

    def test_complete_flow_with_mocked_data(self, mock_team_page_html):
        self.repo._team_cache['spain'] = '/team/spain/'
        self.repo._team_cache['france'] = '/team/france/'

        mock_resp = Mock()
        mock_resp.text = mock_team_page_html
        mock_resp.raise_for_status = Mock()

        with patch.object(self.repo.session, 'get', return_value=mock_resp):
            t1_stats = self.team_service.get_team_stats('Spain', n_matches=5)
            t2_stats = self.team_service.get_team_stats('France', n_matches=5)

        assert t1_stats is not None
        assert t2_stats is not None

        result = self.stats_service.calculate_probabilities(t1_stats, t2_stats)

        assert 0 < result.team1_win_90 < 1
        assert 0 < result.draw_90 < 1
        assert 0 < result.team2_win_90 < 1
        total = result.team1_win_90 + result.draw_90 + result.team2_win_90
        assert abs(total - 1.0) < 0.01

        assert result.exp_t1 >= 0
        assert result.exp_t2 >= 0

    def test_flow_with_identical_stats(self):
        t1 = TeamStats(avg_goals=1.5, avg_conceded=1.0, n_matches=10)
        t2 = TeamStats(avg_goals=1.5, avg_conceded=1.0, n_matches=10)

        result = self.stats_service.calculate_probabilities(t1, t2)

        assert abs(result.team1_win_90 - result.team2_win_90) < 0.05

    def test_flow_with_h2h_data(self):
        t1 = TeamStats(
            avg_goals=2.0, avg_conceded=0.5, n_matches=10,
            h2h_avg_goals=1.8,
        )
        t2 = TeamStats(
            avg_goals=0.8, avg_conceded=1.5, n_matches=10,
            h2h_avg_goals=0.7,
        )

        result = self.stats_service.calculate_probabilities(t1, t2)

        assert result.team1_win_90 > result.team2_win_90
        assert result.exp_t1 > result.exp_t2

    def test_flow_with_extreme_stats(self):
        t1 = TeamStats(avg_goals=5.0, avg_conceded=0.1, n_matches=20)
        t2 = TeamStats(avg_goals=0.2, avg_conceded=4.5, n_matches=20)

        result = self.stats_service.calculate_probabilities(t1, t2)

        assert result.team1_win_90 > 0.95
        assert result.team2_win_90 < 0.01

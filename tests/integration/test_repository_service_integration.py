from unittest.mock import Mock, patch

import pytest
import requests

from domain.services.bet_explorer_team_stats_service import BetExplorerTeamStatsService
from infrastructure.betexplorer_repository import BetExplorerRepository


class TestBetExplorerTeamStatsServiceIntegration:
    def setup_method(self):
        self.repo = BetExplorerRepository()
        self.service = BetExplorerTeamStatsService(self.repo)

    def test_get_team_stats_success(self, mock_team_page_html):
        self.repo._team_cache['spain'] = '/team/spain/'

        mock_resp = Mock()
        mock_resp.text = mock_team_page_html
        mock_resp.raise_for_status = Mock()

        with patch.object(self.repo.session, 'get', return_value=mock_resp):
            stats = self.service.get_team_stats('Spain', n_matches=3)

        assert stats is not None
        assert stats.n_matches == 2
        assert stats.avg_goals >= 0
        assert stats.avg_conceded >= 0
        assert len(stats.matches) == 2

    def test_get_team_stats_team_not_found(self):
        with patch.object(self.repo, 'find_team_url', return_value=None):
            with pytest.raises(ValueError, match='not found'):
                self.service.get_team_stats('Atlantis', n_matches=5)

    def test_get_team_stats_no_matches_for_team(self):
        self.repo._team_cache['spain'] = '/team/spain/'

        empty_html = '''
        <html><body>
        <table class="table-main">
          <tr><th>Qualification round</th></tr>
        </table>
        </body></html>
        '''
        mock_resp = Mock()
        mock_resp.text = empty_html
        mock_resp.raise_for_status = Mock()

        with patch.object(self.repo.session, 'get', return_value=mock_resp):
            stats = self.service.get_team_stats('Spain', n_matches=5)

        assert stats is None

    def test_network_error_on_results_page(self):
        with patch.object(self.repo, 'find_team_url', side_effect=requests.ConnectionError('No connection')):
            with pytest.raises(requests.ConnectionError):
                self.service.get_team_stats('Spain', n_matches=5)

    def test_network_error_on_team_page(self):
        self.repo._team_cache['spain'] = '/team/spain/'
        with patch.object(
            self.repo.session, 'get',
            side_effect=requests.ConnectionError('Team page down'),
        ):
            with pytest.raises(requests.ConnectionError):
                self.service.get_team_stats('Spain', n_matches=5)

    def test_timeout_on_team_page(self):
        self.repo._team_cache['spain'] = '/team/spain/'
        with patch.object(
            self.repo.session, 'get',
            side_effect=requests.Timeout('Timed out'),
        ):
            with pytest.raises(requests.Timeout):
                self.service.get_team_stats('Spain', n_matches=5)

    def test_n_matches_greater_than_available(self, mock_team_page_html):
        self.repo._team_cache['spain'] = '/team/spain/'

        mock_resp = Mock()
        mock_resp.text = mock_team_page_html
        mock_resp.raise_for_status = Mock()

        with patch.object(self.repo.session, 'get', return_value=mock_resp):
            stats = self.service.get_team_stats('Spain', n_matches=100)

        assert stats is not None
        assert stats.n_matches == 2

    def test_stats_computed_correctly(self, mock_team_page_html):
        self.repo._team_cache['spain'] = '/team/spain/'

        mock_resp = Mock()
        mock_resp.text = mock_team_page_html
        mock_resp.raise_for_status = Mock()

        with patch.object(self.repo.session, 'get', return_value=mock_resp):
            stats = self.service.get_team_stats('Spain', n_matches=5)

        assert stats is not None
        # Match 1: Spain 2-1 France -> scored=2, conceded=1
        # Match 2: Germany 1-1 Spain -> scored=1, conceded=1
        # avg_goals = (2+1)/2 = 1.5
        assert stats.avg_goals == 1.5
        assert stats.avg_conceded == 1.0
